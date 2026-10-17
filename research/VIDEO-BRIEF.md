# Trading Bot Video Research Brief

> Context: Futures trading bot lab (NQ/ES on CME). Goal: build owner's personal bot first, then productize for non-technical users. Stack: Next.js + Python engine + Supabase + Databento data. No broker chosen yet.

---

## Per-Video Analysis

**Video 1 — how to actually build an ai trading bot (full guide)**
- URL: https://youtu.be/PBBSMSyU674
- Claim: An AI trading bot built right can generate $8,000/week, but the common failure is building one wrong — the guide claims to show the correct process using Claude and TradingView MCP.
- Stage: build
- Rule we could enforce: Bot must go through a defined build checklist (strategy → backtest → paper → live) before any live capital is deployed.
- What it never specifies: What "building wrong" actually means in measurable terms; no minimum performance threshold before going live; no mention of slippage or commission in backtests.
- Lookahead / cheating risk: Income claims ($8K/week) are unverified and based on cherry-picked periods. No discussion of out-of-sample validation.

---

**Video 2 — How To Actually Find A Profitable Strategy With Claude**
- URL: https://youtu.be/Fb7G5SNpaes
- Claim: Claude can systematically find profitable trading strategies by researching ideas, running backtests, and presenting results — removing the need to manually invent strategies.
- Stage: find
- Rule we could enforce: Every strategy idea must pass a backtest with a minimum number of trades (e.g., 100) and a minimum Sharpe ratio before the bot can be built from it.
- What it never specifies: What data source the backtest uses; whether the strategy is tested on unseen data; no slippage or commission parameters specified.
- Lookahead / cheating risk: Backtests are run and the best one selected, which is classic in-sample curve-fitting. No walk-forward or out-of-sample stage shown.

---

**Video 3 — Jev + Claude Opus 5.5 = The Most Powerful AI Trading Bot Ever**
- URL: https://youtu.be/Pk7W7BKMwqo
- Claim: A specialized fast-execution system called "Jev" (400ms decision time) paired with Claude Opus for strategy reasoning outperforms using Claude alone (5-second latency) for live execution.
- Stage: build
- Rule we could enforce: The bot spec must declare its execution latency class (real-time <1s, near-real-time 1–10s, or batch). The lab enforces that the backtest fill assumption matches the latency class.
- What it never specifies: What Jev actually is or how it makes decisions; no backtest shown; no risk parameters for the combined system.
- Lookahead / cheating risk: No backtest shown at all — pure demonstration of live speed, with no statistical evidence of profitability.

---

**Video 4 — Complete Guide to building an AI Trading Bot with Claude for Beginners**
- URL: https://youtu.be/oQdkFPhqaGk
- Claim: Non-technical users can describe a strategy in plain English, and Claude will generate a working trading bot that executes trades automatically.
- Stage: build
- Rule we could enforce: The strategy description submitted in English must produce a structured spec (instrument, entry rules, exit rules, risk limits) before any code is generated.
- What it never specifies: How the bot actually places orders; which broker API is used; no mention of testing or validation before going live; no position sizing rules.
- Lookahead / cheating risk: No backtesting or paper trading stage shown. Goes from English description directly to live bot.

---

**Video 5 — Claude + Telegram = The Most Insane AI Trading Bot Yet**
- URL: https://youtu.be/DMYQlk9ybj0
- Claim: Integrating Claude with Telegram creates a conversational interface for controlling and monitoring a trading bot in real time from any device.
- Stage: manage
- Rule we could enforce: Every deployed bot must have at least one notification channel configured (e.g., Telegram) before it is allowed to trade live.
- What it never specifies: What commands are available via Telegram; whether Telegram messages can trigger trades directly (and the security risk that implies); no mention of what happens if Telegram is unavailable.
- Lookahead / cheating risk: None identified — this is a management/notification layer, not a strategy or backtest.

---

**Video 6 — 3 free Github repos to print $$$ AI trading**
- URL: https://youtu.be/Z3CUdMYXZm8
- Claim: Three free public GitHub repositories give non-technical users ready-made AI trading infrastructure they can deploy without building from scratch.
- Stage: find / build
- Rule we could enforce: Any external repo used as a bot foundation must be pinned to a specific commit hash and the license recorded in the bot's spec before it is deployed.
- What it never specifies: What the repos actually do (no repo names/links visible from description); whether the repos include backtesting; no performance evidence for any of them.
- Lookahead / cheating risk: Repos of unknown provenance may contain backtests with lookahead bias baked in. Cannot assess without seeing the code.

