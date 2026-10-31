from datetime import datetime, timedelta

import polars as pl

from engine.bars import Bar
from engine.blocks.fair_value_gap import detect_fair_value_gaps
from engine.marketdata.outrights import (
    FrontSegment,
    OutrightBar,
    expiry_key,
    front_schedule,
    ohlcv_to_outrights,
    outright_symbols_from_definitions,
    read_outrights,
    resample_outrights,
    run_front_month_backtest,
    segment_bars,
    volume_session_start,
    write_outrights,
)
from engine.tests.helpers import ny
from engine.tests.test_backtest import _spec


def ob(
    ts: datetime,
    symbol: str,
    price: float,
    volume: float,
    *,
    high=None,
    low=None,
    close=None,
) -> OutrightBar:
    return OutrightBar(
        ts=ts,
        symbol=symbol,
        open=price,
        high=price if high is None else high,
        low=price if low is None else low,
        close=price if close is None else close,
        volume=volume,
    )


def test_one_digit_year_uses_the_bar_year_window():
    asof = ny(2026, 10, 20, 18, 0)
    assert expiry_key("NQZ6", asof) < expiry_key("NQH7", asof)
    assert expiry_key("NQH6", asof) < expiry_key("NQM6", asof)
    assert expiry_key("NQZ4", ny(2024, 12, 1, 18, 0)) == (2024, 12)


def test_spreads_are_not_outrights():
    assert expiry_key("NQZ6-NQH7", ny(2026, 10, 20, 18, 0)) is None


def test_halt_and_weekend_bars_do_not_join_a_volume_session():
    assert volume_session_start(ny(2026, 10, 19, 17, 30)) is None
    assert volume_session_start(ny(2026, 10, 17, 12, 0)) is None
    sunday = volume_session_start(ny(2026, 10, 18, 18, 0))
    assert sunday == ny(2026, 10, 18, 18, 0)
    friday_morning = volume_session_start(ny(2026, 10, 23, 10, 0))
    assert friday_morning == ny(2026, 10, 22, 18, 0)


def test_front_month_is_prior_session_volume_and_rolls_forward_only():
    bars = [
        ob(ny(2026, 10, 18, 18, 1), "NQZ6", 21000, 100),
        ob(ny(2026, 10, 18, 18, 1), "NQH7", 21100, 40),
        ob(ny(2026, 10, 19, 18, 1), "NQZ6", 21010, 90),
        ob(ny(2026, 10, 19, 18, 1), "NQH7", 21110, 120),
        ob(ny(2026, 10, 20, 18, 1), "NQZ6", 21020, 200),
        ob(ny(2026, 10, 20, 18, 1), "NQH7", 21120, 50),
        ob(ny(2026, 10, 21, 18, 1), "NQH7", 21130, 10),
    ]
    segments = front_schedule(bars)
    assert [(item.symbol, item.start) for item in segments] == [
        ("NQZ6", ny(2026, 10, 19, 18, 0)),
        ("NQH7", ny(2026, 10, 20, 18, 0)),
    ]
    assert segments[-1].end == ny(2026, 10, 22, 17, 0)


def test_first_session_tie_picks_the_nearer_expiry():
    bars = [
        ob(ny(2026, 10, 18, 18, 1), "NQZ6", 21000, 50),
        ob(ny(2026, 10, 18, 18, 1), "NQH7", 21100, 50),
        ob(ny(2026, 10, 19, 18, 1), "NQZ6", 21000, 10),
    ]
    segments = front_schedule(bars)
    assert segments == [
        FrontSegment("NQZ6", ny(2026, 10, 19, 18, 0), ny(2026, 10, 20, 17, 0))
    ]


