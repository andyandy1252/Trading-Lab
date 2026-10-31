from __future__ import annotations

import os
from pathlib import Path

import polars as pl

from engine.marketdata.outrights import (
    outright_symbols_from_definitions,
    ohlcv_to_outrights,
    write_outrights,
)

DATASET = "GLBX.MDP3"
PARENT = "NQ.FUT"


def load_databento_key() -> str:
    key = os.environ.get("DATABENTO_API_KEY", "").strip()
    if key:
        return key
    for name in (".env.local", ".env"):
        path = Path(name)
        if not path.exists():
            continue
        from dotenv import dotenv_values

        found = (dotenv_values(path).get("DATABENTO_API_KEY") or "").strip()
        if found:
            return found
    raise RuntimeError(
        "DATABENTO_API_KEY is missing. Add it to the environment or .env.local before fetching NQ."
    )


def store_to_frame(store) -> pl.DataFrame:
    if isinstance(store, pl.DataFrame):
        return store
    if hasattr(store, "to_polars"):
        return store.to_polars()
    pdf = store.to_df()
    if isinstance(pdf, pl.DataFrame):
        return pdf
    index_name = getattr(getattr(pdf, "index", None), "name", None)
    if index_name:
        pdf = pdf.reset_index()
    return pl.from_pandas(pdf)


def _quote_usd(client, **kwargs) -> float | None:
    metadata = getattr(client, "metadata", None)
    if metadata is None:
        return None
    return float(metadata.get_cost(**kwargs))


def pull_nq_outrights(
    client,
    *,
    start: str,
    end: str,
    dest: Path,
    schema: str = "ohlcv-1s",
    max_cost_usd: float = 5.0,
) -> Path:
    """Download NQ raw outrights and write one Parquet file.

    Definitions come from the parent `NQ.FUT`. Bars are requested by raw
    outright symbol. Spreads are dropped. Prices are stored as printed.
    """
    definitions = client.timeseries.get_range(
        dataset=DATASET,
        symbols=PARENT,
        schema="definition",
        stype_in="parent",
        stype_out="instrument_id",
        start=start,
        end=end,
    )
    mapping = outright_symbols_from_definitions(store_to_frame(definitions))
    symbols = sorted(set(mapping.values()))
    if not symbols:
        raise RuntimeError("Databento returned no NQ outright futures for that window")
    cost = _quote_usd(
        client,
        dataset=DATASET,
        symbols=symbols,
        schema=schema,
        stype_in="raw_symbol",
        start=start,
        end=end,
    )
    if cost is not None and cost > max_cost_usd:
        raise RuntimeError(
            f"Databento quote is ${cost:.2f}, over the ${max_cost_usd:.2f} cap. Shorten the window or raise --max-cost."
        )
    ohlcv = client.timeseries.get_range(
        dataset=DATASET,
        symbols=symbols,
        schema=schema,
        stype_in="raw_symbol",
        stype_out="instrument_id",
        start=start,
        end=end,
    )
    bars = ohlcv_to_outrights(store_to_frame(ohlcv), mapping)
    write_outrights(dest, bars)
    return dest
