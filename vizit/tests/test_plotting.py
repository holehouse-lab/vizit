"""Tests for the plotting API in :mod:`vizit.plotting`."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from matplotlib.figure import Figure

from vizit._errors import PlotError
from vizit.dataset import Dataset
from vizit.plotting import PlotConfig, bar, hist, line, scatter


@pytest.fixture
def ds() -> Dataset:
    data = np.array([[0.0, 1.0, 2.0], [1.0, 2.0, 4.0], [2.0, 3.0, 6.0], [3.0, 4.0, 8.0]])
    return Dataset(data=data, names=["t", "a", "b"], source="test.dat")


def test_line_returns_figure(ds: Dataset) -> None:
    fig = line(ds, cols=[2], show=False)
    assert isinstance(fig, Figure)


def test_line_multi_series_artist_count(ds: Dataset) -> None:
    fig = line(ds, cols=[2, 3], x=1, show=False)
    ax = fig.axes[0]
    assert len(ax.lines) == 2
    labels = [ln.get_label() for ln in ax.lines]
    assert labels == ["a", "b"]


def test_line_default_cols_excludes_x(ds: Dataset) -> None:
    fig = line(ds, x=1, show=False)
    # Columns 2 and 3 plotted (column 1 is x).
    assert len(fig.axes[0].lines) == 2


def test_log_scale_applied(ds: Dataset) -> None:
    fig = line(ds, cols=[2], logy=True, show=False)
    assert fig.axes[0].get_yscale() == "log"


def test_symlog_scale_applied(ds: Dataset) -> None:
    fig = line(ds, cols=[2], symlogx=True, show=False)
    assert fig.axes[0].get_xscale() == "symlog"


def test_limits_and_labels(ds: Dataset) -> None:
    fig = line(ds, cols=[2], xlim=(0, 3), ylim=(0, 5), xlabel="X", ylabel="Y", title="T", show=False)
    ax = fig.axes[0]
    assert ax.get_xlim() == (0.0, 3.0)
    assert ax.get_ylim() == (0.0, 5.0)
    assert ax.get_xlabel() == "X"
    assert ax.get_ylabel() == "Y"
    assert ax.get_title() == "T"


def test_default_title_is_source(ds: Dataset) -> None:
    fig = line(ds, cols=[2], show=False)
    assert fig.axes[0].get_title() == "test.dat"


def test_mean_and_fit_add_artists(ds: Dataset) -> None:
    base = len(line(ds, cols=[2], show=False).axes[0].lines)
    fig = line(ds, cols=[2], mean=True, fit=True, show=False)
    # One data line + mean (axhline) + fit line.
    assert len(fig.axes[0].lines) == base + 2


def test_rolling_adds_artist(ds: Dataset) -> None:
    fig = line(ds, cols=[2], rolling=2, show=False)
    assert len(fig.axes[0].lines) == 2


def test_yerr_multi_column_raises(ds: Dataset) -> None:
    with pytest.raises(PlotError, match="single y column"):
        line(ds, cols=[2, 3], yerr=1, show=False)


def test_scatter(ds: Dataset) -> None:
    fig = scatter(ds, x=1, y=2, show=False)
    assert len(fig.axes[0].collections) == 1


def test_scatter_fit_adds_line(ds: Dataset) -> None:
    fig = scatter(ds, x=1, y=2, fit=True, show=False)
    assert len(fig.axes[0].lines) == 1


def test_hist_bins(ds: Dataset) -> None:
    fig = hist(ds, cols=[2], bins=4, show=False)
    # One Patch per bin.
    assert len(fig.axes[0].patches) == 4


def test_hist_multi_column(ds: Dataset) -> None:
    fig = hist(ds, cols=[2, 3], bins=3, show=False)
    assert len(fig.axes[0].patches) == 6


def test_bar(ds: Dataset) -> None:
    fig = bar(ds, cols=[2], show=False)
    assert len(fig.axes[0].patches) == ds.n_rows


def test_unknown_override_raises(ds: Dataset) -> None:
    with pytest.raises(TypeError, match="unknown plot option"):
        line(ds, cols=[2], show=False, nonsense=True)


def test_unknown_style_raises(ds: Dataset) -> None:
    with pytest.raises(PlotError, match="unknown style"):
        line(ds, cols=[2], style="not-a-real-style", show=False)


def test_config_object_used(ds: Dataset) -> None:
    cfg = PlotConfig(logy=True, show=False)
    fig = line(ds, cols=[2], config=cfg)
    assert fig.axes[0].get_yscale() == "log"


@pytest.mark.parametrize("ext", ["png", "pdf", "svg"])
def test_output_written(ds: Dataset, tmp_path: Path, ext: str) -> None:
    out = tmp_path / f"plot.{ext}"
    line(ds, cols=[2], output=out, show=False)
    assert out.exists()
    assert out.stat().st_size > 0
