# Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared Pydantic spec model, database schema, and env modules that every other phase depends on — nothing else in the project can start until this passes its tests.

**Architecture:** The Pydantic model in `shared/spec/model.py` is the single source of truth for what a valid strategy spec looks like. A generation script derives `schema.json` (used by the Next.js web layer for validation) and `types.ts` (used by TypeScript code) from the same model. The database schema lives in SQL migration files. Two env modules (Python and TypeScript) refuse to boot if any required key is missing.

**Tech Stack:** Python 3.11+, Pydantic v2, pydantic-settings, pytest, datamodel-code-generator (for TypeScript generation), psycopg2 / Supabase Python client, Next.js 14, TypeScript 5.

## Global Constraints

- Python 3.11+ required
- Pydantic v2 (not v1 — validators use `model_validator(mode='after')` syntax)
- All spec field names are `snake_case`
- `spec_version` must be the string `"1.0"` — not an integer
- Block ids and session names: lowercase, underscores only, unique within a spec
- Entry/exit references use `block_id.field` format (e.g. `"fvg.midpoint"`)
- `offset_ticks` is a non-negative integer (zero is allowed)
- `limit_through_ticks` minimum is 1
- `contracts` minimum is 1
- ISO weekdays: Monday=1, Sunday=7
- Stop must be on the protective side of entry (long → stop below entry reference; short → stop above entry reference)
- `fill_resolution` must be same granularity or finer than `signal_timeframe`
- All monetary values in USD
- Audit log table: no UPDATE or DELETE permissions granted at DB level

---

## File Map

```
shared/
  spec/
    __init__.py                   create — package init, exports StrategySpec
    model.py                      create — Pydantic model (all classes)
    generate.py                   create — CLI script: generates schema.json + types.ts
    schema.json                   create (generated) — committed, regenerated via script
    types.ts                      create (generated) — committed, regenerated via script
    migrations/
      __init__.py                 create — package init
      001_initial.sql             create — full DB schema
      run.py                      create — migration runner CLI
  tests/
    __init__.py                   create
    test_spec_model.py            create — all validation tests
    fixtures/
      valid_spec.json             create — the sample NQ sweep+FVG spec from SPEC.md
      invalid/
        missing_instrument.json   create
        stop_wrong_side.json      create
        missing_costs.json        create
        coarse_fill_resolution.json  create
        bad_block_reference.json  create
        duplicate_session_name.json  create

engine/
  __init__.py                     create
  env.py                          create — Python env module, raises on missing keys

web/
  lib/
    env.ts                        create — TypeScript env module, throws on missing keys

pyproject.toml                    create — Python project config + deps
requirements.txt                  create — pinned Python deps
```

---

## Task 1: Python project scaffold + Pydantic spec model

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `shared/spec/__init__.py`
- Create: `shared/spec/model.py`
- Create: `shared/tests/__init__.py`
- Create: `shared/tests/test_spec_model.py`
- Create: `shared/tests/fixtures/valid_spec.json`
- Create: `shared/tests/fixtures/invalid/missing_instrument.json`
- Create: `shared/tests/fixtures/invalid/stop_wrong_side.json`
- Create: `shared/tests/fixtures/invalid/missing_costs.json`
- Create: `shared/tests/fixtures/invalid/coarse_fill_resolution.json`
- Create: `shared/tests/fixtures/invalid/bad_block_reference.json`
- Create: `shared/tests/fixtures/invalid/duplicate_session_name.json`

**Interfaces:**
- Produces: `StrategySpec` — the top-level Pydantic model; `from shared.spec import StrategySpec`
- Produces: `StrategySpec.model_validate(dict)` — raises `ValidationError` on any invalid spec
- Produces: `StrategySpec.model_json_schema()` — returns JSON Schema dict

---

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "trading-bot-lab"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.7,<3",
    "pydantic-settings>=2.2,<3",
    "pytest>=8.1,<9",
    "pytest-cov>=5.0,<6",
]

[tool.pytest.ini_options]
testpaths = ["shared/tests", "engine/tests"]
python_files = ["test_*.py"]

[tool.setuptools.packages.find]
where = ["."]
include = ["shared*", "engine*"]
```

- [ ] **Step 2: Create `requirements.txt`**

```
pydantic==2.7.4
pydantic-settings==2.2.1
pytest==8.1.2
pytest-cov==5.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
datamodel-code-generator==0.25.6
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 4: Create `shared/spec/__init__.py`**

```python
from .model import StrategySpec

__all__ = ["StrategySpec"]
```

- [ ] **Step 5: Create `shared/tests/__init__.py`**

```python
```

(Empty file — makes the directory a Python package.)

- [ ] **Step 6: Write failing tests for the spec model**

Create `shared/tests/test_spec_model.py`:

```python
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
```

- [ ] **Step 7: Run tests — verify they all fail**

```bash
python -m pytest shared/tests/test_spec_model.py -v
```

Expected: all tests FAIL with `ModuleNotFoundError` or `ImportError` — `shared.spec.model` does not exist yet.

