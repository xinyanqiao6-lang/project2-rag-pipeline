# HTTPX 快速开始

> 来源：HTTPX 官方文档 https://www.python-httpx.org/quickstart/

## 基本请求

HTTPX 是 Python 的下一代 HTTP 客户端，同时支持同步和异步。首先导入：

```python
import httpx
r = httpx.get('https://httpbin.org/get')
r = httpx.post('https://httpbin.org/post', data={'key': 'value'})
r = httpx.put('https://httpbin.org/put', data={'key': 'value'})
r = httpx.delete('https://httpbin.org/delete')
r = httpx.head('https://httpbin.org/get')
r = httpx.options('https://httpbin.org/get')
```

## URL 查询参数

用 `params` 关键字传入 URL 查询参数：

```python
params = {'key1': 'value1', 'key2': ['value2', 'value3']}
r = httpx.get('https://httpbin.org/get', params=params)
```

## 响应内容

HTTPX 自动处理响应内容的 Unicode 解码。`r.text` 是文本，`r.content` 是字节（适用于非文本响应）。可以通过 `r.encoding` 检查或覆盖解码所用的编码。

对于 JSON 响应，用 `r.json()` 直接解析：

```python
r = httpx.get('https://api.github.com/events')
data = r.json()
```

## 自定义请求头和发送数据

用 `headers` 关键字添加额外请求头。发送表单编码数据用 `data=` 参数，发送 JSON 数据用 `json=` 参数：

```python
r = httpx.post("https://httpbin.org/post", data={'key': 'value'})  # 表单
r = httpx.post("https://httpbin.org/post", json={'key': 'value'})  # JSON
```

上传文件使用 HTTP multipart 编码，通过 `files=` 参数。

## 响应状态码与异常

检查 HTTP 状态码：

```python
r = httpx.get('https://httpbin.org/get')
r.status_code  # 200
```

`raise_for_status()` 会对非 2xx 响应抛出异常：

```python
not_found = httpx.get('https://httpbin.org/status/404')
not_found.raise_for_status()  # 抛出 HTTPStatusError
```

HTTPX 最重要的异常类是 `RequestError`（发起请求时发生的任何错误的超类，含 `.request` 属性）和 `HTTPStatusError`（由 `raise_for_status()` 抛出，含 `.request` 和 `.response` 属性）。基类 `HTTPError` 包含这两类。

## 流式响应

对于大文件下载，可以用流式响应，避免一次性把整个响应体加载进内存：

```python
with httpx.stream("GET", "https://www.example.com") as r:
    for text in r.iter_text():
        print(text)
    # 或 iter_bytes()、iter_lines()、iter_raw()
```

## 重定向

默认情况下，HTTPX 不会对所有 HTTP 方法跟随重定向，但可显式启用。用 `follow_redirects=True` 参数开启。响应的 `history` 属性包含被跟随的重定向响应列表。

## 超时

HTTPX 默认对所有网络操作设置合理的超时（网络不活跃的默认超时为 5 秒），连接无法建立时会报错而不是无限挂起。可用 `timeout` 参数调整严格程度，或传 `None` 完全禁用。

## 认证

HTTPX 支持 Basic 和 Digest 认证。Basic 认证传一个 `(username, password)` 元组作为 `auth` 参数；Digest 认证用 `httpx.DigestAuth("user", "password")` 实例。
