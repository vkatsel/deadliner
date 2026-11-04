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
                    "dueDate": {"year": 2099, "month": 7, "day": 10},
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



@responses.activate
def test_fetch_classroom_detects_submitted_assignments():
    oauth_creds = {"access_token": "valid-google-token"}

    responses.add(responses.GET, COURSES_URL, json={"courses": [{"id": "c1", "name": "CS101"}]}, status=200)
    responses.add(
        responses.GET,
        coursework_url("c1"),
        json={
            "courseWork": [
                {
                    "id": "cw1",
                    "title": "Turned In Homework",
                    "dueDate": {"year": 2099, "month": 7, "day": 10},
                    "dueTime": {"hours": 23, "minutes": 59},
                    "alternateLink": "https://classroom.google.com/c/1/cw/1",
                },
                {
                    "id": "cw2",
                    "title": "Pending Homework",
                    "dueDate": {"year": 2099, "month": 7, "day": 12},
                    "dueTime": {"hours": 23, "minutes": 59},
                    "alternateLink": "https://classroom.google.com/c/1/cw/2",
                },
                {
                    "id": "cw3",
                    "title": "Returned Homework",
                    "dueDate": {"year": 2099, "month": 7, "day": 15},
                    "dueTime": {"hours": 23, "minutes": 59},
                    "alternateLink": "https://classroom.google.com/c/1/cw/3",
                },
            ]
        },
        status=200,
    )

    # Submissions mock: cw1 is TURNED_IN, cw2 is CREATED (unsubmitted), cw3 is RETURNED
    responses.add(
        responses.GET,
        "https://classroom.googleapis.com/v1/courses/c1/courseWork/-/studentSubmissions",
        json={
            "studentSubmissions": [
                {"courseWorkId": "cw1", "state": "TURNED_IN"},
                {"courseWorkId": "cw2", "state": "CREATED"},
                {"courseWorkId": "cw3", "state": "RETURNED"},
            ]
        },
        status=200,
    )

    result = fetch_classroom(oauth_creds)
    assert len(result) == 3

    cw1 = next(a for a in result if a.title == "Turned In Homework")
    assert cw1.is_submitted is True

    cw2 = next(a for a in result if a.title == "Pending Homework")
    assert cw2.is_submitted is False

    cw3 = next(a for a in result if a.title == "Returned Homework")
    assert cw3.is_submitted is True
