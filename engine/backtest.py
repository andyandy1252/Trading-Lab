from __future__ import annotations

from engine.bars import Bar
from engine.blocks.equilibrium import detect_equilibrium
from engine.blocks.fair_value_gap import FairValueGapEvent, detect_fair_value_gaps
from engine.blocks.inverse_fvg import detect_inverse_fvgs
from engine.blocks.liquidity_sweep import SweepEvent, detect_liquidity_sweeps
from engine.blocks.market_structure import StructureShiftEvent, detect_market_structure_shifts
from engine.blocks.order_block import detect_order_blocks
from engine.blocks.session_levels import detect_session_levels
from engine.blocks.swing_points import detect_swing_points
from engine.events import BoundEvent, find_signals
from engine.instruments import INSTRUMENTS
from engine.simulate import BacktestResult, simulate
from shared.spec.model import StrategySpec

SERIES_TYPES = {"session_levels", "swing_points"}


def _occurrence(point, field: str):
    if field == "high" and getattr(point, "high_start", None) is not None:
        return point.high_start
    if field == "low" and getattr(point, "low_start", None) is not None:
        return point.low_start
    return getattr(point, "session_start", None)


def collect_events(spec: StrategySpec, bars: list[Bar]) -> dict[str, list[BoundEvent]]:
    tick = INSTRUMENTS[spec.instrument.value].tick_size
    sessions = {session.name: session for session in spec.sessions}
    series: dict = {}
    events: dict[str, list[BoundEvent]] = {}

    for block in spec.blocks:
        if block.type == "session_levels":
            session = sessions[block.params["session"]]
            series[block.id] = detect_session_levels(
                bars,
                session,
                list(block.params["levels"]),
                block.params["which"],
                block.params.get("asof"),
            )
        elif block.type == "swing_points":
            points = detect_swing_points(bars, kind=str(block.params.get("kind", "both")))
            series[block.id] = points
            swing_events: list[BoundEvent] = []
            prev_high = prev_low = None
            for i, point in enumerate(points):
                if point.high is not None and point.high_start != prev_high:
                    swing_events.append(
                        BoundEvent(block.id, i, {"price": point.high, "side": "high", "high": point.high})
                    )
                    prev_high = point.high_start
                if point.low is not None and point.low_start != prev_low:
                    swing_events.append(
                        BoundEvent(block.id, i, {"price": point.low, "side": "low", "low": point.low})
                    )
                    prev_low = point.low_start
            events[block.id] = swing_events

    for block in spec.blocks:
        if block.type in SERIES_TYPES:
            continue
        if block.type == "liquidity_sweep":
            source_id, field = str(block.params["level"]).split(".", 1)
            points = series[source_id]
            levels = [getattr(point, field) for point in points]
            starts = [_occurrence(point, field) for point in points]
            raw = detect_liquidity_sweeps(
                bars,
                levels,
                starts,
                field=field,
                penetration_ticks=int(block.params["penetration_ticks"]),
                tick_size=tick,
            )
            events[block.id] = [
                BoundEvent(
                    block.id,
                    item.bar_index,
                    {
                        "extreme": item.extreme,
                        "level": item.level,
                        "side": item.side,
                        "penetration_ticks": item.penetration_ticks,
                    },
                )
                for item in raw
            ]
        elif block.type == "fair_value_gap":
            raw = detect_fair_value_gaps(
                bars,
                direction=str(block.params["direction"]),
                min_size_ticks=int(block.params["min_size_ticks"]),
                tick_size=tick,
            )
            events[block.id] = [
                BoundEvent(
                    block.id,
                    item.bar_index,
                    {
                        "near_edge": item.near_edge,
                        "far_edge": item.far_edge,
                        "midpoint": item.midpoint,
                        "size_ticks": item.size_ticks,
                        "direction": item.direction,
                    },
                )
                for item in raw
            ]
        elif block.type == "market_structure_shift":
            swings = series[str(block.params["swings"])]
            raw = detect_market_structure_shifts(
                bars, swings, direction=str(block.params.get("direction", "either"))
            )
            events[block.id] = [
                BoundEvent(
                    block.id,
                    item.bar_index,
                    {"direction": item.direction, "level": item.level},
                )
                for item in raw
            ]
        elif block.type == "inverse_fvg":
            gap_id = str(block.params["gap"])
            gap_events = events[gap_id]
            gaps = [
                FairValueGapEvent(
                    bar_index=item.bar_index,
                    direction=str(item.fields["direction"]),
                    near_edge=float(item.fields["near_edge"]),
                    far_edge=float(item.fields["far_edge"]),
                    midpoint=float(item.fields["midpoint"]),
                    size_ticks=float(item.fields["size_ticks"]),
                    formed_at=bars[item.bar_index].ts,
                )
                for item in gap_events
            ]
            raw = detect_inverse_fvgs(
                bars, gaps, direction=str(block.params["direction"])
            )
            events[block.id] = [
                BoundEvent(
                    block.id,
                    item.bar_index,
                    {
                        "near_edge": item.near_edge,
                        "far_edge": item.far_edge,
                        "midpoint": item.midpoint,
                        "size_ticks": item.size_ticks,
                        "direction": item.direction,
                    },
                )
                for item in raw
            ]
        elif block.type == "order_block":
            sweep_id = str(block.params["sweep"])
            mss_id = str(block.params["mss"])
            swings = series[str(block.params["swings"])]
            sweeps = [
                SweepEvent(
                    bar_index=item.bar_index,
                    confirmed_at=bars[item.bar_index].ts,
                    level=float(item.fields["level"]),
                    extreme=float(item.fields["extreme"]),
                    side=str(item.fields["side"]),
                    penetration_ticks=float(item.fields["penetration_ticks"]),
                )
                for item in events[sweep_id]
            ]
            shifts = [
                StructureShiftEvent(
                    bar_index=item.bar_index,
                    direction=str(item.fields["direction"]),
                    level=float(item.fields["level"]),
                    confirmed_at=bars[item.bar_index].ts,
                )
                for item in events[mss_id]
            ]
            raw = detect_order_blocks(bars, sweeps, shifts, swings)
            events[block.id] = [
                BoundEvent(
                    block.id,
                    item.bar_index,
                    {
                        "direction": item.direction,
                        "high": item.high,
                        "low": item.low,
                        "midpoint": item.midpoint,
                    },
                )
                for item in raw
            ]
        elif block.type == "equilibrium":
            swings = series[str(block.params["swings"])]
            raw = detect_equilibrium(
                bars, swings, location=str(block.params["location"])
            )
            events[block.id] = [
                BoundEvent(
                    block.id,
                    item.bar_index,
                    {
                        "eq": item.eq,
                        "location": item.location,
                        "high": item.high,
                        "low": item.low,
                    },
                    align="completing",
                )
                for item in raw
            ]
        else:
            raise ValueError(f"Unsupported block type {block.type}")
    return events


def run_backtest(spec: StrategySpec, bars: list[Bar]) -> BacktestResult:
    events = collect_events(spec, bars)
    signals = find_signals(spec.entry.when, events, len(bars))
    return simulate(spec, bars, signals)
