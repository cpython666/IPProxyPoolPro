from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
from time import sleep

from lxml import etree

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.spider.HtmlDownLoader import Html_Downloader
from IPProxyPoolPro.spider.HtmlPraser import HtmlPraser
from IPProxyPoolPro.utils.checkProxies import checkproxy


class Html2Proxies(object):
    @staticmethod
    def _parse_and_cache_source(redis, parser, url, response):
        proxies = HtmlPraser.parse(response, parser)
        redis.set_source_proxies_cache(url, proxies)

        return proxies

    @staticmethod
    def _load_source_proxies(redis, parser, url):
        cached_proxies = redis.get_source_proxies_cache(url)
        if cached_proxies is not None:
            return cached_proxies, True

        response = Html_Downloader.download(url)
        if not response:
            return None, False

        proxies = Html2Proxies._parse_and_cache_source(redis, parser, url, response)

        return proxies, False

    @staticmethod
    def _limit_page_count(page_count):
        configured_limit = getattr(config, 'SOURCE_DYNAMIC_MAX_PAGES', 0)
        if configured_limit > 0:
            return min(page_count, configured_limit)

        return page_count

    @staticmethod
    def _html_max_page(response, pagination):
        root = etree.HTML(response)
        if root is None:
            return 1

        page_xpath = pagination.get('page_xpath')
        if not page_xpath:
            return 1

        pages = []
        for item in root.xpath(page_xpath):
            if isinstance(item, str):
                text = item.strip()
            else:
                text = ''.join(item.itertext()).strip()
            if text.isdigit():
                pages.append(int(text))
        return max(pages) if pages else 1

    @staticmethod
    def _json_total_pages(response, pagination):
        try:
            data = json.loads(response)
        except (TypeError, ValueError):
            return 1

        try:
            total = int(data.get(pagination.get('total_field', 'total'), 0))
            limit = int(data.get(pagination.get('limit_field', 'limit'), 0))
        except (TypeError, ValueError):
            return 1

        if total <= 0 or limit <= 0:
            return 1

        return int(math.ceil(total / float(limit)))

    @staticmethod
    def _discover_parser_urls(redis, parser):
        urls = list(parser.get('urls', []))
        pagination = parser.get('pagination')
        if not pagination or not urls:
            return urls, {}

        first_url = pagination.get('first_url') or urls[0]
        response = Html_Downloader.download(first_url)
        if not response:
            print(f'dynamic pagination discovery failed: {parser.get("name", first_url)}')
            return urls, {}

        prefetched = {
            first_url: Html2Proxies._parse_and_cache_source(
                redis,
                parser,
                first_url,
                response,
            )
        }
        pagination_type = pagination.get('type')
        if pagination_type == 'html_max_page':
            page_count = Html2Proxies._html_max_page(response, pagination)
        elif pagination_type == 'json_total':
            page_count = Html2Proxies._json_total_pages(response, pagination)
        else:
            page_count = 1

        page_count = Html2Proxies._limit_page_count(max(1, page_count))
        url_template = pagination.get('url_template')
        if not url_template or page_count <= 1:
            return [first_url], prefetched

        expanded_urls = [
            url_template.format(page=page)
            for page in range(1, page_count + 1)
        ]
        expanded_urls[0] = first_url
        source_name = parser.get('name', first_url)
        print(f'dynamic pagination discovered: {source_name}, pages={page_count}')

        return expanded_urls, prefetched

    @staticmethod
    def _download_parser_urls(redis, parser, fetch_workers):
        urls, prefetched = Html2Proxies._discover_parser_urls(redis, parser)
        remaining_urls = []
        for url in urls:
            if url in prefetched:
                yield url, prefetched[url], False
            else:
                remaining_urls.append(url)

        if fetch_workers <= 1 or len(remaining_urls) <= 1:
            for url in remaining_urls:
                proxies, cached = Html2Proxies._load_source_proxies(
                    redis,
                    parser,
                    url,
                )
                yield url, proxies, cached
            return

        worker_count = min(fetch_workers, len(remaining_urls))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(Html2Proxies._load_source_proxies, redis, parser, url): url
                for url in remaining_urls
            }
            for future in as_completed(futures):
                url = futures[future]
                try:
                    proxies, cached = future.result()
                except Exception as exc:
                    print(f'页面下载失败: {url} ({exc})')
                    proxies = None
                    cached = False

                yield url, proxies, cached

    @staticmethod
    def _precheck_proxy(proxy, selected_client, test_target):
        return checkproxy(
            proxy,
            request_client=selected_client,
            test_target=test_target,
        )

    @staticmethod
    def _precheck_proxies(proxies, selected_client, test_target, precheck_workers):
        if precheck_workers <= 1 or len(proxies) <= 1:
            for proxy in proxies:
                yield proxy, Html2Proxies._precheck_proxy(
                    proxy,
                    selected_client,
                    test_target,
                )
            return

        worker_count = min(precheck_workers, len(proxies))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(
                    Html2Proxies._precheck_proxy,
                    proxy,
                    selected_client,
                    test_target,
                ): proxy
                for proxy in proxies
            }
            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    passed = future.result()
                except Exception as exc:
                    print(f'代理预测试异常: {proxy} ({exc})')
                    passed = False

                yield proxy, passed

    @staticmethod
    def getProxiesList(
        clear_on_start=False,
        region=None,
        request_client=None,
        test_site=None,
        test_url=None,
        precheck_before_add=None,
        fetch_workers=None,
        precheck_workers=None,
    ):
        """Fetch proxies from configured sources and store them in Redis."""
        test_target = config.get_test_target(test_site, test_url)
        pool_domain = test_target['domain']
        redis = RedisHelper(domain=pool_domain)
        if clear_on_start:
            redis.clear()

        parsers = config.get_parser_list(region)
        region_name = region or config.DEFAULT_SOURCE_REGION
        selected_client = config.validate_request_client(request_client)
        precheck_enabled = (
            config.PRECHECK_BEFORE_ADD
            if precheck_before_add is None
            else precheck_before_add
        )
        selected_fetch_workers = max(
            1,
            int(fetch_workers or config.FETCH_CONCURRENCY),
        )
        selected_precheck_workers = max(
            1,
            int(precheck_workers or config.PRECHECK_CONCURRENCY),
        )
        print(
            f"代理采集进程已启动，采集范围: {region_name}，来源数: {len(parsers)}，"
            f"入库前预测试: {precheck_enabled}，请求客户端: {selected_client}，"
            f"测试站点: {test_target['name']}，代理池: {redis.redis_key}，"
            f"网页抓取并发: {selected_fetch_workers}，"
            f"列表页解析缓存: {config.SOURCE_URL_CACHE_SECONDS} 秒，"
            f"预测试并发: {selected_precheck_workers}，"
            f"缓存代理预测试: {config.PRECHECK_CACHED_SOURCE_PROXIES}，"
            f"预测试失败缓存: {config.PRECHECK_FAIL_CACHE_SECONDS} 秒"
        )

        while True:
            for parser in parsers:
                count = redis.count()
                if count >= config.MAX_PROXY_NUMBER:
                    print(f'代理数量 {count} 已达到上限 {config.MAX_PROXY_NUMBER}，暂停抓取')
                    sleep(config.CHECK_TIME)
                    continue

                for url, proxies, source_cached in Html2Proxies._download_parser_urls(
                    redis,
                    parser,
                    selected_fetch_workers,
                ):
                    if redis.count() >= config.MAX_PROXY_NUMBER:
                        print(f'代理数量已达到上限 {config.MAX_PROXY_NUMBER}，跳过本轮剩余结果')
                        break

                    if proxies is None:
                        print(f'页面抓取或解析配置不可用: {url}')
                        continue

                    added = 0
                    skipped = 0
                    cached_failed = 0
                    need_precheck = []
                    for proxy in proxies:
                        if redis.exists(proxy):
                            skipped += 1
                            continue

                        should_precheck = (
                            precheck_enabled
                            and (
                                not source_cached
                                or config.PRECHECK_CACHED_SOURCE_PROXIES
                            )
                        )
                        if should_precheck:
                            if redis.precheck_failed_recently(proxy):
                                cached_failed += 1
                                skipped += 1
                                continue

                            need_precheck.append(proxy)
                            continue

                        added += redis.add(proxy)

                    if precheck_enabled and need_precheck:
                        for proxy, passed in Html2Proxies._precheck_proxies(
                            need_precheck,
                            selected_client,
                            test_target,
                            selected_precheck_workers,
                        ):
                            if passed:
                                redis.clear_precheck_failed(proxy)
                                added += redis.add(proxy)
                            else:
                                redis.mark_precheck_failed(proxy)
                                skipped += 1

                    source_name = parser.get('name', url)
                    cache_status = '历史解析' if source_cached else '请求解析'
                    print(
                        f'完成 {source_name}({cache_status}): 解析 {len(proxies)} 条，新增 {added} 条，'
                        f'跳过 {skipped} 条，缓存跳过 {cached_failed} 条，当前共 {redis.count()} 条'
                    )

                    sleep(1)

            print(f'本轮抓取完成，{config.CHECK_TIME} 秒后开始下一轮')
            sleep(config.CHECK_TIME)


if __name__ == "__main__":
    Html2Proxies.getProxiesList()
