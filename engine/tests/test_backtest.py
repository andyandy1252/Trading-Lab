from engine.backtest import run_backtest
from engine.tests.helpers import bar, ny
from shared.spec.model import StrategySpec


def _spec() -> StrategySpec:
    return StrategySpec.model_validate(
        {
            "spec_version": "1.0",
            "name": "pdh sweep fvg",
            "instrument": "NQ",
            "signal_timeframe": "1m",
            "fill_resolution": "1m",
            "ai_model_version": "test",
            "asset_class": "futures",
            "execution_latency_class": "batch",
            "sessions": [
                {
                    "name": "cme_eth",
                    "tz": "America/New_York",
                    "start": "18:00",
                    "end": "17:00",
                    "days": [7, 1, 2, 3, 4],
                },
                {
                    "name": "ny_am",
                    "tz": "America/New_York",
                    "start": "09:30",
                    "end": "11:00",
                    "days": [1, 2, 3, 4, 5],
                },
            ],
            "blocks": [
                {
                    "id": "pdh",
                    "type": "session_levels",
                    "params": {
                        "session": "cme_eth",
                        "levels": ["high", "low"],
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
                "when": [
                    {"id": "sweep"},
                    {"id": "fvg", "after": "sweep", "within_bars": 20},
                ],
                "order": "limit",
                "price": "fvg.midpoint",
                "expire_bars": 10,
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
            "meta": {
                "source": "test",
                "source_prompt": "pdh sweep then fvg",
                "parent_version": None,
            },
        }
    )


def test_run_backtest_pdh_sweep_then_bearish_fvg():
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
    result = run_backtest(_spec(), bars)
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.side == "short"
    assert trade.entry_price == 100.0
    assert trade.exit_reason == "target"
