from fastapi import FastAPI, HTTPException

from IPProxyPoolPro import config
from IPProxyPoolPro.db.RedisHelper import RedisHelper
from IPProxyPoolPro.utils.checkProxies import probe_proxy


app = FastAPI(title='IPProxyPoolPro', version='1.0.0')


def get_redis(domain=None):
    return RedisHelper(domain=domain)


def list_domains():
    """Registrable domains that currently have a pool."""
    return get_redis().list_pools()


def resolve_domain(domain):
    """Normalize a caller-supplied domain to a registrable domain, or None."""
    if not domain:
        return None
    return config.registrable_domain(domain)


@app.get('/health')
def health():
    try:
        domains = list_domains()
        count = sum(get_redis(d).count() for d in domains)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={'redis': False, 'error': str(exc)},
        )

    return {'redis': True, 'count': count, 'pools': len(domains)}


@app.get('/domains')
def domains():
    """List each pool's domain with its total and usable (full-score) counts."""
    try:
        result = []
        for domain in list_domains():
            helper = get_redis(domain)
            result.append({
                'domain': domain,
                'total': helper.count(),
                'full': helper.full_count(),
            })
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={'redis': False, 'error': str(exc)},
        )

    return result


@app.get('/stats')
def stats(domain: str | None = None):
    """Proxy counts and per-score histogram, aggregated or for one domain.

    Pass ``?domain=baidu.com`` to scope to a single pool; omit it to aggregate
    across every domain pool.
    """
    try:
        target = resolve_domain(domain)
        pools = [target] if target else list_domains()

        total = 0
        full = 0
        distribution = {}
        per_domain = {}
        for pool in pools:
            helper = get_redis(pool)
            pool_total = helper.count()
            pool_full = helper.full_count()
            total += pool_total
            full += pool_full
            per_domain[pool] = {'total': pool_total, 'full': pool_full}
            for score, cnt in helper.score_distribution().items():
                distribution[score] = distribution.get(score, 0) + cnt
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={'redis': False, 'error': str(exc)},
        )

    distribution = dict(sorted(distribution.items(), reverse=True))
    return {
        'total': total,
        'full': full,
        'distribution': distribution,
        'pools': per_domain,
        'score_rule': {
            'max': config.MAX_SCORE,
            'default': config.DEFAULT_SCORE,
            'decrease_step': config.DECREASE_STEP,
        },
    }


@app.get('/test')
def test_proxy(proxy: str, url: str | None = None,
               client: str | None = None, timeout: float | None = None):
    """Send one request through ``proxy`` to ``url`` and return the response."""
    try:
        config.validate_request_client(client)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return probe_proxy(proxy, url=url, request_client=client, timeout=timeout)


def _collect_max(domain=None):
    """Full-score proxies, from one domain pool or merged across all pools."""
    target = resolve_domain(domain)
    if target:
        return get_redis(target).getMax()

    merged = []
    for pool in list_domains():
        merged.extend(get_redis(pool).getMax())
    return merged


@app.get('/')
def hello(domain: str | None = None):
    return _collect_max(domain)


@app.get('/all')
def all_proxies(domain: str | None = None):
    target = resolve_domain(domain)
    if target:
        return get_redis(target).all()

    merged = []
    for pool in list_domains():
        merged.extend(get_redis(pool).all())
    return merged


@app.get('/proxy/{num}')
def proxy(num: int, domain: str | None = None):
    proxies = _collect_max(domain)
    return proxies[:max(num, 0)]
