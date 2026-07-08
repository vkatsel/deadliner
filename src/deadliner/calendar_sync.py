import logging
from datetime import timedelta, datetime
import hashlib

import requests

from deadliner.models import Assignment, AuthError

logger = logging.getLogger(__name__)

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

#: Google Calendar colorId "11" is red — deadlines should be impossible to miss.
EVENT_COLOR_ID = "11"

#: The event ends exactly at the deadline and starts this many minutes before it,
#: so the calendar block visually points at the cutoff moment (US-03: a midnight
#: deadline must read as "the night before", not as the whole next day).
EVENT_DURATION_MINUTES = 15


def _stable_id(assignment: Assignment) -> str:
    """Return a stable identifier for an assignment, for idempotent mapping.

    Prefers the platform URL (unique per assignment on both Moodle and
    Classroom); falls back to a composite key. Stored in the event's private
    extendedProperties so re-syncing updates the same event instead of
    duplicating it. We hash the result to avoid unsafe characters (like '=')
    breaking the Google Calendar API search query.
    """
    if assignment.url:
        raw_id = f"{assignment.platform}:{assignment.url}"
    else:
        raw_id = (
            f"{assignment.platform}:{assignment.course_shortname}:{assignment.title}:{assignment.due_utc.isoformat()}"
        )
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


def _event_payload(assignment: Assignment) -> dict:
    """Translate an Assignment into a Google Calendar event body."""
    end = assignment.due_utc
    start = end - timedelta(minutes=EVENT_DURATION_MINUTES)
    summary = f"[DEADLINE] {assignment.title}"
    if assignment.course_shortname:
        summary = f"[DEADLINE] [{assignment.course_shortname}] {assignment.title}"
    return {
        "summary": summary,
        "description": assignment.url,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "colorId": EVENT_COLOR_ID,
        "extendedProperties": {"private": {"deadliner_id": _stable_id(assignment)}},
    }


def _request(method: str, url: str, headers: dict, **kwargs) -> dict:
    try:
        response = requests.request(method, url, headers=headers, timeout=10, **kwargs)
    except requests.RequestException as e:
        logger.error(f"Calendar connection failed: {e}")
        raise ConnectionError(f"Failed to connect to Google Calendar: {e}")

    if response.status_code == 401:
        logger.error("Calendar OAuth token rejected by API")
        raise AuthError("token rejected")
    response.raise_for_status()

    return response.json()


def _find_existing_event(headers: dict, deadliner_id: str) -> dict | None:
    """Return the full event dictionary of a previously synced event, or None."""
    data = _request(
        "GET",
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers,
        params={
            "privateExtendedProperty": f"deadliner_id={deadliner_id}",
            "maxResults": 1,
            "singleEvents": "true",
        },
    )
    items = data.get("items", [])
    return items[0] if items else None


def sync_to_calendar(assignments: list[Assignment], access_token: str) -> tuple[int, int, int]:
    """Push assignments to Google Calendar as red deadline events.

    Idempotent: each event carries its assignment's stable id in private
    extendedProperties; an assignment that was already synced is patched in
    place (deadline moved on Moodle → event moves too), never duplicated.
    Identical events are skipped entirely to save API quotas.

    Returns (created, updated, skipped) counts. Raises AuthError on a rejected token
    and ConnectionError on network failure — loudly, never silently.
    """
    if not access_token:
        logger.error("Calendar sync attempted without an access token")
        raise AuthError("missing access token")

    headers = {"Authorization": f"Bearer {access_token}"}
    created = 0
    updated = 0
    skipped = 0

    for assignment in assignments:
        deadliner_id = _stable_id(assignment)
        payload = _event_payload(assignment)

        existing_event = _find_existing_event(headers, deadliner_id)
        if existing_event:

            def _parse_dt(s: str | None) -> datetime | None:
                if not s:
                    return None
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                return datetime.fromisoformat(s)

            needs_update = (
                existing_event.get("summary") != payload["summary"]
                or _parse_dt(existing_event.get("start", {}).get("dateTime")) != _parse_dt(payload["start"]["dateTime"])
                or _parse_dt(existing_event.get("end", {}).get("dateTime")) != _parse_dt(payload["end"]["dateTime"])
            )
            if needs_update:
                event_id = existing_event["id"]
                _request(
                    "PATCH",
                    f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
                    headers,
                    json=payload,
                )
                updated += 1
            else:
                skipped += 1
        else:
            _request(
                "POST",
                f"{CALENDAR_API_BASE}/calendars/primary/events",
                headers,
                json=payload,
            )
            created += 1

    logger.debug(f"Calendar sync done: {created} created, {updated} updated, {skipped} skipped")
    return created, updated, skipped
