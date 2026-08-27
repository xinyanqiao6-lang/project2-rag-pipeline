# BERT 模型详解

## BERT 简介

BERT（Bidirectional Encoder Representations from Transformers）是 Google 于 2018 年提出的预训练语言模型。与 GPT 的单向生成不同，BERT 使用双向 Transformer 编码器，能同时利用上下文信息。

## 预训练任务

BERT 使用两个预训练任务：掩码语言模型（MLM）和下一句预测（NSP）。MLM 随机遮盖输入词，让模型预测被遮盖的词。NSP 判断两句话是否是连续的。这两个任务使 BERT 学到了丰富的双向语言表示。

## BERT 的变体

BERT 衍生出多个变体：RoBERTa 去掉了 NSP 任务并增大训练数据；ALBERT 用参数共享减少参数量；DistilBERT 通过知识蒸馏压缩模型。这些变体在不同场景下各有优势。

## BERT 与 Embedding

BERT 及其变体常被用作 Embedding 模型。但原始 BERT 的 [CLS] token 表示并不适合直接做语义相似度计算。后续的 Sentence-BERT 通过对比学习改进了这一点，使 BERT 能输出高质量的句向量。bge 系列也基于类似思路训练，是当前中文 Embedding 的主流选择。
