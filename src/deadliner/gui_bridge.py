"""Backend API bridge exposed to the PyWebView desktop interface via `window.pywebview.api`."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import wraps
import re
import subprocess
import sys
from typing import Callable, TypeVar
import webbrowser

from deadliner import auth, calendar_sync, cli, kse_auth, kse_fetcher, path_util, scheduler
from deadliner.formatter import sort_assignments, sort_schedule_events
from deadliner.models import Assignment, AuthError, ScheduleEvent
from deadliner.storage import DataStore, InMemoryStore, SyncRecord

F = TypeVar("F", bound=Callable[..., dict])

TIME_24H_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def classify_error(exc_or_msg: Exception | str, source: str = "") -> dict:
    """Produce a structured error dictionary with error_code, hint, and suggested action."""
    raw_msg = str(exc_or_msg).strip() or "Unexpected error occurred."
    lower = raw_msg.lower()

    if isinstance(exc_or_msg, AuthError) or "auth" in lower or "401" in lower or "token" in lower or "login" in lower:
        code = "AUTH_ERROR"
        if "moodle" in lower or source == "moodle":
            hint = (
                "Verify your Moodle username and local password (not Google SSO password) "
                "in the Connections tab."
            )
        elif "kse" in lower or source == "kse":
            hint = (
                "Your KSE Schedule session expired. Open Connections -> KSE Schedule and "
                "click 'Sign in via KSE WebView'."
            )
        elif "google" in lower or "calendar" in lower or "classroom" in lower or source == "google":
            hint = (
                "Your Google OAuth token is missing or expired. Re-authenticate with Google "
                "in the Connections tab."
            )
        else:
            hint = "Check your service credentials in the Connections tab and sign in again."
        return {
            "ok": False,
            "error": raw_msg,
            "error_code": code,
            "hint": hint,
            "action_view": "connections",
        }

    if (
        isinstance(exc_or_msg, ConnectionError)
        or "connect" in lower
        or "timeout" in lower
        or "timed out" in lower
        or "network" in lower
    ):
        return {
            "ok": False,
            "error": raw_msg,
            "error_code": "NETWORK_ERROR",
            "hint": "Check your internet connection or verify if the university portal is reachable.",
            "action_view": None,
        }

    return {
        "ok": False,
        "error": raw_msg,
        "error_code": "OPERATION_ERROR",
        "hint": "",
        "action_view": None,
    }


def safe_api_method(func: F) -> F:
    """Boundary decorator ensuring JS callers always receive a structured dict on unexpected errors."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> dict:
        try:
            return func(*args, **kwargs)
        except (AuthError, ConnectionError) as e:
            return classify_error(e)
        except Exception as e:
            return {
                "ok": False,
                "error": f"Internal error in {func.__name__}: {e}",
                "error_code": "INTERNAL_ERROR",
                "hint": "Try refreshing the workspace or check Sync & Logs for details.",
                "action_view": None,
            }

    return wrapper  # type: ignore[return-value]


def serialize_assignment(assignment: Assignment, now: datetime | None = None, local_tz=None) -> dict:
    """Convert an Assignment dataclass into a UI-ready dictionary with urgency semantics."""
    if now is None:
        now = datetime.now(timezone.utc)
    if local_tz is None:
        local_tz = datetime.now().astimezone().tzinfo

    local_due = assignment.due_utc.astimezone(local_tz)
    remaining_sec = int((assignment.due_utc - now).total_seconds())
    is_midnight_cutoff = local_due.hour == 0 and local_due.minute == 0

    if assignment.is_submitted:
        urgency = "submitted"
        countdown_en = "Submitted"
        countdown_ua = "Здано"
    elif remaining_sec < 0:
        abs_sec = abs(remaining_sec)
        days = abs_sec // 86400
        hours = (abs_sec % 86400) // 3600
        urgency = "overdue"
        countdown_en = f"-{days}d {hours}h" if days > 0 else f"-{hours}h"
        countdown_ua = f"-{days}д {hours}г" if days > 0 else f"-{hours}г"
    else:
        days = remaining_sec // 86400
        hours = (remaining_sec % 86400) // 3600
        minutes = (remaining_sec % 3600) // 60
        if remaining_sec <= 86400:
            urgency = "critical"
            countdown_en = f"{hours}h {minutes}m"
            countdown_ua = f"{hours}г {minutes}хв"
        elif remaining_sec <= 3 * 86400:
            urgency = "soon"
            countdown_en = f"{days}d {hours}h"
            countdown_ua = f"{days}д {hours}г"
        else:
            urgency = "normal"
            countdown_en = f"{days}d {hours}h"
            countdown_ua = f"{days}д {hours}г"

    return {
        "platform": assignment.platform,
        "course": assignment.course_shortname or assignment.platform.capitalize(),
        "title": assignment.title,
        "due_utc": assignment.due_utc.isoformat(),
        "due_date_str": local_due.strftime("%Y-%m-%d"),
        "due_day_str": local_due.strftime("%a, %d %b"),
        "due_time_str": local_due.strftime("%H:%M"),
        "remaining_seconds": remaining_sec,
        "countdown_en": countdown_en,
        "countdown_ua": countdown_ua,
        "urgency": urgency,
        "is_submitted": bool(assignment.is_submitted),
        "is_midnight_cutoff": is_midnight_cutoff,
        "url": assignment.url or "",
    }