---

**Video 7 — 7 Free GitHub Repos That Turn Claude Into a $500K Quant Trader**
- URL: https://youtu.be/me5uegV7vOU
- Claim: Seven curated free GitHub repositories, when combined with Claude, replicate the infrastructure of a quantitative trading operation without a quant background.
- Stage: find / build
- Rule we could enforce: Same as Video 6 — external repos must be pinned and licensed. Additionally, any "quantitative" claim must be backed by a minimum out-of-sample trade count before the lab accepts the bot.
- What it never specifies: Whether any of the repos has been independently verified; no discussion of data quality; $500K claim is unverified.
- Lookahead / cheating risk: "$500K quant trader" framing is marketing, not a tested result. No out-of-sample evidence shown.

---

**Video 8 — How I'd Learn AI Trading From Scratch In 2026**
- URL: https://youtu.be/QOkSn0csQRE
- Claim: There is an optimal learning sequence for AI trading that prevents beginners from wasting time and money — starting with understanding markets before touching AI tools.
- Stage: find
- Rule we could enforce: Before a user's first bot can be created, they must complete a one-time onboarding checklist: instrument chosen, session hours understood, risk capital ceiling set.
- What it never specifies: What "understanding markets" means in a measurable gate; no specific timeline or milestones; transcript unavailable, inferred from title and channel context.
- Lookahead / cheating risk: None identified — this is an educational/onboarding video.

---

**Video 9 — TradingView's MCP + Claude OPUS 5.5 = King of AI Trading**
- URL: https://youtu.be/CttOQO-UuEk
- Claim: TradingView's official MCP server combined with Claude Opus 5.5 gives Claude direct access to chart data, indicators, and Pine Script execution — making it the most capable AI trading setup currently available.
- Stage: build
- Rule we could enforce: If the bot uses an MCP server to write Pine Script, the generated script must be version-controlled and the exact version used in each backtest must be recorded in the bot's audit log.
- What it never specifies: Whether the MCP server exposes future data during backtesting (a serious lookahead risk); no performance numbers shown; no risk parameters.
- Lookahead / cheating risk: MCP access to TradingView chart data during strategy generation could expose the AI to future prices if not carefully sandboxed. This is a structural lookahead risk that the video does not address.

---

**Video 10 — I Gave My AI Trading Bot $100 for 22 Hours… Here's What Happened**
- URL: https://youtu.be/QZcA8eyOQwg
- Claim: An AI bot can find, backtest, and execute strategies in a live $100 account over 22 hours — and the process of filtering 1,667 candidate strategies down to 5 produces a viable live bot.
- Stage: test / deploy / manage
- Rule we could enforce: The lab must require that any strategy selected from a batch of N candidates passes a statistical significance correction (e.g., Bonferroni or Deflated Sharpe) — selecting the top 5 from 1,667 without correction is p-hacking.
- What it never specifies: Whether the top 5 strategies were tested on held-out data before live trading; what the statistical significance threshold was; no slippage or commission shown in backtests.
- Lookahead / cheating risk: High. Reviewing 1,667 backtested strategies and picking the top 5 is a textbook example of in-sample overfitting. Without out-of-sample validation, the live results prove nothing about the selection process.

---

**Video 11 — I Built an INSANELY Profitable AI Trading Bot (Full Guide)**
- URL: https://youtu.be/86AlV6174KI
- Claim: A complete free workflow using Claude Code, TradingView, TradingKit, and Trigger.trade takes a trader from zero to a live automated bot with forward testing and portfolio diversification.
- Stage: all stages (find → build → test → deploy → manage)
- Rule we could enforce: After coding, every strategy must enter an "incubation" phase (paper trading for a defined period with a minimum number of trades) before live capital is risked.
- What it never specifies: How long the incubation period should be; what the 5 "crucial rules" for portfolio diversification actually are; no commission or slippage in the backtest shown.
- Lookahead / cheating risk: The NNFX model includes an optimization step ("Coding & Optimizing") on backtest data. If optimization runs before the incubation split, the forward test is not truly forward.

---

**Video 12 — I Built an INSANE AI Trading Bot to Trade My $1,000 (Full Guide)**
- URL: https://youtu.be/KCvSmtKngyQ
- Claim: After losing money trading manually and with others' bots, a disciplined process — research, backtest, incubation, then automated execution via TradingView — is the right way to deploy $1,000 of real capital.
- Stage: all stages
- Rule we could enforce: The bot spec must record whether the strategy was tested on new (out-of-sample) data, and the lab blocks promotion to live if this flag is unset.
- What it never specifies: What "incubation period" length is sufficient; exact commission and slippage values used; whether ChatGPT vs. Claude produces meaningfully different strategies.
- Lookahead / cheating risk: "Impressive equity curve is only the beginning" suggests awareness of overfitting, but the video does not show the out-of-sample split methodology in detail.

