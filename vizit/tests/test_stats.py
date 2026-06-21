"""Tests for the pure-numpy helpers in :mod:`vizit.stats`."""

from __future__ import annotations

import numpy as np
import pytest

from vizit._errors import PlotError
from vizit.stats import linear_fit, rolling_mean, summary


def test_linear_fit_perfect_line() -> None:
    x = np.arange(5, dtype=float)
    y = 2.0 * x + 1.0
    fit = linear_fit(x, y)
    assert fit.slope == pytest.approx(2.0)
    assert fit.intercept == pytest.approx(1.0)
    assert fit.r_squared == pytest.approx(1.0)


def test_linear_fit_predict() -> None:
    fit = linear_fit(np.array([0.0, 1.0]), np.array([0.0, 2.0]))
    np.testing.assert_allclose(fit.predict(np.array([3.0])), [6.0])


def test_linear_fit_requires_two_points() -> None:
    with pytest.raises(PlotError, match="two points"):
        linear_fit(np.array([1.0]), np.array([2.0]))


def test_linear_fit_length_mismatch() -> None:
    with pytest.raises(PlotError, match="equal length"):
        linear_fit(np.array([1.0, 2.0]), np.array([1.0]))


def test_rolling_mean_full_windows() -> None:
    y = np.array([1.0, 2.0, 3.0, 4.0])
    out = rolling_mean(y, 2)
    assert out.shape == y.shape
    # First point is a partial window (just y[0]); rest are 2-point means.
    np.testing.assert_allclose(out, [1.0, 1.5, 2.5, 3.5])


def test_rolling_mean_window_one_is_identity() -> None:
    y = np.array([3.0, 1.0, 4.0])
    np.testing.assert_allclose(rolling_mean(y, 1), y)


def test_rolling_mean_window_too_large() -> None:
    with pytest.raises(PlotError, match="larger than"):
        rolling_mean(np.array([1.0, 2.0]), 5)


def test_rolling_mean_window_too_small() -> None:
    with pytest.raises(PlotError, match=">= 1"):
        rolling_mean(np.array([1.0, 2.0]), 0)


def test_summary() -> None:
    s = summary(np.array([1.0, 2.0, 3.0, 4.0]))
    assert s.mean == pytest.approx(2.5)
    assert s.median == pytest.approx(2.5)
    assert s.std == pytest.approx(np.std([1, 2, 3, 4]))


def test_summary_empty_raises() -> None:
    with pytest.raises(PlotError, match="empty"):
        summary(np.array([]))
