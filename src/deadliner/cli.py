import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys

from deadliner import moodle_fetcher
from deadliner.formatter import (
    format_assignment,
    format_schedule_event,
    sort_assignments,
    sort_schedule_events,
)
from deadliner.models import AuthError

CONFIG_PATH = Path.home() / ".deadliner.json"


def _load_credentials() -> tuple[str, str, str, str]:
    """Read Moodle, Google, and KSE credentials from env vars, falling back to ~/.deadliner.json.

    Env vars:
      DEADLINER_MOODLE_URL / DEADLINER_MOODLE_TOKEN / DEADLINER_GOOGLE_TOKEN / DEADLINER_KSE_TOKEN.

    Returns:
      (moodle_base_url, moodle_token, google_access_token, kse_token)
    """
    base_url = os.environ.get("DEADLINER_MOODLE_URL", "")
    token = os.environ.get("DEADLINER_MOODLE_TOKEN", "")
    g_token = os.environ.get("DEADLINER_GOOGLE_TOKEN", "")
    kse_token = os.environ.get("DEADLINER_KSE_TOKEN", "")

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
            g_token = creds.token

    if not kse_token:
        from deadliner.kse_auth import get_valid_kse_token

        kse_token = get_valid_kse_token()

    return base_url, token, g_token, kse_token



def _collect_assignments(base_url: str, token: str, g_token: str) -> tuple[list, list[str]]:
    """Fetch deadlines from every configured source, tolerating per-source failures."""
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
    creds = _load_credentials()
    base_url, token, g_token = creds[0], creds[1], creds[2]
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

    creds = _load_credentials()
    base_url, token, g_token = creds[0], creds[1], creds[2]
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
    print("Google Calendar Sync Summary (Deadlines)")
    print("=" * 45)
    print(f"Created:   {created}")
    print(f"Updated:   {updated}")
    print(f"Skipped:   {skipped} (duplicates)")
    print("=" * 45 + "\n")
    return 0


def _resolve_date_range(args: argparse.Namespace) -> tuple[str, str]:
    today = date.today()
    from_date = getattr(args, "from_date", None) or today.isoformat()

    days = getattr(args, "days", 7)
    if getattr(args, "till_date", None):
        till_date = args.till_date
    else:
        start_d = date.fromisoformat(from_date) if isinstance(from_date, str) else from_date
        till_date = (start_d + timedelta(days=days)).isoformat()

    return str(from_date), str(till_date)


def _cmd_schedule_fetch(args: argparse.Namespace) -> int:
    from deadliner import kse_fetcher

    creds = _load_credentials()
    kse_token = creds[3] if len(creds) > 3 else ""
    from_str, till_str = _resolve_date_range(args)

    try:
        events = kse_fetcher.fetch_kse_schedule(token=kse_token, from_date=from_str, till_date=till_str)
    except AuthError as e:
        print(f"\033[91merror: KSE authentication failed: {e}\033[0m", file=sys.stderr)
        print("Run `deadliner login kse` to update your token.", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"\033[91merror: KSE connection failed: {e}\033[0m", file=sys.stderr)
        return 1

    if not events:
        print(f"No KSE classes found for period {from_str} to {till_str}.")
        return 0

    local_tz = datetime.now().astimezone().tzinfo
    print(f"\nUpcoming KSE Schedule ({from_str} to {till_str}):")
    print("-" * 65)
    for event in sort_schedule_events(events):
        print(format_schedule_event(event, local_tz))
    print("-" * 65 + "\n")
    return 0


def _cmd_schedule_sync(args: argparse.Namespace) -> int:
    from deadliner import calendar_sync, kse_fetcher

    creds = _load_credentials()
    g_token = creds[2] if len(creds) > 2 else ""
    kse_token = creds[3] if len(creds) > 3 else ""
    if not g_token:
        print(
            "error: Google credentials required for calendar sync. Run `deadliner login google` first.",
            file=sys.stderr,
        )
        return 2

    from_str, till_str = _resolve_date_range(args)

    try:
        print(f"Fetching KSE classes ({from_str} to {till_str})...")
        events = kse_fetcher.fetch_kse_schedule(token=kse_token, from_date=from_str, till_date=till_str)
    except AuthError as e:
        print(f"\033[91merror: KSE authentication failed: {e}\033[0m", file=sys.stderr)
        print("Run `deadliner login kse` to update your token.", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"\033[91merror: KSE connection failed: {e}\033[0m", file=sys.stderr)
        return 1

    if not events:
        print("No KSE classes found to sync.")
        return 0

    try:
        print(f"Syncing {len(events)} classes to Google Calendar...")
        sync_result = calendar_sync.sync_schedule_to_calendar(
            sort_schedule_events(events), g_token, return_details=True
        )
        created, updated, skipped = sync_result[0], sync_result[1], sync_result[2]
        statuses = sync_result[3] if len(sync_result) > 3 else []
    except AuthError as e:
        print(f"\033[91merror: Google Calendar authentication failed: {e}\033[0m", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"\033[91merror: {e}\033[0m", file=sys.stderr)
        return 1

    local_tz = datetime.now().astimezone().tzinfo
    print("-" * 65)
    for event, status in statuses:
        start_local = event.start_utc.astimezone(local_tz).strftime("%a %d %b %H:%M")
        if status == "created":
            tag = "\033[92m[+ Added to Calendar]\033[0m"
        elif status == "updated":
            tag = "\033[93m[~ Updated in Calendar]\033[0m"
        else:
            tag = "\033[90m[= Already in Calendar]\033[0m"
        print(f"{tag} [{event.discipline}] {event.course_name} ({start_local})")
    print("-" * 65)

    print("\n" + "=" * 45)
    print("Google Calendar Sync Summary (KSE Schedule)")
    print("=" * 45)
    print(f"Created:   {created}")
    print(f"Updated:   {updated}")
    print(f"Skipped:   {skipped} (already up-to-date)")
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
    except (KeyboardInterrupt, EOFError):
        print("\nGoogle authentication cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Google authentication failed: {e}", file=sys.stderr)
        return 1


