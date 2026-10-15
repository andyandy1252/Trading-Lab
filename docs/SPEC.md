# Strategy spec

Version 1.0. This file is the contract for the Pydantic model. Users never see it. They see the same rules as plain-English cards.

A spec that omits a required field is rejected. The engine does not fill in a hidden default. The translator may suggest the starter numbers in this document, and those numbers must appear on the rule card before a backtest runs.

The open choices at the bottom are not decided. The sample strategy below is an illustration, not a default strategy.

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

Signals read the raw outright of the front month, the contract whose volume is higher. Prices are not back-adjusted. The exact volume-crossover rule is fixed when the data task is built. A fair value gap, sweep, or session level that would need bars from two contracts does not fire.

## Sample

A long after a sweep of the highs cannot use that high as its protective stop, because the high is above the entry. This illustration is a short. It sweeps the prior cash-session high, waits for a bearish fair value gap, sells a limit at the gap midpoint, and puts the stop 4 ticks above the sweep extreme. Tell me if you wanted the long version, and which price the stop should use. That question is also listed at the bottom.

`cash_rth` below is an example clock on this strategy. It is not a decision about what "prior day" means.

Two fields are missing on purpose until you answer the open choices: how a fair value gap is measured, and when it is used up.

```json
{
  "spec_version": "1.0",
  "name": "NQ prior high sweep then bearish FVG",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "sessions": [
    {
      "name": "cash_rth",
      "tz": "America/New_York",
      "start": "09:30",
      "end": "16:00",
      "days": [1, 2, 3, 4, 5]
    },
    {
      "name": "ny_am",
      "tz": "America/New_York",
      "start": "09:00",
      "end": "11:00",
      "days": [1, 2, 3, 4, 5]
    }
  ],
  "blocks": [
    {
      "id": "cash_rth",
      "type": "session_levels",
      "params": {
        "session": "cash_rth",
        "levels": ["high", "low"],
        "which": "prior_completed"
      }
    },
    {
      "id": "sweep",
      "type": "liquidity_sweep",
      "params": {
        "level": "cash_rth.high",
        "penetration_ticks": 1,
        "confirm_bars": 2
      }
    },
    {
      "id": "fvg",
      "type": "fair_value_gap",
      "params": {
        "direction": "bearish",
        "min_size_ticks": 8
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
    "source_prompt": "Sell NQ after the prior cash high is swept and a bearish fair value gap prints.",
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
- `news_open_slippage_ticks`: a higher adverse tick count for market and stop fills. When this higher number applies is an open choice below. Until you define that window, the engine has nowhere to turn it on.
- `limit_through_ticks`: how far price must trade past a limit before the limit fills. The minimum is 1. The fill price is still the limit. This number is the fill condition. It is not added again as slippage.

Starter numbers the translator may show on the card: ES, 1 tick of market slippage per side. NQ, 1 tick normally and 3 ticks around the open and major news. Commission about $2.50 to $4.50 per side. The strategy stores the exact numbers the user accepts.

## Entries

`entry.side` is `long` or `short`. The engine does not infer the side from the fair value gap.

`entry.when` lists the events that must all have happened. A later event may set `after` to an earlier event id and `within_bars` to a positive integer. `within_bars` counts signal-timeframe bars after the earlier event's bar. A value of 20 allows the later event on the 20th bar after that bar. The same bar does not satisfy `after`.

The signal is complete at the close of the bar where the last required event prints. No order can fill on that signal bar.

- A `market` order fills at the next bar's open. A long is filled at the open plus `market_slippage_ticks`. A short is filled at the open minus those ticks. The news/open slippage replaces the normal slippage only in the window you define.
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

`daily_loss_stop_usd` is checked against closed-trade PnL plus the open trade marked at the last closed bar's close. The check runs before a new entry and after each closed bar while a trade is open. On a breach, the engine flattens at the next bar's open with market slippage and blocks new entries for the rest of that day. A gap may carry the realized loss past the limit. The reset clock for "that day" is an open choice below.

## Session levels

Type: `session_levels`.

The block points at a session name and reports the levels you list. `levels` is a required non-empty list drawn from `high`, `low`, `midpoint`, and `open`.

`which` is required:

- `prior_completed`: the latest occurrence of that session that has fully ended before this bar's open.
- `developing`: the current occurrence, using closed bars only. Whether v1 ships both values is an open choice. The field exists so the two meanings cannot be confused.

`asof` is an optional clock time in the session timezone. Only bars whose open is at or after the session start and strictly before `asof` are included. The level then freezes. This is how "the high as of 10:00" is written. On a 15-minute chart, the 09:45 bar is included in an `asof` of 10:00 because that bar opened before 10:00. The 10:00 bar is not.

Reported fields, and only the ones requested:

- `high`: highest high of the included bars.
- `low`: lowest low of the included bars.
- `midpoint`: the average of `high` and `low`. Requesting it requires both high and low in the included bars.
- `open`: the open of the first included bar.
- `session_start`: the start timestamp of the occurrence that was measured.

If the window contains no bars, the block reports nothing for that occurrence. A sweep of a missing level does not fire.

On the signal timeframe, the high and low are the high and low of the included closed signal bars. Using a finer price inside those bars for the stop extreme is an open choice.

## Liquidity sweep

Type: `liquidity_sweep`.

The block takes a level that another block already computed, such as `cash_rth.high`. It does not compute the session itself.

Working definition, with the close-back rule still waiting on you:

- `penetration_ticks` is a required whole number, zero or greater. Zero means a tag of the level qualifies. One means price must trade at least one tick past it.
- Buy-side sweep of a high: a closed bar's high is greater than or equal to `level + penetration_ticks * tick_size`.
- Sell-side sweep of a low: a closed bar's low is less than or equal to `level - penetration_ticks * tick_size`.
- `confirm_bars` is a required whole number, zero or greater. It is how many signal bars after the penetrating bar may still complete the sweep. Zero means the penetrating bar itself must complete it.
- Recommended completion: the bar closes strictly back through the level. For a high, the close is below the level. For a low, the close is above the level. A close that merely tags the level does not complete the sweep. The wick-only alternative is in the open choices.

The extreme is the furthest price from the penetrating bar through the confirmation bar, inclusive. For a high sweep that is the highest high. For a low sweep that is the lowest low. Which data series supplies that price is an open choice.

Reported fields:

- `level`: the price that was swept.
- `extreme`: the furthest price of the sweep.
- `side`: `buy_side` if the high was run, `sell_side` if the low was run. This names the liquidity, not the trade direction.
- `penetration_ticks`: how far the extreme got past the level, in ticks.
- `confirmed_at`: the open time of the confirmation bar.

## Fair value gap

Type: `fair_value_gap`.

Three consecutive closed signal bars, A then B then C. C is the latest. The pattern is evaluated once C has closed. Each position of the window can produce its own gap. Whether overlapping gaps are all kept is an open choice.

The untraded band sits between candle A and candle C. Candle B is the middle bar. The recommended measurement uses wicks. The body alternative is an open choice.

Recommended wick measurement:

- Bullish: the high of A is below the low of C. The zone runs from the high of A up to the low of C. Price left that band below the market. The near edge is the low of C. The far edge is the high of A.
- Bearish: the low of A is above the high of C. The zone runs from the high of C up to the low of A. Price left that band above the market. The near edge is the high of C. The far edge is the low of A.

`direction` is required and is `bullish` or `bearish`. `min_size_ticks` is required and is a whole number, zero or greater. The zone height in ticks must be at least that large. The recommended rule has no extra size test on candle B.

The block does not know whether a sweep happened. The entry rule handles that.

Reported fields:

- `direction`
- `near_edge`
- `far_edge`
- `midpoint`, the average of the two edges
- `size_ticks`
- `formed_at`, the open time of candle C

When the gap is "used up" is an open choice. Until you pick it, the block reports the zone and does not delete it.

## Later shape: inverse fair value gap

This was the original example. `inverse_fvg` is not a v1 block. The JSON is a picture of a future spec, and the engine will reject it today.

```json
{
  "spec_version": "1.0",
  "name": "NQ NY AM sweep then inverse FVG",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "sessions": [
    {
      "name": "ny_am",
      "tz": "America/New_York",
      "start": "09:00",
      "end": "11:00",
      "days": [1, 2, 3, 4, 5]
    }
  ],
  "blocks": [
    {
      "id": "sweep",
      "type": "liquidity_sweep",
      "params": {
        "level": "session_high",
        "session_ref": "10:00",
        "confirm_bars": 2
      }
    },
    {
      "id": "ifvg",
      "type": "inverse_fvg",
      "params": {
        "direction": "bearish",
        "min_size_ticks": 8,
        "after": "sweep",
        "within_bars": 20
      }
    }
  ],
  "entry": {
    "when": ["sweep", "ifvg"],
    "order": "limit",
    "price": "ifvg.midpoint",
    "expire_bars": 10
  },
  "exit": {
    "stop": { "ref": "sweep.extreme", "offset_ticks": 4 },
    "target": { "type": "rr", "value": 2.0 },
    "time_stop": "session_end"
  },
  "risk": {
    "contracts": 1,
    "max_trades_per_session": 2,
    "daily_loss_stop_usd": 500
  }
}
```

In v1 that 10:00 cutoff belongs on a session-levels block as `asof`, and `after` belongs on the entry. The future inverse-FVG block will be defined on its own, with fixture tests, before any spec is allowed to name it.

## Open choices

These are not in the decision log. I need your call before any of the three blocks is coded. The recommendation is the one I will use if you say yes.

1. **Fair value gap measurement.** Wick to wick, using highs and lows (recommended). Or candle bodies only, using the top and bottom of each body (`max(open, close)` and `min(open, close)`). Body version: a bullish gap is the body top of A below the body bottom of C.

2. **When is a fair value gap used up?** This will be a required parameter. Options: any trade into the zone, a trade to the midpoint, or a trade at least one tick past the far edge. I need the default the translator should put on the card.

3. **Overlapping gaps.** Keep every three-candle window that qualifies (recommended), or keep only the largest gap when several overlap.

4. **Middle candle.** The empty band is the only size test (recommended). The alternative is an extra minimum size on candle B.

5. **Sweep completion.** A close strictly back through the level is required (recommended). The alternative is a wick through the level with no close back. If you want the close-back rule, a close that only tags the level does not count.

6. **What "prior day" means.** I will not guess. Options: the cash session 9:30–16:00 New York, the electronic day session ending at 16:15 or at 17:00, or the full CME day from 18:00 to 17:00 New York. A strategy can always name its own clock. This choice is the default meaning of "prior day" when you say it in English.

7. **Developing levels.** Ship both `prior_completed` and `developing` in v1 (recommended). They are different tools: yesterday's high, and the high of the session that is still open.

8. **Stop extreme.** Detect the sweep on the signal timeframe. Store the extreme from the finest data available inside those bars (recommended), so a 15-minute bar does not hide the real high that the stop is built from. The alternative is to use the signal bar's own high or low.

9. **News and open slippage window.** The spec has a higher tick count. I will not invent the minutes around the open, or what counts as major news. The economic calendar is later work. Until you name the window, only `market_slippage_ticks` can apply.

10. **Daily-loss reset.** When does the daily loss counter go back to zero? Recommendation: 18:00 America/New_York, when the CME equity session reopens. Tell me if you want midnight New York, or the cash open, instead.

11. **Sample direction.** The illustration sells after a high sweep and a bearish fair value gap, so the stop can sit above the sweep extreme. Say if you want a long sample instead, and which price is the stop.
