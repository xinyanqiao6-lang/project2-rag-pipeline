"""
RAG 问答链：retriever → prompt → LLM → output
调用硅基流动 Qwen2.5-7B-Instruct 生成回答
"""
import time
import httpx
from typing import List, Tuple
from app.config import (SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL,
                        LLM_MODEL, MOCK_MODE, TOP_K)
from app.embedder import Embedder
from app.indexer import FAISSIndex
from app.document_processor import load_documents
from app.chunker import chunk_documents, STRATEGIES

# RAG 提示词模板
PROMPT_TEMPLATE = """你是一个知识库问答助手。以下是从知识库中检索到的相关信息：

{context}

请基于上述信息回答用户的问题。如果检索信息不足以回答，请说明。
回答要准确、简洁，并在末尾标注信息来源。

问题：{question}

回答："""


class RAGChain:
    def __init__(self, strategy: str = "recursive", mock: bool = None):
        self.mock = mock if mock is not None else MOCK_MODE
        self.strategy = strategy

        # 加载文档+切分+建索引
        documents = load_documents()
        chunks = chunk_documents(documents, strategy)
        self.embedder = Embedder(mock=self.mock)
        self.index = FAISSIndex(self.embedder, strategy)
        self.index.build(chunks)

        # LLM 客户端
        self._client = None if self.mock else httpx.Client(
            base_url=SILICONFLOW_BASE_URL,
            headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
            timeout=120.0,
        )

    def query(self, question: str, top_k: int = TOP_K) -> dict:
        """完整 RAG 问答流程"""
        t_total = time.time()

        # 1. 检索
        t0 = time.time()
        results = self.index.search(question, top_k=top_k)
        retrieval_latency = (time.time() - t0) * 1000

        # 2. 拼上下文
        context_parts = []
        sources = []
        for chunk, score, rank, _ in results:
            context_parts.append(f"[{rank}] (来源: {chunk.doc_id}, 相似度: {score:.4f})\n{chunk.content}")
            sources.append({"doc_id": chunk.doc_id, "score": score, "rank": rank})
        context = "\n\n---\n\n".join(context_parts)

        # 3. 构造 prompt
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        # 4. 调 LLM 生成回答
        t1 = time.time()
        if self.mock:
            answer = f"[Mock模式] 基于检索到的 {len(results)} 个文档片段回答：\n"
            answer += f"Top-1 来源：{results[0][0].doc_id}（相似度 {results[0][1]:.4f}）\n"
            answer += f"检索延迟：{retrieval_latency:.1f}ms"
        else:
            answer = self._call_llm(prompt)
        llm_latency = (time.time() - t1) * 1000

        return {
            "answer": answer,
            "sources": sources,
            "retrieval_latency_ms": retrieval_latency,
            "llm_latency_ms": llm_latency,
            "total_latency_ms": (time.time() - t_total) * 1000,
        }

    def _call_llm(self, prompt: str) -> str:
        """调用硅基流动 Chat API"""
        resp = self._client.post(
            "/chat/completions",
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def close(self):
        self.embedder.close()
        if self._client:
            self._client.close()


if __name__ == "__main__":
    from app.config import validate
    if not MOCK_MODE:
        validate()
    rag = RAGChain(mock=MOCK_MODE)
    questions = [
        "RAG 系统包含哪几个阶段？",
        "FAISS 支持哪些索引类型？",
        "LoRA 的 rank 参数有什么作用？",
    ]
    for q in questions:
        print(f"\n{'='*60}")
        print(f"  Q: {q}")
        result = rag.query(q)
        print(f"  检索延迟: {result['retrieval_latency_ms']:.1f}ms")
        print(f"  LLM延迟: {result['llm_latency_ms']:.1f}ms")
        print(f"  总延迟: {result['total_latency_ms']:.1f}ms")
        print(f"  来源: {result['sources']}")
        print(f"  回答: {result['answer'][:200]}...")
    rag.close()
