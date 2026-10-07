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


@responses.activate
def test_sync_creates_green_submitted_event():
    responses.add(responses.GET, EVENTS_URL, json={"items": []}, status=200)
    responses.add(responses.POST, EVENTS_URL, json={"id": "evt-sub"}, status=200)

    assignment = _assignment()
    assignment.is_submitted = True

    created, updated, skipped = sync_to_calendar([assignment], "valid-token")

    assert created == 1 and updated == 0 and skipped == 0
    import json

    sent_payload = json.loads(responses.calls[1].request.body)
    assert "[SUBMITTED]" in sent_payload["summary"], "submitted event summary must carry [SUBMITTED]"
    assert sent_payload["colorId"] == "10", "submitted event must be green (colorId 10)"
    assert "Status: Submitted ✓" in sent_payload["description"]


@responses.activate
def test_sync_patches_existing_deadline_to_submitted():
    from deadliner.calendar_sync import _event_payload

    # Existing event in calendar is unsubmitted [DEADLINE] with colorId 11
    unsubmitted = _assignment()
    payload = _event_payload(unsubmitted)
    payload["id"] = "evt-existing"

    responses.add(responses.GET, EVENTS_URL, json={"items": [payload]}, status=200)
    responses.add(responses.PATCH, f"{EVENTS_URL}/evt-existing", json={"id": "evt-existing"}, status=200)

    # Now student submitted the assignment
    submitted = _assignment()
    submitted.is_submitted = True

    created, updated, skipped = sync_to_calendar([submitted], "valid-token")

    assert created == 0 and updated == 1 and skipped == 0
    patch_body = responses.calls[1].request.body.decode()
    assert "[SUBMITTED]" in patch_body
    assert '"colorId": "10"' in patch_body


@responses.activate
def test_sync_detects_and_patches_rescheduled_deadline():
    from deadliner.calendar_sync import _event_payload

    # Existing event in calendar originally due July 10
    original = _assignment()
    payload = _event_payload(original)
    payload["id"] = "evt-rescheduled"

    responses.add(responses.GET, EVENTS_URL, json={"items": [payload]}, status=200)
    responses.add(responses.PATCH, f"{EVENTS_URL}/evt-rescheduled", json={"id": "evt-rescheduled"}, status=200)

    # Professor postponed deadline to July 15
    rescheduled = Assignment(
        platform="moodle",
        course_shortname="CS101",
        title="Lab Report",
        due_utc=datetime(2026, 7, 15, 21, 0, 0, tzinfo=timezone.utc),
        url="https://moodle.example.com/mod/assign/view.php?id=42",
    )

    created, updated, skipped, statuses = sync_to_calendar([rescheduled], "valid-token", return_details=True)

    assert created == 0 and updated == 1 and skipped == 0
    assert len(statuses) == 1
    item, status, old_due = statuses[0]
    assert item == rescheduled
    assert status == "rescheduled"
    assert old_due == datetime(2026, 7, 10, 21, 0, 0, tzinfo=timezone.utc)

    patch_body = responses.calls[1].request.body.decode()
    assert "2026-07-15T21:00:00+00:00" in patch_body


def test_stable_id_without_url_does_not_change_when_due_changes():
    from deadliner.calendar_sync import _legacy_stable_id, _stable_id

    assign1 = Assignment(
        platform="moodle",
        course_shortname="CS101",
        title="Oral Exam",
        due_utc=datetime(2026, 7, 10, 10, 0, 0, tzinfo=timezone.utc),
        url="",
    )
    assign2 = Assignment(
        platform="moodle",
        course_shortname="CS101",
        title="Oral Exam",
        due_utc=datetime(2026, 7, 12, 14, 0, 0, tzinfo=timezone.utc),
        url="",
    )

    # Primary stable id should match despite different due dates
    assert _stable_id(assign1) == _stable_id(assign2)
    # Legacy stable id captured due date
    assert _legacy_stable_id(assign1) != _legacy_stable_id(assign2)

