from datetime import date, datetime, timezone
import pytest
import requests
import responses

from deadliner.kse_fetcher import (
    KSE_API_BASE,
    _period_to_datetimes,
    fetch_kse_schedule,
)
from deadliner.models import AuthError, ScheduleEvent

SCHEDULE_URL = f"{KSE_API_BASE}/schedule"


def test_period_to_datetimes_period_5_summer_dst():
    # 2026-09-02 (EEST is UTC+3)
    # Period 5 is 15:00 - 16:20 local -> 12:00 - 13:20 UTC
    start_utc, end_utc = _period_to_datetimes("2026-09-02", 5)
    assert start_utc == datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
    assert end_utc == datetime(2026, 9, 2, 13, 20, tzinfo=timezone.utc)


def test_period_to_datetimes_period_1_winter():
    # 2026-01-15 (EET is UTC+2)
    # Period 1 is 08:30 - 09:50 local -> 06:30 - 07:50 UTC
    start_utc, end_utc = _period_to_datetimes("2026-01-15", 1)
    assert start_utc == datetime(2026, 1, 15, 6, 30, tzinfo=timezone.utc)
    assert end_utc == datetime(2026, 1, 15, 7, 50, tzinfo=timezone.utc)


@responses.activate
def test_fetch_kse_schedule_valid_response():
    mock_payload = {
        "events": [
            [
                {
                    "event_id": "evt-101",
                    "discipline": "STAT2100",
                    "course_name": "Probability for Computer Science",
                    "event_type": "lecture",
                    "subgroup": None,
                    "date": "2026-09-02",
                    "period": 5,
                    "room": "1.08",
                    "shelter": "S06",
                    "teacher": {"name": {"first": "Iryna", "last": "Rozora"}},
                    "zoom_url": "https://zoom.us/j/12345",
                    "comment": "Passcode 617742",
                }
            ]
        ]
    }
    responses.add(responses.GET, SCHEDULE_URL, json=mock_payload, status=200)

    events = fetch_kse_schedule(token="mock-jwt-token", from_date="2026-09-02", till_date="2026-09-09")

    assert len(events) == 1
    ev = events[0]
    assert isinstance(ev, ScheduleEvent)
    assert ev.event_id == "evt-101"
    assert ev.discipline == "STAT2100"
    assert ev.course_name == "Probability for Computer Science"
    assert ev.event_type == "lecture"
    assert ev.room == "1.08"
    assert ev.shelter == "S06"
    assert ev.teacher == "Iryna Rozora"
    assert ev.zoom_url == "https://zoom.us/j/12345"
    assert ev.comment == "Passcode 617742"
    assert ev.start_utc == datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)


@responses.activate
def test_fetch_kse_schedule_incomplete_data_resilience():
    # Class with missing room, shelter, zoom, teacher (e.g. TBA)
    mock_payload = {
        "events": [
            {
                "id": "evt-bare",
                "discipline": "CS400",
                "date": "2026-09-04",
                "period": 5,
            }
        ]
    }
    responses.add(responses.GET, SCHEDULE_URL, json=mock_payload, status=200)

    events = fetch_kse_schedule(token="mock-token", from_date="2026-09-04", till_date="2026-09-05")

    assert len(events) == 1
    ev = events[0]
    assert ev.event_id == "evt-bare"
    assert ev.discipline == "CS400"
    assert ev.course_name == "CS400"  # fallback to discipline
    assert ev.room == ""
    assert ev.shelter == ""
    assert ev.teacher == ""
    assert ev.zoom_url == ""


@responses.activate
def test_fetch_kse_schedule_unauthorized_raises_auth_error():
    responses.add(responses.GET, SCHEDULE_URL, json={"error": "unauthorized"}, status=401)

    with pytest.raises(AuthError) as exc_info:
        fetch_kse_schedule(token="expired-token")

    assert "authentication failed" in str(exc_info.value).lower()


@responses.activate
def test_fetch_kse_schedule_forbidden_raises_auth_error():
    responses.add(responses.GET, SCHEDULE_URL, json={"error": "forbidden"}, status=403)

    with pytest.raises(AuthError):
        fetch_kse_schedule(token="forbidden-token")


@responses.activate
def test_fetch_kse_schedule_network_failure_raises_connection_error():
    responses.add(responses.GET, SCHEDULE_URL, body=requests.ConnectionError("Connection dropped"))

    with pytest.raises(ConnectionError):
        fetch_kse_schedule()


@responses.activate
def test_fetch_kse_schedule_empty_calendar_returns_empty_list():
    responses.add(responses.GET, SCHEDULE_URL, json={"events": []}, status=200)

    events = fetch_kse_schedule(token="token", from_date="2026-09-01", till_date="2026-09-07")
    assert events == []