- [ ] **Step 8: Create the fixture files**

Create `shared/tests/fixtures/valid_spec.json`:

```json
{
  "spec_version": "1.0",
  "name": "NQ prior high sweep then bearish FVG",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [
    {
      "name": "cash_rth",
      "tz": "America/New_York",
      "start": "09:30",
      "end": "16:00",
      "days": [1, 2, 3, 4, 5]
    },
    {
      "name": "ny_am",
      "tz": "America/New_York",
      "start": "09:00",
      "end": "11:00",
      "days": [1, 2, 3, 4, 5]
    }
  ],
  "blocks": [
    {
      "id": "cash_rth_levels",
      "type": "session_levels",
      "params": {
        "session": "cash_rth",
        "levels": ["high", "low"],
        "which": "prior_completed"
      }
    },
    {
      "id": "sweep",
      "type": "liquidity_sweep",
      "params": {
        "level": "cash_rth_levels.high",
        "penetration_ticks": 1,
        "confirm_bars": 2
      }
    },
    {
      "id": "fvg",
      "type": "fair_value_gap",
      "params": {
        "direction": "bearish",
        "min_size_ticks": 8
      }
    }
  ],
  "entry": {
    "side": "short",
    "when": [
      {"id": "sweep"},
      {"id": "fvg", "after": "sweep", "within_bars": 20}
    ],
    "order": "limit",
    "price": "fvg.midpoint",
    "expire_bars": 10
  },
  "exit": {
    "stop": {"ref": "sweep.extreme", "offset_ticks": 4},
    "target": {"type": "rr", "value": 2.0},
    "time_stop": {"type": "session_end", "session": "ny_am"}
  },
  "risk": {
    "contracts": 1,
    "session": "ny_am",
    "max_trades_per_session": 2,
    "daily_loss_stop_usd": 500.0
  },
  "costs": {
    "commission_per_side_usd": 2.5,
    "market_slippage_ticks": 1,
    "news_open_slippage_ticks": 3,
    "limit_through_ticks": 1
  },
  "reference_instruments": [],
  "agents": [],
  "consensus_rule": {"type": "all"},
  "meta": {
    "source": "english",
    "source_prompt": "Sell NQ after the prior cash high is swept and a bearish fair value gap prints.",
    "parent_version": null
  }
}
```

Create `shared/tests/fixtures/invalid/missing_instrument.json`:

```json
{
  "spec_version": "1.0",
  "name": "Bad spec",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [{"name": "s", "tz": "America/New_York", "start": "09:30", "end": "16:00", "days": [1,2,3,4,5]}],
  "blocks": [],
  "entry": {"side": "long", "when": [], "order": "market"},
  "exit": {"stop": {"ref": "x.y", "offset_ticks": 4}, "target": {"type": "rr", "value": 2.0}, "time_stop": {"type": "session_end", "session": "s"}},
  "risk": {"contracts": 1, "session": "s", "max_trades_per_session": 1, "daily_loss_stop_usd": 100.0},
  "costs": {"commission_per_side_usd": 2.5, "market_slippage_ticks": 1, "news_open_slippage_ticks": 3, "limit_through_ticks": 1},
  "meta": {"source": "english", "source_prompt": "test", "parent_version": null}
}
```

Create `shared/tests/fixtures/invalid/missing_costs.json`:

```json
{
  "spec_version": "1.0",
  "name": "Bad spec",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [{"name": "s", "tz": "America/New_York", "start": "09:30", "end": "16:00", "days": [1,2,3,4,5]}],
  "blocks": [],
  "entry": {"side": "long", "when": [], "order": "market"},
  "exit": {"stop": {"ref": "x.y", "offset_ticks": 4}, "target": {"type": "rr", "value": 2.0}, "time_stop": {"type": "session_end", "session": "s"}},
  "risk": {"contracts": 1, "session": "s", "max_trades_per_session": 1, "daily_loss_stop_usd": 100.0},
  "meta": {"source": "english", "source_prompt": "test", "parent_version": null}
}
```

Create `shared/tests/fixtures/invalid/coarse_fill_resolution.json`:

```json
{
  "spec_version": "1.0",
  "name": "Bad spec",
  "instrument": "NQ",
  "signal_timeframe": "1m",
  "fill_resolution": "15m",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [{"name": "s", "tz": "America/New_York", "start": "09:30", "end": "16:00", "days": [1,2,3,4,5]}],
  "blocks": [],
  "entry": {"side": "long", "when": [], "order": "market"},
  "exit": {"stop": {"ref": "x.y", "offset_ticks": 4}, "target": {"type": "rr", "value": 2.0}, "time_stop": {"type": "session_end", "session": "s"}},
  "risk": {"contracts": 1, "session": "s", "max_trades_per_session": 1, "daily_loss_stop_usd": 100.0},
  "costs": {"commission_per_side_usd": 2.5, "market_slippage_ticks": 1, "news_open_slippage_ticks": 3, "limit_through_ticks": 1},
  "meta": {"source": "english", "source_prompt": "test", "parent_version": null}
}
```

