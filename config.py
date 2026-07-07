'''
定义规则 
urls:url列表
type：解析方式,取值 regular(正则表达式),xpath(xpath解析),module(自定义第三方模块解析)
patten：可以是正则表达式,可以是xpath语句不过要和上面的相对应
'''
import os
import random
from pathlib import Path

try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None


def _load_env_files():
    """Load .env.example first, then .env, without overriding real env vars."""
    if dotenv_values is None:
        return

    base_dir = Path(__file__).resolve().parent
    original_env_keys = set(os.environ)

    for key, value in dotenv_values(base_dir / '.env.example').items():
        if value is not None and key not in os.environ:
            os.environ[key] = value

    for key, value in dotenv_values(base_dir / '.env').items():
        if value is not None and key not in original_env_keys:
            os.environ[key] = value


_load_env_files()

TIMEOUT = 5
FETCH_TIMEOUT = int(os.getenv('IP_PROXY_POOL_FETCH_TIMEOUT', '15'))
FETCH_CONCURRENCY = max(1, int(os.getenv('IP_PROXY_POOL_FETCH_CONCURRENCY', '5')))
SOURCE_URL_CACHE_SECONDS = max(
    0,
    int(os.getenv('IP_PROXY_POOL_SOURCE_URL_CACHE_SECONDS', '14400')),
)
SOURCE_DYNAMIC_MAX_PAGES = max(
    0,
    int(os.getenv('IP_PROXY_POOL_SOURCE_DYNAMIC_MAX_PAGES', '0')),
)
PRECHECK_CONCURRENCY = max(1, int(os.getenv('IP_PROXY_POOL_PRECHECK_CONCURRENCY', '20')))
PRECHECK_CACHED_SOURCE_PROXIES = os.getenv(
    'IP_PROXY_POOL_PRECHECK_CACHED_SOURCE_PROXIES',
    '1',
).lower() not in ('0', 'false', 'no', 'off')
PRECHECK_FAIL_CACHE_SECONDS = max(
    0,
    int(os.getenv('IP_PROXY_POOL_PRECHECK_FAIL_CACHE_SECONDS', '14400')),
)
'''
ip，端口，类型(0高匿名，1透明)，protocol(0 http,1 https),country(国家),area(省市),updatetime(更新时间),speed(连接速度)
'''
parserList = [
    # {
    #     # http://www.66ip.cn/1.html
    #     'urls': ['http://www.66ip.cn/%s.html' % n for n in ['index'] + list(range(2, 800))],
    #     'type': 'xpath',
    #     'pattern': ".//*[@id=\"main\"]/div[1]/div[2]/div[1]/table/tr[position()>1]",
    #     'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[4]', 'protocol': ''}
    # },
        # http://www.66ip.cn/areaindex_1/1.html
    # {
    #     'urls': ['http://www.66ip.cn/areaindex_%s/%s.html' % (m, n) for m in range(1, 35) for n in range(1, 10)],
    #     'type': 'xpath',
    #     'pattern': ".//*[@id='footer']/div/table/tr[position()>1]",
    #     'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[4]', 'protocol': ''}
    # },
    # {
    #     'urls': ['http://cn-proxy.com/', 'http://cn-proxy.com/archives/218'],
    #     'type': 'xpath',
    #     'pattern': ".//table[@class='sortable']/tbody/tr",
    #     'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}
    #
    # },
    # {
    #     'urls': ['http://www.mimiip.com/gngao/%s' % n for n in range(1, 10)],
    #     'type': 'xpath',
    #     'pattern': ".//table[@class='list']/tr",
    #     'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}
    #
    # },
    # {
    #     'urls': ['https://proxy-list.org/english/index.php?p=%s' % n for n in range(1, 10)],
    #     'type': 'module',
    #     'moduleName': 'proxy_listPraser',
    #     'pattern': 'Proxy\(.+\)',
    #     'position': {'ip': 0, 'port': -1, 'type': -1, 'protocol': 2}
    #
    # },
    # {
    #     'urls': ['http://incloak.com/proxy-list/%s#list' % n for n in
    #              ([''] + ['?start=%s' % (64 * m) for m in range(1, 10)])],
    #     'type': 'xpath',
    #     'pattern': ".//table[@class='proxy__t']/tbody/tr",
    #     'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}
    #
    # },
    {
        'name': 'kuaidaili private domestic free',
        'urls': ['https://www.kuaidaili.com/free/'],
        'pagination': {
            'type': 'html_max_page',
            'url_template': 'https://www.kuaidaili.com/free/inha/{page}/',
            'page_xpath': "//*[@id='listnav']//a/text() | //*[contains(@class, 'pagination')]//a/text()",
        },
        'type': 'xpath',
        'region': 'domestic',
        'pattern': ".//*[@id='list']//table//tr[td]",
        'position': {
            'ip': "./td[@data-title='IP' or @data-title='ip'] | ./td[1]",
            'port': "./td[@data-title='PORT' or @data-title='port'] | ./td[2]",
            'type': './td[4]',
            'protocol': './td[4]',
        }
    },
    {
        'name': 'kuaidaili foreign free',
        'urls': ['https://www.kuaidaili.com/free/fps/'],
        'pagination': {
            'type': 'html_max_page',
            'url_template': 'https://www.kuaidaili.com/free/fps/{page}/',
            'page_xpath': "//*[@id='listnav']//a/text() | //*[contains(@class, 'pagination')]//a/text()",
        },
        'type': 'xpath',
        'region': 'foreign',
        'pattern': ".//*[@id='list']//table//tr[td]",
        'position': {
            'ip': "./td[@data-title='IP' or @data-title='ip'] | ./td[1]",
            'port': "./td[@data-title='PORT' or @data-title='port'] | ./td[2]",
            'type': './td[3]',
            'protocol': './td[3]',
        }
    },
    {
        'name': 'Geonode proxy API',
        'urls': [
            'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps'
        ],
        'pagination': {
            'type': 'json_total',
            'url_template': 'https://proxylist.geonode.com/api/proxy-list?limit=500&page={page}&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps',
            'total_field': 'total',
            'limit_field': 'limit',
        },
        'type': 'json',
        'region': 'foreign',
        'list_path': 'data',
        'ip_field': 'ip',
        'port_field': 'port',
    },
    {
        'name': 'TheSpeedX GitHub HTTP list',
        'urls': ['https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'],
        'type': 'regex',
        'region': 'foreign',
        'pattern': r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}(?!\d)',
    },
    {
        'name': 'monosans GitHub HTTP list',
        'urls': ['https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt'],
        'type': 'regex',
        'region': 'foreign',
        'pattern': r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}(?!\d)',
    },
    {
        'name': 'jetkai GitHub online HTTP list',
        'urls': ['https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt'],
        'type': 'regex',
        'region': 'foreign',
        'pattern': r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}(?!\d)',
    },
    {
        'name': 'Zaeem20 GitHub HTTP list',
        'urls': ['https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt'],
        'type': 'regex',
        'region': 'foreign',
        'pattern': r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}(?!\d)',
    },
    {
        'name': 'roosterkid GitHub HTTPS list',
        'urls': ['https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt'],
        'type': 'regex',
        'region': 'foreign',
        'pattern': r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}(?!\d)',
    },
    {
        'name': 'FreeProxy.World',
        'urls': [
            'https://www.freeproxy.world/?type=http&anonymity=&country=&speed=&port=&page=1'
        ],
        'pagination': {
            'type': 'html_max_page',
            'url_template': 'https://www.freeproxy.world/?type=http&anonymity=&country=&speed=&port=&page={page}',
            'page_xpath': "//*[contains(@class, 'pagination')]//a/text()",
        },
        'type': 'xpath',
        'region': 'foreign',
        'pattern': ".//table//tr[td]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}
    },

    # {
    #     'urls': ['http://www.cz88.net/proxy/%s' % m for m in
    #              ['index.shtml'] + ['http_%s.shtml' % n for n in range(2, 11)]],
    #     'type': 'xpath',
    #     'pattern': ".//*[@id='boxright']/div/ul/li[position()>1]",
    #     'position': {'ip': './div[1]', 'port': './div[2]', 'type': './div[3]', 'protocol': ''}
    #
    # },
    # {
    #     'urls': ['http://www.ip181.com/daili/%s.html' % n for n in range(1, 11)],
    #     'type': 'xpath',
    #     'pattern': ".//div[@class='row']/div[3]/table/tbody/tr[position()>1]",
    #     'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[3]', 'protocol': './td[4]'}
    #
    # },
    # {
    #     'urls': ['http://www.xicidaili.com/%s/%s' % (m, n) for m in ['nn', 'nt', 'wn', 'wt'] for n in range(1, 8)],
    #     'type': 'xpath',
    #     'pattern': ".//*[@id='ip_list']/tr[position()>1]",
    #     'position': {'ip': './td[2]', 'port': './td[3]', 'type': './td[5]', 'protocol': './td[6]'}
    # },
    # {
    #     'urls': ['http://www.cnproxy.com/proxy%s.html' % i for i in range(1, 11)],
    #     'type': 'module',
    #     'moduleName': 'CnproxyPraser',
    #     'pattern': r'<tr><td>(\d+\.\d+\.\d+\.\d+)<SCRIPT type=text/javascript>document.write\(\"\:\"(.+)\)</SCRIPT></td><td>(HTTP|SOCKS4)\s*',
    #     'position': {'ip': 0, 'port': 1, 'type': -1, 'protocol': 2}
    # }
]

