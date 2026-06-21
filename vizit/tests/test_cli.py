"""Tests for the command-line interface in :mod:`vizit.cli`."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from vizit import cli


def test_line_writes_output(numeric_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    rc = cli.main(["line", str(numeric_file), "-c", "2", "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0


def test_line_multi_series(numeric_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "multi.png"
    rc = cli.main(["line", str(numeric_file), "-c", "2,3", "-x", "1", "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists()


@pytest.mark.parametrize("command", ["line", "scatter", "hist", "bar"])
def test_each_subcommand(command: str, numeric_file: Path, tmp_path: Path) -> None:
    out = tmp_path / f"{command}.png"
    rc = cli.main([command, str(numeric_file), "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_stdin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("1 2\n3 4\n5 6\n"))
    out = tmp_path / "stdin.png"
    rc = cli.main(["line", "-", "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_bad_column_returns_2(numeric_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["line", str(numeric_file), "-c", "99", "--no-show"])
    assert rc == 2
    err = capsys.readouterr().err
    assert err.startswith("vizit:")


def test_missing_file_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["line", "/no/such/file.dat", "--no-show"])
    assert rc == 2
    assert "vizit:" in capsys.readouterr().err


def test_bad_limits_returns_2(numeric_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["line", str(numeric_file), "-c", "2", "--xlim", "bad", "--no-show"])
    assert rc == 2
    assert "vizit:" in capsys.readouterr().err


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "vizit" in capsys.readouterr().out


def test_installed_entry_point(numeric_file: Path, tmp_path: Path) -> None:
    """Smoke-test the wired-up console script via a subprocess."""
    out = tmp_path / "subproc.png"
    result = subprocess.run(
        [sys.executable, "-m", "vizit", "line", str(numeric_file), "-c", "2", "--no-show", "-o", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
