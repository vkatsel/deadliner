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


def _load_credentials() -> tuple[str, str, str]:
    """Read Moodle and Google credentials from env vars, falling back to ~/.deadliner.json.

    Env vars: DEADLINER_MOODLE_URL / DEADLINER_MOODLE_TOKEN / DEADLINER_GOOGLE_TOKEN.
    Config file shape: {"moodle_base_url": "...", "moodle_token": "...", "google_access_token": "..."}.

    For Google, also checks for stored OAuth credentials (from ``deadliner login google``)
    and refreshes them automatically if expired.
    """
    base_url = os.environ.get("DEADLINER_MOODLE_URL", "")
    token = os.environ.get("DEADLINER_MOODLE_TOKEN", "")
    g_token = os.environ.get("DEADLINER_GOOGLE_TOKEN", "")

    if (not base_url or not token or not g_token) and CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except (OSError, ValueError):
            cfg = {}
        base_url = base_url or cfg.get("moodle_base_url", "")
        token = token or cfg.get("moodle_token", "")
        g_token = g_token or cfg.get("google_access_token", "")

    # If no static Google token, try stored OAuth credentials (refresh-on-use)
    if not g_token:
        from deadliner.google_auth import load_google_credentials

        creds = load_google_credentials()
        if creds:
            g_token = creds.token  # raw access token string for backward compat

    return base_url, token, g_token


def _collect_assignments(base_url: str, token: str, g_token: str) -> tuple[list, list[str]]:
    """Fetch from every configured source, tolerating per-source failures.

    A source that fails (auth or network) contributes a warning instead of
    aborting the run — the other source still gets fetched (fault tolerance).
    Returns (assignments, warnings).
    """
    from deadliner import classroom_fetcher

    warnings = []
    assignments = []

    if base_url and token:
        try:
            assignments.extend(moodle_fetcher.fetch_moodle(base_url, token))
        except AuthError as e:
            warnings.append(f"warning: moodle authentication failed: {e}")
        except ConnectionError as e:
            warnings.append(f"warning: moodle connection: {e}")

    if g_token:
        try:
            assignments.extend(classroom_fetcher.fetch_classroom({"access_token": g_token}))
        except AuthError as e:
            warnings.append(f"warning: classroom authentication failed: {e}")
        except ConnectionError as e:
            warnings.append(f"warning: classroom connection: {e}")

    return assignments, warnings


def _cmd_fetch(args: argparse.Namespace) -> int:
    base_url, token, g_token = _load_credentials()
    if not (base_url and token) and not g_token:
        print(
            "error: No credentials configured. "
            "Set DEADLINER_MOODLE_URL / DEADLINER_MOODLE_TOKEN or google_access_token "
            f"or create {CONFIG_PATH}",
            file=sys.stderr,
        )
        return 2

    assignments, warnings = _collect_assignments(base_url, token, g_token)

    if not assignments:
        print("No upcoming deadlines.")
        if warnings:
            print("\n" + "\033[93m" + "\n".join(warnings) + "\033[0m", file=sys.stderr)
        return 0

    now = datetime.now(timezone.utc)
    local_tz = datetime.now().astimezone().tzinfo
    for assignment in sort_assignments(assignments):
        print(format_assignment(assignment, now, local_tz))

    if warnings:
        sys.stdout.flush()
        print("\n" + "\033[93m" + "\n".join(warnings) + "\033[0m", file=sys.stderr)

    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    from deadliner import calendar_sync

    base_url, token, g_token = _load_credentials()
    if not g_token:
        print(
            "error: Google credentials required for calendar sync. Run `deadliner login google` first.",
            file=sys.stderr,
        )
        return 2

    assignments, warnings = _collect_assignments(base_url, token, g_token)

    for w in warnings:
        print(f"\033[93m{w}\033[0m", file=sys.stderr)

    if not assignments:
        print("No upcoming deadlines to sync.")
        return 0

    try:
        print("Syncing to Google Calendar...")
        created, updated, skipped = calendar_sync.sync_to_calendar(sort_assignments(assignments), g_token)
    except AuthError as e:
        print(f"\033[91merror: calendar authentication failed: {e}\033[0m", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"\033[91merror: {e}\033[0m", file=sys.stderr)
        return 1

    print("\n" + "=" * 45)
    print("Google Calendar Sync Summary")
    print("=" * 45)
    print(f"Created:   {created}")
    print(f"Updated:   {updated}")
    print(f"Skipped:   {skipped} (duplicates)")
    print("=" * 45 + "\n")
    return 0


def _cmd_login_google(args: argparse.Namespace) -> int:
    from deadliner.google_auth import get_token_path, run_oauth_flow

    try:
        run_oauth_flow(args.client_secrets)
        print(f"Google authentication successful. Token saved to {get_token_path()}")
        return 0
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Google authentication failed: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="deadliner",
        description="Fetch and display upcoming deadlines, sorted and timezone-correct.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="fetch deadlines from Moodle and print them")
    fetch_parser.set_defaults(func=_cmd_fetch)

    sync_parser = subparsers.add_parser("sync", help="push all fetched deadlines to Google Calendar as red events")
    sync_parser.set_defaults(func=_cmd_sync)

    login_parser = subparsers.add_parser("login", help="log in to a service")
    login_subparsers = login_parser.add_subparsers(dest="service", required=True)

    from deadliner.auth import _cmd_login_moodle

    moodle_login = login_subparsers.add_parser("moodle", help="log in to Moodle")
    moodle_login.set_defaults(func=_cmd_login_moodle)

    google_login = login_subparsers.add_parser("google", help="authenticate with Google (Classroom + Calendar)")
    google_login.add_argument(
        "--client-secrets",
        default=None,
        help="path to client_secret.json from Google Cloud Console (default: ./client_secret.json)",
    )
    google_login.set_defaults(func=_cmd_login_google)

    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
