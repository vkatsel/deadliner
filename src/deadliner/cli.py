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


def _cmd_sync_all(args: argparse.Namespace) -> int:
    """Synchronize both deadlines (Moodle/Classroom) and KSE class schedule to Google Calendar."""
    from deadliner.scheduler import append_sync_log

    append_sync_log("[SYNC-ALL] Started synchronization")
    print("\n" + "=" * 55)
    print("  DEADLINER — Syncing All (Deadlines + KSE Schedule)")
    print("=" * 55 + "\n")

    print("[1/2] Syncing Deadlines...")
    deadlines_code = _cmd_sync(args)

    print("\n[2/2] Syncing KSE Classes...")
    schedule_code = _cmd_schedule_sync(args)

    res_code = max(deadlines_code, schedule_code)
    print("\n" + "=" * 55)
    if res_code == 0:
        print("  All sync tasks completed successfully!")
        append_sync_log("[SYNC-ALL] Completed successfully (code 0)")
    else:
        print("  Sync completed with warnings/errors. Check logs above.")
        append_sync_log(f"[SYNC-ALL] Completed with exit code {res_code}")
    print("=" * 55 + "\n")
    return res_code


def _cmd_cron_enable(args: argparse.Namespace) -> int:
    from deadliner import scheduler

    time_str = getattr(args, "time", "08:00")
    success, msg = scheduler.enable_schedule(time_str)
    if success:
        print(f"\033[92m{msg}\033[0m")
        return 0
    else:
        print(f"\033[91m{msg}\033[0m", file=sys.stderr)
        return 1


def _cmd_cron_disable(args: argparse.Namespace) -> int:
    from deadliner import scheduler

    success, msg = scheduler.disable_schedule()
    if success:
        print(f"\033[92m{msg}\033[0m")
        return 0
    else:
        print(f"\033[91m{msg}\033[0m", file=sys.stderr)
        return 1


def _cmd_cron_status(args: argparse.Namespace) -> int:
    from deadliner import scheduler

    status = scheduler.get_schedule_status()
    print("\n" + "=" * 50)
    print("  Deadliner Daily Auto-Sync Status")
    print("=" * 50)
    if status.get("enabled"):
        print("  Status:     \033[92mENABLED (Active)\033[0m")
        if "next_run" in status:
            print(f"  Next Run:   {status['next_run']}")
        if "start_time" in status and status["start_time"]:
            print(f"  Start Time: {status['start_time']}")
        if "cron_entry" in status:
            print(f"  Crontab:    {status['cron_entry']}")
    else:
        print("  Status:     \033[90mDISABLED (Not scheduled)\033[0m")
        if "details" in status:
            print(f"  Info:       {status['details']}")
    print("=" * 50 + "\n")
    return 0


def _cmd_cron_logs(args: argparse.Namespace | None = None) -> int:
    from deadliner import scheduler

    logs = scheduler.get_recent_logs(max_lines=30)
    print("\n" + "=" * 58)
    print("  Deadliner Auto-Sync Execution Logs (~/.deadliner/sync.log)")
    print("=" * 58)
    if not logs:
        print("  No sync logs recorded yet.")
    else:
        for line in logs:
            if "error" in line.lower() or "failed" in line.lower():
                print(f"  \033[91m{line}\033[0m")
            elif "success" in line.lower():
                print(f"  \033[92m{line}\033[0m")
            else:
                print(f"  {line}")
    print("=" * 58 + "\n")
    return 0



def _cmd_login_google(args: argparse.Namespace) -> int:
    from deadliner.google_auth import find_client_secrets_path, get_token_path, run_oauth_flow
    import shutil

    secrets_path = getattr(args, "client_secrets", None)
    if not secrets_path:
        found = find_client_secrets_path()
        if not found:
            print("\n" + "=" * 65)
            print("  Google OAuth Setup")
            print("=" * 65)
            print("Could not automatically locate client_secret.json.")
            print("1. Download client_secret.json from Google Cloud Console.")
            print("2. Enter the path to your downloaded file below")
            print("   (or drag & drop the file into this terminal):\n")
            try:
                user_in = input("Path to client_secret.json: ").strip().strip('"').strip("'")
            except (KeyboardInterrupt, EOFError):
                print("\nGoogle authentication cancelled.")
                return 130

            if not user_in or not os.path.isfile(user_in):
                print(f"Error: File '{user_in}' does not exist.", file=sys.stderr)
                return 1

            # Save to ~/.deadliner/client_secret.json for permanent discovery
            dest_dir = Path.home() / ".deadliner"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / "client_secret.json"
            try:
                shutil.copyfile(user_in, dest_file)
                print(f"Saved copy to {dest_file}")
                secrets_path = str(dest_file)
            except Exception:
                secrets_path = user_in
        else:
            secrets_path = str(found)

    try:
        run_oauth_flow(secrets_path)
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


def _get_cron_badge() -> str:
    from deadliner import scheduler

    try:
        st = scheduler.get_schedule_status()
        if st.get("enabled"):
            t = st.get("start_time") or ""
            if not t and "next_run" in st:
                t = st["next_run"].split()[-1] if " " in st["next_run"] else st["next_run"]
            label = f"Active @ {t}" if t else "Active"
            return f"\033[92m[{label}]\033[0m"
        return "\033[90m[Disabled]\033[0m"
    except Exception:
        return ""


