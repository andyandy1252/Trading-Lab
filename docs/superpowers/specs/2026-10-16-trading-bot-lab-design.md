# Trading Bot Lab — Design Spec
_Version 1.0 · 2026-10-16_

## Purpose

A single-tenant personal trading bot platform for futures (NQ/ES on CME). The owner builds, backtests, paper-trades, and live-trades their own bots first. Once the full lifecycle is validated end-to-end, the platform is productized for non-technical users who follow the same path.

---

## Bot Lifecycle

Every bot moves through these states in order:

```
DRAFT → BACKTESTED → INCUBATING → LIVE → RETIRED
```

A bot can be PAUSED (stops new entries, leaves open position running) or STOPPED (flattens and halts) from LIVE. It can be RETIRED from any state. State transitions are logged and irreversible except PAUSED → LIVE.

| State | What it means |
|---|---|
| DRAFT | Spec created, not yet backtested |
| BACKTESTED | Has a passing backtest result attached |
| INCUBATING | Running on live prices in paper mode, working toward the gate |
| LIVE | Sending real orders to the broker |
| PAUSED | No new entries; open position still managed by exit rules |
| RETIRED | Permanently archived; full history readable, cannot reactivate |

---

## Architecture

**Single-tenant for Phase 1. Platform-grade core from day one.**

```
web/          Next.js dashboard + strategy builder (only web server)
engine/       Python worker — all math, no web API
shared/       Pydantic spec model, JSON Schema, TypeScript types, migrations
```

External services:
- **Supabase** — Postgres, auth, file storage
- **Databento** — historical Parquet data (multi-instrument)
- **Claude API** — English/video/PDF → spec translation only; never execution decisions
- **Broker adapter** — pluggable interface; first implementation TBD
- **Telegram** — alerts + two-way bot control commands
- **MCP server** — exposes trading tools so users can operate the lab from Claude Code, Cursor, ChatGPT, or any MCP client

**Key principle:** Claude is called from Next.js server actions only. The browser never calls the model, the broker, or the engine directly.

---

## Multi-Agent Swarm Architecture

Each bot contains a team of agents plus a deterministic execution core.

```
Scanner agents   ─┐
Filter agents    ─┼──→  Signal consensus  ──→  Execution core  ──→  Broker
Risk agent       ─┘         (rules)              (deterministic)
```

### Agent types

| Type | Role | Can be AI-powered? |
|---|---|---|
| Scanner | Find setups matching the strategy concept | Yes |
| Filter | Confirm or veto based on domain (news, timing, regime, correlation) | Yes |
| Risk | Check contracts, daily loss, drawdown | No — always deterministic math |
| Execution | Place and manage orders per spec rules | No — always deterministic |

**Consensus rule:** A trade only enters when all required agents have responded within the latency window. A timed-out or errored agent drops the signal — it is never treated as a "yes."

**Multi-instrument analysis:** Each bot has one execution instrument (the instrument it trades). Agents may analyze any number of reference instruments and timeframes declared in the bot config (e.g. VIX on 1h to filter NQ entries, ES on daily for regime). The worker pre-loads all declared reference data before running agents. Agents cannot reach outside the declared list — this keeps the backtest reproducible.

**Backtestability rule:** Every AI-powered agent has a deterministic proxy — a rule-based approximation used for historical backtesting. In paper and live mode, the real agent runs and its structured outputs are logged. The agent signal log lets you compare real vs. proxy over time.

---

## Signal Block System

Signal blocks are the building blocks of scanner agents. Each block is a pure function: given a set of closed bars, it reports a structured result or nothing.

### Built-in blocks (v1, hand-coded reference implementations)
- `session_levels` — prior/developing session high, low, midpoint, open
- `liquidity_sweep` — price runs a level and closes back through it
- `fair_value_gap` — three-candle untraded zone (bullish or bearish)

### AI-assisted block creation (multi-modal input)

Non-technical users can define a new signal block by providing any of:
- A YouTube URL (system fetches transcript)
- A PDF upload (course material, strategy guide)
- A chart screenshot with annotations
- Plain English description

**Flow:**
1. User submits input(s)
2. Claude analyzes and proposes a draft block definition: name, parameters, what it detects, what it reports
3. Draft appears as a plain-English block card the user reads
4. User confirms ("Yes, that's the setup") or corrects ("Measure wick-to-wick, not body-to-body")
5. Claude revises until confirmed
6. Block is saved, versioned, and available for use in any bot spec

This is the primary path for non-technical users to add new strategy concepts without writing code.

---

## Custom Indicators Library

