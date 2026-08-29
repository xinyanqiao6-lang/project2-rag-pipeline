# 项目2：RAG 数据处理管道

> 构建 RAG（检索增强生成）数据处理管道，实现文档解析 → 文本清洗 → 多策略切分 → Embedding → FAISS 检索全链路，并对比 3 种切分策略的检索效果。
> 语料库为 **7 份真实开源官方文档**（FastAPI/Pydantic/HTTPX/Docker/LangChain），来源见 `SOURCES.md`。

## 架构图

```mermaid
graph TD
    A[文档库 docs/] --> B[文档解析+清洗]
    B --> C{切分策略}
    C -->|固定长度| D1[Fixed Splitter<br/>chunk=500 overlap=50]
    C -->|段落递归| D2[Recursive Splitter<br/>中文标点层次切分]
    C -->|语义细粒度| D3[Semantic Splitter<br/>chunk=200 overlap=30]
    D1 --> E[Embedding<br/>bge-large-zh-v1.5]
    D2 --> E
    D3 --> E
    E --> F[FAISS 向量索引]
    F --> G[检索 Top-K]
    G --> H[上下文拼接]
    H --> I[LLM 生成回答<br/>Qwen2.5-7B-Instruct]
    I --> J[回答 + 来源]

    K[10 个标注问题] --> G
    K --> L[命中率/MRR 评估]
    G --> L
    L --> M[策略对比表 CSV]
```

## 技术栈

