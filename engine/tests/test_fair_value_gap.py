from engine.blocks.fair_value_gap import detect_fair_value_gaps
from engine.tests.helpers import bar, ny

TICK = 0.25


def test_bullish_wick_to_wick_gap():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100.5),
        bar(ny(2024, 1, 9, 9, 31), 100.5, 110, 100.4, 109),
        bar(ny(2024, 1, 9, 9, 32), 109, 112, 108, 111),
    ]
    events = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=0, tick_size=TICK)
    assert len(events) == 1
    gap = events[0]
    assert gap.near_edge == 108.0
    assert gap.far_edge == 101.0
    assert gap.midpoint == 104.5
    assert gap.formed_at == bars[2].ts
    assert gap.size_ticks == (108.0 - 101.0) / TICK


def test_overlapping_wicks_are_not_a_gap():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100.5),
        bar(ny(2024, 1, 9, 9, 31), 100.5, 102, 100, 101),
        bar(ny(2024, 1, 9, 9, 32), 101, 103, 100.5, 102),
    ]
    events = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=0, tick_size=TICK)
    assert events == []


def test_bearish_wick_to_wick_gap():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 110, 111, 109, 109.5),
        bar(ny(2024, 1, 9, 9, 31), 109.5, 109.6, 100, 101),
        bar(ny(2024, 1, 9, 9, 32), 101, 102, 99, 100),
    ]
    events = detect_fair_value_gaps(bars, direction="bearish", min_size_ticks=0, tick_size=TICK)
    assert len(events) == 1
    gap = events[0]
    assert gap.near_edge == 102.0
    assert gap.far_edge == 109.0
    assert gap.formed_at == bars[2].ts


def test_min_size_ticks_filters_small_gaps():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100.5),
        bar(ny(2024, 1, 9, 9, 31), 100.5, 103, 100.4, 102),
        bar(ny(2024, 1, 9, 9, 32), 102, 104, 101.5, 103),
    ]
    none = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=8, tick_size=TICK)
    kept = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=0, tick_size=TICK)
    assert none == []
    assert len(kept) == 1


def test_every_qualifying_window_is_kept():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100.5),
        bar(ny(2024, 1, 9, 9, 31), 100.5, 110, 100.4, 109),
        bar(ny(2024, 1, 9, 9, 32), 109, 112, 108, 111),
        bar(ny(2024, 1, 9, 9, 33), 112, 118, 111.5, 117),
    ]
    events = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=0, tick_size=TICK)
    assert len(events) == 2
    assert events[0].bar_index == 2
    assert events[1].bar_index == 3
