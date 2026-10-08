"""BM25 稀疏检索（零依赖，从零实现）+ RRF 融合 + 重排。

## 为什么必须加 BM25
v1 只有 FAISS 向量召回，在实测里出现"命中率 100%、MRR 1.0"的**指标饱和**——
因为 10 道题都是同一份文档里的直白事实问句，向量检索轻松全对，
说明这套评测**没有区分度**，无法证明任何改进有效。

向量检索的固有弱点正好被 BM25 补上：
- 专有名词、API 名、参数名（`async def`、`extra`、`pymodel`）→ 稀疏检索靠词面精确匹配更强
- 用户原话里的关键词 → BM25 命中更准
- 同义表达 → BM25 弱、向量强
两者互补，所以要做混合检索。

## 中文分词怎么办
不引入 jieba（多一个重依赖）。用**字符二元组 + ASCII 词**的混合切分：
中文语料上 char bigram 的召回效果接近词切分，且对未登录词（FastAPI、pydantic）
特别有效——这正是技术文档的主要成分。

## RRF 融合
RRF（Reciprocal Rank Fusion）只用**排名**不用分数：
    score(d) = Σ 1 / (k + rank_i(d))     k=60
好处是 dense 与 sparse 的分数尺度完全不同（余弦 vs BM25），
直接加权求和需要先归一化且很脆弱；只用排名则天然免疫。
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

# 中文字符：CJK 统一表意文字
_CJK = r"一-鿿"
_ASCII_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")
_SPLIT_CJK = re.compile(f"([{_CJK}]+)")
_CJK_RE = re.compile(f"[{_CJK}]")      # 用于判断某段是否含中文（不能用 "_CJK in seg"，那是子串判断）

# 高频中文虚词停用表。
# 为什么需要：单字 + 二元组的切分会把"的/了/是"这类字也建成词项，
# 而它们几乎出现在每个文档里，于是**任何查询都会拿到非零分数**，
# BM25 的 top_k 永远不为空，检索结果被噪声淹没。
# 这不是理论问题——实测里查"完全不相关的内容"也能命中，只因为里面有个"的"。
STOPWORDS = {
    "的", "了", "是", "在", "和", "与", "及", "等", "把", "被",
    "就", "都", "而", "对", "为", "以", "或", "也", "很", "被",
    "什么", "怎么", "如何", "哪些", "一个", "可以", "这个", "那个",
}


def tokenize(text: str) -> list[str]:
    """混合切分：ASCII 单词整体保留 + 中文取字符一元/二元组，去停用词。

    例："FastAPI 的依赖注入" → ["fastapi", "依赖", "赖注", "注入"]
    （"的"作为停用词被去掉）
    对未登录技术术语（FastAPI、pydantic 等不在词典里）反而比词切分更稳，
    这正是技术文档的主要成分。
    """
    text = (text or "").lower()
    tokens: list[str] = []
    for seg in _SPLIT_CJK.split(text):
        if not seg:
            continue
        if _CJK_RE.search(seg):
            chars = list(seg)
            for c in chars:
                if c not in STOPWORDS:
                    tokens.append(c)
            for i in range(len(chars) - 1):
                bg = chars[i] + chars[i + 1]
                if bg not in STOPWORDS:
                    tokens.append(bg)
        else:
            tokens.extend(w for w in _ASCII_WORD.findall(seg) if w not in STOPWORDS)
    return tokens


@dataclass
class BM25:
    """标准 BM25（Okapi）。k1 控制词频饱和，b 控制文档长度归一化。"""
    k1: float = 1.5
    b: float = 0.75
    corpus_size: int = 0
    df: Counter = field(default_factory=Counter)
    doc_len: list[int] = field(default_factory=list)
    avg_len: float = 0.0
    tf: list[Counter] = field(default_factory=list)

    def fit(self, docs: list[str]) -> "BM25":
        self.corpus_size = len(docs)
        self.tf, self.doc_len, self.df = [], [], Counter()
        for d in docs:
            toks = tokenize(d)
            c = Counter(toks)
            self.tf.append(c)
            self.doc_len.append(len(toks))
            for t in c:
                self.df[t] += 1
        self.avg_len = (sum(self.doc_len) / self.corpus_size) if self.corpus_size else 0.0
        return self

    def idf(self, term: str) -> float:
        # 加 0.5 平滑（BM25+ 变体），避免高频词出现负 idf
        df = self.df.get(term, 0)
        return math.log(1 + (self.corpus_size - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> list[float]:
        """返回与语料同序的分数列表。"""
        q_tokens = tokenize(query)
        scores = [0.0] * self.corpus_size
        for t in q_tokens:
            idf = self.idf(t)
            for i, c in enumerate(self.tf):
                f = c.get(t, 0)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avg_len or 1))
                scores[i] += idf * (f * (self.k1 + 1)) / denom
        return scores

    def top_k(self, query: str, k: int) -> list[tuple[int, float]]:
        scores = self.score(query)
        ranked = sorted(enumerate(scores), key=lambda kv: -kv[1])
        return [(i, s) for i, s in ranked[:k] if s > 0]


# ---------- RRF 融合 ----------

def rrf_fuse(rank_lists: list[list[int]], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion。

    只用排名不用分数：dense（余弦）与 sparse（BM25）分数尺度不可比，
    直接加权要先归一化、很脆弱；用排名则天然免疫尺度问题。
    """
    fused: dict[int, float] = {}
    for ranks in rank_lists:
        for pos, doc_idx in enumerate(ranks):
            fused[doc_idx] = fused.get(doc_idx, 0.0) + 1.0 / (k + pos + 1)
    return fused


