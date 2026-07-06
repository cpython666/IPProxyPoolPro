import requests

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper


def checkproxy(proxy):
    if not RedisHelper.is_valid_proxy(proxy):
        print(f'代理格式无效: {proxy}')
        return False

    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }

    try:
        response = requests.get(
            url=config.TEST_IP,
            headers=config.get_header(),
            proxies=proxies,
            timeout=config.TIMEOUT,
        )
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = response.json()
            if data.get('origin') or data.get('ip'):
                print(f'代理可用: {proxy}')
                return True
        elif response.text:
            print(f'代理可用: {proxy}')
            return True
    except requests.RequestException as exc:
        print(f'代理不可用: {proxy} ({exc})')
    except ValueError as exc:
        print(f'代理响应不是有效 JSON: {proxy} ({exc})')

    return False


def doProxy(redis, proxy):
    if checkproxy(proxy):
        redis.mark_success(proxy)
    else:
        redis.decrease(proxy)
