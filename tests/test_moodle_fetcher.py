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
