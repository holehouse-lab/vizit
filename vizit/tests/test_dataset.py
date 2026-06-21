"""Tests for the :class:`vizit.dataset.Dataset` container."""

from __future__ import annotations

import numpy as np
import pytest

from vizit._errors import ColumnError
from vizit.dataset import Dataset


def _ds(names: list[str] | None = None) -> Dataset:
    data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    return Dataset(data=data, names=names, source="test")


def test_shape_properties() -> None:
    ds = _ds()
    assert ds.n_rows == 2
    assert ds.n_cols == 3
    assert len(ds) == 2


def test_resolve_is_one_based() -> None:
    ds = _ds()
    # Column 1 maps to array column 0.
    assert ds.resolve(1) == 0
    assert ds.resolve(3) == 2
    np.testing.assert_array_equal(ds.column(1), [1.0, 4.0])


def test_resolve_out_of_range_raises() -> None:
    ds = _ds()
    with pytest.raises(ColumnError, match="column 4 requested"):
        ds.resolve(4)
    with pytest.raises(ColumnError):
        ds.resolve(0)


def test_resolve_by_name() -> None:
    ds = _ds(names=["a", "b", "c"])
    assert ds.resolve("b") == 1
    np.testing.assert_array_equal(ds.column("c"), [3.0, 6.0])


def test_resolve_unknown_name_raises() -> None:
    ds = _ds(names=["a", "b", "c"])
    with pytest.raises(ColumnError, match="no column named"):
        ds.resolve("z")


def test_resolve_name_without_header_raises() -> None:
    ds = _ds()
    with pytest.raises(ColumnError, match="no header"):
        ds.resolve("a")


def test_name_of_with_and_without_header() -> None:
    assert _ds(names=["a", "b", "c"]).name_of(2) == "b"
    assert _ds().name_of(2) == "col 2"


def test_columns_preserves_order() -> None:
    ds = _ds()
    out = ds.columns([3, 1])
    assert out.shape == (2, 2)
    np.testing.assert_array_equal(out[:, 0], [3.0, 6.0])
    np.testing.assert_array_equal(out[:, 1], [1.0, 4.0])


def test_rejects_one_dimensional_data() -> None:
    with pytest.raises(ValueError, match="2-dimensional"):
        Dataset(data=np.array([1.0, 2.0]), names=None, source="x")


def test_rejects_name_count_mismatch() -> None:
    with pytest.raises(ValueError, match="column names"):
        Dataset(data=np.zeros((2, 3)), names=["only", "two"], source="x")
