# Hello DSH：从零到跑通第一个技能和插件

就像每门语言都从 Hello World 开始，DSH 从 Hello DSH 开始。

跑完这一课你会有三样东西：一个能用的技能、一个能用的插件、以及知道什么时候该用哪个。

**本文所有输出都是真实运行记录**（DSH `0.1.0-rc.6`，macOS，2026-08-13），包括那些报错。不是示意。

预计 20 分钟。

---

## 目录

- [第 0 步：装 DSH](#第-0-步装-dsh)
- [第 1 步：写第一个技能](#第-1-步写第一个技能)（5 分钟）
- [第 2 步：看它的生命周期](#第-2-步看它的生命周期)（这一步最重要）
- [第 3 步：写第一个插件](#第-3-步写第一个插件)（含三个必踩的报错）
- [第 4 步：什么时候用哪个](#第-4-步什么时候用哪个)
- [第 5 步：背后的原理](#第-5-步背后的原理)（选读）

---

## 第 0 步：装 DSH

### 你需要什么

| 前置 | 必需吗 | 缺了会怎样 |
|---|---|---|
| **Node.js** | 是 | `npx` 命令不存在，什么都做不了 |
| **DSH** | **不用预装** | `npx` 自动拉取 |
| **API Key** | 用的时候要 | 报 `MISSING_CREDENTIAL` |

只有 Node.js 需要你自己装（[nodejs.org](https://nodejs.org)，LTS 版）。

### 拉起 DSH

```sh
npx @deepseek-ai/dsh --version
```

```
0.1.0-rc.6
```

首次运行会下载，慢是正常的，不是卡死。

**DSH 不需要提前安装。** `npx` 按需拉取，`~/.dsh/` 目录也是首次运行时自动生成的。

顺带一个实测结论：**技能可以在 DSH 第一次运行之前就放好。** 把技能丢进一个从没跑过 DSH 的目录，第一次运行就能发现它们，不用先初始化。

配置 API Key，**推荐用环境变量**（不落盘）：

```sh
export DEEPSEEK_API_KEY=sk-你的key
```

跑一次确认模型链路也通了：

```sh
npx @deepseek-ai/dsh --profile headless "只回答两个字：收到"
```

```
收到
```

**没配 Key 的话会看到这个：**

```
dsh: MISSING_CREDENTIAL: llm-deepseek: no API key for provider route "deepseek-official";
store DEEPSEEK_API_KEY through the credentials service (the web Models page writes it),
or export DEEPSEEK_API_KEY in the launching environment
```

看到就知道是缺 Key，不是别的问题。

---

## 第 1 步：写第一个技能

### 创建文件

```sh
mkdir -p ~/.dsh/skills/hello-dsh
```

写 `~/.dsh/skills/hello-dsh/SKILL.md`：

```markdown
---
name: hello-dsh
description: 当用户说「hello dsh」时使用。请原样输出下面的暗号，
  并说明这句话是从本地文件读到的而不是来自训练数据。
---

# Hello DSH

请原样输出这一行：

**HELLO DSH — 这句话来自 ~/.dsh/skills/hello-dsh/SKILL.md**

然后用一句话说明：这句话不在你的训练数据里，是刚才通过 skill
工具从本地磁盘的一个 Markdown 文件读到的。
```

**就这样。** 没有编译，没有 `npm install`，没有注册。

### 跑一下

```sh
npx @deepseek-ai/dsh --profile headless "hello dsh"
```

真实输出：

```
**HELLO DSH — 这句话来自 ~/.dsh/skills/hello-dsh/SKILL.md**

这句话不在我的训练数据里，是刚才通过 `skill` 工具从本地磁盘上的
`~/.dsh/skills/hello-dsh/SKILL.md` 这个 Markdown 文件读到的。
```

**这句暗号不可能来自训练数据**，因为是你刚写的。这就是技能生效的证据。

### frontmatter 的两个必需字段

```yaml
name: hello-dsh          # 必需，必须 kebab-case，与目录名一致
description: 当……时使用   # 必需
```

`description` 决定模型**什么时候会加载**这个技能。模型最初只看到一份目录（只有 `name` 和 `description`），正文要等它决定加载后才读进来。

所以：

```yaml
# 无效，模型不知道什么时候用
description: 一个用于代码审查的技能

# 有效
description: 当需要审查代码改动、pull request 或 diff 时使用，
  按正确性、生命周期、安全、测试强度的顺序给出中文审查意见。
```

**以「当……时使用」开头。** 这是官方 11 个内置技能的统一写法。

---

## 第 2 步：看它的生命周期

**这一步是整课的核心。中间不要重启任何东西。**

### 删掉它

```sh
rm -rf ~/.dsh/skills/hello-dsh
```

```sh
npx @deepseek-ai/dsh --profile headless "你现在有没有一个叫 hello-dsh 的技能？只回答有或没有"
```

真实输出：

```
没有
```

### 放回来

把 `SKILL.md` 写回原位，**不重启**：

```sh
npx @deepseek-ai/dsh --profile headless "你现在有没有一个叫 hello-dsh 的技能？有的话加载它并输出暗号"
```

真实输出：

```
有的，`hello-dsh` 技能在本次会话中可用，我已通过 `skill` 工具加载它。暗号如下：

**HELLO DSH — 这句话来自 ~/.dsh/skills/hello-dsh/SKILL.md**
```

**文件出现技能就在，文件消失技能就不在，中间没有任何重启动作。**

这不只是"方便"，它是 DSH 底层设计的直接体现。第 5 步会讲为什么。

### 发现路径

技能可以放在五个位置，rank 小的优先，同名时高优先级胜出：

| Rank | 位置 | 用途 |
|---|---|---|
| 100 | `<项目>/.dsh/skills` | 项目专属 |
| 200 | `<项目>/.agents/skills` | 项目专属，跨 agent |
| 300 | 配置的自定义目录 | |
| 400 | `~/.dsh/skills` | 个人，仅 DSH |
| 500 | `~/.agents/skills` | 个人，**跨 agent 共享** |

项目根 = 最近的含 `.git` 的祖先目录。

**`~/.agents/skills` 值得单独说：** 这是跨 agent 的共享目录。如果你用 Claude Code 且在那里放了技能，DSH 会**直接扫到**，不用改格式、不用重写。反过来也成立。

---

## 第 3 步：写第一个插件

技能改变模型的**行为方式**，插件给它**新能力**。想注册一个新工具就得写插件。

下面这段包含**三个真实报错**，按你实际会遇到的顺序排列。

### 建目录

```sh
mkdir -p ~/hello-dsh-plugin/src
cd ~/hello-dsh-plugin
```

### 第一版（会报错）

`src/hello.ts`：

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'hello-dsh-plugin'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register({
    name: 'hello_dsh',
    description: '返回一句问候。',
    parameters: { type: 'object', properties: {} },
  }, async () => ({ content: [{ type: 'text', text: 'hi' }] }))
}
```

写 overlay（**路径必须是绝对路径**）：

```sh
cat > cordis.yml <<YAML
- insert:
    - id: hello-dsh
      name: '$(pwd)/src/hello.ts'
YAML
```

跑：

```sh
npx @deepseek-ai/dsh --profile headless --patch ./cordis.yml "调用 hello_dsh"
```

**报错一：**

```
TypeError: tool "hello_dsh" must declare output { schema, render, presentationMeta? }
```

**原因**：工具注册必须声明 `output`，里面要有 `schema`（返回值结构）和 `render`（怎么渲染）。而且要用 `defineTool()` 包裹。

### 第二版（还会报错）

```ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'hello-dsh-plugin'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'hello_dsh',
    description: '返回一句问候。',
    parameters: {
      who: { type: 'string', required: false },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: { greeting: { type: 'string', required: true } },
      },
      render: (_args, value) => [{ type: 'text', text: value.greeting }],
    },
    execute(args) {
      return Promise.resolve({ greeting: `HELLO DSH, ${args.who ?? 'world'}` })
    },
  }))
}
```

**报错二：**

```
code: 'UNSUPPORTED_SCHEMA',
violations: [ 'parameters.who.required must be true when present' ]
```

**原因**：`required` **只能填 `true`**。表示可选参数要直接把这个字段省略掉。

### 第三版（跑通）

把 `required: false` 删掉：

```ts
parameters: {
  who: { type: 'string' },        // 可选：省略 required
  // what: { type: 'string', required: true },   // 必填才写 required
},
```

```sh
npx @deepseek-ai/dsh --profile headless --patch ./cordis.yml \
  "调用 hello_dsh 工具，who 填 pingfan，原样告诉我返回值"
```

真实输出：

```
工具返回值为：

HELLO DSH, pingfan
```

**成了。**

### 报错三：`export default`

这个报错你上面没遇到，但迟早会踩，而且它是**官方自己踩过并写了事故复盘**的。

如果你的模块里有：

```ts
export const name = 'my-plugin'
export const inject = ['tools']
export function apply(ctx) { }
export default apply          // ← 这一行
```

会得到：

```
cannot get property "tools" without inject
```

**原因**：Loader 的 `unwrapExports` 逻辑是 `exports.default ?? exports`，优先取默认导出。有 `export default` 时它拿到的是**裸的 apply 函数**，而 `inject`、`name`、`Config` 这些同级命名导出被整体丢弃，插件在没注入任何服务的环境里运行。

**崩在加载时，不是请求处理时。**

这个坑当时有 **178 个绿色测试和 100% 行覆盖率**都没抓到，因为所有测试都是手动挂载插件的，绕过了真实 Loader 路径。见官方 `docs/postmortem/0001`。

**修法**：删掉 `export default`，只用命名导出。

### 两个 schema 形态不一样

这点容易想当然：

```ts
// parameters 是扁平字段映射
parameters: {
  who: { type: 'string' },
}

// output.schema 是标准 JSON Schema
output: {
  schema: {
    type: 'object',
    additionalProperties: false,
    properties: { greeting: { type: 'string', required: true } },
  },
}
```

别搞混。

### 插件调试

**先看组装后的配置，不启动服务：**

```sh
npx @deepseek-ai/dsh --profile web --dump-config | grep -A3 你的插件id
```

- 插件不在输出里 → overlay 没生效，查是不是绝对路径
- 在输出里但 `disabled: true` → 被禁用了

顺带一个坑：**不要在 `disabled` / `isolate` / `intercept` 上写 `!!js` 表达式。** Cordis 只在插件的 `config` 内部求值表达式，元数据字段直接读原始值，而表达式对象恒为 truthy，结果是插件**永久禁用且无任何诊断**。这也是官方复盘记录过的（`docs/postmortem/0002`）。

一条命令扫出这类问题：

```sh
npx dsh-doctor
```

---

## 第 4 步：什么时候用哪个

| 你要做的事 | 用 | 成本 |
|---|---|---|
| 改变判断标准、输出格式、工作流程 | **技能** | 一个 .md 文件，5 分钟 |
| 注册新工具、接外部服务、挂生命周期钩子 | **插件** | TypeScript + 踩上面那些坑 |

**判断依据：用自然语言能说清楚的，就是技能。**

具体例子：

| 需求 | 选 |
|---|---|
| 让代码审查按固定结构输出中文意见 | 技能 |
| 让它查天气 | 插件（要调 API） |
| 让它写提交信息时遵守 Conventional Commits | 技能 |
| 让它能操作你的数据库 | 插件 |
| 让它排查 bug 时先复现再定位 | 技能 |
| 在 Web UI 里加一个面板 | 插件 |

**还有一个中间选项**：技能可以捆绑 `scripts/`、`references/`、`assets/`，按需加载。所以"需要跑一个脚本"不一定要做成插件。

---

## 第 5 步：背后的原理

到这里你已经会用了。下面是选读。

DSH 建立在 **Cordis** 之上，Cordis 有一篇论文《A Programming Paradigm for Spatiotemporal Composability》（Yifan Shi、Wei Zhang、Tianyi Cui，Peking University / DeepSeek-AI）。

**第 2 步那个演示，正是论文形式化内容的最小可观察实例。**

### 时间可组合性

> 组件被移除时，它对共享环境的修改必须被完整、安全、有序地撤销。

论文的做法：每一次作用都携带它的**逆操作**，运行时追踪，卸载时按 LIFO 顺序执行（§3.1，可逆效应）。

对照一下 VSCode。论文 §1.2.1 给了一组实证数据：安装量前 100 的扩展里有 **87 个**含可执行代码，因此禁用或卸载它们**必须重启整个扩展宿主**；而声明了 `extensionDependencies` 的只有 **7 个**。

你在第 2 步删掉技能时，没有重启任何东西。

### 空间可组合性

> 组件声明它依赖什么，运行时在依赖出现、消失、或换成另一个提供者时，重新判断它能不能运行。

论文称之为**反应式 coeffect**（§3.2）：依赖满足则激活，不满足则停用，无关变化则不动。

在技能这条链路上：`skill-filesystem` 提供 `skills` 能力，`tool-skill` 声明它需要 `skills`。前者不在，后者就不激活。

**关键是它静默不激活，不报错。** 这是排查"插件装了但没反应"的第一个怀疑方向。

### 只有两个状态

论文 §4.1 图 1：

```
        L-Reload
Inactive  ⇄  Active
        L-Unload
```

驱动转换的是一次比较：**当前生效的视图（committed view）和目标视图（target view）是否一致**。不一致就发起转换。

第 2 步那三步，就是这个比较在文件系统层面的表现——文件在不在，决定目标视图是什么。

### fiber

论文把一个组件的**实例**叫 fiber（§4.1，Definition 44）。一个 fiber 记录：来自哪个组件、父 fiber 是谁、自己提供了什么、当前在生命周期的哪一步。

同一个组件可以被实例化多次，每个 fiber 有独立的生命周期状态。

### 有一条实现上的重要提醒

论文 §5.1.1 说得很直接：**逆操作的正确性是组件作者的义务，运行时不验证**（*"an obligation on the component author rather than a property the runtime verifies"*）。

也就是说，你在插件里 `setInterval` 忘了配 `clearInterval`，Cordis 不会告诉你，只会在插件卸载后留下一个还在跑的定时器。热重载时这类泄漏会累积。

正确写法是把作用和逆操作写在一起：

```ts
ctx.effect(() => {
  const timer = setInterval(tick, 1000)
  return () => clearInterval(timer)     // 逆操作紧挨着创建
})
```

---

## 遇到问题

**技能装了但看不到？** 按顺序查：

1. `name` 是不是 kebab-case（必须是，且与目录名一致）
2. 有没有把 `user-invocable` 写成 `userInvocable`——**驼峰会导致整个技能被丢弃**，只留一条警告不报错
3. 有没有嵌套目录（只扫一层）

**插件加载了但没反应？**

1. `--dump-config` 看它在不在、是不是被 `disabled`
2. 有没有 `export default`
3. `inject` 声明的服务有没有提供方（没有就静默不激活）

**一条命令扫出上面大部分问题：**

```sh
npx dsh-doctor
```

它查的都是官方文档或事故复盘里记录过的真实故障，每条结果都带出处链接。

---

## 接下来

装上完整技能集：

```sh
git clone https://github.com/pingfanfan/dsh-skills.git
cd dsh-skills && ./install.sh
```

或者直接把 [INSTALL-FOR-AGENTS.md](../INSTALL-FOR-AGENTS.md) 丢给你的 agent（Codex、Claude Code、DSH 自己都行），说「照这个装」。

装完之后对 DSH 说 **「hello dsh」**，它会带你走一遍，可以一层层往下问。

| 想深入 | 看 |
|---|---|
| 写技能的完整规则 | [`dsh-skill-dev`](../skills/dsh-skill-dev/SKILL.md) |
| 写插件的完整规则 | [`dsh-plugin-dev`](../skills/dsh-plugin-dev/SKILL.md) |
| 排障 | [`dsh-troubleshoot`](../skills/dsh-troubleshoot/SKILL.md) |
| 技能编写指南 | [writing-skills.md](writing-skills.md) |

---

## 附：论文引用

**[A Programming Paradigm for Spatiotemporal Composability](https://github.com/cordiverse/paper)**

| 章节 | 内容 |
|---|---|
| §1.2.1 | VSCode 扩展的实证数据（87/100 卸载需重启，仅 7 个声明依赖） |
| §3.1 | 可逆效应 |
| §3.2 | 反应式 coeffect |
| §4.1 Definition 43/44、图 1 | 组件、fiber、两状态生命周期 |
| §5.1.1 | `ctx.effect` 实现；逆操作正确性是作者义务 |
| §6.6 | 依赖版本与 key 冲突（论文明确列为开放问题） |
