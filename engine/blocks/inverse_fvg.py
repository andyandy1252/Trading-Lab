from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar
from engine.blocks.fair_value_gap import FairValueGapEvent


@dataclass(frozen=True)
class InverseFvgEvent:
    bar_index: int
    direction: str
    near_edge: float
    far_edge: float
    midpoint: float
    size_ticks: float
    formed_at: datetime


def detect_inverse_fvgs(
    bars: list[Bar],
    gaps: list[FairValueGapEvent],
    direction: str,
) -> list[InverseFvgEvent]:
    events: list[InverseFvgEvent] = []
    inverted: set[int] = set()
    for i, bar in enumerate(bars):
        for gap in gaps:
            if gap.bar_index >= i or gap.bar_index in inverted:
                continue
            new_direction = None
            if gap.direction == "bullish" and bar.close < gap.far_edge:
                new_direction = "bearish"
            elif gap.direction == "bearish" and bar.close > gap.far_edge:
                new_direction = "bullish"
            if new_direction is None or new_direction != direction:
                continue
            inverted.add(gap.bar_index)
            events.append(
                InverseFvgEvent(
                    bar_index=i,
                    direction=new_direction,
                    near_edge=gap.near_edge,
                    far_edge=gap.far_edge,
                    midpoint=gap.midpoint,
                    size_ticks=gap.size_ticks,
                    formed_at=bar.ts,
                )
            )
    return events
