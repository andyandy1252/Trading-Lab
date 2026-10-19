from engine.blocks.liquidity_sweep import detect_liquidity_sweeps
from engine.tests.helpers import bar, ny

TICK = 0.25


def test_wick_through_high_is_a_buy_side_sweep():
    level = 100.0
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 99, 99.5, 98.5, 99),
        bar(ny(2024, 1, 9, 9, 31), 99, 100.50, 98.75, 99.25),
    ]
    levels = [level, level]
    starts = [ny(2024, 1, 8, 18, 0), ny(2024, 1, 8, 18, 0)]
    events = detect_liquidity_sweeps(
        bars, levels, starts, field="high", penetration_ticks=1, tick_size=TICK
    )
    assert len(events) == 1
    assert events[0].side == "buy_side"
    assert events[0].level == 100.0
    assert events[0].extreme == 100.50
    assert events[0].confirmed_at == bars[1].ts
    assert events[0].bar_index == 1


def test_tag_with_penetration_one_is_not_a_sweep():
    level = 100.0
    bars = [bar(ny(2024, 1, 9, 9, 30), 99, 100.0, 98.5, 99)]
    events = detect_liquidity_sweeps(
        bars, [level], [ny(2024, 1, 8, 18, 0)], field="high", penetration_ticks=1, tick_size=TICK
    )
    assert events == []


def test_tag_with_penetration_zero_is_a_sweep():
    level = 100.0
    bars = [bar(ny(2024, 1, 9, 9, 30), 99, 100.0, 98.5, 99)]
    events = detect_liquidity_sweeps(
        bars, [level], [ny(2024, 1, 8, 18, 0)], field="high", penetration_ticks=0, tick_size=TICK
    )
    assert len(events) == 1


def test_close_back_through_is_not_required():
    level = 100.0
    bars = [bar(ny(2024, 1, 9, 9, 30), 99, 100.50, 99, 100.25)]
    events = detect_liquidity_sweeps(
        bars, [level], [ny(2024, 1, 8, 18, 0)], field="high", penetration_ticks=1, tick_size=TICK
    )
    assert len(events) == 1
    assert events[0].extreme == 100.50


def test_still_through_the_same_level_is_not_a_second_sweep():
    level = 100.0
    start = ny(2024, 1, 8, 18, 0)
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 99, 100.50, 99, 100.25),
        bar(ny(2024, 1, 9, 9, 31), 100.25, 100.75, 100.0, 100.5),
    ]
    events = detect_liquidity_sweeps(
        bars, [level, level], [start, start], field="high", penetration_ticks=1, tick_size=TICK
    )
    assert len(events) == 1
    assert events[0].bar_index == 0


def test_recross_after_leaving_is_a_new_sweep():
    level = 100.0
    start = ny(2024, 1, 8, 18, 0)
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 99, 100.50, 99, 100.25),
        bar(ny(2024, 1, 9, 9, 31), 99, 99.75, 98.5, 99),
        bar(ny(2024, 1, 9, 9, 32), 99, 100.75, 99, 100),
    ]
    events = detect_liquidity_sweeps(
        bars,
        [level, level, level],
        [start, start, start],
        field="high",
        penetration_ticks=1,
        tick_size=TICK,
    )
    assert [e.bar_index for e in events] == [0, 2]


def test_sell_side_sweep_of_a_low():
    level = 100.0
    bars = [bar(ny(2024, 1, 9, 9, 30), 101, 101.5, 99.50, 100.5)]
    events = detect_liquidity_sweeps(
        bars, [level], [ny(2024, 1, 8, 18, 0)], field="low", penetration_ticks=1, tick_size=TICK
    )
    assert len(events) == 1
    assert events[0].side == "sell_side"
    assert events[0].extreme == 99.50


def test_missing_level_does_not_sweep():
    bars = [bar(ny(2024, 1, 9, 9, 30), 99, 110, 98, 100)]
    events = detect_liquidity_sweeps(
        bars, [None], [None], field="high", penetration_ticks=1, tick_size=TICK
    )
    assert events == []
