import argparse
import json
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


def test_get_valid_kse_token_falls_back_to_refresh(monkeypatch):
    monkeypatch.setattr(kse_auth, "load_kse_credentials", lambda: ("", "refresh-abc", "sess-1"))
    monkeypatch.setattr(kse_auth, "refresh_kse_token", lambda r, s: "refreshed-jwt")

    token = get_valid_kse_token()
    assert token == "refreshed-jwt"


def test_cmd_login_kse_invalid_token_format(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "/")
    exit_code = _cmd_login_kse(argparse.Namespace())
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "invalid jwt format" in err.lower()


@responses.activate
def test_cmd_login_kse_rejected_by_api(monkeypatch, capsys):
    responses.add(responses.GET, KSE_SCHEDULE_VERIFY_URL, json={"error": "unauthorized"}, status=401)
    monkeypatch.setattr("builtins.input", lambda prompt: "header.payload.signature")

    exit_code = _cmd_login_kse(argparse.Namespace())
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

    exit_code = _cmd_login_kse(argparse.Namespace())
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "successfully verified and saved" in out.lower()

    token, _, _ = load_kse_credentials()
    assert token == "valid.jwt.token"
