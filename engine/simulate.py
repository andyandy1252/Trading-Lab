from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from engine.bars import Bar
from engine.events import Signal, resolve_ref
from engine.instruments import INSTRUMENTS
from engine.sessions import cme_day_start, occurrence_containing
from shared.spec.model import TIMEFRAME_MINUTES, Session, StrategySpec


@dataclass
class Trade:
    side: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    exit_reason: str
    pnl_usd: float
    commission_usd: float
    contracts: int
    signal_bar: int


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity: list[tuple[datetime, float]] = field(default_factory=list)
    rejects: list[str] = field(default_factory=list)


@dataclass
class _Position:
    side: str
    entry_price: float
    entry_time: datetime
    stop_price: float
    target_price: float
    contracts: int
    signal_bar: int
    session_end: datetime | None
    cme_day: datetime


@dataclass
class _Working:
    kind: str
    signal: Signal
    expire_index: int | None
    session_end: datetime | None


def _session_by_name(spec: StrategySpec, name: str) -> Session:
    for session in spec.sessions:
        if session.name == name:
            return session
    raise KeyError(name)


def _price_pnl(side: str, entry: float, exit_px: float, contracts: int, tick: float, dpt: float) -> float:
    if side == "long":
        ticks = (exit_px - entry) / tick
    else:
        ticks = (entry - exit_px) / tick
    return ticks * dpt * contracts


def _market_px(is_buy: bool, open_px: float, slip_ticks: int, tick: float) -> float:
    if is_buy:
        return open_px + slip_ticks * tick
    return open_px - slip_ticks * tick


def _stop_px(side: str, ref: float, offset: int, tick: float) -> float:
    if side == "long":
        return ref - offset * tick
    return ref + offset * tick


def _protective_ok(side: str, entry: float, stop: float) -> bool:
    if side == "long":
        return stop < entry
    return stop > entry


def _limit_hit(side: str, bar: Bar, limit: float, through_ticks: int, tick: float) -> bool:
    extra = through_ticks * tick
    if side == "long":
        return bar.open <= limit or bar.low <= limit - extra
    return bar.open >= limit or bar.high >= limit + extra


def _stop_hit(side: str, bar: Bar, stop: float) -> bool:
    if side == "long":
        return bar.open <= stop or bar.low <= stop
    return bar.open >= stop or bar.high >= stop


def _stop_fill(side: str, bar: Bar, stop: float, slip_ticks: int, tick: float) -> float:
    if side == "long":
        adj = stop - slip_ticks * tick
        if bar.open <= stop:
            return min(bar.open, adj)
        return adj
    adj = stop + slip_ticks * tick
    if bar.open >= stop:
        return max(bar.open, adj)
    return adj


def _target_hit(side: str, bar: Bar, target: float, through_ticks: int, tick: float) -> bool:
    extra = through_ticks * tick
    if side == "long":
        return bar.open >= target or bar.high >= target + extra
    return bar.open <= target or bar.low <= target - extra


def _signal_indexes(signal_bars: list[Bar], fill_bars: list[Bar], minutes: int) -> list[int | None]:
    if minutes <= 0:
        raise ValueError("signal timeframe must be at least one minute")
    delta = timedelta(minutes=minutes)
    opens = [bar.ts for bar in signal_bars]
    indexes: list[int | None] = []
    j = 0
    for fill in fill_bars:
        while j + 1 < len(opens) and opens[j + 1] <= fill.ts:
            j += 1
        if opens and opens[j] <= fill.ts < opens[j] + delta:
            indexes.append(j)
        else:
            indexes.append(None)
    return indexes


