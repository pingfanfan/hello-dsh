---
name: error-handling
description: 当需要设计错误处理、决定该抛还是该返回、写错误信息、或排查"出错了但没人知道"的问题时使用——按调用方是否需要区分处理来决定错误的结构。
---

# 错误处理

**核心问题只有一个：调用方拿到这个失败之后，需要做出不同的反应吗？**

需要，错误就必须可区分；不需要，一个通用错误就够。所有其他决定都从这里推出来。

## 最该避免的：静默失败

比崩溃危险得多的是「出错了但没人知道」。三种典型形态：

```js
// 一、吞掉
try { doThing() } catch (e) { }

// 二、用默认值兜底，调用方无法区分"成功返回空"和"失败了"
try { return parse(x) } catch { return {} }

// 三、替换成通用错误，丢失原始信息
try { await sandbox.run() } catch { throw new Error('EXEC_FAILED') }
```

第三种最隐蔽。DSH 有个真实事故：沙箱抛出的结构化 `SandboxUnavailableError` 被上层捕获后替换成了通用的 `SEARCH_FAILED`，调用方彻底失去了判断依据，排查花了很久。

**捕获之后如果不能真正处理它，就不要捕获。**

## 抛还是返回

| 情况 | 做法 |
|---|---|
| 预期内的失败，调用方一定要处理 | **返回**（`Result` 类型或 `undefined`） |
| 违反前置条件、编程错误 | **抛** |
| 外部系统失败 | **抛**，但要带结构化信息 |
| "没找到" | 看语义：查询用返回，按 id 取用抛 |

判断依据：**这个失败是不是正常业务流程的一部分？** 是就返回，不是就抛。

「用户输入的邮箱格式不对」是正常流程，返回。「配置文件里缺了必填项」是编程/部署错误，抛。

## 错误要可区分

```js
// 差：调用方只能靠匹配消息文本
throw new Error('session not found')

// 好
class NotFoundError extends Error {
  constructor(resource, id) {
    super(`${resource} not found: ${id}`)
    this.code = 'NOT_FOUND'
    this.resource = resource
    this.id = id
  }
}
```

**靠解析错误消息来做流程判断，是最脆弱的耦合。** 消息一改，调用方就挂，而且没有任何编译期提示。

## 错误信息写给谁

区分两个受众：

**给用户的**：说清发生了什么、下一步做什么。不要暴露内部结构。

```
✗ ECONNREFUSED 127.0.0.1:5432
✓ 连不上数据库。检查 DATABASE_URL 配置，或确认数据库服务在运行。
```

**给开发者的（日志）**：保留全部上下文。

```js
logger.error('会话恢复失败', {
  sessionId, step: 'projection', eventCount, cause: err
})
```

好的错误信息包含三样：**发生了什么、在什么上下文、下一步做什么**。缺第三样的错误信息只完成了一半工作。

## 保留因果链

包装错误时不要丢掉原因：

```js
// 差：原始堆栈没了
catch (err) { throw new Error('加载配置失败') }

// 好
catch (err) { throw new Error('加载配置失败', { cause: err }) }
```

## 部分失败

批量操作要想清楚语义，并写进文档：

- **全成功或全失败**（事务性）
- **尽力而为，返回每一项的结果**
- **遇错即停，返回已完成的部分**

三种都合理，但**必须明确是哪种**，且返回值要让调用方能知道哪些成功了。最糟的是「抛一个错，调用方不知道已经做了多少」。

## 清理

失败路径上的资源清理最容易漏。

```js
// 差：抛错时 conn 泄漏
const conn = await pool.acquire()
const r = await conn.query(sql)
conn.release()
return r

// 好
const conn = await pool.acquire()
try { return await conn.query(sql) }
finally { conn.release() }
```

规则：**每个获取都要有 `finally` 里的释放**，或者用语言提供的自动释放机制。

## 不要做的事

- 不要空 catch
- 不要把错误替换成不含原因的通用错误
- 不要用错误消息文本做流程控制
- 不要在错误信息里泄漏凭据、完整路径、内部结构
- 不要捕获你处理不了的错误
- 不要让调用方猜「返回空」是成功还是失败
- 不要在 catch 里只打日志然后继续，除非你确定继续是对的
