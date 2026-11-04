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


@responses.activate
def test_fetch_moodle_merges_upcoming_view_and_strictly_verifies_submission():
    base_url = "https://moodle.example.com"
    token = "valid-token"

    # Action events: only HW1 (unsubmitted)
    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        match=[responses.matchers.query_param_matcher({
            "wstoken": token,
            "wsfunction": "core_calendar_get_action_events_by_timesort",
            "moodlewsrestformat": "json",
        }, strict_match=False)],
        json={
            "events": [
                {
                    "name": "HW1 Unsubmitted",
                    "course": {"shortname": "CS101"},
                    "timestart": 1718449200,
                    "url": "http://moodle/1",
                    "action": {"name": "Add submission"},
                }
            ]
        },
        status=200,
    )

    # Upcoming view: has HW1 and HW2 (Assignment 3, submitted, action=None) and HW3 (teacher grading, action=None)
    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        match=[responses.matchers.query_param_matcher({
            "wstoken": token,
            "wsfunction": "core_calendar_get_calendar_upcoming_view",
            "moodlewsrestformat": "json",
        }, strict_match=False)],
        json={
            "events": [
                {
                    "name": "HW1 Unsubmitted",
                    "course": {"shortname": "CS101"},
                    "timestart": 1718449200,
                    "url": "http://moodle/1",
                    "action": {"name": "Add submission"},
                },
                {
                    "id": 999,
                    "name": "HW2 Submitted",
                    "course": {"shortname": "CS400"},
                    "timestart": 1718449200,
                    "url": "https://moodle.example.com/mod/assign/view.php?id=138721",
                    "component": "mod_assign",
                    "instance": 138721,
                    "eventtype": "due",
                    "action": None,
                },
                {
                    "id": 1000,
                    "name": "HW3 Teacher Practice",
                    "course": {"shortname": "CS530"},
                    "timestart": 1718449200,
                    "url": "https://moodle.example.com/mod/assign/view.php?id=142489",
                    "component": "mod_assign",
                    "instance": 142489,
                    "eventtype": "due",
                    "action": None,
                },
            ]
        },
        status=200,
    )

    # Mock cm lookup for HW2 (138721 -> assign 16079)
    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        match=[responses.matchers.query_param_matcher({
            "wsfunction": "core_course_get_course_module",
            "cmid": 138721,
        }, strict_match=False)],
        json={"cm": {"instance": 16079}},
        status=200,
    )

    # Mock submission status for HW2 (assign 16079 -> submitted)
    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        match=[responses.matchers.query_param_matcher({
            "wsfunction": "mod_assign_get_submission_status",
            "assignid": 16079,
        }, strict_match=False)],
        json={"lastattempt": {"submission": {"status": "submitted"}}},
        status=200,
    )

    # Mock cm lookup for HW3 (142489 -> assign 16530)
    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        match=[responses.matchers.query_param_matcher({
            "wsfunction": "core_course_get_course_module",
            "cmid": 142489,
        }, strict_match=False)],
        json={"cm": {"instance": 16530}},
        status=200,
    )

    # Mock submission status for HW3 (assign 16530 -> teacher gradingsummary, no lastattempt)
    responses.add(
        responses.GET,
        "https://moodle.example.com/webservice/rest/server.php",
        match=[responses.matchers.query_param_matcher({
            "wsfunction": "mod_assign_get_submission_status",
            "assignid": 16530,
        }, strict_match=False)],
        json={"gradingsummary": {"participantcount": 50}},
        status=200,
    )

    result = fetch_moodle(base_url, token)
    assert len(result) == 3

    hw1 = next(a for a in result if a.title == "HW1 Unsubmitted")
    assert hw1.is_submitted is False

    hw2 = next(a for a in result if a.title == "HW2 Submitted")
    assert hw2.is_submitted is True

    hw3 = next(a for a in result if a.title == "HW3 Teacher Practice")
    assert hw3.is_submitted is False
