import argparse
from multiprocessing import Process

from IPProxyPoolPro import config


def runTestIP(request_client, test_site, test_url):
    from IPProxyPoolPro.TestIP.TestIP import TestIP

    try:
        TestIP(request_client=request_client, test_site=test_site, test_url=test_url).randomTest()
    except KeyboardInterrupt:
        print('代理检测进程已停止')


def runSpider(
    region,
    request_client,
    test_site,
    test_url,
    precheck_before_add,
    fetch_workers,
    precheck_workers,
):
    from IPProxyPoolPro.spider.Html2Proxies import Html2Proxies

    try:
        Html2Proxies.getProxiesList(
            region=region,
            request_client=request_client,
            test_site=test_site,
            test_url=test_url,
            precheck_before_add=precheck_before_add,
            fetch_workers=fetch_workers,
            precheck_workers=precheck_workers,
        )
    except KeyboardInterrupt:
        print('代理采集进程已停止')


def parse_args():
    parser = argparse.ArgumentParser(description='Start IPProxyPoolPro services.')
    parser.add_argument(
        'command',
        nargs='?',
        choices=('web', 'spider', 'test', 'all'),
        default='all',
        help='service to run: web, spider, test, or all (default: all)',
    )
    parser.add_argument(
        '--region',
        choices=config.SOURCE_REGIONS,
        default=config.DEFAULT_SOURCE_REGION,
        help='proxy source region to collect: domestic, foreign, or all',
    )
    parser.add_argument(
        '--request-client',
        choices=config.REQUEST_CLIENTS,
        default=config.DEFAULT_REQUEST_CLIENT,
        help='HTTP client used by proxy checkers',
    )
    parser.add_argument(
        '--test-site',
        default=config.DEFAULT_TEST_SITE,
        help='proxy validation site(s), comma-separated: httpbin,baidu,... '
             'each distinct domain gets its own pool',
    )
    parser.add_argument(
        '--test-url',
        default=config.DEFAULT_TEST_URL,
        help='custom proxy validation URL(s), comma-separated; overrides --test-site',
    )
    parser.add_argument(
        '--precheck-before-add',
        action=argparse.BooleanOptionalAction,
        default=config.PRECHECK_BEFORE_ADD,
        help='test proxies before adding them to Redis',
    )
    parser.add_argument(
        '--fetch-workers',
        type=int,
        default=config.FETCH_CONCURRENCY,
        help='concurrent source-page fetch workers used by spider',
    )
    parser.add_argument(
        '--precheck-workers',
        type=int,
        default=config.PRECHECK_CONCURRENCY,
        help='concurrent precheck workers used before adding proxies',
    )
    parser.add_argument(
        '--test-workers',
        type=int,
        default=config.TEST_NUMBER,
        help='proxy checker worker processes per test domain',
    )
    args = parser.parse_args()
    config.validate_request_client(args.request_client)
    if args.fetch_workers < 1:
        parser.error('--fetch-workers must be >= 1')
    if args.precheck_workers < 1:
        parser.error('--precheck-workers must be >= 1')
    if args.test_workers < 1:
        parser.error('--test-workers must be >= 1')
    if args.command in ('spider', 'test', 'all'):
        # Resolve now so an unsupported site/URL fails fast before spawning workers.
        args.test_targets = config.get_test_targets(args.test_site, args.test_url)
    else:
        args.test_targets = []
    return args


def runApi():
    import uvicorn

    uvicorn.run(
        'IPProxyPoolPro.flaskapp.GetProxy:app',
        host=config.API_HOST,
        port=config.API_PORT,
        log_level='info',
    )


def _target_args(target):
    """Map a resolved target back to (test_site, test_url) for a worker.

    Named sites (httpbin, baidu, ...) are passed by name so the worker keeps
    their response validation (e.g. expected_text); custom targets pass by URL.
    """
    if target['name'] == 'custom':
        return None, target['url']
    return target['name'], None


def _start_processes(processes):
    for process in processes:
        process.start()
        print(f'Started process: {process.name} (pid={process.pid})')

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print('Stopping child processes...')
        for process in processes:
            if process.is_alive():
                process.terminate()
        for process in processes:
            process.join()


def _build_processes(args):
    processes = []
    if args.command in ('web', 'all'):
        processes.append(Process(target=runApi, name='proxy-api'))

    # One spider/checker group per test domain, each bound to that domain's pool.
    for target in args.test_targets:
        site, url = _target_args(target)
        domain = target['domain']
        if args.command in ('spider', 'all'):
            processes.append(
                Process(
                    target=runSpider,
                    args=(
                        args.region,
                        args.request_client,
                        site,
                        url,
                        args.precheck_before_add,
                        args.fetch_workers,
                        args.precheck_workers,
                    ),
                    name=f'proxy-spider-{domain}',
                )
            )
        if args.command in ('test', 'all'):
            for index in range(args.test_workers):
                processes.append(
                    Process(
                        target=runTestIP,
                        args=(args.request_client, site, url),
                        name=f'proxy-checker-{domain}-{index + 1}',
                    )
                )

    return processes


if __name__ == "__main__":
    args = parse_args()
    if args.test_targets:
        print(
            'Test domains -> pools: '
            + ', '.join(f"{t['name']}={t['domain']}" for t in args.test_targets)
        )

    if args.command == 'web':
        runApi()
    else:
        _start_processes(_build_processes(args))
