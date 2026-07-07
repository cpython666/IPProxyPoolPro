# IPProxyPoolPro

一个轻量级爬虫代理池项目：抓取免费代理，存入 Redis，后台定时检测可用性，并通过 FastAPI 提供查询接口。

## 功能

- 抓取 `config.py` 中配置的代理源。
- 使用 Redis sorted set 存储代理和评分。
- 定时随机检测代理可用性，成功置为满分，失败按步长扣分，扣到 0 后删除。
- 提供 HTTP API 查询满分代理和全部代理。

## 环境要求

- Python 3.10+
- Redis 服务

推荐使用本机已有的 conda 爬虫环境：

```bash
conda activate journal_scrapy
python run.py
```

如果使用新的 Python 环境，先安装依赖：

```bash
pip install -r requirements.txt
```

启动 Redis 后运行：

```bash
python run.py
```

`run.py` 支持拆分启动，也可以继续一键启动：

```bash
# 一键启动 Web 服务、代理采集、代理检测
python run.py
python run.py all

# 只启动 Web API
python run.py web

# 只采集代理
python run.py spider

# 只检测 Redis 中已有代理
python run.py test
```

只采集国内、国外或全部代理源：

```bash
python run.py spider --region domestic
python run.py spider --region foreign
python run.py spider --region all
```

指定代理检测使用的请求客户端和测试站点：

```bash
python run.py --request-client requests --test-site httpbin
python run.py --request-client curl_cffi --test-site hyperdash
python run.py --request-client requests_go --test-site ipify
python run.py --test-url https://example.com/
python run.py --region foreign --request-client curl_cffi --test-site hyperdash
```

采集代理源页面时默认并发数为 `5`，可以按网络情况调整：

```bash
python run.py spider --fetch-workers 10
```

入库前预测试代理默认并发数为 `20`，可以按测试站点和网络情况调整：

```bash
python run.py spider --precheck-workers 20
```

代理列表页的解析结果会缓存 4 小时，重启后同一个列表 URL 不会马上重复请求目标站，而是直接复用历史解析出的代理列表：

```bash
IP_PROXY_POOL_SOURCE_URL_CACHE_SECONDS=14400
```

缓存命中的历史代理默认仍会走入库前预测试；如果想直接入池、交给后台检测，可以关闭：

```bash
IP_PROXY_POOL_PRECHECK_CACHED_SOURCE_PROXIES=0
```

**按测试域名分池**：代理按“用哪个域名测通的”分开存储，Redis key 形如
`proxies:<一级域名>`（如 `proxies:baidu.com`、`proxies:httpbin.org`）。一级域名区分
到可注册域，所以 `foo.com` 和 `foo.cn` 会分开，但 `www.baidu.com` 与 `baidu.com`
归为同一池。`--test-site` / `--test-url` 支持逗号分隔的多个目标，每个不同域名各自
起一个采集进程 + `TEST_NUMBER` 个检测进程，写入各自的池：

```bash
# 同时用 baidu 和 httpbin 两个域名检测，写入 proxies:baidu.com 和 proxies:httpbin.org
python run.py --test-site baidu,httpbin
python run.py --test-url https://a.com/,https://b.cn/
```

默认会在代理入库前先请求测试站点，测试通过才写入 Redis。若只想先快速入库再交给后台检测，可以关闭预测试：

```bash
python run.py --no-precheck-before-add
```

预测试失败的代理会写入 Redis 失败缓存，默认 4 小时内再次采集到会直接跳过，避免重启后反复等待同一批坏代理超时：

```bash
IP_PROXY_POOL_PRECHECK_FAIL_CACHE_SECONDS=14400
```

也可以复制 `.env.example` 为本地 `.env`，用环境变量指定默认采集范围、Redis、检测客户端和测试站点：

```bash
copy .env.example .env
python run.py
```

默认 API 监听 `0.0.0.0:8000`。

FastAPI 文档地址：

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## 配置

主要配置在 `config.py`：

