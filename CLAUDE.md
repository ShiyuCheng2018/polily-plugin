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

This repo uses Claude Code's **canonical plugin layout** as of v0.1.2:

- `.claude-plugin/plugin.json` — the plugin manifest (name, version, author, keywords). Required location; Claude Code only looks here.
- `.claude-plugin/marketplace.json` — the marketplace index. Makes this repo a self-contained marketplace so users can `/plugin marketplace add ShiyuCheng2018/polily-plugin` (bare `owner/repo` form — no `github:` prefix, that variant silently fails). Has `"autoUpdate": true` at the marketplace root (added v0.1.3) so newer Claude Code clients refresh the catalog on session start.

Skills under `skills/<name>/SKILL.md` are **auto-discovered** by Claude Code — the manifest does not need to list them explicitly. A new skill becomes part of the pack the moment its `SKILL.md` lands.

The plugin's install identifier (`polily`) is separate from the repo name (`polily-plugin`). Repo = marketplace name; plugin within = install name. Mirrors the `obra/superpowers` convention.

**Version-bump nuance**: Claude Code resolves a plugin's effective version from `plugin.json.version` first, falling back to `marketplace.json.plugins[*].version`, falling back to git SHA. When both are set (our case), `plugin.json` wins **silently** — so if you bump one but not the other, the marketplace listing lies about what users actually get. The `version-sync-check` CI gate (v0.1.3) catches this before merge.

## Versioning

This pack releases independently of polily. Bump version and tag a new release when:

- A skill's content changes meaningfully (new section, removed section, methodology rewrite)
- A skill is added or removed
- Marketplace metadata changes (description, manifest schema, etc.)

Skip bumps for cosmetic regens (whitespace, headers).

**Bump in lockstep** — `.claude-plugin/plugin.json.version` AND `.claude-plugin/marketplace.json.plugins[0].version` must always match. Update `CHANGELOG.md` `[Unreleased]` → `[X.Y.Z] — YYYY-MM-DD` and add the footer compare link before tagging.

**CI gates the CHANGELOG discipline.** `.github/workflows/ci.yml` runs `scripts/check_changelog.py` on every PR — it'll fail the build if the topmost section is still `[Unreleased]`, the top release has no footer link, or `[Unreleased]` compares against a stale version. Run the script locally before pushing: `python3 scripts/check_changelog.py CHANGELOG.md`.

**CI also gates manifest version-sync.** `scripts/check_version_sync.py` validates that `.claude-plugin/plugin.json.version` and the matching entry in `.claude-plugin/marketplace.json.plugins[].version` are byte-for-byte identical. Per Claude Code's resolution rules, `plugin.json` wins silently when both are set — drift makes the marketplace listing lie. The gate catches this before merge. Run locally: `python3 scripts/check_version_sync.py`.

## Contributing a new skill

Ask first: **does this skill help polily users be more effective at using polily?** Examples that pass: onboarding helper, custom-strategy authoring guide, debugging assistant for polily logs, polymarket-data explorer for polily users, polily upgrade helper. Examples that don't: generic financial analysis skill, broader Polymarket trading tooling, unrelated Claude Code patterns. Polily-bounded scope keeps the pack focused; off-scope contributions get redirected to other homes.

Steps:

1. Create `skills/<your-skill-name>/SKILL.md` with YAML frontmatter (`name` + `description`)
2. Tune the description to fire on the right polily-user queries and not on unrelated ones
3. Bump version in `.claude-plugin/plugin.json` AND `.claude-plugin/marketplace.json` (keep them in sync; minor for additions, major for removals or incompatible changes)
4. Add a `[X.Y.Z]` section to `CHANGELOG.md` describing the change
5. PR

If your skill's content is generated from another repo (polily's single-source-of-truth pattern, or your own equivalent), stamp `SKILL.md` with a `GENERATED FILE — DO NOT EDIT` header naming the source, and add a bullet to "Current skills" above documenting it.

## What's always safe to edit

- `README.md`, `LICENSE`, `CLAUDE.md` (this file), `CHANGELOG.md`
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (version bumps + metadata)
- Any skill that doesn't carry a `GENERATED FILE — DO NOT EDIT` header
