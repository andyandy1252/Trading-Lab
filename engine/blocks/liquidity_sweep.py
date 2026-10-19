from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar


@dataclass(frozen=True)
class SweepEvent:
    bar_index: int
    confirmed_at: datetime
    level: float
    extreme: float
    side: str
    penetration_ticks: float


def _through(
    bar: Bar, level: float, field: str, penetration_ticks: int, tick_size: float
) -> bool:
    extra = penetration_ticks * tick_size
    if field == "high":
        return bar.high >= level + extra
    if field == "low":
        return bar.low <= level - extra
    raise ValueError(f"sweep field must be high or low, got {field!r}")


def detect_liquidity_sweeps(
    bars: list[Bar],
    levels: list[float | None],
    occurrence_starts: list[datetime | None],
    field: str,
    penetration_ticks: int,
    tick_size: float,
) -> list[SweepEvent]:
    events: list[SweepEvent] = []
    prev_through = False
    prev_start: datetime | None = None
    for i, bar in enumerate(bars):
        level = levels[i]
        start = occurrence_starts[i]
        if level is None or start is None:
            prev_through = False
            prev_start = None
            continue
        if prev_start != start:
            prev_through = False
        is_through = _through(bar, level, field, penetration_ticks, tick_size)
        if is_through and not prev_through:
            if field == "high":
                extreme = bar.high
                side = "buy_side"
                measured = (extreme - level) / tick_size
            else:
                extreme = bar.low
                side = "sell_side"
                measured = (level - extreme) / tick_size
            events.append(
                SweepEvent(
                    bar_index=i,
                    confirmed_at=bar.ts,
                    level=level,
                    extreme=extreme,
                    side=side,
                    penetration_ticks=measured,
                )
            )
        prev_through = is_through
        prev_start = start
    return events
