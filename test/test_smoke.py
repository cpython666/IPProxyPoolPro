from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper


def demo():
    assert config.get_parser_list('foreign')
    assert config.validate_request_client('requests') == 'requests'
    assert config.registrable_domain('https://www.baidu.com/path') == 'baidu.com'
    assert RedisHelper.is_valid_proxy('127.0.0.1:8080')
    assert not RedisHelper.is_valid_proxy('127.0.0.1:99999')


if __name__ == '__main__':
    demo()
