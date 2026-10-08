"""混合检索模块的单测：分词、BM25、RRF 融合、重排降级。

这些是纯函数/轻依赖逻辑，可离线跑。守住两条容易回归的底线：
1. 中文必须被切出词项（曾经因为 `_CJK in seg` 写成子串判断，中文全被丢弃）；
2. rerank 失败必须降级而不是抛异常——否则一个外部依赖抖动就让整轮评测作废。
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.hybrid import BM25, Reranker, rrf_fuse, tokenize, top_k_from_fused  # noqa: E402


# ---------- 分词 ----------

def test_tokenize_keeps_ascii_words():
    toks = tokenize("FastAPI 和 Depends")
    assert "fastapi" in toks
    assert "depends" in toks


def test_tokenize_produces_chinese_bigrams():
    """中文必须切出单字与二元组——这是 BM25 在中文语料上能工作的前提。"""
    toks = tokenize("依赖注入")
    assert "依赖" in toks
    assert "赖注" in toks
    assert "dep" not in toks      # 不会误切英文
    assert "依" in toks            # 单字也保留


def test_tokenize_mixed_script():
    toks = tokenize("FastAPI 的依赖注入 Depends")
    assert "fastapi" in toks and "依赖" in toks and "depends" in toks


def test_tokenize_empty_safe():
    assert tokenize("") == []
    assert tokenize(None) == []


# ---------- BM25 ----------

@pytest.fixture()
def corpus():
    return [
        "FastAPI 的依赖注入使用 Depends 声明，支持嵌套依赖",
        "Docker 镜像与容器的关系：镜像是模板，容器是实例",
        "Pydantic 模型通过继承 BaseModel 定义字段",
    ]


def test_bm25_ranks_relevant_first(corpus):
    bm = BM25().fit(corpus)
    hits = bm.top_k("Depends 依赖怎么声明", 2)
    assert hits, "不应返回空结果"
    assert hits[0][0] == 0


def test_bm25_ranks_chinese_query(corpus):
    """纯中文查询也要能命中——曾经的 bug 是中文被整段丢弃。"""
    bm = BM25().fit(corpus)
    hits = bm.top_k("镜像和容器是什么关系", 3)
    assert hits
    assert hits[0][0] == 1


def test_bm25_no_match_returns_empty(corpus):
    """查询词完全不在语料里时，不应返回任何结果（BM25 top_k 的 s>0 过滤）。"""
    bm = BM25().fit(corpus)
    assert bm.top_k("zzz qqq xxx", 3) == []


def test_single_char_tokens_cause_low_score_false_matches(corpus):
    """**已知特性**：单字索引会让"容"这类字命中无关文档，产生低分误匹配。

    这不是 bug 而是字符级切分的固有代价，换来的是未登录术语的召回。
    正因为存在这种噪声，拒答阈值不能只看"有没有命中"，
    必须看**分数高低**——这正是负样本评测存在的原因。
    """
    bm = BM25().fit(corpus)
    hits = bm.top_k("完全不相关的内容", 3)
    assert hits, "含中文单字的查询可能命中——这正是低分噪声"
    top_score = hits[0][1]
    real = bm.top_k("Depends 依赖怎么声明", 1)
    assert real[0][1] > top_score * 3, "真实相关的内容得分应远高于噪声"


def test_bm25_rare_term_scores_higher_than_common():
    """稀有词的 idf 必须高于出现在多篇文档里的常见词——这是 BM25 的核心机制。"""
    corpus = [
        "docker 容器与镜像的关系",      # docker 只出现在这篇
        "docker 的容器编排与镜像分层",  # docker 出现 2 次
        "docker compose 与容器网络",    # docker 出现 3 次
        "机器学习模型与数据",            # 该词只在这篇
        "模型训练与评估流程",            # 模型 2 次
        "模型部署与监控实践",            # 模型 3 次
    ]
    bm = BM25().fit(corpus)
    # docker: df=3；模型: df=3 —— 这里构造 df 相同，改用只在 1 篇出现的词验证
    rare = bm.idf("编排")
    common = bm.idf("模型")
    assert rare > common, f"稀有词 idf({rare}) 应大于常见词 idf({common})"


def test_stopwords_excluded_from_tokens():
    """停用词必须被剔除，否则"的"会让任何查询都拿到非零分。"""
    toks = tokenize("FastAPI 的依赖注入")
    assert "的" not in toks
    assert "依赖" in toks


def test_bm25_idf_is_positive(corpus):
    bm = BM25().fit(corpus)
    # 语料里每个词都出现，idf 仍须为正（BM25+ 平滑），否则负分会打乱排序
    for term in list(bm.df)[:5]:
        assert bm.idf(term) > 0


def test_bm25_score_shape(corpus):
    bm = BM25().fit(corpus)
    assert len(bm.score("任意查询")) == len(corpus)


def test_bm25_empty_corpus_safe():
    bm = BM25().fit([])
    assert bm.score("查询") == []
    assert bm.top_k("查询", 3) == []



# ---------- RRF 融合 ----------

def test_rrf_favors_appearing_in_both_lists():
    """同时出现在两路的文档应排第一——这是混合检索互补性的体现。"""
    fused = rrf_fuse([[0, 1, 2], [1, 0, 3]])
    ranked = top_k_from_fused(fused, 3)
    assert ranked[0][0] in (0, 1)
    assert set(r for r, _ in ranked) >= {0, 1}


def test_rrf_single_list_preserves_order():
    fused = rrf_fuse([[5, 6, 7]])
    ranked = top_k_from_fused(fused, 3)
    assert [r for r, _ in ranked] == [5, 6, 7]


def test_rrf_empty_input_safe():
    assert rrf_fuse([]) == {}
    assert top_k_from_fused({}, 3) == []


def test_rrf_uses_rank_not_score():
    """RRF 只看排名：同一排名在不同列表里贡献相同，与原始分数无关。"""
    a = rrf_fuse([[0, 1]], k=60)
    b = rrf_fuse([[0, 1]], k=60)
    assert a == b
    assert a[0] == pytest.approx(1 / 61)
    assert a[1] == pytest.approx(1 / 62)


# ---------- Reranker 降级 ----------

def test_reranker_degrades_gracefully_without_key(monkeypatch):
    """没有 Key 时必须降级为原始顺序，而不是抛异常。"""
    import app.config as config
    monkeypatch.setattr(config, "SILICONFLOW_API_KEY", "", raising=False)
    r = Reranker()
    assert r.available is False
    docs = ["a", "b", "c"]
    out = r.rerank("query", docs)
    assert [i for i, _ in out] == [0, 1, 2]      # 顺序不变


def test_reranker_empty_docs_safe():
    assert Reranker().rerank("q", []) == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))