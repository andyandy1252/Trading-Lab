from engine.backtest import run_backtest
from engine.events import BoundEvent, Signal
from engine.simulate import simulate
from engine.tests.helpers import bar, ny
from engine.tests.test_backtest import _spec


def _short_spec():
    spec = _spec()
    return spec.model_copy(update={"signal_timeframe": "15m", "fill_resolution": "1m"})


def _signal() -> Signal:
    return Signal(
        bar_index=0,
        bound={
            "fvg": BoundEvent("fvg", 0, {"midpoint": 100.0}),
            "sweep": BoundEvent("sweep", 0, {"extreme": 101.0}),
        },
    )


def test_same_bars_match_the_single_series_backtest():
    bars = [
        bar(ny(2024, 1, 7, 19, 0), 99, 100, 98, 99),
        bar(ny(2024, 1, 9, 9, 30), 99.5, 99.75, 99, 99.5),
        bar(ny(2024, 1, 9, 9, 31), 99.5, 100.50, 99, 100.25),
        bar(ny(2024, 1, 9, 9, 32), 102.5, 103, 102, 102.5),
        bar(ny(2024, 1, 9, 9, 33), 102.5, 102.6, 97, 97.5),
        bar(ny(2024, 1, 9, 9, 34), 97.5, 98, 95, 96),
        bar(ny(2024, 1, 9, 9, 35), 99.5, 100.5, 99.5, 100.2),
        bar(ny(2024, 1, 9, 9, 36), 100, 100.2, 96, 97),
    ]
    plain = run_backtest(_spec(), bars)
    same = run_backtest(_spec(), bars, fill_bars=bars)
    assert [(t.entry_price, t.exit_price, t.exit_reason) for t in same.trades] == [
        (t.entry_price, t.exit_price, t.exit_reason) for t in plain.trades
    ]


def test_finer_fills_take_the_target_when_the_signal_bar_cannot_tell():
    signal_bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.25, 99.75, 100),
        bar(ny(2024, 1, 9, 9, 45), 100, 102.5, 95, 100),
    ]
    coarse = simulate(_short_spec(), signal_bars, [_signal()])
    assert coarse.trades[0].exit_reason == "stop"
    fill_bars = [
        signal_bars[0],
        bar(ny(2024, 1, 9, 9, 45), 100.5, 100.5, 95.5, 96),
        bar(ny(2024, 1, 9, 9, 46), 96, 102.5, 95.75, 102),
    ]
    fine = simulate(_short_spec(), signal_bars, [_signal()], fill_bars=fill_bars)
    assert fine.trades[0].exit_reason == "target"
    assert fine.trades[0].entry_price == 100.0
    assert fine.trades[0].exit_price == 96.0
