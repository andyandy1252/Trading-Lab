# Strategy spec

Version 1.0. This file is the contract for the Pydantic model. Users never see it. They see the same rules as plain-English cards.

A spec that omits a required field is rejected. The engine does not fill in a hidden default. The translator may suggest the starter numbers in this document, and those numbers must appear on the rule card before a backtest runs.

The locked choices at the bottom are the lab defaults. The sample strategy below is an illustration, not a default strategy. English maps through `docs/GLOSSARY.md` into this contract.

## Instruments

The strategy names one instrument. Tick size and dollar value live in this table, not in the strategy.

| Instrument | Tick size | Dollars per tick | Dollars per point |
| --- | --- | --- | --- |
| NQ | 0.25 | 5.00 | 20.00 |
| MNQ | 0.25 | 0.50 | 2.00 |
| ES | 0.25 | 12.50 | 50.00 |
| MES | 0.25 | 1.25 | 5.00 |

Confirm these multipliers against the vendor instrument definition when data is connected.

Long PnL in dollars:

`(exit_price - entry_price) / tick_size * dollars_per_tick * contracts - commission_per_side_usd * contracts * 2`

Short PnL uses `(entry_price - exit_price)` in that same formula. Commission is charged once on the entry and once on the exit.

## Time

Bar timestamps are the bar open time, stored in UTC. Session clocks use the session's IANA timezone, so daylight saving time is part of the clock.

Weekdays are ISO numbers: Monday is 1, Sunday is 7.

A session window is half-open. A bar belongs to the session when its open time, in the session timezone, is greater than or equal to `start` and strictly before `end`. The weekday filter looks at the session's start date in that timezone. A window whose `end` clock is less than or equal to its `start` clock crosses midnight and belongs to the day it started. Sunday 18:00 New York is weekday 7.

Only closed bars can create a level, a gap, or a fill. The bar that is still forming is ignored.

## Prices

Signals read the raw outright of the front month. Prices are not back-adjusted. Spreads are not outrights.

The volume day is the CME equity session, 18:00–17:00 America/New_York, the same window as `cme_eth`. A bar in the 17:00–18:00 halt does not count, and neither does a bar outside that session.

The front month for a session is the outright with the highest volume in the prior completed session. The first session in a file has no prior session, so it is not traded. Its volume chooses the front month for the next session. A tie goes to the nearer expiry. After that, the front month changes only when a later-expiring outright printed strictly more volume in the session that just ended than the incumbent did. It never rolls backward.

A fair value gap, sweep, or session level is computed on one outright. The bars for a front-month segment include that outright's prior session, so the prior-day high exists, and they include no bar from another outright. A pattern that would need both does not fire.

## Sample

A long after a sweep of the highs cannot use that high as its protective stop, because the high is above the entry. This illustration is a short. It sweeps the prior daily high (CME equity session 18:00–17:00 New York), waits for a bearish fair value gap, sells a limit at the gap midpoint, and puts the stop 4 ticks above the sweep extreme.

Fair value gaps are wick-to-wick. A sweep completes when price trades through the level; a body close the other way is MSS, not the sweep. `min_size_ticks` in this sample is 0.

```json
{
  "spec_version": "1.0",
  "name": "NQ prior high sweep then bearish FVG",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "sessions": [
    {
      "name": "cme_eth",
      "tz": "America/New_York",
      "start": "18:00",
      "end": "17:00",
      "days": [7, 1, 2, 3, 4]
    },
    {
      "name": "ny_am",
      "tz": "America/New_York",
      "start": "09:30",
      "end": "11:00",
      "days": [1, 2, 3, 4, 5]
    }
  ],
  "blocks": [
    {
      "id": "pdh",
      "type": "session_levels",
      "params": {
        "session": "cme_eth",
        "levels": ["high", "low"],
        "which": "prior_completed"
      }
    },
    {
      "id": "sweep",
      "type": "liquidity_sweep",
      "params": {
        "level": "pdh.high",
        "penetration_ticks": 1
      }
    },
    {
      "id": "fvg",
      "type": "fair_value_gap",
      "params": {
        "direction": "bearish",
        "min_size_ticks": 0
      }
    }
  ],
  "entry": {
    "side": "short",
    "when": [
      { "id": "sweep" },
      { "id": "fvg", "after": "sweep", "within_bars": 20 }
    ],
    "order": "limit",
    "price": "fvg.midpoint",
    "expire_bars": 10
  },
  "exit": {
    "stop": { "ref": "sweep.extreme", "offset_ticks": 4 },
    "target": { "type": "rr", "value": 2.0 },
    "time_stop": { "type": "session_end", "session": "ny_am" }
  },
  "risk": {
    "contracts": 1,
    "session": "ny_am",
    "max_trades_per_session": 2,
    "daily_loss_stop_usd": 500
  },
  "costs": {
    "commission_per_side_usd": 2.5,
    "market_slippage_ticks": 1,
    "news_open_slippage_ticks": 3,
    "limit_through_ticks": 1
  },
  "meta": {
    "source": "english",
    "source_prompt": "Sell NQ after the prior day high is swept and a bearish fair value gap prints.",
    "parent_version": null
  }
}
```

