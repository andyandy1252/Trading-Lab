from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from engine.bars import Bar
from shared.spec.model import Session


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def crosses_midnight(session: Session) -> bool:
    return session.end <= session.start


def occurrence_bounds(session: Session, start_date: date) -> tuple[datetime, datetime]:
    tz = ZoneInfo(session.tz)
    start_local = datetime.combine(start_date, parse_hhmm(session.start), tzinfo=tz)
    if crosses_midnight(session):
        end_date = start_date + timedelta(days=1)
    else:
        end_date = start_date
    end_local = datetime.combine(end_date, parse_hhmm(session.end), tzinfo=tz)
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def asof_utc(session: Session, start_date: date, asof: str) -> datetime:
    tz = ZoneInfo(session.tz)
    asof_time = parse_hhmm(asof)
    start_time = parse_hhmm(session.start)
    if crosses_midnight(session) and asof_time <= start_time:
        asof_date = start_date + timedelta(days=1)
    else:
        asof_date = start_date
    return datetime.combine(asof_date, asof_time, tzinfo=tz).astimezone(timezone.utc)


def iter_occurrences(
    session: Session, first_ts: datetime, last_ts: datetime
) -> list[tuple[datetime, datetime]]:
    tz = ZoneInfo(session.tz)
    local_first = first_ts.astimezone(tz).date() - timedelta(days=2)
    local_last = last_ts.astimezone(tz).date() + timedelta(days=1)
    days = set(session.days)
    out: list[tuple[datetime, datetime]] = []
    cursor = local_first
    while cursor <= local_last:
        if cursor.isoweekday() in days:
            out.append(occurrence_bounds(session, cursor))
        cursor += timedelta(days=1)
    return out


def bar_in_window(bar: Bar, start: datetime, end: datetime) -> bool:
    return start <= bar.ts < end


def session_end_on_or_after(session: Session, ts: datetime) -> datetime | None:
    """Soonest occurrence end at or after ts, or the end of the occurrence containing ts."""
    occurrences = iter_occurrences(session, ts, ts + timedelta(days=2))
    for start, end in occurrences:
        if start <= ts < end:
            return end
        if ts < start:
            return end
    return None


def cme_day_start(ts: datetime) -> datetime:
    tz = ZoneInfo("America/New_York")
    local = ts.astimezone(tz)
    if local.time() >= time(18, 0):
        start_local = datetime.combine(local.date(), time(18, 0), tzinfo=tz)
    else:
        start_local = datetime.combine(
            local.date() - timedelta(days=1), time(18, 0), tzinfo=tz
        )
    return start_local.astimezone(timezone.utc)


def occurrence_containing(
    session: Session, ts: datetime
) -> tuple[datetime, datetime] | None:
    for start, end in iter_occurrences(session, ts, ts):
        if start <= ts < end:
            return start, end
    return None


def bar_in_session(bar: Bar, session: Session) -> bool:
    if not iter_occurrences(session, bar.ts, bar.ts):
        return False
    for start, end in iter_occurrences(session, bar.ts, bar.ts):
        if bar_in_window(bar, start, end):
            return True
    return False
