# Engine

Python worker: detect v1 blocks on closed bars, simulate pessimistic fills, run a local backtest CLI.

Rules are in `docs/SPEC.md`. Language is in `docs/GLOSSARY.md`. v1 block types: `session_levels`, `liquidity_sweep`, `fair_value_gap`, `swing_points`, `market_structure_shift`, `order_block`, `inverse_fvg`, `equilibrium`.

```
python -m engine.cli fetch-nq --start 2026-10-18 --end 2026-10-31 --out data/nq/outrights.parquet
python -m engine.cli backtest --spec shared/tests/fixtures/valid_spec.json --outrights data/nq/outrights.parquet
python -m engine.cli backtest --spec path.json --bars path.parquet
python -m engine.cli translate "short NQ after prior day high is swept..."
```

`fetch-nq` needs `DATABENTO_API_KEY` in the environment or `.env.local`. It writes raw NQ outrights. The outright backtest keeps the front month, the contract with the higher prior-session volume, and does not stitch two contracts together.

The web app waits until this engine's tests pass. Do not work on more than the one task in front of you.
