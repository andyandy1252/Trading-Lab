from datetime import timedelta

from engine.bars import Bar
from engine.strategies.raid_retrace import (
    Pool,
    RaidSetup,
    collect_pools,
    find_raid_setups,
    simulate_raid_setups,
)
from engine.tests.helpers import bar, ny


def _short_morning() -> list[Bar]:
    return [
        bar(ny(2026, 10, 21, 9, 0), 101, 101.5, 100.25, 100.5),
        bar(ny(2026, 10, 21, 9, 15), 100.5, 100.75, 99, 99.25),
        bar(ny(2026, 10, 21, 9, 30), 99.25, 99.5, 97, 97.25),
        bar(ny(2026, 10, 21, 9, 45), 97.25, 98.5, 97, 98.25),
        bar(ny(2026, 10, 21, 10, 0), 98.25, 99.25, 98, 99),
        bar(ny(2026, 10, 21, 10, 15), 99, 99.75, 98.75, 99.5),
        bar(ny(2026, 10, 21, 10, 30), 99.5, 99.6, 98.2, 98.3),
    ]


def _pool() -> list[Pool]:
    return [Pool(100.0, "buy_side", ny(2026, 10, 21, 8, 0), "1h")]


def test_short_needs_the_retrace_gap_to_invert_after_the_first_gap_is_respected():
    setups = find_raid_setups(_short_morning(), _pool(), tick_size=0.25)
    assert len(setups) == 1
    setup = setups[0]
    assert setup.side == "short"
    assert setup.signal_time == ny(2026, 10, 21, 10, 30)
    assert setup.level == 100.0
    assert setup.sweep_extreme == 101.5
    assert setup.source == "1h"


def test_no_trade_without_a_wick_into_the_displacement_gap():
    bars = _short_morning()
    bars[5] = bar(ny(2026, 10, 21, 10, 15), 99, 99.25, 98.75, 99.1)
    bars[6] = bar(ny(2026, 10, 21, 10, 30), 99.1, 99.2, 98.2, 98.3)
    assert find_raid_setups(bars, _pool(), tick_size=0.25) == []


def test_body_close_through_the_displacement_gap_kills_the_setup():
    bars = _short_morning()
    bars[5] = bar(ny(2026, 10, 21, 10, 15), 99, 100.75, 98.75, 100.5)
    assert find_raid_setups(bars, _pool(), tick_size=0.25) == []


def test_a_later_sweep_does_not_cancel_the_raid_already_working():
    pools = _pool() + [Pool(99.0, "buy_side", ny(2026, 10, 21, 8, 0), "15m")]
    setups = find_raid_setups(_short_morning(), pools, tick_size=0.25)
    assert len(setups) == 1
    assert setups[0].level == 100.0
    assert setups[0].sweep_extreme == 101.5
    assert setups[0].signal_time == ny(2026, 10, 21, 10, 30)


def test_inversion_outside_9_to_11_is_not_a_trade():
    bars = _short_morning()
    bars[6] = bar(ny(2026, 10, 21, 11, 15), 99.5, 99.6, 98.2, 98.3)
    assert find_raid_setups(bars, _pool(), tick_size=0.25) == []


def test_a_sweep_from_the_prior_cme_session_cannot_enter_the_next_morning():
    bars = [
        bar(ny(2026, 10, 21, 16, 0), 101, 101.5, 100.25, 100.5),
        bar(ny(2026, 10, 21, 16, 15), 100.5, 100.75, 99, 99.25),
        bar(ny(2026, 10, 21, 16, 30), 99.25, 99.5, 97, 97.25),
        bar(ny(2026, 10, 22, 9, 45), 97.25, 98.5, 97, 98.25),
        bar(ny(2026, 10, 22, 10, 0), 98.25, 99.25, 98, 99),
        bar(ny(2026, 10, 22, 10, 15), 99, 99.75, 98.75, 99.5),
        bar(ny(2026, 10, 22, 10, 30), 99.5, 99.6, 98.2, 98.3),
    ]
    pools = [Pool(100.0, "buy_side", ny(2026, 10, 21, 15, 0), "15m")]
    assert find_raid_setups(bars, pools, tick_size=0.25) == []


