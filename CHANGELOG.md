# Changelog

All notable changes to **polily-plugin** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] — 2026-05-18

Docs-only release syncing the public-facing portion of `events.event_metadata`
documentation from polily's `skill_sources/core/04_data_freshness.md` v0.12.2
edit. **No SKILL.md content semantics change**, just classification accuracy
+ unreliability warning surfaced.

### Changed

- **`events.event_metadata` reclassified from "Bucket 4 — Static" to a new
  "Bucket 5 — Externally-curated, freshness-tracked"** in `skills/polily/SKILL.md`.
  Prior classification was wrong — polily refetches `event_metadata` when
  Polymarket's `context_requires_regen=true` flag fires (see polily's
  `polily/daemon/event_metadata_regen.py`, shipped v0.12.0). New Bucket 5
  warns about the flag being **empirically unreliable** (polily v0.12.2's
  T-2 dev_feedback evidence: descriptions stayed 5-6 days stale while the
  flag was false) and directs Claude Code chat sessions to always check
  `context_updated_at` against the current time before treating
  `context_description` as authoritative.

### Source-of-truth

This file was regenerated from polily's `skill_sources/core/*.md` via
polily's `scripts/generate_skills.py` — same single-source-of-truth pipeline
that produced earlier v0.1.x releases. The internal-only ephemeral-block
details (which talk about polily's analytical agent's prompt injection)
are filtered out by audience tags; this release only carries the
publicly-meaningful part of the Bucket 5 reclassification.

## [0.1.4] — 2026-05-17

Docs-only release fixing incorrect install commands. **No SKILL.md or
manifest schema changes.**

### Fixed

- **Removed the `github:` prefix from all install/upgrade commands**
  in README, CHANGELOG, and CLAUDE.md. The `/plugin marketplace add
  github:owner/repo` form silently returns *"no content"* in Claude
  Code v2.1.x — three back-to-back attempts during a v0.1.3 smoke test
  hit this. The slash-command parser's modal help lists the valid
  formats: `owner/repo` (GitHub), `git@github.com:owner/repo.git`
  (SSH), `https://...marketplace.json`, or `./path/to/marketplace`.
  The bare `owner/repo` form is what we use now.

- **Removed the "alternate one-shot install" line** that claimed
  `/plugin install github:ShiyuCheng2018/polily-plugin` works without
  adding the marketplace first. Same suspect source — unverified
  against actual Claude Code behavior, and now suspect by association
  with the `github:` prefix. The two-step `marketplace add` +
  `install` is the only flow we have reproducible evidence for.

### Added

- **README "Format details" subsection** listing the 4 valid marketplace
  source formats verbatim from Claude Code's modal help, with an
  explicit warning against the `github:` prefix.
