from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar


@dataclass(frozen=True)
class FairValueGapEvent:
    bar_index: int
    direction: str
    near_edge: float
    far_edge: float
    midpoint: float
    size_ticks: float
    formed_at: datetime


def detect_fair_value_gaps(
    bars: list[Bar],
    direction: str,
    min_size_ticks: int,
    tick_size: float,
) -> list[FairValueGapEvent]:
    events: list[FairValueGapEvent] = []
    for i in range(2, len(bars)):
        a, _b, c = bars[i - 2], bars[i - 1], bars[i]
        if direction == "bullish":
            if a.high >= c.low:
                continue
            far_edge = a.high
            near_edge = c.low
        elif direction == "bearish":
            if a.low <= c.high:
                continue
            far_edge = a.low
            near_edge = c.high
        else:
            raise ValueError(f"Unknown FVG direction {direction!r}")
        height = abs(near_edge - far_edge)
        size_ticks = height / tick_size
        if size_ticks < min_size_ticks:
            continue
        events.append(
            FairValueGapEvent(
                bar_index=i,
                direction=direction,
                near_edge=near_edge,
                far_edge=far_edge,
                midpoint=(near_edge + far_edge) / 2.0,
                size_ticks=size_ticks,
                formed_at=c.ts,
            )
        )
    return events