---

**Video 13 — I Tested 3 INSANE AI Trading Bots… One DOMINATED.**
- URL: https://youtu.be/GtB-i71EyOo
- Claim: Different AI models (Claude, Grok, and a third) produce measurably different trading bot performance when tested against each other over one week.
- Stage: test
- Rule we could enforce: The lab must record which AI model generated each strategy version, so that model-to-model comparisons can be made on identical data and time periods.
- What it never specifies: What metric "dominated" means (win rate? profit factor? drawdown?); whether the one-week test period is statistically significant; which strategies each model generated.
- Lookahead / cheating risk: A one-week live test is too short to distinguish skill from luck. The video likely conflates short-term performance with model superiority.

---

**Video 14 — I Built an INSANELY Profitable AI Trading Bot for Stocks (Full Guide)**
- URL: https://youtu.be/zfEnBDG-u6s
- Claim: The same AI bot workflow (ChatGPT/OpenAI Codex + TradingKit + Trigger.trade + Alpaca paper account) works for stocks and ETFs without a TradingView subscription.
- Stage: all stages
- Rule we could enforce: The bot spec must name its asset class (futures, stocks, crypto, ETFs) and the lab must refuse to mix asset classes in a single strategy without an explicit override.
- What it never specifies: Whether stocks backtests include dividend adjustments or corporate actions; what Alpaca paper account results actually prove about live execution; exact commission values.
- Lookahead / cheating risk: Two-hour strategy research schedule selecting the best result is in-sample selection. Alpaca paper trading does not model real order book depth or market impact.

---

## 1. Lab Loop

How a bot moves from idea to retired:

1. **Seed** — User describes a trading idea in plain English (or selects a concept from a menu). The lab converts this into a structured spec: instrument, entry logic, exit logic, session window, risk limits, and costs. The spec is rejected if any required field is missing.
2. **Backtest** — The deterministic engine runs the spec against historical data with fees and slippage on. The backtest is split: training data for development, a held-out period the user never sees until the bot passes training. Results include trade count, win rate, profit factor, max drawdown, and Sharpe. Batches of candidates are ranked by Deflated Sharpe to penalize selection from large pools.
3. **Incubate** — The bot enters a mandatory paper-trading period on live prices. A minimum number of paper trades and a minimum calendar duration must pass before the bot can request promotion. The bot's live paper results are compared to its backtest projection; large divergence flags a problem.
4. **Unlock** — The user reviews the incubation report and confirms they want to promote the bot to live. The lab shows a warning if the incubation period was skipped or too short. The daily-loss kill switch and position-size cap are set at this point and cannot be removed.
5. **Deploy** — The bot connects to the broker in live mode. Every order is logged with entry price, fill price, slippage, and commission. The audit log is immutable.
6. **Monitor** — The dashboard tracks each live bot's equity curve, daily PnL, drawdown, and fill quality. Alerts fire on the notification channel when the daily loss limit is approached or a kill switch trips.
7. **Retire** — A bot can be paused (stops taking new trades), stopped (closes open positions), or retired (permanently archived with its full audit log). A retired bot's spec and results remain readable but it cannot be reactivated.

---

## 2. Ideas Worth Keeping

- Use AI to generate many candidate strategies from a plain-English description, then filter by statistical quality — not by the equity curve alone. (Videos 2, 10 — find/test)
- Require a minimum trade count (100+) for any backtest result to be considered valid. (Videos 2, 10, 12 — test)
- Incubation / forward-testing phase on paper before live capital. (Videos 11, 12, 14 — test/deploy)
- Record the specific AI model version that generated each strategy, so model comparisons are apples-to-apples. (Video 13 — build)
- Notification channel (Telegram or equivalent) must be configured before live trading is allowed. (Video 5 — manage)
- Paper-trading mode, alerts-only mode, and an account lock as distinct deployment modes. (Video 10 — manage)
- Strategy boilerplate templates to give beginners a valid starting structure. (Video 11 — build)
- Portfolio diversification across multiple uncorrelated bots with a shared daily-loss ceiling. (Video 11 — manage)
- Every bot spec must declare execution latency class; backtest fill assumptions must match. (Video 3 — build)
- Two-hour structured strategy research schedule as a reproducible process. (Videos 12, 14 — find)
- Asset class declared in the spec; cross-asset mixing blocked without explicit override. (Video 14 — build)

