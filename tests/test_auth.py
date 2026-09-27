import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
import responses

from deadliner import auth
from deadliner.auth import (
    DEFAULT_MOODLE_URL,
    _cmd_login_moodle,
    normalize_moodle_url,
    save_moodle_config,
)


def test_normalize_moodle_url_default():
    """Empty or whitespace input defaults to DEFAULT_MOODLE_URL."""
    assert normalize_moodle_url("") == DEFAULT_MOODLE_URL
    assert normalize_moodle_url("   ") == DEFAULT_MOODLE_URL
    assert normalize_moodle_url("\n\t") == DEFAULT_MOODLE_URL


def test_normalize_moodle_url_custom_without_protocol():
    """Custom domain without protocol gets 'https://' prepended and trailing slash stripped."""
    assert normalize_moodle_url("teaching.kse.org.ua") == "https://teaching.kse.org.ua"
    assert normalize_moodle_url("moodle.example.com/") == "https://moodle.example.com"
    assert normalize_moodle_url("  moodle.example.com/sub/  ") == "https://moodle.example.com/sub"


def test_normalize_moodle_url_custom_with_protocol():
    """Custom URL with http or https protocol preserves protocol and strips trailing slash."""
    assert normalize_moodle_url("https://teaching.kse.org.ua/") == "https://teaching.kse.org.ua"
    assert normalize_moodle_url("http://localhost:8080/") == "http://localhost:8080"
    assert normalize_moodle_url("http://custom.moodle.org") == "http://custom.moodle.org"


