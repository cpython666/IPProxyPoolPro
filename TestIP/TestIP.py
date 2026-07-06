import random
from time import sleep

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.utils.checkProxies import doProxy


class TestIP(object):
    def __init__(self, request_client=None, test_site=None, test_url=None):
        self.redisHelper = RedisHelper()
        self.request_client = config.validate_request_client(request_client)
        self.test_target = config.get_test_target(test_site, test_url)
        print(
            f"代理检测进程已启动，请求客户端: {self.request_client}，测试站点: {self.test_target['name']}"
        )

    def randomTest(self):
        while True:
            proxy_list = self.redisHelper.all()
            if not proxy_list:
                sleep(2)
                continue

            sample_size = min(10, len(proxy_list))
            for proxy, _score in random.sample(proxy_list, sample_size):
                doProxy(
                    self.redisHelper,
                    proxy,
                    request_client=self.request_client,
                    test_target=self.test_target,
                )

            sleep(config.CHECK_TIME)
