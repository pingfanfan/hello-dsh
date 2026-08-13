# 给 AI Agent 的安装指令

> 这份文件是写给 AI agent 读的（Codex、Claude Code、DSH 自己、任何能读写文件的 agent）。
> 人类用户：把本文件的链接丢给你的 agent，说「照这个装」即可。

## 任务

把 `pingfanfan/dsh-skills` 仓库里的技能安装到用户本机，让 DeepSeek Harness 能发现它们。

## 你需要知道的

技能是**纯 Markdown 文件**，安装 = 把目录拷到约定位置。**不需要编译、不需要 npm install、不需要任何构建步骤。**

目标位置二选一：

| 位置 | 用于 |
|---|---|
| `~/.dsh/skills/` | 只给 DSH 用 |
| `~/.agents/skills/` | 跨 agent 共享（Claude Code 等也能读到） |

**默认用 `~/.dsh/skills/`**，除非用户说要跨 agent 共享。

## 步骤

### 1. 取得文件

优先用 git（能保留更新能力）：

```sh
git clone --depth 1 https://github.com/pingfanfan/dsh-skills.git /tmp/dsh-skills
```

没有 git 时用打包下载：

```sh
curl -fsSL https://github.com/pingfanfan/dsh-skills/archive/refs/heads/main.tar.gz | tar xz -C /tmp
# 解出 /tmp/dsh-skills-main
```

### 2. 拷贝

```sh
mkdir -p ~/.dsh/skills
cp -R /tmp/dsh-skills/skills/* ~/.dsh/skills/
```

### 3. 验证

```sh
ls ~/.dsh/skills/
```

应该看到 20 多个目录，每个里面有一个 `SKILL.md`。

如果用户配置了 `DEEPSEEK_API_KEY`，可以直接验证：

```sh
npx @deepseek-ai/dsh --profile headless "hello dsh"
```

看到 `HELLO DSH` 开头的暗号就说明装好了。

### 4. 告诉用户

装了哪些技能、装在哪个目录、怎么开始用（建议对 DSH 说「hello dsh」）。

## 重要约束

**只写这两个目录：`~/.dsh/skills/` 和 `~/.agents/skills/`。**

- 不要修改 shell 配置（`.bashrc`、`.zshrc`、`.profile`）
- 不要修改 git 全局配置
- 不要装任何全局 npm 包
- 不要动用户已有的、不属于本仓库的技能目录

## 卸载

按名字逐个删除，**不要用通配符**，否则会误删用户自己写的技能：

```sh
for n in $(ls /tmp/dsh-skills/skills); do
  rm -rf ~/.dsh/skills/"$n"
done
```

## 更新

重新拷贝即可，同名目录会被覆盖：

```sh
cd /tmp/dsh-skills && git pull
cp -R skills/* ~/.dsh/skills/
```

技能是热加载的，**不需要重启 DSH**。

## 常见问题

**技能装了但 DSH 看不到？** 按这个顺序查：

1. `SKILL.md` 的 frontmatter 里 `name` 是不是 kebab-case（必须是）
2. 有没有把 `user-invocable` 写成 `userInvocable`（驼峰会导致**整个技能被丢弃**，只有一条警告）
3. 有没有嵌套目录（只扫一层，`skills/a/b/SKILL.md` 不会被发现）

可以直接扫：

```sh
npx dsh-doctor
```

**用户没装 DSH？** 先让他跑一次：

```sh
npx @deepseek-ai/dsh web
```

这会生成 `~/.dsh/` 目录结构。
