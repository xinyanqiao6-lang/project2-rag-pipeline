"""项目2 配置：从环境变量读取，支持 .env 文件"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API 配置 ──
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# ── 路径 ──
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
RESULTS_DIR = PROJECT_ROOT / "results"
INDEX_DIR = RESULTS_DIR / "indices"

# ── 切分参数 ──
CHUNK_CONFIGS = {
    "fixed":     {"chunk_size": 500, "chunk_overlap": 50},
    "recursive": {"chunk_size": 500, "chunk_overlap": 50,
                  "separators": ["\n\n", "\n", "。", "！", "？", "；", "，", " "]},
    "semantic":  {"chunk_size": 200, "chunk_overlap": 30},
}

# ── Mock 模式（无 Key 时用假数据，验证链路用）──
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# ── 评估 ──
TOP_K = 5  # 检索 Top-K

# ── 生成参数（抑制 7B 小模型的重复 token 退化）──
# 问题：Qwen2.5-7B 在长 prompt 下会重复生成字符（如"外部线线线池"、"运行的的运行实例"）。
# 对照实验（同一问题 / 同一索引，仅改 penalty）：
#   1.00 -> 重复严重；1.05 -> 轻微改善；
#   1.15 -> ✅ 最优，回答分点清晰、结论完整，仅 1 处残留重复；
#   1.30 -> ❌ 过惩罚导致语义崩溃（"FastAI"、"堵住堵塞"等乱字）。
# 结论：1.15 为最优值，越大越好是错的——过惩罚会损害语义连贯性。
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_REPETITION_PENALTY = float(os.getenv("LLM_REPETITION_PENALTY", "1.15"))

def validate():
    """启动前校验 Key"""
    if not MOCK_MODE and not SILICONFLOW_API_KEY:
        raise RuntimeError(
            "SILICONFLOW_API_KEY 未配置！请复制 .env.example 为 .env 并填入 Key。"
            " 或设 MOCK_MODE=true 走 Mock 模式验证链路。"
        )
