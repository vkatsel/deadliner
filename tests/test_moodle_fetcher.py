import pytest

class Assignment:
    pass

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
