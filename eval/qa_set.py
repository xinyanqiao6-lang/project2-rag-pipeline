"""评测集 v2：45 道题 × 4 类难度，核心是**引入负样本与干扰项让指标不再饱和**。

## v1 的问题（必须先说清，否则改动的意义讲不清）
v1 只有 10 道题，全是"在这份文档里直白地问一句话"，于是
**三种切分策略的 Top-5 命中率全是 100%、MRR 全是 1.0000**。

满分指标不是优点，是**评测集没有区分度**的证据：
它证明不了任何改进有效，也无法说明系统能力的边界在哪。

## v2 的四类题目
1. `fact`（12 题）事实检索——和 v1 同类，但覆盖全部 7 份文档
2. `cross_doc`（10 题）跨文档推理——答案需综合两份以上文档
   （例：Docker 镜像与容器的关系 + FastAPI 启动方式 → 容器化部署 API 服务的完整链路）
3. `confusable`（11 题）易混淆干扰——故意用相邻领域的词面做干扰
   （例：问「Pydantic 模型字段定义」但干扰文档里全是 "model" 字样）
4. `negative`（12 题）**无答案题**——语料里根本没有答案，正确行为是**拒答**
   这一类最关键：它同时检验幻觉率与拒答能力，是 v1 完全缺失的维度。

## 指标口径
- `fact/cross_doc/confusable`：算 Hit@k 与 MRR（k 默认 5）
- `negative`：算**拒答正确率**（检索得分低于阈值 → 判拒答）与**幻觉率**
  （自信地给出一个错答案）。这一类不进 MRR，否则会污染检索指标。
"""
from __future__ import annotations

