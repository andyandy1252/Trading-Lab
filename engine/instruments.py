from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentInfo:
    tick_size: float
    dollars_per_tick: float


INSTRUMENTS: dict[str, InstrumentInfo] = {
    "NQ": InstrumentInfo(tick_size=0.25, dollars_per_tick=5.00),
    "MNQ": InstrumentInfo(tick_size=0.25, dollars_per_tick=0.50),
    "ES": InstrumentInfo(tick_size=0.25, dollars_per_tick=12.50),
    "MES": InstrumentInfo(tick_size=0.25, dollars_per_tick=1.25),
}
