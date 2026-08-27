"""
文本切分器：3 种切分策略
1. fixed     — 固定长度切分（按字符数等分 + overlap）
2. recursive — 段落递归切分（按中文标点层次切分）
3. semantic  — 语义细粒度切分（小块 + overlap）
"""
from dataclasses import dataclass
from typing import List
from app.document_processor import Document


@dataclass
class Chunk:
    """一个文本块"""
    chunk_id: str     # 格式：doc_id_chunk序号
    doc_id: str       # 所属文档
    content: str      # 块文本
    char_count: int   # 块字符数
    strategy: str     # 切分策略名


# ── 策略1：固定长度切分 ──
def chunk_fixed(doc: Document, chunk_size: int = 500, overlap: int = 50) -> List[Chunk]:
    chunks = []
    text = doc.content
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(
                chunk_id=f"{doc.doc_id}_{idx}",
                doc_id=doc.doc_id,
                content=piece,
                char_count=len(piece),
                strategy="fixed",
            ))
            idx += 1
        start += chunk_size - overlap  # 滑动窗口
    return chunks


# ── 策略2：段落递归切分 ──
# 按中文标点层次递归切分，优先在自然边界处断开
_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " "]

def _split_recursive(text: str, chunk_size: int, overlap: int, separators: List[str] = None) -> List[str]:
    """递归切分：按 separators 顺序尝试切分"""
    separators = separators or _SEPARATORS
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    for i, sep in enumerate(separators):
        if sep not in text:
            continue
        # 按 sep 切分
        parts = text.split(sep)
        # 尝试合并相邻 part 到 chunk_size 以内
        result = []
        current = ""
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    result.append(current)
                # 如果单个 part 就超长，递归用更细的分隔符
                if len(part) > chunk_size:
                    sub = _split_recursive(part, chunk_size, overlap, separators[i+1:])
                    result.extend(sub)
                    current = ""
                else:
                    current = part
        if current:
            result.append(current)

        # 加 overlap：把上一个块末尾拼到下一个块开头
        if overlap > 0 and len(result) > 1:
            merged = [result[0]]
            for j in range(1, len(result)):
                prev_tail = result[j-1][-overlap:] if len(result[j-1]) >= overlap else result[j-1]
                merged.append(prev_tail + result[j])
            result = merged
        return result

    # 所有分隔符都没找到，强制按 chunk_size 切
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]


def chunk_recursive(doc: Document, chunk_size: int = 500, overlap: int = 50) -> List[Chunk]:
    chunks = []
    pieces = _split_recursive(doc.content, chunk_size, overlap)
    for idx, piece in enumerate(pieces):
        piece = piece.strip()
        if piece:
            chunks.append(Chunk(
                chunk_id=f"{doc.doc_id}_{idx}",
                doc_id=doc.doc_id,
                content=piece,
                char_count=len(piece),
                strategy="recursive",
            ))
    return chunks


# ── 策略3：语义细粒度切分 ──
def chunk_semantic(doc: Document, chunk_size: int = 200, overlap: int = 30) -> List[Chunk]:
    """小块细粒度切分，用递归切分但参数更小"""
    chunks = []
    pieces = _split_recursive(doc.content, chunk_size, overlap)
    for idx, piece in enumerate(pieces):
        piece = piece.strip()
        if piece:
            chunks.append(Chunk(
                chunk_id=f"{doc.doc_id}_{idx}",
                doc_id=doc.doc_id,
                content=piece,
                char_count=len(piece),
                strategy="semantic",
            ))
    return chunks


# ── 统一入口 ──
STRATEGIES = {
    "fixed":     chunk_fixed,
    "recursive": chunk_recursive,
    "semantic":  chunk_semantic,
}

def chunk_documents(documents: List[Document], strategy: str = "recursive") -> List[Chunk]:
    """对文档列表应用指定切分策略"""
    if strategy not in STRATEGIES:
        raise ValueError(f"未知策略：{strategy}，可选：{list(STRATEGIES.keys())}")
    func = STRATEGIES[strategy]
    all_chunks = []
    for doc in documents:
        all_chunks.extend(func(doc))
    return all_chunks


def chunk_stats(chunks: List[Chunk]) -> dict:
    """统计切块信息"""
    sizes = [c.char_count for c in chunks]
    return {
        "total_chunks": len(chunks),
        "avg_size": sum(sizes) // len(sizes) if sizes else 0,
        "min_size": min(sizes) if sizes else 0,
        "max_size": max(sizes) if sizes else 0,
    }


if __name__ == "__main__":
    from app.document_processor import load_documents
    docs = load_documents()
    for name, func in STRATEGIES.items():
        chunks = chunk_documents(docs, name)
        stats = chunk_stats(chunks)
        print(f"  {name:10s}: {stats['total_chunks']:4d} 块 | 均 {stats['avg_size']:4d} | "
              f"min {stats['min_size']:4d} / max {stats['max_size']:4d}")