def test_roll_gap_does_not_become_a_fair_value_gap_and_prices_stay_raw():
    bars = [
        ob(ny(2026, 10, 18, 18, 1), "NQZ6", 100, 50),
        ob(ny(2026, 10, 19, 18, 0), "NQZ6", 100, 5, high=100.5, low=100),
        ob(ny(2026, 10, 19, 18, 1), "NQZ6", 100, 5, high=100.5, low=100),
        ob(ny(2026, 10, 19, 18, 2), "NQZ6", 100, 5, high=100.25, low=99.75),
        ob(ny(2026, 10, 19, 18, 1), "NQH7", 80, 80),
        ob(ny(2026, 10, 20, 18, 0), "NQH7", 80, 5, high=80.25, low=79.75),
        ob(ny(2026, 10, 20, 18, 1), "NQH7", 80, 5, high=80.25, low=79.5),
        ob(ny(2026, 10, 20, 18, 2), "NQH7", 80, 5, high=80.0, low=79.5),
    ]
    stitched = []
    for segment in front_schedule(bars):
        piece = segment_bars(bars, segment)
        assert {bar.symbol for bar in piece} == {segment.symbol}
        stitched.extend(resample_outrights(piece, "1m"))
    crossed = [
        Bar(ny(2026, 10, 19, 18, 0), 100, 100.5, 100, 100),
        Bar(ny(2026, 10, 19, 18, 1), 100, 100.5, 100, 100),
        Bar(ny(2026, 10, 20, 18, 0), 80, 80.25, 79.75, 80),
    ]
    assert detect_fair_value_gaps(crossed, "bearish", 0, 0.25)
    found = []
    for segment in front_schedule(bars):
        found.extend(
            detect_fair_value_gaps(resample_outrights(segment_bars(bars, segment), "1m"), "bearish", 0, 0.25)
        )
    assert found == []
    h7 = [bar for bar in stitched if bar.ts >= ny(2026, 10, 20, 18, 0)]
    assert h7[0].open == 80


def test_parquet_roundtrip_is_read_with_duckdb(tmp_path):
    path = tmp_path / "nq.parquet"
    bars = [
        ob(ny(2026, 10, 19, 18, 0), "NQZ6", 21000.25, 12),
        ob(ny(2026, 10, 19, 18, 1), "NQH7", 21100.5, 7),
    ]
    write_outrights(path, bars)
    got = read_outrights(path)
    assert [(b.symbol, b.open, b.volume) for b in got] == [
        ("NQZ6", 21000.25, 12),
        ("NQH7", 21100.5, 7),
    ]
    assert got[0].ts == ny(2026, 10, 19, 18, 0)
    assert got[0].ts.tzinfo is not None


def test_resample_refuses_two_contracts_and_builds_fifteen_minute_bars():
    origin = ny(2026, 10, 20, 9, 30)
    bars = []
    for minute in range(15):
        px = 100 + minute
        bars.append(ob(origin + timedelta(minutes=minute), "NQZ6", px, 1, high=px + 0.5, low=px - 0.25))
    bars.append(ob(origin, "NQH7", 50, 1))
    try:
        resample_outrights(bars, "15m")
        raised = False
    except ValueError:
        raised = True
    assert raised
    out = resample_outrights(bars[:-1], "15m")
    assert len(out) == 1
    assert out[0].ts == origin
    assert out[0].open == 100
    assert out[0].high == 114.5
    assert out[0].low == 99.75
    assert out[0].close == 114


def test_definitions_keep_nq_outrights_and_ohlcv_joins_on_instrument_id():
    definitions = pl.DataFrame(
        {
            "instrument_id": [1, 2, 3],
            "raw_symbol": ["NQZ6", "NQZ6-NQH7", "MNQZ6"],
            "instrument_class": ["F", "S", "F"],
        }
    )
    mapping = outright_symbols_from_definitions(definitions)
    assert mapping == {1: "NQZ6"}
    ohlcv = pl.DataFrame(
        {
            "instrument_id": [1, 2],
            "ts_event": [ny(2026, 10, 20, 9, 30), ny(2026, 10, 20, 9, 30)],
            "open": [21000.0, 1.0],
            "high": [21001.0, 1.0],
            "low": [20999.0, 1.0],
            "close": [21000.5, 1.0],
            "volume": [9, 100],
        }
    )
    bars = ohlcv_to_outrights(ohlcv, mapping)
    assert len(bars) == 1
    assert bars[0].symbol == "NQZ6"
    assert bars[0].close == 21000.5
    assert bars[0].volume == 9


