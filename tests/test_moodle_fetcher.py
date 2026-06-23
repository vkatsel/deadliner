import pytest


class Assignment:
    pass


class AuthError(Exception):
    """Raised when a connector rejects the supplied credentials (design_doc §3)."""


def fetch_moodle(base_url: str, token: str) -> list[Assignment]:
    # Fails cleanly with an informative message as required by Stage 2
    raise AssertionError("fetch_moodle not implemented yet (needs to return list of Assignments)")


# --- TESTS for US-01 (Fetch & Empty list) ---

def test_fetch_moodle_valid_token_returns_assignments():
    base_url = "https://moodle.example.com"
    token = "valid-token"

    result = fetch_moodle(base_url, token)

    assert isinstance(result, list)
    assert len(result) > 0


def test_fetch_moodle_empty_calendar_returns_empty_list():
    base_url = "https://moodle.example.com"
    token = "valid-token-empty-account"

    result = fetch_moodle(base_url, token)

    # Empty calendar should return an empty list, not crash
    assert result == [], "Expected empty list when no assignments exist"


# --- TESTS for US-04 (Auth error -> fail loudly, never a silent empty list) ---

def test_fetch_moodle_invalid_token_raises_auth_error():
    # Arrange
    base_url = "https://moodle.example.com"
    token = "invalid-or-revoked-token"

    # Act / Assert — a rejected token must raise AuthError (design_doc §3),
    # never return [] silently (PRD §5 anti-pattern: Mini #1 silent 200 OK).
    with pytest.raises(AuthError):
        fetch_moodle(base_url, token)


def test_fetch_moodle_invalid_token_does_not_return_empty_list():
    # Arrange
    base_url = "https://moodle.example.com"
    token = "invalid-or-revoked-token"

    # Act / Assert — guard against the exact Mini #1 regression: an auth failure
    # must raise, not silently return []. The assert is reachable only if no
    # exception fired, which is itself the failure we are guarding against.
    try:
        result = fetch_moodle(base_url, token)
        assert False, (
            "Expected AuthError but got a result — auth failure must not "
            "return an empty list silently"
        )
    except AuthError:
        pass  # correct — auth failure raised loudly