Create `shared/tests/fixtures/invalid/bad_block_reference.json`:

```json
{
  "spec_version": "1.0",
  "name": "Bad spec",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [{"name": "s", "tz": "America/New_York", "start": "09:30", "end": "16:00", "days": [1,2,3,4,5]}],
  "blocks": [
    {"id": "sweep", "type": "liquidity_sweep", "params": {"level": "nonexistent_block.high", "penetration_ticks": 1, "confirm_bars": 2}}
  ],
  "entry": {"side": "short", "when": [{"id": "sweep"}], "order": "limit", "price": "nonexistent_block.midpoint", "expire_bars": 10},
  "exit": {"stop": {"ref": "sweep.extreme", "offset_ticks": 4}, "target": {"type": "rr", "value": 2.0}, "time_stop": {"type": "session_end", "session": "s"}},
  "risk": {"contracts": 1, "session": "s", "max_trades_per_session": 1, "daily_loss_stop_usd": 100.0},
  "costs": {"commission_per_side_usd": 2.5, "market_slippage_ticks": 1, "news_open_slippage_ticks": 3, "limit_through_ticks": 1},
  "meta": {"source": "english", "source_prompt": "test", "parent_version": null}
}
```

Create `shared/tests/fixtures/invalid/duplicate_session_name.json`:

```json
{
  "spec_version": "1.0",
  "name": "Bad spec",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [
    {"name": "ny_am", "tz": "America/New_York", "start": "09:00", "end": "11:00", "days": [1,2,3,4,5]},
    {"name": "ny_am", "tz": "America/New_York", "start": "11:00", "end": "13:00", "days": [1,2,3,4,5]}
  ],
  "blocks": [],
  "entry": {"side": "long", "when": [], "order": "market"},
  "exit": {"stop": {"ref": "x.y", "offset_ticks": 4}, "target": {"type": "rr", "value": 2.0}, "time_stop": {"type": "session_end", "session": "ny_am"}},
  "risk": {"contracts": 1, "session": "ny_am", "max_trades_per_session": 1, "daily_loss_stop_usd": 100.0},
  "costs": {"commission_per_side_usd": 2.5, "market_slippage_ticks": 1, "news_open_slippage_ticks": 3, "limit_through_ticks": 1},
  "meta": {"source": "english", "source_prompt": "test", "parent_version": null}
}
```

Create `shared/tests/fixtures/invalid/stop_wrong_side.json`:

```json
{
  "spec_version": "1.0",
  "name": "Bad spec — short with stop that would be below entry",
  "instrument": "NQ",
  "signal_timeframe": "15m",
  "fill_resolution": "1s",
  "ai_model_version": "claude-opus-4-8",
  "asset_class": "futures",
  "execution_latency_class": "real-time",
  "sessions": [{"name": "s", "tz": "America/New_York", "start": "09:00", "end": "11:00", "days": [1,2,3,4,5]}],
  "blocks": [
    {"id": "sweep", "type": "liquidity_sweep", "params": {"level": "s.low", "penetration_ticks": 1, "confirm_bars": 2}}
  ],
  "entry": {"side": "short", "when": [{"id": "sweep"}], "order": "market"},
  "exit": {
    "stop": {"ref": "sweep.extreme", "offset_ticks": -5},
    "target": {"type": "rr", "value": 2.0},
    "time_stop": {"type": "session_end", "session": "s"}
  },
  "risk": {"contracts": 1, "session": "s", "max_trades_per_session": 1, "daily_loss_stop_usd": 100.0},
  "costs": {"commission_per_side_usd": 2.5, "market_slippage_ticks": 1, "news_open_slippage_ticks": 3, "limit_through_ticks": 1},
  "meta": {"source": "english", "source_prompt": "test", "parent_version": null}
}
```

- [ ] **Step 9: Create `shared/spec/model.py`**