---

## 3. Conflicts Between Videos

**Conflict 1: Claude vs. ChatGPT/Grok for strategy generation**
- Videos 1, 2, 3, 5, 9, 10, 11, 12 use Claude. Video 14 uses ChatGPT/OpenAI Codex. Video 13 tests Claude, Grok, and a third model.
- Lab position: The lab is AI-model-agnostic at the spec level. The spec records which model generated a strategy, but the backtest engine is deterministic Python that does not depend on the model. Users can choose their model; the lab does not endorse one.
- Reason: Model capabilities change rapidly. Locking to one model bakes in a vendor dependency. Recording the model version preserves reproducibility without mandating a choice.

**Conflict 2: TradingView vs. TradingKit for backtesting**
- Videos 1, 9, 11, 12 use TradingView. Video 14 uses TradingKit specifically to avoid a paid TradingView subscription.
- Lab position: The lab runs its own deterministic Python engine (already in the architecture). Neither TradingView nor TradingKit is the lab's backtest engine. Both can be used as strategy development tools, but the authoritative backtest result always comes from the lab engine on Databento data.
- Reason: TradingView and TradingKit use slightly different fill models and data sources. Using an external tool as the canonical backtest creates reproducibility and trust problems.

**Conflict 3: Go live immediately vs. mandatory incubation**
- Videos 3, 4 show moving to live quickly with minimal validation. Videos 11, 12, 14 explicitly advocate for an incubation (paper) period before risking capital.
- Lab position: Mandatory incubation. The lab blocks promotion to live until the incubation requirements are met. A user can override with a logged confirmation, but the kill switch and size cap remain on.
- Reason: The architecture document already established this. Skipping paper trading is how users blow up accounts; the lab's job is to make that harder.

**Conflict 4: Use many GitHub repos vs. build your own**
- Videos 6 and 7 recommend adopting free public repos as bot foundations. Videos 11, 12, 14 build from scratch with Claude Code.
- Lab position: The lab builds its own engine. External repos are not trusted as backtest engines. Users may use external repos for inspiration or strategy ideas, but execution runs on the lab's code.
- Reason: External repos have unknown fill assumptions, potential lookahead bugs, and licensing complications. The lab cannot guarantee results if it does not control the engine.

---

## 4. Rules We Will Not Take

- **"Use good risk management"** — Vague. Cannot be enforced without specific numbers (max drawdown threshold, position size formula, daily loss limit). Mark unusable until the user defines the numbers.
- **"Let the AI decide position sizing"** — Multiple videos imply the AI can choose how much to trade. This cannot be made into a spec field, a test, or a management action because the AI's reasoning is not deterministic or auditable. The lab always uses a fixed contract count from the spec.
- **"The bot learns and improves over time"** (Video 3, implied by Jev) — Self-modifying strategy logic cannot be backtested for safety before it runs. A bot that changes its own rules mid-deployment is indistinguishable from an uncontrolled process. Not in v1.
- **"Just run it for a week and see"** (Video 13) — A one-week test period is not a statistical test. Cannot be enforced as a gate criterion without a minimum trade count and significance threshold.
- **"Use the AI to watch the chart and trade live"** (Videos 1, 3, 5) — Prompting a live LLM on each bar to decide whether to trade is non-deterministic, latency-dependent, and untestable. The lab architecture separates AI (spec translation) from execution (deterministic engine). This pattern is excluded by design.

---

## 5. What Every Bot Spec Must Contain

Before the lab will build or backtest a bot, its spec must include all of the following:

- [ ] Name (unique, human-readable)
- [ ] Instrument (e.g., NQ, ES, MNQ, MES)
- [ ] Signal timeframe (e.g., 15m, 1h)
- [ ] Fill resolution (e.g., 1s, 1m)
- [ ] Session definition (name, timezone, start time, end time, weekdays)
- [ ] Entry rule: side (long or short), trigger condition(s), order type (market/limit/stop), price reference if limit/stop, expiry in bars
- [ ] Exit rule: protective stop (reference price + offset in ticks), profit target (R:R ratio), time stop (session end or explicit bar count)
- [ ] Risk: number of contracts, max trades per session, daily loss stop in dollars
- [ ] Costs: commission per side in dollars, market slippage in ticks, limit fill condition in ticks
- [ ] AI model and version that generated the spec (for audit)
- [ ] spec_version field
- [ ] Asset class declared (futures / stocks / crypto / ETFs)
- [ ] Execution latency class (real-time / near-real-time / batch)

