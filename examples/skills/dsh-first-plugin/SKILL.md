---
name: dsh-first-plugin
description: 当需要从零做出并装上第一个 DSH 插件时使用——给出跑通的完整流程（写文件、写 overlay、加载、验证），以及实测会踩到的三个报错和它们的确切修法。
---

# 做出你的第一个 DSH 插件

这是一条**实测跑通过**的路径，不是从文档推的。下面每个报错都真实遇到过，修法也都验证过。

环境：DSH `0.1.0-rc.6`，Node 20+。

## 先问一句：真的需要插件吗

如果你想做的事用自然语言就能说清楚（改变模型的判断标准、输出格式、工作流程），**写技能**，一个 Markdown 文件，五分钟搞定，也不会被上游 API 变更打挂。

只有需要**注册新工具、接外部服务、挂生命周期钩子**时才需要插件。

## 完整流程

### 一、装 DSH，确认能跑

```sh
npx @deepseek-ai/dsh --version
```

### 二、写插件

`hello-plugin/src/hello.ts`：

```ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'hello-plugin'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'pingfan_hello',
    description: '返回一句固定问候，用于验证第三方插件是否加载成功。',
    parameters: {
      who: { type: 'string', description: '要问候的对象' },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          greeting: { type: 'string', required: true },
        },
      },
      render: (_args, value) => [{ type: 'text', text: value.greeting }],
    },
    execute(args) {
      const who = args.who ?? 'world'
      return Promise.resolve({ greeting: `HELLO to ${who}` })
    },
  }))
}
```

### 三、写 overlay

`hello-plugin/cordis.yml`：

```yaml
- insert:
    - id: hello
      name: '/绝对/路径/hello-plugin/src/hello.ts'
```

**路径必须是绝对路径。** 生成方式：

```sh
cat > cordis.yml <<EOF
- insert:
    - id: hello
      name: '$(pwd)/src/hello.ts'
EOF
```

### 四、加载并验证

```sh
DEEPSEEK_API_KEY=sk-xxx npx @deepseek-ai/dsh --profile headless \
  --patch ./cordis.yml "调用 pingfan_hello 工具，参数 who 填 test"
```

看到工具返回的内容就说明成功了。

Web UI 同理：

```sh
npx @deepseek-ai/dsh web --patch ./cordis.yml
```

## 实测踩到的三个报错

按遇到的顺序，都是真实报错原文。

### 报错一：`must declare output { schema, render, presentationMeta? }`

```
tool "pingfan_hello" must declare output { schema, render, presentationMeta? }
```

**原因**：工具注册必须声明 `output`，里面要有 `schema`（返回值的结构）和 `render`（怎么渲染给模型看）。只写 `name`/`description`/`parameters` 不够。

**修法**：补上 `output` 块，见上面的完整例子。

### 报错二：`parameters.who.required must be true when present`

```
code: 'UNSUPPORTED_SCHEMA',
violations: [ 'parameters.who.required must be true when present' ]
```

**原因**：`required` 字段**只能填 `true`**。想表示可选参数，直接把 `required` 省略掉，不能写 `required: false`。

**修法**：

```ts
who: { type: 'string', required: false }   // ✗ 报错
who: { type: 'string' }                    // ✓ 可选
who: { type: 'string', required: true }    // ✓ 必填
```

### 报错三：`cannot get property "xxx" without inject`

**原因**：你的模块里有 `export default`。

Loader 的 `unwrapExports` 优先取 `exports.default ?? exports`。有默认导出时它拿到的是**裸函数**，而 `inject`、`name`、`Config` 这些同级命名导出被整体丢弃，插件在没注入任何服务的环境里运行。

这个坑有官方事故复盘（`docs/postmortem/0001`），当时有 178 个绿色测试和 100% 行覆盖率都没抓到，因为测试全是手动挂载的，没走真实 Loader。

**修法**：删掉 `export default`，只用命名导出。

## `parameters` 不是标准 JSON Schema

这一点容易想当然。它是**扁平的字段映射**：

```ts
// ✗ 不要这样（标准 JSON Schema 写法）
parameters: {
  type: 'object',
  properties: { who: { type: 'string' } },
}

// ✓ 要这样
parameters: {
  who: { type: 'string', description: '...' },
}
```

而 `output.schema` **是**标准 JSON Schema 结构（带 `type: 'object'` 和 `properties`）。两者形态不同，别搞混。

## 调试

**不启动服务，先看组装后的配置：**

```sh
dsh --profile web --dump-config | grep -A3 你的插件id
```

插件不在输出里 = overlay 没生效（查路径是不是绝对路径）。
在输出里但 `disabled: true` = 被禁用了（检查有没有在 `disabled` 上写 `!!js`，那是另一个官方复盘记录的坑）。

也可以直接扫：

```sh
npx dsh-doctor
```

## 从这里往下

- 参数与返回结构：直接读官方工具包的源码，比文档准。`@deepseek-ai/dsh-tool-todo` 是个结构完整的样本
- 依赖声明、可逆效应、生命周期：见 `dsh-plugin-dev` 技能
- 排障：见 `dsh-troubleshoot` 技能

## 不要做的事

- 不要写 `export default`
- 不要用相对路径
- 不要在 `parameters` 里写 `required: false`
- 不要把 `parameters` 写成标准 JSON Schema
- 不要在 `disabled` / `isolate` / `intercept` 上写 `!!js`
- 不要只用手动挂载的方式测试，要走真实的 `--patch` 路径
