from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar
from engine.blocks.swing_points import SwingPoint


@dataclass(frozen=True)
class StructureShiftEvent:
    bar_index: int
    direction: str
    level: float
    confirmed_at: datetime


def detect_market_structure_shifts(
    bars: list[Bar],
    swings: list[SwingPoint],
    direction: str,
) -> list[StructureShiftEvent]:
    events: list[StructureShiftEvent] = []
    prev_bear = False
    prev_bull = False
    last_low_id: datetime | None = None
    last_high_id: datetime | None = None
    for i, bar in enumerate(bars):
        point = swings[i]
        if direction in ("bearish", "either") and point.low is not None:
            if point.low_start != last_low_id:
                prev_bear = False
                last_low_id = point.low_start
            is_shift = bar.close < point.low
            if is_shift and not prev_bear:
                events.append(
                    StructureShiftEvent(
                        bar_index=i,
                        direction="bearish",
                        level=point.low,
                        confirmed_at=bar.ts,
                    )
                )
            prev_bear = is_shift
        if direction in ("bullish", "either") and point.high is not None:
            if point.high_start != last_high_id:
                prev_bull = False
                last_high_id = point.high_start
            is_shift = bar.close > point.high
            if is_shift and not prev_bull:
                events.append(
                    StructureShiftEvent(
                        bar_index=i,
                        direction="bullish",
                        level=point.high,
                        confirmed_at=bar.ts,
                    )
                )
            prev_bull = is_shift
    return events
