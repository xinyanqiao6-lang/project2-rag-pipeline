# Transformer 架构详解

## Transformer 的核心组件

Transformer 是 2017 年 Google 在论文《Attention Is All You Need》中提出的架构，它完全基于注意力机制，摒弃了 RNN 和 CNN。Transformer 由编码器（Encoder）和解码器（Decoder）两部分组成。

编码器由多个相同的层堆叠而成，每层包含两个子层：多头自注意力机制（Multi-Head Self-Attention）和前馈神经网络（Feed-Forward Network）。每个子层都使用残差连接（Residual Connection）和层归一化（Layer Normalization）。

解码器与编码器类似，但额外增加了一个交叉注意力层（Cross-Attention），用于关注编码器的输出。解码器的自注意力层是掩码的（Masked），确保生成时只能看到已生成的内容。

## 自注意力机制

自注意力机制是 Transformer 的核心。它通过三个矩阵 Q（Query）、K（Key）、V（Value）计算注意力权重。公式为：Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V。

缩放因子 sqrt(d_k) 用于防止内积值过大导致 softmax 梯度消失。多头注意力则是将 Q、K、V 分成多个头并行计算，最后拼接，使模型能同时关注不同维度信息。

## 位置编码

由于 Transformer 没有循环结构，无法感知序列顺序，因此需要位置编码。原始论文使用正弦/余弦函数生成位置编码，与词嵌入相加。后续的模型如 BERT 使用可学习的位置编码，而 ALiBi 和 RoPE 则是更先进的位置编码方案。

## Transformer 在大模型中的应用

GPT 系列只使用 Transformer 的解码器部分，BERT 只使用编码器部分，而 T5 和原始 Transformer 一样使用编码器-解码器结构。Qwen2.5、LLaMA 等主流大语言模型都基于 Transformer 架构，并在此基础上进行了大量优化。
