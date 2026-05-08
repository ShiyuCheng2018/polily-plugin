# polily-plugin

Claude Code plugin for the [polily](https://github.com/ShiyuCheng2018/polily) Polymarket monitoring agent. Loads polily's reference knowledge (DB schema, daemon mechanics, file paths, data freshness rules) into Claude Code sessions so Claude can help you query / debug / extend polily without you re-explaining every time.

## Install

```bash
claude plugin add github.com/ShiyuCheng2018/polily-plugin
```

(Or via Claude Code's plugin marketplace UI.)

## What's inside

- `skills/polily/SKILL.md` — the polily reference manual. Activates when you mention polily, polymarket monitoring, or polily.db queries.

## Source of truth

This plugin is **generated** from polily's source. Do not hand-edit `skills/polily/SKILL.md` — your changes will be overwritten on the next regeneration.

To update the skill content, edit `polily/agents/skill_sources/core/*.md` in the polily repo, then run:

```bash
cd path/to/polily
python scripts/generate_skills.py --plugin-repo path/to/polily-plugin
```

## Versioning

This plugin releases independently of polily. The skill content is regenerated whenever polily's `skill_sources/core/` changes meaningfully (new tables, new mechanics, etc.).

## License

MIT
