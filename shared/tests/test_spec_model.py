import json
import pytest
from pathlib import Path
from pydantic import ValidationError
from shared.spec import StrategySpec

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def load_invalid(name: str) -> dict:
    return json.loads((FIXTURES / "invalid" / name).read_text())


class TestValidSpec:
    def test_valid_spec_loads(self):
        data = load("valid_spec.json")
        spec = StrategySpec.model_validate(data)
        assert spec.name == "NQ prior high sweep then bearish FVG"
        assert spec.instrument.value == "NQ"
        assert spec.spec_version == "1.0"

    def test_valid_spec_has_required_fields(self):
        data = load("valid_spec.json")
        spec = StrategySpec.model_validate(data)
        assert spec.costs is not None
        assert spec.risk is not None
        assert spec.entry is not None
        assert spec.exit is not None
        assert len(spec.sessions) >= 1
        assert len(spec.blocks) >= 1

    def test_valid_spec_has_ai_model_version(self):
        data = load("valid_spec.json")
        spec = StrategySpec.model_validate(data)
        assert spec.ai_model_version != ""

    def test_valid_spec_has_execution_latency_class(self):
        data = load("valid_spec.json")
        spec = StrategySpec.model_validate(data)
        assert spec.execution_latency_class in ("real-time", "near-real-time", "batch")


class TestSpecRejections:
    def test_missing_instrument_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("missing_instrument.json"))
        assert "instrument" in str(exc.value)

    def test_missing_costs_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("missing_costs.json"))
        assert "costs" in str(exc.value)

    def test_invalid_fill_resolution_value_rejected(self):
        # SPEC.md L136: fill_resolution may only be "1s" or "1m". A value
        # outside that set (here "15m") is rejected by the type constraint.
        # NOTE: this does NOT exercise the same-or-finer-than-signal rule --
        # with the only legal values that rule can never be violated. See
        # test_all_legal_timeframe_fill_combinations_accepted and TestDeferredRules.
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("invalid_fill_resolution_value.json"))
        assert "fill_resolution" in str(exc.value).lower()

    def test_bad_block_reference_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("bad_block_reference.json"))
        assert "block" in str(exc.value).lower() or "reference" in str(exc.value).lower()

    def test_duplicate_session_name_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("duplicate_session_name.json"))
        assert "session" in str(exc.value).lower()

    def test_order_block_is_an_allowed_type(self):
        data = load("valid_spec.json")
        data["blocks"].append(
            {
                "id": "ob",
                "type": "order_block",
                "params": {"sweep": "sweep", "mss": "mss", "swings": "swings"},
            }
        )
        spec = StrategySpec.model_validate(data)
        assert spec.blocks[-1].type == "order_block"

    def test_inverse_fvg_is_an_allowed_type(self):
        data = load("valid_spec.json")
        data["blocks"].append(
            {
                "id": "ifvg",
                "type": "inverse_fvg",
                "params": {"gap": "fvg", "direction": "bearish"},
            }
        )
        spec = StrategySpec.model_validate(data)
        assert spec.blocks[-1].type == "inverse_fvg"

    def test_glossary_block_types_are_allowed(self):
        data = load("valid_spec.json")
        extra = [
            {"id": "swings", "type": "swing_points", "params": {"kind": "both"}},
            {
                "id": "mss",
                "type": "market_structure_shift",
                "params": {"direction": "bearish", "swings": "swings"},
            },
            {
                "id": "eq",
                "type": "equilibrium",
                "params": {"swings": "swings", "location": "premium"},
            },
        ]
        data["blocks"].extend(extra)
        spec = StrategySpec.model_validate(data)
        assert [b.type for b in spec.blocks[-3:]] == [
            "swing_points",
            "market_structure_shift",
            "equilibrium",
        ]

    def test_unknown_block_type_rejected(self):
        data = load("valid_spec.json")
        data["blocks"][0]["type"] = "unicorn"
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(data)
        assert "type" in str(exc.value).lower()


# SPEC.md L138 (signal timeframes) and L136 (fill resolutions). Listed here
# as an independent source of truth, not imported from the model under test.
SIGNAL_TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "1h", "4h"]
FILL_RESOLUTIONS = ["1s", "1m"]


@pytest.mark.parametrize(
    "signal,fill",
    [(s, f) for s in SIGNAL_TIMEFRAMES for f in FILL_RESOLUTIONS],
)
def test_all_legal_timeframe_fill_combinations_accepted(signal, fill):
    # Every legal (signal_timeframe, fill_resolution) pair satisfies the
    # same-or-finer rule (SPEC.md L136), so none should be rejected. This
    # replaces the old coarse-fill test, which only proved an illegal enum
    # value was rejected -- not that the granularity rule behaves.
    data = load("valid_spec.json")
    data["signal_timeframe"] = signal
    data["fill_resolution"] = fill
    spec = StrategySpec.model_validate(data)
    assert spec.signal_timeframe == signal
    assert spec.fill_resolution == fill


class TestStopSideValidation:
    def test_negative_stop_offset_rejected(self):
        # SPEC.md L169: offset_ticks is "zero or greater". A negative value is
        # rejected by StopExit.offset_ticks = Field(ge=0). This enforces
        # non-negativity ONLY -- not the full protective-side rule, which
        # needs the entry fill price (runtime). See TestDeferredRules.
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("negative_stop_offset.json"))
        assert "offset_ticks" in str(exc.value)


class TestDeferredRules:
    """SPEC rules Phase 1 cannot enforce statically. Kept as skips so the gaps
    stay visible in the suite instead of masquerading as passing coverage."""

    @pytest.mark.skip(
        reason="SPEC.md L169: protective-side check compares the stop to the "
        "entry FILL price; deferred to Phase 2 fill simulation."
    )
    def test_stop_protective_side_enforced(self):
        raise NotImplementedError

    @pytest.mark.skip(
        reason="SPEC.md L136: with the only legal fill values (1s, 1m), a fill "
        "coarser than the signal cannot be expressed; validator is defensive only."
    )
    def test_coarse_fill_resolution_rejected_by_granularity_rule(self):
        raise NotImplementedError


class TestCrossFieldValidation:
    def test_limit_through_ticks_minimum_is_one(self):
        data = load("valid_spec.json")
        data["costs"]["limit_through_ticks"] = 0
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(data)

    def test_contracts_minimum_is_one(self):
        data = load("valid_spec.json")
        data["risk"]["contracts"] = 0
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(data)

    def test_offset_ticks_zero_is_allowed(self):
        data = load("valid_spec.json")
        data["exit"]["stop"]["offset_ticks"] = 0
        spec = StrategySpec.model_validate(data)
        assert spec.exit.stop.offset_ticks == 0

    def test_offset_ticks_negative_rejected(self):
        data = load("valid_spec.json")
        data["exit"]["stop"]["offset_ticks"] = -1
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(data)

    def test_session_name_referenced_in_risk_must_exist(self):
        data = load("valid_spec.json")
        data["risk"]["session"] = "nonexistent_session"
        with pytest.raises(ValidationError):
            StrategySpec.model_validate(data)
