from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import ValidationError

from shared.spec import StrategySpec

TRANSLATOR_PROMPT = """
You turn trader English into a StrategySpec JSON object. You do not size positions,
detect patterns, or simulate fills. Python does that.

Allowed block types: session_levels, liquidity_sweep, fair_value_gap, swing_points,
market_structure_shift, order_block, inverse_fvg, equilibrium.
Refuse these as not coded yet: breaker, unicorn, SMT, LRL.

Meanings (docs/GLOSSARY.md):
- Sweep: price trades through a named high or low. Not an entry. Not a body close.
- MSS / BOS: body close beyond the last opposite swing. Confirmation after a sweep.
- Prior day high/low: prior CME equity session 18:00-17:00 America/New_York (cme_eth),
  session_levels which=prior_completed.
- Swing points: three-candle fractal. Buy-side is the swing high. Sell-side is the swing low.
- Order block: the impulsive leg that caused the sweep, born at sweep + MSS. Not an FVG.
- Fair value gap: three closed candles, wick to wick. Overlap is not a gap.
- Inverse FVG: body close through the gap's far edge. Wick into the gap is not inversion.
- Equilibrium: midpoint of the latest swing low to swing high. Discount below, premium above.
- Stop: beyond the sweep extreme plus offset_ticks.
- NY AM default: 09:30-11:00 America/New_York.

Required cards: instrument, side, session, entry when, order, stop, target, contracts,
daily_loss_stop_usd, costs. Do not invent missing numbers. Ask for them.

Output JSON only when every required field is present. Otherwise say what is missing.
""".strip()

_UNCODED = [
    (r"\bunicorn\b", "unicorn"),
    (r"\bbreaker\b", "breaker"),
    (r"\bsmt\b", "SMT"),
    (r"\blow-resistance liquidity\b", "LRL"),
    (r"\blrl\b", "LRL"),
]


@dataclass(frozen=True)
class TranslateResult:
    ok: bool
    spec: StrategySpec | None
    error: str | None
    prompt: str = TRANSLATOR_PROMPT


def _uncoded_term(english: str) -> str | None:
    text = english.lower()
    for pattern, label in _UNCODED:
        if re.search(pattern, text):
            return label
    return None


def _try_json(english: str) -> StrategySpec | None:
    stripped = english.strip()
    if not stripped.startswith("{"):
        return None
    try:
        data = json.loads(stripped)
        return StrategySpec.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None


def _find_instrument(text: str) -> str | None:
    for name in ("MNQ", "MES", "NQ", "ES"):
        if re.search(rf"\b{name}\b", text, re.I):
            return name
    return None


def _find_side(text: str) -> str | None:
    if re.search(r"\b(short|sell)\b", text, re.I):
        return "short"
    if re.search(r"\b(long|buy)\b", text, re.I):
        return "long"
    return None


def _find_direction(text: str, side: str) -> str:
    if re.search(r"\bbullish\b", text, re.I):
        return "bullish"
    if re.search(r"\bbearish\b", text, re.I):
        return "bearish"
    return "bearish" if side == "short" else "bullish"


def _find_int(text: str, pattern: str, default: int | None = None) -> int | None:
    match = re.search(pattern, text, re.I)
    if match:
        return int(match.group(1))
    return default


def _find_float(text: str, pattern: str, default: float | None = None) -> float | None:
    match = re.search(pattern, text, re.I)
    if match:
        return float(match.group(1))
    return default


