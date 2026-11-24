"""
Reading tabular numeric data into a :class:`~vizit.dataset.Dataset`.

The loader handles the fiddly parts of real scientific data files: comment
lines (``#``/``@``), a variety of column separators, an optional header row of
column names, and clear, line-numbered error messages when a value cannot be
parsed. ``"-"`` reads from standard input so vizit can be used in pipelines.

Non-numeric columns are tolerated. Data files frequently carry a label column
(a stage name, a residue code) alongside the numbers, and there is no reason to
reject the whole file over a column the user never plots. Such columns are read
as ``NaN`` and flagged; an error is raised only if one is actually selected for
plotting. See :meth:`vizit.dataset.Dataset.column`.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from typing import TextIO

import numpy as np

from ._errors import DataError
from .dataset import Dataset

__all__ = ["load"]

# Separators tried, in order, when ``sep`` is not given. Explicit delimiters are
# preferred over whitespace (``None``, meaning "any run of whitespace") so that a
# tab-separated file with spaces inside a text field splits on tabs.
_AUTO_SEPARATORS: tuple[str | None, ...] = (",", "\t", ";", None)

# Number of data lines sampled when auto-detecting the separator.
_SNIFF_LINES = 50


def load(
    source: str | os.PathLike[str] | TextIO,
    *,
    sep: str | None = None,
    comments: str = "#@",
    header: bool | None = None,
    skip_rows: int = 0,
) -> Dataset:
    """Read tabular numeric data from a file, path, or text stream.

    Parameters
    ----------
    source : str, path-like, or text stream
        Path to a data file, the string ``"-"`` to read from standard input, or
        an already-open text stream.
    sep : str or None, optional
        Column separator. ``None`` (the default) auto-detects between whitespace,
        comma, tab and semicolon. Pass an explicit string (e.g. ``","``) to
        force a particular separator.
    comments : str, optional
        Characters that mark a comment line when they are the first non-whitespace
        character of the line. Default ``"#@"`` (covers gnuplot and xmgrace).
        Pass ``""`` to disable comment handling.
    header : bool or None, optional
        Whether the first non-comment line holds column names. ``True`` forces a
        header, ``False`` forces all-numeric, and ``None`` (default) auto-detects:
        the first non-comment line is treated as a header only if it fails to
        parse as all-numeric.
    skip_rows : int, optional
        Number of leading non-comment data rows to discard *after* any header is
        consumed. Default ``0``.

    Returns
    -------
    Dataset
        The parsed data. A single-column file yields shape ``(n_rows, 1)``.

    Raises
    ------
    DataError
        If the source cannot be read, is empty, contains a non-numeric value in
        the data block, or has rows with differing numbers of columns.

    Examples
    --------
    >>> ds = load("trajectory.dat")                  # doctest: +SKIP
    >>> ds = load("data.csv", sep=",")               # doctest: +SKIP
    >>> import sys; ds = load(sys.stdin)             # doctest: +SKIP
    """
    if skip_rows < 0:
        raise DataError("skip_rows must be >= 0")

    source_name, lines = _read_lines(source)
    data_lines = _strip_comments(lines, comments)

    if not data_lines:
        raise DataError(f"{source_name} contains no data")

    # Resolve the separator once so header detection, header splitting and data
    # parsing all agree (auto-detection from a header row would otherwise differ
    # from auto-detection from the data rows).
    effective_sep = sep if sep is not None else _resolve_separator(data_lines)

    names: list[str] | None = None
    first_is_header = header is True or (
        header is None and _looks_like_header([_split(line, effective_sep) for _, line in data_lines[:2]])
    )
    if first_is_header:
        names = _split(data_lines[0][1], effective_sep)
        data_lines = data_lines[1:]

    if skip_rows:
        data_lines = data_lines[skip_rows:]

    if not data_lines:
        raise DataError(f"{source_name} contains no data rows")

    data, non_numeric = _parse_table(data_lines, effective_sep, source_name)

    if names is not None and len(names) != data.shape[1]:
        raise DataError(f"{source_name}: header has {len(names)} names but data has {data.shape[1]} columns")

    return Dataset(data=data, names=names, source=source_name, non_numeric=non_numeric)


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _read_lines(
    source: str | os.PathLike[str] | TextIO,
) -> tuple[str, list[str]]:
    """Return ``(display_name, lines)`` for any supported source type."""
    if source == "-":
        return "<stdin>", sys.stdin.read().splitlines()
    if hasattr(source, "read"):
        stream: TextIO = source  # type: ignore[assignment]
        name = getattr(stream, "name", "<stream>")
        return str(name), stream.read().splitlines()

    path = os.fspath(source)  # type: ignore[arg-type]
    try:
        with open(path, encoding="utf-8") as handle:
            return path, handle.read().splitlines()
    except FileNotFoundError as exc:
        raise DataError(f"file not found: {path}") from exc
    except OSError as exc:
        raise DataError(f"could not read {path}: {exc}") from exc


def _strip_comments(lines: Iterable[str], comments: str) -> list[tuple[int, str]]:
    """Drop blank and comment lines, keeping 1-based original line numbers."""
    kept: list[tuple[int, str]] = []
    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if comments and stripped[0] in comments:
            continue
        kept.append((lineno, stripped))
    return kept


def _split(line: str, sep: str | None) -> list[str]:
    """Split a single line into string tokens using ``sep``."""
    if sep is None:
        return line.split()
    return [tok.strip() for tok in line.split(sep)]


def _is_float(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def _resolve_separator(data_lines: list[tuple[int, str]]) -> str | None:
    """Pick the separator that splits every sampled line into the same >1 count.

    Explicit delimiters are tried before whitespace so that, for example, a
    tab-separated file with spaces inside a text field is split on tabs rather
    than on every space. Falls back to whitespace (``None``) when no delimiter
    produces a consistent multi-column split (as for single-column data).
    """
    sample = data_lines[:_SNIFF_LINES]
    for candidate in _AUTO_SEPARATORS:
        counts = {len(_split(line, candidate)) for _, line in sample}
        if len(counts) == 1 and counts.pop() > 1:
            return candidate
    return None


def _looks_like_header(rows: list[list[str]]) -> bool:
    """Decide whether the first data line is a row of column names.

    A file may legitimately carry a non-numeric column (a label, a stage name),
    so "the first line isn't all numbers" is not enough to call it a header.
    Instead we compare the first line against the second: it is a header only if
    some column is non-numeric in the first line but numeric in the second — the
    signature of names sitting above numbers.
    """
    if not rows:
        return False
    first = [_is_float(tok) for tok in rows[0]]
    if all(first):
        return False
    if len(rows) < 2:
        # Nothing to compare against: only an entirely non-numeric line reads as
        # a header.
        return not any(first)
    second = [_is_float(tok) for tok in rows[1]]
    return any(not a and b for a, b in zip(first, second, strict=False))


def _parse_table(
    data_lines: list[tuple[int, str]],
    sep: str | None,
    source_name: str,
) -> tuple[np.ndarray, dict[int, tuple[int, str]]]:
    """Parse data rows into a float array, tolerating non-numeric columns.

    Columns that do not parse as numbers are filled with ``NaN`` rather than
    raising: a text column the user never plots is not an error. The offending
    line number and token are recorded per column so that
    :meth:`~vizit.dataset.Dataset.column` can raise a precise error *if and when*
    such a column is actually requested.

    Returns
    -------
    tuple of (numpy.ndarray, dict)
        The ``(n_rows, n_cols)`` float array, and a mapping of 0-based column
        index to the ``(line number, token)`` of the first value that failed to
        parse in that column.
    """
    tokens_per_row: list[list[str]] = []
    width: int | None = None
    for lineno, line in data_lines:
        tokens = _split(line, sep)
        if width is None:
            width = len(tokens)
        elif len(tokens) != width:
            raise DataError(f"{source_name}, line {lineno}: expected {width} columns, got {len(tokens)}")
        tokens_per_row.append(tokens)

    table = np.array(tokens_per_row, dtype=np.str_)
    data = np.full(table.shape, np.nan, dtype=np.float64)
    non_numeric: dict[int, tuple[int, str]] = {}

    for col in range(table.shape[1]):
        try:
            data[:, col] = table[:, col].astype(np.float64)
        except ValueError:
            non_numeric[col] = _first_bad_value(table[:, col], data_lines)

    return data, non_numeric


def _first_bad_value(column: np.ndarray, data_lines: list[tuple[int, str]]) -> tuple[int, str]:
    """Return the ``(line number, token)`` of the first non-numeric cell in a column."""
    for (lineno, _line), token in zip(data_lines, column, strict=False):
        if not _is_float(str(token)):
            return lineno, str(token)
    raise AssertionError("column was reported non-numeric but every value parsed")  # pragma: no cover
