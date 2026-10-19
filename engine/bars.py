from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

BAR_COLUMNS = ["ts", "open", "high", "low", "close"]


@dataclass(frozen=True)
class Bar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if self.ts.tzinfo is None:
            object.__setattr__(self, "ts", self.ts.replace(tzinfo=timezone.utc))


def bars_to_frame(bars: list[Bar]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "ts": [b.ts for b in bars],
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": [b.close for b in bars],
        }
    )


def bars_from_frame(frame: pl.DataFrame) -> list[Bar]:
    rows = frame.sort("ts").iter_rows(named=True)
    out: list[Bar] = []
    for row in rows:
        ts = row["ts"]
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        out.append(
            Bar(
                ts=ts,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            )
        )
    return out


def read_bars(path: str | Path) -> list[Bar]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        frame = pl.read_csv(path, try_parse_dates=True)
    else:
        frame = pl.read_parquet(path)
    return bars_from_frame(frame)


def write_bars(path: str | Path, bars: list[Bar]) -> None:
    path = Path(path)
    frame = bars_to_frame(bars)
    if path.suffix.lower() == ".csv":
        frame.write_csv(path)
    else:
        frame.write_parquet(path)
