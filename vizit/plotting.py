"""
The plotting API: :class:`PlotConfig` plus :func:`line`, :func:`scatter`,
:func:`hist` and :func:`bar`.

Each plot function turns a :class:`~vizit.dataset.Dataset` and a set of options
into a matplotlib :class:`~matplotlib.figure.Figure`, which it returns so that
library users can post-process before saving or showing. Appearance, axis and
output options are collected in :class:`PlotConfig`; every plot function also
accepts those options as keyword overrides for convenience, e.g.
``line(ds, cols=[2, 3], logy=True)``.

``matplotlib.pyplot`` is imported lazily inside functions so that importing
:mod:`vizit` does not select a backend before
:func:`vizit.backend.configure_backend` has run.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ._errors import PlotError
from .dataset import Dataset
from .stats import linear_fit, rolling_mean, summary

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__ = ["PlotConfig", "line", "scatter", "hist", "bar"]


@dataclass(slots=True)
class PlotConfig:
    """Appearance, axis and output options shared by all plot types.

    Parameters
    ----------
    title : str or None
        Figure title. Defaults to the dataset's source name when ``None``.
    xlabel, ylabel : str or None
        Axis labels. Sensible defaults are derived from the selected columns.
    legend : bool
        Whether to draw a legend (only shown when there is more than one label).
    grid : bool
        Whether to draw a background grid.
    logx, logy : bool
        Use a logarithmic scale on the x/y axis.
    symlogx, symlogy : bool
        Use a symmetric-log scale on the x/y axis (handles zero/negative values).
    xlim, ylim : tuple of (float or None, float or None) or None
        Axis limits; either bound may be ``None`` to auto-scale that side.
    style : str or None
        Name of a matplotlib style (e.g. ``"ggplot"``, ``"seaborn-v0_8"``).
    colors : list of str or None
        Cycle of colors applied to successive series.
    markers : list of str or None
        Cycle of marker symbols applied to successive series.
    figsize : tuple of (float, float) or None
        Figure size in inches, ``(width, height)``.
    dpi : int
        Resolution used when saving raster output.
    output : str, path-like, or None
        If set, the figure is saved to this path; the format is inferred from
        the file extension (``.png``, ``.pdf``, ``.svg``, ...).
    show : bool
        Whether to display an interactive window.
    """

    title: str | None = None
    xlabel: str | None = None
    ylabel: str | None = None
    legend: bool = True
    grid: bool = True
    logx: bool = False
    logy: bool = False
    symlogx: bool = False
    symlogy: bool = False
    xlim: tuple[float | None, float | None] | None = None
    ylim: tuple[float | None, float | None] | None = None
    style: str | None = None
    colors: list[str] | None = None
    markers: list[str] | None = None
    figsize: tuple[float, float] | None = None
    dpi: int = 150
    output: str | Any | None = None
    show: bool = True


_CONFIG_FIELDS = frozenset(f.name for f in dataclasses.fields(PlotConfig))


def _resolve_config(config: PlotConfig | None, overrides: dict[str, Any]) -> PlotConfig:
    """Merge keyword overrides onto a (possibly default) :class:`PlotConfig`."""
    base = config if config is not None else PlotConfig()
    if not overrides:
        return base
    unknown = set(overrides) - _CONFIG_FIELDS
    if unknown:
        raise TypeError(
            f"unknown plot option(s): {', '.join(sorted(unknown))}; "
            f"valid options are {', '.join(sorted(_CONFIG_FIELDS))}"
        )
    return dataclasses.replace(base, **overrides)


def _color_for(config: PlotConfig, i: int) -> str | None:
    if not config.colors:
        return None
    return config.colors[i % len(config.colors)]


def _marker_for(config: PlotConfig, i: int) -> str | None:
    if not config.markers:
        return None
    return config.markers[i % len(config.markers)]


def _make_figure(config: PlotConfig) -> tuple[Figure, Axes]:
    """Create a figure/axes pair and apply style and figure-level options."""
    import matplotlib.pyplot as plt

    if config.style is not None:
        if config.style not in plt.style.available and config.style != "default":
            raise PlotError(f"unknown style {config.style!r}; available styles: {', '.join(plt.style.available)}")
        with plt.style.context(config.style):
            fig, ax = plt.subplots(figsize=config.figsize)
    else:
        fig, ax = plt.subplots(figsize=config.figsize)
    return fig, ax


def _apply_axes(ax: Axes, config: PlotConfig, *, default_legend: bool) -> None:
    """Apply axis scales, limits, labels, grid and legend from ``config``."""
    if config.logx:
        ax.set_xscale("log")
    elif config.symlogx:
        ax.set_xscale("symlog")
    if config.logy:
        ax.set_yscale("log")
    elif config.symlogy:
        ax.set_yscale("symlog")

    if config.xlim is not None:
        ax.set_xlim(left=config.xlim[0], right=config.xlim[1])
    if config.ylim is not None:
        ax.set_ylim(bottom=config.ylim[0], top=config.ylim[1])

    if config.xlabel is not None:
        ax.set_xlabel(config.xlabel)
    if config.ylabel is not None:
        ax.set_ylabel(config.ylabel)
    if config.title is not None:
        ax.set_title(config.title)

    ax.grid(config.grid)

    if config.legend and default_legend:
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend()


def _finish(fig: Figure, config: PlotConfig) -> Figure:
    """Save and/or show a figure, then return it."""
    import matplotlib.pyplot as plt

    fig.tight_layout()
    if config.output is not None:
        fig.savefig(config.output, dpi=config.dpi)
    if config.show:
        plt.show()
    return fig


def _x_values(ds: Dataset, x: int | str | None) -> tuple[np.ndarray, str | None]:
    """Return the x-data and its label; default to the row index when ``x`` is None."""
    if x is None:
        return np.arange(ds.n_rows, dtype=float), None
    return ds.column(x), ds.name_of(x)


def _default_y_cols(ds: Dataset, x: int | str | None) -> list[int]:
    """All columns except the chosen x column (1-based)."""
    x_idx = ds.resolve(x) if x is not None else None
    return [i + 1 for i in range(ds.n_cols) if i != x_idx]


def line(
    ds: Dataset,
    cols: Sequence[int | str] | None = None,
    x: int | str | None = None,
    *,
    yerr: int | str | None = None,
    mean: bool = False,
    median: bool = False,
    fit: bool = False,
    rolling: int | None = None,
    config: PlotConfig | None = None,
    **overrides: Any,
) -> Figure:
    """Draw one or more line series.

    Parameters
    ----------
    ds : Dataset
        The data to plot.
    cols : sequence of int or str, optional
        1-based indices or names of the y columns. Defaults to every column
        except ``x``.
    x : int or str, optional
        1-based index or name of the x column. Defaults to the row number.
    yerr : int or str, optional
        Column providing symmetric y error-bar magnitudes. Only meaningful with
        a single y series.
    mean, median : bool, optional
        Overlay a horizontal line at the mean/median of each series.
    fit : bool, optional
        Overlay a linear least-squares fit for each series (the label includes
        the slope and :math:`R^2`).
    rolling : int, optional
        If given, overlay a rolling average with this window for each series.
    config : PlotConfig, optional
        Base configuration; keyword ``overrides`` are merged on top.
    **overrides
        Any :class:`PlotConfig` field, e.g. ``logy=True``.

    Returns
    -------
    matplotlib.figure.Figure
    """
    cfg = _resolve_config(config, overrides)
    refs = list(cols) if cols is not None else _default_y_cols(ds, x)
    if not refs:
        raise PlotError("no y columns to plot")

    xv, xlabel = _x_values(ds, x)
    err = ds.column(yerr) if yerr is not None else None
    if err is not None and len(refs) > 1:
        raise PlotError("yerr can only be used with a single y column")

    fig, ax = _make_figure(cfg)
    for i, ref in enumerate(refs):
        yv = ds.column(ref)
        label = ds.name_of(ref)
        color = _color_for(cfg, i)
        marker = _marker_for(cfg, i)
        if err is not None:
            ax.errorbar(xv, yv, yerr=err, label=label, color=color, marker=marker)
        else:
            ax.plot(xv, yv, label=label, color=color, marker=marker)
        _overlay_stats(ax, xv, yv, label, mean=mean, median=median, fit=fit, rolling=rolling)

    _apply_default_labels(cfg, ax, xlabel, ds, refs)
    _apply_axes(ax, cfg, default_legend=True)
    return _finish(fig, cfg)


def scatter(
    ds: Dataset,
    x: int | str | None = None,
    y: int | str | None = None,
    *,
    yerr: int | str | None = None,
    fit: bool = False,
    config: PlotConfig | None = None,
    **overrides: Any,
) -> Figure:
    """Draw a scatter plot of one column against another.

    Parameters
    ----------
    ds : Dataset
        The data to plot.
    x : int or str, optional
        1-based index or name of the x column. Defaults to the row number.
    y : int or str, optional
        1-based index or name of the y column. Defaults to the first column that
        is not ``x``.
    yerr : int or str, optional
        Column providing symmetric y error-bar magnitudes.
    fit : bool, optional
        Overlay a linear least-squares fit.
    config : PlotConfig, optional
        Base configuration; keyword ``overrides`` are merged on top.
    **overrides
        Any :class:`PlotConfig` field.

    Returns
    -------
    matplotlib.figure.Figure
    """
    cfg = _resolve_config(config, overrides)
    if y is None:
        y = _default_y_cols(ds, x)[0]

    xv, xlabel = _x_values(ds, x)
    yv = ds.column(y)
    ylabel = ds.name_of(y)

    fig, ax = _make_figure(cfg)
    color = _color_for(cfg, 0)
    if yerr is not None:
        ax.errorbar(xv, yv, yerr=ds.column(yerr), fmt="o", label=ylabel, color=color)
    else:
        ax.scatter(xv, yv, label=ylabel, color=color, marker=_marker_for(cfg, 0) or "o")
    if fit:
        _overlay_fit(ax, xv, yv, ylabel)

    if cfg.xlabel is None:
        cfg.xlabel = xlabel or "index"
    if cfg.ylabel is None:
        cfg.ylabel = ylabel
    if cfg.title is None:
        cfg.title = ds.source
    _apply_axes(ax, cfg, default_legend=fit or yerr is not None)
    return _finish(fig, cfg)


def hist(
    ds: Dataset,
    cols: Sequence[int | str] | None = None,
    *,
    bins: int = 10,
    density: bool = False,
    config: PlotConfig | None = None,
    **overrides: Any,
) -> Figure:
    """Draw a histogram of one or more columns.

    Parameters
    ----------
    ds : Dataset
        The data to plot.
    cols : sequence of int or str, optional
        1-based indices or names of the columns to histogram. Defaults to all
        columns.
    bins : int, optional
        Number of histogram bins. Default ``10``.
    density : bool, optional
        If ``True``, normalise the histogram to form a probability density.
    config : PlotConfig, optional
        Base configuration; keyword ``overrides`` are merged on top.
    **overrides
        Any :class:`PlotConfig` field.

    Returns
    -------
    matplotlib.figure.Figure
    """
    cfg = _resolve_config(config, overrides)
    refs = list(cols) if cols is not None else [i + 1 for i in range(ds.n_cols)]

    fig, ax = _make_figure(cfg)
    alpha = 1.0 if len(refs) == 1 else 0.6
    for i, ref in enumerate(refs):
        ax.hist(
            ds.column(ref),
            bins=bins,
            density=density,
            label=ds.name_of(ref),
            color=_color_for(cfg, i),
            alpha=alpha,
        )

    if cfg.xlabel is None:
        cfg.xlabel = ds.name_of(refs[0]) if len(refs) == 1 else "value"
    if cfg.ylabel is None:
        cfg.ylabel = "density" if density else "count"
    if cfg.title is None:
        cfg.title = ds.source
    _apply_axes(ax, cfg, default_legend=len(refs) > 1)
    return _finish(fig, cfg)


def bar(
    ds: Dataset,
    cols: Sequence[int | str] | None = None,
    x: int | str | None = None,
    *,
    config: PlotConfig | None = None,
    **overrides: Any,
) -> Figure:
    """Draw a (optionally grouped) bar chart.

    Parameters
    ----------
    ds : Dataset
        The data to plot.
    cols : sequence of int or str, optional
        1-based indices or names of the value columns. Defaults to every column
        except ``x``. Multiple columns produce grouped bars.
    x : int or str, optional
        1-based index or name of the column giving bar positions. Defaults to
        the row number.
    config : PlotConfig, optional
        Base configuration; keyword ``overrides`` are merged on top.
    **overrides
        Any :class:`PlotConfig` field.

    Returns
    -------
    matplotlib.figure.Figure
    """
    cfg = _resolve_config(config, overrides)
    refs = list(cols) if cols is not None else _default_y_cols(ds, x)
    if not refs:
        raise PlotError("no value columns to plot")

    xv, xlabel = _x_values(ds, x)
    positions = np.arange(len(xv), dtype=float)
    n = len(refs)
    total_width = 0.8
    width = total_width / n

    fig, ax = _make_figure(cfg)
    for i, ref in enumerate(refs):
        offset = (i - (n - 1) / 2) * width
        ax.bar(
            positions + offset,
            ds.column(ref),
            width=width,
            label=ds.name_of(ref),
            color=_color_for(cfg, i),
        )
    ax.set_xticks(positions)
    ax.set_xticklabels([_format_tick(v) for v in xv])

    if cfg.xlabel is None:
        cfg.xlabel = xlabel or "index"
    if cfg.ylabel is None:
        cfg.ylabel = ds.name_of(refs[0]) if n == 1 else "value"
    if cfg.title is None:
        cfg.title = ds.source
    _apply_axes(ax, cfg, default_legend=n > 1)
    return _finish(fig, cfg)


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------
def _format_tick(value: float) -> str:
    """Render a numeric tick label without a trailing ``.0`` for integers."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def _apply_default_labels(
    cfg: PlotConfig,
    ax: Axes,
    xlabel: str | None,
    ds: Dataset,
    refs: Sequence[int | str],
) -> None:
    """Fill in default axis labels and title when not explicitly set."""
    if cfg.xlabel is None:
        cfg.xlabel = xlabel or "index"
    if cfg.ylabel is None:
        cfg.ylabel = ds.name_of(refs[0]) if len(refs) == 1 else "value"
    if cfg.title is None:
        cfg.title = ds.source