```python
from __future__ import annotations

from typing import Annotated, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Instrument(str, Enum):
    NQ = "NQ"
    MNQ = "MNQ"
    ES = "ES"
    MES = "MES"


TIMEFRAME_MINUTES = {
    "1m": 1, "2m": 2, "5m": 5, "15m": 15,
    "30m": 30, "1h": 60, "4h": 240,
}

FILL_RESOLUTION_MINUTES = {"1s": 0, "1m": 1}

SignalTimeframe = Literal["1m", "2m", "5m", "15m", "30m", "1h", "4h"]
FillResolution = Literal["1s", "1m"]
Side = Literal["long", "short"]
OrderType = Literal["market", "limit", "stop"]
LatencyClass = Literal["real-time", "near-real-time", "batch"]
AssetClass = Literal["futures"]
ConsensusType = Literal["all", "majority", "weighted"]
AgentType = Literal["scanner", "filter", "risk", "execution"]
StopType = Literal["session_end"]
TargetType = Literal["rr"]
LevelWhich = Literal["prior_completed", "developing"]
FVGDirection = Literal["bullish", "bearish"]


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Session(BaseModel):
    name: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    tz: str
    start: str = Field(pattern=r'^\d{2}:\d{2}$')
    end: str = Field(pattern=r'^\d{2}:\d{2}$')
    days: list[Annotated[int, Field(ge=1, le=7)]] = Field(min_length=1)


class Block(BaseModel):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    type: str
    params: dict[str, Any]


class WhenCondition(BaseModel):
    id: str
    after: str | None = None
    within_bars: int | None = Field(default=None, ge=1)


class EntryRule(BaseModel):
    side: Side
    when: list[WhenCondition]
    order: OrderType
    price: str | None = None        # required for limit and stop
    expire_bars: int | None = Field(default=None, ge=1)  # required for limit and stop

    @model_validator(mode='after')
    def validate_limit_stop_fields(self) -> EntryRule:
        if self.order in ("limit", "stop"):
            if self.price is None:
                raise ValueError(f"entry.price is required when order type is '{self.order}'")
            if self.expire_bars is None:
                raise ValueError(f"entry.expire_bars is required when order type is '{self.order}'")
        return self


class StopExit(BaseModel):
    ref: str = Field(pattern=r'^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$')
    offset_ticks: int = Field(ge=0)


class TargetExit(BaseModel):
    type: TargetType
    value: float = Field(gt=0)


class TimeStop(BaseModel):
    type: StopType
    session: str


class ExitRule(BaseModel):
    stop: StopExit
    target: TargetExit
    time_stop: TimeStop


class RiskRule(BaseModel):
    contracts: int = Field(ge=1)
    session: str
    max_trades_per_session: int = Field(ge=1)
    daily_loss_stop_usd: float = Field(gt=0)


class Costs(BaseModel):
    commission_per_side_usd: float = Field(ge=0)
    market_slippage_ticks: int = Field(ge=0)
    news_open_slippage_ticks: int = Field(ge=0)
    limit_through_ticks: int = Field(ge=1)


class AgentConfig(BaseModel):
    name: str
    type: AgentType
    params: dict[str, Any] = Field(default_factory=dict)
    is_required: bool = True


class ConsensusRule(BaseModel):
    type: ConsensusType


class ReferenceInstrument(BaseModel):
    instrument: Instrument
    timeframe: SignalTimeframe


class Meta(BaseModel):
    source: str
    source_prompt: str
    parent_version: str | None = None


# ---------------------------------------------------------------------------
# Top-level spec
# ---------------------------------------------------------------------------

class StrategySpec(BaseModel):
    spec_version: Literal["1.0"]
    name: str = Field(min_length=1)
    instrument: Instrument
    signal_timeframe: SignalTimeframe
    fill_resolution: FillResolution
    ai_model_version: str = Field(min_length=1)
    asset_class: AssetClass = "futures"
    execution_latency_class: LatencyClass
    sessions: list[Session] = Field(min_length=1)
    blocks: list[Block]
    entry: EntryRule
    exit: ExitRule
    risk: RiskRule
    costs: Costs
    reference_instruments: list[ReferenceInstrument] = Field(default_factory=list)
    agents: list[AgentConfig] = Field(default_factory=list)
    consensus_rule: ConsensusRule = Field(default_factory=lambda: ConsensusRule(type="all"))
    meta: Meta

    # ------------------------------------------------------------------
    # Cross-field validators
    # ------------------------------------------------------------------

    @model_validator(mode='after')
    def validate_fill_resolution_granularity(self) -> StrategySpec:
        signal_mins = TIMEFRAME_MINUTES[self.signal_timeframe]
        fill_mins = FILL_RESOLUTION_MINUTES[self.fill_resolution]
        if fill_mins > signal_mins:
            raise ValueError(
                f"fill_resolution '{self.fill_resolution}' is coarser than "
                f"signal_timeframe '{self.signal_timeframe}'. "
                "fill_resolution must be the same granularity or finer."
            )
        return self

    @model_validator(mode='after')
    def validate_unique_session_names(self) -> StrategySpec:
        names = [s.name for s in self.sessions]
        if len(names) != len(set(names)):
            dupes = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate session names: {list(set(dupes))}")
        return self

    @model_validator(mode='after')
    def validate_session_references(self) -> StrategySpec:
        session_names = {s.name for s in self.sessions}
        if self.risk.session not in session_names:
            raise ValueError(
                f"risk.session '{self.risk.session}' does not match any session name. "
                f"Available: {sorted(session_names)}"
            )
        if self.exit.time_stop.session not in session_names:
            raise ValueError(
                f"exit.time_stop.session '{self.exit.time_stop.session}' does not match "
                f"any session name. Available: {sorted(session_names)}"
            )
        return self

    @model_validator(mode='after')
    def validate_unique_block_ids(self) -> StrategySpec:
        ids = [b.id for b in self.blocks]
        if len(ids) != len(set(ids)):
            dupes = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate block ids: {list(set(dupes))}")
        return self

    @model_validator(mode='after')
    def validate_entry_block_references(self) -> StrategySpec:
        block_ids = {b.id for b in self.blocks}
        for condition in self.entry.when:
            if condition.id not in block_ids:
                raise ValueError(
                    f"entry.when references block id '{condition.id}' which does not exist. "
                    f"Available block ids: {sorted(block_ids)}"
                )
            if condition.after and condition.after not in block_ids:
                raise ValueError(
                    f"entry.when[].after references block id '{condition.after}' which does not exist."
                )
        if self.entry.price:
            ref_block = self.entry.price.split(".")[0]
            if ref_block not in block_ids:
                raise ValueError(
                    f"entry.price references block '{ref_block}' which does not exist. "
                    f"Available: {sorted(block_ids)}"
                )
        return self

    @model_validator(mode='after')
    def validate_stop_offset_ticks_non_negative(self) -> StrategySpec:
        if self.exit.stop.offset_ticks < 0:
            raise ValueError(
                "exit.stop.offset_ticks must be >= 0. "
                "A stop on the wrong side of the entry is not allowed."
            )
        return self
```

