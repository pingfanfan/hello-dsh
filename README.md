# dsh-skills

English | [中文](README.zh.md)

Chinese-language skills for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (DSH).

Skills are plain Markdown — no code, no build step, no package to publish. Drop a directory in and DSH picks it up. Edits apply without a restart.

## Install

### Easiest: let your agent do it

Hand this link to Codex, Claude Code, or DSH itself:

```
https://github.com/pingfanfan/dsh-skills/blob/main/INSTALL-FOR-AGENTS.md
install this
```

Skills are plain Markdown, so the agent only copies files. No build, no npm install.

### Or run one command

```sh
git clone https://github.com/pingfanfan/dsh-skills.git
cd dsh-skills && ./install.sh
```

Installs to `~/.dsh/skills/`. DSH discovers them automatically — **no restart**.

Preview first: `./install.sh --dry-run`
Cross-agent directory: `./install.sh --agents-dir`
Remove: `./install.sh --uninstall`

You can also just copy any directory under `skills/` into `~/.dsh/skills/`.

## First lesson: Hello DSH

Once installed, just say this to DSH:

```
hello dsh
```

It prints a passphrase that could only have come from a local file, then walks you through it one layer at a time: what a skill is, how the lifecycle works, when to write a plugin instead, and the Cordis theory behind it.

**Full walkthrough**: [docs/hello-dsh.md](docs/hello-dsh.md) — 20 minutes from zero to a working skill *and* a working plugin, with real transcripts including the three errors you will hit writing a plugin and their exact fixes.

## The skills

| Skill | Use it when |
|---|---|
| `hello-dsh` | **Start here**: verify the skill system, lifecycle, skill vs plugin, Cordis theory |
| `dsh-onboarding` | First run of DSH, or stuck on startup, workspace, permissions, discovery |
| `dsh-skill-dev` | Writing a skill, or a skill is not being discovered |
| `dsh-first-plugin` | Building and installing your first plugin (tested walkthrough) |
| `dsh-plugin-dev` | Writing a plugin, or a plugin fails to load or inject |
| `dsh-troubleshoot` | DSH won't start, config not taking effect, UNKNOWN_TOOL, missing skills |
| `plan-before-code` | A task spanning several files, with unknowns, or over half a day |
| `code-review-cn` | Reviewing a change, PR, or diff |
| `debug-systematically` | A bug, a failing test, "it worked yesterday" |
| `explain-codebase` | Getting oriented in an unfamiliar project |
| `refactor-safely` | Refactoring, splitting functions, removing duplication |
| `test-first` | Writing tests, implementing a feature, fixing a bug |
| `api-design` | Designing an interface, adding a public method |
| `error-handling` | Designing error handling, deciding throw vs return |
| `perf-optimize` | Optimizing performance, finding what's slow |
| `security-review-cn` | Security review, attack surface, credential handling |
| `commit-message` | Writing commit messages, splitting changes |
| `pr-description` | Writing a PR description, preparing review |
| `write-tech-cn` | Writing Chinese docs, READMEs, technical posts |
| `write-docs-cn` | Writing or organizing project docs, API references, tutorials |
| `web-research` | Researching online, verifying facts, evaluating options |
| `ask-good-questions` | Asking a technical question, reporting a bug, filing an issue |

More are being added.

## How these are written

**Following the official pattern.** The DSH repo ships [`.agents/skills/`](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills) — 11 skills DeepSeek wrote for their own use. These follow that model: name the sources of truth, give judgment criteria rather than checklists, prefer few and accurate over many and thin.

**Chinese first.** The bundled official skills are in English.

**Instructions, not documentation.** A skill tells the model what to do first, what not to do, and how to know it worked. It is not a background essay.

## About the installer

`install.sh` is the only code here, and it is deliberately conservative:

- Writes only to `~/.dsh/skills` or `~/.agents/skills` — nowhere else
- Prints the exact target paths and asks before writing
- Uninstall removes **only the skills listed in this repo, matched by name** — no globs, so your own skills are never touched
- Never modifies shell profiles, git config, or any global setting
- If the script breaks, the skills still work — copy the directories by hand

## Writing your own

```
~/.dsh/skills/<name>/SKILL.md
```

```markdown
---
name: my-skill          # required, kebab-case
description: ...        # required — this is how the model decides to load it
---

(body is the instruction the model receives)
```

Discovery order (lower rank wins):

| Rank | Location |
|---|---|
| 100 | `<project>/.dsh/skills` |
| 200 | `<project>/.agents/skills` |
| 400 | `~/.dsh/skills` |
| 500 | `~/.agents/skills` |

Two traps:

- **Frontmatter keys must be kebab-case.** Write `userInvocable` instead of `user-invocable` and the entire skill is **silently dropped** with only a warning. Check this first when a skill "disappears".
- **`description` matters more than the body.** The model reads it to decide whether to load the skill at all. Say when to use it.

See [docs/writing-skills.md](docs/writing-skills.md).

## Contributing

Open a PR. Two requirements: Chinese, and you actually use it.

## License

MIT

---

Unofficial community project. Not affiliated with DeepSeek.
