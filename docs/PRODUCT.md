# Product Vision

_Captured 2026-11-12 from a product/monetization grill. This is the north-star spec for what Trading-Lab is becoming. Engine/spec contracts live in `SPEC.md`, `GLOSSARY.md`, and `DECISIONS.md`; this file is the product layer above them._

## What it is

An **all-in-one AI trading desk for futures day traders**: a "trading headquarters" where a trader runs their entire workflow through a curated team of AI agents — honest backtesting, risk protection, news, and journaling — commanded through one clean interface.

## Who it's for

Futures day traders at both ends:
- **Unprofitable** traders hunting for a real edge.
- **Profitable** traders optimizing their workflow.

Warmest leads: **burned refugees** from the get-rich-quick / scam ecosystem who now want the truth. The product is anti-hype by design, so honesty attracts the serious and repels the fantasy-chasers — that is intentional.

## The heroes

- **Risk Guardian** (emotional hero) — watches the trader's prop/live account, knows the firm's exact rules (max daily loss, trailing drawdown), and **warns** before a breach ("$40 from your daily-loss limit"). **Warn, never command** — read-only, human-in-the-loop, to stay inside prop-firm ToS and CFTC/CTA limits.
- **Honest Edge Lab** (credibility hero / the moat) — plain-English or drawn strategy, tested honestly on real data. Nobody in the space does this straight.
- **Auto-Journal** (the TradeZella-killer) — trades auto-import from the broker, AI writes the journal, tags setups, surfaces the trader's leaks.

## Edge Lab architecture (the honest core)

Flow: **chart teaches → engine judges → chart replays.**

1. The trader draws or describes a setup.
2. The AI reads the **structured drawing objects** (tool type + exact price/time coordinates, not pixels) and classifies **intent** ("horizontal line on the session high = liquidity", "rectangle = 15m FVG").
3. **Deterministic ICT detectors** (the `research/ict/` library) own the geometry — exact session windows, FVGs, liquidity, highs/lows. The AI never invents a price level.
4. **Session-scoped backtest** (NY / London / Asia window logic: jump to each session, speed through, skip the day if no entry, one trade per session) runs on **real historical NQ data (Databento)**.
5. **Fee + slippage toggles** per account type (Apex / Topstep / live) show the trader's **true RR**.
6. **Honest Trust Score** — hidden under ~100 trades (no walk-forward sample yet = no published number).
7. Every trade **replays on the chart** so the trader watches winners and losers build the stats.

**Principle: AI = intent-translator, code = ground truth.** This is what keeps it simultaneously impressive (AI buddy on the chart) and statistically honest (reproducible, auditable).

**Chart engine: klinecharts (Apache-2.0)** — rich drawing tools + `createOverlay` API for AI markup, commercial-safe, no branding strings. The pirated "TradingView premium" GitHub repos are permanently off-limits (proprietary, DMCA'd, malware risk). Legit fallback only if pixel-perfect TV parity is ever required: TradingView "Advanced Charts" (free but branded, no open-source).

## The desk / UX (clean despite depth)

- **Two toggleable surfaces:** (1) chart + AI-coach workspace for charting/backtesting; (2) interactive **"trading HQ"** — each agent is a **character at a desk** (coach, risk, news, journal).
- **Progressive disclosure:** the HQ stays neat; click a character to open its "guts" and configure it. Depth is layered behind the avatars.
- **Agents interoperate:** on the chart, the coach can reach the other agents; all share one brain (below).
- **Curated cast now** (coach / risk / news / journal), built to a high bar. **Extensible later** — "empty desks" you hire into. The original plain-English *agent*-building becomes the platform expansion (and an upsell). Plain-English *strategy*-building lives in the Edge Lab today.

## Understanding the user / the moat

- **One shared, compounding per-user trading brain** that every agent reads and writes: instruments and sessions traded, the ICT concepts the trader taught the AI, risk rules, full journal history, recurring leaks.
- Coach references the journal; Guardian knows the trader's rules; News watches the trader's instruments; Edge Lab remembers the trader's setups. One brain, four faces.
- This is the **switching-cost moat**: TradeZella only *stores* trades; this desk *learns the trader* and gets more valuable every session. Leaving means abandoning the only system that understands how they trade.

## Monetization

- **Subscription.** Recurring value = the Edge Lab as an ongoing "edge lab" (keep testing new ideas + "is my edge still alive") **plus** the daily-use desk.
- **Three tiers:** Free → **Edge Lab ~$49/mo** → **Control Room ~$129/mo**.
- **Anchored** against prop-firm fees / data / courses ("cheaper than one blown eval"), not against free.
- **Free tier** = a capped taste of the whole room (a handful of backtests, read-only peek at each agent) so users feel the honesty and the desk before paying.
- **Margins near-pure:** historical data bought **once** and shared across all users; all **live** data comes from the **trader's own broker feed** → per-user data cost ≈ zero, and no CME redistribution licensing.

## Distribution

- **Honesty is the marketing.** Public, verifiable backtest results; show the methodology; "the tool that tries to prove your edge *wrong*."
- Distribute through **credible educators + prop firms** (aligned incentives — they want traders with real edges), not hype influencers.
- Position explicitly against the scam ecosystem.

## Connections & execution

- **MVP connectors: Tradovate OAuth (read-only) + TopstepX / ProjectX API.** Rithmic / CQG are phase-2 (conformance-gated). IBKR is a later adjacent market.
- **Legal guardrails (non-negotiable):** never store broker passwords (prop ToS forbids credential sharing — use OAuth / official read-only keys); journal the user's **own fills**, never redistribute live CME quotes; keep agents **descriptive, not prescriptive** (tailored "you should sell now" advice edges into CFTC/CTA territory).
- **Three modes:**
  - **Backtest** — real *historical* data (Databento), bought once.
  - **Forward / paper test** — real-time on a *simulated* account, via the trader's own broker demo (their feed, their sim).
  - **Live deploy** — **alert-driven / one-click, human-in-the-loop** execution ("your edge just triggered — confirm to send"). **Full hands-off auto-trade is a legally-gated maybe-later** — banned on prop evals, regulated on live — never the default.

## Scope

- **Everything ships at once in v1** — Edge Lab + chart co-pilot + autopilot detectors + Risk Guardian + auto-journal + broker connections + full agent desk.
- **Eyes open:** longest runway to first dollar, full integration + legal surface live at launch, no early-feedback course-correction. Polish/optimize after launch, not before.

## Competitive frame

Beat TradeZella (and Tradervue/Edgewonk) by being what they aren't: futures-native, AI-agent-driven, honest backtesting (not manual replay), live account awareness, auto-sync journaling (incumbents are CSV-only for futures — a real market gap), and a compounding per-user brain.
