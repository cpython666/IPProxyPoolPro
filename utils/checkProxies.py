import time

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.utils.httpClients import get as http_get


def _response_is_valid(response, test_target):
    if hasattr(response, 'raise_for_status'):
        response.raise_for_status()

    response_type = test_target.get('response_type', 'text')
    if response_type == 'ip_json':
        data = response.json()
        return any(data.get(key) for key in test_target.get('success_keys', ('origin', 'ip')))

    text = getattr(response, 'text', '')
    expected_text = test_target.get('expected_text')
    if expected_text:
        return expected_text.lower() in text.lower()

    return bool(text)


def checkproxy(proxy, request_client=None, test_target=None):
    if not RedisHelper.is_valid_proxy(proxy):
        print(f'代理格式无效: {proxy}')
        return False

    selected_client = config.validate_request_client(request_client)
    target = test_target or config.get_test_target()
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }

    try:
        response = http_get(
            selected_client,
            url=target['url'],
            headers=config.get_header(),
            proxies=proxies,
            timeout=config.TIMEOUT,
        )

        if _response_is_valid(response, target):
            print(f"代理可用: {proxy} ({selected_client}, {target['name']})")
            return True
    except Exception as exc:
        print(f"代理不可用: {proxy} ({selected_client}, {target['name']}, {exc})")

    return False


def doProxy(redis, proxy, request_client=None, test_target=None):
    if checkproxy(proxy, request_client=request_client, test_target=test_target):
        redis.mark_success(proxy)
    else:
        redis.decrease(proxy)


def probe_proxy(proxy, url=None, request_client=None, timeout=None):
    """Send one request through ``proxy`` to ``url`` and return a rich result.

    Unlike :func:`checkproxy` (which returns a bool for the collection/checking
    flow), this returns status code, latency and a response body snippet so the
    ``/test`` API can show what actually came back.
    """
    selected_client = config.validate_request_client(request_client)
    target_url = (url or '').strip() or config.get_test_target()['url']
    request_timeout = timeout or config.TIMEOUT

    result = {
        'proxy': proxy,
        'url': target_url,
        'client': selected_client,
        'ok': False,
        'status_code': None,
        'latency_ms': None,
        'body': None,
        'error': None,
    }

    if not RedisHelper.is_valid_proxy(proxy):
        result['error'] = 'invalid proxy format (expected ip:port)'
        return result

    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }

    start = time.time()
    try:
        response = http_get(
            selected_client,
            url=target_url,
            headers=config.get_header(),
            proxies=proxies,
            timeout=request_timeout,
        )
        result['latency_ms'] = int((time.time() - start) * 1000)
        result['status_code'] = getattr(response, 'status_code', None)
        body = getattr(response, 'text', '') or ''
        result['body'] = body[:2000]
        result['ok'] = True
    except Exception as exc:
        result['latency_ms'] = int((time.time() - start) * 1000)
        result['error'] = str(exc)

    return result
