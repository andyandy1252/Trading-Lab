# Glossary

Confirmed 2026-10-19 from PB Trading’s ICT for Dummies (EP. 1, 3–10). Extended 2026-10-19 from TJR’s Boot Camp: same meaning kept where both teachers describe the same object; new rows only where TJR names something PB did not (order block, execution ladder, invalidation stop). Reasoning and compare/contrast live in `research/TJR-BOOTCAMP.md`. English that uses these words must map to this file, then to `docs/SPEC.md`. If the two files disagree, stop and fix the spec. Do not invent a third meaning in code.

Status on every row is **confirmed**. None of these are coded with fixture tests yet.

Source playlist (EP. 2 psychology was not in this batch):

- [EP. 1 Candlesticks](https://youtu.be/RTlRUFNts0Y)
- [EP. 3 Market Structure](https://youtu.be/pBqjCsQ3YS0)
- [EP. 4 Liquidity Pt. 1](https://youtu.be/W5VPyhgwWsQ)
- [EP. 5 Fair Value Gaps](https://youtu.be/8MflBA9AVLU)
- [EP. 6 Time](https://youtu.be/9A0YUxFtB8c)
- [EP. 7 Liquidity Pt. 2](https://youtu.be/t8WxLNp6dEU)
- [EP. 8 Premium and Discount](https://youtu.be/HXbvgyRz5bM)
- [EP. 9 SMT Divergence](https://youtu.be/sHV5Hdl8XIs)
- [EP. 10 Daily Bias](https://youtu.be/VKiTAiQHZBQ)

TJR Boot Camp (same meanings, plus order block / ladder / invalidation): video list and chart-described examples in `research/TJR-BOOTCAMP.md`.

How to read a row: **term**, aliases we accept, what the engine must mean, what it is not, which later block it becomes.

---

## Candles and timeframes

### Candle

Aliases: bar, candlestick.

A closed bar with open, high, low, and close. Bullish if close is above open. Bearish if close is below open. The forming bar cannot create a level, a gap, a sweep, or a fill.

Not this: pattern names (doji as an entry, engulfing, pin bar).

### Body

The open–close range of a closed candle.

### Wick

Aliases: shadow, tail.

The extreme the candle reached but did not close at. High wick is `high` minus `max(open, close)`. Low wick is `min(open, close)` minus `low`.

### Body close

A real break. The close of a closed candle is beyond a named level. Used for market structure shift and for disrespect / inversion of a fair value gap.

Not this: a wick through the same level.

### Strong candle

Large body, little wick in the direction of the move. Displacement. Visual only until a fixture defines body-to-range.

### Weak candle

Long wick that gives back most of the move. Rejection. Visual only until a fixture defines it.

### Doji

Open and close nearly the same. Possible pause. Not an entry by itself. Distance is not numeric yet.

### Nested timeframes

A higher-timeframe candle is the open of its first child bar, the high of the highest child, the low of the lowest child, and the close of its last child. A 15-minute bar is three 5-minute bars or fifteen 1-minute bars. When a stop uses a sweep extreme, store the extreme from the finest bars inside the signal candles.

---

## Market structure

### Bullish structure

Sequence of higher highs and higher lows: low, high, higher low, higher high, repeating.

### Bearish structure

Sequence of lower lows and lower highs: high, low, lower high, lower low, repeating.

### Market structure shift

Aliases: MSS, BOS, break of structure, CISD, change in state of delivery, order-flow flip.

A trend change on closed bars. Only the **most recent** opposite swing counts. Older swings are retired.

- Bearish MSS: body closes below the last higher low.
- Bullish MSS: body closes above the last lower high.

A wick through that swing is not an MSS. That wick is a liquidity sweep until a body close proves the shift. TJR calls the sweep *potential* and the body close *confirmation*. Same split as this row.

v1 block: `market_structure_shift`. Do not treat CISD or BOS as a separate pattern. Same rule as MSS.

### Higher timeframe vs lower timeframe

Higher timeframe structure wins. If the higher timeframe is bullish and the lower timeframe is bearish, wait for bullish structure on the lower timeframe. Do not fade the higher timeframe as the default.

---

## Liquidity

### Liquidity

Fuel for the next move. Stops and limits resting at obvious swing highs and swing lows. Price either seeks liquidity or rebalances a range.

Two opposite pictures, same word family:

- A **pool** is a price with too many resting orders (stops above a high, stops below a low). That is what a sweep runs.
- A **void** is a price with too few opposing orders. That is a fair value gap. Do not call a gap a pool.

### Swing high

Three consecutive closed candles: a high with a lower high on each side. Candle color does not matter. Only the highs.

Reports: `price` (the middle high), `bar_time`.

Lab default is this three-candle fractal. TJR marks a high as two candles (up then down; high = highest wick of the pair). That fires more often. English still maps to this row unless a spec sets `swing_definition: two_candle`.

v1 block: `swing_points` with `kind: high` or `both`.

### Swing low

Three consecutive closed candles: a low with a higher low on each side. Color does not matter.

Reports: `price` (the middle low), `bar_time`.

Same default vs two-candle note as swing high.

### Prominent swing

A swing that started a large move, or a named session / previous-day / weekly pool. Not every two-candle bump. The engine cannot have discretion here: a spec must name the pool (`session_levels`, PDH/PDL, or a swing with a later length filter). Until that filter exists, the translator asks which high or low.

### Buy-side liquidity

Aliases: BSL, buy stops.

Stops above a swing high. Shorts getting bought back. Interchangeable with “that swing high” when the high is the pool.

### Sell-side liquidity

Aliases: SSL, sell stops.

Stops below a swing low. Longs getting sold.

### Resting vs taken

A pool is **taken** when price trades through that high or low. Untaken pools are still magnets. Mark obvious swings only, not every pivot.

### Liquidity sweep

Aliases: raid, stop run, turtle soup (mentioned, not defined as a separate block).

Price trades through a named buy-side or sell-side pool. In this language pack, the sweep is the run through the level. It does not require a close back through the level. A later body close the other way is MSS, not the sweep itself.

Sweep is **unconfirmed** until MSS/BOS. It is not an entry. Large orders needed the other side of those stops; the body close is how we know they filled and flipped.

Not this: support-and-resistance bounce without the run. Not this: a wick that fails to trade through the pool. Not this: every high on the chart.

v1 block: `liquidity_sweep`. Completion rule is this glossary, not “close back through,” unless a later spec change says so.

### Draw on liquidity

The next pool price is likely to run. A strategy names one draw. Session highs, previous-day highs, and equal highs are draws, not first take-profits by default.

---

## Fair value gaps

### Fair value gap

Aliases: FVG, imbalance, inefficiency, liquidity void, BISI (bullish), SIBI (bearish), buy-side imbalance, sell-side imbalance, “bissy,” “cibby.”

Three consecutive closed candles.

- Bullish FVG (BISI): candle 1 high does not overlap candle 3 low. Zone from candle 1 high up to candle 3 low. Displacement higher.
- Bearish FVG (SIBI): candle 1 low does not overlap candle 3 high. Zone from candle 3 high up to candle 1 low. Displacement lower.

Measure wick to wick. If either wick is missing, use that candle’s high or low. If the wicks of 1 and 3 touch or overlap, there is no gap.

Size does not matter. `min_size_ticks` may exist as an optional filter. Default for PB English is 0.

A continuation / retrace tool, not a reversal. In a bullish trend, use bullish gaps. Do not short a bearish gap to catch a top unless higher-timeframe MSS already flipped. A tap without later confirmation (MSS on a lower timeframe, or a named respect reaction) is not an entry.

If a body closes through the gap the other way, drop it as an original-direction level (see Disrespect / inversion).

v1 block: `fair_value_gap`.

### Respect

Price wicks into the gap (or tags it) and trades away in the original displacement direction. The gap is still valid as a continuation level.

### Disrespect / inversion

Aliases: invert, IFVG, inverse fair value gap.

A body closes through the gap. The old gap is no longer used in the original direction. It may then be used the other way.

v1 block: `inverse_fvg`. A wick into the zone is respect, not this block.

### Used up

A tap into the zone is a fill / rebalance. The gap is finished as an original-direction level when a body closes through it (inversion). It is not “used up” at the midpoint unless a spec says so.

---

## Sessions, news, and prior day

Clocks are US Eastern (`America/New_York`) for NQ and ES. Half-open windows still follow `docs/SPEC.md`: start included, end excluded.

### Kill zone

A session window with the cleanest volume for that product. For NQ/ES, New York AM is the default kill zone. Master one session.

### Asia session

20:00–00:00 Eastern.

### London session

02:00–05:00 Eastern.

### New York AM

Aliases: NY AM, NY open kill zone.

08:30–11:00 Eastern. Default execution window for beginners starts at cash open **09:30**. 08:30 is the usual news print and is still in the zone if a spec includes it.

### New York lunch

Midday. Low volume. Default: do not trade.

### New York PM

After lunch. Usually weaker than AM. Some days it is the cleaner session (for example FOMC afternoon).

### Overnight expansion

A huge Asia or London range is a reason to skip New York AM that day.

### News blackout

Red-folder USD events on an economic calendar (CPI, PPI, NFP, FOMC, Powell). Wait about 5–10 minutes after release before a new entry. Beginners skip FOMC day. Size down on NFP. `news_open_slippage_ticks` stays stored but off until a named window is coded.

### Previous day high / previous day low

Aliases: PDH, PDL.

High and low of the **prior daily candle**, not the cash session 09:30–16:00 unless a spec names `cash_rth` instead.

### Previous week high / low

High and low of the prior weekly candle. Same idea as PDH/PDL at week scale.

---

## Other draws (liquidity part 2)

### Session high / session low

Highest high and lowest low of a **completed** named session. After a sweep of one side, look to the other side unless price displaces through (body) and keeps going.

v1 block: `session_levels` with `which: prior_completed`.

### Low-resistance liquidity

Aliases: LRL, trendline liquidity, failure swings, generated liquidity.

Several unswept swings stacked along a trend: lower highs that never take the last high (buy-side stack) or higher lows that never take the last low (sell-side stack). Expect a fast run through the stack, not only the first pivot.

### Equal highs / equal lows

Aliases: EQH, EQL.

Two swing highs or two swing lows printed at the **same price**. Two separate swings hold more than two adjacent candles. Significant on NQ. Ignore as a default on ES; ES prints equals from low volatility.

### Data high / data low

Aliases: data wick.

High and low of the **news candle** only. Not a random large candle. After one side is swept, look at the other side.

### Internal range liquidity / external range liquidity

Aliases: IRL, ERL.

Internal = unfilled fair value gap. External = major swing, session high/low, or PDH/PDL. In trend: into internal, then to external, until MSS. First take-profit is often internal. Session and previous-day pools are not the first TP by default.

### Devil’s mark

A wickless open on a higher timeframe (hourly and up). Price often returns later to print the missing wick. Ignore as a default on 1-minute noise.

### New day opening gap

Aliases: NDOG.

Gap between prior session/day close and the next open. Treated like an FVG. Often wants a full fill before a reaction, unless the twin index already filled it (see SMT).

### New week opening gap

Aliases: NWOG.

Same idea at the week boundary.

---

## Premium and discount

### Dealing range

One impulsive swing, low to high or high to low. Fibonacci 0 to 1 on that leg. New swing, new range. Ranges nest across timeframes.

### Equilibrium

Aliases: EQ, 0.5.

The midpoint of the dealing range (0.5). Not a pattern. A location.

v1 block: `equilibrium`. Discount is a close below this midpoint. Premium is a close above it.

### Discount

The half of a bullish dealing range below equilibrium. Longs belong here, or at least after price has tagged equilibrium.

### Premium

The half of a bearish dealing range above equilibrium. Shorts belong here.

### Rebalance

After a large impulse, wait for a return to at least equilibrium before continuing in that direction. Shorting in discount or longing in premium is a bad location.

When English says “buy the FVG,” prefer the FVG that sits in discount (long) or premium (short).

---

## SMT

### SMT divergence

Aliases: SMT.

NQ and ES compared on the same swing. One index sweeps the swing. The other fails to sweep the matching swing. Reversal hint, not an entry by itself.

- Bullish SMT: one makes a lower low; the other does not.
- Bearish SMT: one makes a higher high; the other does not.

The index that did **not** sweep often delivers to the target faster.

Count only SMTs at significant pools: session high/low, PDH/PDL, or inside a higher-timeframe FVG / PDA. Random 1-minute SMTs are noise.

If the other index already took your take-profit pool, this index may not need to. That is an SMT at the target.

Needs a reference instrument. v1 execution stays one instrument. SMT is a later filter.

Not this: YM as a required third leg. Default pair is NQ vs ES.

---

## Daily bias

### Daily bias

The morning read: direction and draw for the session, plus an if-then condition. Not an order.

Ask:

1. Why would the market move (which pool or gap)?
2. Are we delivering **from** buy-side or sell-side (what was just swept)?
3. Which PD arrays are we respecting vs disrespecting?

### Delivering from buy-side / sell-side

Just swept sell-side and not displacing lower → often bullish delivery from SSL. Just swept buy-side and not displacing higher → often bearish delivery from BSL.

### PD array

Aliases: PDA, PDRA, PD ray.

Catch-all for FVG, inversion, order block, and similar levels. In v1 a PDA is the named `fair_value_gap`, `inverse_fvg`, `order_block`, or session level in the spec. Breaker is still uncoded.

### Condition

An if-then on the bias. Example: if the 4-hour bullish FVG holds, longs toward London highs; if it inverts, shorts toward PDL. A condition can be a gap holding, an SMT holding, or equilibrium holding. Neutral is allowed when HTF PDAs conflict.

### How price gets there

Bias is higher timeframe. Entries for this language pack are 1–5 minute, after a respect tap or an inversion, in premium or discount of the executing leg.

---

## Order blocks (TJR)

### Order block

Aliases: OB, accumulation area.

The impulsive leg **that caused the sweep**. If price rallied through buy-side, that up-leg is the bearish order block (shorts can fill more of the same range on a retrace). If price dumped through sell-side, that down-leg is the bullish order block.

Rules:

- One order block per **new trend** on that timeframe. Born at the sweep + MSS that starts the trend. The next OB appears at the next trend shift. Do not paint one on every candle.
- First retrace tool after a missed sweep+MSS entry, before FVG, before equilibrium.
- Same object on every timeframe. Stop size must match the timeframe of the OB in use.
- Not an entry because price touched a rectangle. Story is: sweep happened, MSS confirmed the fill, price returns to that fill range.

Not this: a fair value gap. Not this: every demand/supply box. v1 block: `order_block`.

---

## Execution recipe (TJR)

### Execution ladder

How the five blocks sequence. Safest at the bottom. Not a sixth pattern.

1. Sweep + MSS (BOS) — aggressive, top of the move.
2. Missed that → wait for the order block (origin of the sweep).
3. Missed that → wait for an FVG tap in the new direction, then lower-timeframe MSS.
4. Beginner default: sweep + MSS + (order block or FVG) **and** equilibrium (discount for longs, premium for shorts).

Still no trade unless daily / higher-timeframe bias agrees. For NQ and ES, New York AM is the session that usually builds the daily candle.

### Invalidation stop

The stop belongs **beyond the sweep extreme**, plus a small buffer for spread, not only beyond the entry candle or the FVG. If that distance kills R:R, the trade is skipped, not “stopped at the order block instead,” unless a spec names that weaker stop on purpose.

---

## Slang to normalize

Do not store these as extra block types. Map them to the rows above.

| Slang | Means |
| --- | --- |
| BISI / bissy | Bullish FVG |
| SIBI / cibby | Bearish FVG |
| CISD | MSS |
| BOS / break of structure | MSS |
| Accumulation area | Order block |
| Liquidity void | Fair value gap |
| Potential (after a sweep) | Unconfirmed until MSS |
| Confirmation | Body-close MSS |
| Unicorn | FVG overlapping a breaker (breaker is not defined yet) |
| Mech model | A named entry recipe, not a pattern |
| Turtle soup | Sweep, until a dedicated block exists |
| Failure swing | Building block of LRL |
| Confluence | More than one confirmed term on the same idea; not a block |

---

## v1 vs later

**v1 engine blocks already in the spec:** `session_levels`, `liquidity_sweep`, `fair_value_gap`, `swing_points`, `market_structure_shift`, `order_block`, `inverse_fvg`, `equilibrium`.

**Confirmed language, not coded yet:** LRL, EQH/EQL, data wick, devil’s mark, NDOG, SMT, condition, news blackout, execution ladder (recipe, not a block), prominent swing length filter.

**Rejected as v1 blocks:** breaker, unicorn, mech model, turtle soup as its own type.