def test_long_is_the_mirror():
    bars = [
        bar(ny(2026, 10, 21, 9, 0), 99, 99.75, 98.5, 99.5),
        bar(ny(2026, 10, 21, 9, 15), 99.5, 101, 99.25, 100.75),
        bar(ny(2026, 10, 21, 9, 30), 100.75, 103, 100.5, 102.75),
        bar(ny(2026, 10, 21, 9, 45), 102.75, 103, 101.5, 101.75),
        bar(ny(2026, 10, 21, 10, 0), 101.75, 102, 100.75, 101),
        bar(ny(2026, 10, 21, 10, 15), 101, 101.25, 100.25, 100.5),
        bar(ny(2026, 10, 21, 10, 30), 100.5, 101.8, 100.4, 101.7),
    ]
    pools = [Pool(100.0, "sell_side", ny(2026, 10, 21, 8, 0), "4h")]
    setups = find_raid_setups(bars, pools, tick_size=0.25)
    assert len(setups) == 1
    assert setups[0].side == "long"
    assert setups[0].signal_time == ny(2026, 10, 21, 10, 30)
    assert setups[0].source == "4h"


def test_swing_pool_is_available_only_after_the_confirmation_bar_closes():
    bars = [
        bar(ny(2026, 10, 21, 8, 0), 100, 101, 99, 100),
        bar(ny(2026, 10, 21, 9, 0), 100, 105, 99, 104),
        bar(ny(2026, 10, 21, 10, 0), 104, 104.5, 100, 101),
    ]
    pools = collect_pools((bars, "1h"))
    assert pools == [Pool(105.0, "buy_side", ny(2026, 10, 21, 11, 0), "1h")]


def test_open_trade_flattens_at_11_and_the_third_entry_is_refused():
    quiet = [bar(ny(2026, 10, 21, 9, 0) + timedelta(minutes=15 * i), 100, 100.25, 99.75, 100) for i in range(8)]
    quiet.append(bar(ny(2026, 10, 21, 11, 0), 100, 100.25, 99.75, 100))
    held = simulate_raid_setups(
        [RaidSetup("short", ny(2026, 10, 21, 9, 0), ny(2026, 10, 21, 9, 0), 101.0, 100.0, "15m")],
        quiet,
        signal_minutes=15,
    )
    assert held[0].exit_reason == "time_stop"
    assert held[0].exit_time == ny(2026, 10, 21, 11, 0)
    assert held[0].entry_price == 99.75
    assert held[0].exit_price == 100.25
    assert held[0].pnl_usd == -15.0

    spiked = [
        bar(ny(2026, 10, 21, 9, 0), 100, 100.25, 99.75, 100),
        bar(ny(2026, 10, 21, 9, 15), 100, 101, 99.75, 100),
        bar(ny(2026, 10, 21, 9, 30), 100, 101, 99.75, 100),
        bar(ny(2026, 10, 21, 9, 45), 100, 101, 99.75, 100),
    ]
    setups = [
        RaidSetup("short", ny(2026, 10, 21, 9, 0), ny(2026, 10, 20, 9, 0), 100.0, 100.0, "15m"),
        RaidSetup("short", ny(2026, 10, 21, 9, 15), ny(2026, 10, 20, 9, 15), 100.0, 100.0, "15m"),
        RaidSetup("short", ny(2026, 10, 21, 9, 30), ny(2026, 10, 20, 9, 30), 100.0, 100.0, "15m"),
    ]
    stopped = simulate_raid_setups(setups, spiked, signal_minutes=15)
    assert len(stopped) == 2
    assert [trade.exit_reason for trade in stopped] == ["stop", "stop"]