- `DB_CONFIG`: Redis 连接配置，可通过环境变量覆盖地址、端口、库、密码和 key。
- `parserList`: 代理源和解析规则，支持 `xpath`、`regex`、`json`，可用 `region` 标记 `domestic`、`foreign` 或 `all`。
- `TEST_SITES`: 代理检测可选测试站点，内置 `httpbin`、`ipify`、`hyperdash`、`baidu`，默认 `httpbin`。
- `DEFAULT_TEST_URL`: 可通过环境变量 `IP_PROXY_POOL_TEST_URL` 设置自定义代理检测 URL。
- `FETCH_TIMEOUT`: 代理源页面/API 抓取超时，默认 15 秒。
- `SOURCE_URL_CACHE_SECONDS`: 代理列表页解析结果缓存时间，默认 `14400` 秒，设置为 `0` 可关闭缓存。
- `REQUEST_CLIENTS`: 代理检测可选请求客户端，支持 `requests`、`curl_cffi`、`requests_go`。
- `PRECHECK_BEFORE_ADD`: 是否在代理入库前先预测试，默认开启。
- `PRECHECK_CONCURRENCY`: 入库前预测试并发数，默认 `20`。
- `PRECHECK_CACHED_SOURCE_PROXIES`: 是否预测试从历史解析缓存取出的代理，默认开启。
- `PRECHECK_FAIL_CACHE_SECONDS`: 预测试失败缓存时间，默认 `14400` 秒，设置为 `0` 可关闭缓存。
- `MAX_PROXY_NUMBER`: 每个域名池最多保留的代理数量。
- `CHECK_TIME`: 抓取轮次和检测轮次的等待间隔。
- `TEST_NUMBER`: 每个测试域名的代理检测进程数，默认 `1`，可通过 `IP_PROXY_POOL_TEST_WORKERS` 配置。
- `IP_PROXY_POOL_REDIS_KEY`: 池 key 前缀，实际池为 `<前缀>:<一级域名>`，默认前缀 `proxies`。

配置项可以写在 `.env` 里，也可以直接用系统环境变量覆盖：

- `IP_PROXY_POOL_API_PORT`: API 端口，默认 `8000`
- `IP_PROXY_POOL_TEST_WORKERS`: 代理检测进程数，默认 `1`
- `IP_PROXY_POOL_DB_CONNECT_TYPE`: 数据库类型，默认 `redis`
- `IP_PROXY_POOL_REDIS_HOST`: Redis 地址，默认 `localhost`
- `IP_PROXY_POOL_REDIS_PORT`: Redis 端口，默认 `6379`
- `IP_PROXY_POOL_REDIS_DB`: Redis DB，默认 `0`
- `IP_PROXY_POOL_REDIS_PASSWORD`: Redis 密码，默认空
- `IP_PROXY_POOL_REDIS_KEY`: Redis sorted set key，默认 `proxies`
- `IP_PROXY_POOL_SOURCE_REGION`: 采集范围，`domestic`、`foreign` 或 `all`
- `IP_PROXY_POOL_FETCH_TIMEOUT`: 代理源抓取超时，默认 `15`
- `IP_PROXY_POOL_FETCH_CONCURRENCY`: 代理源页面抓取并发数，默认 `5`
- `IP_PROXY_POOL_SOURCE_URL_CACHE_SECONDS`: 代理列表页解析结果缓存秒数，默认 `14400`
- `IP_PROXY_POOL_PRECHECK_BEFORE_ADD`: 是否入库前预测试，默认 `1`
- `IP_PROXY_POOL_PRECHECK_CONCURRENCY`: 入库前预测试并发数，默认 `20`
- `IP_PROXY_POOL_PRECHECK_CACHED_SOURCE_PROXIES`: 是否预测试历史解析缓存里的代理，默认 `1`
- `IP_PROXY_POOL_PRECHECK_FAIL_CACHE_SECONDS`: 预测试失败缓存秒数，默认 `14400`
- `IP_PROXY_POOL_REQUEST_CLIENT`: 检测客户端，`requests`、`curl_cffi` 或 `requests_go`
- `IP_PROXY_POOL_TEST_SITE`: 检测站点，支持逗号分隔多个（如 `httpbin,baidu`），每个不同域名一个池
- `IP_PROXY_POOL_TEST_URL`: 自定义检测 URL，支持逗号分隔多个，设置后覆盖 `IP_PROXY_POOL_TEST_SITE`

## 按测试域名分池

代理**按检测所用的测试域名分开存储**。每个测试域名对应一个独立的 Redis sorted set：
`<前缀>:<一级域名>`，例如 `proxies:baidu.com`、`proxies:httpbin.org`。

- 分池依据是**一级（可注册）域名**：`www.baidu.com` 与 `image.baidu.com` 归入同一池 `baidu.com`；
  而 `foo.com` 与 `foo.cn` 是不同池，`baidu.com.cn` 这类二级后缀也能正确识别。
- 每个池独立评分、独立 `MAX_PROXY_NUMBER` 上限。一个代理在 `baidu.com` 池满分，不代表它在
  `httpbin.org` 池也可用——因为它们是用不同域名分别检测的。
