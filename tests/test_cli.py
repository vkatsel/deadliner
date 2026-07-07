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
