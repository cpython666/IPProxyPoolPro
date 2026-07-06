from fastapi import FastAPI, HTTPException

from IPProxyPoolPro.db.RedisHelper import RedisHelper


app = FastAPI(title='IPProxyPoolPro', version='1.0.0')


def get_redis():
    return RedisHelper()


@app.get('/health')
def health():
    redis_helper = get_redis()
    try:
        count = redis_helper.count()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={'redis': False, 'error': str(exc)},
        )

    return {'redis': True, 'count': count}


@app.get('/')
def hello():
    redis_helper = get_redis()
    return redis_helper.getMax() if redis_helper.count() > 0 else []


@app.get('/all')
def all_proxies():
    redis_helper = get_redis()
    return redis_helper.all()


@app.get('/proxy/{num}')
def proxy(num: int):
    redis_helper = get_redis()
    proxies = redis_helper.getMax()
    return proxies[:max(num, 0)]
