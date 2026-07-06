from time import sleep

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.spider.HtmlDownLoader import Html_Downloader
from IPProxyPoolPro.spider.HtmlPraser import HtmlPraser
from IPProxyPoolPro.utils.checkProxies import checkproxy


class Html2Proxies(object):
    @staticmethod
    def getProxiesList(
        clear_on_start=False,
        region=None,
        request_client=None,
        test_site=None,
        test_url=None,
        precheck_before_add=None,
    ):
        """Fetch proxies from configured sources and store them in Redis."""
        redis = RedisHelper()
        if clear_on_start:
            redis.clear()

        parsers = config.get_parser_list(region)
        region_name = region or config.DEFAULT_SOURCE_REGION
        selected_client = config.validate_request_client(request_client)
        test_target = config.get_test_target(test_site, test_url)
        precheck_enabled = (
            config.PRECHECK_BEFORE_ADD
            if precheck_before_add is None
            else precheck_before_add
        )
        print(
            f"代理采集进程已启动，采集范围: {region_name}，来源数: {len(parsers)}，"
            f"入库前预测试: {precheck_enabled}，请求客户端: {selected_client}，测试站点: {test_target['name']}"
        )

        while True:
            for parser in parsers:
                for url in parser['urls']:
                    count = redis.count()
                    if count >= config.MAX_PROXY_NUMBER:
                        print(f'代理数量 {count} 已达到上限 {config.MAX_PROXY_NUMBER}，暂停抓取')
                        sleep(config.CHECK_TIME)
                        continue

                    response = Html_Downloader.download(url)
                    if not response:
                        print(f'页面抓取或解析配置不可用: {url}')
                        continue

                    proxies = HtmlPraser.parse(response, parser)
                    added = 0
                    skipped = 0
                    for proxy in proxies:
                        if redis.exists(proxy):
                            skipped += 1
                            continue

                        if precheck_enabled and not checkproxy(
                            proxy,
                            request_client=selected_client,
                            test_target=test_target,
                        ):
                            skipped += 1
                            continue

                        added += redis.add(proxy)

                    source_name = parser.get('name', url)
                    print(
                        f'完成 {source_name}: 解析 {len(proxies)} 条，新增 {added} 条，跳过 {skipped} 条，当前共 {redis.count()} 条'
                    )

                    sleep(1)

            print(f'本轮抓取完成，{config.CHECK_TIME} 秒后开始下一轮')
            sleep(config.CHECK_TIME)


if __name__ == "__main__":
    Html2Proxies.getProxiesList()
