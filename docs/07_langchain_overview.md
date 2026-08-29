# LangChain 概览

> 来源：LangChain 官方文档 https://docs.langchain.com/oss/python/langchain/overview

## LangChain 是什么

LangChain 提供 `create_agent`：一个最小化、高度可配置的 agent 框架（harness）。核心公式是 **Agent = Model + Harness**——harness 是模型循环之外的一切：prompt、工具（tools）以及塑造行为的中间件（middleware）。从基本原语（primitives）开始，组合出用例所需的确切 agent。

## LangChain 与相关框架的分工

- **Deep Agents**：适合需要"开箱即用"的 agent，特性包括自动上下文压缩、虚拟文件系统、子 agent 生成。它构建在 LangChain agents 之上。
- **LangChain**（`create_agent`）：适合高度可定制的框架，便于针对具体用例和数据定制。
- **LangGraph**：底层编排框架，适合需要结合确定性和 agentic 工作流的高级需求。
- **LangSmith**：用于跟踪、调试、评估这些框架构建的 agent，能监控 trace、检测问题、提出修复建议。

## 创建 agent 示例

```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="openai:gpt-5.5",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)
```

## 核心概念：Agent 的组成

一个 agent 由四部分组成：

1. **模型（Model）**：驱动推理的大语言模型，支持 OpenAI、Anthropic、Google 等多家提供商。
2. **工具（Tools）**：agent 可调用的外部能力（如自定义函数、API），让模型能执行实际操作。
3. **提示词（Prompt / system prompt）**：设定 agent 的角色、行为和约束。
4. **中间件（Middleware）**：塑造 agent 行为的可配置逻辑，在模型循环中插入处理。

## 核心优势

LangChain 的 harness 是围绕模型循环的一切：prompt、tools 和塑造行为的中间件。从原语开始组合，能精确构建用例所需的能力。文档同时支持连接到 Claude、VSCode 等工具（通过 MCP）以获取实时答案。

## 生态

LangChain 生态包含：LangGraph（低级编排）、LangSmith（可观测性/评估）、Deep Agents（电池全配的 agent）等，覆盖从原型到生产的完整链路。
