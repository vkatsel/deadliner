from datetime import datetime, timezone

import pytest
import responses

from deadliner.calendar_sync import CALENDAR_API_BASE, sync_to_calendar
from deadliner.models import Assignment, AuthError

EVENTS_URL = f"{CALENDAR_API_BASE}/calendars/primary/events"


def _assignment():
    return Assignment(
        platform="moodle",
        course_shortname="CS101",
        title="Lab Report",
        due_utc=datetime(2026, 7, 10, 21, 0, 0, tzinfo=timezone.utc),
        url="https://moodle.example.com/mod/assign/view.php?id=42",
    )


@responses.activate
def test_sync_creates_event_for_new_assignment():
    responses.add(responses.GET, EVENTS_URL, json={"items": []}, status=200)
    responses.add(responses.POST, EVENTS_URL, json={"id": "evt1"}, status=200)

    created, updated, skipped = sync_to_calendar([_assignment()], "valid-token")

    assert created == 1 and updated == 0 and skipped == 0
    body = responses.calls[1].request.body.decode()
    assert "[DEADLINE]" in body, "event summary must carry the [DEADLINE] marker"
    assert "deadliner_id" in body, "event must carry the stable id for idempotency"
    assert '"colorId": "11"' in body, "deadline events must be red (colorId 11)"
    # The event must END exactly at the deadline (US-03: the block points at the cutoff)
    assert "2026-07-10T21:00:00+00:00" in body


@responses.activate
def test_sync_patches_existing_event_instead_of_duplicating():
    responses.add(responses.GET, EVENTS_URL, json={"items": [{"id": "evt-old"}]}, status=200)
    responses.add(responses.PATCH, f"{EVENTS_URL}/evt-old", json={"id": "evt-old"}, status=200)

    created, updated, skipped = sync_to_calendar([_assignment()], "valid-token")

    assert created == 0 and updated == 1 and skipped == 0, (
        "an already-synced assignment with different data must be patched"
    )


@responses.activate
def test_sync_skips_identical_event_instead_of_patching():
    assignment = _assignment()
    # Mock GET to return an event with identical summary and times
    from deadliner.calendar_sync import _event_payload

    payload = _event_payload(assignment)
    payload["id"] = "evt-old"
    responses.add(responses.GET, EVENTS_URL, json={"items": [payload]}, status=200)

    created, updated, skipped = sync_to_calendar([assignment], "valid-token")

    assert created == 0 and updated == 0 and skipped == 1, "identical assignments must be skipped"


@responses.activate
def test_sync_revoked_token_raises_auth_error():
    responses.add(responses.GET, EVENTS_URL, json={"error": {"code": 401}}, status=401)

    with pytest.raises(AuthError):
        sync_to_calendar([_assignment()], "revoked-token")


def test_sync_missing_token_raises_auth_error_before_any_http():
    with pytest.raises(AuthError):
        sync_to_calendar([_assignment()], "")


def test_sync_empty_list_makes_no_http_calls():
    created, updated, skipped = sync_to_calendar([], "valid-token")

    assert (created, updated, skipped) == (0, 0, 0)
