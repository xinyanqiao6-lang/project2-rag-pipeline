"""
检索质量评估脚本：10 个标注问题，3 策略对比
计算 Top-K 命中率、MRR、检索延迟，输出 CSV 对比表
"""
import csv
import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import RESULTS_DIR, TOP_K
from app.document_processor import load_documents
from app.chunker import chunk_documents, STRATEGIES, chunk_stats
from app.embedder import Embedder
from app.indexer import FAISSIndex

# ── 10 个标注问题（ground_truth = 正确答案所在的 doc_id）──
# 语料为真实开源官方文档（FastAPI/Pydantic/HTTPX/Docker/LangChain），
# 每份文档标注 1-2 个问题，覆盖 7 份文档。
TEST_QUESTIONS = [
    {"q": "FastAPI 中 async def 和普通 def 的路径操作函数在运行方式上有什么区别？", "gt_doc": "01_fastapi_async"},
    {"q": "FastAPI 的依赖注入用什么声明，依赖函数可以嵌套吗？", "gt_doc": "02_fastapi_dependencies"},
    {"q": "FastAPI 如何声明一个请求体，用什么类型的参数？", "gt_doc": "03_fastapi_request_body"},
    {"q": "Pydantic 中模型如何定义，用什么类继承？", "gt_doc": "04_pydantic_models"},
    {"q": "Pydantic 模型的 extra 配置项可以取哪三个值？", "gt_doc": "04_pydantic_models"},
    {"q": "HTTPX 如何发送 JSON 编码的数据？", "gt_doc": "05_httpx_quickstart"},
    {"q": "HTTPX 最重要的两个异常类是什么？", "gt_doc": "05_httpx_quickstart"},
    {"q": "Docker 客户端-服务器架构中，负责构建和运行容器的守护进程叫什么？", "gt_doc": "06_docker_overview"},
    {"q": "Docker 镜像和容器是什么关系？", "gt_doc": "06_docker_overview"},
    {"q": "LangChain 的 create_agent 核心公式是什么，agent 由哪几部分组成？", "gt_doc": "07_langchain_overview"},
]


def evaluate_strategy(strategy: str, embedder: Embedder, documents) -> Dict:
    """评估单个策略的检索质量"""
    print(f"\n{'='*60}")
    print(f"  评估策略：{strategy}")
    print(f"{'='*60}")

    # 切分
    chunks = chunk_documents(documents, strategy)
    stats = chunk_stats(chunks)
    print(f"  切分结果：{stats['total_chunks']} 块 | 均 {stats['avg_size']} 字符 | "
          f"min {stats['min_size']} / max {stats['max_size']}")

    # 建索引
    index = FAISSIndex(embedder, strategy)
    index.build(chunks)

    # 检索评估
    results = []
    hits = 0
    mrr_sum = 0.0
    latencies = []

    for i, q_data in enumerate(TEST_QUESTIONS):
        q = q_data["q"]
        gt_doc = q_data["gt_doc"]

        results_topk = index.search(q, top_k=TOP_K)

        # 延迟
        lat = results_topk[0][3] if results_topk else 0  # search 返回的 latency
        latencies.append(lat)

        # 命中检查：正确文档是否出现在 Top-K 中
        found_rank = None
        for chunk, score, rank, _ in results_topk:
            if chunk.doc_id == gt_doc:
                found_rank = rank
                break

        hit = found_rank is not None
        rr = 1.0 / found_rank if hit else 0.0

        if hit:
            hits += 1
        mrr_sum += rr

        results.append({
            "question": q,
            "gt_doc": gt_doc,
            "hit": hit,
            "rank": found_rank,
            "rr": rr,
            "latency_ms": lat,
            "top1_doc": results_topk[0][0].doc_id if results_topk else "N/A",
            "top1_score": results_topk[0][1] if results_topk else 0,
        })
        status = f"✅ rank={found_rank}" if hit else "❌ miss"
        print(f"  Q{i+1}: {q[:20]}... → {status} (latency={lat:.1f}ms)")

    hit_rate = hits / len(TEST_QUESTIONS)
    mrr = mrr_sum / len(TEST_QUESTIONS)
    avg_latency = statistics.mean(latencies)
    p95_latency = max(latencies) if len(latencies) <= 20 else sorted(latencies)[int(len(latencies)*0.95)]

    summary = {
        "strategy": strategy,
        "total_chunks": stats["total_chunks"],
        "avg_chunk_size": stats["avg_size"],
        "min_chunk_size": stats["min_size"],
        "max_chunk_size": stats["max_size"],
        "hit_rate": hit_rate,
        "mrr": mrr,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "detail": results,
    }

    print(f"\n  📊 {strategy} 汇总：命中率 {hit_rate*100:.0f}% | MRR {mrr:.4f} | "
          f"均延迟 {avg_latency:.1f}ms | P95 {p95_latency:.1f}ms")

    return summary


def run_evaluation(mock: bool = False):
    """运行全部 3 策略评估"""
    print("=" * 60)
    print(f"  RAG 检索质量评估 | Mock={mock}")
    print("=" * 60)

    documents = load_documents()
    embedder = Embedder(mock=mock)

    all_results = []
    for strategy in STRATEGIES:
        result = evaluate_strategy(strategy, embedder, documents)
        all_results.append(result)

    embedder.close()

    # 输出对比表
    print("\n" + "=" * 60)
    print("  📋 三策略对比汇总")
    print("=" * 60)
    print(f"  {'策略':<12} {'块数':>6} {'均长':>6} {'命中率':>8} {'MRR':>8} {'均延迟':>10} {'P95':>10}")
    print(f"  {'-'*12} {'-'*6} {'-'*6} {'-'*8} {'-'*8} {'-'*10} {'-'*10}")
    for r in all_results:
        print(f"  {r['strategy']:<12} {r['total_chunks']:>6} {r['avg_chunk_size']:>6} "
              f"{r['hit_rate']*100:>7.0f}% {r['mrr']:>8.4f} "
              f"{r['avg_latency_ms']:>8.1f}ms {r['p95_latency_ms']:>8.1f}ms")

    # 找最优
    best = max(all_results, key=lambda x: (x["hit_rate"], x["mrr"]))
    print(f"\n  🏆 最优策略：{best['strategy']}（命中率 {best['hit_rate']*100:.0f}%，MRR {best['mrr']:.4f}）")

    # 保存 CSV
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / "evaluation_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["策略", "块数", "平均块长", "最小块长", "最大块长",
                         "Top-5命中率", "MRR", "均延迟(ms)", "P95延迟(ms)"])
        for r in all_results:
            writer.writerow([r["strategy"], r["total_chunks"], r["avg_chunk_size"],
                             r["min_chunk_size"], r["max_chunk_size"],
                             f"{r['hit_rate']*100:.0f}%", f"{r['mrr']:.4f}",
                             f"{r['avg_latency_ms']:.1f}", f"{r['p95_latency_ms']:.1f}"])
    print(f"\n  📄 对比表已保存：{csv_path}")

    # 保存详细 JSON
    import json
    json_path = RESULTS_DIR / "evaluation_results.json"
    detail = [{k: v for k, v in r.items() if k != "detail"} for r in all_results]
    json_path.write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  📄 详细数据已保存：{json_path}")

    return all_results


if __name__ == "__main__":
    import sys
    mock = "--mock" in sys.argv
    if not mock:
        from app.config import validate
        validate()
    run_evaluation(mock=mock)
