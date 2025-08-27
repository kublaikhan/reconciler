import subprocess
import sys


def test_cli_only_statement_shows_summary(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "reconciler.cli",
            "--transactions",
            "tests/data/ledger.csv",
            "--statement",
            "tests/data/statement.csv",
            "--only-statement",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    out = result.stdout
    assert "Transactions only on credit card statement:" in out
    assert "Transactions only on provided lists:" not in out
    assert "2 transactions only on provided lists" in out
