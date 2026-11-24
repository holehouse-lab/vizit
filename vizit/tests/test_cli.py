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


@pytest.fixture
def matrix_csv(tmp_path: Path) -> Path:
    path = tmp_path / "a.csv"
    path.write_text("1,2\n4,8\n16,32\n")
    return path


@pytest.fixture
def matrix_csv2(tmp_path: Path) -> Path:
    path = tmp_path / "b.csv"
    path.write_text("1,1\n2,4\n4,2\n")
    return path


def test_heatmap_single_file(matrix_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "heat.png"
    rc = cli.main(["heatmap", str(matrix_csv), "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0


def test_heatmap_ratio_of_two_files(matrix_csv: Path, matrix_csv2: Path, tmp_path: Path) -> None:
    out = tmp_path / "ratio.png"
    rc = cli.main(["heatmap", str(matrix_csv), str(matrix_csv2), "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_heatmap_vmin_vmax(matrix_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "scaled.png"
    rc = cli.main(
        ["heatmap", str(matrix_csv), "--vmin", "0", "--vmax", "10", "--cmap", "viridis", "--no-show", "-o", str(out)]
    )
    assert rc == 0
    assert out.exists()


def test_heatmap_auto_midpoint_zero(tmp_path: Path) -> None:
    path = tmp_path / "signed.csv"
    path.write_text("-8,-2\n0,2\n")
    out = tmp_path / "centred.png"
    rc = cli.main(["heatmap", str(path), "--auto-midpoint-zero", "--no-show", "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_heatmap_log_color_and_auto_midpoint_zero_are_exclusive(
    matrix_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        cli.main(["heatmap", str(matrix_csv), "--log-color", "--auto-midpoint-zero", "--no-show"])
    assert "not allowed with" in capsys.readouterr().err


def test_heatmap_ratio_shape_mismatch_returns_2(
    matrix_csv: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    other = tmp_path / "small.csv"
    other.write_text("1,2\n")
    rc = cli.main(["heatmap", str(matrix_csv), str(other), "--no-show"])
    assert rc == 2
    assert "cannot take a ratio" in capsys.readouterr().err


def test_heatmap_tsv(tmp_path: Path) -> None:
    path = tmp_path / "a.tsv"
    path.write_text("1\t2\n3\t4\n")
    out = tmp_path / "tsv.png"
    rc = cli.main(["heatmap", str(path), "--no-show", "-o", str(out)])
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
