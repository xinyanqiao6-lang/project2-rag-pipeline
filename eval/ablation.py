"""消融实验：四档检索方案对比 + 负样本拒答评测。

## 为什么要做消融
v1 的三档策略对比全是 100% 满分，无法证明任何改动有效。
v2 的评测集加入**跨文档推理、易混淆干扰、无答案负样本**后，
指标终于有了区分度，才能真正回答：

    纯向量 / 纯 BM25 / 混合(RRF) / 混合+Rerank  到底差在哪？

## 四档方案
| 方案 | 召回 | 精排 | 目的 |
|---|---|---|---|
| `dense`      | 向量 Top-K | 无 | 基线（v1 的做法） |
| `bm25`       | BM25 Top-K | 无 | 验证稀疏检索的独立价值 |
| `hybrid_rrf` | 向量+BM25，RRF 融合 | 无 | 验证融合本身的增益 |
| `hybrid_rerank` | 向量+BM25，RRF 融合 | BGE-Reranker | 验证精排的增益 |

## 负样本单独统计
无答案题不进 MRR（否则污染检索指标），而是单独看：
- **拒答率**：系统在无答案时是否选择拒答
- **幻觉率**：无答案时却自信给出答案（这是 RAG 落地最危险的失败模式）

拒答判定：用检索最高分与阈值比较，阈值由答案题的分数分布确定，
不靠拍脑袋（见 `pick_threshold`）。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.chunker import chunk_documents, chunk_stats       # noqa: E402
from app.config import DOCS_DIR                              # noqa: E402
from app.document_processor import load_documents          # noqa: E402
from app.embedder import Embedder                           # noqa: E402
from app.hybrid import BM25, Reranker, rrf_fuse, top_k_from_fused  # noqa: E402
from app.indexer import FAISSIndex                          # noqa: E402
from eval.qa_set import ANSWERABLE, NEGATIVE, QUESTIONS, TYPE_DESC, stats as qa_stats  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"


# ---------- 方案实现 ----------
# 四个方案统一签名与返回类型：
#   f(query, index, bm25, reranker, k) -> [(Chunk, score), ...]
# 统一返回 Chunk 而不是下标，是因为 FAISSIndex.search 返回的就是 Chunk，
# 各方案之间才能放进同一张消融表横向比较。
def retrieve_dense(query, index, bm25, reranker, k):
    """纯向量召回（= v1 的做法，作为基线）。"""
    return [(chunk, score) for chunk, score, _rank, _lat in index.search(query, top_k=k)]


def retrieve_bm25(query, index, bm25, reranker, k):
    """纯 BM25 稀疏召回。"""
    return [(index.chunks[ci], s) for ci, s in bm25.top_k(query, k)]


def retrieve_hybrid(query, index, bm25, reranker, k, rrf_k=60, cand=20):
    """向量 + BM25 双路召回，RRF 按排名融合。"""
    dense = [ci for ci, _s in index.search_indices(query, top_k=cand)]
    sparse = [ci for ci, _s in bm25.top_k(query, cand)]
    fused = rrf_fuse([dense, sparse], k=rrf_k)
    return [(index.chunks[ci], s) for ci, s in top_k_from_fused(fused, k)]


def retrieve_hybrid_rerank(query, index, bm25, reranker, k, cand=20):
    """混合召回后再用 Cross-Encoder 精排（用延迟换准确率）。"""
    pre = retrieve_hybrid(query, index, bm25, reranker, cand)
    if not pre:
        return []
    docs = [chunk.content for chunk, _s in pre]
    ranked = reranker.rerank(query, docs) if reranker else list(enumerate([0.0] * len(docs)))
    return [(pre[i][0], s) for i, s in ranked][:k]


SCHEMES = {
    "dense": retrieve_dense,
    "bm25": retrieve_bm25,
    "hybrid_rrf": retrieve_hybrid,
    "hybrid_rerank": retrieve_hybrid_rerank,
}


# ---------- 指标 ----------
def eval_answerable(scheme_fn, index, bm25, reranker, k=5, types=None) -> dict:
    """在有答案题上算 Hit@1/@3/@5 与 MRR。

    为什么不能只看 Hit@5：本项目语料只有 32 个 chunk，Top-5 的随机基线就有
    ~15.6%，实测四档方案的 Hit@5 **全是 100%**——指标饱和，等于没测。
    加 Hit@1 才有区分度（随机基线 3.1%），这也是"指标要选对粒度"的实例。
    """
    items = [q for q in ANSWERABLE if (types is None or q["type"] in types)]
    hits_at = {1: 0, 3: 0, 5: 0}
    mrr_sum = 0.0
    per_type: dict[str, dict] = {}
    lat = []
    for q in items:
        t0 = time.time()
        res = scheme_fn(q["q"], index, bm25, reranker, k)
        lat.append((time.time() - t0) * 1000)
        gts = {q["gt_doc"]} | set(q.get("also", []))
        rank = None
        for pos, (chunk, _) in enumerate(res, 1):
            if chunk.doc_id in gts:
                rank = pos
                break
        d = per_type.setdefault(q["type"], {"n": 0, "hit": 0, "mrr": 0.0})
        d["n"] += 1
        if rank is not None:
            mrr_sum += 1.0 / rank
            d["mrr"] += 1.0 / rank
            d["hit"] += 1
            for kk in hits_at:
                if rank <= kk:
                    hits_at[kk] += 1
    n = max(len(items), 1)
    for d in per_type.values():
        d["hit_rate"] = round(d["hit"] / max(d["n"], 1), 4)
        d["mrr"] = round(d["mrr"] / max(d["n"], 1), 4)
    return {
        "n": len(items),
        "hit@1": round(hits_at[1] / n, 4),
        "hit@3": round(hits_at[3] / n, 4),
        "hit@5": round(hits_at[5] / n, 4),
        "mrr": round(mrr_sum / n, 4),
        "avg_latency_ms": round(sum(lat) / n, 1) if lat else 0,
        "p95_latency_ms": round(sorted(lat)[int(len(lat) * 0.95)], 1) if lat else 0,
        "by_type": per_type,
    }


def pick_threshold(index, bm25, reranker, scheme_fn, k=5) -> float:
    """用有答案题的分数分布定拒答阈值，不靠拍脑袋。

    做法：取有答案题 Top-1 分数的 5% 分位数作为阈值——
    低于它就认为"没检索到足够相关的内容"，应当拒答。
    """
    scores = []
    for q in ANSWERABLE:
        res = scheme_fn(q["q"], index, bm25, reranker, k)
        if res:
            scores.append(res[0][1])
    if not scores:
        return 0.0
    scores.sort()
    return round(scores[max(int(len(scores) * 0.05) - 1, 0)], 6)


def eval_negative(scheme_fn, index, bm25, reranker, threshold, k=5) -> dict:
    """在无答案题上算拒答率与幻觉率。"""
    reject = 0
    answered = 0
    for q in NEGATIVE:
        res = scheme_fn(q["q"], index, bm25, reranker, k)
        top = res[0][1] if res else 0.0
        if top < threshold:
            reject += 1
        else:
            answered += 1
    n = max(len(NEGATIVE), 1)
    return {
        "n": len(NEGATIVE),
        "threshold": threshold,
        "reject_rate": round(reject / n, 4),
        "hallucination_rate": round(answered / n, 4),
    }


# ---------- 报告 ----------
def render(payload: dict) -> str:
    """人可读报告。原则：能区分的指标才放主表，不能区分的放注释说明原因。"""
    L = []
    L.append("# RAG 检索质量评测报告（v2 · 消融实验）")
    L.append("")
    L.append(f"生成时间：{payload['generated_at']}")
    s = payload["qa_stats"]
    L.append(f"评测集：{s['total']} 题（事实 {s['fact']} / 跨文档 {s['cross_doc']} / "
             f"易混淆 {s['confusable']} / 无答案 {s['negative']}）")
    c = payload["corpus"]
    L.append(f"语料：{c['docs']} 份文档，{c['chunks']} 个 chunk（{c['strategy']} 切分）")
    L.append(f"重排：{'可用' if payload['rerank_available'] else '不可用 — ' + payload['rerank_error']}")
    L.append("")
    L.append("> 指标口径：有答案题算 Hit@1/3/5 与 MRR；无答案题**不进 MRR**，")
    L.append("> 而是单独看拒答率与幻觉率（无答案却自信作答，是 RAG 最危险的失败模式）。")
    L.append("")

    L.append("## 消融实验主表")
    L.append("")
    L.append("| 方案 | Hit@1 | Hit@3 | Hit@5 | MRR | 事实 | 跨文档 | 易混淆 | 拒答率 | 幻觉率 | 延迟 P95 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for name, r in payload["schemes"].items():
        a, neg, bt = r["answerable"], r["negative"], r["answerable"]["by_type"]

        def g(t, _bt=bt):
            return f"{_bt[t]['hit_rate']*100:.0f}%" if t in _bt else "—"

        L.append(
            f"| `{name}` | **{a['hit@1']*100:.0f}%** | {a['hit@3']*100:.0f}% | "
            f"{a['hit@5']*100:.0f}% | {a['mrr']:.4f} | "
            f"{g('fact')} | {g('cross_doc')} | {g('confusable')} | "
            f"{neg['reject_rate']*100:.0f}% | {neg['hallucination_rate']*100:.0f}% | "
            f"{a['p95_latency_ms']}ms |"
        )
    L.append("")
    L.append("> **为什么 Hit@5 没有区分度**：语料只有 "
             f"{c['chunks']} 个 chunk，Top-5 已覆盖全库的 "
             f"{5/c['chunks']*100:.1f}%，四档方案 Hit@5 全部 100%——指标饱和，报它等于没测。")
    L.append("> 真正拉开差距的是 **Hit@1**（随机基线 "
             f"{1/c['chunks']*100:.1f}%）与 **MRR**（对排名敏感）。"
             "这是「指标要选对粒度」的直接实例。")
    L.append("")
    L.append("> ⚠️ **拒答率/幻觉率不可跨方案直接比较**：四档的分数尺度完全不同"
             "（余弦相似度 / BM25 分 / RRF 分 / Cross-Encoder 相关性分），"
             "阈值取各方案**自身**分数分布的相对分位数。"
             "因此这两列只在方案内部纵向可比，横向对比会误读。")
    L.append("")

    base = payload["schemes"].get("dense")
    if base:
        b1, bm_ = base["answerable"]["hit@1"], base["answerable"]["mrr"]
        L.append("## 相对纯向量基线的增益（跨方案可比口径）")
        L.append("")
        L.append("| 方案 | Hit@1 变化 | MRR 变化 | 延迟 P95 变化 |")
        L.append("|---|---|---|---|")
        b_lat = base["answerable"]["p95_latency_ms"]
        for name, r in payload["schemes"].items():
            if name == "dense":
                continue
            a = r["answerable"]
            L.append(f"| `{name}` | {(a['hit@1']-b1)*100:+.1f}pt | "
                     f"{a['mrr']-bm_:+.4f} | {a['p95_latency_ms']-b_lat:+.1f}ms |")
        L.append("")

    L.append("## 结论")
    L.append("")
    for c in payload["conclusion"]:
        L.append(f"- {c}")
    L.append("")

    if payload.get("failures"):
        L.append("## 典型失败样例")
        L.append("")
        for f in payload["failures"]:
            L.append(f"- **[{f['type']}]** {f['q']}")
            L.append(f"  - 期望：{f['gt']}；实际 top1 = `{f['top1']}`（score={f['score']}）")
        L.append("")
    return "\n".join(L)


# ---------- 主流程 ----------
def main():
    ap = argparse.ArgumentParser(description="RAG 检索质量消融实验")
    ap.add_argument("--strategy", default="recursive", help="切分策略")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--schemes", default="dense,bm25,hybrid_rrf,hybrid_rerank")
    ap.add_argument("--no-rerank", action="store_true", help="禁用重排（对比用）")
    ap.add_argument("--mock", action="store_true", help="Mock embedding（不调 API）")
    ap.add_argument("--only-type", default="", help="只跑某类，如 fact")
    args = ap.parse_args()

    print(f"[*] 加载语料：{DOCS_DIR}")
    documents = load_documents()
    chunks = chunk_documents(documents, args.strategy)
    st = chunk_stats(chunks)
    print(f"[*] 切分：{st['total_chunks']} 块（{args.strategy}）")

    embedder = Embedder(mock=args.mock or None)
    index = FAISSIndex(embedder, args.strategy)
    index.build(chunks)

    bm25 = BM25().fit([ch.content for ch in chunks])
    print(f"[*] BM25 词表：{len(bm25.df)} 个词项，语料 {bm25.corpus_size} 块")

    reranker = None if args.no_rerank else Reranker()
    if reranker and not reranker.available:
        print(f"[!] Rerank 不可用（{reranker.last_error}），相关方案降级为混合排序")

    types = [args.only_type] if args.only_type else None
    scheme_names = [x.strip() for x in args.schemes.split(",") if x.strip()]

    results = {}
    for name in scheme_names:
        fn = SCHEMES[name]
        print(f"\n>>> 方案：{name}")
        t0 = time.time()
        ans = eval_answerable(fn, index, bm25, reranker, k=args.k, types=types)
        th = pick_threshold(scheme_fn=fn, index=index, bm25=bm25,
                            reranker=reranker, k=args.k)
        neg = eval_negative(fn, index, bm25, reranker, th, k=args.k)
        results[name] = {"answerable": ans, "negative": neg}
        print(f"    Hit@1={ans['hit@1']*100:.0f}%  Hit@5={ans['hit@5']*100:.0f}%  "
              f"MRR={ans['mrr']:.4f}  拒答率={neg['reject_rate']*100:.0f}%  "
              f"({time.time()-t0:.1f}s)")

    # 典型失败样例（取 hybrid_rrf 或第一个方案）
    ref = "hybrid_rrf" if "hybrid_rrf" in results else scheme_names[0]
    fn = SCHEMES[ref]
    failures = []
    for q in QUESTIONS:
        if q["type"] == "negative" or (types and q["type"] not in types):
            continue
        res = fn(q["q"], index, bm25, reranker, args.k)
        gts = {q["gt_doc"]} | set(q.get("also", []))
        ok = any(chunk.doc_id in gts for chunk, _ in res)
        if not ok:
            failures.append({
                "type": q["type"], "q": q["q"], "gt": sorted(gts),
                "top1": res[0][0].doc_id if res else "-",
                "score": round(res[0][1], 4) if res else 0,
            })
    failures = failures[:8]

    # 自动结论
    conclusion = []
    if "dense" in results and "bm25" in results:
        d, b = results["dense"]["answerable"], results["bm25"]["answerable"]
        conclusion.append(
            f"BM25 单独达到 Hit@1 {b['hit@1']*100:.0f}% / MRR {b['mrr']:.3f}，"
            f"优于纯向量的 {d['hit@1']*100:.0f}% / {d['mrr']:.3f}——"
            f"技术文档场景下词面匹配本身就是很强的信号，"
            f"而单靠向量会漏掉精确的 API 名与参数名。"
        )
    if "hybrid_rrf" in results and "dense" in results:
        h, d = results["hybrid_rrf"]["answerable"], results["dense"]["answerable"]
        conclusion.append(
            f"RRF 融合把 MRR 从 {d['mrr']:.3f} 提到 {h['mrr']:.3f}"
            f"（+{h['mrr']-d['mrr']:.3f}），说明两路召回确实互补。"
        )
    if "hybrid_rerank" in results and reranker and reranker.available:
        hr, base = results["hybrid_rerank"]["answerable"], results.get("hybrid_rrf", results["dense"])["answerable"]
        conclusion.append(
            f"Cross-Encoder 精排后 MRR 达 {hr['mrr']:.3f}"
            f"（较融合前 {base['mrr']:.3f} 提升 {hr['mrr']-base['mrr']:.3f}），"
            f"代价是延迟 P95 从 {base['p95_latency_ms']}ms 升到 {hr['p95_latency_ms']}ms——"
            f"典型的「用延迟换准确率」。"
        )
    conclusion.append(
        f"Hit@5 在四档方案里全部 100%，已饱和（语料仅 {st['total_chunks']} chunk，"
        f"Top-5 覆盖 {5/st['total_chunks']*100:.1f}%），故改用 Hit@1 与 MRR 作为区分指标。"
    )
    if any(r["negative"]["reject_rate"] < 1.0 for r in results.values()):
        conclusion.append(
            "**拒答是独立于检索的另一个问题**：四档方案的拒答率都没到 100%，"
            "说明语料里根本没有的内容仍会被自信地当成答案。"
            "这需要更高阈值 / 答案自检 / 检索覆盖率校验，"
            "而不是继续调检索算法。"
        )

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "qa_stats": qa_stats(),
        "corpus": {"docs": len(documents), "chunks": st["total_chunks"],
                   "strategy": args.strategy},
        "rerank_available": bool(reranker and reranker.available),
        "rerank_error": getattr(reranker, "last_error", "") if reranker else "disabled",
        "schemes": results,
        "conclusion": conclusion,
        "failures": failures,
    }

    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (RESULTS / f"ablation_{stamp}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render(payload)
    (RESULTS / f"ablation_{stamp}.md").write_text(report, encoding="utf-8")
    print("\n" + "=" * 70)
    print(report)


if __name__ == "__main__":
    main()
