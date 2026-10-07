import argparse
import json
import sys
import pytest
import responses

from deadliner import kse_auth
from deadliner.kse_auth import (
    KSE_AUTH_REFRESH_URL,
    KSE_SCHEDULE_VERIFY_URL,
    _cmd_login_kse,
    get_valid_kse_token,
    load_kse_credentials,
    refresh_kse_token,
    save_kse_credentials,
)
from deadliner.models import AuthError


def test_save_and_load_kse_credentials(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_REFRESH_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_SESSION_ID", "")

    save_kse_credentials("jwt-token-123", "refresh-token-456", "session-789")

    token, refresh, session = load_kse_credentials()
    assert token == "jwt-token-123"
    assert refresh == "refresh-token-456"
    assert session == "session-789"


@responses.activate
def test_refresh_kse_token_success(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_REFRESH_TOKEN", "")

    responses.add(
        responses.POST,
        KSE_AUTH_REFRESH_URL,
        json={"token": "new-jwt-token-999", "refresh_token": "new-refresh-token-999"},
        status=200,
    )

    new_token = refresh_kse_token("old-refresh-token", "sess-1")
    assert new_token == "new-jwt-token-999"

    saved_token, saved_refresh, _ = load_kse_credentials()
    assert saved_token == "new-jwt-token-999"
    assert saved_refresh == "new-refresh-token-999"


@responses.activate
def test_refresh_kse_token_failure(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)

    responses.add(responses.POST, KSE_AUTH_REFRESH_URL, json={"error": "unauthorized"}, status=401)

    new_token = refresh_kse_token("invalid-refresh", "sess-1")
    assert new_token is None


@responses.activate
def test_refresh_kse_token_rotation_camelcase(tmp_path, monkeypatch):
    """Verify Bug 1 fix: React Admin camelCase refreshToken rotation is persisted."""
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_REFRESH_TOKEN", "")

    responses.add(
        responses.POST,
        KSE_AUTH_REFRESH_URL,
        json={
            "accessToken": "new-access-jwt",
            "refreshToken": "rotated-refresh-token-xyz",
            "sessionId": "rotated-session-123",
        },
        status=200,
    )

    new_token = refresh_kse_token("stale-refresh-token", "old-sess")
    assert new_token == "new-access-jwt"

    saved_token, saved_refresh, saved_session = load_kse_credentials()
    assert saved_token == "new-access-jwt"
    assert saved_refresh == "rotated-refresh-token-xyz"
    assert saved_session == "rotated-session-123"

    # Also verify request sent both camelCase and snake_case
    req_body = json.loads(responses.calls[0].request.body)
    assert req_body["refresh_token"] == "stale-refresh-token"
    assert req_body["refreshToken"] == "stale-refresh-token"
    assert req_body["sessionId"] == "old-sess"


def test_is_kse_token_expired_millisecond_timestamp():
    import time
    # Expiring in 10 minutes, but timestamp in milliseconds (13 digits)
    future_ms = (time.time() + 600) * 1000
    token_valid = f"eyJhbGciOi.{kse_auth.base64.urlsafe_b64encode(json.dumps({'exp': future_ms}).encode()).decode()}.sig"
    assert not kse_auth.is_kse_token_expired(token_valid)

    # Expired 10 minutes ago in milliseconds
    past_ms = (time.time() - 600) * 1000
    token_expired = f"eyJhbGciOi.{kse_auth.base64.urlsafe_b64encode(json.dumps({'exp': past_ms}).encode()).decode()}.sig"
    assert kse_auth.is_kse_token_expired(token_expired)



def test_get_valid_kse_token_falls_back_to_refresh(monkeypatch):
    monkeypatch.setattr(kse_auth, "load_kse_credentials", lambda: ("", "refresh-abc", "sess-1"))
    monkeypatch.setattr(kse_auth, "refresh_kse_token", lambda r, s: "refreshed-jwt")

    token = get_valid_kse_token()
    assert token == "refreshed-jwt"


def test_get_valid_kse_token_expired_refresh_failed_returns_empty_or_raises(monkeypatch):
    monkeypatch.setattr(kse_auth, "load_kse_credentials", lambda: ("expired-jwt", "bad-refresh", "sess-1"))
    monkeypatch.setattr(kse_auth, "is_kse_token_expired", lambda tok: True)
    monkeypatch.setattr(kse_auth, "refresh_kse_token", lambda r, s: None)

    # By default (raise_on_failure=False), returns empty string instead of expired token
    assert get_valid_kse_token(raise_on_failure=False) == ""

    # When raise_on_failure=True, raises AuthError
    with pytest.raises(AuthError) as exc_info:
        get_valid_kse_token(raise_on_failure=True)
    assert "re-authenticate" in str(exc_info.value).lower()


def test_cmd_login_kse_invalid_token_format(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "/")
    exit_code = _cmd_login_kse(argparse.Namespace(manual=True))
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "invalid jwt format" in err.lower()


@responses.activate
def test_cmd_login_kse_rejected_by_api(monkeypatch, capsys):
    responses.add(responses.GET, KSE_SCHEDULE_VERIFY_URL, json={"error": "unauthorized"}, status=401)
    monkeypatch.setattr("builtins.input", lambda prompt: "header.payload.signature")

    exit_code = _cmd_login_kse(argparse.Namespace(manual=True))
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "401 unauthorized" in err.lower()


@responses.activate
def test_cmd_login_kse_success(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_REFRESH_TOKEN", "")

    responses.add(responses.GET, KSE_SCHEDULE_VERIFY_URL, json={"groups": []}, status=200)
    monkeypatch.setattr("builtins.input", lambda prompt: "valid.jwt.token")

    exit_code = _cmd_login_kse(argparse.Namespace(manual=True))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "successfully verified and saved" in out.lower()

    token, _, _ = load_kse_credentials()
    assert token == "valid.jwt.token"


@responses.activate
def test_cmd_login_kse_native_webview_success(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_REFRESH_TOKEN", "")

    monkeypatch.setattr(
        kse_auth,
        "login_kse_webview",
        lambda: ("webview.captured.token", "webview-refresh-token", "webview-sess-1", "Test Student"),
    )
    responses.add(responses.GET, KSE_SCHEDULE_VERIFY_URL, json={"groups": []}, status=200)

    exit_code = _cmd_login_kse(argparse.Namespace(manual=False, clipboard=False))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "successfully received kse credentials via native web login" in out.lower()

    token, refresh, sess = load_kse_credentials()
    assert token == "webview.captured.token"
    assert refresh == "webview-refresh-token"
    assert sess == "webview-sess-1"


@responses.activate
def test_cmd_login_kse_1click_clipboard_sync(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")
    monkeypatch.setenv("DEADLINER_KSE_REFRESH_TOKEN", "")

    # Native webview unavailable -> falls back to clipboard
    monkeypatch.setattr(kse_auth, "login_kse_webview", lambda: None)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(
        kse_auth,
        "login_kse_clipboard_sync",
        lambda: ("browser.captured.token", "browser-refresh-token", "browser-sess-1", "Test Student"),
    )
    responses.add(responses.GET, KSE_SCHEDULE_VERIFY_URL, json={"groups": []}, status=200)

    exit_code = _cmd_login_kse(argparse.Namespace(manual=False, clipboard=False))
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "successfully received kse credentials from clipboard" in out.lower()

    token, refresh, sess = load_kse_credentials()
    assert token == "browser.captured.token"
    assert refresh == "browser-refresh-token"
    assert sess == "browser-sess-1"


def test_login_kse_webview_not_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "webview", None)
    creds = kse_auth.login_kse_webview()
    assert creds is None


def test_login_kse_webview_lifecycle_mocked(monkeypatch):
    import types

    fake_window = types.SimpleNamespace(
        evaluate_js=lambda expr: json.dumps({
            "user": {
                "token": "wv.tok.jwt",
                "refreshToken": "wv-ref",
                "sessionId": "wv-sess",
                "profile": {"name": "Vadym Katsel"},
            }
        }),
        destroy=lambda: None,
    )

    class FakeWebview:
        Window = types.SimpleNamespace
        settings = {}

        @staticmethod
        def create_window(*args, **kwargs):
            return fake_window

        @staticmethod
        def start(func, window, *args, **kwargs):
            func(window)

    monkeypatch.setitem(sys.modules, "webview", FakeWebview)

    creds = kse_auth.login_kse_webview(timeout=5)
    assert creds is not None
    assert creds[0] == "wv.tok.jwt"
    assert creds[1] == "wv-ref"
    assert creds[2] == "wv-sess"
    assert creds[3] == "Vadym Katsel"


def test_extract_credentials_from_json():
    payload = {
        "user": {
            "token": "hdr.pay.sig",
            "refreshToken": "ref-123",
            "sessionId": "sess-456",
            "profile": {"name": "Taras Shevchenko"},
        }
    }
    creds = kse_auth._extract_credentials_from_text(json.dumps(payload))
    assert creds is not None
    assert creds == ("hdr.pay.sig", "ref-123", "sess-456", "Taras Shevchenko")


def test_extract_credentials_from_raw_jwt():
    creds = kse_auth._extract_credentials_from_text("eyJhbGciOi.payload.signature")
    assert creds is not None
    assert creds == ("eyJhbGciOi.payload.signature", "", "", "")


def test_extract_credentials_invalid():
    assert kse_auth._extract_credentials_from_text("not-a-token") is None
    assert kse_auth._extract_credentials_from_text("") is None
