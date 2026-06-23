import pytest


class Assignment:
    pass


class AuthError(Exception):
    """Raised when a connector rejects the supplied credentials (design_doc §3)."""


def fetch_classroom(oauth_credentials: dict) -> list[Assignment]:
    raise AssertionError("fetch_classroom not implemented yet (needs to parse Google API response)")


# --- TESTS for US-01 (Fetch & Empty list) ---

def test_fetch_classroom_valid_oauth_returns_assignments():
    oauth_creds = {"access_token": "valid-google-token"}

    result = fetch_classroom(oauth_creds)

    assert isinstance(result, list)
    assert len(result) > 0


def test_fetch_classroom_no_active_courses_returns_empty_list():
    oauth_creds = {"access_token": "valid-token-no-courses"}

    result = fetch_classroom(oauth_creds)

    assert result == [], "Expected empty list when user has no active Google Classroom assignments"


# --- TESTS for US-04 (Auth error -> fail loudly on a revoked/expired OAuth token) ---

def test_fetch_classroom_revoked_oauth_raises_auth_error():
    # Arrange — an expired or revoked OAuth token.
    oauth_creds = {"access_token": "revoked-google-token"}

    # Act / Assert — design_doc §3 requires AuthError when the OAuth token is
    # revoked or expired, not a silent empty list.
    with pytest.raises(AuthError):
        fetch_classroom(oauth_creds)


def test_fetch_classroom_missing_access_token_raises_auth_error():
    # Arrange — credentials dict present but missing the required field;
    # a missing token is an auth failure, not "no courses".
    oauth_creds = {}

    # Act / Assert
    with pytest.raises(AuthError):
        fetch_classroom(oauth_creds)
