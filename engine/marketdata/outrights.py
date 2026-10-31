from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from engine.backtest import run_backtest
from engine.bars import Bar
from engine.sessions import iter_occurrences
from engine.simulate import BacktestResult
from shared.spec.model import Session, StrategySpec

_OUTRIGHT = re.compile(r"^NQ([FGHJKMNQUVXZ])(\d{1,2})$")
_MONTH = {
    "F": 1,
    "G": 2,
    "H": 3,
    "J": 4,
    "K": 5,
    "M": 6,
    "N": 7,
    "Q": 8,
    "U": 9,
    "V": 10,
    "X": 11,
    "Z": 12,
}
_EVERY = {
    "1s": "1s",
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
}
_NY = ZoneInfo("America/New_York")

# Volume day. Same clock as the sample cme_eth session.
CME_EQUITY = Session(
    name="cme_eth",
    tz="America/New_York",
    start="18:00",
    end="17:00",
    days=[7, 1, 2, 3, 4],
)


@dataclass(frozen=True)
class OutrightBar:
    ts: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.ts.tzinfo is None:
            object.__setattr__(self, "ts", self.ts.replace(tzinfo=timezone.utc))
        else:
            object.__setattr__(self, "ts", self.ts.astimezone(timezone.utc))
        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "open", float(self.open))
        object.__setattr__(self, "high", float(self.high))
        object.__setattr__(self, "low", float(self.low))
        object.__setattr__(self, "close", float(self.close))
        object.__setattr__(self, "volume", float(self.volume))


@dataclass(frozen=True)
class FrontSegment:
    symbol: str
    start: datetime
    end: datetime


def is_nq_outright(symbol: str) -> bool:
    return _OUTRIGHT.fullmatch(symbol.upper()) is not None


def contract_year(digit: int, asof_year: int) -> int:
    """Year ending in `digit` that falls in [asof_year - 1, asof_year + 8]."""
    year = asof_year - 1
    while year % 10 != digit % 10:
        year += 1
    return year


def expiry_key(symbol: str, asof: datetime) -> tuple[int, int] | None:
    match = _OUTRIGHT.fullmatch(symbol.upper())
    if match is None:
        return None
    month = _MONTH[match.group(1)]
    raw = match.group(2)
    if len(raw) == 2:
        year = 2000 + int(raw)
    else:
        year = contract_year(int(raw), asof.year)
    return year, month


def volume_session_start(ts: datetime) -> datetime | None:
    """CME equity session open that owns this bar, or None outside that session."""
    local = ts.astimezone(_NY)
    if local.hour == 17:
        return None
    session_date = local.date() if local.hour >= 18 else local.date() - timedelta(days=1)
    if session_date.isoweekday() not in {7, 1, 2, 3, 4}:
        return None
    start_local = datetime.combine(session_date, time(18, 0), tzinfo=_NY)
    return start_local.astimezone(timezone.utc)


def _session_end(start: datetime) -> datetime:
    local = start.astimezone(_NY)
    end_local = datetime.combine(local.date() + timedelta(days=1), time(17, 0), tzinfo=_NY)
    return end_local.astimezone(timezone.utc)


def _as_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def session_volumes(bars: list[OutrightBar]) -> list[tuple[datetime, dict[str, float]]]:
    totals: dict[datetime, dict[str, float]] = {}
    order: list[datetime] = []
    for bar in bars:
        if not is_nq_outright(bar.symbol):
            continue
        start = volume_session_start(bar.ts)
        if start is None or bar.volume <= 0:
            continue
        bucket = totals.get(start)
        if bucket is None:
            bucket = {}
            totals[start] = bucket
            order.append(start)
        bucket[bar.symbol] = bucket.get(bar.symbol, 0.0) + float(bar.volume)
    order.sort()
    return [(start, totals[start]) for start in order]


def _leader(volumes: dict[str, float], asof: datetime) -> str | None:
    ranked = [(volume, expiry_key(symbol, asof), symbol) for symbol, volume in volumes.items()]
    ranked = [item for item in ranked if item[0] > 0 and item[1] is not None]
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2]


def _roll_forward(incumbent: str, volumes: dict[str, float], asof: datetime) -> str:
    inc_key = expiry_key(incumbent, asof)
    if inc_key is None:
        leader = _leader(volumes, asof)
        return incumbent if leader is None else leader
    inc_vol = volumes.get(incumbent, 0.0)
    later = []
    for symbol, volume in volumes.items():
        key = expiry_key(symbol, asof)
        if key is None or volume <= inc_vol or key <= inc_key:
            continue
        later.append((volume, key, symbol))
    if not later:
        return incumbent
    later.sort(key=lambda item: (-item[0], item[1]))
    return later[0][2]


def front_schedule(bars: list[OutrightBar]) -> list[FrontSegment]:
    sessions = session_volumes(bars)
    if len(sessions) < 2:
        return []
    first_start, first_vols = sessions[0]
    incumbent = _leader(first_vols, first_start)
    if incumbent is None:
        return []
    pieces: list[tuple[str, datetime, datetime]] = []
    for start, vols in sessions[1:]:
        pieces.append((incumbent, start, _session_end(start)))
        incumbent = _roll_forward(incumbent, vols, start)
    merged: list[FrontSegment] = []
    for symbol, start, end in pieces:
        if merged and merged[-1].symbol == symbol:
            merged[-1] = FrontSegment(symbol, merged[-1].start, end)
        else:
            merged.append(FrontSegment(symbol, start, end))
    return merged