def top_k_from_fused(fused: dict[int, float], k: int) -> list[tuple[int, float]]:
    ranked = sorted(fused.items(), key=lambda kv: -kv[1])
    return ranked[:k]


# ---------- 重排 ----------
class Reranker:
    """调用硅基流动的 BAAI/bge-reranker-v2-m3 做精排。

    为什么需要：召回（recall）与精排（precision）是两件事。
    向量/BM25 负责把候选缩到 Top-N，Cross-Encoder 负责这 N 个的精细排序——
    它能同时看到 query 与文档，做的是"逐对匹配"打分，比双塔向量准得多。

    工程上刻意做成**失败即降级**：rerank 不可用时返回原始顺序并标记
    available=False，而不是抛异常中断整条评测链路——否则一个外部依赖抖动
    就会让整轮实验数据作废。
    """

    def __init__(self, model: str = "BAAI/bge-reranker-v2-m3", top_n: int = 20):
        self.model = model
        self.top_n = top_n
        self.available = True
        self.last_error = ""
        self.calls = 0
        self._client = None
        try:
            from app.config import SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL
            if SILICONFLOW_API_KEY:
                import httpx
                self._client = httpx.Client(
                    base_url=SILICONFLOW_BASE_URL,
                    headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
                    timeout=30.0,
                    # 不走系统代理：代理会给每次调用叠加不可控延迟，污染检索耗时统计
                    trust_env=False,
                )
            else:
                self.available = False
                self.last_error = "无 API Key"
        except Exception as e:                     # noqa: BLE001
            self.available = False
            self.last_error = f"{type(e).__name__}: {e}"

    def rerank(self, query: str, documents: list[str]) -> list[tuple[int, float]]:
        """返回 [(原始下标, 相关性分数)]，按分数降序。失败则返回原始顺序。"""
        if not documents:
            return []
        fallback = list(enumerate([0.0] * len(documents)))
        if not self.available or self._client is None:
            self.last_error = self.last_error or "rerank 不可用"
            return fallback
        try:
            self.calls += 1
            r = self._client.post(
                "/rerank",
                json={
                    "model": self.model,
                    "query": query,
                    "documents": documents,
                    "top_n": min(self.top_n, len(documents)),
                },
            )
            if r.status_code != 200:
                self.available = False
                self.last_error = f"HTTP {r.status_code}"
                return fallback
            results = (r.json() or {}).get("results") or []
            out = [(int(x["index"]), float(x.get("relevance_score", 0.0))) for x in results]
            return out if out else fallback
        except Exception as e:                     # noqa: BLE001
            self.available = False
            self.last_error = f"{type(e).__name__}: {e}"
            return fallback