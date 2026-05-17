#!/usr/bin/env python3
"""Version-sync validator for `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

Claude Code resolves a plugin's effective version from the first of these
that is set:
  1. `version` in `.claude-plugin/plugin.json`
  2. `version` in the plugin's entry inside `.claude-plugin/marketplace.json`
  3. The git commit SHA (fallback when neither is set)

Per the official plugin docs, **the `plugin.json` value always wins
silently** when both are set — so if the two drift, the marketplace
listing is a lie. Source:
  https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels

This gate enforces parity:

1. Both files exist and parse as JSON.
2. `plugin.json.version` is set (we use explicit versions, not commit SHAs).
3. `marketplace.json.plugins[*]` contains exactly one entry whose `name`
   matches `plugin.json.name`.
4. That entry's `version` matches `plugin.json.version` byte-for-byte.

Usage:
    python scripts/check_version_sync.py
    python scripts/check_version_sync.py <path-to-repo-root>

Exits 0 on pass, 1 on any violation. Pure stdlib — no install step.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


def _load_json(path: Path, errors: list[str]) -> dict | None:
    """Read + parse JSON; on failure, append a human error and return None."""
    if not path.exists():
        errors.append(f"{path} does not exist")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{path} is not valid JSON: {e}")
        return None


def validate(repo_root: Path) -> ValidationResult:
    """Pure function — no stderr / exit. Caller wraps with CLI handling."""
    result = ValidationResult(ok=True)
    plugin_path = repo_root / ".claude-plugin" / "plugin.json"
    market_path = repo_root / ".claude-plugin" / "marketplace.json"

    plugin = _load_json(plugin_path, result.errors)
    market = _load_json(market_path, result.errors)

    if plugin is None or market is None:
        result.ok = False
        return result

    # --- Rule 1: plugin.json.version is set ---
    plugin_version = plugin.get("version")
    if not plugin_version:
        result.ok = False
        result.errors.append(
            "plugin.json is missing `version`. We use explicit semver "
            "versions, not git-SHA fallback. Add `\"version\": \"X.Y.Z\"`."
        )

    plugin_name = plugin.get("name")
    if not plugin_name:
        result.ok = False
        result.errors.append("plugin.json is missing `name`.")

    # --- Rule 2: marketplace.json has plugins array ---
    plugins = market.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        result.ok = False
        result.errors.append(
            "marketplace.json must have a non-empty `plugins` array."
        )
        return result

    # --- Rule 3: find matching entry by name ---
    matching = [p for p in plugins if p.get("name") == plugin_name]
    if not matching:
        result.ok = False
        result.errors.append(
            f"marketplace.json has no entry with `name: {plugin_name!r}` "
            f"matching plugin.json. Found entries: "
            f"{[p.get('name') for p in plugins]}"
        )
        return result
    if len(matching) > 1:
        result.ok = False
        result.errors.append(
            f"marketplace.json has {len(matching)} entries with "
            f"`name: {plugin_name!r}` — expected exactly one."
        )

    entry = matching[0]
    entry_version = entry.get("version")

    # --- Rule 4: versions match byte-for-byte ---
    if plugin_version and entry_version != plugin_version:
        result.ok = False
        result.errors.append(
            f"Version drift: `.claude-plugin/plugin.json.version` is "
            f"{plugin_version!r} but `.claude-plugin/marketplace.json.plugins["
            f"name={plugin_name!r}].version` is {entry_version!r}. "
            f"Per Claude Code's resolution rules, plugin.json wins silently — "
            f"the marketplace listing would be lying. Bump both in lockstep."
        )

    return result


def main(argv: list[str]) -> int:
    repo_root = Path(argv[0]) if argv else Path(".")
    repo_root = repo_root.resolve()

    result = validate(repo_root)
    if result.ok:
        print(f"✓ {repo_root}: plugin.json ↔ marketplace.json version-sync OK")
        return 0

    print(
        f"✗ {repo_root}: version-sync violations:",
        file=sys.stderr,
    )
    for err in result.errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