def segment_bars(bars: list[OutrightBar], segment: FrontSegment) -> list[OutrightBar]:
    occurrences = iter_occurrences(
        CME_EQUITY, segment.start - timedelta(days=4), segment.end
    )
    priors = [start for start, end in occurrences if end <= segment.start]
    lookback = priors[-1] if priors else segment.start
    chosen = [
        bar
        for bar in bars
        if bar.symbol == segment.symbol and lookback <= bar.ts < segment.end
    ]
    chosen.sort(key=lambda bar: bar.ts)
    return chosen


def resample_outrights(bars: list[OutrightBar], timeframe: str) -> list[Bar]:
    if timeframe not in _EVERY:
        raise ValueError(f"Unsupported timeframe {timeframe!r}")
    if not bars:
        return []
    symbols = {bar.symbol for bar in bars}
    if len(symbols) != 1:
        raise ValueError("A resampled series cannot mix outright contracts")
    frame = pl.DataFrame(
        {
            "ts": [bar.ts for bar in bars],
            "open": [bar.open for bar in bars],
            "high": [bar.high for bar in bars],
            "low": [bar.low for bar in bars],
            "close": [bar.close for bar in bars],
        }
    ).with_columns(pl.col("ts").dt.convert_time_zone("UTC"))
    frame = frame.sort("ts").with_columns(pl.col("ts").dt.truncate(_EVERY[timeframe]).alias("bucket"))
    grouped = frame.group_by("bucket", maintain_order=True).agg(
        pl.col("open").first().alias("open"),
        pl.col("high").max().alias("high"),
        pl.col("low").min().alias("low"),
        pl.col("close").last().alias("close"),
    )
    out: list[Bar] = []
    for row in grouped.iter_rows(named=True):
        out.append(
            Bar(
                ts=_as_utc(row["bucket"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            )
        )
    return out


def write_outrights(path: str | Path, bars: list[OutrightBar]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pl.DataFrame(
        {
            "ts": [bar.ts for bar in bars],
            "symbol": [bar.symbol for bar in bars],
            "open": [bar.open for bar in bars],
            "high": [bar.high for bar in bars],
            "low": [bar.low for bar in bars],
            "close": [bar.close for bar in bars],
            "volume": [float(bar.volume) for bar in bars],
        }
    ).with_columns(
        pl.col("ts").dt.convert_time_zone("UTC").dt.replace_time_zone(None)
    )
    frame.write_parquet(path)


def read_outrights(path: str | Path) -> list[OutrightBar]:
    import duckdb

    rows = duckdb.execute(
        """
        SELECT ts, symbol, open, high, low, close, volume
        FROM read_parquet(?)
        ORDER BY ts, symbol
        """,
        [str(path)],
    ).fetchall()
    return [
        OutrightBar(
            ts=_as_utc(ts),
            symbol=str(symbol),
            open=float(open_),
            high=float(high),
            low=float(low),
            close=float(close),
            volume=float(volume),
        )
        for ts, symbol, open_, high, low, close, volume in rows
    ]


def _is_future(value: object) -> bool:
    raw = getattr(value, "value", value)
    text = str(raw).strip().upper()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text in {"F", "FUTURE"}


def outright_symbols_from_definitions(frame: pl.DataFrame) -> dict[int, str]:
    symbol_col = "raw_symbol" if "raw_symbol" in frame.columns else "symbol"
    found: dict[int, str] = {}
    for row in frame.iter_rows(named=True):
        if not _is_future(row.get("instrument_class", "F")):
            continue
        symbol = str(row[symbol_col]).strip().upper()
        if not is_nq_outright(symbol):
            continue
        found[int(row["instrument_id"])] = symbol
    return found


def ohlcv_to_outrights(frame: pl.DataFrame, id_to_symbol: dict[int, str]) -> list[OutrightBar]:
    ts_col = "ts_event" if "ts_event" in frame.columns else "ts"
    bars: list[OutrightBar] = []
    for row in frame.iter_rows(named=True):
        symbol = id_to_symbol.get(int(row["instrument_id"]))
        if symbol is None:
            continue
        bars.append(
            OutrightBar(
                ts=_as_utc(row[ts_col]),
                symbol=symbol,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
        )
    bars.sort(key=lambda bar: (bar.ts, bar.symbol))
    return bars


def run_front_month_backtest(spec: StrategySpec, bars: list[OutrightBar]) -> BacktestResult:
    combined = BacktestResult()
    segments = front_schedule(bars)
    if not segments:
        combined.rejects.append("no_front_month")
        return combined
    fill_name = "1s" if spec.fill_resolution == "1s" else "1m"
    for segment in segments:
        piece = segment_bars(bars, segment)
        if not piece:
            continue
        signal = resample_outrights(piece, spec.signal_timeframe)
        fill = resample_outrights(piece, fill_name)
        if not signal or not fill:
            continue
        result = run_backtest(spec, signal, fill_bars=fill, not_before=segment.start)
        combined.trades.extend(result.trades)
        combined.equity.extend(result.equity)
        combined.rejects.extend(result.rejects)
    return combined
