# Decisions

## 2026-10-15

- We chose raw front-month prices for fair value gaps, liquidity sweeps, and session levels because a back-adjusted continuous contract shifts older prices by the roll gap and can create or erase those patterns. A back-adjusted series can be added later for trend research. It is not the default for these blocks.
- We chose a recommended paper period of 5 trading days and 20 completed trades, with a warning and one logged confirmation if the user goes live sooner, because the wait should be shown and the user must be able to skip it on purpose.
- We chose to leave the daily-loss kill switch and the micro-contract size cap on after that skip because those are the protections that remain once the wait is skipped.
- We chose `.cursor/rules/*.mdc` as the only rules location because that is the format Cursor loads. A second copy at `.cursorrules` would drift.
- We chose to put `after` and `within_bars` on the entry rule because each building block has to stay a pure function that can be fixture-tested on a chart by itself.
- We chose separate required fields, `limit_through_ticks` (minimum 1) and `market_slippage_ticks`, because trading through a limit is the fill condition. Adding slippage on top of that same limit would charge the cost twice. The fill price of a limit is the limit.
- We chose a JSON Schema generated from the Pydantic model as the web app's validator because the web server cannot import Python. The worker still validates with Pydantic. TypeScript types are generated from the same model.
- We chose one position in v1, all contracts in and all contracts out, because scale-in, scale-out, and flipping need their own fill rules. A new signal while a trade is open is ignored.
- We chose ISO weekdays, Monday 1 through Sunday 7, because a Sunday-equals-zero clock would shift every session by a day.
- We chose to return a running job to the queue after the worker timeout and to mark it dead after three attempts because a crashed worker must not hold a job forever.
- We chose phase-1 parity as vectorized detection versus the event-driven simulator on the same fixtures because the broker path does not exist yet and the two engine paths still have to agree.
- We chose half-open session windows on the bar's open time, start included and end excluded, because each bar has to belong to one window. A window whose end clock is at or before its start clock crosses midnight and belongs to the day it started.
- We chose the stop fill as the worse of the gap-through open and the slippage-adjusted stop because a small gap must not get a better price than the slippage allowance. A gap that is already worse than that allowance fills at the open.
- We chose that limit and stop orders cannot fill on the signal bar, and that a market order fills at the next bar's open, because the signal bar's close is never a fill. A stop entry fills at the next open only when that open is already through the stop. Otherwise it uses the stop-fill rule once price trades through it.
- We chose an explicit `entry.side` of long or short because the engine must not infer the trade direction from the fair value gap.
- We chose to reject a stop that sits on the wrong side of the entry fill because the engine must not quietly flip it.
- We chose to count `within_bars` and `expire_bars` in signal-timeframe bars because on a 15-minute strategy, 10 bars means two and a half hours.
- We chose to require a session name on `time_stop` and on `max_trades_per_session` because a spec can contain more than one session.
- We chose to mark the open trade at the last closed bar's close for the daily-loss check, and to flatten at the next bar's open if the limit is hit, because the check has to use a closed bar. A gap can still carry the loss past the limit.
- We chose to keep the original inverse-FVG example in the spec, labeled as a future shape, because that block is not one of the first three and a v1 spec that names it would be invalid.

## 2026-10-19

