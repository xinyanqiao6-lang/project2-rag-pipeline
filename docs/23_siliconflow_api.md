# 硅基流动 API

## 硅基流动简介

硅基流动（SiliconFlow）是国内领先的 AI 模型推理服务提供商，提供多种开源大模型的 API 服务。它的优势是模型丰富、价格低（部分免费）、国内访问速度快、兼容 OpenAI API 格式。

## 支持的模型

硅基流动支持多种模型：Qwen2.5 系列（7B/14B/72B）、DeepSeek 系列、GLM 系列、BAAI Embedding 系列等。免费模型包括 Qwen2.5-7B-Instruct 和 BAAI/bge-large-zh-v1.5，适合学习和原型开发。

## API 调用方式

硅基流动 API 兼容 OpenAI 格式。调用方式与 OpenAI SDK 完全一致，只需替换 base_url 和 api_key。支持非流式和流式（SSE）两种模式。

## Embedding API

Embedding API 端点为 /v1/embeddings，支持 BAAI/bge-large-zh-v1.5 等模型。输入文本，输出向量。请求格式与 OpenAI Embedding API 一致。

## 在本项目中的使用

项目1 使用硅基流动的 Qwen2.5-7B-Instruct 构建对话 API 服务。项目2 使用同一平台提供的 BAAI/bge-large-zh-v1.5 做 Embedding，Qwen2.5-7B-Instruct 做 RAG 问答。两个项目共用一个 API Key，成本为零。
