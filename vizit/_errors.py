"""
Exception hierarchy for vizit.

These are raised by the library layer so the CLI can render concise,
user-facing error messages (``vizit: ...``) instead of tracebacks, while
programmatic users still get real, catchable exceptions.
"""

from __future__ import annotations

__all__ = ["VizitError", "DataError", "ColumnError", "PlotError"]


class VizitError(Exception):
    """Base class for all expected, user-facing vizit errors.

    The CLI catches :class:`VizitError` (and subclasses) and prints the message
    without a traceback. Anything that is *not* a :class:`VizitError` is treated
    as a programming bug and allowed to propagate.
    """


class DataError(VizitError):
    """Raised when input data cannot be read or parsed into a :class:`~vizit.dataset.Dataset`."""


class ColumnError(VizitError):
    """Raised when a requested column index or name does not exist."""


class PlotError(VizitError):
    """Raised when plot inputs or options are invalid (e.g. an unknown style)."""
