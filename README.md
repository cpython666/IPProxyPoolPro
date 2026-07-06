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

只采集国内、国外或全部代理源：

```bash
python run.py --region domestic
python run.py --region foreign
python run.py --region all
```

指定代理检测使用的请求客户端和测试站点：

```bash
python run.py --request-client requests --test-site httpbin
python run.py --request-client curl_cffi --test-site hyperdash
python run.py --request-client requests_go --test-site ipify
python run.py --test-url https://example.com/
python run.py --region foreign --request-client curl_cffi --test-site hyperdash
```

默认会在代理入库前先请求测试站点，测试通过才写入 Redis。若只想先快速入库再交给后台检测，可以关闭预测试：

```bash
python run.py --no-precheck-before-add
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
- `TEST_SITES`: 代理检测可选测试站点，内置 `httpbin`、`ipify`、`hyperdash`，默认 `httpbin`。
- `DEFAULT_TEST_URL`: 可通过环境变量 `IP_PROXY_POOL_TEST_URL` 设置自定义代理检测 URL。
- `FETCH_TIMEOUT`: 代理源页面/API 抓取超时，默认 15 秒。
- `REQUEST_CLIENTS`: 代理检测可选请求客户端，支持 `requests`、`curl_cffi`、`requests_go`。
- `PRECHECK_BEFORE_ADD`: 是否在代理入库前先预测试，默认开启。
- `MAX_PROXY_NUMBER`: Redis 中最多保留的代理数量。
- `CHECK_TIME`: 抓取轮次和检测轮次的等待间隔。
- `TEST_NUMBER`: 代理检测进程数。

配置项可以写在 `.env` 里，也可以直接用系统环境变量覆盖：

- `IP_PROXY_POOL_API_PORT`: API 端口，默认 `8000`
- `IP_PROXY_POOL_TEST_WORKERS`: 代理检测进程数，默认 `3`
- `IP_PROXY_POOL_DB_CONNECT_TYPE`: 数据库类型，默认 `redis`
- `IP_PROXY_POOL_REDIS_HOST`: Redis 地址，默认 `localhost`
- `IP_PROXY_POOL_REDIS_PORT`: Redis 端口，默认 `6379`
- `IP_PROXY_POOL_REDIS_DB`: Redis DB，默认 `1`
- `IP_PROXY_POOL_REDIS_PASSWORD`: Redis 密码，默认空
- `IP_PROXY_POOL_REDIS_KEY`: Redis sorted set key，默认 `proxies`
- `IP_PROXY_POOL_SOURCE_REGION`: 采集范围，`domestic`、`foreign` 或 `all`
- `IP_PROXY_POOL_FETCH_TIMEOUT`: 代理源抓取超时，默认 `15`
- `IP_PROXY_POOL_PRECHECK_BEFORE_ADD`: 是否入库前预测试，默认 `1`
- `IP_PROXY_POOL_REQUEST_CLIENT`: 检测客户端，`requests`、`curl_cffi` 或 `requests_go`
- `IP_PROXY_POOL_TEST_SITE`: 检测站点，`httpbin`、`ipify` 或 `hyperdash`
- `IP_PROXY_POOL_TEST_URL`: 自定义检测 URL，设置后覆盖 `IP_PROXY_POOL_TEST_SITE`

`curl_cffi` 对应 Python 包 `curl_cffi.requests`；`requests_go` 对应 Python 包 `requests-go`/`requests_go`。这两个客户端是可选依赖，不指定时默认只需要 `requests`。

如果新环境里需要启用这两个可选客户端，可以安装：

```bash
pip install curl_cffi requests-go
```

## API

- `GET /health`: 服务健康检查，返回 Redis 状态和代理数量。
- `GET /`: 返回所有满分代理。
- `GET /proxy/<num>`: 返回前 `num` 个满分代理。
- `GET /all`: 返回全部代理及分数。

示例：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/proxy/10
curl http://localhost:8000/all
```

## 评分规则

- 新抓取代理初始分：`DEFAULT_SCORE = 50`
- 检测成功：置为 `MAX_SCORE = 100`
- 检测失败：扣 `DECREASE_STEP = 30`
- 分数小于等于 0：从 Redis 删除

## 说明

免费代理源经常变动，`parserList` 中的 XPath 可能会随着目标网站改版而失效。若抓取不到代理，优先检查目标网站是否仍可访问，以及表格结构是否与配置一致。

本项目早期实现参考了 [qiyeboy/IPProxyPool](https://github.com/qiyeboy/IPProxyPool)。


## 代理来源

当前默认启用的来源都在 `config.py` 的 `parserList` 中维护，并按 `region` 分为国内和国外。

国内来源：

- 快代理代理列表页：`https://www.kuaidaili.com/proxylist/`
- 快代理国内免费代理页：`https://www.kuaidaili.com/free/inha/`、`https://www.kuaidaili.com/free/intr/`

国外来源：

- Geonode Free Proxy List：`https://geonode.com/free-proxy-list/`
- TheSpeedX/PROXY-List：`https://github.com/TheSpeedX/PROXY-List`
- monosans/proxy-list：`https://github.com/monosans/proxy-list`
- jetkai/proxy-list：`https://github.com/jetkai/proxy-list`
- Zaeem20/FREE_PROXIES_LIST：`https://github.com/Zaeem20/FREE_PROXIES_LIST`
- roosterkid/openproxylist：`https://github.com/roosterkid/openproxylist`
- FreeProxy.World：`https://www.freeproxy.world/`
