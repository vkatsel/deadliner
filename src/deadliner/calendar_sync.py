import logging
from datetime import timedelta, datetime
import hashlib

import requests

from deadliner.models import Assignment, AuthError, ScheduleEvent

logger = logging.getLogger(__name__)

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

#: Google Calendar colorId "11" is red — deadlines should be impossible to miss.
EVENT_COLOR_ID = "11"

#: Google Calendar colorId "6" is Tangerine (warm autumn orange) — for KSE classes.
SCHEDULE_EVENT_COLOR_ID = "2"

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


def _schedule_stable_id(event: ScheduleEvent) -> str:
    """Return a primary stable identifier for a KSE schedule class based on DB event_id."""
    if event.event_id:
        raw_id = f"kse_class:{event.event_id}"
    else:
        raw_id = f"kse_class:{event.date}:{event.period}:{event.discipline}:{event.subgroup}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


def _schedule_legacy_stable_id(event: ScheduleEvent) -> str:
    """Return the legacy composite identifier for backward-compatible event matching."""
    raw_id = f"kse_class:{event.event_id}:{event.date}:{event.period}:{event.discipline}:{event.subgroup}"
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


def _schedule_event_payload(event: ScheduleEvent) -> dict:
    """Translate a ScheduleEvent into a Google Calendar event body."""
    type_ua = (
        "Лекція"
        if event.event_type == "lecture"
        else "Практика"
        if event.event_type == "practice"
        else event.event_type.capitalize()
    )
    summary = (
        f"[{event.discipline}] {event.course_name} ({type_ua})"
        if event.discipline
        else f"{event.course_name} ({type_ua})"
    )

    loc_parts = []
    if event.room:
        loc_parts.append(f"Ауд. {event.room}")
    if event.shelter:
        loc_parts.append(f"Укриття {event.shelter}")
    loc_parts.append("вул. М. Шпака 3")
    location = ", ".join(loc_parts)

    desc_lines = []
    if event.teacher:
        desc_lines.append(f"Викладач: {event.teacher}")
    if event.subgroup is not None:
        desc_lines.append(f"Підгрупа: {event.subgroup}")
    if event.zoom_url:
        desc_lines.append(f"Zoom: {event.zoom_url}")
    if event.comment:
        desc_lines.append(f"Коментар: {event.comment}")
    description = "\n".join(desc_lines)

    return {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": event.start_utc.isoformat()},
        "end": {"dateTime": event.end_utc.isoformat()},
        "colorId": SCHEDULE_EVENT_COLOR_ID,
        "extendedProperties": {"private": {"deadliner_id": _schedule_stable_id(event)}},
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


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


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


def sync_schedule_to_calendar(
    events: list[ScheduleEvent],
    access_token: str,
    return_details: bool = False,
) -> tuple[int, int, int] | tuple[int, int, int, list[tuple[ScheduleEvent, str]]]:
    """Push KSE schedule classes to Google Calendar as peacock blue events.

    Idempotent: uses extendedProperties.private.deadliner_id to match and update.
    Returns (created, updated, skipped) or (created, updated, skipped, item_statuses) if return_details=True.
    """
    if not access_token:
        logger.error("Schedule sync attempted without a Google access token")
        raise AuthError("missing access token")

    headers = {"Authorization": f"Bearer {access_token}"}
    created = 0
    updated = 0
    skipped = 0
    statuses: list[tuple[ScheduleEvent, str]] = []

    for event in events:
        deadliner_id = _schedule_stable_id(event)
        payload = _schedule_event_payload(event)

        existing_event = _find_existing_event(headers, deadliner_id)
        if not existing_event:
            legacy_id = _schedule_legacy_stable_id(event)
            if legacy_id != deadliner_id:
                existing_event = _find_existing_event(headers, legacy_id)

        if existing_event:
            needs_update = (
                existing_event.get("summary") != payload["summary"]
                or existing_event.get("location") != payload.get("location")
                or existing_event.get("description") != payload.get("description")
                or _parse_dt(existing_event.get("start", {}).get("dateTime")) != _parse_dt(payload["start"]["dateTime"])
                or _parse_dt(existing_event.get("end", {}).get("dateTime")) != _parse_dt(payload["end"]["dateTime"])
                or existing_event.get("extendedProperties", {}).get("private", {}).get("deadliner_id") != deadliner_id
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
                statuses.append((event, "updated"))
            else:
                skipped += 1
                statuses.append((event, "skipped"))
        else:
            _request(
                "POST",
                f"{CALENDAR_API_BASE}/calendars/primary/events",
                headers,
                json=payload,
            )
            created += 1
            statuses.append((event, "created"))

    logger.debug(f"KSE schedule sync done: {created} created, {updated} updated, {skipped} skipped")
    if return_details:
        return created, updated, skipped, statuses
    return created, updated, skipped
