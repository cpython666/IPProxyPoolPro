import ipaddress

import redis

from IPProxyPoolPro import config


class RedisHelper(object):
    def __init__(self, domain=None):
        redis_config = config.DB_CONFIG['redis']
        self.host = redis_config['HOST']
        self.port = redis_config['PORT']
        self.db = redis_config['DB']
        self.password = redis_config['PASSWORD']
        self.key_prefix = redis_config['REDIS_KEY']
        # Each test domain gets its own sorted-set pool: ``<prefix>:<domain>``.
        # ``domain=None`` keeps the bare prefix so legacy single-pool data and
        # callers that don't care about a domain still work.
        self.domain = domain
        self.redis_key = (
            config.redis_key_for_domain(domain) if domain else self.key_prefix
        )

        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
        )
        self.r = redis.Redis(connection_pool=self.pool)

        self.default_score = config.DEFAULT_SCORE
        self.max_score = config.MAX_SCORE
        self.decrease_step = config.DECREASE_STEP

    @staticmethod
    def is_valid_proxy(proxy):
        try:
            host, port = proxy.rsplit(':', 1)
            ipaddress.ip_address(host.strip())
            port_number = int(port)
            return 0 < port_number <= 65535
        except (AttributeError, TypeError, ValueError):
            return False

    def clear(self):
        return self.r.delete(self.redis_key)

    def count(self):
        return self.r.zcard(self.redis_key)

    def all(self):
        return self.r.zrevrange(self.redis_key, 0, -1, withscores=True)

    def add(self, proxy, score=None):
        if not self.is_valid_proxy(proxy):
            return 0

        if self.r.zscore(self.redis_key, proxy) is not None:
            return 0

        return self.r.zadd(self.redis_key, {proxy: score or self.default_score})

    def exists(self, proxy):
        if not self.is_valid_proxy(proxy):
            return False

        return self.r.zscore(self.redis_key, proxy) is not None

    def mark_success(self, proxy):
        if not self.is_valid_proxy(proxy):
            return 0

        return self.r.zadd(self.redis_key, {proxy: self.max_score})

    def decrease(self, proxy):
        if self.r.zscore(self.redis_key, proxy) is None:
            return

        score = self.r.zincrby(self.redis_key, -1 * self.decrease_step, proxy)
        if score <= 0:
            self.r.zrem(self.redis_key, proxy)

    def getMax(self):
        return self.r.zrevrangebyscore(self.redis_key, self.max_score, self.max_score)

    def full_count(self):
        """Number of proxies at the max score (currently usable)."""
        return self.r.zcount(self.redis_key, self.max_score, self.max_score)

    def count_by_score(self, min_score, max_score):
        """Number of proxies whose score is within [min_score, max_score]."""
        return self.r.zcount(self.redis_key, min_score, max_score)

    def score_distribution(self):
        """Histogram of exact score -> count, ordered from high score to low."""
        distribution = {}
        for _proxy, score in self.r.zrange(self.redis_key, 0, -1, withscores=True):
            bucket = int(score) if float(score).is_integer() else score
            distribution[bucket] = distribution.get(bucket, 0) + 1
        return dict(sorted(distribution.items(), key=lambda item: item[0], reverse=True))

    def list_pools(self):
        """Return the registrable domains that currently have a pool.

        Scans for keys shaped like ``<prefix>:<domain>`` and returns the domain
        suffixes, so the API can enumerate and aggregate per-domain pools
        without hard-coding which test domains are in use.
        """
        prefix = f'{self.key_prefix}:'
        domains = []
        for key in self.r.scan_iter(match=f'{prefix}*'):
            domain = key[len(prefix):]
            if domain:
                domains.append(domain)
        return sorted(domains)

if __name__ == "__main__":
    redisHelper=RedisHelper()
    for i in range(3):
        redisHelper.add(f'k{i}')

    redisHelper.count()


    redisHelper.all()
    redisHelper.decrease('k2')
    redisHelper.add('k1')
