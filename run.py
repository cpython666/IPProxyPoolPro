from multiprocessing import Process

from IPProxyPoolPro import config
from IPProxyPoolPro.TestIP.TestIP import TestIP
from IPProxyPoolPro.spider.Html2Proxies import Html2Proxies


def runTestIP():
    TestIP().randomTest()


def runSpider():
    Html2Proxies.getProxiesList()


def runApi():
    import uvicorn

    uvicorn.run(
        'IPProxyPoolPro.flaskapp.GetProxy:app',
        host=config.API_HOST,
        port=config.API_PORT,
        log_level='info',
    )


if __name__ == "__main__":
    processes = [
        Process(target=runSpider, name='proxy-spider'),
        Process(target=runApi, name='proxy-api'),
    ]

    for index in range(config.TEST_NUMBER):
        processes.append(Process(target=runTestIP, name=f'proxy-checker-{index + 1}'))

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
