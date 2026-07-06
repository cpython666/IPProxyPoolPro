import random
from time import sleep

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.utils.checkProxies import doProxy


class TestIP(object):
    def __init__(self):
        self.redisHelper = RedisHelper()
        print('代理检测进程已启动')

    def randomTest(self):
        while True:
            proxy_list = self.redisHelper.all()
            if not proxy_list:
                sleep(2)
                continue

            sample_size = min(10, len(proxy_list))
            for proxy, _score in random.sample(proxy_list, sample_size):
                doProxy(self.redisHelper, proxy)

            sleep(config.CHECK_TIME)