Indicators are first-class objects, defined once and reusable across any number of bots. A custom indicator is a named, versioned computation that takes bar data (and optionally reference instrument data) and returns a scalar or series. It is not a signal block — it does not detect a pattern. It is a building block that signal blocks and agents can consume.

### Examples
- "NY session high as of 10:00 AM" — a time-bounded session level
- "NQ 20-period EMA minus ES 20-period EMA" — cross-instrument spread
- "ATR-normalized candle body size" — volatility-adjusted measurement

### Definition flow
1. User describes the indicator in plain English (or uploads a PDF/video showing it)
2. Claude proposes a definition: name, inputs (timeframe, instrument, parameters), output type (scalar / series), formula in plain English
3. User confirms or corrects
4. Indicator is saved, versioned, and appears in the indicator library
5. Any signal block or agent can reference it by name

### Storage
Each indicator has its own row in `indicators` table: name, version, definition JSONB (formula, inputs, output type), ai_model_version, created_at. The library is shared across all bots owned by the user.

---

## Strategy Marketplace

A public library of strategies and indicators that any user can browse, fork, and build on. Solves the blank-page problem — new users start from a working example rather than nothing.

### What is published
- Strategy name and plain-English description
- Backtest summary metrics (trade count, win rate, profit factor, Sharpe, max drawdown, date range tested)
- The signal blocks and agents used (names only — not the exact parameters unless the author chooses to share)
- Whether it is futures / stocks / crypto (we are futures-only, but the field exists for the platform version)
- Author handle (optional anonymous)

### What is never published
- Exact entry/exit parameters, stop offsets, or timing windows (competitive edge stays private by default)
- Live or paper trading results from the author's real account
- Broker credentials or account details of any kind

### Fork flow
1. User finds a strategy in the marketplace
2. Clicks "Fork" — creates a new DRAFT bot in their account with the public fields pre-filled
3. They fill in or adjust the private fields (parameters, risk limits, costs) before backtest runs
4. Forked bot is entirely theirs; no link back to original after fork

### Tables
`marketplace_listings` — strategy_id (optional, if author links their bot), title, description, metrics_snapshot JSONB, blocks_used JSONB (names only), published_at, fork_count

---

## MCP Server Layer

Exposes the lab's trading tools as MCP endpoints so users can operate the full workflow from Claude Code, Cursor, ChatGPT, Gemini, or any MCP-compatible client. This IS the "one workspace" experience — users never have to leave the AI they already work in.

### How it works
The MCP server sits in front of the web layer. It authenticates via the user's API key (generated in the dashboard). Each tool call hits a Next.js API route internally and returns a structured result. The AI client renders the result — either as plain text or, in clients that support it, as a rich interactive card.

### MCP tools (v1)

| Tool | What it does |
|---|---|
| `research_market` | Pull quotes, bar data, or key metrics for any supported instrument |
| `get_chart` | Return OHLCV data for a symbol + timeframe, optionally with indicator overlays |
| `build_strategy` | Translate a plain-English description into a draft strategy spec |
| `run_backtest` | Queue a backtest for a named bot config; return job ID |
| `get_backtest_result` | Return the full result for a completed backtest job |
| `list_bots` | Return all bots with their current state and today's PnL |
| `get_bot_status` | Return full detail for one bot: state, open position, last signal |
| `deploy_to_paper` | Promote a BACKTESTED bot to INCUBATING (paper mode) |
| `preview_order` | Show an order ticket with quantity, type, price, and risk — nothing submits |
| `get_portfolio` | Return open positions, today's PnL, and account balance |
| `get_event_log` | Return the execution event log for a bot: signals, orders, fills, risk checks |
| `pause_bot` | Pause a LIVE bot (same as Telegram `/pause`) |
| `stop_bot` | Stop and flatten a LIVE bot |
| `kill_bot` | Emergency kill with slippage + lock |

### Interactive result cards
For clients that support MCP UI extensions (Claude Desktop, some Cursor builds), each tool returns a structured card schema alongside the text response. Card types: `chart_card`, `backtest_card`, `order_preview_card`, `positions_card`, `event_log_card`, `bot_status_card`. Clients that don't support cards get the same data as formatted text.

### Auth
API key generated per user in the dashboard. Key is scoped to read-only or read-write. `preview_order` and any destructive action require read-write scope. Key can be revoked instantly from the dashboard.

---

## Strategy Spec Requirements

A bot spec is rejected by the engine and the web app if any required field is missing. Required fields:

- [ ] Name (unique, human-readable)
- [ ] Execution instrument (NQ / MNQ / ES / MES)
- [ ] Reference instruments list (can be empty)
- [ ] Signal timeframe
- [ ] Fill resolution (1s goal; 1m allowed)
- [ ] Session definition (name, timezone, start, end, weekdays)
- [ ] Entry rule: side (long or short, explicit — never inferred), trigger conditions, order type, price reference if limit/stop, expiry in bars
- [ ] Exit rule: stop (reference + offset in ticks, must be on protective side), target (R:R ratio), time stop
- [ ] Risk: contracts, max trades per session, daily loss stop in USD
- [ ] Costs: commission per side USD, market slippage ticks, limit-through ticks
- [ ] Agent roster: which agents are active, their parameters, consensus rule
- [ ] AI model version that generated the spec
- [ ] spec_version field
- [ ] Asset class (futures)
- [ ] Execution latency class (real-time / near-real-time / batch)

---

## Backtest Requirements

A backtest result is accepted only if it includes all of:

- [ ] Total trades ≥ 100
- [ ] Out-of-sample trades ≥ 30
- [ ] Win rate
- [ ] Profit factor
- [ ] Maximum drawdown (USD and %)
- [ ] Sharpe ratio (annualized)
- [ ] Deflated Sharpe (corrects for batch selection — penalizes picking the best from a large pool)
- [ ] Commission and slippage paid (totals, not zero)
- [ ] In-sample and out-of-sample date ranges (both recorded)
- [ ] Full equity curve
- [ ] Worst consecutive loss streak
- [ ] Data source and date range

If the spec is modified after a backtest, the result is invalidated. The bot reverts to DRAFT and must rerun.

---

## Guards & Gates

| Gate | Rule |
|---|---|
| Spec gate | All required fields present and valid before backtest runs |
| Backtest quality gate | Meets minimum trade counts and required metrics |
| Spec lock | Modifying spec after backtest invalidates the result |
| Incubation gate | ≥ 5 trading days AND ≥ 20 paper trades before LIVE promotion |
| Incubation override | Allowed with a single logged confirmation; kill switch stays on |
| Notification gate | Telegram channel must be verified before LIVE |
| Kill switch | Daily loss limit set at promotion; can only be lowered while running; trips → flatten + block + alert |
| Agent consensus | All required agents must respond within latency window; timeout = drop signal |
| Audit immutability | Audit log is append-only at DB level; no application code can update or delete |

---

## Dashboard Management Actions

Every deployed bot supports:

- **Start** — begin taking signals on the next session open
- **Pause** — stop new entries; open position runs to its exit rules
- **Stop** — flatten open position at market; bot transitions to PAUSED state (no open position, no new entries)
- **Kill** — emergency flatten with slippage; lock bot from restarting without confirmation
- **Switch to paper** — move to paper execution without changing the spec
- **Switch to alerts-only** — generate signals, log them, do not send orders
- **View equity curve** — real-time PnL, drawdown, fill log
- **Compare to backtest** — live curve vs. backtest projection; divergence triggers alert
- **Tighten daily loss limit** — can be tightened any time; cannot be raised
- **View audit log** — every order, fill price, slippage, commission, agent signals
- **Retire** — archive permanently; history stays readable
- **Notification channel management** — add/remove/test Telegram without stopping bot

**Portfolio view:** All bots visible simultaneously with status, today's PnL, state. Shared daily loss ceiling across all live bots.

**Telegram two-way commands:** `/pause {bot-name}`, `/stop {bot-name}`, `/status`, `/pnl`, `/kill {bot-name}`

---

## Data Model

### Core tables

**`bots`** — one row per bot; name, state, created_at

**`bot_configs`** — versioned; every save is a new row. Fields: bot_id, version, parent_version, spec JSONB, agent roster JSONB, ai_model_version, reference_instruments JSONB

**`backtest_jobs`** — job queue. Fields: bot_config_id, status (queued/running/done/dead), attempts (max 3), claimed_at, error

**`backtest_results`** — written by worker. Fields: job_id, all required metrics, equity curve JSONB, in-sample/out-of-sample dates, data source

**`trades`** — all modes (backtest/paper/live) in one table. Fields: bot_id, mode, entry/exit times and prices, fill prices, slippage ticks, commission USD, PnL, exit reason, agent_signals JSONB

**`agent_signal_log`** — append-only. Fields: bot_id, bar_time, agent_name, agent_type, structured output JSONB, latency_ms

**`audit_log`** — immutable. Fields: bot_id, trade_id, timestamp, event_type, details JSONB. No updates, no deletes.

### Supporting tables

**`incubation_progress`** — paper trade count, trading days elapsed, gate_met_at, backtest_result_id (for divergence)