@responses.activate
def test_cmd_login_moodle_default_base_url_success(tmp_path, monkeypatch, capsys):
    """Empty base URL input uses default URL, authenticates, and saves token."""
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(auth, "CONFIG_PATH", test_cfg)

    inputs = iter(["", "test_user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "mysecretpassword")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={"token": "mock-moodle-token-123"},
        status=200,
    )

    exit_code = _cmd_login_moodle(argparse.Namespace())
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "=== Moodle Login Setup ===" in captured.out
    assert "Successfully logged in and saved Moodle token!" in captured.out

    # Verify requests query parameters
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert "username=test_user%40kse.org.ua" in req.url or "username=test_user@kse.org.ua" in req.url
    assert "service=moodle_mobile_app" in req.url

    # Verify saved configuration
    assert test_cfg.exists()
    cfg = json.loads(test_cfg.read_text(encoding="utf-8"))
    assert cfg["moodle_base_url"] == DEFAULT_MOODLE_URL
    assert cfg["moodle_token"] == "mock-moodle-token-123"


@responses.activate
def test_cmd_login_moodle_custom_base_url_without_protocol(tmp_path, monkeypatch, capsys):
    """Custom domain without protocol gets prepended with https:// and authenticated."""
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(auth, "CONFIG_PATH", test_cfg)

    inputs = iter(["moodle.university.edu", "myuser"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass123")

    responses.add(
        responses.GET,
        "https://moodle.university.edu/login/token.php",
        json={"token": "univ-token-999"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 0

    cfg = json.loads(test_cfg.read_text(encoding="utf-8"))
    assert cfg["moodle_base_url"] == "https://moodle.university.edu"
    assert cfg["moodle_token"] == "univ-token-999"


@responses.activate
def test_cmd_login_moodle_custom_base_url_with_protocol(tmp_path, monkeypatch, capsys):
    """Custom URL with http protocol is preserved."""
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(auth, "CONFIG_PATH", test_cfg)

    inputs = iter(["http://localhost:8000/", "devuser"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "devpass")

    responses.add(
        responses.GET,
        "http://localhost:8000/login/token.php",
        json={"token": "dev-token-456"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 0

    cfg = json.loads(test_cfg.read_text(encoding="utf-8"))
    assert cfg["moodle_base_url"] == "http://localhost:8000"
    assert cfg["moodle_token"] == "dev-token-456"


@responses.activate
def test_cmd_login_moodle_preserves_existing_config(tmp_path, monkeypatch):
    """Moodle login preserves existing config attributes like Google and KSE tokens."""
    test_cfg = tmp_path / ".deadliner.json"
    test_cfg.write_text(
        json.dumps({"google_token": "goog-token-abc", "kse_token": "kse-jwt-xyz"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(auth, "CONFIG_PATH", test_cfg)

    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "password")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={"token": "new-moodle-token"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 0

    cfg = json.loads(test_cfg.read_text(encoding="utf-8"))
    assert cfg["google_token"] == "goog-token-abc"
    assert cfg["kse_token"] == "kse-jwt-xyz"
    assert cfg["moodle_base_url"] == DEFAULT_MOODLE_URL
    assert cfg["moodle_token"] == "new-moodle-token"


@responses.activate
def test_cmd_login_moodle_corrupt_existing_config_handled(tmp_path, monkeypatch):
    """Corrupt existing config file is overwritten safely."""
    test_cfg = tmp_path / ".deadliner.json"
    test_cfg.write_text("NOT_JSON_DATA", encoding="utf-8")
    monkeypatch.setattr(auth, "CONFIG_PATH", test_cfg)

    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "password")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={"token": "brand-new-token"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 0

    cfg = json.loads(test_cfg.read_text(encoding="utf-8"))
    assert cfg["moodle_token"] == "brand-new-token"


@responses.activate
def test_cmd_login_moodle_invalid_credentials_prints_tip(monkeypatch, capsys):
    """When credentials are wrong, prints incorrect credentials error and Google SSO tip."""
    inputs = iter(["", "wrong_user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "wrongpass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={
            "error": "Invalid login, please check your username and password",
            "errorcode": "invalidlogin",
        },
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Incorrect username or password." in captured.err
    assert "Tip: If you normally sign into Moodle via the Google button" in captured.err
    assert "local password" in captured.err


@responses.activate
def test_cmd_login_moodle_wrong_username_password_variant_prints_tip(monkeypatch, capsys):
    """Alternative error message format also triggers the Google SSO tip."""
    inputs = iter(["", "wrong_user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "wrongpass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={"error": "wrong username or password"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Incorrect username or password." in captured.err
    assert "Tip: If you normally sign into Moodle via the Google button" in captured.err


@responses.activate
def test_cmd_login_moodle_other_moodle_error(monkeypatch, capsys):
    """Unrecognized Moodle error string prints generic login failure."""
    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={"error": "Service moodle_mobile_app is disabled"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Login failed: Service moodle_mobile_app is disabled" in captured.err


@responses.activate
def test_cmd_login_moodle_connection_error(monkeypatch, capsys):
    """Network connection failure is gracefully handled."""
    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        body=requests.exceptions.ConnectionError("Failed to connect"),
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Could not connect to the Moodle server." in captured.err


@responses.activate
def test_cmd_login_moodle_timeout(monkeypatch, capsys):
    """Connection timeout is gracefully handled."""
    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        body=requests.exceptions.Timeout("Request timed out"),
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Connection to Moodle timed out." in captured.err


@responses.activate
def test_cmd_login_moodle_http_error(monkeypatch, capsys):
    """Bad HTTP status code prints helpful error."""
    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        status=404,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Received a bad response from the server (404)." in captured.err


@responses.activate
def test_cmd_login_moodle_invalid_json(monkeypatch, capsys):
    """Non-JSON response from server is handled."""
    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        body="<html>Not JSON</html>",
        content_type="text/html",
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Moodle returned invalid JSON." in captured.err


def test_save_moodle_config_io_error(tmp_path, monkeypatch, capsys):
    """Failed file write returns False and error message is printed on failure."""
    read_only_path = tmp_path / "subdir" / ".deadliner.json"

    def mock_write_text(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "write_text", mock_write_text)

    success = save_moodle_config(DEFAULT_MOODLE_URL, "dummy-token", read_only_path)
    assert success is False


@responses.activate
def test_cmd_login_moodle_save_config_failure(tmp_path, monkeypatch, capsys):
    """If saving configuration fails, an error is printed and returns code 1."""
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setattr(auth, "save_moodle_config", lambda *args, **kwargs: False)

    inputs = iter(["", "user@kse.org.ua"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "pass")

    responses.add(
        responses.GET,
        f"{DEFAULT_MOODLE_URL}/login/token.php",
        json={"token": "mock-token"},
        status=200,
    )

    exit_code = _cmd_login_moodle()
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Failed to save Moodle credentials to" in captured.err