def test_front_month_backtest_keeps_the_same_contract_for_prior_day_high(tmp_path):
    spec = _spec()
    bars = [
        ob(ny(2024, 1, 4, 19, 0), "NQH4", 90, 30),
        ob(ny(2024, 1, 7, 19, 0), "NQH4", 99, 40, high=100, low=98, close=99),
        ob(ny(2024, 1, 9, 9, 30), "NQH4", 99.5, 10, high=99.75, low=99, close=99.5),
        ob(ny(2024, 1, 9, 9, 31), "NQH4", 99.5, 10, high=100.50, low=99, close=100.25),
        ob(ny(2024, 1, 9, 9, 32), "NQH4", 102.5, 10, high=103, low=102, close=102.5),
        ob(ny(2024, 1, 9, 9, 33), "NQH4", 102.5, 10, high=102.6, low=97, close=97.5),
        ob(ny(2024, 1, 9, 9, 34), "NQH4", 97.5, 10, high=98, low=95, close=96),
        ob(ny(2024, 1, 9, 9, 35), "NQH4", 99.5, 10, high=100.5, low=99.5, close=100.2),
        ob(ny(2024, 1, 9, 9, 36), "NQH4", 100, 10, high=100.2, low=96, close=97),
        ob(ny(2024, 1, 7, 19, 0), "NQM4", 500, 1, high=500, low=500),
    ]
    result = run_front_month_backtest(spec, bars)
    assert len(result.trades) == 1
    assert result.trades[0].side == "short"
    assert result.trades[0].entry_price == 100.0
    path = tmp_path / "outrights.parquet"
    write_outrights(path, bars)
    from engine.cli import main

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json(), encoding="utf-8")
    code = main(["backtest", "--spec", str(spec_path), "--outrights", str(path)])
    assert code == 0


def test_pull_requests_parent_definitions_then_raw_outright_ohlcv(tmp_path):
    from engine.marketdata.databento_nq import pull_nq_outrights

    definitions = pl.DataFrame(
        {
            "instrument_id": [1, 2],
            "raw_symbol": ["NQZ6", "NQZ6-NQH7"],
            "instrument_class": ["F", "S"],
        }
    )
    ohlcv = pl.DataFrame(
        {
            "instrument_id": [1],
            "ts_event": [ny(2026, 10, 20, 9, 30)],
            "open": [21000.0],
            "high": [21001.0],
            "low": [20999.0],
            "close": [21000.5],
            "volume": [9],
        }
    )
    calls: list[dict] = []

    class TimeSeries:
        def get_range(self, **kwargs):
            calls.append(kwargs)
            if kwargs["schema"] == "definition":
                return definitions
            return ohlcv

    class Client:
        timeseries = TimeSeries()

    dest = tmp_path / "nq.parquet"
    pull_nq_outrights(Client(), start="2026-10-18", end="2026-10-31", dest=dest)
    assert calls[0]["dataset"] == "GLBX.MDP3"
    assert calls[0]["symbols"] == "NQ.FUT"
    assert calls[0]["stype_in"] == "parent"
    assert calls[0]["schema"] == "definition"
    assert calls[1]["schema"] == "ohlcv-1s"
    assert calls[1]["stype_in"] == "raw_symbol"
    assert calls[1]["symbols"] == ["NQZ6"]
    assert read_outrights(dest)[0].symbol == "NQZ6"
    assert read_outrights(dest)[0].close == 21000.5


def test_pull_stops_when_the_quote_is_over_the_cap(tmp_path):
    from engine.marketdata.databento_nq import pull_nq_outrights

    definitions = pl.DataFrame(
        {
            "instrument_id": [1],
            "raw_symbol": ["NQZ6"],
            "instrument_class": ["F"],
        }
    )
    schemas: list[str] = []

    class TimeSeries:
        def get_range(self, **kwargs):
            schemas.append(kwargs["schema"])
            if kwargs["schema"] == "definition":
                return definitions
            raise AssertionError("ohlcv should not download")

    class Metadata:
        def get_cost(self, **kwargs):
            return 9.5

    class Client:
        timeseries = TimeSeries()
        metadata = Metadata()

    try:
        pull_nq_outrights(
            Client(),
            start="2026-10-18",
            end="2026-10-31",
            dest=tmp_path / "nq.parquet",
        )
        raised = False
    except RuntimeError as exc:
        raised = "9.50" in str(exc)
    assert raised
    assert schemas == ["definition"]


def test_fetch_nq_without_a_key_prints_the_reason(tmp_path, capsys, monkeypatch):
    from engine.cli import main

    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    code = main(
        [
            "fetch-nq",
            "--start",
            "2026-10-18",
            "--end",
            "2026-10-31",
            "--out",
            "nq.parquet",
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "DATABENTO_API_KEY" in captured.out
    assert "Traceback" not in captured.err
