"""
Embedding 客户端：调用硅基流动 BAAI/bge-large-zh-v1.5
支持批量 Embedding 和 Mock 模式
"""
import time
import hashlib
import random
from typing import List, Union
import httpx
from app.config import SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, EMBEDDING_MODEL, MOCK_MODE


class Embedder:
    def __init__(self, mock: bool = None):
        self.mock = mock if mock is not None else MOCK_MODE
        self.model = EMBEDDING_MODEL
        self._client = None if self.mock else httpx.Client(
            base_url=SILICONFLOW_BASE_URL,
            headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
            timeout=60.0,
        )
        # Mock 模式用确定性哈希向量
        self._mock_dim = 128  # Mock 向量维度（真实 bge 是 1024）

    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """将文本转为向量。输入 str 返回单向量，输入 list 返回矩阵"""
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        if self.mock:
            vectors = [self._mock_embed(t) for t in texts]
        else:
            vectors = self._api_embed(texts)

        return vectors[0] if single else vectors

    def _api_embed(self, texts: List[str]) -> List[List[float]]:
        """调用硅基流动 Embedding API"""
        resp = self._client.post(
            "/embeddings",
            json={"model": self.model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()
        # 按 index 排序确保顺序
        items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]

    def _mock_embed(self, text: str) -> List[float]:
        """Mock：用文本哈希生成确定性伪向量"""
        h = hashlib.sha256(text.encode()).hexdigest()
        # 用哈希的每 2 位做种子生成 128 维向量
        vec = []
        for i in range(0, self._mock_dim):
            seed = int(h[(i * 2) % len(h):(i * 2) % len(h) + 2], 16)
            random.seed(seed)
            vec.append(random.uniform(-1, 1))
        # 归一化
        norm = sum(v * v for v in vec) ** 0.5
        return [v / norm for v in vec]

    def embed_query(self, query: str) -> List[float]:
        """对查询语句做 Embedding"""
        return self.embed(query)

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        if self.mock:
            return self._mock_dim
        # bge-large-zh-v1.5 是 1024 维
        return 1024

    def close(self):
        if self._client:
            self._client.close()


if __name__ == "__main__":
    from app.config import validate
    if not MOCK_MODE:
        validate()
    emb = Embedder()
    t0 = time.time()
    v = emb.embed("什么是 RAG？")
    print(f"✅ 向量维度：{len(v)}，耗时：{(time.time()-t0)*1000:.1f}ms")
    print(f"   前5维：{v[:5]}")
    emb.close()