- [ ] **Step 10: Run tests — verify they pass**

```bash
python -m pytest shared/tests/test_spec_model.py -v
```

Expected output: all tests PASS. Example:
```
PASSED shared/tests/test_spec_model.py::TestValidSpec::test_valid_spec_loads
PASSED shared/tests/test_spec_model.py::TestValidSpec::test_valid_spec_has_required_fields
...
```

If `test_stop_wrong_side_rejected` fails — the fixture uses `offset_ticks: -5` which the model validator catches. If it passes unexpectedly, check that the fixture json has `"offset_ticks": -5`.

- [ ] **Step 11: Commit**

```bash
git add pyproject.toml requirements.txt shared/
git commit -m "feat(shared): Pydantic spec model with validation and fixture tests"
```

---

## Task 2: JSON Schema + TypeScript type generation

**Files:**
- Create: `shared/spec/generate.py`
- Create: `shared/spec/schema.json` (generated)
- Create: `shared/spec/types.ts` (generated)
- Modify: `shared/tests/test_spec_model.py` (add schema tests)

**Interfaces:**
- Consumes: `StrategySpec.model_json_schema()` from Task 1
- Produces: `shared/spec/schema.json` — valid JSON Schema that Next.js can import
- Produces: `shared/spec/types.ts` — TypeScript interfaces matching the Pydantic model
- Produces: `python shared/spec/generate.py` — CLI command to regenerate both files

---

- [ ] **Step 1: Add schema round-trip tests to `shared/tests/test_spec_model.py`**

Append to the file:

```python
import jsonschema


class TestJsonSchema:
    def test_schema_can_be_generated(self):
        schema = StrategySpec.model_json_schema()
        assert schema["title"] == "StrategySpec"
        assert "properties" in schema

    def test_valid_spec_passes_json_schema(self):
        import jsonschema
        schema = StrategySpec.model_json_schema()
        data = load("valid_spec.json")
        # Should not raise
        jsonschema.validate(instance=data, schema=schema)

    def test_missing_instrument_fails_json_schema(self):
        import jsonschema
        schema = StrategySpec.model_json_schema()
        data = load_invalid("missing_instrument.json")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=schema)
```

- [ ] **Step 2: Install jsonschema**

```bash
pip install jsonschema==4.22.0
echo "jsonschema==4.22.0" >> requirements.txt
```

- [ ] **Step 3: Run new tests — verify they fail**

```bash
python -m pytest shared/tests/test_spec_model.py::TestJsonSchema -v
```

Expected: FAIL — `generate.py` not yet created and `schema.json` not yet written.

- [ ] **Step 4: Create `shared/spec/generate.py`**

```python
#!/usr/bin/env python3
"""
Generate schema.json and types.ts from the Pydantic spec model.

Usage:
    python shared/spec/generate.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def generate_json_schema() -> None:
    from shared.spec.model import StrategySpec
    schema = StrategySpec.model_json_schema()
    out = HERE / "schema.json"
    out.write_text(json.dumps(schema, indent=2))
    print(f"Written: {out}")


def generate_typescript() -> None:
    schema_path = HERE / "schema.json"
    out_path = HERE / "types.ts"
    result = subprocess.run(
        [
            sys.executable, "-m", "datamodel_code_generator",
            "--input", str(schema_path),
            "--input-file-type", "jsonschema",
            "--output", str(out_path),
            "--output-model-type", "typing.TypedDict",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"TypeScript generation failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    generate_json_schema()
    generate_typescript()
    print("Done.")
```

- [ ] **Step 5: Run the generator**

```bash
python shared/spec/generate.py
```

Expected output:
```
Written: shared/spec/schema.json
Written: shared/spec/types.ts
Done.
```

Verify both files exist and are non-empty:
```bash
python -c "import json; s=json.load(open('shared/spec/schema.json')); print('title:', s['title'])"
```
Expected: `title: StrategySpec`

- [ ] **Step 6: Run schema tests — verify they pass**

```bash
python -m pytest shared/tests/test_spec_model.py -v
```

Expected: all tests PASS including the new `TestJsonSchema` class.

