from engine.blocks.fair_value_gap import detect_fair_value_gaps
from engine.blocks.inverse_fvg import detect_inverse_fvgs
from engine.tests.helpers import bar, ny

TICK = 0.25


def test_body_close_through_far_edge_inverts_a_bullish_gap():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100.5),
        bar(ny(2024, 1, 9, 9, 31), 100.5, 110, 100.4, 109),
        bar(ny(2024, 1, 9, 9, 32), 109, 112, 108, 111),
        bar(ny(2024, 1, 9, 9, 33), 108, 108.5, 100, 100.5),
    ]
    gaps = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=0, tick_size=TICK)
    events = detect_inverse_fvgs(bars, gaps, direction="bearish")
    assert len(events) == 1
    assert events[0].direction == "bearish"
    assert events[0].far_edge == 101.0
    assert events[0].near_edge == 108.0
    assert events[0].bar_index == 3
    assert events[0].midpoint == 104.5


def test_wick_into_the_gap_is_not_an_inversion():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100.5),
        bar(ny(2024, 1, 9, 9, 31), 100.5, 110, 100.4, 109),
        bar(ny(2024, 1, 9, 9, 32), 109, 112, 108, 111),
        bar(ny(2024, 1, 9, 9, 33), 110, 111, 100.5, 109),
    ]
    gaps = detect_fair_value_gaps(bars, direction="bullish", min_size_ticks=0, tick_size=TICK)
    events = detect_inverse_fvgs(bars, gaps, direction="bearish")
    assert events == []


def test_bearish_gap_inverts_on_close_above_far_edge():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 110, 111, 109, 109.5),
        bar(ny(2024, 1, 9, 9, 31), 109.5, 109.6, 100, 101),
        bar(ny(2024, 1, 9, 9, 32), 101, 102, 99, 100),
        bar(ny(2024, 1, 9, 9, 33), 102, 110, 101.5, 109.5),
    ]
    gaps = detect_fair_value_gaps(bars, direction="bearish", min_size_ticks=0, tick_size=TICK)
    events = detect_inverse_fvgs(bars, gaps, direction="bullish")
    assert len(events) == 1
    assert events[0].direction == "bullish"
    assert events[0].far_edge == 109.0
