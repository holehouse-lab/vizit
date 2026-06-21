"""
Shared pytest configuration and fixtures for the vizit test suite.

The non-interactive ``Agg`` backend is forced before any test imports
``matplotlib.pyplot`` so plotting tests never try to open a window.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    """Close any matplotlib figures left open by a test."""
    import matplotlib.pyplot as plt

    yield
    plt.close("all")


@pytest.fixture
def numeric_file(tmp_path: Path) -> Path:
    """A whitespace-separated, header-less three-column numeric file."""
    path = tmp_path / "numeric.dat"
    path.write_text("0 1 2\n1 2 4\n2 3 6\n3 4 8\n")
    return path


@pytest.fixture
def commented_file(tmp_path: Path) -> Path:
    """A file with ``#`` and ``@`` comment lines and blank lines."""
    path = tmp_path / "commented.dat"
    path.write_text("# a comment\n@ another comment\n\n0 10\n1 20\n\n2 30\n")
    return path


@pytest.fixture
def header_file(tmp_path: Path) -> Path:
    """A file whose first non-comment line is column names."""
    path = tmp_path / "header.dat"
    path.write_text("time energy\n0 1.0\n1 2.5\n2 1.5\n")
    return path


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """A comma-separated file with a header line."""
    path = tmp_path / "data.csv"
    path.write_text("x,y\n0,1\n1,4\n2,9\n")
    return path


@pytest.fixture
def single_column_file() -> Path:
    """The packaged single-column ``look_and_say.dat`` data file."""
    return DATA_DIR / "look_and_say.dat"
