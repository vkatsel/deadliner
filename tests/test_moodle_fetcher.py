import pytest
import responses
from deadliner.models import AuthError
from deadliner.moodle_fetcher import fetch_moodle

# --- TESTS for US-01 (Fetch & Empty list) ---


@responses.activate
def test_fetch_moodle_valid_token_returns_assignments():
    base_url = "https://moodle.example.com"
    token = "valid-token"

    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        json={
            "events": [
                {
                    "name": "Homework 1",
                    "course": {"shortname": "CS101"},
                    "timestart": 1718449200,
                    "url": "http://moodle/1",
                }
            ]
        },
        status=200,
    )

    result = fetch_moodle(base_url, token)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].platform == "moodle"
    assert result[0].title == "Homework 1"
    assert result[0].course_shortname == "CS101"


@responses.activate
def test_fetch_moodle_strips_year_from_course_shortname():
    base_url = "https://moodle.example.com"
    token = "valid-token"

    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        json={
            "events": [
                {"name": "HW1", "course": {"shortname": "STAT2100-2024"}, "timestart": 1718449200, "url": "url1"},
                {"name": "HW2", "course": {"shortname": "SEBA2000_2025"}, "timestart": 1718449200, "url": "url2"},
                {"name": "HW3", "course": {"shortname": "CS101 2026"}, "timestart": 1718449200, "url": "url3"},
                {"name": "HW4", "course": {"shortname": "ML2000"}, "timestart": 1718449200, "url": "url4"},
            ]
        },
        status=200,
    )

    result = fetch_moodle(base_url, token)

    assert len(result) == 4
    assert result[0].course_shortname == "STAT2100"
    assert result[1].course_shortname == "SEBA2000"
    assert result[2].course_shortname == "CS101"
    assert result[3].course_shortname == "ML2000"
@responses.activate
def test_fetch_moodle_empty_calendar_returns_empty_list():
    base_url = "https://moodle.example.com"
    token = "valid-token-empty-account"

    responses.add(
        responses.GET, "https://moodle.example.com/webservice/rest/server.php", json={"events": []}, status=200
    )

    result = fetch_moodle(base_url, token)

    assert result == [], "Expected empty list when no assignments exist"


# --- TESTS for US-04 (Auth error -> fail loudly, never a silent empty list) ---


@responses.activate
def test_fetch_moodle_invalid_token_raises_auth_error():
    base_url = "https://moodle.example.com"
    token = "invalid-or-revoked-token"

    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        json={"exception": "moodle_exception", "errorcode": "invalidtoken", "message": "Invalid token"},
        status=200,
    )

    with pytest.raises(AuthError):
        fetch_moodle(base_url, token)


@responses.activate
def test_fetch_moodle_invalid_token_does_not_return_empty_list():
    base_url = "https://moodle.example.com"
    token = "invalid-or-revoked-token"

    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        json={"exception": "moodle_exception", "errorcode": "invalidtoken", "message": "Invalid token"},
        status=200,
    )

    try:
        fetch_moodle(base_url, token)
        assert False, "Expected AuthError but got a result — auth failure must not return an empty list silently"
    except AuthError:
        pass  # correct — auth failure raised loudly


@responses.activate
def test_fetch_moodle_submitted_assignment_detected():
    base_url = "https://moodle.example.com"
    token = "valid-token"

    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        json={
            "events": [
                {
                    "name": "Submitted HW",
                    "course": {"shortname": "CS101"},
                    "timestart": 1718449200,
                    "url": "http://moodle/1",
                    "action": {
                        "name": "Edit submission",
                        "url": "http://moodle/1?action=editsubmission",
                    },
                },
                {
                    "name": "View Only Submitted HW",
                    "course": {"shortname": "CS102"},
                    "timestart": 1718449200,
                    "url": "http://moodle/2",
                    "action": {
                        "name": "View submission",
                        "url": "http://moodle/2?action=view",
                    },
                },
                {
                    "name": "Ukrainian Submitted HW",
                    "course": {"shortname": "CS103"},
                    "timestart": 1718449200,
                    "url": "http://moodle/3",
                    "action": {
                        "name": "Редагувати відповідь",
                        "url": "http://moodle/3?action=editsubmission",
                    },
                },
            ]
        },
        status=200,
    )

    result = fetch_moodle(base_url, token)
    assert len(result) == 3
    assert result[0].is_submitted is True
    assert result[1].is_submitted is True
    assert result[2].is_submitted is True


@responses.activate
def test_fetch_moodle_unsubmitted_and_overdue_not_marked_submitted():
    base_url = "https://moodle.example.com"
    token = "valid-token"

    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        json={
            "events": [
                {
                    "name": "Unsubmitted HW",
                    "course": {"shortname": "CS101"},
                    "timestart": 1718449200,
                    "url": "http://moodle/1",
                    "action": {
                        "name": "Add submission",
                        "url": "http://moodle/1?action=editsubmission",
                    },
                },
                {
                    "name": "Overdue Missing Action HW",
                    "course": {"shortname": "CS102"},
                    "timestart": 1718449200,
                    "url": "http://moodle/2",
                    "overdue": True,
                    "action": None,
                },
                {
                    "name": "Teacher Grade Action HW",
                    "course": {"shortname": "CS103"},
                    "timestart": 1718449200,
                    "url": "http://moodle/3",
                    "action": {
                        "name": "Grade",
                        "url": "http://moodle/3?action=grader",
                    },
                },
            ]
        },
        status=200,
    )

    result = fetch_moodle(base_url, token)
    assert len(result) == 3
    assert result[0].is_submitted is False
    assert result[1].is_submitted is False
    assert result[2].is_submitted is False
