"""
The :class:`Dataset` container — vizit's in-memory representation of a numeric
data table.

A :class:`Dataset` wraps a single 2-D :class:`numpy.ndarray` (``float64``)
together with optional column names parsed from a header line. Reading, comment
stripping and header detection are the responsibility of :mod:`vizit.loader`.

Columns that are not numeric — a stage label, a residue name — are kept as
``NaN`` and listed in :attr:`Dataset.non_numeric`. They cost nothing until you
ask for them: :meth:`Dataset.column` raises only when a non-numeric column is
actually selected, so a text column sitting next to the numbers you care about
never blocks a plot.

Column indexing convention
--------------------------
All *user-facing* column references are **1-based** (column ``1`` is the first
column), matching the convention familiar to gnuplot/awk users. The single
conversion to 0-based array indexing happens in :meth:`Dataset.resolve`; no
other part of the codebase performs index arithmetic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from ._errors import ColumnError, DataError

__all__ = ["Dataset"]


@dataclass(frozen=True, slots=True)
class Dataset:
    """Tabular numeric data: a 2-D array plus optional column names.

    Columns that could not be parsed as numbers (a label column, say) are held
    as ``NaN`` and recorded in :attr:`non_numeric`. They are not an error in
    themselves — only selecting one for plotting is. See :meth:`column`.

    Parameters
    ----------
    data : numpy.ndarray
        Two-dimensional array of shape ``(n_rows, n_cols)`` and dtype
        ``float64``. A single-column file yields shape ``(n_rows, 1)``. Cells
        that did not parse as numbers hold ``NaN``.
    names : list of str or None
        Column names parsed from a header line, or ``None`` when the source had
        no header. When provided, its length must equal ``n_cols``.
    source : str
        Human-readable origin of the data (a file path or ``"<stdin>"``), used
        to build default plot titles.
    non_numeric : dict, optional
        Maps the 0-based index of each non-numeric column to the
        ``(line number, token)`` of the first value in it that failed to parse.
        Empty (the default) when every column is numeric.

    Raises
    ------
    ValueError
        If ``data`` is not two-dimensional, or if ``names`` is given but its
        length does not match the number of columns.
    """

    data: np.ndarray
    names: list[str] | None
    source: str
    non_numeric: dict[int, tuple[int, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.data.ndim != 2:
            raise ValueError(f"Dataset.data must be 2-dimensional, got {self.data.ndim}-D")
        if self.names is not None and len(self.names) != self.data.shape[1]:
            raise ValueError(f"got {len(self.names)} column names for {self.data.shape[1]} columns")

    # ------------------------------------------------------------------
    # Shape helpers
    # ------------------------------------------------------------------
    @property
    def n_rows(self) -> int:
        """Number of data rows."""
        return int(self.data.shape[0])

    @property
    def n_cols(self) -> int:
        """Number of columns."""
        return int(self.data.shape[1])

    def __len__(self) -> int:
        return self.n_rows

    @property
    def numeric_columns(self) -> list[int]:
        """1-based indices of the columns that parsed fully as numbers.

        Returns
        -------
        list of int
            Plottable columns, in file order. Columns holding text (and so
            recorded in :attr:`non_numeric`) are excluded.
        """
        return [i + 1 for i in range(self.n_cols) if i not in self.non_numeric]

    # ------------------------------------------------------------------
    # Column access (all public methods take 1-based indices or names)
    # ------------------------------------------------------------------
    def resolve(self, ref: int | str) -> int:
        """Map a 1-based index or column name to a 0-based array index.

        Parameters
        ----------
        ref : int or str
            A 1-based column number, or a column name matching the header.

        Returns
        -------
        int
            The corresponding 0-based index into :attr:`data`.

        Raises
        ------
        ColumnError
            If the index is out of range or the name is not found.
        """
        if isinstance(ref, str):
            return self._resolve_name(ref)
        if ref < 1 or ref > self.n_cols:
            raise ColumnError(f"{self.source} has {self.n_cols} column(s); column {ref} requested")
        return ref - 1

    def _resolve_name(self, name: str) -> int:
        if self.names is None:
            raise ColumnError(
                f"{self.source} has no header; cannot select column by name {name!r} "
                f"(use a 1-based index between 1 and {self.n_cols})"
            )
        # Exact match first, then whitespace-stripped match.
        if name in self.names:
            return self.names.index(name)
        stripped = [n.strip() for n in self.names]
        if name in stripped:
            return stripped.index(name)
        raise ColumnError(f"{self.source} has no column named {name!r}; available names: {', '.join(self.names)}")

    def _require_numeric(self, idx: int) -> None:
        """Raise if the 0-based column ``idx`` holds values that are not numbers."""
        if idx not in self.non_numeric:
            return
        lineno, token = self.non_numeric[idx]
        label = f"column {idx + 1}"
        if self.names is not None:
            label = f"column {idx + 1} ({self.names[idx]!r})"
        usable = self.numeric_columns
        hint = (
            f"numeric columns are {', '.join(str(c) for c in usable)}"
            if usable
            else "this file has no numeric columns"
        )
        raise DataError(f"{self.source}: {label} is not numeric — line {lineno} contains {token!r}; {hint}")

    def column(self, ref: int | str) -> np.ndarray:
        """Return a single column as a 1-D array.

        Parameters
        ----------
        ref : int or str
            A 1-based column index or a column name.

        Returns
        -------
        numpy.ndarray
            A 1-D view of the requested column.

        Raises
        ------
        ColumnError
            If the index is out of range or the name is not found.
        DataError
            If the column exists but does not hold numeric data. Non-numeric
            columns are only rejected here, at the point of use — loading a file
            that contains one is fine.
        """
        idx = self.resolve(ref)
        self._require_numeric(idx)
        return self.data[:, idx]

    def columns(self, refs: Sequence[int | str]) -> np.ndarray:
        """Return several columns as a 2-D array, in the requested order.

        Parameters
        ----------
        refs : sequence of int or str
            1-based column indices and/or names.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_rows, len(refs))``.

        Raises
        ------
        ColumnError
            If an index is out of range or a name is not found.
        DataError
            If any selected column does not hold numeric data.
        """
        idxs = [self.resolve(r) for r in refs]
        for idx in idxs:
            self._require_numeric(idx)
        return self.data[:, idxs]

    def name_of(self, ref: int | str) -> str:
        """Return a display label for a column.

        Uses the header name when available, otherwise a generated ``"col N"``
        label (1-based).

        Parameters
        ----------
        ref : int or str
            A 1-based column index or a column name.

        Returns
        -------
        str
            The column's display label.
        """
        idx = self.resolve(ref)
        if self.names is not None:
            return self.names[idx]
        return f"col {idx + 1}"
