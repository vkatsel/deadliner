import logging
from datetime import timedelta

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
    duplicating it — no fuzzy title matching (design_doc.md §5).
    """
    if assignment.url:
        return f"{assignment.platform}:{assignment.url}"
    return f"{assignment.platform}:{assignment.course_shortname}:{assignment.title}:{assignment.due_utc.isoformat()}"


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


def _find_existing_event(headers: dict, deadliner_id: str) -> str | None:
    """Return the event id of a previously synced event, or None."""
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
    return items[0]["id"] if items else None


def sync_to_calendar(assignments: list[Assignment], access_token: str) -> tuple[int, int]:
    """Push assignments to Google Calendar as red deadline events.

    Idempotent: each event carries its assignment's stable id in private
    extendedProperties; an assignment that was already synced is patched in
    place (deadline moved on Moodle → event moves too), never duplicated.

    Returns (created, updated) counts. Raises AuthError on a rejected token
    and ConnectionError on network failure — loudly, never silently.
    """
    if not access_token:
        logger.error("Calendar sync attempted without an access token")
        raise AuthError("missing access token")

    headers = {"Authorization": f"Bearer {access_token}"}
    created = 0
    updated = 0

    for assignment in assignments:
        deadliner_id = _stable_id(assignment)
        payload = _event_payload(assignment)

        event_id = _find_existing_event(headers, deadliner_id)
        if event_id:
            _request(
                "PATCH",
                f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
                headers,
                json=payload,
            )
            updated += 1
            logger.info(f"Updated calendar event for '{assignment.title}'")
        else:
            _request(
                "POST",
                f"{CALENDAR_API_BASE}/calendars/primary/events",
                headers,
                json=payload,
            )
            created += 1
            logger.info(f"Created calendar event for '{assignment.title}'")

    logger.info(f"Calendar sync done: {created} created, {updated} updated")
    return created, updated