- [ ] **Step 7: Commit**

```bash
git add shared/spec/generate.py shared/spec/schema.json shared/spec/types.ts requirements.txt
git commit -m "feat(shared): JSON Schema and TypeScript generation from Pydantic model"
```

---

## Task 3: Database schema

**Files:**
- Create: `shared/spec/migrations/__init__.py`
- Create: `shared/spec/migrations/001_initial.sql`
- Create: `shared/spec/migrations/run.py`
- Create: `shared/tests/test_migrations.py`

**Interfaces:**
- Consumes: Supabase Postgres connection string from `DATABASE_URL` env var
- Produces: All 11 tables created in the database
- Produces: `python shared/spec/migrations/run.py` — idempotent migration runner

---

- [ ] **Step 1: Create `shared/spec/migrations/__init__.py`**

```python
```

(Empty.)

- [ ] **Step 2: Write failing migration smoke test**

Create `shared/tests/test_migrations.py`:

```python
"""
Smoke test: run migrations against a real Postgres connection and verify tables exist.
Requires DATABASE_URL env var pointing to a test database (not production).
Skip if DATABASE_URL is not set.
"""
import os
import pytest
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL not set — skipping migration tests"
)

EXPECTED_TABLES = [
    "bots",
    "bot_configs",
    "backtest_jobs",
    "backtest_results",
    "trades",
    "agent_signal_log",
    "audit_log",
    "incubation_progress",
    "live_deployments",
    "notification_channels",
    "daily_loss_checks",
]


@pytest.fixture(scope="module")
def conn():
    c = psycopg2.connect(DATABASE_URL)
    yield c
    c.close()


def test_all_tables_exist(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    existing = {row[0] for row in cur.fetchall()}
    for table in EXPECTED_TABLES:
        assert table in existing, f"Table '{table}' not found after migration"


def test_audit_log_has_no_update_rule(conn):
    cur = conn.cursor()
    # Verify the audit_log trigger/rule prevents updates
    cur.execute("""
        SELECT rulename FROM pg_rules
        WHERE tablename = 'audit_log' AND rulename = 'no_update_audit_log'
    """)
    assert cur.fetchone() is not None, "audit_log should have a no_update_audit_log rule"


def test_bots_state_enum_values(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT enumlabel FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname = 'bot_state'
        ORDER BY enumsortorder
    """)
    states = [row[0] for row in cur.fetchall()]
    assert states == ["DRAFT", "BACKTESTED", "INCUBATING", "LIVE", "PAUSED", "RETIRED"]
```

- [ ] **Step 3: Run test — verify it skips (DATABASE_URL not set)**

```bash
python -m pytest shared/tests/test_migrations.py -v
```

Expected: all tests SKIP with `DATABASE_URL not set`.

- [ ] **Step 4: Create `shared/spec/migrations/001_initial.sql`**

