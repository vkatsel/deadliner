import pytest

from deadliner import cli
from deadliner.models import AuthError


def test_cli_continues_on_moodle_auth_error(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("https://moodle.example.com", "tok", ""))

    def _raise_auth_error(base_url, token):
        raise AuthError("token rejected")

    monkeypatch.setattr(cli.moodle_fetcher, "fetch_moodle", _raise_auth_error)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["fetch"])

    assert exc_info.value.code == 0, "auth failure must not crash the app, but continue"


def test_cli_continues_on_moodle_connection_error(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("https://moodle.example.com", "tok", ""))

    def _raise_connection_error(base_url, token):
        raise ConnectionError("Failed to connect to Moodle")

    monkeypatch.setattr(cli.moodle_fetcher, "fetch_moodle", _raise_connection_error)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["fetch"])

    assert exc_info.value.code == 0


def test_cli_exits_nonzero_when_credentials_missing(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("", "", ""))

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["fetch"])

    assert exc_info.value.code != 0


def test_cli_sync_requires_google_token(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("https://moodle.example.com", "tok", ""))

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["sync"])

    assert exc_info.value.code != 0, "sync without Google credentials must exit non-zero"


def test_cli_sync_pushes_fetched_assignments(monkeypatch, capsys):
    from datetime import datetime, timezone

    from deadliner.models import Assignment

    monkeypatch.setattr(cli, "_load_credentials", lambda: ("https://moodle.example.com", "tok", "g-tok"))

    a = Assignment("moodle", "CS101", "Lab 1", datetime(2026, 7, 10, 21, 0, tzinfo=timezone.utc), "https://m/1")
    monkeypatch.setattr(cli, "_collect_assignments", lambda *args: ([a], []))

    from deadliner import calendar_sync

    synced = []
    monkeypatch.setattr(
        calendar_sync, "sync_to_calendar", lambda assignments, token: (synced.extend(assignments), (1, 0))[1]
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["sync"])

    assert exc_info.value.code == 0
    assert synced == [a], "sync must push exactly the fetched assignments"
    assert "1 created" in capsys.readouterr().out
