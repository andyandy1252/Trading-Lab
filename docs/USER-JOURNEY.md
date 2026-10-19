# User Journey — the product we are building toward

> **Purpose:** This is the north star. It describes, in plain English, the full
> experience a paying user has with the software, and why they pay. Every build
> task should visibly serve one of the stages below. If a task does not map to a
> stage here, that is the "are we getting sidetracked?" alarm.
>
> _Last updated: 2026-10-19._

---

## The person and the problem

Our user is a **futures trader** (NQ first, ES next) who has a trading idea but
either can't code, doesn't trust the backtests they see online, or both. Their
only options today are: learn to program, pay a developer, or fool themselves
with a sloppy backtest. This software removes all three problems:

**Describe the idea in plain English, and get an honestly-tested bot you can
trust before risking real money.**

---

## The workflow, stage by stage

### 1. Sign up and set up
The user creates an account (Supabase handles auth and the database). Optionally
they connect their **brokerage read-only** (Tradovate first, TopstepX second) so
the app can later sync their account. Nothing can trade yet.

### 2. Describe the strategy in plain English
The user types their idea, e.g.:

> *"Short NQ after the prior cash-session high gets swept and a bearish fair
> value gap prints. Stop 4 ticks above the sweep, target 2x the risk, only trade
> the New York morning."*

The built-in **AI agent translates that English into a strategy spec** — the
machine-readable recipe. The AI is a **translator, not a trader**: it turns
words into a structured recipe. A **deterministic engine** (same inputs ->
same outputs, every time) does all the actual math later. The user can watch the
AI reason through the translation, so it feels transparent.

### 3. Review the strategy as rule cards — not code
The user never sees raw JSON. The recipe appears as clean **rule cards**:
Entry, Stop, Target, Session, Risk. They read it back in human terms, fix
anything the AI misread, and edit it directly. Every save becomes a new
**version** (each spec is stored with a `parent_version`), so ideas can branch
and be compared without losing earlier ones. This is the human-in-the-loop
checkpoint: the user controls what the bot will actually do.

### 4. Backtest — the honest way
The user hits "Backtest." The web app drops a **job** into a queue; a Python
**worker** picks it up and runs the strategy over **our own licensed historical
data** (stored as fast Parquet files). The test is deliberately pessimistic and
honest:

- **Real costs are on** — commissions and slippage, every trade.
- **Worst-case fills** — if one bar could have hit both the stop and the target,
  it assumes the stop (the losing one).
- **Walk-forward testing** — train on older history, test on a later stretch the
  strategy never saw, rolling forward.
- **A locked holdout** — the most recent 6 months are sealed; no tuning ever
  peeks at them. The final honesty exam.

The user can **replay the trades bar by bar** on a chart ("Bar Replay") to see
where and why the bot entered and exited — our data, our charts.

### 5. Read the verdict — the Trust Score
Instead of a vanity "+400%!" number, the user gets a **Trust Score from 0-100**,
built from three honest questions:
1. Does it still work on data it never saw?
2. Does it survive small tweaks to its settings (or was it a fragile fluke)?
3. Does it survive real fees?

A score requires **at least 100 trades on unseen data** — no scoring off three
lucky wins. Batches of variations are ranked by a statistic (**Deflated Sharpe**)
that punishes "we tried 500 combos and cherry-picked the best." A **Monte Carlo**
check reshuffles the same trades to show a realistic worse drawdown. **This
believable number is the core thing users pay for.**

### 6. Iterate
The user tweaks the rule cards, tries different sessions or market conditions
("regime selection"), re-tests, and compares versions side by side — all in
plain English, all honestly scored.

### 7. Paper trade (the default)
When a strategy earns trust, the user deploys it to **paper trading** (simulated
money) — the default, not an afterthought. The key guarantee: the paper bot runs
the **exact same Python code** as the backtest (this is **parity**), so what they
tested is literally what runs. No bait-and-switch.

### 8. Go live — with guardrails
Only after paper trading does live unlock, and the design deliberately slows the
user down for their own good:
- A **recommended wait** of 5 trading days and 20 completed paper trades. Going
  sooner shows a warning and needs one logged confirmation.
- Even after skipping, a **daily-loss kill switch** and a **micro-contract size
  cap** stay on.
- **Full position size stays locked** until live results track the backtest.

Live orders route through the user's own broker. (Live routing waits for a legal
review.)

### 9. Live, ongoing
The user monitors the bot: live trades vs. what the backtest predicted, a
"deploy review" before each change goes live, and later a **strategy marketplace**
to share or sell proven strategies, plus **custom indicators** for power users.

---

## Why a user pays a subscription

Four things nobody gets in one place:

1. **No code required.** "Describe it in English, get a working bot." The hook
   for the huge population of futures traders who can't program. **This is the
   single most important piece** — everyone else makes bot-building look
   impossibly technical; we make it a sentence of English.
2. **A backtest they can actually trust.** Everyone else shows rosy, easily-faked
   results. We show a **Trust Score built to try to disprove the strategy** —
   unseen data, fees on, locked holdout, 100-trade minimum. This is the product's
   soul, and it is what protects their money.
3. **What you test is what you trade.** Backtest, paper, and live all run the
   **same engine**, so the promising backtest isn't a lie that falls apart live.
4. **Guardrails that keep them from blowing up.** The forced paper period, kill
   switch, and size caps are the product quietly acting in the user's interest —
   the opposite of the "turn it on and pray" bots they've been burned by.

**In one sentence:** they pay because it turns a plain-English idea into a bot
that's been honestly stress-tested and safely walked from backtest -> paper ->
live — without ever writing code, and without fooling themselves.

---

## What is real today vs. the destination

Everything above is the **destination** the architecture describes. As of
2026-10-19, only the **foundation** is built: the spec model that validates the
recipe (the contract under Stage 3). The AI translator (Stage 2), the data
pipeline and backtest engine (Stage 4), the Trust Score (Stage 5), and paper/live
(Stages 7-8) are **designed but not yet built.** That is normal and on-path.

**Strategy coverage:** the ICT family (fair value gap, liquidity sweep, session
levels) is **language pack #1** — the first of many futures strategy families.
The engine is built around generic building **blocks**, so new families are added
later as new block types + glossary entries, not rewrites. We master ICT
end-to-end first, then widen.

---

## How to use this document

Before starting any task, ask: **which stage above does this serve?** The
critical path to the product's soul is Stage 2 (English -> spec) and Stage 4
(spec -> real executing engine). Build those until a plain-English ICT idea can
be turned into a spec and honestly backtested end-to-end. Then widen the strategy
knowledge base and build the web experience on top.
