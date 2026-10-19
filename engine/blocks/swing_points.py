from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from engine.bars import Bar


@dataclass(frozen=True)
class SwingPoint:
    bar_time: datetime
    high: float | None = None
    low: float | None = None
    midpoint: float | None = None
    open: float | None = None
    session_start: datetime | None = None
    high_start: datetime | None = None
    low_start: datetime | None = None


def detect_swing_points(bars: list[Bar], kind: str) -> list[SwingPoint]:
    highs: list[tuple[int, float, datetime]] = []
    lows: list[tuple[int, float, datetime]] = []
    for i in range(2, len(bars)):
        left, mid, right = bars[i - 2], bars[i - 1], bars[i]
        if mid.high > left.high and mid.high > right.high:
            highs.append((i, mid.high, mid.ts))
        if mid.low < left.low and mid.low < right.low:
            lows.append((i, mid.low, mid.ts))

    want_high = kind in ("high", "both")
    want_low = kind in ("low", "both")
    points: list[SwingPoint] = []
    for i, bar in enumerate(bars):
        high = high_start = None
        low = low_start = None
        if want_high:
            confirmed = [item for item in highs if item[0] <= i]
            if confirmed:
                _, high, high_start = confirmed[-1]
        if want_low:
            confirmed = [item for item in lows if item[0] <= i]
            if confirmed:
                _, low, low_start = confirmed[-1]
        midpoint = None
        if high is not None and low is not None:
            midpoint = (high + low) / 2.0
        session_start = high_start if kind == "high" else low_start if kind == "low" else high_start
        points.append(
            SwingPoint(
                bar_time=bar.ts,
                high=high,
                low=low,
                midpoint=midpoint,
                session_start=session_start,
                high_start=high_start,
                low_start=low_start,
            )
        )
    return points