`fill_resolution` may be `1s` or `1m`. It must be the same size as the signal timeframe or finer. One-second fills are the goal. One-minute fills are allowed.

Allowed signal timeframes for v1: `1m`, `2m`, `5m`, `15m`, `30m`, `1h`, `4h`.

Block ids and session names are unique, lowercase, and use underscores. An entry or exit reference has the form `block_id.field` and must name a numeric field that the block actually reports.

## Costs

Every spec includes `costs`. The engine rejects the spec without it.

- `commission_per_side_usd`: dollars charged per contract on the entry, and the same amount again on the exit.
- `market_slippage_ticks`: adverse ticks added to market and stop fills.
- `news_open_slippage_ticks`: a higher adverse tick count for market and stop fills. The news and open window is not coded in v1. The field is stored. Only `market_slippage_ticks` applies.
- `limit_through_ticks`: how far price must trade past a limit before the limit fills. The minimum is 1. The fill price is still the limit. This number is the fill condition. It is not added again as slippage.

Starter numbers the translator may show on the card: ES, 1 tick of market slippage per side. NQ, 1 tick normally and 3 ticks around the open and major news. Commission about $2.50 to $4.50 per side. The strategy stores the exact numbers the user accepts.

## Entries

`entry.side` is `long` or `short`. The engine does not infer the side from the fair value gap.

`entry.when` lists the events that must all have happened. A later event may set `after` to an earlier event id and `within_bars` to a positive integer. `within_bars` counts signal-timeframe bars after the earlier event's bar. A value of 20 allows the later event on the 20th bar after that bar. The same bar does not satisfy `after`.

The signal is complete at the close of the bar where the last required event prints. No order can fill on that signal bar.

- A `market` order fills at the next bar's open. A long is filled at the open plus `market_slippage_ticks`. A short is filled at the open minus those ticks. News/open slippage stays stored and off.
- A `limit` order starts working on the next bar. `price` is a `block_id.field` reference. `expire_bars` counts signal-timeframe bars, starting with the first bar after the signal bar. The order is checked on every fill-resolution bar inside that life. A buy limit fills only when price trades at or below `limit - limit_through_ticks * tick_size`. A sell limit fills only when price trades at or above `limit + limit_through_ticks * tick_size`. The fill price is the limit. If the bar opens already through the limit, the fill is still the limit.
- A `stop` order to enter starts working on the next bar and uses the stop-fill rule below. `expire_bars` is required for `limit` and `stop`. A `market` order does not take `expire_bars`.

v1 holds one position, all contracts in and all contracts out. A new signal while a trade is open is ignored. There is no scale-in, scale-out, or flip.

## Exits

The stop reference must sit on the protective side of the entry fill. For a long, the stop price is `ref - offset_ticks * tick_size`, and that price must be below the entry fill. For a short, the stop price is `ref + offset_ticks * tick_size`, and that price must be above the entry fill. `offset_ticks` is a required whole number, zero or greater. A stop on the wrong side is rejected.

Stop fills:

- If the bar opens already through the stop, the fill is the worse of the open and the slippage-adjusted stop. A gap larger than the slippage allowance fills at the open. A gap smaller than that allowance still pays the full slippage.
- If the bar opens on the safe side and later trades through the stop, the fill is the slippage-adjusted stop.

The only target type in v1 is `rr`. A value of `2.0` means the target sits twice as far from the entry fill as the stop does. The distance is measured from the actual entry fill.

A target is a limit. It fills only after price trades through it by `limit_through_ticks`, and the fill price is the target. A gap through the target fills at the target.

If the stop and the target both fall inside one fill bar and that bar cannot prove which came first, the stop fills and the target does not.

`time_stop` flattens with a market order at the first fill bar whose open is at or after the named session's end, plus adverse slippage.

## Risk

`contracts` is a whole number of 1 or more.

`max_trades_per_session` counts filled entries whose signal bar falls in the named `risk.session`. Ignored signals do not count. The session name is required.

