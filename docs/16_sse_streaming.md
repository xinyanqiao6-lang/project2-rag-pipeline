# SSE 流式输出

## 什么是 SSE

SSE（Server-Sent Events）是一种允许服务器向客户端推送实时数据的 HTTP 协议。在 LLM 应用中，SSE 用于流式输出生成内容，用户体验远好于等待完整响应。

## SSE 的工作原理

SSE 基于 HTTP 长连接，服务器通过 Content-Type: text/event-stream 头声明这是一个 SSE 流。服务器逐条发送 event: data 行，客户端通过 EventSource API 接收。连接保持打开，直到服务器关闭。

## SSE vs WebSocket

SSE 是单向（服务器→客户端），WebSocket 是双向。LLM 应用中只需要服务器向客户端推送生成内容，SSE 足够且更简单。SSE 基于 HTTP，天然支持代理和负载均衡。WebSocket 需要额外的握手协议和连接管理。

## 在 FastAPI 中实现 SSE

FastAPI 通过 StreamingResponse 实现 SSE。将 LLM 的流式输出（如 OpenAI 兼容的 stream API）透传给客户端。每个 chunk 以 data: 前缀发送，以双换行结束。

## TTFB 优化

流式输出的关键指标是 TTFB（Time To First Byte，首字节延迟）。用户希望尽快看到第一个字。优化方法包括：使用流式推理（而非等待完整响应）；减少网络延迟（CDN、就近部署）；优化 prompt 长度减少首 token 计算时间。
