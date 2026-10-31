import json

from engine.bars import write_bars
from engine.cli import main
from engine.tests.test_backtest import _spec
from engine.tests.helpers import bar, ny


def _tape():
    return [
        bar(ny(2024, 1, 7, 19, 0), 99, 100, 98, 99),
        bar(ny(2024, 1, 9, 9, 30), 99.5, 99.75, 99, 99.5),
        bar(ny(2024, 1, 9, 9, 31), 99.5, 100.50, 99, 100.25),
        bar(ny(2024, 1, 9, 9, 32), 102.5, 103, 102, 102.5),
        bar(ny(2024, 1, 9, 9, 33), 102.5, 102.6, 97, 97.5),
        bar(ny(2024, 1, 9, 9, 34), 97.5, 98, 95, 96),
        bar(ny(2024, 1, 9, 9, 35), 99.5, 100.5, 99.5, 100.2),
        bar(ny(2024, 1, 9, 9, 36), 100, 100.2, 96, 97),
    ]


def test_cli_backtest_prints_a_trade(tmp_path, capsys):
    spec_path = tmp_path / "spec.json"
    bars_path = tmp_path / "bars.parquet"
    spec_path.write_text(json.dumps(_spec().model_dump(mode="json")), encoding="utf-8")
    write_bars(bars_path, _tape())
    code = main(["backtest", "--spec", str(spec_path), "--bars", str(bars_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "short" in captured.out
    assert "target" in captured.out
    assert "net_pnl_usd" in captured.out


def test_cli_raid_retrace_on_a_short_file_prints_no_trades(tmp_path, capsys):
    from engine.marketdata.outrights import OutrightBar, write_outrights

    path = tmp_path / "outrights.parquet"
    write_outrights(
        path,
        [
            OutrightBar(ny(2026, 10, 19, 18, 0), "NQZ6", 100, 101, 99, 100, 10),
            OutrightBar(ny(2026, 10, 20, 10, 0), "NQZ6", 100, 101, 99, 100, 10),
        ],
    )
    code = main(["raid-retrace", "--outrights", str(path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "No trades." in captured.out


def test_cli_translate_refuses_unicorn(capsys):
    code = main(["translate", "enter", "the", "unicorn"])
    captured = capsys.readouterr()
    assert code == 1
    assert "not coded" in captured.out.lower()


def test_cli_translate_emits_json(capsys):
    code = main(
        [
            "translate",
            "Short NQ in NY AM after prior day high is swept, then a bearish FVG, "
            "limit at midpoint, stop 4 ticks above the sweep, 2R, 1 contract, $500 daily loss",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    data = json.loads(captured.out)
    assert data["instrument"] == "NQ"
    assert data["entry"]["side"] == "short"
