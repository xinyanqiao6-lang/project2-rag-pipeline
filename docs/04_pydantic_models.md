# Pydantic 模型（Models）

> 来源：Pydantic 官方文档 https://docs.pydantic.dev/latest/concepts/models/

## 什么是模型

在 Pydantic 中，定义 schema 的主要方式之一就是通过模型（Models）。模型是继承自 `BaseModel` 的类，通过带类型注解的属性定义字段。可以把模型类比为 C 语言中的 struct。

不可信数据可以传入模型，经过解析和验证之后，Pydantic 保证生成的模型实例的字段会符合模型上定义的字段类型。当数据无法成功解析为模型实例时，Pydantic 会抛出 `ValidationError`。

## 基本模型用法

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    id: int
    name: str = 'Jane Doe'
    model_config = ConfigDict(str_max_length=10)
```

这个 `User` 模型有两个字段：`id`（int，必填）、`name`（str，有默认值，非必填）。初始化对象时执行所有解析和验证：

```python
user = User(id='123')  # 字符串 '123' 被强制转换为整数 123
assert user.id == 123
assert user.name == 'Jane Doe'
```

`model_fields_set` 属性可以检查初始化时显式设置了哪些字段。

## 核心方法

模型类拥有的关键方法：

- `model_validate()`：根据模型验证给定对象
- `model_validate_json()`：验证 JSON 数据
- `model_construct()`：不运行验证地创建模型
- `model_dump()`：返回模型字段和值的字典
- `model_dump_json()`：返回 JSON 字符串
- `model_copy()`：返回模型副本（默认浅拷贝）
- `model_json_schema()`：返回 JSON Schema

## 数据转换与严格模式

Pydantic 会转换输入数据以符合字段类型。例如 `Model(a=3.000, b='2.72')` 会把 a 转成 `3`、b 转成 `2.72`。这是刻意设计，通常最有用。Pydantic 也提供严格模式（strict mode），在该模式下不执行任何数据转换，值必须与声明的字段类型完全相同。

## 额外数据（Extra data）

默认情况下，Pydantic 模型在提供额外数据时不会报错，这些值被简单忽略。`extra` 配置项控制此行为，可取三个值：

- `'ignore'`：忽略额外数据（默认）
- `'forbid'`：不允许额外数据（会报错）
- `'allow'`：允许并存储在 `__pydantic_extra__` 字典中

## 嵌套模型

更复杂的层次化数据结构可以用模型本身作为注解类型定义：

```python
from typing import Optional
from pydantic import BaseModel

class Foo(BaseModel):
    count: int
    size: Optional[float] = None

class Bar(BaseModel):
    apple: str = 'x'
    banana: str = 'y'

class Spam(BaseModel):
    foo: Foo
    bars: list[Bar]

m = Spam(foo={'count': 4}, bars=[{'apple': 'x1'}, {'apple': 'x2'}])
```

自引用模型也受支持（配合 `model_rebuild()` 使用）。

## 验证的三种模式

Pydantic 可以在三种模式下验证数据：Python 模式、JSON 模式和 strings 模式。分别对应 `__init__()`/`model_validate()`、`model_validate_json()`、`model_validate_strings()`。

`model_construct()` 允许不经过验证创建模型，适用于处理已知有效的复杂数据（性能考虑）或验证器有副作用的场景。但用它创建的可能是无效模型，只应对已验证或绝对信任的数据使用。

## 错误处理

验证数据时发现错误，Pydantic 抛出 `ValidationError`。无论发现多少个错误，都只抛出一个异常，包含所有错误的信息和发生位置。

## 泛型模型

Pydantic 支持泛型模型，复用通用结构。定义要点：声明 `TypeVar`、同时继承 `BaseModel` 和 `typing.Generic`（必须此顺序）、在注解位置使用类型变量。参数化时 Pydantic 会在运行时创建泛型模型的子类，这些类会被缓存，开销极小。

## 伪不可变性（Frozen）

模型可通过 `model_config['frozen'] = True` 配置为不可变。设置后修改实例属性会报错。注意 Python 中的不可变性并非强制性的——即使模型 frozen，其内部的可变字段（如 dict）仍可修改。