def serialize_schedule_event(event: ScheduleEvent, local_tz=None) -> dict:
    """Convert a ScheduleEvent dataclass into a UI-ready dictionary."""
    if local_tz is None:
        local_tz = datetime.now().astimezone().tzinfo

    local_start = event.start_utc.astimezone(local_tz)
    local_end = event.end_utc.astimezone(local_tz)

    if event.event_type == "lecture":
        semantic_color = "sage"
        type_label_en = "Lecture"
        type_label_ua = "Лекція"
    elif event.event_type == "practice":
        semantic_color = "peacock"
        type_label_en = "Practice"
        type_label_ua = "Практика"
    else:
        semantic_color = "neutral"
        type_label_en = (event.event_type or "Class").capitalize()
        type_label_ua = (event.event_type or "Заняття").capitalize()

    return {
        "event_id": event.event_id,
        "discipline": event.discipline,
        "course_name": event.course_name,
        "event_type": event.event_type,
        "semantic_color": semantic_color,
        "type_label_en": type_label_en,
        "type_label_ua": type_label_ua,
        "subgroup": event.subgroup,
        "date": event.date,
        "day_header_en": local_start.strftime("%A, %d %b %Y"),
        "day_short_en": local_start.strftime("%a %d %b"),
        "period": event.period,
        "start_time": local_start.strftime("%H:%M"),
        "end_time": local_end.strftime("%H:%M"),
        "time_range": f"{local_start.strftime('%H:%M')}–{local_end.strftime('%H:%M')}",
        "start_utc": event.start_utc.isoformat(),
        "end_utc": event.end_utc.isoformat(),
        "room": event.room,
        "shelter": event.shelter,
        "teacher": event.teacher,
        "zoom_url": event.zoom_url,
        "comment": event.comment,
        "is_shifted": bool(event.is_shifted),
    }


