from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar
from engine.blocks.liquidity_sweep import SweepEvent
from engine.blocks.market_structure import StructureShiftEvent
from engine.blocks.swing_points import SwingPoint


@dataclass(frozen=True)
class OrderBlockEvent:
    bar_index: int
    direction: str
    high: float
    low: float
    midpoint: float
    formed_at: datetime


def detect_order_blocks(
    bars: list[Bar],
    sweeps: list[SweepEvent],
    shifts: list[StructureShiftEvent],
    swings: list[SwingPoint],
) -> list[OrderBlockEvent]:
    events: list[OrderBlockEvent] = []
    last_trend: str | None = None
    for shift in shifts:
        prior = [sweep for sweep in sweeps if sweep.bar_index < shift.bar_index]
        if not prior:
            continue
        sweep = prior[-1]
        if shift.direction == "bearish" and sweep.side != "buy_side":
            continue
        if shift.direction == "bullish" and sweep.side != "sell_side":
            continue
        if last_trend == shift.direction:
            continue
        origin = swings[sweep.bar_index]
        if shift.direction == "bearish":
            if origin.low is None:
                continue
            low = origin.low
            high = sweep.extreme
            if high <= low:
                continue
        else:
            if origin.high is None:
                continue
            high = origin.high
            low = sweep.extreme
            if high <= low:
                continue
        last_trend = shift.direction
        events.append(
            OrderBlockEvent(
                bar_index=shift.bar_index,
                direction=shift.direction,
                high=high,
                low=low,
                midpoint=(high + low) / 2.0,
                formed_at=bars[shift.bar_index].ts,
            )
        )
    return events
