from engine.blocks.equilibrium import detect_equilibrium
from engine.blocks.swing_points import detect_swing_points
from engine.tests.helpers import bar, ny


def _range_tape():
    return [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100),
        bar(ny(2024, 1, 9, 9, 31), 100, 100, 90, 91),
        bar(ny(2024, 1, 9, 9, 32), 91, 95, 91, 94),
        bar(ny(2024, 1, 9, 9, 33), 94, 110, 94, 108),
        bar(ny(2024, 1, 9, 9, 34), 108, 108, 100, 101),
        bar(ny(2024, 1, 9, 9, 35), 101, 102, 85, 85),
    ]


def test_close_below_midpoint_is_discount():
    bars = _range_tape()
    swings = detect_swing_points(bars, kind="both")
    events = detect_equilibrium(bars, swings, location="discount")
    last = [e for e in events if e.bar_index == 5]
    assert last
    assert last[0].location == "discount"
    assert last[0].eq == (110 + 90) / 2


def test_close_above_midpoint_is_premium():
    bars = _range_tape()[:5]
    swings = detect_swing_points(bars, kind="both")
    events = detect_equilibrium(bars, swings, location="premium")
    assert events[-1].bar_index == 4
    assert events[-1].location == "premium"
