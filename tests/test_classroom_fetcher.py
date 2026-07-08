import pytest
import responses
from deadliner.models import AuthError
from deadliner.classroom_fetcher import fetch_classroom

COURSES_URL = "https://classroom.googleapis.com/v1/courses"


def coursework_url(course_id):
    return f"https://classroom.googleapis.com/v1/courses/{course_id}/courseWork"


# --- TESTS for US-01 (Fetch & Empty list) ---


@responses.activate
def test_fetch_classroom_valid_oauth_returns_assignments():
    oauth_creds = {"access_token": "valid-google-token"}

    responses.add(responses.GET, COURSES_URL, json={"courses": [{"id": "c1", "name": "CS101"}]}, status=200)
    responses.add(
        responses.GET,
        coursework_url("c1"),
        json={
            "courseWork": [
                {
                    "title": "Homework 1",
                    "dueDate": {"year": 2026, "month": 7, "day": 10},
                    "dueTime": {"hours": 23, "minutes": 59},
                    "alternateLink": "https://classroom.google.com/c/1",
                }
            ]
        },
        status=200,
    )

    result = fetch_classroom(oauth_creds)

    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0].platform == "classroom"
    assert result[0].title == "Homework 1"
    assert result[0].course_shortname == "CS101"


@responses.activate
def test_fetch_classroom_filters_out_past_deadlines():
    oauth_creds = {"access_token": "valid-google-token"}

    responses.add(responses.GET, COURSES_URL, json={"courses": [{"id": "c1", "name": "CS101"}]}, status=200)
    responses.add(
        responses.GET,
        coursework_url("c1"),
        json={
            "courseWork": [
                {
                    "title": "Past Homework",
                    "dueDate": {"year": 2020, "month": 1, "day": 1},
                    "dueTime": {"hours": 12, "minutes": 0},
                    "alternateLink": "https://classroom.google.com/c/1",
                }
            ]
        },
        status=200,
    )

    result = fetch_classroom(oauth_creds)
    assert result == []


@responses.activate
def test_fetch_classroom_no_active_courses_returns_empty_list():
    oauth_creds = {"access_token": "valid-token-no-courses"}

    responses.add(responses.GET, COURSES_URL, json={"courses": []}, status=200)

    result = fetch_classroom(oauth_creds)

    assert result == [], "Expected empty list when user has no active Google Classroom assignments"


# --- TESTS for US-04 (Auth error -> fail loudly on a revoked/expired OAuth token) ---


@responses.activate
def test_fetch_classroom_revoked_oauth_raises_auth_error():
    # Arrange — an expired or revoked OAuth token.
    oauth_creds = {"access_token": "revoked-google-token"}

    responses.add(
        responses.GET, COURSES_URL, json={"error": {"code": 401, "message": "Invalid Credentials"}}, status=401
    )

    # Act / Assert — design_doc §3 requires AuthError when the OAuth token is
    # revoked or expired, not a silent empty list.
    with pytest.raises(AuthError):
        fetch_classroom(oauth_creds)


def test_fetch_classroom_missing_access_token_raises_auth_error():
    # Arrange — credentials dict present but missing the required field;
    # a missing token is an auth failure, not "no courses". No HTTP call
    # should even be attempted, so no `responses` mocking is needed here.
    oauth_creds = {}

    # Act / Assert
    with pytest.raises(AuthError):
        fetch_classroom(oauth_creds)
