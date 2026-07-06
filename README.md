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

默认 API 监听 `0.0.0.0:8000`。

FastAPI 文档地址：

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## 配置

主要配置在 `config.py`：

- `DB_CONFIG`: Redis 地址、端口、库和 key。
- `parserList`: 代理源和 XPath 解析规则。
- `TEST_IP`: 代理检测使用的 IP 回显接口，默认 `https://httpbin.org/ip`。
- `MAX_PROXY_NUMBER`: Redis 中最多保留的代理数量。
- `CHECK_TIME`: 抓取轮次和检测轮次的等待间隔。
- `TEST_NUMBER`: 代理检测进程数。

也可以用环境变量覆盖部分配置：

```bash
set IP_PROXY_POOL_API_PORT=8000
set IP_PROXY_POOL_TEST_WORKERS=3
python run.py
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


代理来源：

https://www.zdaye.com/free/

https://francevpn.github.io/free-proxy/page-3.htm

