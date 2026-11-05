"""Native desktop GUI window launcher for Deadliner using PyWebView."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from deadliner.gui_bridge import DeadlinerGuiApi
from deadliner.storage import DataStore

UI_DIR = Path(__file__).resolve().parent / "ui"
UI_INDEX_PATH = UI_DIR / "index.html"


def get_ui_index_path() -> Path:
    """Return the path to the packaged HTML entrypoint for the desktop interface."""
    return UI_INDEX_PATH


def should_default_to_gui() -> bool:
    """Return True if invoking `deadliner` with no arguments should open the GUI by default.

    True when compiled as a standalone binary (`sys.frozen`) or when `DEADLINER_DEFAULT_GUI=1`
    is set in the environment. Otherwise defaults to False so CLI users keep `deadliner menu`.
    """
    if os.environ.get("DEADLINER_DEFAULT_GUI", "").strip().lower() in ("1", "true", "yes"):
        return True
    return bool(getattr(sys, "frozen", False))


def launch_gui(debug: bool = False, store: DataStore | None = None) -> int:
    """Create and start the native Deadliner desktop window."""
    try:
        import webview
    except ImportError:
        print(
            "error: pywebview is required to launch the desktop GUI. "
            "Install it with `pip install pywebview>=5.0.0`.",
            file=sys.stderr,
        )
        return 1

    index_path = get_ui_index_path()
    if not index_path.is_file():
        print(f"error: UI entrypoint not found at {index_path}", file=sys.stderr)
        return 1

    api = DeadlinerGuiApi(store=store)

    try:
        window = webview.create_window(
            title="Deadliner — Academic Command Workspace",
            url=index_path.as_uri(),
            js_api=api,
            width=1240,
            height=800,
            min_size=(940, 620),
            background_color="#050508",
            text_select=True,
        )
        webview.start(debug=bool(debug))
        _ = window
        return 0
    except Exception as e:
        print(f"error: Failed to start desktop GUI window: {e}", file=sys.stderr)
        return 1


def _cmd_gui(args: argparse.Namespace | None = None) -> int:
    """CLI handler for `deadliner gui`."""
    debug = bool(getattr(args, "debug", False)) if args is not None else False
    return launch_gui(debug=debug)

