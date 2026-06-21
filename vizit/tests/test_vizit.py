"""Smoke test for the top-level :mod:`vizit` package."""

from __future__ import annotations

import vizit


def test_public_api_exposed() -> None:
    """The documented public names are importable from the package root."""
    for name in ("load", "Dataset", "line", "scatter", "hist", "bar", "PlotConfig"):
        assert hasattr(vizit, name)


def test_version_is_a_string() -> None:
    assert isinstance(vizit.__version__, str)
    assert vizit.__version__