def _cmd_menu(args: argparse.Namespace | None = None) -> int:
    """Interactive CLI menu for seamless workflow navigation."""
    from deadliner import scheduler

    while True:
        cron_badge = _get_cron_badge()

        print("\n\033[1;36m" + "=" * 58 + "\033[0m")
        print("\033[1;37m  DEADLINER \033[0m— \033[36mAcademic Hub & Calendar Sync\033[0m")
        print("\033[1;36m" + "=" * 58 + "\033[0m")
        print("\033[1;34m[ Deadlines & Coursework ]\033[0m")
        print("  \033[1m1.\033[0m Fetch upcoming deadlines \033[90m(Moodle & Classroom)\033[0m")
        print("  \033[1m2.\033[0m Sync deadlines to Google Calendar \033[91m[Red]\033[0m")
        print("\n\033[1;34m[ KSE University Schedule ]\033[0m")
        print("  \033[1m3.\033[0m Fetch KSE class schedule \033[90m(Next 7 days)\033[0m")
        print("  \033[1m4.\033[0m Sync KSE class schedule to Google Calendar \033[92m[Green]\033[0m")
        print("\n\033[1;34m[ Automation & All-in-One ]\033[0m")
        print("  \033[1m5.\033[0m Sync Everything \033[92m[Deadlines + KSE Schedule]\033[0m")
        print(f"  \033[1m6.\033[0m Auto-Sync Background Scheduler       {cron_badge}")
        print("\n\033[1;34m[ Account & Settings ]\033[0m")
        print("  \033[1m7.\033[0m Login / Configure Services \033[90m(Moodle / Google / KSE)\033[0m")
        print("  \033[1m8.\033[0m Exit")
        print("\033[1;36m" + "=" * 58 + "\033[0m")

        try:
            choice = input("\033[1mSelect an option [1-8]:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return 0

        match choice:
            case "1":
                _cmd_fetch(argparse.Namespace())
            case "2":
                _cmd_sync(argparse.Namespace())
            case "3":
                _cmd_schedule_fetch(argparse.Namespace(from_date=None, till_date=None, days=7))
            case "4":
                _cmd_schedule_sync(argparse.Namespace(from_date=None, till_date=None, days=7))
            case "5":
                _cmd_sync_all(argparse.Namespace())
            case "6":
                st = scheduler.get_schedule_status()
                st_text = (
                    f"\033[92mENABLED (Next: {st.get('next_run', 'N/A')})\033[0m"
                    if st.get("enabled")
                    else "\033[90mDISABLED\033[0m"
                )
                print("\n" + "-" * 55)
                print(f"Daily Auto-Sync Status: {st_text}")
                print("-" * 55)
                print("  a) Enable / Update daily sync time (Default: 08:00)")
                print("  b) Check status and next scheduled run")
                print("  c) View recent auto-sync logs (~/.deadliner/sync.log)")
                print("  d) Disable daily auto-sync")
                print("  e) Back")
                try:
                    cron_choice = input("Choice [a/b/c/d/e]: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    continue
                match cron_choice:
                    case "a":
                        time_in = input("Enter daily sync time (HH:MM in 24h, default 08:00): ").strip() or "08:00"
                        _cmd_cron_enable(argparse.Namespace(time=time_in))
                    case "b":
                        _cmd_cron_status(argparse.Namespace())
                    case "c":
                        _cmd_cron_logs(argparse.Namespace())
                    case "d":
                        _cmd_cron_disable(argparse.Namespace())
                    case "e" | "q" | "back":
                        pass
                    case _:
                        print("Invalid choice.")
            case "7":
                print("\nSelect service to configure:")
                print("  a) Moodle Login")
                print("  b) Google OAuth (Classroom & Calendar)")
                print("  c) KSE Schedule Token")
                print("  d) Back")
                try:
                    sub_choice = input("Choice [a/b/c/d]: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    continue
                match sub_choice:
                    case "a":
                        from deadliner.auth import _cmd_login_moodle

                        _cmd_login_moodle(argparse.Namespace())
                    case "b":
                        _cmd_login_google(argparse.Namespace(client_secrets=None))
                    case "c":
                        from deadliner.kse_auth import _cmd_login_kse

                        _cmd_login_kse(argparse.Namespace())
                    case "d" | "q" | "back":
                        pass
                    case _:
                        print("Invalid choice.")
            case "8" | "q" | "exit":
                print("Goodbye!")
                return 0
            case _:
                print("Invalid selection. Please choose 1-8.")


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

        # deadliner sync-all
        sync_all_parser = subparsers.add_parser(
            "sync-all", help="push both deadlines and KSE schedule to Google Calendar"
        )
        sync_all_parser.set_defaults(func=_cmd_sync_all)

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

        # deadliner cron [enable|disable|status|logs]
        cron_parser = subparsers.add_parser("cron", help="manage daily 24h background auto-sync")
        cron_subparsers = cron_parser.add_subparsers(dest="cron_cmd", required=True)

        cron_enable_parser = cron_subparsers.add_parser("enable", help="enable daily auto-sync")
        cron_enable_parser.add_argument("--time", default="08:00", help="Time of day (HH:MM in 24h, default: 08:00)")
        cron_enable_parser.set_defaults(func=_cmd_cron_enable)

        cron_disable_parser = cron_subparsers.add_parser("disable", help="disable daily auto-sync")
        cron_disable_parser.set_defaults(func=_cmd_cron_disable)

        cron_status_parser = cron_subparsers.add_parser("status", help="check daily auto-sync status")
        cron_status_parser.set_defaults(func=_cmd_cron_status)

        cron_logs_parser = cron_subparsers.add_parser("logs", help="view recent auto-sync logs")
        cron_logs_parser.set_defaults(func=_cmd_cron_logs)

        # deadliner logs (shortcut for deadliner cron logs)
        logs_parser = subparsers.add_parser("logs", help="view recent auto-sync logs (~/.deadliner/sync.log)")
        logs_parser.set_defaults(func=_cmd_cron_logs)

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
