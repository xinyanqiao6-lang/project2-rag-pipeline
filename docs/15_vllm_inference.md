# vLLM 推理优化

## vLLM 简介

vLLM 是加州大学伯克利分校开源的大语言模型推理引擎，通过 PagedAttention 技术大幅提升了推理吞吐量。它是目前最流行的 LLM 推理框架之一。

## PagedAttention

vLLM 的核心创新是 PagedAttention。它借鉴操作系统的虚拟内存管理，将 KV Cache 按固定大小的"页"管理，避免了传统推理引擎中 KV Cache 的内存碎片和浪费。这使得并发请求的 KV Cache 管理效率大幅提升。

## 连续批处理

vLLM 支持连续批处理（Continuous Batching），不同于传统的静态批处理需要等所有请求完成，vLLM 可以在每个 token 生成时动态加入新请求或移除已完成的请求，最大化 GPU 利用率。

## 吞吐量对比

相比 Hugging Face Transformers，vLLM 可以提升 2-24 倍的吞吐量。在多用户并发场景下优势更明显。但单请求延迟可能不如 TensorRT-LLM 等优化框架。

## vLLM vs 云 API

对于本项目，使用硅基流动的云 API 而非自部署 vLLM，主要原因是成本和运维：无需购买 GPU、无需运维推理服务、按量付费。但如果数据隐私要求高或用量极大，自部署 vLLM 是更好的选择。
