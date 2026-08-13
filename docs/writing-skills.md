# 怎么给 DSH 写一个技能

技能是 DSH 里成本最低的扩展方式：一个 Markdown 文件，不用写代码，不用构建，不用发包。

本文的规则来自 DSH 官方文档、`packages/skill/skill-filesystem/README.md`，以及在 `0.1.0-rc.6` 上的实测。

## 最小例子

```
~/.dsh/skills/my-skill/SKILL.md
```

```markdown
---
name: my-skill
description: 当需要做某件具体的事时使用——一句话说清适用场景。
---

# 标题

（正文是直接交给模型的指令）
```

存盘。几秒内生效，**不用重启 DSH**。

## 两种放法

```
<name>/SKILL.md     ← 目录形式，可以带附加资源
<name>.md           ← 单文件形式
```

嵌套的 `**/SKILL.md` **不会**被发现，只扫一层。

## 发现路径

按 rank 排序，数字小的优先。同名技能，优先级高的胜出：

| Rank | 来源 | 路径 |
|---|---|---|
| 100 | `project-dsh` | `<项目>/.dsh/skills` |
| 200 | `project-agents` | `<项目>/.agents/skills` |
| 300 | `custom` | 配置的自定义目录 |
| 400 | `user-dsh` | `~/.dsh/skills` |
| 500 | `user-agents` | `~/.agents/skills` |

项目根 = 最近的含 `.git` 的祖先目录；没有则用当前工作目录。

**`~/.agents/skills` 是跨 agent 的共享目录。** Claude Code 等工具的技能放在这里，DSH 也能直接发现——技能资产在不同 agent 之间是通用的。

## frontmatter

必需：

| 字段 | 说明 |
|---|---|
| `name` | **必须 kebab-case**，且要和目录名一致 |
| `description` | 决定模型什么时候加载它 |

可选：

| 字段 | 说明 |
|---|---|
| `whenToUse` | 补充的使用时机提示 |
| `metadata` | 自定义元数据 |
| `disable-model-invocation` | `true` 则模型看不到它 |
| `user-invocable` | `false` 则用户命令里看不到它 |

### 最容易踩的坑：fail-closed

**键名写成驼峰，整个技能会被丢弃。**

```yaml
user-invocable: true     # ✓ 正确
userInvocable: true      # ✗ 整条技能被静默跳过，只留一条警告
```

布尔值也一样：非布尔的值会导致整条被丢弃，而不是"忽略这个字段"。

这是官方有意为之的 fail-closed 设计——把技能暴露在本该禁用的界面上，比丢弃它更危险。

**技能"不见了"的时候，第一个怀疑对象就是这里。**

可接受的布尔写法：`true`/`false`、`yes`/`no`、`on`/`off`、`1`/`0`，大小写不敏感。

## description 比正文更重要

模型先看到的是一份目录，只含每个技能的 `name` 和 `description`。**正文只有在模型决定加载之后才会被读到。**

所以 `description` 的唯一任务是：让模型在正确的时机想起这个技能。

```yaml
# ✗ 说了等于没说
description: 一个用于代码审查的技能

# ✓ 说清了触发条件
description: 当需要审查代码改动、pull request 或 diff 时使用——按正确性、
  生命周期、安全、测试强度的顺序给出中文审查意见。
```

写法上：**以"当……时使用"开头**，然后说清它会做什么。这也是官方 11 个技能的统一写法。

## 正文怎么写

看官方自己怎么写的：[`.agents/skills/`](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills)。11 个技能，其中 `dsh-code-review` 有 8KB，是最值得读的样本。

从中能总结出几条：

**1. 明确事实来源。** 官方技能开头常有一节列出权威文档的位置，并说明"读它，不要复述它"。

**2. 定位成判断指引，不是清单。** `dsh-code-review` 第一句就是 *"This skill is guidance, not a complete checklist."* 因为清单会让模型机械执行，而判断标准让它思考。

**3. 分层。** 官方的写法是：阻断项（blocking requirements）→ 人工检查项（manual checks）→ 不要做的事。优先级明确。

**4. 给对照。** 正例反例并排，比抽象描述有效得多。

**5. 说不要做什么。** 这一节经常比"要做什么"更有价值——它挡住了模型最容易犯的错。

## 附加资源

目录形式的技能可以带 `scripts/`、`references/`、`assets/`。它们**按需加载**：只有正文里明确引用的路径才会被解析，模型不会拿到整个目录列表。

这意味着技能不必只是提示词——可以把真正的脚本捆绑进去。

注意：这些子目录的变化**不会**触发技能目录重新发现。只有 `SKILL.md` 本身的增删改会。

## 热加载的边界

会触发重新发现：

- 新增、删除技能目录
- 新增、删除、修改 `SKILL.md`（为了重读 frontmatter）
- 扁平 `.md` 技能的增删

不会触发：

- `references`、`scripts`、`assets` 下的改动

另外：**正文的改动不需要任何缓存失效**。每次 `skill(name)` 调用都会重新读取当前文件，所以改正文即时生效。

## 自测

写完之后至少确认三件事：

1. **它出现在列表里** —— 没出现就是 frontmatter 有问题，查 kebab-case
2. **`description` 能触发它** —— 用一个真实场景描述问一句，看模型会不会加载它
3. **正文真的改变了行为** —— 对比加载前后的输出差异，没差异说明写的是废话

第三条最容易被跳过，也最重要。

## 参考

- [DSH 官方仓库](https://github.com/deepseek-ai/deepseek-harness)
- [`.agents/skills/`](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills) —— 官方自用的 11 个技能
- `packages/skill/skill-filesystem/README.md` —— 发现与解析的权威说明
- `packages/skill/tool-skill/README.md` —— 目录与加载机制
