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

    def test_coarse_fill_resolution_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("coarse_fill_resolution.json"))
        assert "fill_resolution" in str(exc.value).lower()

    def test_bad_block_reference_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("bad_block_reference.json"))
        assert "block" in str(exc.value).lower() or "reference" in str(exc.value).lower()

    def test_duplicate_session_name_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("duplicate_session_name.json"))
        assert "session" in str(exc.value).lower()


class TestStopSideValidation:
    def test_stop_wrong_side_rejected(self):
        with pytest.raises(ValidationError) as exc:
            StrategySpec.model_validate(load_invalid("stop_wrong_side.json"))
        assert "stop" in str(exc.value).lower()


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