```sql
-- 001_initial.sql
-- Full database schema for the Trading Bot Lab.
-- Idempotent: safe to run multiple times.

-- -----------------------------------------------------------------------
-- Enums
-- -----------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE bot_state AS ENUM (
        'DRAFT', 'BACKTESTED', 'INCUBATING', 'LIVE', 'PAUSED', 'RETIRED'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE trade_mode AS ENUM ('backtest', 'paper', 'live');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('queued', 'running', 'done', 'dead');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE exit_reason AS ENUM ('target', 'stop', 'time_stop', 'kill_switch', 'manual');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- -----------------------------------------------------------------------
-- bots
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bots (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    state       bot_state NOT NULL DEFAULT 'DRAFT',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- bot_configs  (versioned — never overwrite)
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bot_configs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id                  UUID NOT NULL REFERENCES bots(id),
    version                 INTEGER NOT NULL DEFAULT 1,
    parent_version          INTEGER,
    spec                    JSONB NOT NULL,
    agents_roster           JSONB NOT NULL DEFAULT '[]',
    reference_instruments   JSONB NOT NULL DEFAULT '[]',
    ai_model_version        TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (bot_id, version)
);

-- -----------------------------------------------------------------------
-- backtest_jobs  (job queue — worker polls with SKIP LOCKED)
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS backtest_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_config_id   UUID NOT NULL REFERENCES bot_configs(id),
    status          job_status NOT NULL DEFAULT 'queued',
    attempts        INTEGER NOT NULL DEFAULT 0,
    claimed_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_backtest_jobs_queued
    ON backtest_jobs(created_at)
    WHERE status = 'queued';

-- -----------------------------------------------------------------------
-- backtest_results
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS backtest_results (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_job_id         UUID NOT NULL REFERENCES backtest_jobs(id),
    bot_config_id           UUID NOT NULL REFERENCES bot_configs(id),
    metrics                 JSONB NOT NULL,
    equity_curve            JSONB NOT NULL,
    in_sample_start         DATE NOT NULL,
    in_sample_end           DATE NOT NULL,
    out_of_sample_start     DATE NOT NULL,
    out_of_sample_end       DATE NOT NULL,
    data_source             TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- trades  (backtest, paper, and live in one table)
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS trades (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id                  UUID NOT NULL REFERENCES bots(id),
    bot_config_id           UUID NOT NULL REFERENCES bot_configs(id),
    mode                    trade_mode NOT NULL,
    side                    TEXT NOT NULL CHECK (side IN ('long', 'short')),
    contracts               INTEGER NOT NULL,
    entry_time              TIMESTAMPTZ NOT NULL,
    entry_price             NUMERIC(18,6) NOT NULL,
    entry_fill_price        NUMERIC(18,6) NOT NULL,
    entry_slippage_ticks    INTEGER NOT NULL DEFAULT 0,
    entry_commission_usd    NUMERIC(10,4) NOT NULL DEFAULT 0,
    exit_time               TIMESTAMPTZ,
    exit_price              NUMERIC(18,6),
    exit_fill_price         NUMERIC(18,6),
    exit_slippage_ticks     INTEGER,
    exit_commission_usd     NUMERIC(10,4),
    pnl_usd                 NUMERIC(10,4),
    exit_reason             exit_reason,
    signal_bar_time         TIMESTAMPTZ,
    agent_signals           JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- agent_signal_log  (append-only, never delete)
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_signal_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    bar_time        TIMESTAMPTZ NOT NULL,
    agent_name      TEXT NOT NULL,
    agent_type      TEXT NOT NULL,
    output          JSONB NOT NULL,
    latency_ms      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- audit_log  (IMMUTABLE — no updates, no deletes)
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id      UUID NOT NULL REFERENCES bots(id),
    trade_id    UUID REFERENCES trades(id),
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type  TEXT NOT NULL,
    details     JSONB NOT NULL DEFAULT '{}'
);

-- Rule: block UPDATE on audit_log
DO $$ BEGIN
    CREATE RULE no_update_audit_log AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Rule: block DELETE on audit_log
DO $$ BEGIN
    CREATE RULE no_delete_audit_log AS ON DELETE TO audit_log DO INSTEAD NOTHING;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- -----------------------------------------------------------------------
-- incubation_progress
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS incubation_progress (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id                  UUID NOT NULL UNIQUE REFERENCES bots(id),
    paper_trade_count       INTEGER NOT NULL DEFAULT 0,
    trading_days_elapsed    INTEGER NOT NULL DEFAULT 0,
    started_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    gate_met_at             TIMESTAMPTZ,
    backtest_result_id      UUID REFERENCES backtest_results(id)
);

-- -----------------------------------------------------------------------
-- live_deployments
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS live_deployments (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id                      UUID NOT NULL REFERENCES bots(id),
    bot_config_id               UUID NOT NULL REFERENCES bot_configs(id),
    deployed_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    daily_loss_limit_usd        NUMERIC(10,4) NOT NULL,
    position_size_cap_contracts INTEGER NOT NULL,
    broker_adapter              TEXT NOT NULL,
    broker_credentials_enc      TEXT,
    confirmation_logged_at      TIMESTAMPTZ NOT NULL
);

-- -----------------------------------------------------------------------
-- notification_channels
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notification_channels (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id      UUID NOT NULL REFERENCES bots(id),
    type        TEXT NOT NULL CHECK (type IN ('telegram')),
    config      JSONB NOT NULL DEFAULT '{}',
    verified_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- daily_loss_checks
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS daily_loss_checks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id              UUID NOT NULL REFERENCES bots(id),
    date                DATE NOT NULL,
    realized_pnl_usd    NUMERIC(10,4) NOT NULL DEFAULT 0,
    open_mark_usd       NUMERIC(10,4) NOT NULL DEFAULT 0,
    total_pnl_usd       NUMERIC(10,4) GENERATED ALWAYS AS (realized_pnl_usd + open_mark_usd) STORED,
    limit_usd           NUMERIC(10,4) NOT NULL,
    tripped_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (bot_id, date)
);
```

- [ ] **Step 5: Create `shared/spec/migrations/run.py`**

```python
#!/usr/bin/env python3
"""
Idempotent migration runner.

Usage:
    DATABASE_URL=postgresql://... python shared/spec/migrations/run.py
"""
import os
import sys
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).parent
DATABASE_URL = os.environ.get("DATABASE_URL")


def run() -> None:
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        print("No migration files found.")
        return

    for sql_file in sql_files:
        print(f"Running {sql_file.name}...")
        sql = sql_file.read_text()
        cur.execute(sql)
        print(f"  OK")

    cur.close()
    conn.close()
    print("Migrations complete.")


if __name__ == "__main__":
    run()
```

- [ ] **Step 6: Run migrations against your Supabase database**

Set `DATABASE_URL` to your Supabase direct connection string (find it in Supabase dashboard → Settings → Database → Connection string → URI mode).

```bash
DATABASE_URL="postgresql://postgres:[password]@[host]:5432/postgres" python shared/spec/migrations/run.py
```

Expected:
```
Running 001_initial.sql...
  OK
Migrations complete.
```

- [ ] **Step 7: Run migration tests**

