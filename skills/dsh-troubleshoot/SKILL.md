---
name: dsh-troubleshoot
description: 当 DeepSeek Harness 起不来、插件没加载、技能不见了、工具报 UNKNOWN_TOOL、或出现"配置写了但没生效"这类静默失效时使用——按静默失效优先的顺序排查。
---

# DSH 排障

DSH 的故障有个特点：**很多问题不报错**。配置写了没生效、插件加载了但没注入、技能存在但不出现，这类静默失效比崩溃难查得多，所以要先排它们。

处于 developer preview，官方明确警告有破坏性变更。任何"应该可以"都要用命令验证。

## 先定位在哪一层

| 层 | 症状 |
|---|---|
| 进程起不来 | 端口占用、Node 版本、依赖安装失败 |
| 配置没生效 | 命令跑了但行为没变、插件像不存在 |
| 插件加载但异常 | `cannot get property X without inject` |
| 工具不存在 | `UNKNOWN_TOOL` |
| 技能不出现 | 文件在那儿但列表里没有 |
| 模型层 | 401、限流、余额 |

**先用这条命令确认组装后的配置，不启动服务：**

```sh
dsh --profile web --dump-config
```

它比读文档快，也比猜准。想知道某个插件到底加载了没有，直接 grep 它的输出。

## 静默失效：优先排查

### 一、`!!js` 写在了 config 之外

**这是官方自己踩过并写了复盘的坑**（`docs/postmortem/0002`）。

```yaml
- insert:
    - id: fs
      name: '@deepseek-ai/dsh-tool-fs'
      disabled: !!js ctx.mode !== 'full'    # ← 永远为真
```

Cordis **只在插件的 `config` 内部**对 `!!js` 求值。`disabled`、`isolate`、`intercept` 这些配置项元数据是直接读取的，拿到的是一个表达式对象，而对象恒为 truthy。结果是插件**在所有模式下永久禁用**，没有任何诊断信息。

修法：条件组合改用显式的 overlay 文件，不要在元数据字段上用表达式。

### 二、插件带了 default export

**同样有官方复盘**（`docs/postmortem/0001`）。症状是 `cannot get property "agents" without inject`。

```ts
export const name = 'acp'
export const inject = ['agents', 'sessions']
export function apply(ctx, config) { }
export default apply          // ← 就是这行
```

Loader 的 `unwrapExports` 优先取 `exports.default ?? exports`。有默认导出时它解析出裸的 `apply` 函数，而 `inject`、`name`、`Config` 作为同级命名导出被整体丢弃。插件于是在一个没注入任何服务的 fiber 里运行，第一次访问 `ctx.xxx` 就崩。

注意这个 bug 当时有 178 个绿色单元测试和 100% 行覆盖率，因为所有测试都是手动挂载插件的，绕过了真实 Loader 路径。

修法：删掉 default export，只保留命名导出。

### 三、技能不见了

先查 frontmatter 键名，**不要先查路径**：

```yaml
user-invocable: true       # 对
userInvocable: true        # 整条技能被丢弃，只有一条警告
```

调用策略键必须 kebab-case，值必须是布尔或 `yes`/`no`/`on`/`off`/`1`/`0`。写错的结果是**整个技能被丢弃**，不是忽略那个字段。

其次查：`name` 是不是 kebab-case、`description` 有没有缺、是不是放成了嵌套目录（只扫一层）。

### 四、`UNKNOWN_TOOL`

意味着模型调用了注册表里不存在的工具。顺序：

1. `--dump-config` 确认对应的插件真的在配置里
2. 确认它没有被 `disabled` 掉（回到第一条）
3. 确认它的 fiber 真的 ACTIVE，而不是因为依赖不满足停在 INACTIVE

**依赖不满足时组件会静默保持不活跃**，这是 Cordis 的设计：consumer 声明的依赖没有 provider 时它不会报错，只是不激活。

## 进程起不来

按出现频率：

- **`EADDRINUSE: 127.0.0.1:3080`** —— `lsof -nP -iTCP:3080 -sTCP:LISTEN` 看谁占的。最常见是自己之前的实例没退干净。
- **Node 版本** —— `node -v` 先确认，再排查别的方向。
- **首次 `npx` 很慢** —— 在下载，不是卡死。
- **路径含空格** —— 插件路径必须绝对路径，含空格务必加引号。

## 一条自查捷径

上面前三类问题可以直接扫出来：

```sh
npx dsh-doctor
```

只读工具，不改任何文件。每条检查都链到对应的官方文档或事故复盘。

## 提问前准备什么

官方 Issues 关闭，反馈走 GitHub Discussions。带上：

- `dsh --version`
- 操作系统与 Node 版本
- 最小复现步骤
- 完整报错，**脱敏掉 API Key 和主目录路径**
- `--dump-config` 的相关片段

带这些的问题会被认真对待，"用不了"不会。

## 不要做的事

- 不要在没有 `--dump-config` 的情况下猜配置有没有生效
- 不要看到「测试全绿」就认为配置正确，官方自己就栽在这上面
- 不要在真实项目上调试，新建空目录代价为零
- 不要把 API Key 贴进 issue 或日志