- **README "Modal fallback" subsection** for users whose Claude Code
  version doesn't accept the inline argument: run `/plugin marketplace
  add` bare and use the interactive modal.
- **`/reload-plugins` mention** — Claude Code prompts this after
  `/plugin install` to activate the plugin without restarting the
  session. Not in the prior docs.
- **Stronger "run as two separate commands, don't paste both at once"
  framing** in the install section. The smoke test that surfaced the
  prefix bug also surfaced this UX trap (the second command got
  shoved into the first command's modal input).

## [0.1.3] — 2026-05-17

User-upgrade-flow hardening. **No SKILL.md content changes.** This release
exists to (a) document how users actually get future updates, (b) work around
a known Claude Code marketplace-refresh bug, and (c) prevent the maintainer
from accidentally shipping a version with mismatched manifest files.

### Added

- **README "Upgrading" section** documenting the two-step update flow
  (`/plugin marketplace update polily-plugin` → `/plugin update polily@polily-plugin`)
  and the rationale (Claude Code [issue #21995](https://github.com/anthropics/claude-code/issues/21995):
  `/plugin update` alone doesn't fast-forward the local marketplace clone,
  so single-step updates often report "already at the latest version" even
  after a real release).
- **README "Troubleshooting" subsection** for the most likely user
  failure modes (`/plugin update` reports stale; `/plugin list` and
  `/plugin details` for diagnostics).
- **CI: version-sync gate** (`scripts/check_version_sync.py` +
  `version-sync-check` job in `ci.yml`). Validates that
  `.claude-plugin/plugin.json.version` and the matching entry in
  `.claude-plugin/marketplace.json.plugins[].version` are byte-for-byte
  identical. Per Claude Code's docs, plugin.json wins silently when both
  are set — drift would make the marketplace listing lie.

### Changed

- **`.claude-plugin/marketplace.json` adds `"autoUpdate": true`** at the
  marketplace root. Newer Claude Code clients use this to refresh the
  marketplace catalog on session start, partially mitigating the
  marketplace-cache bug above. Third-party-marketplace autoUpdate support
  varies between Claude Code releases, so the README still documents the
  explicit two-step as the reliable path.

## [0.1.2] — 2026-05-17

### Fixed

- **Plugin manifest moved to `.claude-plugin/plugin.json`** — the canonical lookup
  location for Claude Code plugins. The prior root-level `plugin.json` was being
  silently ignored; Claude Code was falling back to bare auto-discovery of
  `skills/polily/SKILL.md` and the manifest metadata (name, version, description)
  never reached the plugin manager. With this fix, `/plugin list` and
  `/plugin details` now show the right info.

- **Added `.claude-plugin/marketplace.json`** so the repo functions as a
  self-contained Claude Code marketplace. Users can now run
  `/plugin marketplace add ShiyuCheng2018/polily-plugin` followed by
  `/plugin install polily@polily-plugin` — the standard two-step path used by
  superpowers and other plugins in `claude-plugins-official`.

### Changed

- **Plugin install identifier `polily-plugin` → `polily`.** The repo stays named
  `polily-plugin` (that name is now the *marketplace* identifier). The plugin
  itself is invoked as `polily@polily-plugin`. This mirrors the convention
  superpowers uses (repo `obra/superpowers`, plugin `superpowers`).

- **Manifest enriched** with `author`, `license`, and `keywords` fields to match
  the documented Claude Code plugin schema and improve discoverability in
  `/plugin details` and any future marketplace listings.

- **README install section rewritten** to use the modern `/plugin marketplace add`
  + `/plugin install` flow. The legacy `claude plugin add <repo>` command no
  longer exists in current Claude Code releases.

### Added

- **CI: CHANGELOG release-discipline gate** (`scripts/check_changelog.py` +
  `.github/workflows/ci.yml`). Mirrors the sister polily repo's gate, adapted
  for polily-plugin's master-only branching model. Runs on every PR; validates
  (1) topmost section is `[X.Y.Z]` not `[Unreleased]`, (2) top release has a
  `releases/tag/vX.Y.Z` footer link, (3) `[Unreleased]` link compares against
  the current top release. Catches the forgotten-rename and stale-link mistakes
  before merge.

### Notes

- No SKILL.md content changes. The skill itself is the v0.1.1 build (regenerated
  against polily v0.12.0); this release is pure packaging-standards alignment
  + CI hardening.
- No semantic CLAUDE.md changes — just adds a pointer to the new gate.

## [0.1.1] — 2026-05-17

### Changed

- Regenerate `skills/polily/SKILL.md` against polily v0.12.0 baseline — picks up
  the BREAKING markdown agent output, Strategy page, `has_position` drift fix,
  and runtime methodology lookup pattern (§9 fallback ladder).
- Decorate README to match polily main-repo style: badges, AI_METADATA block,
  before/after chat examples in the "Why install this" section.

### Added

- `CLAUDE.md` scoped to polily user lifecycle support — inclusion bar
  ("does this skill help polily users be more effective at using polily?")
  documented for future contributors.

## [0.1.0] — 2026-05-09

### Added

- Initial release. Single skill `polily` covering onboarding, daily analysis
  follow-ups, custom strategy authoring, and troubleshooting reference. Skill
  generated from `polily/agents/skill_sources/core/*.md` via
  `scripts/generate_skills.py` in the sister repo.

[Unreleased]: https://github.com/ShiyuCheng2018/polily-plugin/compare/v0.1.5...master
[0.1.5]: https://github.com/ShiyuCheng2018/polily-plugin/releases/tag/v0.1.5
[0.1.4]: https://github.com/ShiyuCheng2018/polily-plugin/releases/tag/v0.1.4
[0.1.3]: https://github.com/ShiyuCheng2018/polily-plugin/releases/tag/v0.1.3
[0.1.2]: https://github.com/ShiyuCheng2018/polily-plugin/releases/tag/v0.1.2
[0.1.1]: https://github.com/ShiyuCheng2018/polily-plugin/releases/tag/v0.1.1
[0.1.0]: https://github.com/ShiyuCheng2018/polily-plugin/releases/tag/v0.1.0
