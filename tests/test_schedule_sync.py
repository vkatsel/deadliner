from datetime import datetime, timezone
import json
import pytest
import responses

from deadliner.calendar_sync import (
    CALENDAR_API_BASE,
    SCHEDULE_EVENT_COLOR_ID,
    sync_schedule_to_calendar,
)
from deadliner.models import AuthError, ScheduleEvent

EVENTS_URL = f"{CALENDAR_API_BASE}/calendars/primary/events"


def _sample_schedule_event():
    return ScheduleEvent(
        event_id="evt-101",
        discipline="STAT2100",
        course_name="Probability for Computer Science",
        event_type="lecture",
        subgroup=None,
        date="2026-09-02",
        period=5,
        start_utc=datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc),
        end_utc=datetime(2026, 9, 2, 13, 20, tzinfo=timezone.utc),
        room="1.08",
        shelter="S06",
        teacher="Iryna Rozora",
        zoom_url="https://zoom.us/j/12345",
        comment="Passcode 617742",
    )


@responses.activate
def test_sync_schedule_creates_new_event():
    responses.add(responses.GET, EVENTS_URL, json={"items": []}, status=200)
    responses.add(responses.GET, EVENTS_URL, json={"items": []}, status=200)
    responses.add(responses.POST, EVENTS_URL, json={"id": "gcal-evt-1"}, status=200)

    created, updated, skipped = sync_schedule_to_calendar([_sample_schedule_event()], "google-token")

    assert created == 1 and updated == 0 and skipped == 0
    post_calls = [c for c in responses.calls if c.request.method == "POST"]
    assert len(post_calls) == 1
    payload = json.loads(post_calls[0].request.body.decode())
    assert payload["summary"] == "[STAT2100] Probability for Computer Science (Лекція)"
    assert payload["colorId"] == SCHEDULE_EVENT_COLOR_ID
    assert "Ауд. 1.08, Укриття S06" in payload["location"]
    assert "Викладач: Iryna Rozora" in payload["description"]
    assert "deadliner_id" in payload["extendedProperties"]["private"]


@responses.activate
def test_sync_schedule_patches_modified_event():
    existing_event = {
        "id": "gcal-old-evt",
        "summary": "[STAT2100] Probability for Computer Science (Лекція)",
        "location": "Ауд. 1.01",  # Different room
        "start": {"dateTime": "2026-09-02T12:00:00+00:00"},
        "end": {"dateTime": "2026-09-02T13:20:00+00:00"},
    }
    responses.add(responses.GET, EVENTS_URL, json={"items": [existing_event]}, status=200)
    responses.add(responses.PATCH, f"{EVENTS_URL}/gcal-old-evt", json={"id": "gcal-old-evt"}, status=200)

    created, updated, skipped = sync_schedule_to_calendar([_sample_schedule_event()], "google-token")

    assert created == 0 and updated == 1 and skipped == 0


@responses.activate
def test_sync_schedule_skips_identical_event():
    from deadliner.calendar_sync import _schedule_event_payload

    event = _sample_schedule_event()
    payload = _schedule_event_payload(event)
    payload["id"] = "gcal-identical-evt"

    responses.add(responses.GET, EVENTS_URL, json={"items": [payload]}, status=200)

    created, updated, skipped = sync_schedule_to_calendar([event], "google-token")

    assert created == 0 and updated == 0 and skipped == 1


def test_sync_schedule_missing_token_raises_auth_error():
    with pytest.raises(AuthError):
        sync_schedule_to_calendar([_sample_schedule_event()], "")


def test_sync_schedule_empty_list_makes_no_calls():
    created, updated, skipped = sync_schedule_to_calendar([], "google-token")
    assert (created, updated, skipped) == (0, 0, 0)


@responses.activate
def test_sync_schedule_backward_compatible_migration():
    from deadliner.calendar_sync import _schedule_legacy_stable_id, _schedule_stable_id

    event = _sample_schedule_event()
    legacy_id = _schedule_legacy_stable_id(event)
    new_id = _schedule_stable_id(event)

    # First GET (with new_id) returns empty
    responses.add(responses.GET, EVENTS_URL, json={"items": []}, status=200)
    # Second GET (fallback with legacy_id) returns existing event
    legacy_event = {
        "id": "gcal-legacy-evt",
        "summary": "[STAT2100] Probability for Computer Science (Лекція)",
        "location": "Ауд. 1.08, Укриття S06, вул. М. Шпака 3",
        "description": "Викладач: Iryna Rozora\nZoom: https://zoom.us/j/12345\nКоментар: Passcode 617742",
        "start": {"dateTime": "2026-09-02T12:00:00+00:00"},
        "end": {"dateTime": "2026-09-02T13:20:00+00:00"},
        "extendedProperties": {"private": {"deadliner_id": legacy_id}},
    }
    responses.add(responses.GET, EVENTS_URL, json={"items": [legacy_event]}, status=200)
    # PATCH should be called to migrate deadliner_id to new_id
    responses.add(responses.PATCH, f"{EVENTS_URL}/gcal-legacy-evt", json={"id": "gcal-legacy-evt"}, status=200)

    created, updated, skipped = sync_schedule_to_calendar([event], "google-token")
    assert created == 0 and updated == 1 and skipped == 0
    assert len(responses.calls) == 3

