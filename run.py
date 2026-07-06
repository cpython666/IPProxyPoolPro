import argparse
from multiprocessing import Process

from IPProxyPoolPro import config


def runTestIP(request_client, test_site, test_url):
    from IPProxyPoolPro.TestIP.TestIP import TestIP

    TestIP(request_client=request_client, test_site=test_site, test_url=test_url).randomTest()


def runSpider(region, request_client, test_site, test_url, precheck_before_add):
    from IPProxyPoolPro.spider.Html2Proxies import Html2Proxies

    Html2Proxies.getProxiesList(
        region=region,
        request_client=request_client,
        test_site=test_site,
        test_url=test_url,
        precheck_before_add=precheck_before_add,
    )


def parse_args():
    parser = argparse.ArgumentParser(description='Start IPProxyPoolPro services.')
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
        help='proxy validation site: httpbin, ipify, hyperdash, or a URL',
    )
    parser.add_argument(
        '--test-url',
        default=config.DEFAULT_TEST_URL,
        help='custom proxy validation URL; overrides --test-site',
    )
    parser.add_argument(
        '--precheck-before-add',
        action=argparse.BooleanOptionalAction,
        default=config.PRECHECK_BEFORE_ADD,
        help='test proxies before adding them to Redis',
    )
    args = parser.parse_args()
    config.validate_request_client(args.request_client)
    config.get_test_target(args.test_site, args.test_url)
    return args


def runApi():
    import uvicorn

    uvicorn.run(
        'IPProxyPoolPro.flaskapp.GetProxy:app',
        host=config.API_HOST,
        port=config.API_PORT,
        log_level='info',
    )


if __name__ == "__main__":
    args = parse_args()
    processes = [
        Process(
            target=runSpider,
            args=(
                args.region,
                args.request_client,
                args.test_site,
                args.test_url,
                args.precheck_before_add,
            ),
            name=f'proxy-spider-{args.region}',
        ),
        Process(target=runApi, name='proxy-api'),
    ]

    for index in range(config.TEST_NUMBER):
        processes.append(
            Process(
                target=runTestIP,
                args=(args.request_client, args.test_site, args.test_url),
                name=f'proxy-checker-{index + 1}',
            )
        )

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