- We chose PB Trading’s ICT for Dummies (EP. 1, 3–10) as the language pack in `docs/GLOSSARY.md` because the trader approved every draft from that bootcamp before any term was written down. EP. 2 (psychology) was not in the batch.
- We chose one lab meaning per term, with aliases mapped in the glossary, because English-to-spec translation fails if “sweep,” “MSS,” and “FVG” have two definitions.
- We chose to distinguish a liquidity sweep from a market structure shift because the same wick cannot mean both. A sweep is price trading through a swing high or low. An MSS is a body close beyond the last higher low or lower high. This replaces the earlier idea that a sweep completes only on a close back through the level.
- We chose previous-day high and low as the prior daily candle, not cash 09:30–16:00 New York, because that is the PB meaning of PDH/PDL that was approved. A spec may still name `cash_rth` when the English says “cash session” or “RTH.”
- We chose wick-to-wick fair value gaps with no size filter in the default English reading (`min_size_ticks` 0) because the approved lesson said overlap of candles 1 and 3 is the test and size does not matter. A spec may still set a positive `min_size_ticks` as an explicit filter.
- We chose “used up” for a fair value gap as: a tap is a fill; a body close through the gap inverts it. We did not use the midpoint rule. Inverse FVG stays a future block until it has fixture tests.
- We chose New York AM (09:30–11:00 America/New_York, with 08:30 optional) as the default kill zone for NQ and ES because the approved time lesson tells beginners to master that session.
- We chose not to recode `docs/SPEC.md` in this session because the task was to freeze language, not to change the engine contract. The next spec-lock session must copy these four forks into SPEC.md so the Pydantic model cannot drift.
- We chose TJR’s Boot Camp as a second language source, stored as reasoning in `research/TJR-BOOTCAMP.md` and as extra glossary rows only where TJR names a new object, because two teachers describing the same wick must not produce two engine meanings.
- We chose to keep the three-candle swing as the lab default and to treat TJR’s two-candle high/low as an optional later `swing_definition`, because the PB fractal was already confirmed and a two-candle swing would fire more often on the same chart.
- We chose BOS / break of structure as aliases of MSS, not a second block, because TJR’s body-close-beyond-the-last-swing is the same rule as the confirmed MSS row. Sweep stays potential; BOS stays confirmation.
- We chose order block as the impulsive leg that caused the sweep, one per new trend per timeframe, first retrace tool after a missed sweep+MSS, because that is the object PB did not give us as a first-class term. It stays uncoded until labeled chart fixtures exist. We did not treat FVG and order block as the same box.
- We chose TJR’s execution ladder (sweep+MSS, then order block, then FVG, then FVG/OB plus equilibrium) as recipe language, not a sixth pattern, because the engine still evaluates named blocks in `when` order.
- We chose the default stop for this language as invalidation beyond the sweep extreme plus a spread buffer, because a stop only beyond the FVG can keep a trade alive after the idea is already dead.
- We chose not to put TJR psychology / ego / “how to take a loss” days into the glossary because they are not patterns the engine can test.
- We chose to copy the glossary forks into `docs/SPEC.md` and close the eleven open choices there because the engine README refused to start until that contract matched the language pack.
- We chose wick-to-wick fair value gaps, every overlapping window kept, no extra middle-candle size test, and `min_size_ticks` default 0 because that is the confirmed FVG meaning.
- We chose sweep completion as a trade through the level, with `confirm_bars` ignored if present, because a close back through is MSS, not the sweep.
- We chose previous-day high and low as the prior CME equity session 18:00–17:00 America/New_York because that is the confirmed daily candle. Cash RTH remains a named session when English says cash or RTH.
- We chose both `prior_completed` and `developing` session levels in v1 because they are different tools.
- We chose to store the sweep extreme from the finest bars inside the signal candle when fill data exists because a 15-minute high can hide the stop.
- We chose to leave `news_open_slippage_ticks` stored and off because no news window is coded yet.
- We chose the daily-loss reset at 18:00 America/New_York because that is the CME equity reopen.
- We chose to allowlist `Block.type` to `session_levels`, `liquidity_sweep`, and `fair_value_gap` first because those three could ship on session/PDH levels alone. The trader later asked to spec the rest of the core glossary objects.
- We chose polars and pyarrow for synthetic bar fixtures and parquet because the approved engine plan needs columnar bars before Databento or DuckDB.
- We chose the `tzdata` package because Windows Python’s `zoneinfo` has no IANA database, and session clocks are America/New_York with daylight saving.
- We chose to remove the `validate_stop_offset_ticks_non_negative` model validator because `StopExit.offset_ticks = Field(ge=0)` already rejects negatives before any model validator runs, so the validator was unreachable and its "wrong side" message was misleading. The full protective-side rule (SPEC.md L169) compares the stop to the entry fill price and is deferred to Phase 2 fill simulation; it is recorded as a skipped test (`TestDeferredRules.test_stop_protective_side_enforced`) so the gap stays visible rather than passing silently.
- We chose to keep `validate_fill_resolution_granularity` as a defensive guard even though it is currently unreachable, because SPEC.md L136 limits `fill_resolution` to `1s` or `1m` and the coarsest fill (`1m`) equals the finest signal (`1m`), so no legal pair can violate it. The old `coarse_fill_resolution.json` fixture used an illegal value (`15m`) and therefore tested enum rejection, not the granularity rule; it is renamed `invalid_fill_resolution_value.json`, and a parametrized test now asserts every legal (signal, fill) pair is accepted. The unreachable granularity case is a skipped test so the limitation is explicit.
- We chose to spec and code `swing_points`, `market_structure_shift`, `order_block`, `inverse_fvg`, and `equilibrium` because those are the glossary objects that turn a sweep into the TJR ladder. SMT, LRL, equal highs, data wick, devil’s mark, NDOG, news, breaker, and unicorn stay language-only.
- We chose a three-candle swing with a strict higher/lower middle wick because that is the confirmed lab default. Two-candle swings stay uncoded.
- We chose MSS as a body close beyond the latest opposite swing, one event per swing occurrence, because a wick through that swing is already a sweep.
- We chose an order block as the leg from the origin swing to the sweep extreme, born on the confirming MSS, one per new trend, because that is the TJR cause-leg, not a demand box and not an FVG.
- We chose inverse FVG as a later body close through the gap’s far edge because a wick into the zone is respect, not inversion.
- We chose equilibrium as a signal-bar location filter on the latest swing range midpoint because it is a location, not a sixth pattern.

## 2026-10-31

- We chose the front month from the prior completed CME equity session (18:00–17:00 America/New_York) because the contract has to be known at the session open. Using the session's own volume would look ahead.
- We chose not to trade the first session in a file because it has no prior session to rank. That session's volume picks the next front month.
- We chose to break a first-session tie toward the nearer expiry, and to roll only when a later expiry's prior-session volume is strictly higher, because an expiring contract's volume blip must not pull signals back onto the old prices.
- We chose to keep each front-month segment on that outright's own bars, plus one prior session of the same outright, because prior-day high has to exist and a roll gap must not print a fair value gap.
- We chose Databento GLBX.MDP3 parent `NQ.FUT` for definitions, then raw outright `ohlcv-1s` (or `ohlcv-1m`) written to one Parquet file. DuckDB reads it. Polars builds the signal bars. `databento` and `duckdb` were added because the stack already named them.
- We chose to store bar opens as UTC without a timezone marker because DuckDB's timezone reader on Windows asked for `pytz`, and every bar open in this lab is UTC.
- We chose a one-digit contract year in the window from the bar's year minus one through eight years ahead, because Globex raw symbols look like `NQZ6`.
- We chose to resolve a stop and a target on the fill bars when those bars are finer than the signal, and to keep counting `expire_bars` in signal bars, because the sample strategy is 15-minute signals and 1-second fills. One fill bar that contains both still fills the stop.
- We chose to refuse a Databento quote over $5 unless `--max-cost` is raised, because the first download should not spend more than that on its own.