def _overlay_stats(
    ax: Axes,
    xv: np.ndarray,
    yv: np.ndarray,
    label: str,
    *,
    mean: bool,
    median: bool,
    fit: bool,
    rolling: int | None,
) -> None:
    """Draw any requested statistical overlays for a single series."""
    if mean or median:
        stats = summary(yv)
        if mean:
            ax.axhline(stats.mean, linestyle="--", linewidth=1, label=f"{label} mean")
        if median:
            ax.axhline(stats.median, linestyle=":", linewidth=1, label=f"{label} median")
    if fit:
        _overlay_fit(ax, xv, yv, label)
    if rolling is not None:
        ax.plot(
            xv,
            rolling_mean(yv, rolling),
            linestyle="--",
            linewidth=1.5,
            label=f"{label} rolling({rolling})",
        )


def _overlay_fit(ax: Axes, xv: np.ndarray, yv: np.ndarray, label: str) -> None:
    """Overlay a linear least-squares fit line on ``ax``."""
    fit_result = linear_fit(xv, yv)
    order = np.argsort(xv)
    ax.plot(
        xv[order],
        fit_result.predict(xv[order]),
        linestyle="-",
        linewidth=1.5,
        label=(f"{label} fit (slope={fit_result.slope:.3g}, $R^2$={fit_result.r_squared:.3f})"),
    )
