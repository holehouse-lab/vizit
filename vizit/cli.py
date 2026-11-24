"""
Command-line interface for vizit.

The CLI is a thin wrapper over the Python API in :mod:`vizit.loader` and
:mod:`vizit.plotting`. It defines one subcommand per plot type
(``line``, ``scatter``, ``hist``, ``bar``), shares argument groups for I/O,
axis, style and output options, and translates the parsed namespace into a
:class:`~vizit.plotting.PlotConfig` plus a single call into the plotting API.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING

from . import __version__
from ._errors import VizitError
from .backend import configure_backend

if TYPE_CHECKING:
    from .dataset import Dataset
    from .plotting import PlotConfig

__all__ = ["main", "build_parser"]


# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def _add_io_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("input")
    group.add_argument(
        "filename",
        help="data file to read, or '-' to read from standard input",
    )
    group.add_argument(
        "-s",
        "--sep",
        default=None,
        help="column separator (default: auto-detect whitespace/comma/tab/semicolon)",
    )
    group.add_argument(
        "--comments",
        default="#@",
        help="characters that mark a comment line (default: '#@')",
    )
    header = group.add_mutually_exclusive_group()
    header.add_argument(
        "--header",
        dest="header",
        action="store_true",
        default=None,
        help="force the first non-comment line to be column names",
    )
    header.add_argument(
        "--no-header",
        dest="header",
        action="store_false",
        help="force all rows to be numeric (no column-name line)",
    )
    group.add_argument(
        "--skip-rows",
        type=int,
        default=0,
        metavar="N",
        help="discard N leading data rows after any header (default: 0)",
    )


def _add_axis_args(parser: argparse.ArgumentParser, *, grid_default: bool = True) -> None:
    group = parser.add_argument_group("axes")
    group.add_argument("--xlabel", help="x-axis label")
    group.add_argument("--ylabel", help="y-axis label")
    group.add_argument("--title", help="figure title")
    group.add_argument("--xlim", metavar="LO,HI", help="x-axis limits, e.g. 0,100")
    group.add_argument("--ylim", metavar="LO,HI", help="y-axis limits, e.g. -5,5")
    group.add_argument("--logx", action="store_true", help="logarithmic x-axis")
    group.add_argument("--logy", action="store_true", help="logarithmic y-axis")
    group.add_argument("--symlogx", action="store_true", help="symmetric-log x-axis")
    group.add_argument("--symlogy", action="store_true", help="symmetric-log y-axis")
    grid = group.add_mutually_exclusive_group()
    grid_help = "show grid" + (" (default)" if grid_default else "")
    no_grid_help = "hide grid" + ("" if grid_default else " (default)")
    grid.add_argument("--grid", dest="grid", action="store_true", default=grid_default, help=grid_help)
    grid.add_argument("--no-grid", dest="grid", action="store_false", help=no_grid_help)
    group.add_argument("--no-legend", dest="legend", action="store_false", default=True, help="hide legend")


def _add_style_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("style")
    group.add_argument("--style", help="matplotlib style name (e.g. ggplot)")
    group.add_argument("--color", action="append", dest="colors", metavar="C", help="series color (repeatable)")
    group.add_argument("--marker", action="append", dest="markers", metavar="M", help="series marker (repeatable)")
    group.add_argument("--figsize", nargs=2, type=float, metavar=("W", "H"), help="figure size in inches")
    group.add_argument("--dpi", type=int, default=150, help="output resolution (default: 150)")


def _add_output_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("output")
    group.add_argument("-o", "--output", help="save figure to this path; format from extension (.png/.pdf/.svg)")
    group.add_argument("--no-show", dest="show", action="store_false", default=True, help="do not open a window")


def _add_common_args(parser: argparse.ArgumentParser, *, grid_default: bool = True) -> None:
    _add_io_args(parser)
    _add_axis_args(parser, grid_default=grid_default)
    _add_style_args(parser)
    _add_output_args(parser)


def build_parser() -> argparse.ArgumentParser:
    """Construct the full argument parser with all subcommands.

    Returns
    -------
    argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="vizit",
        description="Visualize scientific data from the command line.",
    )
    parser.add_argument("--version", action="version", version=f"vizit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="PLOT")

    # line
    p_line = sub.add_parser("line", help="line plot of one or more columns")
    _add_common_args(p_line)
    p_line.add_argument("-c", "--cols", help="1-based y columns, comma-separated (e.g. 2,3,4)")
    p_line.add_argument("-x", help="1-based x column (default: row index)")
    p_line.add_argument("--yerr", help="column with symmetric y error magnitudes")
    p_line.add_argument("--mean", action="store_true", help="overlay mean of each series")
    p_line.add_argument("--median", action="store_true", help="overlay median of each series")
    p_line.add_argument("--fit", action="store_true", help="overlay a linear fit of each series")
    p_line.add_argument("--rolling", type=int, metavar="N", help="overlay a rolling average")

    # scatter
    p_scatter = sub.add_parser("scatter", help="scatter plot of one column against another")
    _add_common_args(p_scatter)
    p_scatter.add_argument("-x", help="1-based x column (default: row index)")
    p_scatter.add_argument("-y", help="1-based y column")
    p_scatter.add_argument("--yerr", help="column with symmetric y error magnitudes")
    p_scatter.add_argument("--fit", action="store_true", help="overlay a linear fit")

    # hist
    p_hist = sub.add_parser("hist", help="histogram of one or more columns")
    _add_common_args(p_hist)
    p_hist.add_argument("-c", "--cols", help="1-based columns, comma-separated")
    p_hist.add_argument("--bins", type=int, default=10, help="number of bins (default: 10)")
    p_hist.add_argument("--density", action="store_true", help="normalise to a density")

    # bar
    p_bar = sub.add_parser("bar", help="bar chart of one or more columns")
    _add_common_args(p_bar)
    p_bar.add_argument("-c", "--cols", help="1-based value columns, comma-separated")
    p_bar.add_argument("-x", help="1-based column for bar positions (default: row index)")

    # heatmap
    p_heat = sub.add_parser(
        "heatmap",
        help="heatmap of a matrix, or the ratio of two matrices",
        description=(
            "Plot a CSV/TSV matrix as a heatmap. Give a second file to plot the "
            "element-wise ratio of the two matrices (FILE / FILE2)."
        ),
    )
    _add_common_args(p_heat, grid_default=False)
    p_heat.add_argument(
        "denominator",
        nargs="?",
        metavar="FILE2",
        help="optional second matrix; the heatmap becomes the ratio FILE / FILE2",
    )
    p_heat.add_argument("-c", "--cols", help="1-based columns forming the matrix, comma-separated")
    p_heat.add_argument("--vmin", type=float, help="lower limit of the color scale (default: data min)")
    p_heat.add_argument("--vmax", type=float, help="upper limit of the color scale (default: data max)")
    p_heat.add_argument(
        "--cmap",
        help="matplotlib colormap name (default: matplotlib's; 'seismic' when two files are given)",
    )
    p_heat.add_argument("--cbar-label", dest="cbar_label", help="colorbar label")
    p_heat.add_argument("--no-colorbar", dest="colorbar", action="store_false", default=True, help="hide the colorbar")
    # A log scale cannot span zero, so these two are inherently incompatible.
    scale = p_heat.add_mutually_exclusive_group()
    scale.add_argument(
        "--log-color",
        dest="log_color",
        action="store_true",
        help="logarithmic color scale (needs strictly positive values)",
    )
    scale.add_argument(
        "--auto-midpoint-zero",
        dest="auto_midpoint_zero",
        action="store_true",
        help="centre the color scale on zero, so zero takes the midpoint colour (white, in seismic)",
    )
    p_heat.add_argument(
        "--aspect",
        default="auto",
        choices=["auto", "equal"],
        help="'auto' fills the axes (default); 'equal' keeps cells square",
    )
    p_heat.add_argument(
        "--origin",
        default="upper",
        choices=["upper", "lower"],
        help="'upper' (default) puts the first row at the top",
    )
    p_heat.add_argument(
        "--interpolation", default="nearest", help="imshow interpolation (default: nearest, i.e. raw cells)"
    )

    return parser


# ----------------------------------------------------------------------
# Namespace -> API translation
# ----------------------------------------------------------------------
def _parse_limits(text: str | None) -> tuple[float | None, float | None] | None:
    """Parse a ``"LO,HI"`` limits string; either side may be blank for auto."""
    if text is None:
        return None
    parts = text.split(",")
    if len(parts) != 2:
        raise VizitError(f"invalid limits {text!r}; expected 'LO,HI'")

    def _one(token: str) -> float | None:
        token = token.strip()
        if token == "":
            return None
        try:
            return float(token)
        except ValueError as exc:
            raise VizitError(f"invalid limit value {token!r}") from exc

    return _one(parts[0]), _one(parts[1])


def _parse_cols(text: str | None) -> list[int | str] | None:
    """Parse a comma-separated column spec into ints (where possible) or names."""
    if text is None:
        return None
    refs: list[int | str] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            refs.append(int(token))
        except ValueError:
            refs.append(token)
    if not refs:
        raise VizitError(f"no columns parsed from {text!r}")
    return refs


def _parse_ref(text: str | None) -> int | str | None:
    """Parse a single column reference as an int index or a name."""
    if text is None:
        return None
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return text


def _config_from_args(args: argparse.Namespace) -> PlotConfig:
    """Build a :class:`~vizit.plotting.PlotConfig` from shared CLI flags."""
    from .plotting import PlotConfig

    return PlotConfig(
        title=args.title,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        legend=args.legend,
        grid=args.grid,
        logx=args.logx,
        logy=args.logy,
        symlogx=args.symlogx,
        symlogy=args.symlogy,
        xlim=_parse_limits(args.xlim),
        ylim=_parse_limits(args.ylim),
        style=args.style,
        colors=args.colors,
        markers=args.markers,
        figsize=tuple(args.figsize) if args.figsize else None,
        dpi=args.dpi,
        output=args.output,
        show=args.show,
    )


def _dispatch(args: argparse.Namespace) -> None:
    """Load the data and call the plotting function for the chosen subcommand."""
    from . import plotting
    from .loader import load

    def _load(path: str) -> Dataset:
        return load(
            path,
            sep=args.sep,
            comments=args.comments,
            header=args.header,
            skip_rows=args.skip_rows,
        )

    ds = _load(args.filename)
    config = _config_from_args(args)

    if args.command == "heatmap":
        plotting.heatmap(
            ds,
            _load(args.denominator) if args.denominator else None,
            cols=_parse_cols(args.cols),
            vmin=args.vmin,
            vmax=args.vmax,
            cmap=args.cmap,
            colorbar=args.colorbar,
            cbar_label=args.cbar_label,
            log_color=args.log_color,
            auto_midpoint_zero=args.auto_midpoint_zero,
            aspect=args.aspect,
            origin=args.origin,
            interpolation=args.interpolation,
            config=config,
        )
    elif args.command == "line":
        plotting.line(
            ds,
            cols=_parse_cols(args.cols),
            x=_parse_ref(args.x),
            yerr=_parse_ref(args.yerr),
            mean=args.mean,
            median=args.median,
            fit=args.fit,
            rolling=args.rolling,
            config=config,
        )
    elif args.command == "scatter":
        plotting.scatter(
            ds,
            x=_parse_ref(args.x),
            y=_parse_ref(args.y),
            yerr=_parse_ref(args.yerr),
            fit=args.fit,
            config=config,
        )
    elif args.command == "hist":
        plotting.hist(
            ds,
            cols=_parse_cols(args.cols),
            bins=args.bins,
            density=args.density,
            config=config,
        )
    elif args.command == "bar":
        plotting.bar(
            ds,
            cols=_parse_cols(args.cols),
            x=_parse_ref(args.x),
            config=config,
        )
    else:  # pragma: no cover - argparse enforces a valid subcommand
        raise VizitError(f"unknown command {args.command!r}")


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``vizit`` command.

    Parameters
    ----------
    argv : sequence of str, optional
        Argument list (excluding the program name). Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code: ``0`` on success, ``2`` on an expected
        :class:`~vizit._errors.VizitError`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Choose the backend before plotting imports pyplot.
    args.show = configure_backend(show=args.show)

    try:
        _dispatch(args)
    except VizitError as err:
        print(f"vizit: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