| 组件 | 技术 | 说明 |
|---|---|---|
| 文档解析 | Python + regex | 支持 .md/.txt，清洗去空白统一换行 |
| 切分策略 | 自实现 3 种 | 固定长度 / 段落递归 / 语义细粒度 |
| Embedding | 硅基流动 API | BAAI/bge-large-zh-v1.5（1024 维） |
| 向量检索 | FAISS (IndexFlatIP) | 精确检索，cosine 相似度 |
| RAG 生成 | 硅基流动 API | Qwen2.5-7B-Instruct |
| Web 界面 | Gradio | 问答 Demo |
| 评估 | 自实现 | Top-K 命中率 + MRR + 检索延迟 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入硅基流动 API Key
```

### 3. 语料库

语料已就位：`docs/` 下 7 份真实开源官方文档（来源见 `SOURCES.md`），无需生成。

### 4. 运行检索质量评估

```bash
python scripts/evaluate.py          # 真实 API
python scripts/evaluate.py --mock  # Mock 模式（无需 Key）
```

输出：3 策略对比表（命中率 / MRR / 延迟）+ CSV + JSON

### 5. 启动 RAG 问答 Demo

```bash
python app.py
# 打开 http://127.0.0.1:7860
```

## 项目结构

```
project2-rag-pipeline/
├── app/
│   ├── config.py              # 配置
│   ├── document_processor.py  # 文档解析+清洗
│   ├── chunker.py             # 3 种切分策略
│   ├── embedder.py            # 硅基流动 Embedding 客户端
│   ├── indexer.py             # FAISS 向量索引
│   └── rag_chain.py           # RAG 问答链
├── scripts/
│   └── evaluate.py            # 检索质量评估（命中率/MRR/延迟）
├── docs/                      # 语料库（7 份真实开源文档 .md）
├── results/                   # 评估结果输出
├── app.py                     # Gradio 界面
├── SOURCES.md                 # 语料来源清单
├── requirements.txt
├── .env.example
└── README.md
```

## 3 种切分策略说明

| 策略 | 参数 | 特点 | 适用场景 |
|---|---|---|---|
| **fixed** (固定长度) | chunk=500, overlap=50 | 按字符数等分+滑动窗口 | 格式统一的文档 |
| **recursive** (段落递归) | chunk=500, overlap=50 | 按中文标点层次切分，优先自然边界 | 技术文档（推荐） |
| **semantic** (语义细粒度) | chunk=200, overlap=30 | 小块细粒度 | FAQ 类文档 |

## 评估指标说明

### Top-K 命中率
正确答案文档出现在检索 Top-K 结果中的问题占比。Top-5 命中率 80% = 80% 的问题正确答案在前 5 个检索结果中。

### MRR (Mean Reciprocal Rank)
衡量正确答案的排名质量。每个问题的得分为 1/rank（第 1 位=1.0，第 2 位=0.5，第 5 位=0.2），取平均。MRR 越高说明正确答案排名越靠前。

### 检索延迟
单次检索的耗时（毫秒），包括查询 Embedding + FAISS 搜索。报告平均值和 P95。

## 面试必考题参考

### Q1: 3 种切分策略各有什么优劣？
- **固定长度**：简单可控，块大小一致，但可能切断语义。
- **段落递归**：优先在自然边界切分，语义完整性好，是最常用的策略。
- **语义细粒度**：检索精度高但上下文可能不足，适合 FAQ。

### Q2: 为什么选 bge-large-zh-v1.5？
- 中文效果优秀（C-MTEB 基准排名前列）
- 1024 维，存储和检索效率好
- 硅基流动免费提供 API，无需本地部署

### Q3: 命中率和 MRR 有什么区别？
- 命中率只看正确答案是否在 Top-K 中（二元判断）
- MRR 还看排名位置（第 1 位和第 5 位得分不同）
- 两个系统可能命中率相同但 MRR 不同

### Q4: FAISS vs Milvus？
- FAISS 是库，单机百万级，无分布式
- Milvus 是数据库，支持分布式、十亿级、高可用
- 项目级用 FAISS 足够，生产级用 Milvus

### Q5: 100 万文档怎么扩？
- 用 IVF 或 HNSW 索引替代 Flat
- 分片部署多 FAISS 实例
- 或直接迁移到 Milvus 分布式

### Q6: 生成的答案出现重复字符（"外部线线线池"）怎么排查？
- **先定位是不是 RAG 的问题**：看检索端 Top-1 来源是否准确——实测 3/3 = 100% 命中正确文档，说明检索完全正常，问题不在管道
- **根因**：7B 小模型在长 prompt 下的 repetition 退化（重复 token），属生成端模型能力问题
- **对策一（实测有效）**：调 `repetition_penalty`，**1.15 最优**；注意不是越大越好，1.3 会导致语义崩溃
- **对策二**：换更大的模型——生成端与检索管道解耦，上游 LLM 可插拔，本项目改 `LLM_MODEL` 环境变量即可
- **对策三**：压缩上下文（降低 Top-K 或缩短 chunk），减轻长上下文压力

## 真实指标（2026-08-29 实测，真实开源语料）

| 策略 | 块数 | 均长 | Top-5 命中率 | MRR | 均延迟 | P95 延迟 |
|---|---|---|---|---|---|---|
| fixed | 33 | 437 | 100 % | 1.0000 | 142.5 ms | 511.2 ms |
| recursive | 32 | 447 | 100 % | 1.0000 | 159.3 ms | 328.6 ms |
| semantic | 88 | 176 | 100 % | 1.0000 | 91.8 ms | 106.3 ms |

> 最优策略：语义切分（命中率/MRR 满分，延迟最优 91.8ms；但块数最多、存储成本高）
> 实用推荐：段落递归（块数最少 32 块，延迟可接受，性价比最优）

## 端到端问答验证（2026-08-29 真实 API 实测）

用 evaluate.py 中已标注的 3 个问题（覆盖 3 份不同文档）跑完整链路 检索→prompt→Qwen2.5-7B→回答，重复 3 轮：

| 指标 | 实测值 |
|---|---|
| **来源准确性（Top-1）** | **3/3 = 100%**（3 轮独立测试均 100%） |
| 检索延迟 | 160.9 ~ 216.8 ms |
| LLM 延迟 | 5,314 ~ 10,633 ms |
| 总延迟 | 5,506 ~ 10,794 ms |
| 检索 / 生成耗时占比 | 约 3% / 97% |

> 结论：检索端不是瓶颈（仅占约 3%），端到端优化的重点在生成端。

### 生成质量调优：repetition_penalty 对照实验

7B 小模型在长 prompt 下会重复生成字符（"外部线线线池中的线线线运行"），且稳定复现。用同一问题、同一索引，仅改 `repetition_penalty` 做对照：

| repetition_penalty | 生成质量表现 | 结论 |
|---|---|---|
| 1.00（默认） | 重复严重：三连重复字符 | 基线 |
| 1.05 | 轻微改善：三连重复降为单字重复 | 力度不足 |
| **1.15** | ✅ **最优**：分点清晰、结论完整，仅 1 处残留重复 | **采用（已写入配置）** |
| 1.30 | ❌ 过惩罚导致语义崩溃："FastAI"、"堵住堵塞"、"迓织"等乱字 | 弃用 |

> **结论**：重复惩罚不是越大越好——1.15 为最优值，调到 1.3 反而损害语义连贯性。
> **配置**：`app/config.py` 的 `LLM_TEMPERATURE` / `LLM_REPETITION_PENALTY`，均可用环境变量覆盖。