# ground_truth 为答案所在 doc_id；negative 类为 None（正确答案 = 明确拒答）
QUESTIONS: list[dict] = [
    # ---------- 1. 事实检索 12 题 ----------
    {"id": "f01", "type": "fact", "q": "FastAPI 中 async def 和普通 def 的路径操作函数在运行方式上有什么区别？", "gt_doc": "01_fastapi_async"},
    {"id": "f02", "type": "fact", "q": "FastAPI 的依赖注入用什么声明，依赖函数可以嵌套吗？", "gt_doc": "02_fastapi_dependencies"},
    {"id": "f03", "type": "fact", "q": "FastAPI 如何声明一个请求体，用什么类型的参数？", "gt_doc": "03_fastapi_request_body"},
    {"id": "f04", "type": "fact", "q": "Pydantic 中模型如何定义，用什么类继承？", "gt_doc": "04_pydantic_models"},
    {"id": "f05", "type": "fact", "q": "Pydantic 模型的 extra 配置项可以取哪三个值？", "gt_doc": "04_pydantic_models"},
    {"id": "f06", "type": "fact", "q": "HTTPX 如何发送 JSON 编码的数据？", "gt_doc": "05_httpx_quickstart"},
    {"id": "f07", "type": "fact", "q": "HTTPX 最重要的两个异常类是什么？", "gt_doc": "05_httpx_quickstart"},
    {"id": "f08", "type": "fact", "q": "Docker 客户端-服务器架构中，负责构建和运行容器的守护进程叫什么？", "gt_doc": "06_docker_overview"},
    {"id": "f09", "type": "fact", "q": "Docker 镜像和容器是什么关系？", "gt_doc": "06_docker_overview"},
    {"id": "f10", "type": "fact", "q": "LangChain 的 create_agent 核心公式是什么，agent 由哪几部分组成？", "gt_doc": "07_langchain_overview"},
    {"id": "f11", "type": "fact", "q": "HTTPX 相比 requests 在异步支持上有什么优势？", "gt_doc": "05_httpx_quickstart"},
    {"id": "f12", "type": "fact", "q": "Docker 容器之间如何通信，共享数据要用什么机制？", "gt_doc": "06_docker_overview"},

    # ---------- 2. 跨文档推理 10 题（答案分散在多份文档）----------
    {"id": "c01", "type": "cross_doc", "q": "我要把一个 FastAPI 服务用 Docker 容器化上线，FastAPI 的异步模型和 Docker 的镜像分层分别该怎么用？", "gt_doc": "01_fastapi_async", "also": ["06_docker_overview"]},
    {"id": "c02", "type": "cross_doc", "q": "容器里的 FastAPI 服务要请求外部 API，用 HTTPX 的异步客户端和容器的端口映射该怎么配合？", "gt_doc": "05_httpx_quickstart", "also": ["06_docker_overview"]},
    {"id": "c03", "type": "cross_doc", "q": "FastAPI 接收的 JSON 请求体要校验，用 Pydantic 模型和容器的环境变量配置该怎么配合？", "gt_doc": "04_pydantic_models", "also": ["03_fastapi_request_body"]},
    {"id": "c04", "type": "cross_doc", "q": "用 LangChain 搭一个能查 HTTPX 文档的 Agent，Agent 的工具应该怎么定义？", "gt_doc": "07_langchain_overview", "also": ["05_httpx_quickstart"]},
    {"id": "c05", "type": "cross_doc", "q": "Pydantic 校验失败的报错怎么通过 FastAPI 返回给客户端？", "gt_doc": "04_pydantic_models", "also": ["03_fastapi_request_body"]},
    {"id": "c06", "type": "cross_doc", "q": "在 Docker 容器里跑异步 FastAPI 服务，事件循环和守护进程的关系是什么？", "gt_doc": "06_docker_overview", "also": ["01_fastapi_async"]},
    {"id": "c07", "type": "cross_doc", "q": "HTTPX 的超时异常和 FastAPI 的依赖注入冲突处理该怎么配合？", "gt_doc": "05_httpx_quickstart", "also": ["02_fastapi_dependencies"]},
    {"id": "c08", "type": "cross_doc", "q": "Docker 镜像里装 Python 服务时，镜像分层和依赖缓存策略怎么设计？", "gt_doc": "06_docker_overview", "also": ["01_fastapi_async"]},
    {"id": "c09", "type": "cross_doc", "q": "LangChain Agent 调用外部工具时，工具描述和 Pydantic 模型定义的关系是什么？", "gt_doc": "07_langchain_overview", "also": ["04_pydantic_models"]},
    {"id": "c10", "type": "cross_doc", "q": "FastAPI 的依赖缓存机制和 Docker 的容器隔离，各自解决什么问题？", "gt_doc": "02_fastapi_dependencies", "also": ["06_docker_overview"]},

    # ---------- 3. 易混淆干扰 11 题（相邻领域词面做干扰）----------
    {"id": "x01", "type": "confusable", "q": "Pydantic 模型里怎么定义字段类型？和 FastAPI 的依赖注入有什么区别？", "gt_doc": "04_pydantic_models"},
    {"id": "x02", "type": "confusable", "q": "HTTPX 里怎么设置请求超时？和 Docker 的构建超时有什么区别？", "gt_doc": "05_httpx_quickstart"},
    {"id": "x03", "type": "confusable", "q": "FastAPI 的 path operation 参数怎么声明？和请求体参数怎么区分？", "gt_doc": "03_fastapi_request_body"},
    {"id": "x04", "type": "confusable", "q": "LangChain 的 agent 是什么？和 FastAPI 的依赖注入是什么关系？", "gt_doc": "07_langchain_overview"},
    {"id": "x05", "type": "confusable", "q": "Docker 的 image 和 container 术语怎么区分？和 Python 的模型类比有关系吗？", "gt_doc": "06_docker_overview"},
    {"id": "x06", "type": "confusable", "q": "async 和 await 在 FastAPI 里怎么用？和 HTTPX 的异步请求怎么配合？", "gt_doc": "01_fastapi_async"},
    {"id": "x07", "type": "confusable", "q": "Pydantic 的 extra 字段配置和 FastAPI 的额外参数声明冲突吗？", "gt_doc": "04_pydantic_models"},
    {"id": "x08", "type": "confusable", "q": "HTTPX 发送 form 数据还是 JSON 数据？和 FastAPI 请求体类型对应吗？", "gt_doc": "05_httpx_quickstart"},
    {"id": "x09", "type": "confusable", "q": "Docker Compose 和 Docker 守护进程的关系？和微服务依赖管理像吗？", "gt_doc": "06_docker_overview"},
    {"id": "x10", "type": "confusable", "q": "LangChain 里如何注册自定义工具？和 FastAPI 注册路由像吗？", "gt_doc": "07_langchain_overview"},
    {"id": "x11", "type": "confusable", "q": "Pydantic 模型可以嵌套吗？和 FastAPI 的嵌套依赖像吗？", "gt_doc": "04_pydantic_models"},

    # ---------- 4. 无答案题 12 题（正确行为 = 拒答）----------
    {"id": "n01", "type": "negative", "q": "FastAPI 如何配置 Redis 缓存中间件？", "gt_doc": None},
    {"id": "n02", "type": "negative", "q": "Pydantic v2 的 field_validator 装饰器怎么用？", "gt_doc": None},
    {"id": "n03", "type": "negative", "q": "Docker 集群如何做服务发现和高可用？", "gt_doc": None},
    {"id": "n04", "type": "negative", "q": "LangChain 的 Memory 组件怎么持久化对话历史？", "gt_doc": None},
    {"id": "n05", "type": "negative", "q": "HTTPX 怎么配置 SOCKS 代理？", "gt_doc": None},
    {"id": "n06", "type": "negative", "q": "FastAPI 怎么实现 JWT 鉴权？", "gt_doc": None},
    {"id": "n07", "type": "negative", "q": "Pydantic 的 ORM 模式怎么和 SQLAlchemy 配合？", "gt_doc": None},
    {"id": "n08", "type": "negative", "q": "Docker 镜像怎么压缩到最小体积？", "gt_doc": None},
    {"id": "n09", "type": "negative", "q": "LangChain 怎么接入向量数据库做检索增强？", "gt_doc": None},
    {"id": "n10", "type": "negative", "q": "HTTPX 的流式响应怎么实现？", "gt_doc": None},
    {"id": "n11", "type": "negative", "q": "FastAPI 支持 gRPC 协议吗？", "gt_doc": None},
    {"id": "n12", "type": "negative", "q": "Pydantic 模型怎么做性能基准测试？", "gt_doc": None},
]

ANSWERABLE = [q for q in QUESTIONS if q["type"] != "negative"]
NEGATIVE = [q for q in QUESTIONS if q["type"] == "negative"]

TYPE_DESC = {
    "fact": "事实检索（单一文档内直白问答）",
    "cross_doc": "跨文档推理（答案分散在 2-3 份文档）",
    "confusable": "易混淆干扰（相邻领域词面做干扰）",
    "negative": "无答案题（正确行为是拒答）",
}


def stats() -> dict:
    out = {}
    for t in ("fact", "cross_doc", "confusable", "negative"):
        out[t] = len([q for q in QUESTIONS if q["type"] == t])
    out["total"] = len(QUESTIONS)
    return out


if __name__ == "__main__":
    print(stats())