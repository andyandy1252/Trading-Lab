from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

from shared.spec.model import WhenCondition


@dataclass(frozen=True)
class BoundEvent:
    block_id: str
    bar_index: int
    fields: dict[str, Any]
    align: str = "any"


@dataclass(frozen=True)
class Signal:
    bar_index: int
    bound: dict[str, BoundEvent]


def resolve_ref(ref: str, bound: dict[str, BoundEvent]) -> float:
    block_id, field = ref.split(".", 1)
    value = bound[block_id].fields[field]
    return float(value)


def find_signals(
    when: list[WhenCondition],
    events: dict[str, list[BoundEvent]],
    bar_count: int,
) -> list[Signal]:
    signals: list[Signal] = []
    for bar_index in range(bar_count):
        bound = _bind_at(when, events, bar_index)
        if bound is not None:
            signals.append(Signal(bar_index=bar_index, bound=bound))
    return signals


def _bind_at(
    when: list[WhenCondition],
    events: dict[str, list[BoundEvent]],
    bar_index: int,
) -> dict[str, BoundEvent] | None:
    candidates: list[list[BoundEvent]] = []
    for cond in when:
        evs = [e for e in events.get(cond.id, []) if e.bar_index <= bar_index]
        evs = [
            e for e in evs
            if e.align != "completing" or e.bar_index == bar_index
        ]
        if not evs:
            return None
        candidates.append(evs)
    chosen: dict[str, BoundEvent] | None = None
    for combo in product(*candidates):
        by_id = {when[i].id: combo[i] for i in range(len(when))}
        if max(event.bar_index for event in combo) != bar_index:
            continue
        ok = True
        for cond in when:
            if not cond.after:
                continue
            later = by_id[cond.id].bar_index
            earlier = by_id[cond.after].bar_index
            if later <= earlier:
                ok = False
                break
            if cond.within_bars is not None and later - earlier > cond.within_bars:
                ok = False
                break
        if ok:
            chosen = by_id
            break
    return chosen
