"""Tests for the plotting API in :mod:`vizit.plotting`."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from matplotlib.figure import Figure

from vizit._errors import PlotError
from vizit.dataset import Dataset
from vizit.plotting import PlotConfig, bar, heatmap, hist, line, scatter


@pytest.fixture
def ds() -> Dataset:
    data = np.array([[0.0, 1.0, 2.0], [1.0, 2.0, 4.0], [2.0, 3.0, 6.0], [3.0, 4.0, 8.0]])
    return Dataset(data=data, names=["t", "a", "b"], source="test.dat")


@pytest.fixture
def labelled_ds() -> Dataset:
    """A dataset whose first column is a non-numeric label (all-NaN)."""
    data = np.array([[np.nan, 1.0, 2.0], [np.nan, 2.0, 4.0], [np.nan, 3.0, 6.0]])
    return Dataset(
        data=data,
        names=None,
        source="labelled.dat",
        non_numeric={0: (1, "equil")},
    )


def test_line_returns_figure(ds: Dataset) -> None:
    fig = line(ds, cols=[2], show=False)
    assert isinstance(fig, Figure)


def test_default_cols_skip_non_numeric(labelled_ds: Dataset) -> None:
    """With no explicit -c, a text column is ignored rather than plotted."""
    fig = line(labelled_ds, show=False)
    assert len(fig.axes[0].lines) == 2  # columns 2 and 3 only


def test_hist_default_cols_skip_non_numeric(labelled_ds: Dataset) -> None:
    fig = hist(labelled_ds, bins=3, show=False)
    assert len(fig.axes[0].patches) == 6  # two numeric columns x 3 bins


def test_explicit_non_numeric_column_raises(labelled_ds: Dataset) -> None:
    from vizit._errors import DataError

    with pytest.raises(DataError, match="not numeric"):
        line(labelled_ds, cols=[1], show=False)


def test_all_non_numeric_raises(show_all_text: Dataset) -> None:
    with pytest.raises(PlotError, match="no numeric columns"):
        line(show_all_text, show=False)


@pytest.fixture
def show_all_text() -> Dataset:
    data = np.full((2, 1), np.nan)
    return Dataset(data=data, names=None, source="text.dat", non_numeric={0: (1, "abc")})


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


# ----------------------------------------------------------------------
# heatmap
# ----------------------------------------------------------------------
def _image_data(fig: Figure) -> np.ndarray:
    """Return the drawn image as a plain float array.

    ``imshow`` stores a masked array (non-finite cells are masked), so unmask it
    back to NaN before asserting.
    """
    array = fig.axes[0].images[0].get_array()
    assert array is not None
    return np.ma.filled(array.astype(float), np.nan)


@pytest.fixture
def mat() -> Dataset:
    """A 3x2 matrix of positive values."""
    data = np.array([[1.0, 2.0], [4.0, 8.0], [16.0, 32.0]])
    return Dataset(data=data, names=None, source="a.csv")


@pytest.fixture
def mat2() -> Dataset:
    """A 3x2 matrix, same shape as ``mat``, containing a zero."""
    data = np.array([[1.0, 1.0], [2.0, 4.0], [0.0, 2.0]])
    return Dataset(data=data, names=None, source="b.csv")


def test_heatmap_draws_an_image(mat: Dataset) -> None:
    fig = heatmap(mat, show=False)
    assert len(fig.axes[0].images) == 1
    np.testing.assert_array_equal(_image_data(fig), mat.data)


def test_heatmap_vmin_vmax_fix_the_scale(mat: Dataset) -> None:
    fig = heatmap(mat, vmin=0, vmax=10, show=False)
    assert fig.axes[0].images[0].get_clim() == (0.0, 10.0)


def test_heatmap_scale_is_automatic_by_default(mat: Dataset) -> None:
    fig = heatmap(mat, show=False)
    assert fig.axes[0].images[0].get_clim() == (1.0, 32.0)


def test_heatmap_colorbar_toggles(mat: Dataset) -> None:
    # The colorbar lives in its own axes, so it shows up as a second axes.
    assert len(heatmap(mat, show=False).axes) == 2
    assert len(heatmap(mat, colorbar=False, show=False).axes) == 1


def test_heatmap_ratio_of_two_files(mat: Dataset, mat2: Dataset) -> None:
    drawn = _image_data(heatmap(mat, mat2, show=False))
    # Element-wise ratio; the zero denominator becomes NaN rather than inf.
    np.testing.assert_allclose(drawn[0], np.array([1.0, 2.0]))
    np.testing.assert_allclose(drawn[1], np.array([2.0, 2.0]))
    assert np.isnan(drawn[2][0])
    np.testing.assert_allclose(drawn[2][1], 16.0)


def test_heatmap_ratio_shape_mismatch_raises(mat: Dataset) -> None:
    other = Dataset(data=np.ones((2, 2)), names=None, source="small.csv")
    with pytest.raises(PlotError, match="cannot take a ratio"):
        heatmap(mat, other, show=False)


def test_heatmap_default_cmap_is_matplotlibs_for_one_file(mat: Dataset) -> None:
    fig = heatmap(mat, show=False)
    assert fig.axes[0].images[0].get_cmap().name == "viridis"


def test_heatmap_default_cmap_is_seismic_for_a_ratio(mat: Dataset, mat2: Dataset) -> None:
    fig = heatmap(mat, mat2, show=False)
    assert fig.axes[0].images[0].get_cmap().name == "seismic"


def test_heatmap_explicit_cmap_overrides_the_ratio_default(mat: Dataset, mat2: Dataset) -> None:
    fig = heatmap(mat, mat2, cmap="viridis", show=False)
    assert fig.axes[0].images[0].get_cmap().name == "viridis"


@pytest.fixture
def signed() -> Dataset:
    """A matrix spanning zero, with a larger negative than positive excursion."""
    data = np.array([[-8.0, -2.0], [0.0, 2.0]])
    return Dataset(data=data, names=None, source="d.csv")


def test_auto_midpoint_zero_puts_zero_at_the_midpoint(signed: Dataset) -> None:
    image = heatmap(signed, auto_midpoint_zero=True, show=False).axes[0].images[0]
    # 0.5 is the midpoint of the colormap.
    assert image.norm(0.0) == pytest.approx(0.5)


def test_auto_midpoint_zero_makes_limits_symmetric(signed: Dataset) -> None:
    image = heatmap(signed, auto_midpoint_zero=True, show=False).axes[0].images[0]
    # Data runs -8..2, so the scale becomes the symmetric -8..8.
    assert image.get_clim() == pytest.approx((-8.0, 8.0))


def test_auto_midpoint_zero_respects_explicit_limits(signed: Dataset) -> None:
    image = heatmap(signed, auto_midpoint_zero=True, vmin=-4, vmax=2, show=False).axes[0].images[0]
    # The larger magnitude wins, keeping the scale symmetric about zero.
    assert image.get_clim() == pytest.approx((-4.0, 4.0))
    assert image.norm(0.0) == pytest.approx(0.5)


def test_auto_midpoint_zero_defaults_to_seismic(signed: Dataset) -> None:
    fig = heatmap(signed, auto_midpoint_zero=True, show=False)
    assert fig.axes[0].images[0].get_cmap().name == "seismic"


def test_auto_midpoint_zero_conflicts_with_log_color(signed: Dataset) -> None:
    with pytest.raises(PlotError, match="cannot be combined"):
        heatmap(signed, auto_midpoint_zero=True, log_color=True, show=False)


def test_auto_midpoint_zero_rejects_an_all_zero_matrix() -> None:
    ds = Dataset(data=np.zeros((2, 2)), names=None, source="z.csv")
    with pytest.raises(PlotError, match="every value is zero"):
        heatmap(ds, auto_midpoint_zero=True, show=False)


def test_heatmap_log_color(mat: Dataset) -> None:
    from matplotlib.colors import LogNorm

    fig = heatmap(mat, log_color=True, show=False)
    assert isinstance(fig.axes[0].images[0].norm, LogNorm)


def test_heatmap_log_color_rejects_non_positive() -> None:
    ds = Dataset(data=np.array([[0.0, 1.0]]), names=None, source="z.csv")
    with pytest.raises(PlotError, match="strictly positive"):
        heatmap(ds, log_color=True, show=False)


def test_heatmap_skips_non_numeric_columns() -> None:
    """A leading text label column is excluded from the matrix."""
    data = np.array([[np.nan, 1.0, 2.0], [np.nan, 3.0, 4.0]])
    ds = Dataset(data=data, names=None, source="l.tsv", non_numeric={0: (1, "row0")})
    assert _image_data(heatmap(ds, show=False)).shape == (2, 2)


def test_heatmap_uses_header_for_column_labels() -> None:
    ds = Dataset(data=np.ones((2, 2)), names=["a", "b"], source="h.csv")
    fig = heatmap(ds, show=False)
    assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == ["a", "b"]


def test_heatmap_grid_defaults_off(mat: Dataset) -> None:
    fig = heatmap(mat, show=False)
    assert not any(line.get_visible() for line in fig.axes[0].get_xgridlines())


def test_heatmap_cols_subset(mat: Dataset) -> None:
    assert _image_data(heatmap(mat, cols=[2], show=False)).shape == (3, 1)


@pytest.mark.parametrize("ext", ["png", "pdf", "svg"])
def test_output_written(ds: Dataset, tmp_path: Path, ext: str) -> None:
    out = tmp_path / f"plot.{ext}"
    line(ds, cols=[2], output=out, show=False)
    assert out.exists()
    assert out.stat().st_size > 0
