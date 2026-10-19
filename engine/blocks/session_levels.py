from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from zoneinfo import ZoneInfo

from engine.bars import Bar
from engine.sessions import asof_utc, bar_in_window, iter_occurrences
from shared.spec.model import Session


@dataclass(frozen=True)
class SessionLevelPoint:
    bar_time: datetime
    high: float | None = None
    low: float | None = None
    midpoint: float | None = None
    open: float | None = None
    session_start: datetime | None = None


def _window_stats(
    bars: list[Bar],
    start: datetime,
    end: datetime,
    asof: datetime | None,
    up_to: datetime | None,
) -> tuple[float | None, float | None, float | None, datetime | None]:
    included: list[Bar] = []
    for bar in bars:
        if not bar_in_window(bar, start, end):
            continue
        if asof is not None and bar.ts >= asof:
            continue
        if up_to is not None and bar.ts > up_to:
            continue
        included.append(bar)
    if not included:
        return None, None, None, None
    high = max(b.high for b in included)
    low = min(b.low for b in included)
    open_px = included[0].open
    return high, low, open_px, start


def detect_session_levels(
    bars: list[Bar],
    session: Session,
    levels: list[str],
    which: str,
    asof: str | None = None,
) -> list[SessionLevelPoint]:
    if not bars:
        return []
    occurrences = iter_occurrences(session, bars[0].ts, bars[-1].ts)
    points: list[SessionLevelPoint] = []
    for bar in bars:
        chosen: tuple[datetime, datetime] | None = None
        up_to: datetime | None = None
        if which == "prior_completed":
            ended = [(s, e) for s, e in occurrences if e <= bar.ts]
            if ended:
                chosen = ended[-1]
        elif which == "developing":
            current = [(s, e) for s, e in occurrences if s <= bar.ts < e]
            if current:
                chosen = current[-1]
                up_to = bar.ts
        else:
            raise ValueError(f"Unknown session_levels which={which!r}")

        if chosen is None:
            points.append(SessionLevelPoint(bar_time=bar.ts))
            continue

        start, end = chosen
        asof_ts = None
        if asof:
            start_date = start.astimezone(ZoneInfo(session.tz)).date()
            asof_ts = asof_utc(session, start_date, asof)

        high, low, open_px, session_start = _window_stats(
            bars, start, end, asof_ts, up_to
        )
        midpoint = None
        if high is not None and low is not None and "midpoint" in levels:
            midpoint = (high + low) / 2.0
        points.append(
            SessionLevelPoint(
                bar_time=bar.ts,
                high=high if "high" in levels else None,
                low=low if "low" in levels else None,
                midpoint=midpoint,
                open=open_px if "open" in levels else None,
                session_start=session_start,
            )
        )
    return points
