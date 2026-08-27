# Embedding 模型详解

## 什么是 Embedding

Embedding 是将文本映射为稠密向量的过程。好的 Embedding 模型能让语义相近的文本在向量空间中距离也近，这是 RAG 检索的基础。Embedding 的质量直接决定了 RAG 系统的效果。

## 主流 Embedding 模型

中文场景的主流 Embedding 模型包括：

1. BAAI/bge-large-zh-v1.5：1024 维，中文效果优秀，免费可用，是本项目选择的模型。
2. BAAI/bge-m3：多语言模型，支持 100+ 语言，维度 1024。
3. text-embedding-ada-002：OpenAI 的闭源模型，1536 维。
4. moka-ai/m3e-base：512 维，中文效果也不错。

## Embedding 模型的选择

选择 Embedding 模型需要考虑：语言（中文优先 bge 系列）、维度（影响存储和检索速度）、成本（API 调用 vs 本地部署）、效果（在 MTEB 等基准测试上的表现）。

本项目使用硅基流动提供的 BAAI/bge-large-zh-v1.5，通过 API 调用，无需本地部署。

## Embedding 与检索质量

Embedding 质量直接影响检索质量。如果 Embedding 模型无法区分相似但不同的概念，RAG 系统就会检索到错误的内容。因此评估 Embedding 效果时，通常用 Top-K 命中率和 MRR 作为指标。
