import pytest

class Assignment:
    pass

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
