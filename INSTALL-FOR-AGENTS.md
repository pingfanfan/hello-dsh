# 给 AI Agent 的安装指令

> 这份文件是写给 AI agent 读的（Codex、Claude Code、DSH 自己、任何能读写文件并执行命令的 agent）。
>
> **人类用户**：把本文件的链接丢给你的 agent，说「照这个装」即可。你不需要懂下面的内容。

## 任务

让用户能用上 `pingfanfan/hello-dsh` 这套 DeepSeek Harness（DSH）中文技能。

**先检查前置条件，再安装。** 用户很可能什么都没装过。

---

## 第一步：检查前置条件

按顺序检查这三项，**不要跳过**。

### 1. Node.js（硬前置，缺了做不下去）

```sh
node --version
```

没有 Node 就**停下来告诉用户去装**，不要自作主张用包管理器装（可能污染他的环境）：

> DSH 需要 Node.js。请先从 https://nodejs.org 安装（建议 LTS 版本），装完告诉我，我继续。

macOS 用户如果有 Homebrew，可以建议 `brew install node`，但**要先问过再执行**。

### 2. DSH 本身（不用预装）

```sh
npx @deepseek-ai/dsh --version
```

**这一步会自动下载 DSH，首次会比较慢（几十秒到几分钟），不是卡死。**

如果输出了版本号（例如 `0.1.0-rc.6`），说明没问题。

> 注意：DSH **不需要提前安装**。`npx` 会按需拉取，`~/.dsh/` 目录也是首次运行时自动生成的。所以技能可以在 DSH 第一次运行之前就放好——实测确认过，把技能放进一个从没跑过 DSH 的目录，第一次运行就能发现它们。

### 3. API Key（不影响安装，但影响使用）

```sh
echo ${DEEPSEEK_API_KEY:+已设置}
```

没设置的话，安装照常进行，但**要在最后告诉用户**：

> 技能已装好，但 DSH 还需要 API Key 才能用。去 https://platform.deepseek.com 拿一个，然后：
> ```sh
> export DEEPSEEK_API_KEY=sk-你的key
> ```
> 想永久生效就写进 `~/.zshrc` 或 `~/.bashrc`。

缺 Key 时的报错长这样，看到就是这个原因：

```
dsh: MISSING_CREDENTIAL: llm-deepseek: no API key for provider route "deepseek-official"
```

**不要替用户设置 Key，也不要把 Key 写进任何文件或提交到任何地方。**

---

## 第二步：安装技能

技能是**纯 Markdown 文件**。安装 = 把目录拷到约定位置。**不需要编译、不需要 npm install、不需要构建。**

目标位置二选一：

| 位置 | 用于 |
|---|---|
| `~/.dsh/skills/` | 只给 DSH 用（**默认选这个**） |
| `~/.agents/skills/` | 跨 agent 共享，Claude Code 等也能读到 |

### 取得文件

优先用 git（保留后续更新能力）：

```sh
git clone --depth 1 https://github.com/pingfanfan/hello-dsh.git /tmp/hello-dsh
```

没有 git 时用打包下载：

```sh
curl -fsSL https://github.com/pingfanfan/hello-dsh/archive/refs/heads/main.tar.gz | tar xz -C /tmp
# 解出 /tmp/hello-dsh-main
```

### 拷贝

```sh
mkdir -p ~/.dsh/skills
cp -R /tmp/hello-dsh/examples/skills/* ~/.dsh/skills/
```

`~/.dsh/skills/` 不存在时直接创建即可，**不用先跑 DSH**。

---

## 第三步：验证

```sh
ls ~/.dsh/skills/
```

应该看到 20 多个目录，每个里面有一个 `SKILL.md`。

如果用户有 API Key，直接做端到端验证：

```sh
npx @deepseek-ai/dsh --profile headless "hello dsh"
```

成功的话会输出一句以 `HELLO DSH` 开头的暗号，并列出四层入门菜单。

---

## 第四步：告诉用户

说清楚这几件事：

1. 装了多少个技能，装在哪个目录
2. 怎么开始：**对 DSH 说「hello dsh」**，它会带着走一遍
3. 如果缺 Key，告诉他怎么配（见上面第 3 项）
4. 完整教程在 `~/.dsh/skills/` 同源仓库的 `docs/hello-dsh.md`

---

## 重要约束

**只写这两个目录：`~/.dsh/skills/` 和 `~/.agents/skills/`。**

- 不要修改 shell 配置（`.bashrc`、`.zshrc`、`.profile`）
- 不要修改 git 全局配置
- 不要装任何全局 npm 包
- 不要替用户设置或写入 API Key
- 不要动用户已有的、不属于本仓库的技能目录

---

## 卸载

按名字逐个删除，**绝对不要用通配符**，否则会误删用户自己写的技能：

```sh
for n in $(ls /tmp/hello-dsh/examples/skills); do
  rm -rf ~/.dsh/skills/"$n"
done
```

## 更新

```sh
cd /tmp/hello-dsh && git pull
cp -R examples/skills/* ~/.dsh/skills/
```

技能是热加载的，**不需要重启 DSH**。

---

## 排查

**技能装了但 DSH 看不到？** 按顺序查：

1. `SKILL.md` 的 frontmatter 里 `name` 是不是 kebab-case（必须是，且与目录名一致）
2. 有没有把 `user-invocable` 写成 `userInvocable` —— 驼峰会导致**整个技能被丢弃**，只有一条警告不报错
3. 有没有嵌套目录（只扫一层，`skills/a/b/SKILL.md` 不会被发现）

一条命令扫出这类问题：

```sh
npx dsh-doctor
```

**`npx` 卡住不动？** 首次下载 DSH 需要时间，等几分钟。如果用户在中国大陆，可能需要配置 npm 镜像。

**报 `MISSING_CREDENTIAL`？** 缺 API Key，见第一步第 3 项。
