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
