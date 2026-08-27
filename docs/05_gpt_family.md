# GPT 模型家族

## GPT 的演进

GPT（Generative Pre-trained Transformer）是 OpenAI 提出的生成式预训练模型。GPT-1 首次验证了"预训练+微调"范式的可行性。GPT-2 展示了 zero-shot 能力。GPT-3 以 1750 亿参数展示了 few-shot 学习的强大能力。

GPT-4 引入了多模态能力，可以处理图像和文本。GPT-4o 进一步实现了实时语音交互。GPT 系列只使用 Transformer 的解码器部分，通过自回归方式生成文本。

## In-Context Learning

GPT-3 的最大贡献是展示了大模型的上下文学习能力。通过在 prompt 中给出少量示例，模型就能学会新任务，无需微调。这被称为 few-shot learning。

## 从 GPT 到 Qwen

Qwen 是阿里巴巴推出的大语言模型系列。Qwen2.5 是最新版本，支持中英文，在多项基准测试上表现优秀。Qwen2.5-7B 是中小参数量版本，适合部署在消费级硬件上，也是硅基流动等平台提供的免费模型之一。

## 开源大模型生态

除了 Qwen，主流开源大模型还包括 Meta 的 LLaMA、Mistral AI 的 Mistral/Mixtral、DeepSeek 等。这些模型推动了 AI 应用的发展，降低了使用门槛。
