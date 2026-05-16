# polily-plugin

<!-- AI_METADATA
purpose: Claude Code marketplace skill pack scoped to polily user lifecycle support
keywords: polily, polymarket, claude-code, claude-code-plugin, skill, marketplace, prediction-market
suitable_for: polily users wanting Claude Code to know their install (DB schema, analyses, methodology) without re-explaining each chat
install: claude plugin add github.com/ShiyuCheng2018/polily-plugin
requires: Claude Code; polily installed locally for most skills
sister_repo: https://github.com/ShiyuCheng2018/polily
license: MIT
-->

[![License](https://img.shields.io/github/license/ShiyuCheng2018/polily-plugin)](https://github.com/ShiyuCheng2018/polily-plugin/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/ShiyuCheng2018/polily-plugin?label=plugin%20release)](https://github.com/ShiyuCheng2018/polily-plugin/releases)
[![Last commit](https://img.shields.io/github/last-commit/ShiyuCheng2018/polily-plugin)](https://github.com/ShiyuCheng2018/polily-plugin/commits/master)
[![polily](https://img.shields.io/badge/polily-main_repo-9cf?logo=github)](https://github.com/ShiyuCheng2018/polily)

Claude Code skills scoped to **[polily](https://github.com/ShiyuCheng2018/polily) user lifecycle support** — onboarding, daily analysis follow-ups, custom strategy authoring, troubleshooting. Install the pack once; the skills auto-activate in your Claude Code sessions when you reference polily, no re-explaining each time.

## Why install this

Without the plugin, asking Claude Code about your polily install means starting from scratch every chat:

> *"What's the schema of polily's `analyses` table? It's a Polymarket monitoring tool I run locally; the DB is at..."*

With the plugin loaded, Claude already knows polily — DB schema, daemon mechanics, file paths, and how polily's analytical agent thinks. You ask, Claude answers, grounded in your actual `polily.db` state:

> *"Why did polily say BTC market edge was thin in yesterday's analysis?"*
> *"Show me my biggest open position and how it's tracking against the entry thesis."*
> *"What's my realized PnL this week, by event?"*
> *"I want to write a custom analysis strategy — walk me through the active_strategy mechanism."*

Claude consults the skill's reference knowledge, runs SQL against your local `polily.db`, fetches polily's analytical methodology at runtime (your custom strategy if you've authored one, polily's official `default.md` otherwise), and answers in polily's own framing — consistent with whatever you just read in the TUI.

## Install

```bash
claude plugin add github.com/ShiyuCheng2018/polily-plugin
```

(Or via Claude Code's plugin marketplace UI.)

Requires [Claude Code](https://claude.com/claude-code). Most skills also assume polily is installed locally (`pipx install polily`) — they'll fall back to fetching from GitHub when polily isn't installed, but the local-install experience is faster and more accurate.

## Skills in this pack

| Skill | What it does | Source |
|---|---|---|
| [`skills/polily/`](skills/polily/SKILL.md) | Reference for polily users chat-querying their install — DB schema, daemon mechanics, file paths, runtime methodology lookup (consults user's active strategy or polily's `default.md` at chat time) | [polily/agents/skill_sources/core/](https://github.com/ShiyuCheng2018/polily/tree/master/polily/agents/skill_sources/core) |

As polily evolves and new lifecycle-stage skills land, they get added here. See [CLAUDE.md](CLAUDE.md) for the inclusion bar and contribution flow.

## Activation triggers

The polily skill activates when you mention polily by name in a Claude Code chat, or reference polily-specific concepts (`structure_score`, `polily.db`, `next_check_at`, etc.). It does **not** activate on generic Polymarket questions unrelated to polily — that boundary is encoded in the skill's YAML `description` so the plugin stays scoped.

Examples that activate:

- "Why did polily flag this event as Tier C?"
- "Show me my polily positions"
- "polily structure_score 怎么算的？"

Examples that **don't**:

- "What is Polymarket?" (no polily reference; generic platform question)
- "How does Kalshi compare to Polymarket?" (no polily reference; cross-platform comparison)

## Single source of truth

Each skill file carries a `GENERATED FILE — DO NOT EDIT` header naming its source repo. Hand-edits to generated skills are overwritten on the next regeneration. To change a generated skill's content, edit the source files in the source repo and run its generator:

```bash
cd path/to/polily
python scripts/generate_skills.py --plugin-repo path/to/polily-plugin
```

The generator writes to both polily's internal copy AND this repo's artifact. See [CLAUDE.md](CLAUDE.md) for full rules.

## Versioning

This pack releases independently of polily. Each release bumps `plugin.json.version` and gets a corresponding git tag. See [releases](https://github.com/ShiyuCheng2018/polily-plugin/releases) for history.

## License

[MIT](LICENSE)
