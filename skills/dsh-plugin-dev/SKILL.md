---
name: dsh-plugin-dev
description: 当需要给 DeepSeek Harness 写插件、调试插件没加载或没注入的问题、或理解 Cordis 的组件生命周期时使用——覆盖导出规则、依赖声明、可逆效应和加载路径陷阱。
---

# 给 DSH 写插件

插件是 TypeScript 模块，跑在 Cordis 之上。DSH 处于 developer preview，官方明确警告有破坏性变更，所以任何行为都要在当前版本上验证。

**先问一句：这件事非要插件不可吗？** 如果用自然语言就能说清楚要模型做什么，写技能（一个 Markdown 文件）成本低一个数量级，也不会被上游 API 变更打挂。需要执行代码、接外部服务、挂生命周期钩子的，才需要插件。

## 最小形态

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'my-plugin'
export const inject = ['tools']

export function apply(ctx: Context) {
  // 在这里注册能力
}
```

加载方式是写一个 overlay：

```yaml
- insert:
    - id: my-plugin
      name: '/absolute/path/to/my-plugin.ts'
```

```sh
dsh web --patch ./my-plugin/cordis.yml
```

**路径必须是绝对路径**，官方文档明确要求，相对路径不会被解析。

## 第一个致命陷阱：不要写 default export

这条有官方事故复盘（`docs/postmortem/0001`），值得完整理解。

```ts
export const name = 'acp'
export const inject = ['agents', 'sessions']
export function apply(ctx, config) { }
export default apply          // ← 这一行会让插件彻底失效
```

Loader 的 `unwrapExports` 逻辑是 `exports.default ?? exports`，优先取默认导出。有 `export default` 时，它解析出来的是**裸的 apply 函数**，而 `inject`、`name`、`Config` 是挂在模块命名空间上的同级命名导出，取 `.default` 那一步把整个命名空间丢掉了。

Loader 于是用一个空的 `inject` 构建 fiber。插件在什么服务都没注入的环境里运行，第一次访问 `ctx.xxx` 时沿 fiber 树一路找到根，抛出 `cannot get property "agents" without inject`。

**崩在加载时，不是请求处理时。**

当时这个 bug 有 178 个绿色测试和 100% 行覆盖率，因为所有测试都是手动挂载插件的，绕过了真实 Loader 路径。

**规则：命名空间插件只用命名导出，绝不加 default export。**

## 第二个致命陷阱：`!!js` 只在 config 里有效

同样有官方复盘（`docs/postmortem/0002`）。

```yaml
- insert:
    - id: fs
      name: '@deepseek-ai/dsh-tool-fs'
      disabled: !!js ctx.mode !== 'full'    # ← 永远为真
      config:
        root: !!js process.cwd()            # ← 这里才有效
```

Cordis 只对插件的 `config` 做递归插值。`disabled`、`isolate`、`intercept` 这些配置项元数据是直接读取的，拿到的是表达式对象，而对象恒为 truthy。结果是插件在所有模式下永久禁用，且无任何诊断。

**规则：条件组合用显式的 overlay 文件，不要在元数据字段上写表达式。**

## 依赖声明

```ts
export const inject = ['tools', 'agents']
```

`inject` 声明这个插件需要哪些服务。Cordis 的行为是**反应式**的：

- 依赖不满足时，组件**保持不激活**，不报错
- 依赖出现时自动激活
- 提供方卸载时，依赖它的消费者**先**停用，提供方再回收资源
- 循环依赖会让相关组件永久不激活，且这个状态可以从声明本身预测出来

所以「插件没生效但也没报错」时，第一个怀疑对象是依赖没满足。

访问未声明的服务会抛 `UNDECLARED_ACCESS`；声明了但提供方未加载时抛 `INACTIVE_ACCESS`。这两个错误信息能直接告诉你是哪种情况。

## 可逆效应：注册必须能撤销

Cordis 的核心机制是**每个作用都携带它的逆操作**，运行时追踪，卸载时按 LIFO 顺序恢复。

```ts
export function apply(ctx: Context) {
  ctx.effect(() => {
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)   // 逆操作和创建写在一起
  })
}
```

**关键点：逆操作的正确性是插件作者的义务，运行时不验证。** 官方文档原文说这是 "an obligation on the component author rather than a property the runtime verifies"。

也就是说，你漏掉一个 `clearInterval`，Cordis 不会告诉你，只会在插件卸载后留下一个还在跑的定时器。热重载时这类泄漏会累积。

自测方法：加载卸载十次，看注册数、监听器数、定时器数是否回到初始值。

## 调试

**先看组装后的配置，不启动服务：**

```sh
dsh --profile web --dump-config
```

排查顺序：

1. 插件在 `--dump-config` 输出里吗（不在 = 配置没生效）
2. 它被 `disabled` 掉了吗（回到 `!!js` 陷阱）
3. 有 default export 吗（回到第一个陷阱）
4. `inject` 声明的服务都有提供方吗

也可以直接扫：

```sh
npx dsh-doctor
```

## 测试

**必须走真实入口。** 手动挂载插件的测试无法发现 Loader 层的问题，DSH 自己就栽在这上面。

至少有一个测试是通过真实的 Loader、真实的 `cordis.yml` 加载插件的。

## 不要做的事

- 不要写 `export default`
- 不要在 `disabled`/`isolate`/`intercept` 上用 `!!js`
- 不要用相对路径
- 不要在 `apply` 外面持有可变全局状态（会逃出 fiber 生命周期）
- 不要注册了不写清理
- 不要只用手动挂载的方式测试
- 不要为了一个能用自然语言说清的需求写插件，那应该是技能
