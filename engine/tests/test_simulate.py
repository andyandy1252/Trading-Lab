from engine.events import BoundEvent, Signal
from engine.simulate import simulate
from engine.tests.helpers import bar, ny
from shared.spec.model import StrategySpec

TICK = 0.25


def _spec(**overrides) -> StrategySpec:
    data = {
        "spec_version": "1.0",
        "name": "sim",
        "instrument": "NQ",
        "signal_timeframe": "1m",
        "fill_resolution": "1m",
        "ai_model_version": "test",
        "asset_class": "futures",
        "execution_latency_class": "batch",
        "sessions": [
            {
                "name": "ny_am",
                "tz": "America/New_York",
                "start": "09:30",
                "end": "11:00",
                "days": [1, 2, 3, 4, 5],
            }
        ],
        "blocks": [
            {
                "id": "pdh",
                "type": "session_levels",
                "params": {
                    "session": "ny_am",
                    "levels": ["high"],
                    "which": "prior_completed",
                },
            },
            {
                "id": "sweep",
                "type": "liquidity_sweep",
                "params": {"level": "pdh.high", "penetration_ticks": 1},
            },
            {
                "id": "fvg",
                "type": "fair_value_gap",
                "params": {"direction": "bearish", "min_size_ticks": 0},
            },
        ],
        "entry": {
            "side": "short",
            "when": [{"id": "sweep"}],
            "order": "market",
        },
        "exit": {
            "stop": {"ref": "sweep.extreme", "offset_ticks": 4},
            "target": {"type": "rr", "value": 2.0},
            "time_stop": {"type": "session_end", "session": "ny_am"},
        },
        "risk": {
            "contracts": 1,
            "session": "ny_am",
            "max_trades_per_session": 2,
            "daily_loss_stop_usd": 500.0,
        },
        "costs": {
            "commission_per_side_usd": 2.5,
            "market_slippage_ticks": 1,
            "news_open_slippage_ticks": 3,
            "limit_through_ticks": 1,
        },
        "meta": {"source": "test", "source_prompt": "test", "parent_version": None},
    }
    for key, value in overrides.items():
        data[key] = value
    return StrategySpec.model_validate(data)


def _signal(bar_index: int = 0, extreme: float = 101.0, midpoint: float = 100.0) -> Signal:
    return Signal(
        bar_index=bar_index,
        bound={
            "sweep": BoundEvent(
                "sweep",
                bar_index,
                {"extreme": extreme, "level": 100.0, "side": "buy_side"},
            ),
            "fvg": BoundEvent(
                "fvg",
                bar_index,
                {"midpoint": midpoint, "near_edge": 99.0, "far_edge": 101.0},
            ),
        },
    )


def test_market_short_fills_next_open_minus_slippage():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 99.25, 98.5, 98.75),
        bar(ny(2024, 1, 9, 10, 59), 98.75, 98.75, 90.0, 90.0),
    ]
    result = simulate(spec, bars, [_signal(0)])
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_price == 99.0 - TICK
    assert trade.side == "short"


def test_no_fill_on_the_signal_bar():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 110, 90, 100),
    ]
    result = simulate(spec, bars, [_signal(0)])
    assert result.trades == []


def test_same_bar_stop_and_target_fills_the_stop():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 110.0, 80.0, 90.0),
    ]
    result = simulate(spec, bars, [_signal(0, extreme=101.0)])
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    stop_price = 101.0 + 4 * TICK
    assert trade.exit_price == stop_price + TICK


def test_limit_sell_fills_at_limit_after_trade_through():
    data = _spec().model_dump()
    data["entry"]["order"] = "limit"
    data["entry"]["price"] = "fvg.midpoint"
    data["entry"]["expire_bars"] = 10
    spec = StrategySpec.model_validate(data)
    midpoint = 100.0
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 99, 99.5, 98.5, 99),
        bar(ny(2024, 1, 9, 9, 31), 99, 100.50, 99, 100),
        bar(ny(2024, 1, 9, 10, 59), 100, 100, 90, 90),
    ]
    result = simulate(spec, bars, [_signal(0, midpoint=midpoint)])
    assert len(result.trades) == 1
    assert result.trades[0].entry_price == midpoint
    assert result.trades[0].entry_time == bars[1].ts


def test_commission_is_charged_both_sides():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 99.0, 80.0, 80.0),
    ]
    result = simulate(spec, bars, [_signal(0)])
    trade = result.trades[0]
    assert trade.pnl_usd < 0 or trade.commission_usd == 5.0
    assert trade.commission_usd == 5.0


def test_wrong_side_stop_does_not_enter():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 99.25, 98.5, 98.75),
        bar(ny(2024, 1, 9, 10, 59), 98.75, 98.75, 90.0, 90.0),
    ]
    result = simulate(spec, bars, [_signal(0, extreme=90.0)])
    assert result.trades == []


def test_time_stop_flattens_at_session_end():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 99.0, 98.5, 98.75),
        bar(ny(2024, 1, 9, 11, 0), 98.75, 99.0, 98.5, 98.6),
    ]
    result = simulate(spec, bars, [_signal(0)])
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "time_stop"
    assert result.trades[0].exit_price == 98.75 + TICK


def test_second_signal_ignored_while_in_trade():
    spec = _spec()
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 99.0, 98.5, 98.75),
        bar(ny(2024, 1, 9, 9, 32), 98.75, 99.0, 98.5, 98.6),
        bar(ny(2024, 1, 9, 10, 59), 98.6, 98.6, 90.0, 90.0),
    ]
    result = simulate(spec, bars, [_signal(0), _signal(1)])
    assert len(result.trades) == 1


def test_max_trades_per_session_caps_fills():
    data = _spec().model_dump()
    data["risk"]["max_trades_per_session"] = 1
    spec = StrategySpec.model_validate(data)
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 110, 80, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 110.0, 80.0, 90.0),
        bar(ny(2024, 1, 9, 9, 32), 90.0, 90.0, 89.0, 89.5),
        bar(ny(2024, 1, 9, 9, 33), 89.5, 110.0, 80.0, 90.0),
    ]
    result = simulate(spec, bars, [_signal(0), _signal(2)])
    assert len(result.trades) == 1


def test_daily_loss_flattens_next_open_and_blocks_entries():
    data = _spec().model_dump()
    data["risk"]["daily_loss_stop_usd"] = 1.0
    spec = StrategySpec.model_validate(data)
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 100.5, 99.5, 100),
        bar(ny(2024, 1, 9, 9, 31), 99.0, 100.0, 98.5, 101.0),
        bar(ny(2024, 1, 9, 9, 32), 101.0, 101.5, 100.5, 101.0),
        bar(ny(2024, 1, 9, 9, 33), 101.0, 110.0, 80.0, 90.0),
    ]
    result = simulate(spec, bars, [_signal(0), _signal(2)])
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "daily_loss"
