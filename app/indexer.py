"""
FAISS 向量索引：建索引、检索 Top-K
支持持久化（保存/加载）
"""
import time
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple
from app.embedder import Embedder
from app.chunker import Chunk
from app.config import INDEX_DIR


class FAISSIndex:
    def __init__(self, embedder: Embedder, strategy: str = "recursive"):
        self.embedder = embedder
        self.strategy = strategy
        self.chunks: List[Chunk] = []
        self.vectors: np.ndarray = None
        self.index: faiss.IndexFlatIP = None  # 内积（cosine，因为已归一化）

    def build(self, chunks: List[Chunk], batch_size: int = 32):
        """建索引：对每个 chunk 做 Embedding，存入 FAISS"""
        self.chunks = chunks
        texts = [c.content for c in chunks]
        dim = self.embedder.dimension

        # 分批 Embedding
        all_vectors = []
        total = len(texts)
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            vecs = self.embedder.embed(batch)
            all_vectors.extend(vecs)
            print(f"  Embedding 进度：{min(i + batch_size, total)}/{total}")

        self.vectors = np.array(all_vectors, dtype=np.float32)
        # 归一化（cosine 相似度 = 内积）
        faiss.normalize_L2(self.vectors)

        # 建 Flat 索引（精确检索）
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(self.vectors)
        print(f"✅ 索引建成：{self.index.ntotal} 个向量，维度 {dim}")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Chunk, float]]:
        """检索：返回 Top-K (chunk, score) 对"""
        if self.index is None:
            raise RuntimeError("索引未建，请先调用 build()")

        t0 = time.time()
        query_vec = self.embedder.embed_query(query)
        query_vec = np.array([query_vec], dtype=np.float32)
        faiss.normalize_L2(query_vec)

        scores, indices = self.index.search(query_vec, top_k)
        latency = (time.time() - t0) * 1000

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < 0:
                continue
            chunk = self.chunks[idx]
            results.append((chunk, float(score), rank + 1, latency))
        return results

    def save(self, path: Path = None):
        """保存索引和 chunks 到磁盘"""
        path = path or (INDEX_DIR / f"index_{self.strategy}")
        path.mkdir(parents=True, exist_ok=True)
        # 保存 FAISS 索引
        faiss.write_index(self.index, str(path / "faiss.index"))
        # 保存 chunks 元数据和向量
        import json
        meta = {
            "strategy": self.strategy,
            "chunks": [{"chunk_id": c.chunk_id, "doc_id": c.doc_id,
                        "content": c.content, "char_count": c.char_count,
                        "strategy": c.strategy} for c in self.chunks],
        }
        (path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        np.save(str(path / "vectors.npy"), self.vectors)
        print(f"✅ 索引已保存：{path}")

    def load(self, path: Path = None):
        """从磁盘加载索引"""
        path = path or (INDEX_DIR / f"index_{self.strategy}")
        self.index = faiss.read_index(str(path / "faiss.index"))
        self.vectors = np.load(str(path / "vectors.npy"))
        import json
        meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
        self.chunks = [Chunk(**c) for c in meta["chunks"]]
        print(f"✅ 索引已加载：{self.index.ntotal} 个向量，策略={self.strategy}")
