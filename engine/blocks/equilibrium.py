from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar
from engine.blocks.swing_points import SwingPoint


@dataclass(frozen=True)
class EquilibriumEvent:
    bar_index: int
    location: str
    eq: float
    high: float
    low: float
    formed_at: datetime


def detect_equilibrium(
    bars: list[Bar],
    swings: list[SwingPoint],
    location: str,
) -> list[EquilibriumEvent]:
    events: list[EquilibriumEvent] = []
    for i, bar in enumerate(bars):
        point = swings[i]
        if point.high is None or point.low is None:
            continue
        eq = (point.high + point.low) / 2.0
        if bar.close < eq:
            here = "discount"
        elif bar.close > eq:
            here = "premium"
        else:
            here = "equilibrium"
        if here != location:
            continue
        events.append(
            EquilibriumEvent(
                bar_index=i,
                location=here,
                eq=eq,
                high=point.high,
                low=point.low,
                formed_at=bar.ts,
            )
        )
    return events