**`live_deployments`** — daily_loss_limit_usd (locked at promotion), position_size_cap, broker_adapter, encrypted broker credentials, confirmation_logged_at

**`notification_channels`** — bot_id, type (telegram), config JSONB, verified_at

**`daily_loss_checks`** — bot_id, date, realized + open-mark PnL, limit, tripped_at

**`indicators`** — name, version, parent_version, definition JSONB (formula, inputs, output type), ai_model_version, created_at. Shared library across all user bots.

**`marketplace_listings`** — title, description, metrics_snapshot JSONB, blocks_used JSONB (names only), published_at, fork_count. No private parameters stored.

**`api_keys`** — user_id, key_hash (never store plaintext), scope (read / read-write), created_at, revoked_at. Powers MCP server authentication.

---

## Build Order

### Phase 1 — Foundation
1. **Pydantic spec model** — all required fields, cross-field validation (stop on correct side, etc.), JSON Schema + TypeScript generation, fixture tests for every rejection case
2. **Database schema** — all tables, migrations in `shared/spec/migrations/`
3. **Env module** — refuses to boot if any required key is missing

### Phase 2 — Engine
4. **Signal block interface** — abstract base every block implements; fixture test harness
5. **Built-in signal blocks** — `session_levels`, `liquidity_sweep`, `fair_value_gap`; fixture tests from labeled chart examples
6. **Fill simulator** — pessimistic fills, slippage, commission, stop gap-fill rule
7. **Backtest runner** — multi-instrument data load, bar iteration, agent proxy hooks, result write-back
8. **Job worker** — SKIP LOCKED claim, run, retry, dead-letter

### Phase 3 — Agent layer
9. **Agent interface** — abstract base (input schema, output schema, proxy flag, latency class)
10. **Deterministic agents** — timing agent, risk agent (establish the pattern)
11. **AI-powered agents** — market scanner, news filter (Claude API, log outputs, deterministic proxies)
12. **AI-assisted block creation flow** — multi-modal input (YouTube/PDF/image/text) → draft block card → user confirmation → save
13. **Custom indicators library** — indicator definition, versioning, storage, reference from blocks/agents

### Phase 4 — MCP server
14. **API key auth** — generate, scope, revoke; key_hash stored never plaintext
15. **MCP tool definitions** — all 14 tools from the MCP tools table, wired to internal Next.js API routes
16. **Interactive card schemas** — structured card payloads for clients that support MCP UI extensions
17. **MCP server documentation** — how to connect from Claude Code, Cursor, ChatGPT

### Phase 5 — Live execution
18. **Paper trading runner** — same engine, live price feed
19. **Incubation tracker** — gate logic, divergence check vs. backtest
20. **Broker adapter interface** — abstract layer; first real implementation when broker is chosen
21. **Telegram notifier** — fills, alerts, kill-switch, two-way commands

### Phase 6 — Dashboard
22. **Strategy builder** — chat + file upload interface → Claude → rule card
23. **Backtest viewer** — results, equity curve, metrics display
24. **Bot dashboard** — portfolio view, per-bot controls, audit log, unified event log
25. **Incubation UI + live deployment flow** — gate progress, confirmation, Telegram setup
26. **Marketplace** — browse public strategies, fork to DRAFT, publish your own (metrics only by default)
27. **Indicator library UI** — view, create, edit, and test custom indicators

---

## Decisions

1. **Broker** — Interactive Brokers or Tradovate; TBD based on which is easiest to connect first. Personal bot will be tested with a small live account ($100–$200). Broker adapter is pluggable — decision does not block engine work. Additional brokers (and data vendors like QuantData) will be evaluated as candidates.

2. **Incubation gate** — Default of 5 trading days + 20 paper trades stays. The gate is editable but reducing it requires a prominent warning explaining the risk. The kill switch and size cap stay on regardless.

3. **Daily loss limit** — 10% of the account balance at deployment time. For a $100 account that is $10. The limit is stored as a dollar amount (computed at deployment). It can only be lowered while the bot is running — raising it requires retiring and redeploying.

4. **Market data** — Tick-by-tick 1-second fills via Databento (primary). Cost to be confirmed once data subscriptions are set up. QuantData is a candidate cheaper alternative — user will provide a link for evaluation.

5. **Held-out test data** — Visible to the owner during development of the first bot. Acceptable for personal use; the platform version for other users will lock it by default.

6. **AI model** — Claude Opus 4.8 for strategy translation and signal block creation. More capable; cost and latency are acceptable for the use case.

7. **Divergence alert threshold** — Default: alert when live PnL is more than 30% below the backtest projection over the same number of completed trades. Configurable per bot.
