from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.backtest import run_backtest
from engine.bars import read_bars
from engine.translate import translate
from shared.spec import StrategySpec


def _print_result(result) -> None:
    if not result.trades:
        print("No trades.")
        if result.rejects:
            print("Rejects:", ", ".join(result.rejects))
        return
    print("trades")
    print("side,entry_time,entry_price,exit_time,exit_price,exit_reason,pnl_usd,commission_usd")
    for trade in result.trades:
        print(
            f"{trade.side},{trade.entry_time.isoformat()},{trade.entry_price},"
            f"{trade.exit_time.isoformat()},{trade.exit_price},{trade.exit_reason},"
            f"{trade.pnl_usd:.2f},{trade.commission_usd:.2f}"
        )
    total = sum(trade.pnl_usd for trade in result.trades)
    print(f"net_pnl_usd,{total:.2f}")
    if result.equity:
        print(f"final_equity,{result.equity[-1][1]:.2f}")


def cmd_backtest(spec_path: str, bars_path: str) -> int:
    spec = StrategySpec.model_validate_json(Path(spec_path).read_text(encoding="utf-8"))
    bars = read_bars(bars_path)
    result = run_backtest(spec, bars)
    _print_result(result)
    return 0


def cmd_backtest_outrights(spec_path: str, outrights_path: str) -> int:
    from engine.marketdata.outrights import read_outrights, run_front_month_backtest

    spec = StrategySpec.model_validate_json(Path(spec_path).read_text(encoding="utf-8"))
    bars = read_outrights(outrights_path)
    result = run_front_month_backtest(spec, bars)
    _print_result(result)
    return 0


def cmd_fetch_nq(start: str, end: str, out: str, schema: str, max_cost: float) -> int:
    import databento as db

    from engine.marketdata.databento_nq import load_databento_key, pull_nq_outrights

    try:
        client = db.Historical(load_databento_key())
        path = pull_nq_outrights(
            client,
            start=start,
            end=end,
            dest=Path(out),
            schema=schema,
            max_cost_usd=max_cost,
        )
    except RuntimeError as exc:
        print(exc)
        return 1
    print(f"wrote,{path}")
    return 0


def cmd_raid_retrace(outrights_path: str, csv_path: str | None) -> int:
    from zoneinfo import ZoneInfo

    from engine.marketdata.outrights import read_outrights
    from engine.strategies.raid_retrace import backtest_raid_retrace

    ny = ZoneInfo("America/New_York")
    trades = backtest_raid_retrace(read_outrights(outrights_path))
    if not trades:
        print("No trades.")
        return 0
    print(
        "side,entry_ny,entry_price,exit_ny,exit_price,exit_reason,pnl_usd,pool,source"
    )
    lines = [
        "side,entry_ny,entry_price,exit_ny,exit_price,exit_reason,pnl_usd,pool,source"
    ]
    for trade in trades:
        entry = trade.entry_time.astimezone(ny).strftime("%Y-%m-%d %H:%M")
        exit_at = trade.exit_time.astimezone(ny).strftime("%Y-%m-%d %H:%M")
        row = (
            f"{trade.side},{entry},{trade.entry_price:.2f},{exit_at},"
            f"{trade.exit_price:.2f},{trade.exit_reason},{trade.pnl_usd:.2f},"
            f"{trade.level:.2f},{trade.source}"
        )
        print(row)
        lines.append(row)
    total = sum(trade.pnl_usd for trade in trades)
    print(f"net_pnl_usd,{total:.2f}")
    if csv_path:
        Path(csv_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote,{csv_path}")
    return 0


def cmd_translate(english: str) -> int:
    outcome = translate(english)
    if not outcome.ok:
        print(outcome.error)
        return 1
    assert outcome.spec is not None
    print(json.dumps(outcome.spec.model_dump(mode="json"), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="engine.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    backtest = sub.add_parser("backtest", help="Run a spec against bars")
    backtest.add_argument("--spec", required=True)
    source = backtest.add_mutually_exclusive_group(required=True)
    source.add_argument("--bars", help="One Parquet or CSV series")
    source.add_argument("--outrights", help="Raw outright Parquet from fetch-nq")
    fetch = sub.add_parser("fetch-nq", help="Download NQ raw outrights to Parquet")
    fetch.add_argument("--start", required=True)
    fetch.add_argument("--end", required=True)
    fetch.add_argument("--out", required=True)
    fetch.add_argument("--schema", default="ohlcv-1s", choices=("ohlcv-1s", "ohlcv-1m"))
    fetch.add_argument("--max-cost", type=float, default=5.0)
    raid = sub.add_parser(
        "raid-retrace",
        help="Backtest the strict sweep, respect, and inverse-gap strategy",
    )
    raid.add_argument("--outrights", required=True)
    raid.add_argument("--csv", help="Also write the trade list to this path")
    trans = sub.add_parser("translate", help="English to spec JSON")
    trans.add_argument("english", nargs="+")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "backtest":
        if args.outrights:
            return cmd_backtest_outrights(args.spec, args.outrights)
        return cmd_backtest(args.spec, args.bars)
    if args.cmd == "fetch-nq":
        return cmd_fetch_nq(args.start, args.end, args.out, args.schema, args.max_cost)
    if args.cmd == "raid-retrace":
        return cmd_raid_retrace(args.outrights, args.csv)
    if args.cmd == "translate":
        return cmd_translate(" ".join(args.english))
    return 2


if __name__ == "__main__":
    sys.exit(main())
