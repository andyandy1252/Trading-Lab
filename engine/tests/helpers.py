from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from engine.bars import Bar
from shared.spec.model import Session

NY = ZoneInfo("America/New_York")


def ny(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=NY).astimezone(timezone.utc)


def bar(ts: datetime, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(ts=ts, open=float(o), high=float(h), low=float(l), close=float(c))


CASH_RTH = Session(
    name="cash_rth",
    tz="America/New_York",
    start="09:30",
    end="16:00",
    days=[1, 2, 3, 4, 5],
)

CME_ETH = Session(
    name="cme_eth",
    tz="America/New_York",
    start="18:00",
    end="17:00",
    days=[7, 1, 2, 3, 4],
)

NY_AM = Session(
    name="ny_am",
    tz="America/New_York",
    start="09:30",
    end="11:00",
    days=[1, 2, 3, 4, 5],
)
