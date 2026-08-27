# LangChain 框架详解

## LangChain 是什么

LangChain 是一个用于构建大语言模型应用的开源框架。它提供了模块化的组件，帮助开发者快速构建 RAG、Agent、对话系统等应用。LangChain 支持 Python 和 JavaScript。

## 核心组件

LangChain 的核心组件包括：

1. Document Loaders：从各种来源加载文档（PDF、网页、数据库等）。
2. Text Splitters：将长文档切分成适合 Embedding 的文本块。支持递归字符切分、Markdown 切分等多种策略。
3. Embeddings：将文本转为向量。支持 OpenAI、HuggingFace、硅基流动等多种 Embedding 服务。
4. Vector Stores：向量存储与检索。支持 FAISS、Chroma、Milvus、Pinecone 等。
5. Chains：将多个组件串联起来，如 RAG 链（retriever → prompt → LLM → output）。
6. Agents：让 LLM 自主决定调用哪些工具完成任务。

## LangChain 的优势

LangChain 的优势在于丰富的生态和组件复用。开发者可以快速切换不同的大模型、Embedding 模型、向量数据库，而不需要重写代码。LangChain 的 LCEL（LangChain Expression Language）使得链的构建更加灵活。

## 在本项目中的使用

本项目使用 LangChain 的 Text Splitters 实现三种切分策略，使用 FAISS 作为向量存储，并构建 RAG 问答链。LangChain 的模块化设计使得切分策略对比和检索质量评估变得简单。
