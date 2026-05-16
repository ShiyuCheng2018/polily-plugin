# CLAUDE.md (polily-plugin)

Instructions for Claude Code working in this repo.

## What this repo is

A Claude Code marketplace plugin pack scoped to **polily user lifecycle support**. Every skill in the pack helps users get more out of [polily](https://github.com/ShiyuCheng2018/polily) at some point in their journey — onboarding, daily analysis follow-ups, custom strategy authoring, troubleshooting, upgrades.

The pack may grow with additional skills, including community contributions. **The inclusion bar is: the skill makes polily users more effective at using polily.** Generic Claude Code skills, broader prediction-market tooling, or unrelated finance topics belong in different packs.

## Editing skills

Skills live in `skills/<name>/SKILL.md`. Before editing one, **read its top matter first**. Some skills carry a `GENERATED FILE — DO NOT EDIT` header naming a source repo and telling you where to make changes instead. If a skill has no such header, edit the SKILL.md directly, following Anthropic's skill conventions:

- YAML frontmatter with `name` and `description`
- The description shapes when Claude activates the skill — be specific about polily-relevant triggers, and include negative triggers (e.g. "Do NOT activate for generic Polymarket questions unrelated to polily")
- Body content guides what Claude does once activated

## Current skills

- `skills/polily/` — reference for polily users chat-querying their install (DB schema, mechanics, file paths, runtime methodology lookup). Generated from polily's `polily/agents/skill_sources/core/*.md` via `scripts/generate_skills.py` in the [polily repo](https://github.com/ShiyuCheng2018/polily). To change content, edit polily sources and regenerate; do NOT hand-edit `SKILL.md` here.

(Append bullets as new polily-lifecycle skills land.)

## Plugin manifest discipline

`plugin.json` is the source of truth for what the marketplace ships. A new skill is not part of the pack until you add `./skills/<name>` to `plugin.json.skills`. A directory under `skills/` without a manifest entry is dead code.

## Versioning

This pack releases independently of polily. Bump `plugin.json.version` and tag a new release when:

- A skill's content changes meaningfully (new section, removed section, methodology rewrite)
- A skill is added or removed
- Marketplace metadata changes (description, icons, etc.)

Skip bumps for cosmetic regens (whitespace, headers).

## Contributing a new skill

Ask first: **does this skill help polily users be more effective at using polily?** Examples that pass: onboarding helper, custom-strategy authoring guide, debugging assistant for polily logs, polymarket-data explorer for polily users, polily upgrade helper. Examples that don't: generic financial analysis skill, broader Polymarket trading tooling, unrelated Claude Code patterns. Polily-bounded scope keeps the pack focused; off-scope contributions get redirected to other homes.

Steps:

1. Create `skills/<your-skill-name>/SKILL.md` with YAML frontmatter (`name` + `description`)
2. Tune the description to fire on the right polily-user queries and not on unrelated ones
3. Add `./skills/<your-skill-name>` to `plugin.json.skills`
4. Bump `plugin.json.version` (minor for additions; major for removals or incompatible changes)
5. PR

If your skill's content is generated from another repo (polily's single-source-of-truth pattern, or your own equivalent), stamp `SKILL.md` with a `GENERATED FILE — DO NOT EDIT` header naming the source, and add a bullet to "Current skills" above documenting it.

## What's always safe to edit

- `README.md`, `LICENSE`, `CLAUDE.md` (this file)
- `plugin.json`
- Any skill that doesn't carry a `GENERATED FILE — DO NOT EDIT` header
