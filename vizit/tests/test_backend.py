"""Tests for backend / headless selection in :mod:`vizit.backend`."""

from __future__ import annotations

import pytest

from vizit import backend


def test_no_show_forces_headless(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MPLBACKEND", raising=False)
    assert backend.configure_backend(show=False) is False


def test_explicit_mplbackend_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MPLBACKEND", "Agg")
    # The requested show value passes through untouched.
    assert backend.configure_backend(show=True) is True


def test_headless_when_no_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MPLBACKEND", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(backend.sys, "platform", "linux")
    assert backend.display_available() is False
    assert backend.configure_backend(show=True) is False


def test_display_available_on_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backend.sys, "platform", "darwin")
    assert backend.display_available() is True


def test_display_available_with_x11(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backend.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    assert backend.display_available() is True
