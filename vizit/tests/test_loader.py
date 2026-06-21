"""Tests for :func:`vizit.loader.load`."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

from vizit._errors import DataError
from vizit.loader import load


def test_load_numeric(numeric_file: Path) -> None:
    ds = load(numeric_file)
    assert ds.data.shape == (4, 3)
    assert ds.names is None
    np.testing.assert_array_equal(ds.column(1), [0, 1, 2, 3])


def test_strips_comments_and_blanks(commented_file: Path) -> None:
    ds = load(commented_file)
    assert ds.data.shape == (3, 2)
    np.testing.assert_array_equal(ds.column(2), [10, 20, 30])


def test_header_autodetect(header_file: Path) -> None:
    ds = load(header_file)
    assert ds.names == ["time", "energy"]
    assert ds.data.shape == (3, 2)


def test_header_forced_off(header_file: Path) -> None:
    # Forcing no header makes the name row a parse error.
    with pytest.raises(DataError, match="could not parse"):
        load(header_file, header=False)


def test_header_forced_on(numeric_file: Path) -> None:
    ds = load(numeric_file, header=True)
    assert ds.names == ["0", "1", "2"]
    assert ds.data.shape == (3, 3)


def test_comma_separator(csv_file: Path) -> None:
    ds = load(csv_file, sep=",")
    assert ds.names == ["x", "y"]
    np.testing.assert_array_equal(ds.column("y"), [1, 4, 9])


def test_comma_autodetect(csv_file: Path) -> None:
    ds = load(csv_file)  # no sep given
    assert ds.names == ["x", "y"]
    assert ds.data.shape == (3, 2)


def test_scientific_notation(tmp_path: Path) -> None:
    path = tmp_path / "sci.dat"
    path.write_text("1e-3 2.0\n1.5e2 3e0\n")
    ds = load(path)
    np.testing.assert_allclose(ds.column(1), [1e-3, 150.0])


def test_skip_rows(numeric_file: Path) -> None:
    ds = load(numeric_file, skip_rows=2)
    assert ds.data.shape == (2, 3)
    np.testing.assert_array_equal(ds.column(1), [2, 3])


def test_single_column_file(single_column_file: Path) -> None:
    ds = load(single_column_file)
    assert ds.n_cols == 1
    assert ds.n_rows > 0


def test_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("1 2\n3 4\n"))
    ds = load("-")
    assert ds.source == "<stdin>"
    assert ds.data.shape == (2, 2)


def test_stream_source() -> None:
    ds = load(io.StringIO("5 6\n7 8\n"))
    assert ds.data.shape == (2, 2)


def test_missing_file_raises() -> None:
    with pytest.raises(DataError, match="file not found"):
        load("/no/such/file.dat")


def test_bad_value_names_line(tmp_path: Path) -> None:
    path = tmp_path / "bad.dat"
    path.write_text("1 2\n3 notanumber\n")
    with pytest.raises(DataError, match="line 2"):
        load(path)


def test_ragged_rows_raise(tmp_path: Path) -> None:
    path = tmp_path / "ragged.dat"
    path.write_text("1 2 3\n4 5\n")
    with pytest.raises(DataError, match="expected 3 columns"):
        load(path)


def test_empty_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "empty.dat"
    path.write_text("# only a comment\n")
    with pytest.raises(DataError, match="no data"):
        load(path)


def test_negative_skip_rows_raises(numeric_file: Path) -> None:
    with pytest.raises(DataError, match="skip_rows"):
        load(numeric_file, skip_rows=-1)
