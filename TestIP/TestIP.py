from time import sleep

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.utils.checkProxies import doProxy


class TestIP(object):
    def __init__(self, request_client=None, test_site=None, test_url=None):
        self.request_client = config.validate_request_client(request_client)
        self.test_target = config.get_test_target(test_site, test_url)
        self.redisHelper = RedisHelper(domain=self.test_target['domain'])
        print(
            f"代理检测进程已启动，请求客户端: {self.request_client}，"
            f"测试站点: {self.test_target['name']}，代理池: {self.redisHelper.redis_key}"
        )

    def randomTest(self):
        while True:
            proxy_list = self.redisHelper.all()
            if not proxy_list:
                sleep(2)
                continue

            print(f'开始检测代理池 {self.redisHelper.redis_key}，本轮共 {len(proxy_list)} 个代理')
            for proxy, _score in proxy_list:
                doProxy(
                    self.redisHelper,
                    proxy,
                    request_client=self.request_client,
                    test_target=self.test_target,
                )

            print(f'本轮检测完成，{config.CHECK_TIME} 秒后开始下一轮')
            sleep(config.CHECK_TIME)