SOURCE_REGIONS = ('domestic', 'foreign', 'all')
DEFAULT_SOURCE_REGION = os.getenv('IP_PROXY_POOL_SOURCE_REGION', 'all').lower()

REQUEST_CLIENTS = ('requests', 'curl_cffi', 'requests_go')
DEFAULT_REQUEST_CLIENT = os.getenv('IP_PROXY_POOL_REQUEST_CLIENT', 'requests').lower()
PRECHECK_BEFORE_ADD = os.getenv('IP_PROXY_POOL_PRECHECK_BEFORE_ADD', '1').lower() not in (
    '0',
    'false',
    'no',
    'off',
)

TEST_SITES = {
    'httpbin': {
        'url': 'https://httpbin.org/ip',
        'response_type': 'ip_json',
        'success_keys': ('origin', 'ip'),
    },
    'ipify': {
        'url': 'https://api.ipify.org?format=json',
        'response_type': 'ip_json',
        'success_keys': ('ip',),
    },
    'hyperdash': {
        'url': 'https://hyperdash.com/',
        'response_type': 'text',
        'expected_text': 'Hyperdash',
    },
    'baidu': {
        'url': 'https://www.baidu.com/',
        'response_type': 'text',
        'expected_text': 'baidu',
    },
}
DEFAULT_TEST_SITE = os.getenv('IP_PROXY_POOL_TEST_SITE', 'httpbin').lower()
DEFAULT_TEST_URL = os.getenv('IP_PROXY_POOL_TEST_URL', '').strip()


