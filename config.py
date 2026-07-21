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
parserList = [
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

def get_header():
    return {
        'User-Agent': random.choice(MODERN_USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate',
        'Upgrade-Insecure-Requests': '1',
    }

def _env_optional(name, default=None):
    value = os.getenv(name)
    if value is None or value == '':
        return default

    return value

DB_CONFIG = {
    'DB_CONNECT_TYPE': os.getenv('IP_PROXY_POOL_DB_CONNECT_TYPE', 'redis'),
    'redis': {
        'HOST': os.getenv('IP_PROXY_POOL_REDIS_HOST', 'localhost'),
        'PORT': int(os.getenv('IP_PROXY_POOL_REDIS_PORT', '6379')),
        'DB': int(os.getenv('IP_PROXY_POOL_REDIS_DB', '0')),
        'PASSWORD': _env_optional('IP_PROXY_POOL_REDIS_PASSWORD'),
        'REDIS_KEY': os.getenv('IP_PROXY_POOL_REDIS_KEY', 'proxies')
    }
}
DEFAULT_SCORE = 50
MAX_SCORE = 100
ADD_STEP = MAX_SCORE
DECREASE_STEP = max(1, int(os.getenv('IP_PROXY_POOL_DECREASE_STEP', '30')))

MAX_PROXY_NUMBER = 8000
CHECK_TIME = 30
API_HOST = '0.0.0.0'
API_PORT = int(os.getenv('IP_PROXY_POOL_API_PORT', '8000'))

TEST_NUMBER = int(os.getenv('IP_PROXY_POOL_TEST_WORKERS', '1'))
