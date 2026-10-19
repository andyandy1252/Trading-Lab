from engine.blocks.market_structure import detect_market_structure_shifts
from engine.blocks.swing_points import detect_swing_points
from engine.tests.helpers import bar, ny


def _tape_then(extra):
    base = [
        bar(ny(2024, 1, 9, 9, 30), 102, 102, 100, 101),
        bar(ny(2024, 1, 9, 9, 31), 101, 101, 98, 99),
        bar(ny(2024, 1, 9, 9, 32), 99, 101, 99, 100),
    ]
    return base + extra


def test_body_close_below_last_swing_low_is_bearish_mss():
    bars = _tape_then(
        [bar(ny(2024, 1, 9, 9, 33), 100, 100.5, 97, 97.5)]
    )
    swings = detect_swing_points(bars, kind="both")
    events = detect_market_structure_shifts(bars, swings, direction="bearish")
    assert len(events) == 1
    assert events[0].direction == "bearish"
    assert events[0].level == 98
    assert events[0].bar_index == 3


def test_wick_through_swing_low_is_not_mss():
    bars = _tape_then(
        [bar(ny(2024, 1, 9, 9, 33), 100, 101, 97, 99.5)]
    )
    swings = detect_swing_points(bars, kind="both")
    events = detect_market_structure_shifts(bars, swings, direction="bearish")
    assert events == []


def test_body_close_above_last_swing_high_is_bullish_mss():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 10, 10, 9, 9.5),
        bar(ny(2024, 1, 9, 9, 31), 10, 12, 10, 11),
        bar(ny(2024, 1, 9, 9, 32), 11, 11, 10, 10.5),
        bar(ny(2024, 1, 9, 9, 33), 11, 13, 11, 12.5),
    ]
    swings = detect_swing_points(bars, kind="both")
    events = detect_market_structure_shifts(bars, swings, direction="bullish")
    assert len(events) == 1
    assert events[0].direction == "bullish"
    assert events[0].level == 12
