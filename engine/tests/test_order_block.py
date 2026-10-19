from engine.blocks.liquidity_sweep import detect_liquidity_sweeps
from engine.blocks.market_structure import detect_market_structure_shifts
from engine.blocks.order_block import detect_order_blocks
from engine.blocks.swing_points import detect_swing_points
from engine.tests.helpers import bar, ny

TICK = 0.25


def _buy_side_then_bearish_mss():
    # Swing low at 98 (middle bar 1), swing high at 104 (middle bar 4),
    # then wick through 104, then body close below 98.
    return [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100),
        bar(ny(2024, 1, 9, 9, 31), 100, 100, 98, 99),
        bar(ny(2024, 1, 9, 9, 32), 99, 101, 99, 100),
        bar(ny(2024, 1, 9, 9, 33), 100, 103, 100, 102),
        bar(ny(2024, 1, 9, 9, 34), 102, 104, 102, 103),
        bar(ny(2024, 1, 9, 9, 35), 103, 103.5, 102, 102.5),
        bar(ny(2024, 1, 9, 9, 36), 103, 105, 102.5, 104),
        bar(ny(2024, 1, 9, 9, 37), 104, 104.5, 97, 97.5),
    ]


def test_bearish_order_block_is_the_up_leg_that_caused_the_sweep():
    bars = _buy_side_then_bearish_mss()
    swings = detect_swing_points(bars, kind="both")
    highs = [p.high for p in swings]
    starts = [p.session_start if p.high is not None else None for p in swings]
    sweeps = detect_liquidity_sweeps(
        bars, highs, starts, field="high", penetration_ticks=1, tick_size=TICK
    )
    shifts = detect_market_structure_shifts(bars, swings, direction="bearish")
    blocks = detect_order_blocks(bars, sweeps, shifts, swings)
    assert len(sweeps) >= 1
    assert len(shifts) == 1
    assert len(blocks) == 1
    ob = blocks[0]
    assert ob.direction == "bearish"
    assert ob.low == 98
    assert ob.high == sweeps[0].extreme
    assert ob.midpoint == (ob.high + ob.low) / 2
    assert ob.bar_index == shifts[0].bar_index


def test_no_order_block_without_mss():
    bars = _buy_side_then_bearish_mss()[:-1]
    swings = detect_swing_points(bars, kind="both")
    highs = [p.high for p in swings]
    starts = [p.session_start if p.high is not None else None for p in swings]
    sweeps = detect_liquidity_sweeps(
        bars, highs, starts, field="high", penetration_ticks=1, tick_size=TICK
    )
    shifts = detect_market_structure_shifts(bars, swings, direction="bearish")
    blocks = detect_order_blocks(bars, sweeps, shifts, swings)
    assert shifts == []
    assert blocks == []