def simulate(
    spec: StrategySpec,
    bars: list[Bar],
    signals: list[Signal],
    fill_bars: list[Bar] | None = None,
) -> BacktestResult:
    info = INSTRUMENTS[spec.instrument.value]
    tick = info.tick_size
    dpt = info.dollars_per_tick
    slip = spec.costs.market_slippage_ticks
    through = spec.costs.limit_through_ticks
    contracts = spec.risk.contracts
    commission_one = spec.costs.commission_per_side_usd * contracts
    commission_round = commission_one * 2
    risk_session = _session_by_name(spec, spec.risk.session)
    time_session = _session_by_name(spec, spec.exit.time_stop.session)

    result = BacktestResult()
    position: _Position | None = None
    working: _Working | None = None
    pending_flatten = False
    closed_pnl_by_day: dict[datetime, float] = {}
    blocked_days: set[datetime] = set()
    fills_by_occurrence: dict[datetime, int] = {}
    equity = 0.0
    signal_by_index = {s.bar_index: s for s in signals}
    if fill_bars is None:
        fill_bars = bars
        signal_of: list[int | None] = list(range(len(bars)))
    else:
        signal_of = _signal_indexes(bars, fill_bars, TIMEFRAME_MINUTES[spec.signal_timeframe])

    def day_pnl(ts: datetime) -> float:
        return closed_pnl_by_day.get(cme_day_start(ts), 0.0)

    def close_position(bar: Bar, exit_px: float, reason: str) -> None:
        nonlocal position, equity
        assert position is not None
        pnl = _price_pnl(position.side, position.entry_price, exit_px, contracts, tick, dpt)
        pnl -= commission_round
        day = position.cme_day
        closed_pnl_by_day[day] = closed_pnl_by_day.get(day, 0.0) + pnl
        equity += pnl
        result.trades.append(
            Trade(
                side=position.side,
                entry_time=position.entry_time,
                entry_price=position.entry_price,
                exit_time=bar.ts,
                exit_price=exit_px,
                exit_reason=reason,
                pnl_usd=pnl,
                commission_usd=commission_round,
                contracts=contracts,
                signal_bar=position.signal_bar,
            )
        )
        if closed_pnl_by_day[day] <= -spec.risk.daily_loss_stop_usd:
            blocked_days.add(day)
        position = None

    def open_position(bar: Bar, entry_px: float, signal: Signal) -> None:
        nonlocal position, working
        side = spec.entry.side
        ref = resolve_ref(spec.exit.stop.ref, signal.bound)
        stop = _stop_px(side, ref, spec.exit.stop.offset_ticks, tick)
        if not _protective_ok(side, entry_px, stop):
            result.rejects.append("stop_wrong_side")
            working = None
            return
        distance = abs(entry_px - stop)
        target = entry_px + spec.exit.target.value * distance if side == "long" else entry_px - spec.exit.target.value * distance
        occ = occurrence_containing(time_session, bars[signal.bar_index].ts)
        session_end = occ[1] if occ else None
        signal_occ = occurrence_containing(risk_session, bars[signal.bar_index].ts)
        if signal_occ is not None:
            key = signal_occ[0]
            fills_by_occurrence[key] = fills_by_occurrence.get(key, 0) + 1
        position = _Position(
            side=side,
            entry_price=entry_px,
            entry_time=bar.ts,
            stop_price=stop,
            target_price=target,
            contracts=contracts,
            signal_bar=signal.bar_index,
            session_end=session_end,
            cme_day=cme_day_start(bar.ts),
        )
        working = None

    def can_take(signal: Signal) -> bool:
        if position is not None or working is not None or pending_flatten:
            return False
        day = cme_day_start(bars[signal.bar_index].ts)
        if day in blocked_days:
            return False
        occ = occurrence_containing(risk_session, bars[signal.bar_index].ts)
        if occ is not None:
            if fills_by_occurrence.get(occ[0], 0) >= spec.risk.max_trades_per_session:
                return False
        return True

    for fill_i, bar in enumerate(fill_bars):
        sig_i = signal_of[fill_i]
        is_last = fill_i + 1 == len(fill_bars) or signal_of[fill_i + 1] != sig_i
        day = cme_day_start(bar.ts)

        if pending_flatten and position is not None:
            is_buy = position.side == "short"
            close_position(bar, _market_px(is_buy, bar.open, slip, tick), "daily_loss")
            pending_flatten = False
            blocked_days.add(day)

        if position is not None and position.session_end is not None and bar.ts >= position.session_end:
            is_buy = position.side == "short"
            close_position(bar, _market_px(is_buy, bar.open, slip, tick), "time_stop")

        if (
            working is not None
            and working.expire_index is not None
            and sig_i is not None
            and sig_i > working.expire_index
        ):
            working = None

        if working is not None and position is None:
            if working.kind == "market":
                is_buy = spec.entry.side == "long"
                open_position(bar, _market_px(is_buy, bar.open, slip, tick), working.signal)
            elif working.kind == "limit":
                limit = resolve_ref(spec.entry.price or "", working.signal.bound)
                if _limit_hit(spec.entry.side, bar, limit, through, tick):
                    open_position(bar, limit, working.signal)
                elif (
                    is_last
                    and sig_i is not None
                    and working.expire_index is not None
                    and sig_i >= working.expire_index
                ):
                    working = None

        if position is not None:
            stop_now = _stop_hit(position.side, bar, position.stop_price)
            target_now = _target_hit(position.side, bar, position.target_price, through, tick)
            if stop_now and target_now:
                close_position(
                    bar,
                    _stop_fill(position.side, bar, position.stop_price, slip, tick),
                    "stop",
                )
            elif stop_now:
                close_position(
                    bar,
                    _stop_fill(position.side, bar, position.stop_price, slip, tick),
                    "stop",
                )
            elif target_now:
                close_position(bar, position.target_price, "target")

        if position is not None:
            mtm = _price_pnl(position.side, position.entry_price, bar.close, contracts, tick, dpt)
            if day_pnl(bar.ts) + mtm <= -spec.risk.daily_loss_stop_usd:
                pending_flatten = True
                blocked_days.add(day)

        if is_last and sig_i is not None and sig_i in signal_by_index and can_take(signal_by_index[sig_i]):
            sig = signal_by_index[sig_i]
            expire = None
            if spec.entry.order in ("limit", "stop") and spec.entry.expire_bars is not None:
                expire = sig_i + spec.entry.expire_bars
            occ = occurrence_containing(time_session, bars[sig_i].ts)
            working = _Working(
                kind=spec.entry.order,
                signal=sig,
                expire_index=expire,
                session_end=occ[1] if occ else None,
            )

        result.equity.append((bar.ts, equity + (
            _price_pnl(position.side, position.entry_price, bar.close, contracts, tick, dpt)
            if position is not None else 0.0
        )))

    return result