---

## 6. What a Test Must Report Before a Bot Can Be Deployed

The lab blocks promotion to paper or live if any of the following is missing from the test report:

- [ ] Total number of trades (must be ≥ 100 for a result to be considered valid)
- [ ] Win rate
- [ ] Profit factor (gross profit / gross loss)
- [ ] Maximum drawdown (in dollars and as a percentage of starting equity)
- [ ] Sharpe ratio (annualized)
- [ ] Deflated Sharpe ratio (corrected for the number of strategies tested in the same batch)
- [ ] Commission and slippage paid (total, not just shown as a footnote)
- [ ] In-sample vs. out-of-sample split dates (both must be recorded)
- [ ] Out-of-sample trade count (must be ≥ 30 for the out-of-sample result to count)
- [ ] Equity curve (full, not cherry-picked period)
- [ ] Worst consecutive loss streak
- [ ] Data source and date range used
- [ ] Whether the spec was modified after seeing the backtest results (if yes, the test is invalidated and must rerun on new data)

---

## 7. What the Lab Must Be Able to Do to a Deployed Bot

- **Start** — Begin taking new signals on the next bar after the session opens.
- **Pause** — Stop taking new entries; leave any open position running to its exit rules.
- **Stop** — Close any open position at market and stop taking new entries.
- **Kill** — Emergency flatten at market with slippage; log the reason; lock the bot from restarting without explicit user confirmation.
- **Switch to paper mode** — Move from live to paper execution without changing the strategy spec; useful for testing changes.
- **Switch to alerts-only mode** — Generate signals and log them but do not send orders; user executes manually.
- **Monitor equity curve** — Real-time view of the bot's running PnL, drawdown, and fill log.
- **Compare to backtest projection** — Side-by-side view of live results vs. the backtest equity curve; divergence threshold triggers an alert.
- **Set or update daily loss limit** — Can be tightened (not loosened without confirmation) while the bot is running.
- **View full audit log** — Every order, fill price, slippage paid, commission paid, and signal that triggered it.
- **Retire** — Archive the bot permanently with its complete run history; the spec and results remain readable.
- **Notification channel management** — Add, remove, or test the Telegram (or equivalent) channel without stopping the bot.

---

## 8. Next 5 Build Tasks (in order)

1. **Define and validate the bot spec model.**
   Write the Pydantic model that enforces section 5's checklist. Every field in the checklist must be a required field with explicit validation (type, range, and cross-field constraints — e.g., stop must sit on the protective side of entry, out-of-sample split date must be after in-sample end date). Generate a JSON Schema from the model for the web layer. Write fixture tests covering: a valid spec passes, each required field missing causes rejection, each cross-field constraint catches the violation. The model lives in `shared/spec/`. No UI and no engine work until this model has green tests.

2. **Build the deterministic backtest engine core.** — Wire up the event loop, bar iteration, and fill simulator against the validated spec.

3. **Implement the three signal blocks.** — Session levels, liquidity sweep, and fair value gap, each with fixture tests from labeled chart examples.

4. **Build the job queue and worker.** — Postgres job table, `SELECT FOR UPDATE SKIP LOCKED` claim, result write-back, retry-on-timeout logic.

5. **Build the incubation tracker.** — Paper trade execution against live prices, trade counter, calendar timer, divergence check vs. backtest projection.

---

## 9. Open Questions

1. Which broker API do you want to connect first for live order routing — Tradovate, TopstepX, Interactive Brokers, or another?
2. What is the minimum incubation period you want to enforce — 5 trading days and 20 paper trades (as noted in the architecture doc), or a different threshold?
3. Do you want the strategy research step to be AI-assisted (you describe it in English and the lab generates the spec) from day one, or do you want to fill in a structured form manually for the first bot?
4. What is the maximum daily loss in dollars you want to hard-code for your personal bot, and should the lab allow you to raise it (or only lower it) after deployment?
5. Which notification channel do you want for alerts — Telegram, email, or SMS?
6. Do you want to support trading multiple bots simultaneously from the start, or restrict to one active bot per account for the personal version?
7. What is your preferred data subscription for Databento — tick-by-tick (1s fills) or minute bars (cheaper but lower fill accuracy)?
8. Should the held-out test period be locked even from you (the developer) until a bot formally requests promotion, or is it acceptable for you to see it during development of the first bot?
