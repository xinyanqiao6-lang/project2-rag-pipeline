"""
Gradio 界面：RAG 问答 Demo
运行：python app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import validate, MOCK_MODE, LLM_MODEL, EMBEDDING_MODEL
from app.rag_chain import RAGChain

# 初始化 RAG 链
print("正在初始化 RAG 系统...")
if not MOCK_MODE:
    validate()
rag = RAGChain(strategy="recursive", mock=MOCK_MODE)
print("✅ RAG 系统就绪\n")

import gradio as gr


def answer_question(question: str):
    """Gradio 回调"""
    if not question.strip():
        return "请输入问题", "", ""

    result = rag.query(question)

    # 格式化来源
    sources_text = "\n".join([
        f"Top-{s['rank']}: {s['doc_id']} (相似度: {s['score']:.4f})"
        for s in result["sources"]
    ])

    # 性能指标
    metrics = (f"检索延迟: {result['retrieval_latency_ms']:.1f}ms\n"
               f"LLM 延迟: {result['llm_latency_ms']:.1f}ms\n"
               f"总延迟: {result['total_latency_ms']:.1f}ms")

    return result["answer"], sources_text, metrics


# ── Gradio 界面 ──
with gr.Blocks(title="RAG 知识库问答 Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"""
    # RAG 知识库问答 Demo

    > 基于检索增强生成（RAG）的知识库问答系统
    >
    > **Embedding 模型**: `{EMBEDDING_MODEL}` | **LLM**: `{LLM_MODEL}` | **模式**: {"Mock" if MOCK_MODE else "真实 API"}
    """)
    with gr.Row():
        question_input = gr.Textbox(
            label="请输入问题",
            placeholder="例如：RAG 系统包含哪几个阶段？",
            lines=2,
        )
    with gr.Row():
        submit_btn = gr.Button("提交", variant="primary")
        clear_btn = gr.ClearButton([question_input])

    with gr.Row():
        with gr.Column(scale=3):
            answer_output = gr.Textbox(label="回答", lines=8)
        with gr.Column(scale=1):
            sources_output = gr.Textbox(label="检索来源 (Top-5)", lines=8)
            metrics_output = gr.Textbox(label="性能指标", lines=3)

    gr.Examples(
        examples=[
            "RAG 系统包含哪几个核心阶段？",
            "FAISS 支持哪些索引类型？",
            "LoRA 的 rank 参数有什么作用？",
            "MRR 指标是怎么计算的？",
            "SSE 和 WebSocket 有什么区别？",
        ],
        inputs=question_input,
    )

    submit_btn.click(answer_question, inputs=[question_input],
                     outputs=[answer_output, sources_output, metrics_output])
    question_input.submit(answer_question, inputs=[question_input],
                          outputs=[answer_output, sources_output, metrics_output])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, show_error=True)
