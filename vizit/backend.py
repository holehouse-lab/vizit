"""
Matplotlib backend selection.

The historical approach of calling ``matplotlib.use('MacOSX' / 'TkAgg')`` per
platform is wrong: it overrides the user's configuration and forces GUI
backends that may not be installed. Instead we only *force* the non-interactive
``Agg`` backend when no window is wanted or no display is available, and
otherwise leave matplotlib to pick its configured default.

:func:`configure_backend` must be called *before* ``matplotlib.pyplot`` is first
imported. The plotting layer imports ``pyplot`` lazily (inside functions) so
that importing :mod:`vizit` never locks in a backend prematurely.
"""

from __future__ import annotations

import os
import sys

__all__ = ["configure_backend", "display_available"]


def display_available() -> bool:
    """Return whether an interactive display is likely available.

    Returns
    -------
    bool
        ``True`` if a GUI window can probably be shown. macOS and Windows are
        assumed to always have a display; on other platforms a display is
        considered available only if ``DISPLAY`` or ``WAYLAND_DISPLAY`` is set.
    """
    if sys.platform == "darwin" or sys.platform.startswith("win"):
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def configure_backend(*, show: bool) -> bool:
    """Select an appropriate matplotlib backend and return the effective ``show``.

    Call this before importing ``matplotlib.pyplot``.

    Parameters
    ----------
    show : bool
        Whether the caller wants to display an interactive window.

    Returns
    -------
    bool
        The effective ``show`` flag. This is forced to ``False`` when no display
        is available, even if ``show=True`` was requested.

    Notes
    -----
    If the user has explicitly set the ``MPLBACKEND`` environment variable it is
    always respected and never overridden. When a window *is* wanted and a
    display is available, no backend is forced — matplotlib chooses its own
    configured default.
    """
    import matplotlib

    # Respect an explicit user choice unconditionally.
    if os.environ.get("MPLBACKEND"):
        return show

    if not show:
        matplotlib.use("Agg", force=True)
        return False

    if not display_available():
        matplotlib.use("Agg", force=True)
        print(
            "vizit: no display detected; rendering headlessly (use -o to save a file)",
            file=sys.stderr,
        )
        return False

    # A display is available and a window was requested: let matplotlib decide.
    return True
