import json

from engine.translate import TRANSLATOR_PROMPT, translate
from shared.spec import StrategySpec
from shared.tests.test_spec_model import load


def test_canonical_english_builds_a_valid_spec():
    english = (
        "Short NQ in NY AM after prior day high is swept, then a bearish FVG, "
        "limit at midpoint, stop 4 ticks above the sweep, 2R, 1 contract, $500 daily loss"
    )
    result = translate(english)
    assert result.ok
    assert result.spec is not None
    assert result.spec.instrument.value == "NQ"
    assert result.spec.entry.side == "short"
    assert result.spec.exit.stop.offset_ticks == 4
    assert result.spec.exit.target.value == 2.0
    assert result.spec.risk.daily_loss_stop_usd == 500
    assert result.spec.blocks[1].params["level"] == "pdh.high"
    assert result.spec.blocks[2].params["min_size_ticks"] == 0


def test_order_block_english_maps_when_cards_are_present():
    english = (
        "Short NQ in NY AM after they grab highs, wait for a break of structure, "
        "enter the order block, stop 4 ticks above the sweep, 2R, 1 contract, $500 daily loss"
    )
    result = translate(english)
    assert result.ok
    assert result.spec is not None
    types = [block.type for block in result.spec.blocks]
    assert "swing_points" in types
    assert "market_structure_shift" in types
    assert "order_block" in types
    assert result.spec.entry.price == "ob.midpoint"


def test_incomplete_order_block_asks_for_cards():
    result = translate("Enter the order block after they grab lows")
    assert not result.ok
    assert "Missing required cards" in (result.error or "")


def test_inverse_fvg_english_maps_when_cards_are_present():
    english = (
        "Short NQ in NY AM after prior day high is swept, then an inverse FVG, "
        "limit at midpoint, stop 4 ticks above the sweep, 2R, 1 contract, $500 daily loss"
    )
    result = translate(english)
    assert result.ok
    assert result.spec is not None
    types = [block.type for block in result.spec.blocks]
    assert "inverse_fvg" in types
    assert result.spec.entry.price == "ifvg.midpoint"


def test_pasted_json_is_validated():
    data = load("valid_spec.json")
    result = translate(json.dumps(data))
    assert result.ok
    assert result.spec is not None
    assert result.spec.name == data["name"]


def test_missing_cards_are_listed():
    result = translate("Trade NQ with a fair value gap")
    assert not result.ok
    assert "Missing required cards" in (result.error or "")
    assert "side" in (result.error or "")


def test_prompt_lists_allowed_blocks():
    assert "session_levels" in TRANSLATOR_PROMPT
    assert "order_block" in TRANSLATOR_PROMPT
    assert "fair_value_gap" in TRANSLATOR_PROMPT


def test_valid_spec_fixture_still_round_trips():
    spec = StrategySpec.model_validate(load("valid_spec.json"))
    result = translate(spec.model_dump_json())
    assert result.ok
