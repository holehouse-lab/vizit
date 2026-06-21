"""
Reading tabular numeric data into a :class:`~vizit.dataset.Dataset`.

The loader handles the fiddly parts of real scientific data files: comment
lines (``#``/``@``), a variety of column separators, an optional header row of
column names, and clear, line-numbered error messages when a value cannot be
parsed. ``"-"`` reads from standard input so vizit can be used in pipelines.
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

# Separators tried, in order, when ``sep`` is not given. ``None`` means "any run
# of whitespace" (numpy's default split behaviour).
_AUTO_SEPARATORS: tuple[str | None, ...] = (None, ",", "\t", ";")


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
    # from auto-detection from the numeric data rows).
    effective_sep = sep if sep is not None else _resolve_separator(data_lines)

    names: list[str] | None = None
    first_line = data_lines[0][1]
    first_is_header = header is True or (header is None and not _is_numeric_row(first_line, effective_sep))
    if first_is_header:
        names = _split(first_line, effective_sep)
        data_lines = data_lines[1:]

    if skip_rows:
        data_lines = data_lines[skip_rows:]

    if not data_lines:
        raise DataError(f"{source_name} contains no numeric rows")

    data = _parse_rows(data_lines, effective_sep, source_name)

    if names is not None and len(names) != data.shape[1]:
        raise DataError(f"{source_name}: header has {len(names)} names but data has {data.shape[1]} columns")

    return Dataset(data=data, names=names, source=source_name)


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


def _is_numeric_row(line: str, sep: str | None) -> bool:
    """Return whether every token on ``line`` parses as a float."""
    tokens = _split(line, sep)
    if not tokens:
        return False
    for tok in tokens:
        try:
            float(tok)
        except ValueError:
            return False
    return True


def _detect_separator(line: str) -> str | None:
    """Pick the separator that yields the most numeric tokens for ``line``."""
    best_sep: str | None = None
    best_count = 0
    for candidate in _AUTO_SEPARATORS:
        tokens = _split(line, candidate)
        if len(tokens) > 1 and all(_is_float(tok) for tok in tokens):
            if len(tokens) > best_count:
                best_sep, best_count = candidate, len(tokens)
    return best_sep


def _resolve_separator(data_lines: list[tuple[int, str]]) -> str | None:
    """Detect the separator from the first line that parses as numeric data.

    A header line (non-numeric) yields no detectable separator, so we scan past
    it to a real data row. Falls back to whitespace (``None``) for single-column
    data where no delimiter is present.
    """
    for _lineno, line in data_lines:
        sep = _detect_separator(line)
        if sep is not None:
            return sep
    return None


def _is_float(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def _parse_rows(
    data_lines: list[tuple[int, str]],
    sep: str | None,
    source_name: str,
) -> np.ndarray:
    """Parse numeric rows into a 2-D float array.

    The separator is already resolved by the caller. Values are validated
    eagerly so failures can name the exact file line and offending token;
    numpy's own parse errors are opaque.
    """
    rows: list[list[float]] = []
    width: int | None = None
    for lineno, line in data_lines:
        tokens = _split(line, sep)
        try:
            values = [float(tok) for tok in tokens]
        except ValueError as exc:
            bad = next(tok for tok in tokens if not _is_float(tok))
            raise DataError(f"{source_name}, line {lineno}: could not parse {bad!r} as a number") from exc
        if width is None:
            width = len(values)
        elif len(values) != width:
            raise DataError(f"{source_name}, line {lineno}: expected {width} columns, got {len(values)}")
        rows.append(values)

    array = np.array(rows, dtype=np.float64)
    if array.ndim == 1:  # pragma: no cover - guarded by width checks above
        array = array.reshape(-1, 1)
    return array
