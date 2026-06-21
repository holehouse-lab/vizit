# vizit

A simple tool for visualizing scientific data — a lightweight, scriptable
replacement for quick gnuplot-style plotting, built on
[numpy](https://numpy.org) and [matplotlib](https://matplotlib.org).

vizit is for the everyday case of *"I have some columns of numbers in a text
file and I want to see them"* — while still handling headers, comments,
multiple series, log axes, error bars, fits and a handful of plot types. It
works three ways:

- as a **command-line tool** — `vizit line data.dat -c 2`
- as a **Python library** — `from vizit import load, line`
- in **shell pipelines** — `cat data.dat | vizit line -`

```bash
vizit line trajectory.dat -x 1 -c 2,3 --logy --title "Energy" -o energy.png
```

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [The data-file model](#the-data-file-model)
- [Column references](#column-references)
- [Command-line interface](#command-line-interface)
  - [Subcommands](#subcommands)
  - [Shared options](#shared-options)
- [Reading from a pipe / stdin](#reading-from-a-pipe--stdin)
- [Statistics & overlays](#statistics--overlays)
- [Styling & output](#styling--output)
- [Headless / no-display behaviour](#headless--no-display-behaviour)
- [Python API](#python-api)
- [Recipes](#recipes)
- [Exit status & error handling](#exit-status--error-handling)
- [Development](#development)
- [Building the docs](#building-the-docs)
- [Copyright](#copyright)

---

## Installation

vizit requires **Python 3.12+**.

```bash
pip install .
# or, for development (tests + tooling):
pip install -e '.[test]'
```

This installs the `vizit` command and the importable `vizit` package. You can
also invoke it as a module: `python -m vizit ...`.

Check the install:

```bash
vizit --version
```

---

## Quick start

A few representative commands (all use the packaged sample file
`vizit/data/look_and_say.dat`, a single column of integers):

```bash
# line plot of the single column, log y-axis, with a title
vizit line vizit/data/look_and_say.dat -c 1 --logy --title "Look and say"

# save to a PNG and don't open a window
vizit line vizit/data/look_and_say.dat -c 1 --logy -o look.png --no-show

# histogram with 5 bins
vizit hist vizit/data/look_and_say.dat -c 1 --bins 5
```

For multi-column files, select the x column and one or more y columns:

```bash
vizit line data.dat -x 1 -c 2,3,4          # three series vs column 1
vizit scatter data.dat -x 1 -y 2 --fit     # scatter + linear fit
vizit bar data.dat -x 1 -c 2,3             # grouped bars
```

---

## The data-file model

vizit reads whitespace- or delimiter-separated **numeric** tables. The parser
handles the messy realities of scientific data files:

- **Comments.** Any line whose first non-blank character is `#` or `@` is
  ignored. Change the markers with `--comments` (e.g. `--comments '%'`), or pass
  `--comments ''` to disable comment handling. Blank lines are always skipped.
- **Separators.** Whitespace, comma, tab and semicolon are auto-detected. Force
  a specific one with `-s/--sep` — for example `-s ,` for CSV, or
  ``-s $'\t'`` for tab-separated data.
- **Headers.** If the first non-comment line is *not* all-numeric, it is taken
  as a row of column names. You can then select columns by name. Force the
  behaviour either way with `--header` / `--no-header`.
- **Scientific notation** (`1.5e-3`) is supported natively.
- **Leading rows** can be discarded with `--skip-rows N` (applied after any
  header line is consumed).

Example file with a header and a comment:

```
# simulation run 7
time   energy   error
0.0    0.10     0.01
1.0    0.22     0.02
2.0    0.31     0.02
```

> **Note on headers vs comments.** Column names are read from a *plain*
> (non-comment) header line. A `#`-prefixed line like `# time energy` is treated
> as a comment and skipped, so it is **not** used for names. Put the names on
> their own uncommented line if you want name-based selection.

Malformed input is reported with the exact file line number and offending
token, e.g. `vizit: data.dat, line 4: could not parse 'NA' as a number`.

---

## Column references

All column references — on the command line and in the Python API — are
**1-based**: column `1` is the first column. This matches the convention used by
gnuplot and `awk`.

- Numeric: `-c 2`, `-c 2,3,4`, `-x 1`, `-y 2`, `--yerr 3`
- By name (when the file has a header): `-c energy`, `-c energy,error`,
  `-x time`
- When no `x` column is given, the **row index** (starting at 0) is used as the
  x-axis.

An out-of-range index or unknown name produces a clear error listing the valid
columns.

---

## Command-line interface

```
vizit <plot> <file> [options]
```

`<plot>` is one of `line`, `scatter`, `hist`, `bar`. `<file>` is a path, or `-`
to read standard input. Run `vizit <plot> --help` for the exact, up-to-date
flag list.

### Subcommands

**`line`** — line plot of one or more y columns against an x column (or the row
index), with optional statistical overlays.

| Flag | Meaning |
|---|---|
| `-c, --cols` | 1-based y columns, comma-separated (e.g. `2,3,4`) |
| `-x` | 1-based x column (default: row index) |
| `--yerr` | column of symmetric y error-bar magnitudes |
| `--mean` | overlay the mean of each series |
| `--median` | overlay the median of each series |
| `--fit` | overlay a linear least-squares fit of each series |
| `--rolling N` | overlay a rolling average with window `N` |

**`scatter`** — scatter plot of one column against another.

| Flag | Meaning |
|---|---|
| `-x` | 1-based x column (default: row index) |
| `-y` | 1-based y column |
| `--yerr` | column of symmetric y error-bar magnitudes |
| `--fit` | overlay a linear least-squares fit |

**`hist`** — histogram of one or more columns.

| Flag | Meaning |
|---|---|
| `-c, --cols` | 1-based columns, comma-separated |
| `--bins N` | number of bins (default: 10) |
| `--density` | normalise to a probability density |

**`bar`** — bar chart of one or more value columns (multiple columns produce
grouped bars).

| Flag | Meaning |
|---|---|
| `-c, --cols` | 1-based value columns, comma-separated |
| `-x` | 1-based column for bar positions (default: row index) |

### Shared options

Every subcommand accepts the following groups.

**Input**

| Flag | Meaning |
|---|---|
| `-s, --sep SEP` | column separator (default: auto-detect) |
| `--comments CHARS` | comment-line markers (default: `#@`) |
| `--header` / `--no-header` | force / disable the column-name header line |
| `--skip-rows N` | discard `N` leading data rows |

**Axes**

| Flag | Meaning |
|---|---|
| `--xlabel` / `--ylabel` | axis labels |
| `--title` | figure title |
| `--xlim LO,HI` | x-axis limits (either side may be left blank, e.g. `0,` ) |
| `--ylim LO,HI` | y-axis limits |
| `--logx` / `--logy` | logarithmic axis |
| `--symlogx` / `--symlogy` | symmetric-log axis (handles zero/negative values) |
| `--grid` / `--no-grid` | toggle the background grid (default: on) |
| `--no-legend` | hide the legend |

**Style**

| Flag | Meaning |
|---|---|
| `--style NAME` | matplotlib style (e.g. `ggplot`, `seaborn-v0_8`) |
| `--color C` | series color (repeatable, cycles over series) |
| `--marker M` | series marker (repeatable) |
| `--figsize W H` | figure size in inches |
| `--dpi N` | output resolution (default: 150) |

**Output**

| Flag | Meaning |
|---|---|
| `-o, --output PATH` | save figure; format inferred from extension (`.png`, `.pdf`, `.svg`, …) |
| `--no-show` | do not open an interactive window |

---

## Reading from a pipe / stdin

Use `-` as the filename to read from standard input, so vizit drops into shell
pipelines:

```bash
cat data.dat | vizit line -
awk '{print $1, $5}' raw.log | vizit line - -o out.png --no-show
seq 1 100 | vizit hist - --bins 20 --no-show -o hist.png
```

Because stdin is consumed for *data*, combine it with `-o ... --no-show` when
running non-interactively.

---

## Statistics & overlays

The `line` plot can add analysis overlays computed with numpy:

```bash
vizit line noisy.dat -c 1 --mean --median     # horizontal mean/median lines
vizit line noisy.dat -c 1 --rolling 20        # 20-point rolling average
vizit line data.dat  -x 1 -c 2 --fit          # linear least-squares fit
```

The `--fit` legend entry includes the fitted slope and R². `scatter` also
supports `--fit`. Error bars are drawn by pointing `--yerr` at a column of
symmetric magnitudes (single series only):

```bash
vizit line data.dat -x 1 -c 2 --yerr 3
```

---

## Styling & output

```bash
vizit line data.dat -c 2 \
  --style ggplot \
  --color tab:red --marker o \
  --figsize 8 5 --dpi 300 \
  --title "Run 7" --xlabel "time (ns)" --ylabel "energy" \
  -o figure.pdf --no-show
```

The output format is taken from the file extension, so `-o figure.pdf` produces
a vector PDF and `-o figure.svg` an SVG — handy for publication figures.

---

## Headless / no-display behaviour

vizit never hardcodes a GUI backend. It shows an interactive window by default,
but automatically falls back to non-interactive rendering when:

- you pass `--no-show`, or
- no display is detected (e.g. over SSH without X forwarding).

In the headless case, use `-o` to capture the figure to a file. If you set the
`MPLBACKEND` environment variable, vizit respects your choice and does not
override it.

---

## Python API

The CLI is a thin wrapper over the library, so anything you can do from the
shell you can do from Python. Each plotting function returns a matplotlib
[`Figure`](https://matplotlib.org/stable/api/figure_api.html), which you can
keep customising before saving or showing.

```python
from vizit import load, line, scatter, hist, bar, PlotConfig

# Load once into a Dataset, then plot.
ds = load("data.dat")               # auto-detects separator/header/comments
ds = load("data.csv", sep=",")      # force a separator
ds = load("-", header=True)         # read stdin, force a header row

fig = line(ds, cols=[2, 3], x=1, logy=True)
fig.savefig("plot.png", dpi=300)
```

Columns may be given by 1-based index or by name:

```python
line(ds, x="time", cols=["energy", "error"])
```

Options can be passed as keyword overrides, or bundled in a reusable
`PlotConfig`:

```python
# inline overrides
line(ds, cols=[2], logy=True, title="Run 7", output="run7.png", show=False)

# or a shared config object
cfg = PlotConfig(style="ggplot", figsize=(8, 5), dpi=300, show=False)
line(ds, cols=[2], config=cfg, output="a.png")
scatter(ds, x=1, y=2, fit=True, config=cfg, output="b.png")
```

The `Dataset` container exposes the underlying numpy array and helpers:

```python
ds.data            # 2-D float64 numpy array, shape (n_rows, n_cols)
ds.n_rows, ds.n_cols
ds.column(2)       # 1-D array of column 2 (1-based) — or ds.column("energy")
ds.columns([2, 3]) # 2-D array of the selected columns
ds.name_of(2)      # display label ("energy", or "col 2" if no header)
```

Post-process the returned figure with the full matplotlib API:

```python
fig = line(ds, cols=[2], show=False)
ax = fig.axes[0]
ax.axvspan(10, 20, alpha=0.2, color="red")
fig.savefig("annotated.png", dpi=300)
```

---

## Recipes

```bash
# Multiple series vs a shared x, log scale, legend off
vizit line data.dat -x 1 -c 2,3,4 --logy --no-legend

# Select columns by name (file has a header line)
vizit line data.dat -x time -c energy,entropy

# CSV input, custom axis limits
vizit scatter data.csv -s , -x 1 -y 2 --xlim 0,100 --ylim -5,5

# Density histogram of two columns overlaid
vizit hist samples.dat -c 1,2 --bins 40 --density

# Smooth a noisy signal and mark its mean
vizit line noisy.dat -c 1 --rolling 25 --mean -o smoothed.png --no-show

# Build a figure straight from a pipeline
grep -v '^#' raw.tsv | cut -f1,3 | vizit line - -s $'\t' -o out.pdf --no-show
```

---

## Exit status & error handling

vizit returns:

- `0` on success
- `2` for expected errors (missing file, bad column, malformed value, bad
  option) — it prints a concise `vizit: ...` message to standard error, with no
  Python traceback.

This makes it safe to use in scripts (`vizit ... || echo "plot failed"`). In the
Python API the same conditions raise a `vizit.VizitError` subclass
(`DataError`, `ColumnError`, `PlotError`) that you can catch.

---

## Development

```bash
pip install -e '.[test]'

pytest          # run the test suite
ruff check .    # lint
ruff format .   # format
mypy vizit      # type-check
```

Versioning is handled automatically from git tags by
[versioningit](https://versioningit.readthedocs.io); to cut a release, tag the
commit (`git tag -a X.Y.Z -m "vizit X.Y.Z" && git push --follow-tags`).
Continuous integration runs on GitHub Actions (see `.github/workflows/ci.yml`).

---

## Building the docs

Full documentation (getting started, CLI reference, examples and API) lives in
`docs/` and is built with Sphinx:

```bash
pip install sphinx sphinx_rtd_theme
cd docs && make html
# open docs/_build/html/index.html
```

---

## Copyright

Copyright (c) 2020-2026, Alex Holehouse — released under the LGPL-3.0-or-later
license.

#### Acknowledgements

Project originally based on the
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.
