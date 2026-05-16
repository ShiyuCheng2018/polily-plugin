---
name: polily
description: |
  Use when the user references polily — either asking follow-up questions about a polily-generated analysis (interpreting structure_score, edge claims, friction breakdowns, position guidance, why polily said what it said) or querying polily's local state (positions, wallet, past analyses in polily.db). Provides DB schema, daemon mechanics, file paths, and a runtime-lookup procedure for polily's analytical methodology. Do NOT activate for generic Polymarket questions unrelated to polily.
---

<!--
GENERATED FILE — DO NOT EDIT
Source: polily/agents/skill_sources/core/*.md
Generator: scripts/generate_skills.py
To modify: edit polily/agents/skill_sources/core/*.md, then re-run.
-->

## 1. About Polily

Polily is a Polymarket prediction-market monitoring tool — paste a Polymarket event URL into its TUI and it fetches the event + child markets, scores tradability across multiple dimensions, watches for price movements, surfaces friction (spread / fees / depth) explicitly, and dispatches an AI analysis on demand or on a daemon-driven cadence. State is SQLite at `~/Library/Application Support/polily/polily.db` (macOS default; see §5 for the full path resolution).

**Polily is read-only / advisory — it never executes trades on the user's behalf.** Analyses suggest operations (BUY / SELL / HOLD / stop-loss thresholds); the user always pulls the trigger via polymarket.com. When answering chat follow-ups, preserve this stance — recommend, don't execute.

## 2. Polily Mechanics

Polily is structured around two domain concepts:

- **Event** (`events` table): a Polymarket event identified by a slug. An event holds metadata (title, end_date, neg_risk flag, market_type, structure_score, tier) and references one or more child markets via `markets.event_id` FK.
- **Market** (`markets` table): a single tradable outcome under an event. Each market has yes_price / no_price / volume / spread / bid_depth / ask_depth, lifecycle state (closed, resolved_outcome ∈ `'yes' | 'no' | 'split' | 'void' | NULL`), and per-market `structure_score` + `score_breakdown` JSON (see §3 for the full column list).

**negRisk events** have multiple mutually-exclusive markets summing to ~1.0 (winner-take-all). For these, each market's `score_breakdown.implied_fair_value` is the implied price under the negRisk completeness identity:

    implied_fair_value(M) = 1 − Σ(other markets' yes_price)

This is computed at scan time and refreshed each daemon score-refresh cycle. Use it as a structural anchor for negRisk reasoning; for crypto markets, use `score_breakdown.mispricing_signal` instead.

**Daemon poll cycle**: a single global poll job runs every **30 s** on a dedicated APScheduler executor. Each tick: fetches prices for every market the user is monitoring, records movement signals into `movement_log`, drains overdue rows in `scan_logs` (the `scheduled_at` column — see §3) by dispatching AI analyses, and may auto-trigger a movement-driven analysis if magnitude × quality crosses thresholds.

**Trigger sources** for an analysis (column `scan_logs.trigger_source` and `analyses.trigger_source`):

- `manual` — user clicked "AI analysis" in the TUI (event detail page key `a`)
- `scan` — initial scoring of a freshly-pasted URL (one-time per event)
- `scheduled` — daemon dispatched at the time the previous analysis requested via its `next_check_at` agent-output field (stored in `scan_logs.scheduled_at`)
- `movement` — significant price movement on a monitored market crossed the daemon's magnitude/quality thresholds

**Scoring** — polily has **two separate scores**, both 0–100, both stored as `structure_score`:

**Per-market `markets.structure_score`** (5 dimensions, weights are market_type-specific; see `_TYPE_WEIGHTS` in `polily/scan/scoring.py`):

1. **Liquidity Structure** — spread + log-scale depth + bid/ask balance
2. **Objective Verifiability** — resolution-source quality (baseline 0)
3. **Probability Space** — symmetric `min(p, 1-p)` linear
4. **Time Structure** — sweet spot [1, 5] days + catalyst proximity
5. **Trading Friction** — pure friction 6-tier
   *(+ **Net Edge** crypto-only bonus dim — `|deviation% − round_trip_friction|`, 0 for non-crypto)*

`markets.score_breakdown` JSON exposes each dimension's contribution plus optional fields: `mispricing_signal` / `mispricing_details` (crypto), `implied_fair_value` (negRisk).

**Event-level `events.structure_score`** is computed independently by `compute_event_quality_score` (see `polily/scan/event_scoring.py`) — **NOT** an aggregate of child markets. Six dimensions:

1. **Information Value** (0–20) — does the event reward research?
2. **Liquidity Aggregate** (0–20) — total depth across child markets
3. **Resolution Quality** — same source quality as per-market dim 2, but at event level
4. **Consistency** — internal consistency of child market prices (negRisk-aware)
5. **Time Window** — same sweet-spot logic at event level
6. **Best Market Quality** — quality of the strongest child market

When narrating, both scores measure **tradability** (whether the market / event is *tradeable*), not **trade quality** (whether you should trade) — never conflate the two.

## 3. Database Schema

The Polily SQLite database lives at the path listed in §5. Use the `Bash` tool with `sqlite3` to query it directly:

    sqlite3 <db_path> "SELECT ... FROM ... WHERE ..."

Compose your own SELECTs as needed — no canned templates here. Below is the schema; column meanings are what you need to write good queries. Column names are exact — match them precisely or your query returns 0 rows.

### Table: `events`

The Polymarket event identified by a slug. One row per event; references one or more `markets` via `markets.event_id` FK.

- `event_id` TEXT PRIMARY KEY (the slug)
- `title` TEXT NOT NULL
- `slug` TEXT
- `description` TEXT
- `resolution_source` TEXT — verbatim Polymarket-provided source URL/text; empty / vague values lower the Objectivity dimension score
- `neg_risk` INTEGER (boolean) — 1 = winner-take-all multi-market event
- `neg_risk_market_id` TEXT — umbrella market id when `neg_risk = 1`
- `market_count` INTEGER
- `start_date`, `end_date` TEXT (ISO 8601)
- `volume`, `liquidity`, `open_interest`, `competitive` REAL
- `tags` TEXT (JSON array)
- `market_type` TEXT — e.g. `crypto / political / sports / economic / default`
- `event_metadata` TEXT (JSON; may contain `context_description` and other notes)
- `structure_score` REAL — event-level 0–100 score (computed by `compute_event_quality_score`; **not** an aggregate of child markets — see §2)
- `tier` TEXT — `A / B / C / D` based on score thresholds
- `user_status` TEXT
- `active`, `closed` INTEGER (booleans)
- `created_at`, `updated_at` TEXT (ISO 8601)

### Table: `markets`

A single tradable outcome under an event. Many real-time-streamed columns (see §4 freshness rules).

**Identity / outcome:**
- `market_id` TEXT PRIMARY KEY
- `event_id` TEXT NOT NULL REFERENCES `events(event_id)`
- `question` TEXT NOT NULL
- `slug`, `description`, `group_item_title`, `group_item_threshold` TEXT
- `outcomes` TEXT (JSON array; default `["Yes","No"]`)
- `condition_id`, `question_id` TEXT — Polymarket on-chain identifiers
- `clob_token_id_yes`, `clob_token_id_no` TEXT — CLOB token IDs

**negRisk:**
- `neg_risk` INTEGER (boolean) — 1 = part of a winner-take-all set
- `neg_risk_request_id`, `neg_risk_other` (INT) TEXT — negRisk auction metadata

**Real-time pricing** (updated every ~30 s by daemon poll):
- `yes_price`, `no_price` REAL
- `best_bid`, `best_ask`, `spread`, `last_trade_price` REAL
- `bid_depth`, `ask_depth` REAL — USD-denominated cumulative depth
- `book_bids`, `book_asks` TEXT (JSON arrays of `[price, size]` levels)
- `recent_trades` TEXT (JSON array)
- `volume`, `liquidity` REAL

**Trading parameters:**
- `order_min_tick_size` REAL
- `accepting_orders` INTEGER (boolean)
- `fees_enabled` INTEGER (boolean) — authoritative gate for taker fee
- `fee_rate` REAL — fee schedule coefficient; NULL when no schedule

**Scoring:**
- `structure_score` REAL — per-market 0–100 (5-dim system; see §2)
- `score_breakdown` TEXT (JSON) — exposes each dimension's contribution; for negRisk events this includes `implied_fair_value`; for crypto markets it includes `mispricing_signal` / `mispricing_details`

**Lifecycle:**
- `resolved_outcome` TEXT NULL — `'yes' | 'no' | 'split' | 'void' | NULL`
- `active`, `closed` INTEGER (booleans)
- `end_date`, `resolution_source` TEXT
- `created_at`, `updated_at` TEXT

### Table: `analyses`

Versioned AI analyses per event. Composite PRIMARY KEY `(event_id, version)`.

- `event_id` TEXT NOT NULL REFERENCES `events(event_id)`
- `version` INTEGER NOT NULL — 1-indexed, monotonically increasing per event
- `created_at` TEXT NOT NULL
- `trigger_source` TEXT — CHECK constraint enforces `'manual' | 'scan' | 'scheduled' | 'movement'`
- `prices_snapshot` TEXT (JSON) — yes/no prices at analysis time
- `narrative_output` TEXT NOT NULL — for `narrative_format='json'` (legacy v0.11.x): JSON-encoded NarrativeWriterOutput dict. For `narrative_format='markdown'` (v0.12.0+): full raw markdown including YAML frontmatter at top
- `narrative_format` TEXT — `'json' | 'markdown'` (added in v0.12.0)
- `structure_score` REAL NULLABLE — score snapshot at analysis time
- `score_breakdown` TEXT NULLABLE (JSON)
- `mispricing_signal` TEXT — `'none'` or other categorical labels
- `mispricing_details` TEXT NULLABLE
- `elapsed_seconds` REAL — claude CLI total elapsed for this analysis

### Table: `scan_logs`

Per-event analysis dispatch ledger — unified lifecycle for manual / scheduled / movement triggers. **Every analysis run has a corresponding scan_logs row** that gates persistence (atomic `finish_scan` claim).

- `scan_id` TEXT PRIMARY KEY
- `type` TEXT — CHECK `'scan' | 'analyze' | 'add_event'`
- `event_id` TEXT
- `market_title` TEXT
- `started_at`, `finished_at` TEXT (ISO 8601 UTC)
- `total_elapsed` REAL
- `status` TEXT — CHECK `'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'superseded'`
- `error` TEXT NULL — failure message when `status='failed'`
- `total_markets`, `research_count`, `watchlist_count`, `filtered_count` INTEGER
- `steps` TEXT (JSON) — per-step trace
- **`scheduled_at` TEXT NULL** — UTC ISO 8601 of when this scan was scheduled to run. **Naming note:** the agent's output field is called `next_check_at` (in YAML frontmatter) but it lands here as `scheduled_at` — same semantic, different name at the storage boundary
- `trigger_source` TEXT — CHECK `'manual' | 'scan' | 'scheduled' | 'movement'`
- `scheduled_reason` TEXT — context for the schedule (mirrors agent's `next_check_reason` field)

### Table: `movement_log`

Per-tick movement records. One row per significant price tick on a monitored market.

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `event_id` TEXT NOT NULL, `market_id` TEXT
- `created_at` TEXT NOT NULL (ISO 8601)
- `yes_price`, `no_price`, `prev_yes_price` REAL
- `trade_volume`, `bid_depth`, `ask_depth`, `spread` REAL
- `magnitude` REAL — movement size signal
- `quality` REAL — movement quality / confidence
- `label` TEXT — CHECK `'consensus' | 'whale_move' | 'slow_build' | 'noise'`
- `triggered_analysis` INTEGER (boolean) — whether this row spawned an AI analysis
- `snapshot` TEXT (JSON) — full pricing snapshot at the tick

### Table: `event_monitors`

Per-event user-intent flag (scheduling moved to `scan_logs` in v0.7.0).

- `event_id` TEXT PRIMARY KEY REFERENCES `events(event_id)`
- `auto_monitor` INTEGER (boolean) — 1 = user wants polily to keep polling
- `price_snapshot` TEXT (JSON)
- `notes` TEXT
- `updated_at` TEXT NOT NULL

### Table: `positions`

Aggregated paper-trading holdings — one row per `(market_id, side)`. Composite PRIMARY KEY `(market_id, side)`. PositionManager is the sole writer.

- `market_id` TEXT NOT NULL REFERENCES `markets(market_id)`
- `side` TEXT — CHECK `'yes' | 'no'`
- `event_id` TEXT NOT NULL REFERENCES `events(event_id)`
- **`shares` REAL NOT NULL** — quantity of YES or NO shares held (column name is `shares`, not `quantity`)
- `avg_cost` REAL NOT NULL — weighted-average entry price
- `cost_basis` REAL NOT NULL — `= shares × avg_cost` (kept in sync by PositionManager)
- `realized_pnl` REAL — cumulative realized P&L on partial closes
- `title` TEXT NOT NULL — denormalized market title (snapshot for display)
- `opened_at`, `updated_at` TEXT NOT NULL

### Table: `wallet`

Singleton paper-trading cash account. `id INTEGER PRIMARY KEY CHECK(id = 1)` enforces single-row.

- `id` INTEGER — always 1
- **`cash_usd` REAL NOT NULL** — current cash balance (column name is `cash_usd`, not `cash_balance`)
- `starting_balance` REAL NOT NULL
- `topup_total`, `withdraw_total` REAL — running totals from ledger
- `created_at`, `updated_at` TEXT NOT NULL

### Table: `wallet_transactions`

Append-only paper-trading ledger. INTEGER PRIMARY KEY AUTOINCREMENT. **`market_id` and `event_id` are stored WITHOUT FK constraints** — the ledger must survive market soft-close.

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `created_at` TEXT NOT NULL
- **`type` TEXT** — CHECK `'TOPUP' | 'WITHDRAW' | 'BUY' | 'SELL' | 'RESOLVE' | 'FEE' | 'MIGRATION'` (column name is `type`, not `tx_type`)
- `market_id`, `event_id` TEXT NULL
- `side` TEXT NULL — CHECK `'yes' | 'no'`
- `shares`, `price` REAL NULL
- **`amount_usd` REAL NOT NULL** — sign convention: positive = cash IN to wallet, negative = cash OUT (column name is `amount_usd`, not `amount`)
- `fee_usd` REAL NOT NULL DEFAULT 0
- `balance_after` REAL NOT NULL — wallet cash after this tx
- `realized_pnl` REAL NULL — set on `SELL` / `RESOLVE`; null on `TOPUP / WITHDRAW / FEE / MIGRATION`
- `notes` TEXT NULL

### Table: `config`

DB-canonical config storage. Flat `key_path → JSON-encoded value`. Writes go through `polily.core.config_store.upsert(db, key_path, value)` which validates against `PolilyConfig` before insert.

- `key_path` TEXT PRIMARY KEY — dotted path (e.g. `wallet.starting_balance`, `active_strategy`, `movement.magnitude_threshold`)
- `value` TEXT NOT NULL — JSON-encoded; decode via `json.loads(value)` (a string knob like `active_strategy='official'` is stored as `"official"` literally, including the quotes)
- `updated_at` TEXT NOT NULL

### Table: `user_prefs`

Lightweight key-value store for runtime UI preferences (separate from `config` — these are not Pydantic-validated).

- `key` TEXT PRIMARY KEY — e.g. `language` (TUI F2 toggle persists here)
- `value` TEXT NOT NULL — raw string (no JSON encoding)
- `updated_at` TEXT NOT NULL

### Table: `user_strategy`

Single-row table holding the user's custom analysis strategy (v0.12.0+). `id INTEGER PRIMARY KEY CHECK(id = 1)` enforces single-slot.

- `id` INTEGER — always 1
- `text` TEXT NOT NULL — full markdown body of the user's strategy (may be `''` empty when user hasn't authored one)
- `updated_at` TEXT NOT NULL

## 4. Data Freshness

Polily exposes data with four distinct freshness profiles. Knowing which is which prevents you from over-trusting a stale value or wasting time re-querying a fresh stream.

### Bucket 1 — Real-time stream (≤ 30 s old)

Updated by the global poll job every 30 s on every **monitored** market (`event_monitors.auto_monitor = 1`). Stream columns on `markets`:

- Pricing: `yes_price`, `no_price`, `best_bid`, `best_ask`, `spread`, `last_trade_price`
- Depth / book: `bid_depth`, `ask_depth`, `book_bids` (JSON), `book_asks` (JSON), `recent_trades` (JSON)
- Volume: `volume`
- Timestamp: `updated_at` (ISO 8601 UTC — this is the actual column, **not** `last_updated`)

If you query the same row 5 seconds apart you may see different values; that is correct, not a race condition. Use a timestamp-anchored reference when narrating: *"at 20:51:25, BTC-30k YES sat at 0.42"*. Treat in-window drift as a narrative input (*"during my analysis YES drifted +14 bps over 2 min, reflecting moderate buying pressure"*) — never as a database race or a polily bug.

**Unmonitored events are not in this bucket.** Their pricing columns reflect whatever was last fetched (scan time or last `auto_monitor=1` window). If `event_monitors.auto_monitor = 0` for an event, every "live" price you see may be hours old.

### Bucket 2 — Periodic computed (≤ 30 s lag for monitored events; static for unmonitored)

Recomputed by `polily/daemon/score_refresh.py` each poll cycle, **but only for events with `event_monitors.auto_monitor = 1`**. Columns:

- `markets.structure_score` — per-market 0–100 score
- `markets.score_breakdown` — JSON exposing per-dimension contributions plus optional `implied_fair_value` (negRisk events) and `mispricing_signal` / `mispricing_details` (crypto markets, derived from Binance underlying via `polily.scan.mispricing`)
- `events.structure_score` — event-level 6-dim aggregate (recomputed when child market scores change)

**Caveat:** `events.score_breakdown` does **not** exist as a column — score_breakdown JSON only lives on `markets` and on `analyses` (snapshot at analysis time). If you need event-level dimension breakdown, query the constituent markets and aggregate yourself.

For unmonitored events, these computed values are frozen at the moment the event was last scanned (or last had monitoring enabled). Don't trust the freshness without checking `markets.updated_at` against the current time.

### Bucket 3 — External / fresh at analysis time

What you can fetch live during this analysis run via your tools:

- **`WebSearch`** — live web pages (polls, news, betting odds aggregators, on-chain block explorers)
- **`Bash`** — anything: `curl https://...` to hit external APIs directly (Polymarket Gamma, sportsbook APIs, oracle feeds), `sqlite3 <db>` to query polily's DB, etc.
- **`Read`** — local file system

Cost is non-trivial — `WebSearch` and `Bash curl` add seconds per call. Use them when the question genuinely needs live data, not by default.

**What you cannot call directly:**

- Binance / ccxt for crypto vol underlying — that runs in `polily.scan.mispricing` at scan time and `daemon/score_refresh.py` per poll for monitored events; results land in `markets.score_breakdown.mispricing_signal`. If you want fresh BTC/ETH spot, shell out via `Bash` (`curl https://api.binance.com/...`).
- Sub-agent dispatch — there is no `Task` tool; you are a single claude session.

### Bucket 4 — Static (set once, doesn't change)

- `events.event_metadata` (JSON; may include `context_description`)
- `events.tags`, `events.market_type`, `events.resolution_source`
- `events.start_date`, `events.end_date`
- DB schema itself (column names, CHECK constraints) — see §3
- Polily mechanics — see §2
- Pre-existing rows in `analyses` (immutable history; new rows append per analysis)

When you observe a value changing across two reads in the same analysis, it is bucket 1 or 2 — not bucket 4, not a bug. Mention the timestamps in your narrative if it materially affected your reasoning.

## 5. File Paths

The canonical path resolver is `polily/core/paths.py`. Three-layer resolution (highest priority first):

1. **CLI flag** — `polily --data-dir=PATH` sets a process-scoped override
2. **Env vars** — `POLILY_DATA_DIR` (data root) and `POLILY_LOG_DIR` (logs only — escape hatch when you want logs elsewhere)
3. **Default** — `platformdirs.user_data_dir("polily")`:
   - **macOS**: `~/Library/Application Support/polily/`
   - **Linux**: `$XDG_DATA_HOME/polily` or `~/.local/share/polily/`

If `POLILY_LOG_DIR` is unset, `log_dir()` defaults to `data_dir() / "logs"` — so a single `POLILY_DATA_DIR` covers both.

### Inside `data_dir()`

| Path | Purpose |
|---|---|
| `polily.db` | Primary SQLite database — every table in §3 lives here |
| `config.yaml` | **Read-only** snapshot of the `config` table, regenerated on every polily startup. Manual edits are silently overwritten — the canonical source is the `config` table (§3). Pre-v0.11.0 had a writable yaml at `$CWD/config.yaml` — that path is **legacy** and only used during one-time migration |
| `logs/` | Daemon + agent log files (see below) |

### Inside `log_dir()` (default `data_dir() / logs/`)

| File | Producer | Use |
|---|---|---|
| `agent_feedback.log` | `narrative_writer._write_dev_feedback` | Append-only log of agent `dev_feedback` strings (one line per successful analysis). |
| `agent_debug.log` | `BaseAgent` (claude CLI wrapper) | stdout/stderr dump from claude CLI subprocess, captured on retry / parse failures |
| `daemon-stderr.log`, `daemon-stdout.log` | launchd / `polily scheduler run` | Daemon process output — covers poll cycles, score refresh, scan dispatches |
| `scheduler-stderr.log`, `scheduler-stdout.log` | APScheduler internal | Scheduler-level diagnostics (job dispatch, missed runs) |

### Quick reference

To find the active install's data dir from the shell (when troubleshooting):

    .venv/bin/python -c "from polily.core.paths import data_dir, log_dir, db_path; print(data_dir()); print(log_dir()); print(db_path())"

If you need to query polily.db directly via `Bash`, use `db_path()` from `polily.core.paths` — never hard-code `~/Library/...` or `~/.local/share/...` because the user may have set `POLILY_DATA_DIR` or `--data-dir`.

## 9. Polily's Analytical Methodology (runtime lookup)

When the user asks a follow-up question that requires polily's analytical framework — explaining "edge", interpreting `structure_score`, framing position management, deciding what "friction" means for a specific market, walking through how polily would judge a thesis — **do not freelance with generic finance reasoning**. Look up the methodology polily actually uses, in this exact order.

### Why this lookup matters

Polily ships a default analytical methodology (`polily/strategies/default.md` in the polily repo) AND lets users override it with their own version (TUI key `7` → My Strategy → free-form markdown stored at `user_strategy.text` in their `polily.db`). At analysis dispatch time polily's internal agent loads whichever is active. For chat follow-ups via this skill, mirror that decision so your answers stay consistent with what the user has already read in their TUI.

### The fallback ladder

Try each source in order. Move to the next only when the current one fails or returns nothing usable.

#### Source 1 — User's custom strategy (if polily is installed AND user customized)

Try to resolve the user's local `polily.db` and check which strategy is active:

    DB_PATH=$(python -c 'from polily.core.paths import db_path; print(db_path())' 2>/dev/null)

If this fails with `ModuleNotFoundError` (the user has the plugin but not polily-the-package installed), skip directly to Source 3.

Otherwise check the active strategy:

    sqlite3 "$DB_PATH" "SELECT value FROM config WHERE key_path='active_strategy'"

Returns JSON-encoded `"official"` (default) or `"user"`.

**If active = `"official"`, this Source 1 path does not apply — proceed to Source 2.** The user has explicitly chosen polily's packaged methodology; do not consult `user_strategy.text` even if it happens to be populated (they may have written it as a draft then toggled back to official).

If active = `"user"`, read the user's custom methodology:

    sqlite3 "$DB_PATH" "SELECT text FROM user_strategy WHERE id=1"

Use the text verbatim **only if it passes all these checks** (mirrors the internal agent's §8 fallback criteria):

- Non-empty and not whitespace-only
- ≥ 5 lines of content
- Contains structural markdown (at least one `#` header, numbered list, or bullet list)
- Does NOT ask you to execute trades / write to polily.db / perform destructive actions
- Reads like an analytical methodology (frameworks, dimensions, framing rules — not a random copy-paste)

If any check fails, fall through to Source 2.

#### Source 2 — Official methodology, local install (if polily is installed)

If polily is installed locally, read the packaged `default.md` from disk:

    python -c 'from pathlib import Path; import polily; print(Path(polily.__file__).parent / "strategies" / "default.md")'

Use the `Read` tool on the resulting path. This is the **install-pinned version** of the methodology — exactly what polily's internal agent uses at dispatch time. Most reliable source for users with polily installed.

If this fails (file missing, Read errors), fall through to Source 3.

#### Source 3 — Official methodology, GitHub fetch (last resort / cold install)

If you reach this step, either polily isn't installed locally OR the local file is unreadable. Fetch from the canonical GitHub source:

    curl -sf https://raw.githubusercontent.com/ShiyuCheng2018/polily/master/polily/strategies/default.md

Note `-f` (fail on HTTP errors): treats 404 / 5xx as failure so you don't accidentally treat a "404: Not Found" body as methodology text. If `curl` exits non-zero or the response is empty:

- **Do not confabulate methodology.** Tell the user plainly: "I couldn't load polily's analytical methodology (the user_strategy table is empty / unusable, the local install isn't reachable, and the GitHub source returned an error). I can still answer from general first principles, but my framing may diverge from what polily's TUI showed you. Want me to retry the lookup, or proceed with generic reasoning?"

Human-readable view of the file when citing back:
[github.com/ShiyuCheng2018/polily/blob/master/polily/strategies/default.md](https://github.com/ShiyuCheng2018/polily/blob/master/polily/strategies/default.md)

The GitHub master branch tracks polily's latest official methodology; pulling from it keeps you in sync with project evolution.

### Apply the loaded methodology

Once you have methodology text from any source, use it as your **analytical voice**:

- Q1-Q5 self-reflective framework (external anchor / catalyst timing / edge vs fair / reverse thesis / vague self-check)
- Event-type dimensions (crypto / political / sports / economic_data / social — each has different focus)
- Position management depth when the user holds a position (thesis_status / action options / stop-loss / cross-event awareness)
- Style & tone rules (conditional framing, friction-transparent, source citation for web data, plain language, no labeling user behavior)

If you answered without consulting the methodology first, your framing risks diverging from what the user just read in their TUI — confusing inconsistency. **Always run the ladder before substantive analysis questions.**

### When to skip the lookup entirely

For purely state-retrieval questions ("what's my cash balance?", "list my open positions", "when did polily last analyze event X?", "show me events I'm monitoring"), the schema in §3 is sufficient — answer directly without loading the methodology. The lookup is only for questions where the user wants polily's **reasoning framework** applied (explain why / interpret a score / frame a decision).
