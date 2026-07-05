import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from deadliner import moodle_fetcher
from deadliner.formatter import format_assignment, sort_assignments
from deadliner.models import AuthError

CONFIG_PATH = Path.home() / ".deadliner.json"


def _load_credentials() -> tuple[str, str]:
    """Read Moodle credentials from env vars, falling back to ~/.deadliner.json.

    Env vars: DEADLINER_MOODLE_URL / DEADLINER_MOODLE_TOKEN.
    Config file shape: {"moodle_base_url": "...", "moodle_token": "..."}.
    """
    base_url = os.environ.get("DEADLINER_MOODLE_URL", "")
    token = os.environ.get("DEADLINER_MOODLE_TOKEN", "")

    if (not base_url or not token) and CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except (OSError, ValueError):
            cfg = {}
        base_url = base_url or cfg.get("moodle_base_url", "")
        token = token or cfg.get("moodle_token", "")

    return base_url, token


def _cmd_fetch(args: argparse.Namespace) -> int:
    base_url, token = _load_credentials()
    if not base_url or not token:
        print(
            "error: Moodle credentials not configured. "
            "Set DEADLINER_MOODLE_URL / DEADLINER_MOODLE_TOKEN "
            f"or create {CONFIG_PATH}",
            file=sys.stderr,
        )
        return 2

    try:
        assignments = moodle_fetcher.fetch_moodle(base_url, token)
    except AuthError as e:
        print(f"error: authentication failed: {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not assignments:
        print("No upcoming deadlines.")
        return 0

    now = datetime.now(timezone.utc)
    local_tz = datetime.now().astimezone().tzinfo
    for assignment in sort_assignments(assignments):
        print(format_assignment(assignment, now, local_tz))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="deadliner",
        description="Fetch and display upcoming deadlines, sorted and timezone-correct.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="fetch deadlines from Moodle and print them")
    fetch_parser.set_defaults(func=_cmd_fetch)

    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