`daily_loss_stop_usd` is checked against closed-trade PnL plus the open trade marked at the last closed bar's close. The check runs before a new entry and after each closed bar while a trade is open. On a breach, the engine flattens at the next bar's open with market slippage and blocks new entries for the rest of that day. A gap may carry the realized loss past the limit. The day resets at 18:00 America/New_York, when the CME equity session reopens.

## Session levels

Type: `session_levels`.

The block points at a session name and reports the levels you list. `levels` is a required non-empty list drawn from `high`, `low`, `midpoint`, and `open`.

`which` is required:

- `prior_completed`: the latest occurrence of that session that has fully ended before this bar's open.
- `developing`: the current occurrence, using closed bars only, including this bar once it has closed. v1 ships both values. They are different tools: yesterday's high, and the high of the session that is still open.

Previous-day high and low are this block on the CME equity session 18:00–17:00 America/New_York (`cme_eth` in the sample), `which: prior_completed`. Cash 09:30–16:00 is a named session only when English says cash or RTH.

`asof` is an optional clock time in the session timezone. Only bars whose open is at or after the session start and strictly before `asof` are included. The level then freezes. This is how "the high as of 10:00" is written. On a 15-minute chart, the 09:45 bar is included in an `asof` of 10:00 because that bar opened before 10:00. The 10:00 bar is not.

Reported fields, and only the ones requested:

- `high`: highest high of the included bars.
- `low`: lowest low of the included bars.
- `midpoint`: the average of `high` and `low`. Requesting it requires both high and low in the included bars.
- `open`: the open of the first included bar.
- `session_start`: the start timestamp of the occurrence that was measured.

If the window contains no bars, the block reports nothing for that occurrence. A sweep of a missing level does not fire.

On the signal timeframe, the high and low are the high and low of the included closed signal bars. Detect sweeps on the signal timeframe. Store the extreme from the finest bars inside those signal candles when fill data exists. When signal and fill are the same timeframe, the signal bar high or low is the extreme.

## Liquidity sweep

Type: `liquidity_sweep`.

The block takes a level that another block already computed, such as `cash_rth.high`. It does not compute the session itself.

Completion is a trade through the level. A close back through the level is not required. That close is `market_structure_shift`.

- `penetration_ticks` is a required whole number, zero or greater. Zero means a tag of the level qualifies. One means price must trade at least one tick past it.
- Buy-side sweep of a high: a closed bar's high is greater than or equal to `level + penetration_ticks * tick_size`.
- Sell-side sweep of a low: a closed bar's low is less than or equal to `level - penetration_ticks * tick_size`.
- The penetrating bar completes the sweep. `confirm_bars` may still appear in JSON for older specs and is ignored.
- A later bar that is still through the same occurrence is not a new sweep. A new sweep of the same level fires only after a bar that did not trade through, then a bar that does (a recross). A new session occurrence is a new level.

The extreme is the furthest price on the penetrating bar. For a high sweep that is that bar's high. For a low sweep that is that bar's low. When finer fill bars exist inside the signal candle, the extreme is the finest high or low inside it.

Reported fields:

- `level`: the price that was swept.
- `extreme`: the furthest price of the sweep.
- `side`: `buy_side` if the high was run, `sell_side` if the low was run. This names the liquidity, not the trade direction.
- `penetration_ticks`: how far the extreme got past the level, in ticks.
- `confirmed_at`: the open time of the confirmation bar.

## Fair value gap

Type: `fair_value_gap`.

Three consecutive closed signal bars, A then B then C. C is the latest. The pattern is evaluated once C has closed. Each position of the window can produce its own gap. Keep every qualifying window. Overlapping gaps are all kept.

The untraded band sits between candle A and candle C. Candle B is the middle bar. Measurement is wick to wick. There is no extra size test on candle B.

Wick measurement:

- Bullish: the high of A is below the low of C. The zone runs from the high of A up to the low of C. Price left that band below the market. The near edge is the low of C. The far edge is the high of A.
- Bearish: the low of A is above the high of C. The zone runs from the high of C up to the low of A. Price left that band above the market. The near edge is the high of C. The far edge is the low of A.

If the wicks of A and C touch or overlap, there is no gap.

`direction` is required and is `bullish` or `bearish`. `min_size_ticks` is required and is a whole number, zero or greater. Default English reading is 0. The zone height in ticks must be at least that large.

The block does not know whether a sweep happened. The entry rule handles that.

A tap into the zone is a fill of the void. The detector still reports the zone. It does not delete the gap on first tap. A body close through the gap is `inverse_fvg`.

Reported fields:

- `direction`
- `near_edge`
- `far_edge`
- `midpoint`, the average of the two edges
- `size_ticks`
- `formed_at`, the open time of candle C

## Swing points

Type: `swing_points`.

