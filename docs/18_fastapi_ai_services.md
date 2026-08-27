# FastAPI 构建 AI 服务

## 为什么选 FastAPI

FastAPI 是一个现代 Python Web 框架，基于 Starlette 和 Pydantic。它的优势：原生异步支持（适合 LLM 流式输出）、自动 API 文档（Swagger UI）、类型检查、高性能。是构建 AI 应用 API 服务的首选框架。

## OpenAI 兼容接口

OpenAI 的 API 格式已成为事实标准。构建兼容接口的好处是：可以直接用 OpenAI SDK、LangChain 等生态工具连接。核心接口是 /v1/chat/completions，支持 messages 数组和 stream 参数。

## 健康检查端点

生产级服务需要 /health 端点用于健康检查。它应快速返回（<10ms），不依赖外部服务。负载均衡器通过健康检查决定是否将流量路由到该实例。

## 统计端点

/stats 端点暴露运行时指标：总请求数、缓存命中数、缓存命中率、限流拒绝数。这对运维监控和性能调优至关重要。简历中可以引用这些真实指标证明项目效果。
