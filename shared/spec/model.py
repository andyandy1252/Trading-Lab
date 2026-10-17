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
