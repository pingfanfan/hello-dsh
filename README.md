<div align="center">

# Hello DSH

**The first lesson for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)**

From "open a terminal" to your first plugin, in 30 minutes

[![Tutorial](https://img.shields.io/badge/tutorial-10%20steps-blue)](docs/hello-dsh.md)
[![Skills](https://img.shields.io/badge/example%20skills-22-green)](examples/skills/)
[![DSH](https://img.shields.io/badge/DSH-0.1.0--rc.6%20verified-orange)](https://github.com/deepseek-ai/deepseek-harness)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

**English** · [中文](README.zh.md) · [**Start →**](docs/hello-dsh.md)

</div>

---

DSH introduces itself as *"Everything is a Plugin."*

That is not marketing. Open Settings → Plugins → Plugin list and look at the count:

![Plugin list](assets/05-plugin-list-133.png)

**133 of them.** `llm` (the model adapter), `session` (conversation history), `webserver` (the page you are looking at), `ui-sidebar` (the sidebar on the left), and `agent-loop` — **the agent loop itself is a plugin**.

This repo walks you from "open a terminal" to building your own plugin and watching its lifecycle.

---

## Start here

**→ [Full tutorial: Hello DSH](docs/hello-dsh.md)**

> 🌏 **The tutorial is currently written in Chinese.** An English version is in progress.
> The code, commands, and screenshots are language-neutral, so the walkthrough is still
> followable — and the skills in [`examples/skills/`](examples/skills/) work regardless of
> what language you read.
>
> ⚠️ **Launch the web UI with `--patch`**, or skills silently do nothing. See
> [the gotcha below](#one-gotcha).

It assumes you have nothing: no Node.js, no command-line experience. Every section ends with a checkpoint — **you don't move on until you see the expected result**.

| Steps | What | Time |
|---|---|---|
| 1–2 | Open a terminal, install Node.js | 7 min |
| 3–5 | Launch DSH, configure the API key, pick a workspace | 10 min |
| 6 | **See all 133 plugins for yourself** | 3 min |
| 7–8 | **Build your first plugin, watch its lifecycle** | 10 min |
| 9–10 | What's next, theory (optional) | 13 min |

Steps 1–8 take about 30 minutes and leave you with a working setup.

---

## Two routes to extend DSH

| Route | What you write | Effort | Good for |
|---|---|---|---|
| **Markdown** (skill) | One text file | 5 minutes | Changing how the model judges, formats, and works |
| **TypeScript** (code plugin) | A code module | 30+ minutes | New tools, external services, UI changes |

**Rule of thumb: if you can explain it in plain language, take the Markdown route.**

The tutorial walks through both.

---

## Ready-made examples

Once you're through the tutorial, [`examples/skills/`](examples/skills/) has 22 Chinese-language skills ready to use.

### Let an AI install them (easiest)

Hand this link to Codex, Claude Code, or DSH itself:

```
https://github.com/pingfanfan/hello-dsh/blob/main/INSTALL-FOR-AGENTS.md
install this
```

It checks Node, DSH, and the API key first, then copies files.

### Or run one command

```sh
git clone https://github.com/pingfanfan/hello-dsh.git
cd hello-dsh && ./install.sh
```

Preview first: `./install.sh --dry-run`
Remove: `./install.sh --uninstall`

### The skills

| Skill | Use it when |
|---|---|
| `hello-dsh` | **Start here**: verify the plugin system, lifecycle, theory |
| `dsh-onboarding` | First run of DSH, or stuck on startup, workspace, permissions |
| `dsh-skill-dev` | Full rules for writing skills (Markdown route) |
| `dsh-first-plugin` | Building your first code plugin (tested walkthrough) |
| `dsh-plugin-dev` | Full rules for writing plugins (TypeScript route) |
| `dsh-troubleshoot` | Won't start, config not applying, UNKNOWN_TOOL, missing skills |
| `plan-before-code` | A task spanning several files, with unknowns |
| `code-review-cn` | Reviewing a change, PR, or diff |
| `debug-systematically` | A bug, a failing test, "it worked yesterday" |
| `explain-codebase` | Getting oriented in an unfamiliar project |
| `refactor-safely` | Refactoring, splitting functions, removing duplication |
| `test-first` | Writing tests, implementing a feature, fixing a bug |
| `api-design` | Designing an interface, adding a public method |
| `error-handling` | Designing error handling, throw vs return |
| `perf-optimize` | Optimizing performance, finding what's slow |
| `security-review-cn` | Security review, attack surface, credential handling |
| `commit-message` | Writing commit messages, splitting changes |
| `pr-description` | Writing a PR description, preparing review |
| `write-tech-cn` | Writing Chinese docs, READMEs, technical posts |
| `write-docs-cn` | Writing or organizing project docs, API references |
| `web-research` | Researching online, verifying facts, evaluating options |
| `ask-good-questions` | Asking a technical question, reporting a bug |

Once installed, say **"hello dsh"** to DSH and it walks you through, one layer at a time.

---

## One gotcha

⚠️ **The DSH web UI ships with skills disabled** (the CLI profile has them on). Verified on `0.1.0-rc.6`.

To use skills in the web UI:

```sh
npx @deepseek-ai/dsh web --patch ./enable-skills-in-web.yml
```

That file is in this repo's root.

---

## What this tutorial found

Writing this meant running DSH end to end on two clean Macs. These behaviors are documented in the tutorial because each one silently blocks a beginner:

| Finding | Why it matters |
|---|---|
| The web profile ships with `tool-skill` and `skill-filesystem` **disabled**; `headless` has them on | Same skill works in the CLI, silently does nothing in the web UI, with no error |
| The web UI **requires a workspace** before the send button activates | The CLI has no such requirement, so it's easy to miss when testing |
| A stale DSH process holding port 3080 makes the page **load normally** | New instance exits with `EADDRINUSE`; the browser silently talks to the old one and no config change appears to take effect |
| `--patch` **inserts** rather than overrides, so patched plugins mount twice | Harmless, but the plugin list shows 7 skill plugins instead of 5 |
| A camelCase frontmatter key drops the **entire skill**, warning only | Documented fail-closed behavior, but hard to diagnose without knowing it |

All verified on `0.1.0-rc.6`.

## Companion tool

`dsh-doctor` — config health checks that catch silent failures:

```sh
npx dsh-doctor
```

Read-only. Every rule maps to a real failure documented in DeepSeek's own docs or postmortems.

---

## How these skills are written

Following DSH's own [`.agents/skills/`](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills) — 11 skills DeepSeek wrote for internal use. What they have in common:

1. **Guidance, not a checklist** (their words: *"This skill is guidance, not a complete checklist"*)
2. **Name the sources of truth**, and say "read them, don't restate them"
3. **Layer it**: blocking requirements / manual checks / what not to do
4. **A dedicated "what not to do" section** — it prevents more than the positive instructions do

See [docs/writing-skills.md](docs/writing-skills.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Two requirements: Chinese, and you actually use it.

## License

MIT

---

Unofficial community project. Not affiliated with DeepSeek.