def get_parser_list(region=None):
    """Return parser configs filtered by source region."""
    selected_region = (region or DEFAULT_SOURCE_REGION or 'all').lower()
    if selected_region not in SOURCE_REGIONS:
        raise ValueError(f'unsupported source region: {selected_region}')

    if selected_region == 'all':
        return parserList

    return [
        parser
        for parser in parserList
        if parser.get('region', 'all') == selected_region
    ]


def validate_request_client(client=None):
    selected_client = (client or DEFAULT_REQUEST_CLIENT or 'requests').lower()
    if selected_client not in REQUEST_CLIENTS:
        raise ValueError(f'unsupported request client: {selected_client}')

    return selected_client


def get_test_target(site=None, url=None):
    """Return the configured proxy validation target."""
    selected_url = (url or DEFAULT_TEST_URL or '').strip()
    if selected_url:
        target = {
            'name': 'custom',
            'url': selected_url,
            'response_type': 'text',
        }
        target['domain'] = registrable_domain(selected_url)
        return target

    selected_site = (site or DEFAULT_TEST_SITE or 'httpbin').lower()
    if selected_site.startswith(('http://', 'https://')):
        return {
            'name': 'custom',
            'url': selected_site,
            'response_type': 'text',
            'domain': registrable_domain(selected_site),
        }

    if selected_site not in TEST_SITES:
        raise ValueError(f'unsupported test site: {selected_site}')

    target = TEST_SITES[selected_site].copy()
    target['name'] = selected_site
    target['domain'] = registrable_domain(target['url'])
    return target


def get_test_targets(sites=None, urls=None):
    """Return one target per requested test site/URL, deduped by pool domain.

    ``sites``/``urls`` may be a comma-separated string or a list. This is what
    lets a single ``run.py`` populate several per-domain pools at once, e.g.
    ``--test-site httpbin,baidu``. Falls back to the single configured target
    when nothing is supplied.
    """
    def _split(value):
        if value is None:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.split(',') if part.strip()]
        return [part for part in value if part]

    url_items = _split(urls) or _split(DEFAULT_TEST_URL)
    site_items = _split(sites) or _split(DEFAULT_TEST_SITE)

    targets = []
    seen_domains = set()

    def _add(target):
        if target['domain'] not in seen_domains:
            seen_domains.add(target['domain'])
            targets.append(target)

    for url in url_items:
        _add(get_test_target(url=url))
    for site in site_items:
        _add(get_test_target(site=site))

    if not targets:
        _add(get_test_target())

    return targets


