"""Strict raid, retrace, and inverse-gap setups.

A buy-side sweep (a high) is only a short. A sell-side sweep is only a long.
The opposite fair value gap has to print on that reversal leg, a later bar has
to wick into it without a body close through it, and a fair value gap on the
retrace has to invert back the other way. The inversion bar has to fall in
09:00–11:00 America/New_York, Monday to Friday, and in the same CME session as
the sweep. Pools are three-candle swings on the 15-minute, 1-hour, and 4-hour
charts. Yesterday's hourly liquidity is the 1-hour swings from the prior CME
session, which are already in that 1-hour set.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from engine.bars import Bar
from shared.spec.model import TIMEFRAME_MINUTES
from engine.marketdata.outrights import volume_session_start
from engine.marketdata.outrights import OutrightBar

_NY = ZoneInfo("America/New_York")
_TICK = 0.25
_DOLLARS_PER_TICK = 5.0
_COMMISSION_PER_SIDE = 2.5
_SLIP_TICKS = 1
_STOP_BUFFER_TICKS = 4


@dataclass(frozen=True)
class Pool:
    price: float
    side: str
    available: datetime
    source: str


@dataclass(frozen=True)
class RaidSetup:
    side: str
    signal_time: datetime
    sweep_time: datetime
    sweep_extreme: float
    level: float
    source: str
    gap_far: float = 0.0


@dataclass(frozen=True)
class RaidRules:
    """One locked reading of the same raid sequence.

    The five names below were chosen before the October tape was scored.
    """

    name: str
    sources: tuple[str, ...] = ("15m", "1h", "4h")
    require_respect: bool = True
    window_start: int = 9 * 60
    window_end: int = 11 * 60
    prior_session_only: bool = False
    stop_at: str = "sweep"


BASELINE = RaidRules("Baseline")
VARIANTS: tuple[RaidRules, ...] = (
    BASELINE,
    RaidRules("Higher-timeframe sweep", sources=("1h", "4h")),
    RaidRules("No respect wick", require_respect=False),
    RaidRules("Stop beyond the gap", stop_at="gap"),
    RaidRules(
        "Prior-hour liquidity, 9:30",
        sources=("1h",),
        window_start=9 * 60 + 30,
        prior_session_only=True,
    ),
)


@dataclass(frozen=True)
class RaidTrade:
    side: str
    signal_time: datetime
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    exit_reason: str
    pnl_usd: float
    level: float
    source: str
    sweep_extreme: float


@dataclass
class _Gap:
    index: int
    direction: str
    near: float
    far: float


@dataclass
class _Leg:
    trade_side: str
    sweep_index: int
    sweep_time: datetime
    session: datetime
    extreme: float
    level: float
    source: str
    displacement: _Gap | None = None
    respected: bool = False
    dead: bool = False
    retrace: list[_Gap] = field(default_factory=list)
    used: set[int] = field(default_factory=set)


def _minutes(timeframe: str) -> int:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe {timeframe!r}")
    return TIMEFRAME_MINUTES[timeframe]


def collect_pools(*series: tuple[list[Bar], str]) -> list[Pool]:
    pools: list[Pool] = []
    for bars, timeframe in series:
        step = timedelta(minutes=_minutes(timeframe))
        for i in range(2, len(bars)):
            left, mid, right = bars[i - 2], bars[i - 1], bars[i]
            available = right.ts + step
            if mid.high > left.high and mid.high > right.high:
                pools.append(Pool(mid.high, "buy_side", available, timeframe))
            if mid.low < left.low and mid.low < right.low:
                pools.append(Pool(mid.low, "sell_side", available, timeframe))
    return pools


def _in_entry_window(ts: datetime, start: int = 9 * 60, end: int = 11 * 60) -> bool:
    local = ts.astimezone(_NY)
    if local.isoweekday() > 5:
        return False
    minutes = local.hour * 60 + local.minute
    return start <= minutes < end


def _window_end(ts: datetime, end_minute: int = 11 * 60) -> datetime:
    local = ts.astimezone(_NY)
    hour, minute = divmod(end_minute, 60)
    end_local = datetime.combine(local.date(), time(hour, minute), tzinfo=_NY)
    return end_local.astimezone(timezone.utc)


def _pool_allowed(pool: Pool, session: datetime, rules: RaidRules) -> bool:
    if pool.source not in rules.sources:
        return False
    if rules.prior_session_only and pool.available >= session:
        return False
    return True


def _ny_date(ts: datetime):
    return ts.astimezone(_NY).date()


def _gap_at(bars: list[Bar], index: int) -> _Gap | None:
    if index < 2:
        return None
    first, third = bars[index - 2], bars[index]
    if first.high < third.low:
        return _Gap(index, "bullish", third.low, first.high)
    if first.low > third.high:
        return _Gap(index, "bearish", third.high, first.low)
    return None


def _apply_bar(leg: _Leg, bars: list[Bar], index: int, rules: RaidRules) -> RaidSetup | None:
    if leg.dead:
        return None
    born = _gap_at(bars, index)
    if born is not None and index > leg.sweep_index:
        if leg.trade_side == "short":
            if born.direction == "bearish" and leg.displacement is None:
                leg.displacement = born
            elif born.direction == "bullish" and leg.displacement is not None and index > leg.displacement.index:
                leg.retrace.append(born)
        elif born.direction == "bullish" and leg.displacement is None:
            leg.displacement = born
        elif born.direction == "bearish" and leg.displacement is not None and index > leg.displacement.index:
            leg.retrace.append(born)

    bar = bars[index]
    gap = leg.displacement
    if gap is not None and index > gap.index:
        if leg.trade_side == "short":
            if bar.close > gap.far:
                leg.dead = True
            elif bar.high >= gap.near:
                leg.respected = True
        elif bar.close < gap.far:
            leg.dead = True
        elif bar.low <= gap.near:
            leg.respected = True
    if leg.dead or gap is None:
        return None
    if rules.require_respect and not leg.respected:
        return None

    for retrace in leg.retrace:
        if retrace.index >= index or retrace.index in leg.used:
            continue
        inverted = (
            leg.trade_side == "short" and retrace.direction == "bullish" and bar.close < retrace.far
        ) or (
            leg.trade_side == "long" and retrace.direction == "bearish" and bar.close > retrace.far
        )
        if not inverted:
            continue
        leg.used.add(retrace.index)
        session = volume_session_start(bar.ts)
        if session != leg.session or not _in_entry_window(bar.ts, rules.window_start, rules.window_end):
            return None
        return RaidSetup(
            side=leg.trade_side,
            signal_time=bar.ts,
            sweep_time=leg.sweep_time,
            sweep_extreme=leg.extreme,
            level=leg.level,
            source=leg.source,
            gap_far=gap.far,
        )
    return None


def find_raid_setups(
    bars: list[Bar],
    pools: list[Pool],
    *,
    tick_size: float,
    rules: RaidRules | None = None,
) -> list[RaidSetup]:
    rules = rules or BASELINE
    was_through = [False] * len(pools)
    leg: _Leg | None = None
    found: list[RaidSetup] = []
    for index, bar in enumerate(bars):
        if leg is not None:
            setup = _apply_bar(leg, bars, index, rules)
            if leg.dead:
                leg = None
            if setup is not None:
                found.append(setup)
                leg = None

        session = volume_session_start(bar.ts)
        taken_buy: list[int] = []
        taken_sell: list[int] = []
        for pool_index, pool in enumerate(pools):
            if bar.ts < pool.available:
                continue
            if pool.side == "buy_side":
                through = bar.high >= pool.price + tick_size
                bucket = taken_buy
            else:
                through = bar.low <= pool.price - tick_size
                bucket = taken_sell
            if (
                through
                and not was_through[pool_index]
                and session is not None
                and _pool_allowed(pool, session, rules)
            ):
                bucket.append(pool_index)
            was_through[pool_index] = through
        if taken_buy and taken_sell:
            continue
        if not taken_buy and not taken_sell:
            continue
        # A later pool does not cancel the raid already in progress. The
        # sequence belongs to the sweep that started it. A body close through
        # the displacement gap is what ends it.
        if leg is not None:
            continue
        if session is None:
            continue
        if taken_buy:
            pool_index = max(taken_buy, key=lambda item: pools[item].price)
            trade_side = "short"
            extreme = bar.high
        else:
            pool_index = min(taken_sell, key=lambda item: pools[item].price)
            trade_side = "long"
            extreme = bar.low
        pool = pools[pool_index]
        leg = _Leg(
            trade_side=trade_side,
            sweep_index=index,
            sweep_time=bar.ts,
            session=session,
            extreme=extreme,
            level=pool.price,
            source=pool.source,
        )
    return found


def _bar_at(fill_bars: list[Bar], ts: datetime) -> int:
    return bisect_left(fill_bars, ts, key=lambda bar: bar.ts)


def _refine_extreme(setup: RaidSetup, fill_bars: list[Bar], signal_minutes: int) -> float:
    end = setup.sweep_time + timedelta(minutes=signal_minutes)
    chosen = fill_bars[_bar_at(fill_bars, setup.sweep_time) : _bar_at(fill_bars, end)]
    if not chosen:
        return setup.sweep_extreme
    if setup.side == "short":
        return max(bar.high for bar in chosen)
    return min(bar.low for bar in chosen)


def _pnl(side: str, entry: float, exit_px: float) -> float:
    if side == "short":
        ticks = (entry - exit_px) / _TICK
    else:
        ticks = (exit_px - entry) / _TICK
    return ticks * _DOLLARS_PER_TICK - _COMMISSION_PER_SIDE * 2


def _stop_price(side: str, extreme: float) -> float:
    buffer = _STOP_BUFFER_TICKS * _TICK
    if side == "short":
        return extreme + buffer
    return extreme - buffer


def _stop_hit(side: str, bar: Bar, stop: float) -> bool:
    if side == "short":
        return bar.open >= stop or bar.high >= stop
    return bar.open <= stop or bar.low <= stop


def _stop_fill(side: str, bar: Bar, stop: float) -> float:
    slip = _SLIP_TICKS * _TICK
    if side == "short":
        adjusted = stop + slip
        if bar.open >= stop:
            return max(bar.open, adjusted)
        return adjusted
    adjusted = stop - slip
    if bar.open <= stop:
        return min(bar.open, adjusted)
    return adjusted


def _market(is_buy: bool, open_px: float) -> float:
    slip = _SLIP_TICKS * _TICK
    if is_buy:
        return open_px + slip
    return open_px - slip


def simulate_raid_setups(
    setups: list[RaidSetup],
    fill_bars: list[Bar],
    *,
    signal_minutes: int = 15,
    stop_at: str = "sweep",
    window_end: int = 11 * 60,
) -> list[RaidTrade]:
    trades: list[RaidTrade] = []
    fills_per_day: dict = {}
    busy_until: datetime | None = None
    for setup in setups:
        entry_from = setup.signal_time + timedelta(minutes=signal_minutes)
        deadline = _window_end(setup.signal_time, window_end)
        entry_index = _bar_at(fill_bars, entry_from)
        if entry_index >= len(fill_bars) or fill_bars[entry_index].ts >= deadline:
            continue
        entry_bar = fill_bars[entry_index]
        if busy_until is not None and entry_bar.ts < busy_until:
            continue
        day = _ny_date(entry_bar.ts)
        if fills_per_day.get(day, 0) >= 2:
            continue
        if stop_at == "gap":
            extreme = setup.gap_far
        else:
            extreme = _refine_extreme(setup, fill_bars, signal_minutes)
        stop = _stop_price(setup.side, extreme)
        entry_px = _market(setup.side == "long", entry_bar.open)
        if setup.side == "short" and stop <= entry_px:
            continue
        if setup.side == "long" and stop >= entry_px:
            continue
        exit_time = entry_bar.ts
        exit_px = entry_px
        reason = "data_end"
        for index in range(entry_index, len(fill_bars)):
            bar = fill_bars[index]
            if bar.ts >= deadline:
                exit_time = bar.ts
                exit_px = _market(setup.side == "short", bar.open)
                reason = "time_stop"
                break
            if _stop_hit(setup.side, bar, stop):
                exit_time = bar.ts
                exit_px = _stop_fill(setup.side, bar, stop)
                reason = "stop"
                break
        else:
            if fill_bars:
                last = fill_bars[-1]
                exit_time = last.ts
                exit_px = _market(setup.side == "short", last.close)
                reason = "data_end"
        fills_per_day[day] = fills_per_day.get(day, 0) + 1
        busy_until = exit_time
        trades.append(
            RaidTrade(
                side=setup.side,
                signal_time=setup.signal_time,
                entry_time=entry_bar.ts,
                entry_price=entry_px,
                exit_time=exit_time,
                exit_price=exit_px,
                exit_reason=reason,
                pnl_usd=_pnl(setup.side, entry_px, exit_px),
                level=setup.level,
                source=setup.source,
                sweep_extreme=extreme,
            )
        )
    return trades


def backtest_raid_retrace(
    outright_bars: list[OutrightBar],
    rules: RaidRules | None = None,
) -> list[RaidTrade]:
    rules = rules or BASELINE
    trades: list[RaidTrade] = []
    fills_per_day: dict = {}
    busy_until: datetime | None = None
    for _piece, signal, pools, fills, segment in _prepared(outright_bars):
        setups = [
            setup
            for setup in find_raid_setups(signal, pools, tick_size=_TICK, rules=rules)
            if setup.signal_time >= segment.start
        ]
        segment_trades = _simulate_with_book(
            setups,
            fills,
            fills_per_day,
            busy_until,
            rules,
        )
        if segment_trades:
            busy_until = segment_trades[-1].exit_time
        trades.extend(segment_trades)
    return trades


def compare_raid_variants(outright_bars: list[OutrightBar]) -> list[tuple[RaidRules, list[RaidTrade]]]:
    """Score the five locked variants on one prepared tape."""
    books: dict[str, tuple[dict, datetime | None]] = {rules.name: ({}, None) for rules in VARIANTS}
    scored: dict[str, list[RaidTrade]] = {rules.name: [] for rules in VARIANTS}
    for _piece, signal, pools, fills, segment in _prepared(outright_bars):
        for rules in VARIANTS:
            fills_per_day, busy_until = books[rules.name]
            setups = [
                setup
                for setup in find_raid_setups(signal, pools, tick_size=_TICK, rules=rules)
                if setup.signal_time >= segment.start
            ]
            segment_trades = _simulate_with_book(setups, fills, fills_per_day, busy_until, rules)
            if segment_trades:
                books[rules.name] = (fills_per_day, segment_trades[-1].exit_time)
            scored[rules.name].extend(segment_trades)
    return [(rules, scored[rules.name]) for rules in VARIANTS]


def _prepared(outright_bars: list[OutrightBar]):
    from engine.marketdata.outrights import front_schedule, resample_outrights, segment_bars

    prepared = []
    for segment in front_schedule(outright_bars):
        piece = segment_bars(outright_bars, segment)
        signal = resample_outrights(piece, "15m")
        pools = collect_pools(
            (signal, "15m"),
            (resample_outrights(piece, "1h"), "1h"),
            (resample_outrights(piece, "4h"), "4h"),
        )
        prepared.append((piece, signal, pools, resample_outrights(piece, "1s"), segment))
    return prepared


def _simulate_with_book(setups, fill_bars, fills_per_day, busy_until, rules: RaidRules | None = None):
    """Same simulator, but the daily count and the open trade carry across contracts."""
    trades: list[RaidTrade] = []
    for setup in setups:
        rules = rules or BASELINE
        entry_from = setup.signal_time + timedelta(minutes=15)
        deadline = _window_end(setup.signal_time, rules.window_end)
        entry_index = _bar_at(fill_bars, entry_from)
        if entry_index >= len(fill_bars) or fill_bars[entry_index].ts >= deadline:
            continue
        entry_bar = fill_bars[entry_index]
        if busy_until is not None and entry_bar.ts < busy_until:
            continue
        day = _ny_date(entry_bar.ts)
        if fills_per_day.get(day, 0) >= 2:
            continue
        produced = simulate_raid_setups(
            [setup],
            fill_bars,
            signal_minutes=15,
            stop_at=rules.stop_at,
            window_end=rules.window_end,
        )
        if not produced:
            continue
        trade = produced[0]
        fills_per_day[day] = fills_per_day.get(day, 0) + 1
        busy_until = trade.exit_time
        trades.append(trade)
    return trades