class DeadlinerGuiApi:
    """JS-accessible API surface for Deadliner Desktop Workspace."""

    def __init__(self, store: DataStore | None = None) -> None:
        self._store: DataStore = store if store is not None else InMemoryStore()

    @property
    def store(self) -> DataStore:
        return self._store

    @safe_api_method
    def get_initial_state(self) -> dict:
        """Return current connection states, scheduler settings, and cached data snapshot."""
        base_url, moodle_token, g_token, kse_token = cli._load_credentials()
        raw_kse_tok, raw_kse_ref, _ = kse_auth.load_kse_credentials()
        from deadliner.google_auth import find_client_secrets_path, get_token_path

        cron_status = scheduler.get_schedule_status()
        classroom_enabled = cli.is_classroom_sync_enabled()
        on_path = path_util.is_on_path()

        now = datetime.now(timezone.utc)
        local_tz = datetime.now().astimezone().tzinfo
        cached_deadlines = [
            serialize_assignment(a, now, local_tz)
            for a in sort_assignments(self._store.get_deadlines())
        ]
        cached_schedule = [
            serialize_schedule_event(e, local_tz)
            for e in sort_schedule_events(self._store.get_schedule())
        ]

        return {
            "ok": True,
            "version": "2.0.0",
            "storage_engine": self._store.engine_name,
            "connections": {
                "moodle": {
                    "connected": bool(base_url and moodle_token),
                    "base_url": base_url or auth.DEFAULT_MOODLE_URL,
                },
                "google": {
                    "connected": bool(g_token),
                    "has_client_secrets": find_client_secrets_path() is not None,
                    "token_path": str(get_token_path()),
                    "classroom_enabled": classroom_enabled,
                },
                "kse": {
                    "connected": bool(kse_token),
                    "has_refresh_token": bool(raw_kse_ref),
                    "has_saved_token": bool(raw_kse_tok),
                },
            },
            "scheduler": {
                "enabled": bool(cron_status.get("enabled")),
                "start_time": cron_status.get("start_time") or "08:00",
                "next_run": cron_status.get("next_run") or "",
                "details": cron_status.get("details") or "",
            },
            "system": {
                "on_path": on_path,
                "platform": sys.platform,
                "config_path": str(cli.CONFIG_PATH),
            },
            "deadlines": cached_deadlines,
            "schedule": cached_schedule,
            "analytics": self._store.get_analytics_snapshot(),
        }

    @safe_api_method
    def fetch_deadlines(self) -> dict:
        """Fetch deadlines from Moodle and Google Classroom, update store, and return serialized items."""
        base_url, token, g_token, _ = cli._load_credentials()
        if not (base_url and token) and not g_token:
            return {
                "ok": False,
                "error": "No deadline sources are connected yet.",
                "error_code": "CONFIG_MISSING",
                "hint": "Connect your Moodle account or Google Classroom in the Connections tab to load assignments.",
                "action_view": "connections",
                "warnings": [],
                "deadlines": [],
                "analytics": self._store.get_analytics_snapshot(),
            }

        assignments, warnings = cli._collect_assignments(base_url, token, g_token)

        # If every configured source failed with a warning and returned 0 assignments, surface as actionable error
        if not assignments and warnings:
            joined = " | ".join(warnings)
            err_info = classify_error(joined)
            err_info["warnings"] = warnings
            err_info["deadlines"] = []
            err_info["analytics"] = self._store.get_analytics_snapshot()
            return err_info

        sorted_items = sort_assignments(assignments)
        self._store.save_deadlines(sorted_items)

        now = datetime.now(timezone.utc)
        local_tz = datetime.now().astimezone().tzinfo
        serialized = [serialize_assignment(a, now, local_tz) for a in sorted_items]

        return {
            "ok": True,
            "warnings": warnings,
            "deadlines": serialized,
            "fetched_at": now.astimezone(local_tz).strftime("%H:%M:%S"),
            "analytics": self._store.get_analytics_snapshot(),
        }

    @safe_api_method
    def fetch_schedule(
        self, days: int = 7, from_date: str | None = None, till_date: str | None = None
    ) -> dict:
        """Fetch KSE schedule for the requested period, update store, and return serialized events."""
        _, _, _, kse_token = cli._load_credentials()
        if not kse_token:
            return {
                "ok": False,
                "error": "KSE Schedule is not connected or your session has expired.",
                "error_code": "AUTH_ERROR",
                "hint": "Open Connections -> KSE Schedule to sign in via the native WebView window.",
                "action_view": "connections",
                "schedule": [],
                "analytics": self._store.get_analytics_snapshot(),
            }

        today = date.today()
        start_str = from_date or today.isoformat()
        if till_date:
            end_str = till_date
        else:
            start_d = date.fromisoformat(start_str)
            end_str = (start_d + timedelta(days=max(1, int(days)))).isoformat()

        try:
            events = kse_fetcher.fetch_kse_schedule(
                token=kse_token, from_date=start_str, till_date=end_str
            )
        except (AuthError, ConnectionError) as e:
            err = classify_error(e, source="kse")
            err["schedule"] = []
            err["period"] = {"from": start_str, "till": end_str}
            err["analytics"] = self._store.get_analytics_snapshot()
            return err

        sorted_events = sort_schedule_events(events)
        self._store.save_schedule(sorted_events)

        now = datetime.now(timezone.utc)
        local_tz = datetime.now().astimezone().tzinfo
        serialized = [serialize_schedule_event(e, local_tz) for e in sorted_events]

        return {
            "ok": True,
            "schedule": serialized,
            "period": {"from": start_str, "till": end_str, "days": int(days)},
            "fetched_at": now.astimezone(local_tz).strftime("%H:%M:%S"),
            "analytics": self._store.get_analytics_snapshot(),
        }

    @safe_api_method
    def sync_deadlines(self) -> dict:
        """Synchronize deadlines to Google Calendar and return detailed summary."""
        base_url, token, g_token, _ = cli._load_credentials()
        if not g_token:
            msg = "Google Calendar authentication is required before syncing deadlines."
            cli._report_sync_error("Deadlines Sync Failed", msg)
            return {
                "ok": False,
                "error": msg,
                "error_code": "AUTH_ERROR",
                "hint": "Go to the Connections tab and sign in with your Google account.",
                "action_view": "connections",
            }

        assignments, warnings = cli._collect_assignments(base_url, token, g_token)
        sorted_items = sort_assignments(assignments)
        self._store.save_deadlines(sorted_items)

        if warnings:
            cli._report_sync_error("Deadlines Sync Warning", "\n".join(warnings))

        if not sorted_items:
            now = datetime.now(timezone.utc)
            local_tz = datetime.now().astimezone().tzinfo
            return {
                "ok": True,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "warnings": warnings,
                "details": [],
                "deadlines": [],
                "synced_at": now.astimezone(local_tz).strftime("%H:%M:%S"),
                "analytics": self._store.get_analytics_snapshot(),
            }

        try:
            sync_result = calendar_sync.sync_to_calendar(
                sorted_items,
                g_token,
                return_details=True,
            )
            created, updated, skipped = sync_result[0], sync_result[1], sync_result[2]
            statuses = sync_result[3] if len(sync_result) > 3 else []
        except (AuthError, ConnectionError) as e:
            cli._report_sync_error("Deadlines Sync Failed", str(e))
            err = classify_error(e, source="google")
            err["warnings"] = warnings
            return err

        now = datetime.now(timezone.utc)
        local_tz = datetime.now().astimezone().tzinfo
        details = []
        for assignment, status, old_due in statuses:
            due_local = assignment.due_utc.astimezone(local_tz).strftime("%a %d %b %H:%M")
            old_local = old_due.astimezone(local_tz).strftime("%a %d %b %H:%M") if old_due else None
            if status == "submitted":
                scheduler.append_sync_log(f"[SYNC] Marked as submitted: {assignment.title}")
            elif status == "rescheduled" and old_local:
                scheduler.append_sync_log(
                    f"[SYNC] Rescheduled deadline: {assignment.title} ({old_local} -> {due_local})"
                )
            details.append(
                {
                    "course": assignment.course_shortname or assignment.platform,
                    "title": assignment.title,
                    "status": status,
                    "due_local": due_local,
                    "old_due_local": old_local,
                }
            )

        self._store.record_sync(
            SyncRecord(
                timestamp_utc=now,
                target="deadlines",
                created=created,
                updated=updated,
                skipped=skipped,
                warnings=warnings,
                success=True,
            )
        )

        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "warnings": warnings,
            "details": details,
            "deadlines": [serialize_assignment(a, now, local_tz) for a in sorted_items],
            "synced_at": now.astimezone(local_tz).strftime("%H:%M:%S"),
            "analytics": self._store.get_analytics_snapshot(),
        }

    @safe_api_method
    def sync_schedule(self, days: int = 7) -> dict:
        """Synchronize KSE schedule to Google Calendar and return detailed summary."""
        _, _, g_token, kse_token = cli._load_credentials()
        if not g_token:
            msg = "Google Calendar authentication is required before syncing your class schedule."
            cli._report_sync_error("KSE Schedule Sync Failed", msg)
            return {
                "ok": False,
                "error": msg,
                "error_code": "AUTH_ERROR",
                "hint": "Open the Connections tab and sign in with Google first.",
                "action_view": "connections",
            }

        if not kse_token:
            msg = "KSE Schedule credentials are required to sync classes."
            cli._report_sync_error("KSE Schedule Sync Failed", msg)
            return {
                "ok": False,
                "error": msg,
                "error_code": "AUTH_ERROR",
                "hint": "Open Connections -> KSE Schedule and sign in.",
                "action_view": "connections",
            }

        today = date.today()
        from_str = today.isoformat()
        till_str = (today + timedelta(days=max(1, int(days)))).isoformat()

        try:
            events = kse_fetcher.fetch_kse_schedule(
                token=kse_token, from_date=from_str, till_date=till_str
            )
        except (AuthError, ConnectionError) as e:
            cli._report_sync_error("KSE Schedule Sync Failed", str(e))
            return classify_error(e, source="kse")

        sorted_events = sort_schedule_events(events)
        self._store.save_schedule(sorted_events)

        now = datetime.now(timezone.utc)
        local_tz = datetime.now().astimezone().tzinfo

        if not sorted_events:
            return {
                "ok": True,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "deleted": 0,
                "details": [],
                "schedule": [],
                "synced_at": now.astimezone(local_tz).strftime("%H:%M:%S"),
                "analytics": self._store.get_analytics_snapshot(),
            }

        time_min_utc = (
            datetime.fromisoformat(from_str)
            .replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=kse_fetcher.KYIV_TZ)
            .astimezone(timezone.utc)
        )
        time_max_utc = (
            datetime.fromisoformat(till_str)
            .replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=kse_fetcher.KYIV_TZ)
            .astimezone(timezone.utc)
        )

        try:
            sync_result = calendar_sync.sync_schedule_to_calendar(
                sorted_events,
                g_token,
                time_min=time_min_utc,
                time_max=time_max_utc,
                return_details=True,
            )
            created, updated, skipped, deleted = (
                sync_result[0],
                sync_result[1],
                sync_result[2],
                sync_result[3],
            )
            statuses = sync_result[4] if len(sync_result) > 4 else []
        except (AuthError, ConnectionError) as e:
            cli._report_sync_error("KSE Schedule Sync Failed", str(e))
            return classify_error(e, source="google")

        details = []
        for item, status in statuses:
            if status == "deleted":
                summary = item if isinstance(item, str) else getattr(item, "course_name", "Cancelled Class")
                details.append({"course": "KSE", "title": summary, "status": "deleted", "time": "removed"})
            else:
                start_local = item.start_utc.astimezone(local_tz).strftime("%a %d %b %H:%M")
                details.append(
                    {
                        "course": item.discipline or "KSE",
                        "title": item.course_name,
                        "status": status,
                        "time": start_local,
                    }
                )

        self._store.record_sync(
            SyncRecord(
                timestamp_utc=now,
                target="schedule",
                created=created,
                updated=updated,
                skipped=skipped,
                deleted=deleted,
                success=True,
            )
        )

        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "deleted": deleted,
            "details": details,
            "schedule": [serialize_schedule_event(e, local_tz) for e in sorted_events],
            "synced_at": now.astimezone(local_tz).strftime("%H:%M:%S"),
            "analytics": self._store.get_analytics_snapshot(),
        }

    @safe_api_method
    def sync_all(self, days: int = 7) -> dict:
        """Run both deadlines sync and KSE schedule sync."""
        scheduler.append_sync_log("[SYNC-ALL] Started synchronization from Desktop GUI")
        d_res = self.sync_deadlines()
        s_res = self.sync_schedule(days=days)

        ok = bool(d_res.get("ok") and s_res.get("ok"))
        if ok:
            scheduler.append_sync_log("[SYNC-ALL] Completed successfully (code 0)")
        else:
            scheduler.append_sync_log("[SYNC-ALL] Completed with warnings/errors")

        primary_err = None
        if not ok:
            primary_err = d_res if not d_res.get("ok") else s_res

        return {
            "ok": ok,
            "error": primary_err.get("error") if primary_err else None,
            "hint": primary_err.get("hint") if primary_err else None,
            "action_view": primary_err.get("action_view") if primary_err else None,
            "deadlines_sync": d_res,
            "schedule_sync": s_res,
            "analytics": self._store.get_analytics_snapshot(),
        }

    @safe_api_method
    def get_logs(self, max_lines: int = 50) -> dict:
        """Return recent auto-sync and execution logs with severity tags."""
        lines = scheduler.get_recent_logs(max_lines=max_lines)
        entries = []
        for line in lines:
            lower = line.lower()
            if "error" in lower or "failed" in lower:
                level = "error"
            elif "warn" in lower or "rescheduled" in lower:
                level = "warning"
            elif "success" in lower or "submitted" in lower:
                level = "success"
            else:
                level = "info"
            entries.append({"raw": line, "level": level})

        return {"ok": True, "entries": entries}

    @safe_api_method
    def get_analytics(self) -> dict:
        """Return current analytics snapshot."""
        return {"ok": True, "analytics": self._store.get_analytics_snapshot()}

    @safe_api_method
    def connect_moodle(self, base_url: str, username: str, password: str) -> dict:
        """Authenticate against Moodle API and persist token to ~/.deadliner.json."""
        if not username or not username.strip():
            return {
                "ok": False,
                "field": "moodleUserInput",
                "error": "Please enter your Moodle username or KSE email.",
                "error_code": "VALIDATION_ERROR",
            }
        if not password:
            return {
                "ok": False,
                "field": "moodlePassInput",
                "error": "Please enter your Moodle password.",
                "error_code": "VALIDATION_ERROR",
                "hint": "Note: Moodle API requires your Moodle password, not your Google SSO password.",
            }

        norm_url = auth.normalize_moodle_url(base_url)
        try:
            token = auth.authenticate_moodle_credentials(norm_url, username.strip(), password)
        except (AuthError, ConnectionError) as e:
            return classify_error(e, source="moodle")

        if not auth.save_moodle_config(norm_url, token, cli.CONFIG_PATH):
            return {
                "ok": False,
                "error": f"Failed to write configuration to {cli.CONFIG_PATH}.",
                "error_code": "IO_ERROR",
                "hint": "Check file permissions for your home directory.",
            }

        scheduler.append_sync_log(f"[AUTH] Connected Moodle account ({norm_url})")
        return {"ok": True, "base_url": norm_url, "state": self.get_initial_state()}

    @safe_api_method
    def connect_google(
        self, client_id: str = "", client_secret: str = "", raw_json: str = ""
    ) -> dict:
        """Configure optional Google OAuth client secrets and launch local OAuth browser flow."""
        from deadliner.google_auth import (
            DEFAULT_CLIENT_ID,
            DEFAULT_CLIENT_SECRET,
            construct_client_secrets_from_keys,
            find_client_secrets_path,
            run_oauth_flow,
            save_client_secrets_json,
        )

        try:
            if raw_json and raw_json.strip():
                save_client_secrets_json(raw_json.strip())
            elif client_id.strip() and client_secret.strip():
                data = construct_client_secrets_from_keys(client_id.strip(), client_secret.strip())
                save_client_secrets_json(data)
        except ValueError as e:
            return {
                "ok": False,
                "field": "googleSecretsTextarea",
                "error": f"Invalid client_secret.json format: {e}",
                "error_code": "VALIDATION_ERROR",
                "hint": "Paste the full JSON content downloaded from Google Cloud Console -> OAuth 2.0 Client IDs.",
            }

        secrets_path = find_client_secrets_path()
        if not secrets_path and not (DEFAULT_CLIENT_ID and DEFAULT_CLIENT_SECRET):
            return {
                "ok": False,
                "needs_secrets": True,
                "field": "googleSecretsTextarea",
                "error": "Google OAuth client_secret.json is not configured yet.",
                "error_code": "CONFIG_MISSING",
                "hint": "Paste your downloaded client_secret.json into the box below, then click 'Sign in with Google'.",
            }

        try:
            run_oauth_flow(str(secrets_path) if secrets_path else None)
        except Exception as e:
            return {
                "ok": False,
                "error": f"Google OAuth authorization did not complete: {e}",
                "error_code": "AUTH_ERROR",
                "hint": "Ensure you approve Calendar and Classroom access in the browser window that opens.",
            }

        scheduler.append_sync_log("[AUTH] Connected Google OAuth (Calendar & Classroom)")
        return {"ok": True, "state": self.get_initial_state()}

    @safe_api_method
    def connect_kse(self, clean: bool = False) -> dict:
        """Launch KSE native WebView login in an isolated subprocess and reload credentials."""
        cmd = [sys.executable, "-m", "deadliner", "login", "kse"]
        if clean:
            cmd.append("--clean")

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "error": "KSE login window timed out after 3 minutes.",
                "error_code": "AUTH_TIMEOUT",
                "hint": "Click 'Sign in via KSE WebView' to try again, or paste your token directly below.",
            }
        except Exception as e:
            return {
                "ok": False,
                "error": f"Failed to launch KSE login window: {e}",
                "error_code": "PROCESS_ERROR",
                "hint": "You can also paste your KSE token directly in the fallback field below.",
            }

        token = kse_auth.get_valid_kse_token()
        if proc.returncode == 0 and token:
            scheduler.append_sync_log("[AUTH] Connected KSE Schedule via Native WebView")
            return {"ok": True, "state": self.get_initial_state()}

        stderr_msg = (proc.stderr or proc.stdout or "").strip()
        return {
            "ok": False,
            "error": stderr_msg or "KSE login window was closed before completing sign-in.",
            "error_code": "AUTH_CANCELLED",
            "hint": "Sign in with your @kse.org.ua Google account inside the window, or use the token paste box.",
        }

    @safe_api_method
    def save_kse_token(self, raw_text: str) -> dict:
        """Validate and save a pasted KSE JWT or JSON auth payload directly from the GUI."""
        if not raw_text or not raw_text.strip():
            return {
                "ok": False,
                "field": "kseTokenTextarea",
                "error": "Please paste a KSE JWT token or JSON payload first.",
                "error_code": "VALIDATION_ERROR",
            }

        creds = kse_auth._extract_credentials_from_text(raw_text.strip())
        if not creds:
            return {
                "ok": False,
                "field": "kseTokenTextarea",
                "error": "Could not find a valid 3-part JWT token (eyJ...) in the pasted text.",
                "error_code": "VALIDATION_ERROR",
                "hint": 'Copy the value of localStorage.getItem("__NEXUS_REACT_ADMIN_AUTH__") from schedule.kse.ua.',
            }

        tok, ref, sess, uname = creds
        if not kse_auth.verify_kse_token(tok):
            if ref:
                refreshed = kse_auth.refresh_kse_token(ref, sess)
                if refreshed and kse_auth.verify_kse_token(refreshed):
                    tok = refreshed
                else:
                    return {
                        "ok": False,
                        "field": "kseTokenTextarea",
                        "error": "The pasted KSE token is expired and could not be refreshed.",
                        "error_code": "AUTH_ERROR",
                        "hint": "Sign out and sign back in on schedule.kse.ua, or use the Native WebView Login button above.",
                    }
            else:
                return {
                    "ok": False,
                    "field": "kseTokenTextarea",
                    "error": "The pasted KSE token is expired or rejected by the KSE API.",
                    "error_code": "AUTH_ERROR",
                    "hint": "Use the Native WebView Login button above to obtain a fresh session.",
                }

        kse_auth.save_kse_credentials(tok, ref, sess)
        scheduler.append_sync_log("[AUTH] Updated KSE Schedule token via manual paste")
        return {"ok": True, "user_name": uname, "state": self.get_initial_state()}

    @safe_api_method
    def set_classroom_enabled(self, enabled: bool) -> dict:
        """Toggle Google Classroom deadline fetching."""
        cli.set_classroom_sync_enabled(bool(enabled))
        return {"ok": True, "classroom_enabled": bool(enabled), "state": self.get_initial_state()}

    @safe_api_method
    def configure_scheduler(self, enabled: bool, time_str: str = "08:00") -> dict:
        """Enable or disable the daily 24h background auto-sync task."""
        if enabled:
            clean_time = (time_str or "08:00").strip()
            if not TIME_24H_RE.match(clean_time):
                return {
                    "ok": False,
                    "field": "cronTimeInput",
                    "error": f"Invalid time format '{clean_time}'. Expected 24-hour HH:MM (e.g. 08:00 or 19:30).",
                    "error_code": "VALIDATION_ERROR",
                }
            success, msg = scheduler.enable_schedule(clean_time)
        else:
            success, msg = scheduler.disable_schedule()

        return {
            "ok": success,
            "error": None if success else msg,
            "message": msg,
            "state": self.get_initial_state(),
        }

    @safe_api_method
    def configure_path(self) -> dict:
        """Add Deadliner executable directory to the user's permanent system PATH."""
        if path_util.is_on_path():
            return {
                "ok": True,
                "message": "Deadliner is already configured in your system PATH.",
                "state": self.get_initial_state(),
            }
        success, msg = path_util.add_to_path()
        return {
            "ok": success,
            "error": None if success else msg,
            "message": msg,
            "state": self.get_initial_state(),
        }

    @safe_api_method
    def open_external_url(self, url: str) -> dict:
        """Safely open an external HTTP(S) URL in the default system browser."""
        if not url or not isinstance(url, str):
            return {"ok": False, "error": "URL cannot be empty."}
        cleaned = url.strip()
        if not (cleaned.startswith("https://") or cleaned.startswith("http://")):
            return {"ok": False, "error": "Only http:// and https:// URLs are permitted."}
        try:
            webbrowser.open(cleaned)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": f"Could not open browser: {e}"}
