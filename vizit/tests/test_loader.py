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
    # Forcing no header keeps the name row as data, which makes both columns
    # non-numeric. That is not an error until a column is actually used.
    ds = load(header_file, header=False)
    assert ds.names is None
    assert ds.numeric_columns == []
    with pytest.raises(DataError, match="not numeric"):
        ds.column(1)


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


def test_bad_value_deferred_until_column_used(tmp_path: Path) -> None:
    """A bad value only errors when its column is actually requested."""
    path = tmp_path / "bad.dat"
    path.write_text("1 2\n3 notanumber\n")
    ds = load(path)  # loading is fine
    assert ds.numeric_columns == [1]
    np.testing.assert_array_equal(ds.column(1), [1, 3])  # the good column works
    with pytest.raises(DataError, match="line 2"):
        ds.column(2)  # the bad one names the offending line and token


def test_label_column_is_tolerated(tmp_path: Path) -> None:
    """A text label column does not block the numeric columns beside it."""
    path = tmp_path / "energy.dat"
    path.write_text(
        "# stage\tstep\tT_K\tE_pot\n"
        "equil\t10\t597.297\t343.947\n"
        "equil\t20\t594.294\t332.271\n"
        "prod\t30\t300.000\t-322.115\n"
    )
    ds = load(path)
    assert ds.n_cols == 4
    assert ds.numeric_columns == [2, 3, 4]
    assert ds.non_numeric == {0: (2, "equil")}
    np.testing.assert_allclose(ds.column(3), [597.297, 594.294, 300.0])
    np.testing.assert_allclose(ds.column(4), [343.947, 332.271, -322.115])


def test_label_column_row_is_not_mistaken_for_a_header(tmp_path: Path) -> None:
    """A first data row with a text column must not be eaten as column names."""
    path = tmp_path / "labelled.dat"
    path.write_text("equil 10 1.5\nequil 20 2.5\nprod 30 3.5\n")
    ds = load(path)
    assert ds.names is None  # no header consumed
    assert ds.n_rows == 3  # all three data rows kept
    np.testing.assert_allclose(ds.column(2), [10, 20, 30])


def test_header_above_a_label_column_still_detected(tmp_path: Path) -> None:
    """Names are still found when the table also carries a text column."""
    path = tmp_path / "both.dat"
    path.write_text("stage step value\nequil 10 1.5\nprod 20 2.5\n")
    ds = load(path)
    assert ds.names == ["stage", "step", "value"]
    assert ds.numeric_columns == [2, 3]
    np.testing.assert_allclose(ds.column("value"), [1.5, 2.5])


def test_non_numeric_column_error_is_informative(tmp_path: Path) -> None:
    path = tmp_path / "labelled.dat"
    path.write_text("equil 10\nprod 20\n")
    ds = load(path)
    with pytest.raises(DataError, match=r"column 1 is not numeric.*'equil'.*numeric columns are 2"):
        ds.column(1)


def test_tab_separated_with_spaces_in_text_field(tmp_path: Path) -> None:
    """Tabs win over whitespace so a spacey label stays one field."""
    path = tmp_path / "spacey.dat"
    path.write_text("run one\t1\t2\nrun two\t3\t4\n")
    ds = load(path)
    assert ds.n_cols == 3
    assert ds.numeric_columns == [2, 3]
    np.testing.assert_allclose(ds.column(2), [1, 3])


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