- 用逗号指定多个测试域名时，`run.py` 会为每个域名各起一个采集进程 + `TEST_NUMBER` 个检测进程，
  分别写入各自的池：

```bash
python run.py --test-site httpbin,baidu
```

`curl_cffi` 对应 Python 包 `curl_cffi.requests`；`requests_go` 对应 Python 包 `requests-go`/`requests_go`。这两个客户端是可选依赖，不指定时默认只需要 `requests`。

如果新环境里需要启用这两个可选客户端，可以安装：

```bash
pip install curl_cffi requests-go
```

## API

多池说明：`/`、`/all`、`/proxy/<num>`、`/stats` 默认**跨所有域名池聚合**，
也可加 `?domain=baidu.com` 只看某个池（会自动归一到一级域名）。

- `GET /health`: 服务健康检查，返回 Redis 状态、代理总数和池数量。
- `GET /domains`: 列出各测试域名池及其总数、满分数量。
- `GET /`: 返回所有满分代理（可选 `?domain=`）。
- `GET /proxy/<num>`: 返回前 `num` 个满分代理（可选 `?domain=`）。
- `GET /all`: 返回全部代理及分数（可选 `?domain=`）。
- `GET /stats`: 返回代理总数、满分（可用）数量、各分数的数量分布、各池明细，以及评分规则（可选 `?domain=`）。
- `GET /test`: 用指定代理请求测试链接并返回响应。查询参数：
  - `proxy`（必填）：`ip:port`
  - `url`（选填）：测试链接，默认使用配置的测试站点
  - `client`（选填）：请求客户端 `requests` / `curl_cffi` / `requests_go`，默认全局配置
  - `timeout`（选填）：超时秒数，默认 `TIMEOUT`
  - 返回 `ok`、`status_code`、`latency_ms`、`body`（截断）、`error`

示例：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/domains
curl http://localhost:8000/proxy/10
curl 'http://localhost:8000/proxy/10?domain=baidu.com'
curl http://localhost:8000/all
curl http://localhost:8000/stats
curl 'http://localhost:8000/stats?domain=httpbin.org'
curl 'http://localhost:8000/test?proxy=1.2.3.4:8080&url=https://httpbin.org/ip'
```

`GET /stats` 返回示例（跨池聚合，`pools` 给出每个域名池的明细）：

```json
{
  "total": 128,
  "full": 42,
  "distribution": {"100": 42, "70": 31, "50": 25, "40": 18, "20": 8, "10": 4},
  "pools": {
    "httpbin.org": {"total": 80, "full": 30},
    "baidu.com": {"total": 48, "full": 12}
  },
  "score_rule": {"max": 100, "default": 50, "decrease_step": 30}
}
```

## 评分规则

- 新抓取代理初始分：`DEFAULT_SCORE = 50`
- 检测成功：置为 `MAX_SCORE = 100`
- 检测失败：扣 `DECREASE_STEP = 30`
- 分数小于等于 0：从 Redis 删除

## 数据持久化与重启

代理数据保存在 Redis（默认 `db0`），**重启不会清空历史数据**。重新运行 `python run.py`
后会重连 Redis，在已有数据基础上继续抓取和检测，只有分数扣到 0 的代理才会被删除。

## 说明

免费代理源经常变动，`parserList` 中的 XPath 可能会随着目标网站改版而失效。若抓取不到代理，优先检查目标网站是否仍可访问，以及表格结构是否与配置一致。

本项目早期实现参考了 [qiyeboy/IPProxyPool](https://github.com/qiyeboy/IPProxyPool)。


## 代理来源

当前默认启用的来源都在 `config.py` 的 `parserList` 中维护，并按 `region` 分为国内和国外。

国内来源：

- 快代理国内免费私密代理页：`https://www.kuaidaili.com/free/`

国外来源：

- 快代理海外免费代理页：`https://www.kuaidaili.com/free/fps/`
- Geonode Free Proxy List：`https://geonode.com/free-proxy-list/`
- TheSpeedX/PROXY-List：`https://github.com/TheSpeedX/PROXY-List`
- monosans/proxy-list：`https://github.com/monosans/proxy-list`
- jetkai/proxy-list：`https://github.com/jetkai/proxy-list`
- Zaeem20/FREE_PROXIES_LIST：`https://github.com/Zaeem20/FREE_PROXIES_LIST`
- roosterkid/openproxylist：`https://github.com/roosterkid/openproxylist`
- FreeProxy.World：`https://www.freeproxy.world/`
