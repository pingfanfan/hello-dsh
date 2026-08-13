# dsh-skills

[English](README.md) | 中文

给 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（DSH）用的中文技能集。

技能是纯 Markdown——不用写代码，不用构建，不用发包。放进目录就自动生效，改完不用重启。

## 安装

```sh
git clone https://github.com/pingfanfan/dsh-skills.git
cd dsh-skills
./install.sh
```

安装到 `~/.dsh/skills/`。DSH 会自动发现，**无需重启**。

先看会发生什么：

```sh
./install.sh --dry-run
```

装到跨 agent 的共享目录（Claude Code 等工具也能用）：

```sh
./install.sh --agents-dir      # → ~/.agents/skills/
```

移除：

```sh
./install.sh --uninstall
```

也可以直接把 `skills/` 下的任意目录拷进 `~/.dsh/skills/`，脚本只是省事，不是必需的。

## 第一课：Hello Skill

装完之后，直接对 DSH 说：

```
hello skill
```

它会输出一句只可能来自本地文件的暗号，然后可以一层一层往下讲：这个文件是什么、生命周期怎么走、背后的 Cordis 理论是什么。

完整教程：[docs/hello-skill.md](docs/hello-skill.md)，里面有真实运行记录，包括「删掉技能 → 放回来」全程不重启的生命周期演示。

## 技能清单

| 技能 | 什么时候用 |
|---|---|
| `hello-skill` | **第一课**：验证技能系统，分层讲解生命周期与原理 |
| `dsh-onboarding` | 第一次跑 DSH，或卡在启动、工作区、权限、技能发现 |
| `dsh-skill-dev` | 给 DSH 写技能，或技能没被发现 |
| `dsh-first-plugin` | 从零做出并装上第一个插件（实测流程 + 三个报错） |
| `dsh-plugin-dev` | 给 DSH 写插件，或插件没加载没注入 |
| `dsh-troubleshoot` | DSH 起不来、配置没生效、UNKNOWN_TOOL、技能不见了 |
| `plan-before-code` | 任务要改多处、有不确定性、超过半天 |
| `code-review-cn` | 审查代码改动、PR、diff |
| `debug-systematically` | 遇到 bug、测试失败、本来是好的现在坏了 |
| `explain-codebase` | 快速理解陌生项目 |
| `refactor-safely` | 重构、拆函数、消除重复 |
| `test-first` | 写测试、实现功能、修缺陷 |
| `api-design` | 设计接口、加公开方法、定数据结构 |
| `error-handling` | 设计错误处理、决定该抛还是该返回 |
| `perf-optimize` | 优化性能、排查慢的原因 |
| `security-review-cn` | 安全审查、评估攻击面、检查凭据处理 |
| `commit-message` | 写提交信息、拆分改动 |
| `pr-description` | 写 PR 描述、准备评审 |
| `write-tech-cn` | 写中文文档、README、技术博客 |
| `write-docs-cn` | 写或整理项目文档、API 说明、教程 |
| `web-research` | 联网查资料、核实事实、技术选型 |
| `ask-good-questions` | 提技术问题、报 bug、写 issue |

技能持续增加中。

## 设计原则

**按官方范式写。** DSH 仓库里有 [`.agents/skills/`](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills)，DeepSeek 官方自己在用的 11 个技能。本仓库的写法参照它们：明确事实来源、给判断依据而非清单、宁可少而准。

**中文优先。** 官方内置技能是英文的。

**说人话。** 技能是给模型的指令，不是文档。写"先做什么、不要做什么、怎么判断做对了"，不写背景介绍。

## 关于安装脚本

`install.sh` 是这个仓库里唯一的代码，有意写得很保守：

- 只写入 `~/.dsh/skills` 或 `~/.agents/skills`，不碰其他任何路径
- 安装前打印将写入的确切路径并要求确认
- 卸载按本仓库的技能清单**逐个比对删除**，不使用通配符——你自己的技能不会被误删
- 不修改 shell 配置、git 配置或任何全局设置
- 脚本坏了也不影响技能可用，手动拷贝目录即可

## 自己写一个技能

```
~/.dsh/skills/<name>/SKILL.md
```

```markdown
---
name: my-skill          # 必需，kebab-case
description: ...        # 必需，决定模型什么时候会用它
---

（正文是给模型的指令）
```

发现路径按优先级（rank 小的优先）：

| Rank | 位置 |
|---|---|
| 100 | `<项目>/.dsh/skills` |
| 200 | `<项目>/.agents/skills` |
| 400 | `~/.dsh/skills` |
| 500 | `~/.agents/skills` |

两个坑：

- **frontmatter 的键必须是 kebab-case。** 写成 `userInvocable` 而不是 `user-invocable`，整个技能会被**静默丢弃**，只留一条警告。技能"不见了"先查这里。
- **`description` 比正文更重要。** 模型靠它决定要不要加载这个技能。写清楚"什么时候用"。

详见 [docs/writing-skills.md](docs/writing-skills.md)。

## 欢迎投稿

有好用的技能就提 PR。要求只有两条：中文、并且你真的在用它。

## 许可

MIT

---

非官方社区项目，与 DeepSeek 无隶属关系。
