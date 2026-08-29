# FastAPI 依赖注入

> 来源：FastAPI 官方文档 https://fastapi.tiangolo.com/tutorial/dependencies/

## 什么是依赖注入

依赖注入（Dependency Injection）意味着，在编程中，有一种方式让你的代码（路径操作函数）声明它需要使用的"依赖"，然后系统（FastAPI）负责提供这些依赖（"注入"依赖）。

依赖注入在以下场景非常有用：共享逻辑（同一段代码逻辑反复使用）、共享数据库连接、强制安全/认证/角色要求等，同时最小化代码重复。

## 基本用法

依赖本质上就是一个函数，可以接收和路径操作函数相同的所有参数。使用 `Depends` 声明依赖：

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons

@app.get("/users/")
async def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

你只给 `Depends` 一个参数，这个参数必须是一个函数（不要直接调用它，不要加括号）。每当新请求到达，FastAPI 会负责：用正确的参数调用依赖函数、获取结果、把结果赋给路径操作函数的参数。

## 共享依赖（type alias）

由于使用 `Annotated`，可以把带类型注解的 `Depends()` 存进变量，在多个地方复用：

```python
CommonsDep = Annotated[dict, Depends(common_parameters)]

@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons

@app.get("/users/")
async def read_users(commons: CommonsDep):
    return commons
```

这只是标准 Python 的 type alias（类型别名），不是 FastAPI 特有的。好处是类型信息被保留，编辑器能继续提供自动补全、内联错误检查，`mypy` 等工具也能正常工作。在大型代码库中反复使用相同依赖时尤其有用。

## 依赖的 async 规则

依赖和路径操作函数一样由 FastAPI 调用，因此定义函数时同样适用 async 规则：可以用 `async def` 或普通 `def`，也可以混合（`async def` 依赖用在普通 `def` 路径操作函数里，或反之），FastAPI 都会正确处理。

## 依赖的层级（子依赖）

依赖注入系统虽然定义简单，但非常强大。你可以定义依赖，依赖本身又可以定义依赖。最终会构建一棵分层的依赖树，依赖注入系统负责解决所有这些依赖（以及子依赖），并在每一步提供（注入）结果。

例如有 4 个端点 `/items/public/`、`/items/private/`、`/users/{user_id}/activate`、`/items/pro/`，你可以仅通过依赖和子依赖为它们各自添加不同的权限要求。

## 与其他术语的对应

依赖注入这个概念的其他常见术语包括：resources（资源）、providers（提供者）、services（服务）、injectables（可注入对象）、components（组件）。

## 与 OpenAPI 集成

所有依赖（和子依赖）的请求声明、验证和要求都会集成到同一个 OpenAPI schema 中，因此交互式文档也会包含这些依赖的信息。

依赖注入系统的简洁性使 FastAPI 兼容所有关系型数据库、NoSQL 数据库、外部包、外部 API、认证授权系统、API 监控系统等。
