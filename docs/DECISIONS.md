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
