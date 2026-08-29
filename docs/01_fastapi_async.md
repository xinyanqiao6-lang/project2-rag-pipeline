# FastAPI 并发与 async/await

> 来源：FastAPI 官方文档 https://fastapi.tiangolo.com/async/

## 什么是异步代码

异步代码意味着语言提供一种方式，告诉程序：在代码的某个时刻，必须等待"其他事情"在其他地方完成（例如一个"慢速文件"或网络请求）。在等待期间，计算机可以去执行其他工作，等慢任务完成后再回来继续处理。

"等待其他事情"通常指相对较慢的 I/O 操作，例如：客户端通过网络发送数据、远程 API 操作完成、数据库操作完成、磁盘读写。由于执行时间主要消耗在等待 I/O 上，这类操作被称为 I/O bound（I/O 密集型）操作。

大多数 Web 应用正是如此：服务器在等待众多用户的网络请求和响应。这种异步特性正是 NodeJS 流行的原因，也是 Go 语言的优势所在，FastAPI 也能提供相同级别的性能。

## 何时使用 async def

如果使用的第三方库要求通过 `await` 调用，则用 `async def` 声明路径操作函数：

```python
@app.get('/')
async def read_results():
    results = await some_library()
    return results
```

如果第三方库需要与外部通信（数据库、API、文件系统等）但不支持 `await`（目前大多数数据库库都是如此），则按正常方式用 `def` 声明：

```python
@app.get('/')
def results():
    results = some_library()
    return results
```

可以在路径操作函数中按需混合使用 `def` 和 `async def`，FastAPI 会正确处理它们。

## async 和 await 的技术细节

现代 Python 通过 `async` 和 `await` 语法支持异步代码。`await` 必须放在用 `async def` 声明的函数内部。同时，`async def` 函数必须被 `await`——因此 `async def` 函数也只能在 `async def` 函数内部被调用。

在 FastAPI 中无需担心"鸡生蛋"问题（如何调用第一个 async 函数），因为那个"第一个"函数就是路径操作函数，FastAPI 知道如何处理。

协程（Coroutine）是对 `async def` 函数返回结果的术语称呼。它可以在内部遇到 `await` 时被暂停。这整套功能可类比 Go 语言的 Goroutines。

## 技术细节：def 与 async def 的运行方式

用普通 `def`（而非 `async def`）声明路径操作函数时，它会在外部线程池中运行并被 `await`，而不是被直接调用（因为直接调用会阻塞服务器）。

这与某些其他异步框架相反：在 FastAPI 中，最好使用 `async def`，除非路径操作函数包含执行阻塞 I/O 的代码。依赖项同理——如果依赖是标准 `def` 函数而非 `async def`，它也会在外部线程池中运行。

## 核心要点

| 场景 | 使用方式 |
|------|----------|
| 三方库支持 `await` | `async def` |
| 三方库不支持 `await`（如大多数数据库库） | 普通 `def` |
| 无需与外部通信等待响应 | `async def` |
| 不确定 | 普通 `def` |

关键区别：普通 `def` 路径操作函数和依赖项会在外部线程池中运行并被 await；`async def` 则直接参与异步事件循环，不会额外占用线程池资源。