Three consecutive closed signal bars. Candle color does not matter.

- Swing high: the middle high is strictly above the high on each side. Price is that middle high.
- Swing low: the middle low is strictly below the low on each side. Price is that middle low.

`kind` is required and is `high`, `low`, or `both`. A swing is confirmed on the third bar's close. Each bar reports the latest confirmed swing of the requested kind. `session_start` is the open time of the middle candle (the occurrence id for a later sweep).

Reported fields: `high` and/or `low`, `session_start`. A new fractal also emits an event at the confirming bar with `price` and `side`.

This is the lab default three-candle fractal. Two-candle swings are not a v1 switch.

A `liquidity_sweep` may point at `swings.high` or `swings.low` the same way it points at `pdh.high`.

## Market structure shift

Type: `market_structure_shift`.

Aliases in English: MSS, BOS, break of structure, CISD. One block type.

`swings` is a required block id of `swing_points`. `direction` is `bullish`, `bearish`, or `either`.

- Bearish: a body closes strictly below the latest confirmed swing low. Only the most recent swing low counts.
- Bullish: a body closes strictly above the latest confirmed swing high. Only the most recent swing high counts.

A wick through that swing is not an MSS. That wick is a sweep until a body close proves the shift. One MSS per swing occurrence. A recross of the same swing after a bar that did not close beyond it can fire again.

Reported fields: `direction`, `level` (the swing price that was closed through), `confirmed_at`.

## Order block

Type: `order_block`.

The impulsive leg that caused the sweep, born when that sweep is confirmed by MSS. One order block per new trend (the next one appears at the next MSS the other way).

`sweep`, `mss`, and `swings` are required block ids.

- Buy-side sweep then bearish MSS: bearish order block. The up-leg from the last swing low before the sweep to the sweep extreme.
- Sell-side sweep then bullish MSS: bullish order block. The down-leg from the last swing high before the sweep to the sweep extreme.

If the origin swing is missing, the block reports nothing. This is not a fair value gap.

Reported fields: `direction`, `high`, `low`, `midpoint`, `formed_at` (the MSS bar).

## Inverse fair value gap

Type: `inverse_fvg`.

`gap` is a required block id of `fair_value_gap`. `direction` is the **new** direction after inversion: `bullish` or `bearish`.

A body must close through the gap's far edge. A wick into the zone is respect, not inversion.

- A bullish gap inverts when a later close is strictly below `far_edge`. That prints a bearish inverse FVG.
- A bearish gap inverts when a later close is strictly above `far_edge`. That prints a bullish inverse FVG.

The zone edges stay the same. `after` belongs on the entry, not on this block.

Reported fields: `direction`, `near_edge`, `far_edge`, `midpoint`, `size_ticks`, `formed_at` (the close-through bar).

## Equilibrium

Type: `equilibrium`.

Location, not a pattern. `swings` is a required block id of `swing_points`. `location` is `discount`, `premium`, or `equilibrium`.

The dealing range is the latest confirmed swing low to the latest confirmed swing high. Equilibrium is the midpoint. Discount is a close strictly below that midpoint. Premium is a close strictly above it.

This event must occur on the signal bar (it is a location filter, not a later retrace). If both swings are missing, it does not fire.

Reported fields: `eq`, `location`, `high`, `low`.

## Locked choices

Copied from the glossary and the 2026-10-19 plan approval. Do not reopen these in engine code.

1. **Fair value gap measurement.** Wick to wick, using highs and lows.
2. **When is a fair value gap used up?** A tap is a fill of the void. A body close through the far edge is `inverse_fvg`. The original FVG detector still reports the zone and does not delete it on first tap.
3. **Overlapping gaps.** Keep every three-candle window that qualifies.
4. **Middle candle.** The empty band is the only size test. No extra minimum on candle B.
5. **Sweep completion.** Price trades through the level. No close-back required.
6. **What "prior day" means.** The prior CME equity daily candle, 18:00–17:00 America/New_York. A spec may still name cash RTH when English says cash or RTH.
7. **Developing levels.** Both `prior_completed` and `developing` ship in v1.
8. **Stop extreme.** Detect on the signal timeframe. Store the extreme from the finest bars inside those candles when fill data exists.
9. **News and open slippage window.** Stored, off. Only `market_slippage_ticks` applies.
10. **Daily-loss reset.** 18:00 America/New_York.
11. **Sample direction.** Short after a high sweep and a bearish fair value gap.

v1 block types: `session_levels`, `liquidity_sweep`, `fair_value_gap`, `swing_points`, `market_structure_shift`, `order_block`, `inverse_fvg`, `equilibrium`. `breaker`, `unicorn`, and any other type are rejected.