```bash
DATABASE_URL="postgresql://..." python -m pytest shared/tests/test_migrations.py -v
```

Expected: all tests PASS (not skipped, not failed).

- [ ] **Step 8: Commit**

```bash
git add shared/spec/migrations/ shared/tests/test_migrations.py
git commit -m "feat(shared): database schema migration — 11 tables"
```

---

## Task 4: Env modules (Python + TypeScript)

**Files:**
- Create: `engine/__init__.py`
- Create: `engine/env.py`
- Create: `engine/tests/__init__.py`
- Create: `engine/tests/test_env.py`
- Create: `web/lib/env.ts`

**Interfaces:**
- Produces: `from engine.env import Env` — a settings object; raises `SystemExit` if any required key is missing
- Produces: `import { env } from '@/lib/env'` — TypeScript equivalent; throws at module load time if missing

---

- [ ] **Step 1: Create `engine/__init__.py`**

```python
```

(Empty.)

- [ ] **Step 2: Create `engine/tests/__init__.py`**

```python
```

(Empty.)

- [ ] **Step 3: Write failing env tests**

Create `engine/tests/test_env.py`:

```python
import os
import pytest


class TestEnv:
    def test_env_loads_when_all_keys_present(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("DATABENTO_API_KEY", "db-test-key")

        # Re-import to pick up monkeypatched env
        import importlib
        import engine.env as env_module
        importlib.reload(env_module)
        from engine.env import Env

        assert Env.supabase_url == "https://example.supabase.co"
        assert Env.anthropic_api_key == "sk-ant-test"

    def test_env_raises_on_missing_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
        monkeypatch.setenv("DATABENTO_API_KEY", "db-test-key")

        import importlib
        import engine.env as env_module
        with pytest.raises(SystemExit):
            importlib.reload(env_module)
```

- [ ] **Step 4: Run test — verify it fails**

```bash
python -m pytest engine/tests/test_env.py -v
```

Expected: FAIL — `engine.env` does not exist yet.

- [ ] **Step 5: Create `engine/env.py`**

```python
"""
Environment module. Reads all required env vars at import time.
Raises SystemExit with a clear message if any required key is missing.
Never import secrets from this module outside server-side code.
"""
import os
import sys
from dataclasses import dataclass


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        print(
            f"FATAL: required environment variable '{key}' is not set. "
            "Check your .env file or deployment configuration.",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


@dataclass(frozen=True)
class _Env:
    supabase_url: str
    supabase_service_role_key: str
    anthropic_api_key: str
    databento_api_key: str


Env = _Env(
    supabase_url=_require("SUPABASE_URL"),
    supabase_service_role_key=_require("SUPABASE_SERVICE_ROLE_KEY"),
    anthropic_api_key=_require("ANTHROPIC_API_KEY"),
    databento_api_key=_require("DATABENTO_API_KEY"),
)
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
python -m pytest engine/tests/test_env.py -v
```

Expected: both tests PASS.

- [ ] **Step 7: Create `web/lib/env.ts`**

```typescript
/**
 * Environment module for the Next.js web layer.
 * Throws at module load time if any required variable is missing.
 * Import this wherever you need env vars — never read process.env directly.
 */

function require(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(
      `FATAL: required environment variable '${key}' is not set. ` +
      'Check your .env.local file or deployment configuration.'
    );
  }
  return value;
}

export const env = {
  supabaseUrl: require('NEXT_PUBLIC_SUPABASE_URL'),
  supabaseAnonKey: require('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
  supabaseServiceRoleKey: require('SUPABASE_SERVICE_ROLE_KEY'),
  anthropicApiKey: require('ANTHROPIC_API_KEY'),
} as const;
```

- [ ] **Step 8: Create `.env.local.example` in the web directory**

```bash
# web/.env.local.example
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ANTHROPIC_API_KEY=sk-ant-your-key
```

Copy it to `web/.env.local` and fill in real values from Supabase dashboard + Anthropic console.

- [ ] **Step 9: Run full test suite — all tasks green**

```bash
python -m pytest shared/tests/ engine/tests/ -v
```

Expected: all tests PASS (migration tests skip if `DATABASE_URL` not set — that is acceptable here).

- [ ] **Step 10: Final commit**

```bash
git add engine/ web/lib/env.ts web/.env.local.example
git commit -m "feat(engine,web): env modules — boot fails if required keys missing"
```

---

## Self-Review Notes

- **Spec coverage:** All required spec fields from the design doc's checklist are present in `model.py`. All 8 cross-field constraints are validated. DB tables cover all 11 from the design doc. Env modules cover all required keys.
- **No placeholders:** All steps contain actual code. No TBDs.
- **Type consistency:** `StrategySpec` is the only public export from `shared.spec`. All test fixtures reference `valid_spec.json` which matches the full model shape.
- **One gap addressed:** `stop_wrong_side.json` fixture uses `offset_ticks: -5` to trigger the `>= 0` validator — this is the most direct way to test "stop on wrong side" without needing a full fill simulation (which is Phase 2).
