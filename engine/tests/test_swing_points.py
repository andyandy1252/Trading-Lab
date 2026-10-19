from engine.blocks.swing_points import detect_swing_points
from engine.tests.helpers import bar, ny


def test_three_candle_swing_high():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 10, 10, 9, 9.5),
        bar(ny(2024, 1, 9, 9, 31), 10, 12, 10, 11),
        bar(ny(2024, 1, 9, 9, 32), 11, 11, 10, 10.5),
    ]
    points = detect_swing_points(bars, kind="high")
    assert points[0].high is None
    assert points[1].high is None
    assert points[2].high == 12
    assert points[2].session_start == bars[1].ts


def test_three_candle_swing_low():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 12, 12, 10, 11),
        bar(ny(2024, 1, 9, 9, 31), 11, 11, 8, 9),
        bar(ny(2024, 1, 9, 9, 32), 9, 11, 9, 10),
    ]
    points = detect_swing_points(bars, kind="low")
    assert points[2].low == 8
    assert points[2].session_start == bars[1].ts


def test_latest_swing_high_is_replaced_by_the_next_fractal():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 10, 10, 9, 9.5),
        bar(ny(2024, 1, 9, 9, 31), 10, 12, 10, 11),
        bar(ny(2024, 1, 9, 9, 32), 11, 11, 10, 10.5),
        bar(ny(2024, 1, 9, 9, 33), 10.5, 14, 10.5, 13),
        bar(ny(2024, 1, 9, 9, 34), 13, 13, 12, 12.5),
    ]
    points = detect_swing_points(bars, kind="high")
    assert points[2].high == 12
    assert points[4].high == 14


def test_equal_side_highs_are_not_a_swing():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 10, 12, 9, 11),
        bar(ny(2024, 1, 9, 9, 31), 11, 12, 10, 11),
        bar(ny(2024, 1, 9, 9, 32), 11, 12, 10, 11),
    ]
    points = detect_swing_points(bars, kind="high")
    assert points[2].high is None
