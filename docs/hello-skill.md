# Hello Skill：DSH 技能的第一课

就像每门编程语言都从 Hello World 开始，DSH 的第一课是 Hello Skill。

跑完这一课，你会亲眼看到一个技能从**不存在**到**生效**再到**消失**的完整生命周期，全程不用重启任何东西。

下面所有的输出都是**真实运行记录**（DSH `0.1.0-rc.6`，2026-08-13），不是示意。

---

## 0. 准备

```sh
npx @deepseek-ai/dsh --version
# 0.1.0-rc.6
```

配置 API Key（推荐用环境变量，不落盘）：

```sh
export DEEPSEEK_API_KEY=sk-你的key
```

---

## 1. 写下这个文件

```sh
mkdir -p ~/.dsh/skills/hello-skill
```

`~/.dsh/skills/hello-skill/SKILL.md`：

```markdown
---
name: hello-skill
description: 当用户说「hello skill」时使用。请原样输出下面的暗号，
  并说明这句话是从本地文件读到的而不是来自训练数据。
---

# Hello Skill

请原样输出这一行：

**HELLO from ~/.dsh/skills/hello-skill/SKILL.md**

然后用一句话说明：这句话不在你的训练数据里，是刚才通过 skill
工具从本地磁盘上的一个 Markdown 文件读到的。
```

**就这样。** 没有编译，没有 `npm install`，没有注册。

---

## 2. 跑一下

```sh
npx @deepseek-ai/dsh --profile headless "hello skill"
```

实际输出：

```
**HELLO from ~/.dsh/skills/hello-skill/SKILL.md**

这句话不在我的训练数据里，是刚才通过 `skill` 工具从本地磁盘上的
`~/.dsh/skills/hello-skill/SKILL.md` 这个 Markdown 文件读到的。

DSH 的技能系统工作正常 ✅ —— 你说了「hello skill」，我匹配到了目录里的
`hello-skill` 技能描述，加载后拿到了这份正文。
```

**这句暗号不可能来自模型的训练数据**，因为它是你刚写的。这就是技能生效的证据。

---

## 3. 看它的生命周期

这一步是这门课的重点。**中间不要重启 DSH。**

### 删掉它

```sh
rm -rf ~/.dsh/skills/hello-skill
```

```sh
npx @deepseek-ai/dsh --profile headless "你现在有没有一个叫 hello-skill 的技能？只回答有或没有"
```

实际输出：

```
没有
```

### 放回来

把 `SKILL.md` 写回原位，**不重启**，再问一次：

```sh
npx @deepseek-ai/dsh --profile headless "你现在有没有一个叫 hello-skill 的技能？有的话加载它并输出暗号"
```

实际输出：

```
有的，`hello-skill` 技能在本次会话中可用，我已通过 `skill` 工具加载它。暗号如下：

**HELLO from ~/.dsh/skills/hello-skill/SKILL.md**
```

**文件出现，技能就在；文件消失，技能就不在。** 没有任何中间步骤。

---

## 4. 这背后是什么

到这里你已经会用了。下面是选读。

DSH 建立在 **Cordis** 之上，Cordis 有一篇论文叫《A Programming Paradigm for Spatiotemporal Composability》（Yifan Shi、Wei Zhang、Tianyi Cui，PKU / DeepSeek-AI）。你刚才跑的那三步，正是论文形式化的东西的最小可观察实例。

论文把动态组合拆成两个互相独立的维度：

### 时间可组合性

> 组件被移除时，它对共享环境的修改必须被**完整、安全、有序地撤销**。

论文的做法是：让每一次作用都携带它的**逆操作**，运行时追踪这些逆操作，卸载时按 LIFO 顺序执行（§3.1，可逆效应）。

对比一下 VSCode：论文 §1.2.1 给了一组实证数据，安装量前 100 的扩展里有 **87 个**含可执行代码，因此禁用或卸载它们**必须重启整个扩展宿主**。

你刚才删掉 `hello-skill` 时没有重启任何东西。

### 空间可组合性

> 组件声明它依赖什么，运行时在依赖出现、消失、或换成另一个提供者时，重新判断它能不能运行。

论文称之为**反应式 coeffect**（§3.2）：依赖满足则激活，不满足则停用，无关变化则不动。

在技能这条链路上：`skill-filesystem` 提供 `skills` 能力，`tool-skill` 声明它需要 `skills`。前者不在，后者就不激活——而且是**静默不激活，不报错**。这也是排查技能问题时的重要线索。

### 只有两个状态

论文 §4.1 的图 1，组件生命周期就这么简单：

```
        L-Reload
Inactive  ⇄  Active
        L-Unload
```

驱动转换的是一次比较：**当前生效的视图（committed view）和目标视图（target view）是否一致**。不一致就发起转换。

你上面那三步，就是这个比较在文件系统层面的表现：文件在不在，决定目标视图是什么。

### fiber

论文把一个组件的**实例**叫做 fiber（§4.1，Definition 44）。一个 fiber 记录了：

- 它来自哪个组件（依赖声明 `d`、提供什么 `p`、作用函数 `e`）
- 父 fiber 是谁
- 自己实际提供了哪些能力
- 当前处于生命周期的哪个状态

同一个组件可以被实例化多次，每个 fiber 有自己独立的生命周期状态。DSH 实现里，`fiber.committed` 就是上面说的"当前生效的视图"。

---

## 5. 知道这些有什么用

**不读论文也能用技能。** 但知道这套机制之后，两件事变得可预期：

**一、为什么改完不用重启。** 因为技能的加载不是"启动时读一次配置"，而是每一步之前都重新比较一次目标视图。

**二、为什么技能"明明在那儿却不生效"。** 只有两种可能：

- **依赖没满足** → 组件静默停在 Inactive，不报错
- **frontmatter 被 fail-closed 丢弃** → 键名写成驼峰（`userInvocable` 而不是 `user-invocable`），整条技能被丢弃，只留一条警告

第二种可以直接扫出来：

```sh
npx dsh-doctor
```

---

## 6. 下一步

| 想做什么 | 看哪里 |
|---|---|
| 自己写一个技能 | [`dsh-skill-dev`](../skills/dsh-skill-dev/SKILL.md) |
| 技能不出现，排查 | [`dsh-troubleshoot`](../skills/dsh-troubleshoot/SKILL.md) |
| 写详细的技能编写指南 | [writing-skills.md](writing-skills.md) |
| 做插件（技能做不到的事） | [`dsh-first-plugin`](../skills/dsh-first-plugin/SKILL.md) |

装上这套技能集之后，直接对 DSH 说 **「hello skill」**，它会带你走一遍，并且可以一层一层往下问。

```sh
git clone https://github.com/pingfanfan/dsh-skills.git
cd dsh-skills && ./install.sh
```

---

## 附：论文引用

- **论文**：[A Programming Paradigm for Spatiotemporal Composability](https://github.com/cordiverse/paper)
- §1.2.1 —— VSCode 扩展的实证数据（87/100 需要重启）
- §3.1 —— 可逆效应
- §3.2 —— 反应式 coeffect
- §4.1 Definition 43/44、图 1 —— 组件、fiber、两状态生命周期
- §5.1.1 —— `ctx.effect` 实现，以及"逆操作的正确性是组件作者的义务，运行时不验证"