# Compound (two-level) public suffixes. Without these, ``baidu.com.cn`` would
# collapse to ``com.cn``. We keep the registrable label in front, so
# ``www.baidu.com.cn`` -> ``baidu.com.cn``. Not exhaustive; extend as needed.
TWO_LEVEL_SUFFIXES = frozenset({
    'com.cn', 'net.cn', 'org.cn', 'gov.cn', 'edu.cn', 'ac.cn',
    'co.uk', 'org.uk', 'gov.uk', 'ac.uk', 'me.uk',
    'co.jp', 'or.jp', 'ne.jp', 'ac.jp',
    'com.hk', 'org.hk', 'com.tw', 'org.tw',
    'com.au', 'net.au', 'org.au',
    'co.nz', 'co.kr', 'com.br', 'com.sg', 'co.in', 'com.mx',
})


def registrable_domain(host_or_url):
    """Return the registrable domain used to key a proxy pool.

    Subdomains collapse (``www.baidu.com`` -> ``baidu.com``) while different
    TLDs stay distinct (``foo.com`` vs ``foo.cn``). IP hosts and single-label
    hosts are returned as-is. Falls back to the raw input if it cannot be
    parsed, so a pool is always derivable.
    """
    if not host_or_url:
        return 'default'

    host = host_or_url.strip().lower()
    if '://' in host:
        host = host.split('://', 1)[1]
    # strip path / query / fragment / userinfo / port
    host = host.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    host = host.rsplit('@', 1)[-1]
    host = host.split(':', 1)[0].strip('.')
    if not host:
        return 'default'

    # IPv4/IPv6 literal -> use verbatim (no TLD concept)
    try:
        import ipaddress
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    labels = host.split('.')
    if len(labels) <= 2:
        return host

    last_two = '.'.join(labels[-2:])
    if last_two in TWO_LEVEL_SUFFIXES:
        return '.'.join(labels[-3:])
    return last_two


def redis_key_for_domain(domain):
    """Build the Redis sorted-set key for a given registrable domain."""
    prefix = DB_CONFIG['redis']['REDIS_KEY']
    return f'{prefix}:{domain}'

MODERN_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
]

def get_header():
    return {
        'User-Agent': random.choice(MODERN_USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate',
        'Upgrade-Insecure-Requests': '1',
    }

TEST_URL = 'http://ip.chinaz.com/getip.aspx'
# 获取请求网站ip接口
TEST_IP = 'https://httpbin.org/ip'
# TEST_IP = 'https://api.ipify.org?format=json'
# http请求验证接口
TEST_HTTP_HEADER = 'http://httpbin.org/get'
# https请求验证接口
TEST_HTTPS_HEADER = 'https://httpbin.org/get'


def _env_optional(name, default=None):
    value = os.getenv(name)
    if value is None or value == '':
        return default

    return value



DB_CONFIG = {
# OTHER DATABASES

    'DB_CONNECT_TYPE': os.getenv('IP_PROXY_POOL_DB_CONNECT_TYPE', 'redis'),
    'redis':{
        'HOST': os.getenv('IP_PROXY_POOL_REDIS_HOST', 'localhost'),
        'PORT': int(os.getenv('IP_PROXY_POOL_REDIS_PORT', '6379')),
        'DB': int(os.getenv('IP_PROXY_POOL_REDIS_DB', '0')),
        'PASSWORD': _env_optional('IP_PROXY_POOL_REDIS_PASSWORD'),
        'REDIS_KEY': os.getenv('IP_PROXY_POOL_REDIS_KEY', 'proxies')
    }

}
# 初始默认的代理分数
DEFAULT_SCORE = 50
DEFAULT_SORE = DEFAULT_SCORE
# 成功一次加6分，失败一次减4分,相当于请求成功率大于40%分支才会增加
# ADD_STEP=6
# DECREASE_STEP=4

# 成功直接为100，每次失败减
MAX_SCORE = 100
ADD_STEP = MAX_SCORE
DECREASE_STEP = max(1, int(os.getenv('IP_PROXY_POOL_DECREASE_STEP', '30')))

# 代理存储最大数量
MAX_PROXY_NUMBER=8000
# 检查一次数据库里的代理状态的间隔时间
CHECK_TIME=30
# 请求接口
API_HOST = '0.0.0.0'
API_PORT = int(os.getenv('IP_PROXY_POOL_API_PORT', '8000'))

TEST_NUMBER = int(os.getenv('IP_PROXY_POOL_TEST_WORKERS', '1'))
