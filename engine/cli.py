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
    backtest.add_argument("--bars", required=True)
    trans = sub.add_parser("translate", help="English to spec JSON")
    trans.add_argument("english", nargs="+")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "backtest":
        return cmd_backtest(args.spec, args.bars)
    if args.cmd == "translate":
        return cmd_translate(" ".join(args.english))
    return 2


if __name__ == "__main__":
    sys.exit(main())
