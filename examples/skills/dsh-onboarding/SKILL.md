---
name: dsh-onboarding
description: 当用户第一次使用 DeepSeek Harness（DSH），或在启动、工作区、权限、技能发现环节卡住时使用——解释 DSH 的进程模型、目录约定和权限边界，并给出可自查的排错路径。
---

# 带一个人跑通 DeepSeek Harness

这是引导，不是照抄清单。先判断对方卡在哪一层，再给对应的动作；不要把七个步骤一次性倒给一个只是端口被占用的人。

DSH 处于 developer preview，官方明确警告会有破坏兼容性的变更。任何"应该可以"的说法都要用实际命令验证一次。

## 事实来源

- 官方 README 与 `docs/user/guide/` —— 启动方式与 Web UI 指南
- `docs/user/develop/basic/` —— 插件编写与 `cordis.yml` 加载
- `packages/skill/skill-filesystem/README.md` —— 技能发现路径与 frontmatter 规则
- `dsh --help` / `dsh --profile web --dump-config` —— 当前版本的权威命令面

不要凭记忆回答版本相关的问题。`dsh --version` 和 `--dump-config` 的输出才算数。

## 先分清四个东西

新手最常见的混乱是把这四层当成一个东西。回答任何问题前先定位在哪一层：

| 层 | 是什么 | 出问题的表现 |
|---|---|---|
| **模型** | DeepSeek 的 API，在云端 | 401、余额不足、限流 |
| **Harness（DSH）** | 本机跑的 agent 运行时 | 端口占用、Node 版本、插件加载失败 |
| **Profile** | 一组插件的组合（`web` / `headless`） | 某个工具不存在、配置没生效 |
| **工作区** | agent 实际读写的目录 | 找不到文件、权限被拒 |

"它没反应"这类描述必须先追问是哪一层，否则会浪费两轮。

## 启动

最短路径，不需要克隆仓库：

```sh
npx @deepseek-ai/dsh web
```

默认服务在 `http://127.0.0.1:3080`。首次运行会在 `~/.dsh/` 下生成 `profiles/`、`skills/`、`storages/`。

从源码跑（需要改 DSH 本身时才用）：

```sh
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness && pnpm install && pnpm run build && pnpm dsh web
```

不启动服务、只看组装后的配置：

```sh
dsh --profile web --dump-config
```

这条命令在排查"某个插件到底加载了没有"时比读文档快得多。

## 常见启动失败

按出现频率排序，每条都给可执行的下一步：

- **端口被占用** —— `EADDRINUSE: 127.0.0.1:3080`。先 `lsof -nP -iTCP:3080 -sTCP:LISTEN` 看是谁占的；常见是自己之前起的实例没退干净。
- **Node 版本** —— DSH 要求较新的 Node。`node -v` 确认后再排查其他方向。
- **路径含空格或中文** —— 插件路径必须是绝对路径，含空格时务必加引号。
- **首次 npx 下载慢** —— 不是卡死。观察是否有网络代理需要配置。
- **API Key 未配置** —— 启动本身不需要 Key，但任何模型任务都需要。启动成功不等于能对话。

## 权限：看懂它要什么

DSH 会请求读文件、执行命令、写文件。批准前至少确认三件事：

1. **要执行的确切命令**，包括参数——不是"运行测试"这种概括
2. **工作目录**——是不是你以为的那个目录
3. **写入范围**——会碰哪些文件

拒绝一次不会破坏会话。第一次使用时，主动拒绝一个越界请求是有价值的练习：你会看到被拒后的表现，也会知道边界在哪。

**不要在真实项目上做第一次尝试。** 新建一个空目录作为工作区，代价为零。

## 技能（skill）：DSH 的能力扩展

技能是纯 Markdown，不需要写代码、不需要构建、不需要发包：

```
~/.dsh/skills/<name>/SKILL.md
```

```yaml
---
name: my-skill          # 必需，kebab-case
description: ...        # 必需，决定模型何时会用它
---
```

发现路径按优先级（rank 小的优先）：

| Rank | 位置 |
|---|---|
| 100 | `<项目>/.dsh/skills` |
| 200 | `<项目>/.agents/skills` |
| 400 | `~/.dsh/skills` |
| 500 | `~/.agents/skills` |

项目级优先于用户级，所以同名技能可以在单个项目里被覆盖。

两个容易踩的点：

- **改完不用重启。** 新增或删除技能目录后几秒内自动生效。
- **frontmatter 写错会整条丢弃。** 键名必须是 kebab-case——写成 `userInvocable` 而不是 `user-invocable`，这个技能会被静默跳过，只留一条警告。技能"不见了"时先查这里。

`~/.agents/skills` 是跨 agent 的共享目录，Claude Code 等工具的技能放在这里时 DSH 也能直接发现。

## 判断是不是真的成功了

模型说"已完成"不是验收标准。让对方确认：

- 文件确实被改了（看 diff，不是看回复）
- 命令确实跑过（看退出码和输出）
- 结果符合预期（跑测试，不是读描述）

这个习惯要在第一次使用时就建立，之后很难补。

## 什么时候该去提问

官方 Issues 是关闭的，反馈走 GitHub Discussions。提问前准备好：

- `dsh --version` 输出
- 操作系统与 Node 版本
- 最小复现步骤
- 完整报错（脱敏掉 Key 和主目录路径）

带这些信息的问题会被认真对待；"用不了"不会。
