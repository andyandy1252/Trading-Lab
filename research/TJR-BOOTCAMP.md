# TJR Boot Camp — compare, contrast, and lab use

Worked from published captions of [TJR’s Boot Camp](https://www.youtube.com/@TJRTrades), not from the moving chart picture. Chart examples below are the ones he described out loud. Psychology days are listed and then ignored as engine rules.

Rule used here: if TJR and PB describe the same thing, keep the **already confirmed** meaning in `docs/GLOSSARY.md`. Add a new term only when TJR names a real extra object (order block, execution ladder, invalidation stop). Do not give the translator two definitions for “sweep” or “FVG.”

---

## What these 27 videos are

Technical days (language + later blocks):

| Day | Title | Lab use |
| --- | --- | --- |
| 2 | [Candlesticks](https://youtu.be/bEkbNGUzQME) | Same as PB candle / body / wick |
| 4 | [Trends](https://youtu.be/viuGHEuv0nw) | Same as PB bullish / bearish structure; HTF wins |
| 6 | [Break of Structure](https://youtu.be/PmhuPbY8ZHo) | Same as PB MSS. Alias: **BOS** |
| 8 | [Liquidity Pt 1](https://youtu.be/Lxnu7InGhGE) | Why: resting orders; banks need the other side |
| 10 | [Liquidity Pt 2](https://youtu.be/rdz6vnXb8wE) | Where: above highs / below lows, every timeframe |
| 12 | [Liquidity Pt 3](https://youtu.be/KtC2SbemF6w) | How to trade it: magnet + wait for BOS |
| 13 | [Risk](https://youtu.be/RkMBoqbeUq8) | Spec `risk` fields, not a pattern |
| 14 | [FVG Pt 1](https://youtu.be/d0AxLACYaqU) | Why: void of opposing orders |
| 16 | [FVG Pt 2](https://youtu.be/S1kY3Fw6JUQ) | How to mark: three candles, wick 1 to wick 3 |
| 18 | [FVG Pt 3](https://youtu.be/qecF411R83s) | How to use: retrace tool after sweep + BOS |
| 19 | [News](https://youtu.be/w5sUCqFH3Lg) | Same as PB news blackout |
| 20–24 | [Order Blocks](https://youtu.be/qhuFg_OXdmE) [pt 2](https://youtu.be/RQSVIKddFHI) [pt 3](https://youtu.be/12_F-mIUfL0) | **New object** |
| 26–28 | [Equilibrium](https://youtu.be/j1pVK897oZQ) [pt 2](https://youtu.be/-E7plUbSJUk) | Same as PB premium / discount |
| 30–33 | [Execution](https://youtu.be/ESsy0uoFAz4) [pt 2](https://youtu.be/SLhIA7vW9x8) [pt 3](https://youtu.be/K8DwhtmvAW8) | Recipe that sequences the five blocks |
| 34–36 | [Daily Bias](https://youtu.be/sjuWqKDsQtI) [pt 2](https://youtu.be/UPA9LQW7phk) [pt 3](https://youtu.be/Y1lqifylC4s) | Same job as PB daily bias, top-down |
| 38 | [Stop Losses](https://youtu.be/1FunNCUw_jM) | Stop = invalidation beyond the sweep |

Not engine (discipline, ego, losses, bank-holiday “don’t trade”): [Day 3](https://youtu.be/w2CWF0WtLmQ), [15](https://youtu.be/T4xVS7iV5d8), [21](https://youtu.be/z9p7OThLkr4), [41](https://youtu.be/PyCPHiO2nj0). Useful as product copy (“do not trade FOMC / US bank holiday”) later. Not patterns.

TJR’s five building blocks, in his words: **liquidity sweep, break of structure, order block, fair value gap, equilibrium.**

---

## Deep dive: liquidity

TJR’s claim is not “price bounces off a line.” It is: **large orders cannot fill in empty air.** To buy a lot, someone must sell a lot. The cheap way to find those sellers is to run stops under a low (longs selling) and to trigger breakout sells under that same low. That burst of transactions is the pool. After it prints, the larger player can go the other way.

That is why a sweep alone is not a trade. Sweep = *potential* that orders got filled. You do not know until structure flips.

**On the chart (his examples):**

- Uptrend: pending buys and short stops sit above the last high. Price trades through that high, then often sells off. He showed this on daily ES, weekly, even a yearly low taken then reversing.
- Downtrend: sell stops and long stops sit under the last low. Price trades through that low, then often rallies.
- Same picture on 15-minute Asia, 1-minute, monthly. Fractal.
- Prominent pools only. The high that started a large leg matters more than every two-candle bump.
- After a sweep + BOS, the **opposing** pool is the take-profit magnet (shorts aim at prior lows; longs aim at prior highs). Institutions exit where the crowd will take the other side again.

**Lab split (keep PB):**

| Word | Meaning |
| --- | --- |
| Liquidity | Resting stops / limits at a swing |
| Sweep | Price trades through that swing |
| Taken vs resting | Through the level vs not yet |
| Draw | The next pool |

TJR adds one **state** the engine can use: sweep is unconfirmed until BOS. That matches our already-locked “wick through = sweep, body close = MSS.”

Do not enter on the sweep bar. Do not treat every high as a pool.

---

## Deep dive: fair value gap

TJR names it three ways on purpose: FVG, imbalance, **liquidity void**. Opposite of a pool.

- A pool is a price with **too many** resting orders (stops).
- A gap is a price with **too few** opposing orders. That is why the middle candle can travel far: nothing was there to fade it.

**Mark it (same as PB):** three closed candles. Bullish: from candle 1 high wick to candle 3 low wick. Bearish: from candle 1 low wick to candle 3 high wick. If those wicks overlap, the void is already filled — **not an FVG**. Size of the hole does not make it more true.

**How he uses it (this is the depth, not the box):**

- FVG is a **retracement / continuation** tool, not a reversal. In a bullish trend you want **bullish** gaps. You do not short a bearish gap to “catch the top” unless higher-timeframe bias already flipped.
- After HTF BOS, wait for price to trade back into the HTF gap, then drop to LTF and wait for LTF BOS (or a clear reaction candle). The gap tap without LTF BOS is not the entry. He showed a 15-minute BOS, premarket tap of the 15-minute void, then a 1-minute BOS after cash open as the short.
- If price **closes through** the gap the other way, he drops it. “The second we push past this, no longer considering it.”
- He prefers sweep + BOS as the start of the move. FVG is the patient second chance when the first entry has bad R:R.
- Gaps are everywhere. Entering every tap is how people blow up. Confirmation is mandatory.

**Lab split:** keep PB wick-to-wick FVG, tap = fill, body through = invert. TJR agrees. Add the job label: **void (lack of opposing orders)** vs **pool (resting stops)**. That is how the translator should think, not a second measurement.

---

## Deep dive: order block (new)

This is the term PB did not give us as a first-class object.

**What it is.** The impulsive leg **that caused the sweep**. If price rallies through buy-side, the up-leg that did that run is the bearish order block: the range where shorts could fill. If price dumps through sell-side, the down-leg is the bullish order block.

**Why price comes back.** They already filled in that range once. On a retrace they can fill more of the same side there, then continue.

**Rules he actually stated:**

- One order block per **new trend** on that timeframe. It is born at the sweep + BOS that starts the trend. You do not paint an OB on every candle in the trend. The next OB appears at the next trend shift.
- First retracement tool, before FVG, before equilibrium. Still near the origin of the move, so R:R is often better than chasing the BOS close.
- Same object on every timeframe. A 4-hour OB is a wide range; a 1-minute OB is tight. Stops must match the timeframe of the OB you are using.
- Alias he uses: accumulation area. Same thing. Do not invent a second block type.
- Not an entry because price “touched a rectangle.” Entry is: sweep happened, BOS confirmed the fill, then price returns to that fill range.

**Not v1.** Spec still has only `session_levels`, `liquidity_sweep`, `fair_value_gap`. Order block waits for chart fixtures you label: “this down candle is the OB, this one is not.”

---

## Break of structure vs our MSS

TJR **BOS** = our **MSS**. Body close beyond the **most recent** opposite swing. Wick through is a sweep / fake, not BOS. Only the latest swing counts; old swing lows are retired.

**Fork to record, not to split the glossary:** PB’s swing is a **three-candle** fractal. TJR’s high is **two candles** (up then down; high = highest wick of the pair). Two-candle swings fire more often. The lab default stays **three-candle** (already confirmed). English “break of structure” still maps to MSS. A spec may later set `swing_definition: two_candle`.

---

## Execution ladder (how the five blocks click)

TJR’s Day 30 recipe, safest at the bottom:

1. **Sweep + BOS** — potential fill, then confirmation. Top of the move. Most aggressive.
2. Missed that? Wait for the **order block** (origin of the sweep).
3. Missed that? Wait for an **FVG** tap in the new direction, then LTF BOS.
4. Best beginner stack: sweep + BOS + (OB or FVG) **and** equilibrium (discount for longs, premium for shorts).

All of that is still “no trade” unless daily/HTF bias agrees. Indices: New York session is where the daily candle is mostly built. London on ES/NQ is usually not his session.

**Stop (Day 38):** invalidation is **beyond the sweep**, not just beyond the entry candle, plus a small buffer for spread. If the sweep is so far that R:R dies, he may stop beyond the OB instead — and he dislikes that, because the true invalidation is still the sweep.

---

## Compare / contrast with the PB glossary

| Idea | Keep (PB, already confirmed) | TJR adds | Do not merge |
| --- | --- | --- | --- |
| Candle / body / wick | Closed OHLC; body close vs wick | — | — |
| Trend | HH/HL vs LL/LH; HTF wins | Line chart to read HTF | — |
| MSS / BOS | Body close beyond last opposite swing | Name **BOS**; most-recent swing only | Wick-as-break |
| Sweep | Trade through the pool | Unconfirmed until BOS | Enter on the sweep |
| FVG | 3 candles, wick-to-wick, overlap = none | Call it a **void**; continuation only | FVG as reversal |
| EQ / premium / discount | 0.5 of the dealing range | Same Doritos-on-sale story | Enter on 0.5 alone |
| Daily bias | Why move, from which side, respect vs not | Top-down weekly → daily structure → 4h/1h confirm → 1–5m execute | Fade HTF because LTF looks pretty |
| Sessions / news | NY AM kill zone; wait after red news | Don’t trade US bank holiday / stacked PPI+FOMC as default | — |
| SMT, LRL, EQH, data wick, devil’s mark | PB only | TJR bootcamp does not teach these | Don’t delete them |
| Order block | — | **New** | Don’t call FVG an order block |
| Inverse FVG | Body through = invert; not a v1 block | He “drops” a gap once closed through | Don’t code IFVG yet |

---

## How this helps the engine

The engine never “understands ICT.” It evaluates **named blocks on closed bars**.

TJR gives the **order of operations** those blocks must run in:

```
prominent swing
  → sweep (price through the swing)
    → BOS / MSS (body close the other way)   // confirmation
      → optional retrace: order_block, then fvg, then equilibrium
        → target: opposing liquidity
```

v1 can already express a slice of that: session level or swing → `liquidity_sweep` → `fair_value_gap` on the entry `when` list, with `after` / `within_bars`. BOS and order block are the next two pure functions, each with fixtures.

Fill rules stay ours (pessimistic, fees on, stop if both hit). TJR does not replace fill math.

---

## How this helps memory / knowledge base

`docs/GLOSSARY.md` is the only meaning of a word. This file is the **reasoning**: why a sweep is not an entry, why a gap is a void, why an order block is the cause-leg.

When later English says “buy the order block after they grab lows,” the translator should:

1. Map grab lows → `liquidity_sweep` of sell-side.
2. Map after they grab → wait for MSS/BOS (once that block exists) or require a later event.
3. Map order block → future `order_block` (not FVG).
4. Refuse to invent a second FVG definition.

Psychology videos stay out of the glossary so the model does not turn “be disciplined” into a fake indicator.

---

## How this helps the software build strategies from English

The user will not say JSON. They will say TJR/PB slang. The model’s job is a **dictionary lookup**, then a spec:

- “Sweep the high and go short” → incomplete. Prompt for BOS / FVG / stop / session / costs.
- “Sweep, break structure, tap the FVG in discount” → that is TJR ladder step 3–4. Legal once BOS exists; today it can be sweep + FVG with `after`.
- “Enter the order block” → not v1. Show a card: “we know this word; it is not coded yet.”

Discretion on a chart, for a human, is “does this high look prominent?” The engine cannot have discretion. Prominence has to become a parameter (minimum swing length, session high, PDH). Until then the translator must ask, or use `session_levels` / PDH as the prominent pool.

---

## How you use this to build a bot

Say the story in the five-block order, then fill the cards we already require:

1. Instrument and session (NQ, NY AM).
2. What gets swept (prior day high, London high, a marked swing).
3. What confirms (today: FVG after the sweep; later: BOS).
4. Entry (limit at FVG midpoint or next-bar market — you pick).
5. Stop beyond the sweep, not beyond the FVG only.
6. Target at opposing liquidity or R:R.
7. Costs and daily loss.

Example English that the lab should eventually accept:

> Short NQ in New York AM after buy-side at prior day high is swept, then a body close under the last higher low, then a limit at the bearish FVG in premium. Stop 4 ticks above the sweep extreme. Target 2R. 1 contract. $500 daily loss.

Until BOS and order block are coded, that sentence is stored as language and only the **sweep + FVG** slice can backtest.

---

## Homework for the next spec-lock (not this file)

- Copy glossary forks into `docs/SPEC.md`.
- Add alias `break_of_structure` / `bos` → MSS.
- Keep 3-candle swings as default.
- Queue `order_block` as the first block after the original three, with labeled charts.
