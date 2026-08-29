# FastAPI 请求体（Request Body）

> 来源：FastAPI 官方文档 https://fastapi.tiangolo.com/tutorial/body/

## 什么是请求体

当需要把数据从客户端（比如浏览器）发送到 API 时，你把它作为请求体（request body）发送。请求体是客户端发送给 API 的数据，响应体（response body）是 API 发送给客户端的数据。

要声明请求体，使用 Pydantic 模型（继承 `BaseModel` 的类）及其全部能力。发送数据应使用 `POST`（最常见）、`PUT`、`DELETE` 或 `PATCH`。

## 声明请求体模型

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

模型属性有默认值则非必填，否则必填。用 `None` 使其可选。上面这个模型声明了这样一个 JSON 对象（`description` 和 `tax` 可选）：

```json
{
    "name": "Foo",
    "description": "An optional description",
    "price": 45.2,
    "tax": 3.5
}
```

## FastAPI 自动完成的工作

仅凭 Python 类型声明，FastAPI 会：把请求体读取为 JSON；转换相应类型（如需要）；验证数据（无效则返回清晰错误，指出具体位置和错误内容）；把收到的数据放进参数 `item`；为模型生成 JSON Schema 定义，成为 OpenAPI schema 的一部分，用于自动文档 UI。

## 参数识别规则

函数参数按以下规则识别：

- 如果参数也在路径中声明，则作为路径参数；
- 如果参数是单一类型（如 `int`、`float`、`str`、`bool`），则解释为查询参数；
- 如果参数声明为 Pydantic 模型类型，则解释为请求体。

## 请求体 + 路径 + 查询参数

可以同时声明 body、path 和 query 参数，FastAPI 会从正确位置取数据：

```python
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result
```

注意：FastAPI 通过参数的默认值 `= None` 判断它是否必填，而不是通过类型注解 `str | None`。类型注解用于让编辑器提供更好的支持和错误检测。

## 不使用 Pydantic 的情况

如果不想用 Pydantic 模型，也可以使用 `Body` 参数（在 body-multiple-params 文档中说明）。
