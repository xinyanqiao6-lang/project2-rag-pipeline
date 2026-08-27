"""文档解析与清洗管道：读取 docs/ 下的 TXT/MD 文件，做基本清洗"""
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List
from app.config import DOCS_DIR


@dataclass
class Document:
    """一份文档"""
    doc_id: str        # 文件名（无后缀）
    source: str        # 文件路径
    content: str       # 清洗后正文
    char_count: int    # 字符数


def clean_text(text: str) -> str:
    """清洗文本：去多余空白、统一换行、去行首尾空格"""
    # 统一换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 去每行首尾空格
    lines = [line.strip() for line in text.split("\n")]
    # 合并连续空行（3+ 变 1）
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return text.strip()


def parse_file(filepath: Path) -> Document:
    """解析单个文件"""
    content = filepath.read_text(encoding="utf-8")
    cleaned = clean_text(content)
    doc_id = filepath.stem  # 文件名无后缀
    return Document(
        doc_id=doc_id,
        source=str(filepath),
        content=cleaned,
        char_count=len(cleaned),
    )


def load_documents(docs_dir: Path = None) -> List[Document]:
    """加载目录下所有 .txt/.md 文件"""
    docs_dir = docs_dir or DOCS_DIR
    if not docs_dir.exists():
        raise FileNotFoundError(f"文档目录不存在：{docs_dir}")

    files = sorted(
        list(docs_dir.glob("*.md")) + list(docs_dir.glob("*.txt")),
        key=lambda f: f.name,
    )
    if not files:
        raise FileNotFoundError(f"文档目录为空：{docs_dir}")

    documents = [parse_file(f) for f in files]
    total = sum(d.char_count for d in documents)
    print(f"📄 加载 {len(documents)} 份文档，共 {total:,} 字符，平均 {total // len(documents):,} 字符/份")
    return documents


if __name__ == "__main__":
    docs = load_documents()
    for d in docs[:5]:
        print(f"  {d.doc_id}: {d.char_count} 字符")
