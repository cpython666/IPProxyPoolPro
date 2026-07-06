from time import sleep

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.spider.HtmlDownLoader import Html_Downloader
from IPProxyPoolPro.spider.HtmlPraser import HtmlPraser


class Html2Proxies(object):
    @staticmethod
    def getProxiesList(clear_on_start=False):
        """Fetch proxies from configured sources and store them in Redis."""
        redis = RedisHelper()
        if clear_on_start:
            redis.clear()

        while True:
            for parser in config.parserList:
                for url in parser['urls']:
                    count = redis.count()
                    if count >= config.MAX_PROXY_NUMBER:
                        print(f'代理数量 {count} 已达到上限 {config.MAX_PROXY_NUMBER}，暂停抓取')
                        sleep(config.CHECK_TIME)
                        continue

                    response = Html_Downloader.download(url)
                    if not response or parser['type'] != 'xpath':
                        print(f'页面抓取或解析配置不可用: {url}')
                        continue

                    proxies = HtmlPraser.XpathPraser(response, parser)
                    added = 0
                    for proxy in proxies:
                        added += redis.add(proxy)

                    print(
                        f'完成 {url}: 解析 {len(proxies)} 条，新增 {added} 条，当前共 {redis.count()} 条'
                    )

                    sleep(1)

            print(f'本轮抓取完成，{config.CHECK_TIME} 秒后开始下一轮')
            sleep(config.CHECK_TIME)


if __name__ == "__main__":
    Html2Proxies.getProxiesList()