def _cmd_menu(args: argparse.Namespace | None = None) -> int:
    """Interactive CLI menu for seamless workflow navigation."""
    while True:
        print("\n" + "=" * 55)
        print("  DEADLINER — Academic Hub & Calendar Sync")
        print("=" * 55)
        print("1. Fetch upcoming deadlines (Moodle & Classroom)")
        print("2. Sync deadlines to Google Calendar (Red events)")
        print("3. Fetch KSE class schedule (Next 7 days)")
        print("4. Sync KSE class schedule to Google Calendar (Green events)")
        print("5. Login / Configure Services (Moodle / Google / KSE)")
        print("6. Exit")
        print("=" * 55)

        try:
            choice = input("Select an option [1-6]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return 0

        if choice == "1":
            _cmd_fetch(argparse.Namespace())
        elif choice == "2":
            _cmd_sync(argparse.Namespace())
        elif choice == "3":
            _cmd_schedule_fetch(argparse.Namespace(from_date=None, till_date=None, days=7))
        elif choice == "4":
            _cmd_schedule_sync(argparse.Namespace(from_date=None, till_date=None, days=7))
        elif choice == "5":
            print("\nSelect service to configure:")
            print("  a) Moodle Login")
            print("  b) Google OAuth (Classroom & Calendar)")
            print("  c) KSE Schedule Token")
            print("  d) Back")
            try:
                sub_choice = input("Choice [a/b/c/d]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                continue
            if sub_choice == "a":
                from deadliner.auth import _cmd_login_moodle

                _cmd_login_moodle(argparse.Namespace())
            elif sub_choice == "b":
                _cmd_login_google(argparse.Namespace(client_secrets=None))
            elif sub_choice == "c":
                from deadliner.kse_auth import _cmd_login_kse

                _cmd_login_kse(argparse.Namespace())
        elif choice in ("6", "q", "exit"):
            print("Goodbye!")
            return 0
        else:
            print("Invalid selection. Please choose 1-6.")


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    try:
        # If no arguments given, open the interactive menu
        if not argv:
            sys.exit(_cmd_menu())

        parser = argparse.ArgumentParser(
            prog="deadliner",
            description="Aggregate academic deadlines and KSE classes, sorted and synced to Google Calendar.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        # deadliner fetch
        fetch_parser = subparsers.add_parser("fetch", help="fetch deadlines from Moodle & Classroom")
        fetch_parser.set_defaults(func=_cmd_fetch)

        # deadliner sync
        sync_parser = subparsers.add_parser("sync", help="push deadlines to Google Calendar as red events")
        sync_parser.set_defaults(func=_cmd_sync)

        # deadliner menu
        menu_parser = subparsers.add_parser("menu", help="open interactive workflow menu")
        menu_parser.set_defaults(func=_cmd_menu)

        # deadliner schedule [fetch|sync]
        schedule_parser = subparsers.add_parser("schedule", help="manage KSE class schedule")
        schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_cmd", required=True)

        sched_fetch_parser = schedule_subparsers.add_parser("fetch", help="fetch KSE class schedule")
        sched_fetch_parser.add_argument("--from", dest="from_date", default=None, help="Start date (YYYY-MM-DD)")
        sched_fetch_parser.add_argument("--till", dest="till_date", default=None, help="End date (YYYY-MM-DD)")
        sched_fetch_parser.add_argument("--days", type=int, default=7, help="Number of days to fetch (default: 7)")
        sched_fetch_parser.set_defaults(func=_cmd_schedule_fetch)

        sched_sync_parser = schedule_subparsers.add_parser("sync", help="sync KSE class schedule to Google Calendar")
        sched_sync_parser.add_argument("--from", dest="from_date", default=None, help="Start date (YYYY-MM-DD)")
        sched_sync_parser.add_argument("--till", dest="till_date", default=None, help="End date (YYYY-MM-DD)")
        sched_sync_parser.add_argument("--days", type=int, default=7, help="Number of days to sync (default: 7)")
        sched_sync_parser.set_defaults(func=_cmd_schedule_sync)

        # deadliner login [moodle|google|kse]
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

        from deadliner.kse_auth import _cmd_login_kse

        kse_login = login_subparsers.add_parser("kse", help="log in to KSE schedule")
        kse_login.set_defaults(func=_cmd_login_kse)

        args = parser.parse_args(argv)
        sys.exit(args.func(args))
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)



if __name__ == "__main__":
    main()
