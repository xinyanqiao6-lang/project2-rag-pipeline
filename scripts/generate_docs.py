"""
生成 24 份 AI 技术文档作为 RAG 语料库。
每份文档有真实技术内容，涵盖 RAG/Transformer/LangChain/FAISS/Embedding 等主题。
运行：python scripts/generate_docs.py
"""
import os
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"

# 24 份文档，每份有标题+多段正文
DOCUMENTS = {
    "01_rag_overview.md": """# RAG（检索增强生成）概述

## 什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合检索和生成的大模型应用架构。它通过从外部知识库中检索相关文档片段，将这些片段作为上下文输入给大语言模型，从而生成更准确、更可靠的回答。

RAG 的核心思想是：不依赖大模型自身的参数化记忆，而是通过外部知识库提供事实依据。这样可以有效缓解大模型的幻觉问题，同时使知识可以随时更新而无需重新训练模型。

## RAG 的工作流程

一个标准的 RAG 系统包含三个核心阶段：

1. 索引阶段（Indexing）：将原始文档进行解析、清洗、切分，然后通过 Embedding 模型将文本块向量化，最后存入向量数据库（如 FAISS、Milvus）。

2. 检索阶段（Retrieval）：用户提问后，将问题同样向量化，在向量数据库中检索语义最相似的 Top-K 文本块。

3. 生成阶段（Generation）：将检索到的文本块作为上下文，与用户问题拼接后输入给大语言模型，生成最终回答。

## RAG 的优势

RAG 相比纯大模型直接生成有以下优势：知识可随时更新（只需更新知识库）；可溯源（回答基于检索到的具体文档）；减少幻觉（有事实依据）；数据隐私可控（知识库在本地）；成本远低于微调。

## RAG 的挑战

RAG 也面临诸多挑战：检索质量取决于切分策略和 Embedding 模型；长文档切分不当会丢失上下文；多轮对话中的上下文管理复杂；实时性要求高时需要优化检索延迟。
""",

    "02_transformer_architecture.md": """# Transformer 架构详解

## Transformer 的核心组件

Transformer 是 2017 年 Google 在论文《Attention Is All You Need》中提出的架构，它完全基于注意力机制，摒弃了 RNN 和 CNN。Transformer 由编码器（Encoder）和解码器（Decoder）两部分组成。

编码器由多个相同的层堆叠而成，每层包含两个子层：多头自注意力机制（Multi-Head Self-Attention）和前馈神经网络（Feed-Forward Network）。每个子层都使用残差连接（Residual Connection）和层归一化（Layer Normalization）。

解码器与编码器类似，但额外增加了一个交叉注意力层（Cross-Attention），用于关注编码器的输出。解码器的自注意力层是掩码的（Masked），确保生成时只能看到已生成的内容。

## 自注意力机制

自注意力机制是 Transformer 的核心。它通过三个矩阵 Q（Query）、K（Key）、V（Value）计算注意力权重。公式为：Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V。

缩放因子 sqrt(d_k) 用于防止内积值过大导致 softmax 梯度消失。多头注意力则是将 Q、K、V 分成多个头并行计算，最后拼接，使模型能同时关注不同维度信息。

## 位置编码

由于 Transformer 没有循环结构，无法感知序列顺序，因此需要位置编码。原始论文使用正弦/余弦函数生成位置编码，与词嵌入相加。后续的模型如 BERT 使用可学习的位置编码，而 ALiBi 和 RoPE 则是更先进的位置编码方案。

## Transformer 在大模型中的应用

GPT 系列只使用 Transformer 的解码器部分，BERT 只使用编码器部分，而 T5 和原始 Transformer 一样使用编码器-解码器结构。Qwen2.5、LLaMA 等主流大语言模型都基于 Transformer 架构，并在此基础上进行了大量优化。
""",

    "03_attention_mechanism.md": """# 注意力机制（Attention Mechanism）

## 注意力机制的本质

注意力机制源于人类视觉系统的启发：人类在观察事物时会聚焦于重要区域而忽略其他。在深度学习中，注意力机制是一种让模型动态分配不同输入权重的机制。

## 从 Seq2Seq 到 Attention

早期 Seq2Seq 模型用编码器将输入序列压缩成一个固定长度的上下文向量，这在长序列上信息丢失严重。注意力机制（Bahdanau, 2014）解决了这个问题：解码时动态关注编码器的不同位置，而非只用一个向量。

## 缩放点积注意力

Transformer 使用的缩放点积注意力公式为：softmax(QK^T / sqrt(d_k)) * V。其中 Q 是查询矩阵，K 是键矩阵，V 是值矩阵。缩放因子 sqrt(d_k) 防止内积过大导致梯度消失。

## 多头注意力

多头注意力将 Q、K、V 拆分成 h 个头，每个头独立计算注意力，最后拼接并做线性变换。这使得模型能同时从不同表示子空间捕获信息。例如 8 头注意力可以同时关注语法、语义、实体等不同方面。

## 注意力在 RAG 中的应用

在 RAG 系统中，注意力机制体现在两个层面：Embedding 模型内部用自注意力编码文本语义；大语言模型在生成回答时用交叉注意力关注检索到的上下文。
""",

    "04_bert_model.md": """# BERT 模型详解

## BERT 简介

BERT（Bidirectional Encoder Representations from Transformers）是 Google 于 2018 年提出的预训练语言模型。与 GPT 的单向生成不同，BERT 使用双向 Transformer 编码器，能同时利用上下文信息。

## 预训练任务

BERT 使用两个预训练任务：掩码语言模型（MLM）和下一句预测（NSP）。MLM 随机遮盖输入词，让模型预测被遮盖的词。NSP 判断两句话是否是连续的。这两个任务使 BERT 学到了丰富的双向语言表示。

## BERT 的变体

BERT 衍生出多个变体：RoBERTa 去掉了 NSP 任务并增大训练数据；ALBERT 用参数共享减少参数量；DistilBERT 通过知识蒸馏压缩模型。这些变体在不同场景下各有优势。

## BERT 与 Embedding

BERT 及其变体常被用作 Embedding 模型。但原始 BERT 的 [CLS] token 表示并不适合直接做语义相似度计算。后续的 Sentence-BERT 通过对比学习改进了这一点，使 BERT 能输出高质量的句向量。bge 系列也基于类似思路训练，是当前中文 Embedding 的主流选择。
""",

    "05_gpt_family.md": """# GPT 模型家族

## GPT 的演进

GPT（Generative Pre-trained Transformer）是 OpenAI 提出的生成式预训练模型。GPT-1 首次验证了"预训练+微调"范式的可行性。GPT-2 展示了 zero-shot 能力。GPT-3 以 1750 亿参数展示了 few-shot 学习的强大能力。

GPT-4 引入了多模态能力，可以处理图像和文本。GPT-4o 进一步实现了实时语音交互。GPT 系列只使用 Transformer 的解码器部分，通过自回归方式生成文本。

## In-Context Learning

GPT-3 的最大贡献是展示了大模型的上下文学习能力。通过在 prompt 中给出少量示例，模型就能学会新任务，无需微调。这被称为 few-shot learning。

## 从 GPT 到 Qwen

Qwen 是阿里巴巴推出的大语言模型系列。Qwen2.5 是最新版本，支持中英文，在多项基准测试上表现优秀。Qwen2.5-7B 是中小参数量版本，适合部署在消费级硬件上，也是硅基流动等平台提供的免费模型之一。

## 开源大模型生态

除了 Qwen，主流开源大模型还包括 Meta 的 LLaMA、Mistral AI 的 Mistral/Mixtral、DeepSeek 等。这些模型推动了 AI 应用的发展，降低了使用门槛。
""",

    "06_langchain_framework.md": """# LangChain 框架详解

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
""",

    "07_faiss_vector_search.md": """# FAISS 向量检索

## FAISS 简介

FAISS（Facebook AI Similarity Search）是 Meta 开源的高效相似度搜索库，专门用于稠密向量检索。它支持百万级向量的快速检索，是 RAG 系统中最常用的向量检索引擎之一。

## FAISS 的索引类型

FAISS 提供多种索引类型，适应不同场景：

1. Flat（暴力检索）：精确计算，精度最高但速度慢，适合小数据集。
2. IVF（倒排文件）：先聚类再在簇内检索，速度更快，精度略有损失。
3. HNSW（分层可导航小世界图）：基于图的近似最近邻检索，速度和精度的良好平衡。
4. PQ（乘积量化）：压缩向量减少内存，适合超大规模数据。

## FAISS vs Milvus

FAISS 是一个库，需要自行管理数据持久化和分布式扩展。Milvus 是一个完整的向量数据库，支持分布式、高可用、数据持久化。对于项目级 RAG 系统，FAISS 足够；对于生产级百万级文档系统，Milvus 更合适。

## 在 RAG 中的使用

在 RAG 系统中，FAISS 的工作流程是：将每个文本块通过 Embedding 模型转为向量，存入 FAISS 索引。查询时，将问题同样向量化，用 FAISS 检索 Top-K 最相似的文本块。检索速度通常在毫秒级。

## 性能考量

FAISS 的检索延迟主要受向量维度、索引类型、数据量影响。bge-large-zh 输出 1024 维向量，Flat 索引在 1000 个向量上检索延迟约 1-5ms。增大到百万级时，需要用 IVF 或 HNSW 索引。
""",

    "08_embedding_models.md": """# Embedding 模型详解

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
""",

    "09_prompt_engineering.md": """# 提示词工程（Prompt Engineering）

## 什么是提示词工程

提示词工程是通过设计和优化输入给大语言模型的提示词，来获得更好输出的技术。它不需要修改模型参数，而是通过改变输入方式来引导模型行为。

## 核心技巧

1. 角色设定：给模型一个明确角色，如"你是一个 RAG 系统的问答助手"。
2. 上下文提供：将检索到的文档作为上下文，要求模型基于上下文回答。
3. 格式约束：指定输出格式，如"用 Markdown 格式回答，引用来源"。
4. 少样本示例：给出几个问答示例，引导模型学习输出风格。
5. 思维链：要求模型逐步推理，如"请一步步分析"。

## RAG 中的提示词设计

RAG 系统的提示词通常包含：系统角色、检索到的上下文、用户问题、输出要求。例如：

"你是一个知识库问答助手。以下是从知识库中检索到的相关信息：{context}。请基于上述信息回答用户的问题。如果信息不足，请说明。问题：{question}"

## 提示词优化的实践

提示词优化需要反复迭代。实践中，应该先测试基线提示词，然后逐步调整。记录每次修改的效果（命中率、回答质量评分），找到最优配置。结构化的提示词模板比自由文本更稳定可复现。
""",

    "10_finetuning_lora.md": """# 微调与 LoRA

## 为什么需要微调

预训练大模型虽然通用性强，但在特定任务上可能不如微调后的模型。微调通过在下游任务数据上继续训练模型，使其适应特定领域、风格或任务。

## 全量微调 vs 参数高效微调

全量微调更新模型所有参数，效果最好但成本极高（需要大量 GPU 显存）。参数高效微调（PEFT）只更新少量参数，成本低效果好。LoRA 是最流行的 PEFT 方法。

## LoRA 原理

LoRA（Low-Rank Adaptation）在模型权重矩阵旁增加一个低秩分解矩阵。训练时只更新这个低秩矩阵，原始权重冻结。推理时将低秩矩阵与原始权重合并，不增加推理延迟。

LoRA 的关键参数：rank（r）决定低秩矩阵的大小，通常取 8-64；alpha 是缩放因子。rank 越大表达能力越强但参数也越多。

## QLoRA

QLoRA 在 LoRA 基础上引入 4-bit 量化，进一步减少显存占用。这使得在单张消费级 GPU 上微调 70B 级别的模型成为可能。QLoRA 是目前资源受限场景下微调大模型的首选方案。

## 微调 vs RAG

微调适合：需要改变模型风格/格式/领域深度知识的场景。RAG 适合：知识需要频繁更新、需要溯源、数据隐私的场景。两者可以结合使用。
""",

    "11_vector_databases.md": """# 向量数据库

## 为什么需要向量数据库

RAG 系统需要存储和检索大量向量，传统数据库无法高效处理向量相似度搜索。向量数据库专门为此设计，支持 ANN（近似最近邻）搜索，能在百万级向量中毫秒返回结果。

## 主流向量数据库

1. FAISS：Meta 开源的库，非数据库，适合单机百万级。
2. Milvus：开源分布式向量数据库，支持十亿级向量，适合生产环境。
3. Pinecone：闭源托管服务，零运维，适合快速上线。
4. Chroma：轻量级，适合原型开发。
5. Qdrant：Rust 编写，性能优秀，支持过滤检索。

## 选择标准

选择向量数据库需要考虑：数据规模（FAISS 适合百万以下，Milvus 适合十亿级）；是否需要分布式和高可用；预算（自建 vs 托管）；检索延迟要求；是否需要元数据过滤。

## 元数据过滤

高级向量数据库支持在向量检索时做元数据过滤。例如只检索某个时间范围、某个类别的文档。这在实际 RAG 应用中很重要，可以显著提升检索精度。
""",

    "12_ai_agents.md": """# AI Agent 与工作流

## 什么是 AI Agent

AI Agent 是能够自主规划、使用工具、执行多步骤任务的大模型应用。与简单的问答不同，Agent 能根据用户需求分解任务、选择工具、观察结果、循环执行直到完成。

## Agent 的核心组件

1. 规划：将复杂任务分解为子任务。常用技术如 ReAct（Reasoning + Acting）框架。
2. 工具使用：调用外部 API、数据库、搜索引擎等。如 Function Calling。
3. 记忆：短期记忆（对话历史）和长期记忆（向量数据库存储的经验）。
4. 执行循环：思考→行动→观察→调整→再行动。

## Agent vs RAG

RAG 是单次检索+生成，Agent 是多步骤自主执行。Agent 可以在执行过程中调用 RAG 作为工具。例如：Agent 接到"总结最新的 AI 论文"任务后，先搜索论文（RAG），然后逐篇总结，最后汇总。

## 多 Agent 协作

复杂任务可以用多个 Agent 协作完成。如 LangGraph 支持构建多 Agent 工作流：一个 Agent 负责检索，一个负责分析，一个负责写作。每个 Agent 专注自己的职责，通过消息传递协作。
""",

    "13_chain_of_thought.md": """# 思维链推理（Chain-of-Thought）

## 什么是思维链

思维链（Chain-of-Thought, CoT）是一种让大语言模型逐步推理的技术。通过要求模型展示推理过程，而不是直接给出答案，可以显著提升复杂推理任务的表现。

## CoT 的原理

大模型直接预测答案时，复杂推理容易出错。但如果让模型先输出推理步骤，每一步的中间结果会作为下一步的上下文，形成更好的推理链。这类似于人类解题时先列公式再算结果。

## 零样本 CoT

最简单的 CoT 方法是在 prompt 末尾加上"让我们一步步思考"。这无需额外示例就能激活模型的推理能力。研究表明这在数学、逻辑推理任务上能提升 10-30% 的准确率。

## 少样本 CoT

在 prompt 中给出带推理过程的示例，效果更好。例如：问题→推理步骤→答案的格式。模型会模仿这个格式输出推理过程。

## Tree-of-Thought

Tree-of-Thought（ToT）是 CoT 的进阶版本，它让模型生成多个推理分支，评估每个分支的前景，选择最优路径。这适合更复杂的规划类任务，但计算成本更高。
""",

    "14_quantization.md": """# 模型量化与压缩

## 为什么需要量化

大语言模型参数量巨大（7B 模型约 14GB FP16），部署成本高。量化通过降低参数精度来减少模型体积和推理成本。例如将 FP16 量化为 INT8 可以减少 50% 显存，INT4 可以减少 75%。

## 量化方法

1. 对称量化：将权重对称映射到整数范围，简单但精度损失较大。
2. GPTQ：基于二阶信息的量化方法，精度损失小，广泛使用。
3. AWQ：激活感知量化，保护重要权重，精度优秀。
4. GGUF/llama.cpp：面向 CPU 推理的量化格式，支持 2-8 bit 量化。

## 量化的权衡

量化是精度与成本的权衡。4-bit 量化通常保持 95%+ 的原始模型性能，但可以显著降低部署门槛。8-bit 量化几乎无损，但节省的显存不如 4-bit 多。

## 量化在 RAG 中的应用

在 RAG 系统中，量化可以应用于两个组件：生成模型（用量化后的 LLM 降低推理成本）和 Embedding 模型（量化 Embedding 减少向量存储空间）。但 Embedding 量化需要谨慎，因为可能影响检索精度。
""",

    "15_vllm_inference.md": """# vLLM 推理优化

## vLLM 简介

vLLM 是加州大学伯克利分校开源的大语言模型推理引擎，通过 PagedAttention 技术大幅提升了推理吞吐量。它是目前最流行的 LLM 推理框架之一。

## PagedAttention

vLLM 的核心创新是 PagedAttention。它借鉴操作系统的虚拟内存管理，将 KV Cache 按固定大小的"页"管理，避免了传统推理引擎中 KV Cache 的内存碎片和浪费。这使得并发请求的 KV Cache 管理效率大幅提升。

## 连续批处理

vLLM 支持连续批处理（Continuous Batching），不同于传统的静态批处理需要等所有请求完成，vLLM 可以在每个 token 生成时动态加入新请求或移除已完成的请求，最大化 GPU 利用率。

## 吞吐量对比

相比 Hugging Face Transformers，vLLM 可以提升 2-24 倍的吞吐量。在多用户并发场景下优势更明显。但单请求延迟可能不如 TensorRT-LLM 等优化框架。

## vLLM vs 云 API

对于本项目，使用硅基流动的云 API 而非自部署 vLLM，主要原因是成本和运维：无需购买 GPU、无需运维推理服务、按量付费。但如果数据隐私要求高或用量极大，自部署 vLLM 是更好的选择。
""",

    "16_sse_streaming.md": """# SSE 流式输出

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
""",

    "17_redis_caching.md": """# Redis 缓存策略

## 为什么需要缓存

在 AI 应用中，缓存可以显著降低延迟和成本。相同的问题往往会被反复提问，缓存命中时可以直接返回缓存的回答，无需调用 LLM API。缓存的命中率通常在 30-80%。

## 缓存键设计

缓存键的设计至关重要。本项目使用 model + messages + temperature 的组合做 SHA256 哈希作为缓存键。这样相同问题和参数会命中缓存，但任何参数变化都不会命中，保证正确性。

## TTL 策略

TTL（Time To Live）决定缓存过期时间。过短则命中率低，过长则可能返回过期信息。本项目设 TTL 为 3600 秒（1 小时）。对于知识库类的 RAG 系统，TTL 可以更长，因为知识不会频繁变化。

## 滑动窗口限流

Redis 的 ZSET 数据结构非常适合实现滑动窗口限流。用 ZSET 存储请求时间戳，每次请求时先清理过期记录再计数，超过阈值则拒绝。相比固定窗口算法，滑动窗口没有边界突变问题。

## 缓存穿透与击穿

缓存穿透指大量请求查不到缓存也查不到数据库。缓存击穿指热点 key 过期瞬间大量请求涌入。防护方法：空结果也缓存（短 TTL）、互斥锁、热点 key 永不过期。
""",

    "18_fastapi_ai_services.md": """# FastAPI 构建 AI 服务

## 为什么选 FastAPI

FastAPI 是一个现代 Python Web 框架，基于 Starlette 和 Pydantic。它的优势：原生异步支持（适合 LLM 流式输出）、自动 API 文档（Swagger UI）、类型检查、高性能。是构建 AI 应用 API 服务的首选框架。

## OpenAI 兼容接口

OpenAI 的 API 格式已成为事实标准。构建兼容接口的好处是：可以直接用 OpenAI SDK、LangChain 等生态工具连接。核心接口是 /v1/chat/completions，支持 messages 数组和 stream 参数。

## 健康检查端点

生产级服务需要 /health 端点用于健康检查。它应快速返回（<10ms），不依赖外部服务。负载均衡器通过健康检查决定是否将流量路由到该实例。

## 统计端点

/stats 端点暴露运行时指标：总请求数、缓存命中数、缓存命中率、限流拒绝数。这对运维监控和性能调优至关重要。简历中可以引用这些真实指标证明项目效果。
""",

    "19_docker_ml_deployment.md": """# Docker 机器学习部署

## 为什么用 Docker

Docker 将应用及其依赖打包为容器，确保环境一致性。在 ML 部署中，Python 依赖版本冲突是常见问题，Docker 从根本上解决了这个问题。

## Dockerfile 最佳实践

1. 使用 slim 基础镜像减小体积。
2. 先 COPY requirements.txt 再 pip install，利用层缓存。
3. 用 .dockerignore 排除不必要的文件。
4. 非 root 用户运行提升安全性。
5. EXPOSE 端口声明。

## Docker Compose 多容器编排

Docker Compose 可以编排多个容器。在 AI 服务中，通常需要 API 容器 + Redis 容器。docker-compose.yml 定义服务间依赖关系、网络、卷挂载。一键 docker compose up 启动全部服务。

## 镜像优化

Python ML 镜像通常较大（>1GB）。优化方法：多阶段构建（builder 阶段编译，runtime 阶段只保留运行时）；使用 .dockerignore 排除测试数据和缓存；选择 alpine 或 slim 基础镜像。
""",

    "20_hf_spaces.md": """# Hugging Face Spaces 部署

## HF Spaces 简介

Hugging Face Spaces 是一个免费托管 ML 应用演示的平台。支持 Gradio 和 Streamlit 框架。适合部署 RAG 系统的在线 Demo，让面试官和招聘方直接体验。

## Gradio 部署

Gradio 是一个 Python 库，可以快速构建 ML 应用的 Web 界面。几行代码就能创建一个交互式界面。在 HF Spaces 上部署 Gradio 应用，只需在仓库根目录放一个 app.py 和 requirements.txt。

## 部署步骤

1. 在 Hugging Face 创建 Space，选择 Gradio SDK。
2. 将项目代码推送到 Space 仓库。
3. 确保 requirements.txt 包含所有依赖。
4. 等待自动构建部署，获得公开 URL。

## 免费 CPU 部署的限制

HF Spaces 免费版使用 CPU，不适合运行大模型推理。解决方案：Demo 调用云 API（如硅基流动）而非本地推理。这样可以充分利用免费 CPU 资源，只在需要时调用 API。

## 部署的意义

在线 Demo 是简历的重要加分项。简历中附一个可访问的 URL，让招聘方直接体验你的产品，比文字描述更有说服力。HF Spaces 是零成本部署 Demo 的最佳选择。
""",

    "21_mrr_evaluation.md": """# 检索质量评估指标

## 为什么需要评估

RAG 系统的效果取决于检索质量，而检索质量取决于切分策略和 Embedding 模型。没有量化评估，就无法判断哪种策略更好。评估指标使优化有据可依。

## Top-K 命中率

Top-K 命中率是指正确答案在检索的 Top-K 个结果中的比例。例如 Top-5 命中率 80% 意味着 80% 的问题的正确答案出现在前 5 个检索结果中。这是最直观的检索质量指标。

## MRR（平均倒数排名）

MRR（Mean Reciprocal Rank）更精细地衡量排名质量。对于每个问题，找到正确答案在 Top-K 中的排名 r，计算 1/r。所有问题的 1/r 取平均就是 MRR。

例如正确答案在第 1 位得 1.0，第 2 位得 0.5，第 3 位得 0.33。MRR 越高说明正确答案排名越靠前。

## 命中率 vs MRR

命中率只关心正确答案是否在 Top-K 中（二元），MRR 还关心排名位置。两个系统可能有相同的 Top-5 命中率，但 MRR 不同的系统实际体验不同：正确答案排在第 1 位比第 5 位好得多。

## 评估流程

1. 人工标注 10+ 个测试问题，每个标注正确的答案文档。
2. 对每个问题用不同策略检索 Top-K。
3. 计算命中率和 MRR。
4. 记录检索延迟。
5. 对比表格，选择最优策略。
""",

    "22_text_chunking.md": """# 文本切分策略

## 为什么切分很重要

RAG 系统中，文本切分直接影响检索质量。切分太长则单个块包含太多信息，检索精度下降；切分太短则上下文断裂，语义不完整。好的切分策略要在精度和完整性间取得平衡。

## 固定长度切分

固定长度切分按字符数等分，设置 overlap 防止语义断裂。优点是简单可控，块大小一致。缺点是可能在句子中间切断，破坏语义完整性。适合格式统一的文档。

## 递归字符切分

递归字符切分按分隔符层次切分：先用段落分隔（\\n\\n），再换行（\\n），再标点（。！？）。优先在自然边界处切分，保持语义完整。LangChain 的 RecursiveCharacterTextSplitter 是最常用的切分器。

## 语义切分

语义切分使用更小的 chunk_size 和 overlap，适合需要细粒度检索的场景。小块更精准但可能丢失上下文。适合 FAQ 类文档。

## 切分策略的权衡

选择切分策略需要考虑：文档类型（技术文档 vs FAQ）、平均段落长度、检索精度要求。最佳实践是实际测试不同策略，用命中率和 MRR 量化对比，而非凭直觉选择。这正是本项目的核心价值。
""",

    "23_siliconflow_api.md": """# 硅基流动 API

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
""",

    "24_qwen25_model.md": """# Qwen2.5 模型

## Qwen2.5 简介

Qwen2.5 是阿里巴巴通义千问团队发布的开源大语言模型系列。包含 0.5B、1.5B、7B、14B、32B、72B 等多个参数量版本，支持中英文。在多项基准测试上达到或超过同级别模型。

## Qwen2.5-7B 特点

Qwen2.5-7B-Instruct 是 7B 参数量级别的指令微调版本。它支持 32K 上下文窗口，在代码生成、数学推理、中文理解等方面表现优秀。硅基流动提供免费 API 调用，适合学习和项目开发。

## 在 AI 应用中的使用

Qwen2.5-7B 适合以下场景：RAG 系统的生成模型（基于检索结果生成回答）；对话系统（多轮对话理解）；代码助手（代码生成和解释）；文档摘要（长文档压缩）。它的 32K 上下文窗口可以容纳较多检索结果。

## 与其他模型的对比

Qwen2.5-7B 在中文场景下优于同级别的 LLaMA-3-8B（中文训练数据少）。DeepSeek-V3 在推理任务上更强但参数量更大。对于需要中文理解的项目，Qwen 系列是目前最好的开源选择之一。

## 模型选择建议

选择模型需要考虑：任务类型（对话 vs 推理 vs 代码）、语言（中文优先 Qwen/DeepSeek）、资源（API 调用 vs 本地部署）、成本（免费模型 vs 付费模型）。本项目使用免费的 Qwen2.5-7B，在硅基流动平台上调用，平衡了效果和成本。
""",
}


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, content in DOCUMENTS.items():
        path = DOCS_DIR / filename
        path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"✅ 生成 {len(DOCUMENTS)} 份文档到 {DOCS_DIR}")
    total_chars = sum(len(c) for c in DOCUMENTS.values())
    print(f"   总字符数：{total_chars:,}")
    print(f"   平均每份：{total_chars // len(DOCUMENTS):,} 字符")


if __name__ == "__main__":
    main()