def _recipe_spec(english: str) -> TranslateResult:
    instrument = _find_instrument(english)
    side = _find_side(english)
    wants_ob = bool(re.search(r"\border[\s_-]*block\b", english, re.I))
    wants_ifvg = bool(re.search(r"\binverse[\s_-]*fvg\b", english, re.I))
    wants_mss = wants_ob or bool(
        re.search(r"\b(mss|bos|break of structure)\b", english, re.I)
    )
    wants_eq = bool(re.search(r"\b(discount|premium|equilibrium)\b", english, re.I))
    wants_fvg = bool(re.search(r"fair value gap|\bfvg\b", english, re.I))
    wants_swings = wants_ob or wants_mss or wants_eq or bool(
        re.search(r"\b(swing|grab)\b", english, re.I)
    )
    has_prior = bool(re.search(r"prior day|pdh|pdl|previous day", english, re.I))
    missing: list[str] = []
    if instrument is None:
        missing.append("instrument (NQ, MNQ, ES, or MES)")
    if side is None:
        missing.append("side (long or short)")
    if not has_prior and not wants_swings:
        missing.append("what gets swept (prior day high/low or a swing)")
    if not wants_fvg and not wants_ifvg and not wants_ob:
        missing.append("entry tool (fair value gap, inverse FVG, or order block)")
    offset = _find_int(english, r"stop\s+(\d+)\s+ticks?")
    if offset is None:
        missing.append("stop offset in ticks")
    rr = _find_float(english, r"(\d+(?:\.\d+)?)\s*r\b")
    if rr is None:
        missing.append("target R multiple")
    contracts = _find_int(english, r"(\d+)\s+contracts?", 1)
    daily_loss = _find_float(english, r"\$?\s*(\d+(?:\.\d+)?)\s*(?:daily loss|daily-loss)")
    if daily_loss is None:
        missing.append("daily loss in dollars")
    if missing:
        return TranslateResult(
            ok=False,
            spec=None,
            error="Missing required cards: " + "; ".join(missing),
        )

    assert instrument is not None and side is not None and offset is not None and rr is not None
    assert daily_loss is not None and contracts is not None
    grab_lows = bool(re.search(r"grab lows|prior day low|\bpdl\b", english, re.I))
    level_field = "low" if grab_lows else "high"
    direction = _find_direction(english, side)
    eq_location = "discount" if side == "long" else "premium"
    if re.search(r"\bdiscount\b", english, re.I):
        eq_location = "discount"
    if re.search(r"\bpremium\b", english, re.I):
        eq_location = "premium"

    blocks: list[dict] = []
    if wants_swings:
        blocks.append(
            {"id": "swings", "type": "swing_points", "params": {"kind": "both"}}
        )
    if has_prior or not wants_swings:
        blocks.append(
            {
                "id": "pdh",
                "type": "session_levels",
                "params": {
                    "session": "cme_eth",
                    "levels": ["high", "low"],
                    "which": "prior_completed",
                },
            }
        )
        sweep_level = f"pdh.{level_field}"
    else:
        sweep_level = f"swings.{level_field}"
    blocks.append(
        {
            "id": "sweep",
            "type": "liquidity_sweep",
            "params": {"level": sweep_level, "penetration_ticks": 1},
        }
    )
    if wants_mss:
        blocks.append(
            {
                "id": "mss",
                "type": "market_structure_shift",
                "params": {"direction": "bearish" if side == "short" else "bullish", "swings": "swings"},
            }
        )
    if wants_ob:
        blocks.append(
            {
                "id": "ob",
                "type": "order_block",
                "params": {"sweep": "sweep", "mss": "mss", "swings": "swings"},
            }
        )
    if wants_fvg or wants_ifvg:
        fvg_direction = direction
        if wants_ifvg:
            fvg_direction = "bullish" if direction == "bearish" else "bearish"
        blocks.append(
            {
                "id": "fvg",
                "type": "fair_value_gap",
                "params": {"direction": fvg_direction, "min_size_ticks": 0},
            }
        )
    if wants_ifvg:
        blocks.append(
            {
                "id": "ifvg",
                "type": "inverse_fvg",
                "params": {"gap": "fvg", "direction": direction},
            }
        )
    if wants_eq:
        blocks.append(
            {
                "id": "eq",
                "type": "equilibrium",
                "params": {"swings": "swings", "location": eq_location},
            }
        )

    when: list[dict] = [{"id": "sweep"}]
    last = "sweep"
    if wants_mss:
        when.append({"id": "mss", "after": last, "within_bars": 20})
        last = "mss"
    if wants_ob:
        when.append({"id": "ob", "after": last, "within_bars": 20})
        last = "ob"
    if wants_ifvg:
        when.append({"id": "ifvg", "after": last, "within_bars": 20})
        last = "ifvg"
    elif wants_fvg:
        when.append({"id": "fvg", "after": last, "within_bars": 20})
        last = "fvg"
    if wants_eq:
        when.append({"id": "eq"})

    if wants_ob:
        price = "ob.midpoint"
    elif wants_ifvg:
        price = "ifvg.midpoint"
    else:
        price = "fvg.midpoint"

    tools = []
    if wants_mss:
        tools.append("MSS")
    if wants_ob:
        tools.append("order block")
    if wants_ifvg:
        tools.append("inverse FVG")
    elif wants_fvg:
        tools.append("FVG")
    name = f"{instrument} sweep then {' then '.join(tools) if tools else 'FVG'}"

    data = {
        "spec_version": "1.0",
        "name": name,
        "instrument": instrument,
        "signal_timeframe": "1m",
        "fill_resolution": "1m",
        "ai_model_version": "glossary-v1",
        "asset_class": "futures",
        "execution_latency_class": "batch",
        "sessions": [
            {
                "name": "cme_eth",
                "tz": "America/New_York",
                "start": "18:00",
                "end": "17:00",
                "days": [7, 1, 2, 3, 4],
            },
            {
                "name": "ny_am",
                "tz": "America/New_York",
                "start": "09:30",
                "end": "11:00",
                "days": [1, 2, 3, 4, 5],
            },
        ],
        "blocks": blocks,
        "entry": {
            "side": side,
            "when": when,
            "order": "limit",
            "price": price,
            "expire_bars": 10,
        },
        "exit": {
            "stop": {"ref": "sweep.extreme", "offset_ticks": offset},
            "target": {"type": "rr", "value": rr},
            "time_stop": {"type": "session_end", "session": "ny_am"},
        },
        "risk": {
            "contracts": contracts,
            "session": "ny_am",
            "max_trades_per_session": 2,
            "daily_loss_stop_usd": daily_loss,
        },
        "costs": {
            "commission_per_side_usd": 2.5,
            "market_slippage_ticks": 1,
            "news_open_slippage_ticks": 3,
            "limit_through_ticks": 1,
        },
        "meta": {
            "source": "english",
            "source_prompt": english,
            "parent_version": None,
        },
    }
    spec = StrategySpec.model_validate(data)
    return TranslateResult(ok=True, spec=spec, error=None)


def translate(english: str) -> TranslateResult:
    parsed = _try_json(english)
    if parsed is not None:
        return TranslateResult(ok=True, spec=parsed, error=None)
    term = _uncoded_term(english)
    if term is not None:
        return TranslateResult(
            ok=False,
            spec=None,
            error=f"We know this; {term} is not coded yet.",
        )
    return _recipe_spec(english)
