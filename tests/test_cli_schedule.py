from datetime import datetime, timezone
import pytest

from deadliner import cli
from deadliner.models import AuthError, ScheduleEvent


def _mock_schedule_event():
    return ScheduleEvent(
        event_id="e1",
        discipline="CS400",
        course_name="Languages and Compilers",
        event_type="practice",
        subgroup=1,
        date="2026-09-04",
        period=5,
        start_utc=datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc),
        end_utc=datetime(2026, 9, 4, 13, 20, tzinfo=timezone.utc),
        room="1.08.1",
        shelter="SO1.2",
        teacher="Volodymyr Skochko",
    )


def test_cli_schedule_fetch_success(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("", "", "", "mock-kse-token"))

    from deadliner import kse_fetcher
    monkeypatch.setattr(kse_fetcher, "fetch_kse_schedule", lambda **kwargs: [_mock_schedule_event()])

    with pytest.raises(SystemExit) as exc:
        cli.main(["schedule", "fetch"])

    assert exc.value.code == 0
    captured = capsys.readouterr().out
    assert "Languages and Compilers" in captured
    assert "CS400" in captured
    assert "Volodymyr Skochko" in captured


def test_cli_schedule_fetch_auth_error(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("", "", "", "bad-token"))

    from deadliner import kse_fetcher

    def _raise_auth(*args, **kwargs):
        raise AuthError("token rejected")

    monkeypatch.setattr(kse_fetcher, "fetch_kse_schedule", _raise_auth)

    with pytest.raises(SystemExit) as exc:
        cli.main(["schedule", "fetch"])

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "authentication failed" in err.lower()


def test_cli_schedule_sync_requires_google_token(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("", "", "", "mock-kse-token"))

    with pytest.raises(SystemExit) as exc:
        cli.main(["schedule", "sync"])

    assert exc.value.code != 0


def test_cli_schedule_sync_pushes_events(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("", "", "google-token", "kse-token"))

    from deadliner import calendar_sync, kse_fetcher

    event = _mock_schedule_event()
    monkeypatch.setattr(kse_fetcher, "fetch_kse_schedule", lambda **kwargs: [event])

    synced_events = []
    monkeypatch.setattr(
        calendar_sync,
        "sync_schedule_to_calendar",
        lambda events, token, *args, **kwargs: (synced_events.extend(events), (1, 0, 0, [(event, "created")]))[1],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main(["schedule", "sync"])

    assert exc.value.code == 0
    assert synced_events == [event]
    assert "Created:   1" in capsys.readouterr().out


def test_cli_menu_exit(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "8")
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 0


def test_cli_load_credentials_refreshes_expired_kse_token(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    test_cfg.write_text(
        '{"kse_token": "expired-token", "kse_refresh_token": "refresh-1", "kse_session_id": "sess-1"}'
    )
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)
    monkeypatch.setenv("DEADLINER_KSE_TOKEN", "")

    from deadliner import kse_auth

    monkeypatch.setattr(kse_auth, "CONFIG_PATH", test_cfg)
    monkeypatch.setattr(kse_auth, "is_kse_token_expired", lambda tok: True)
    monkeypatch.setattr(kse_auth, "refresh_kse_token", lambda r, s: "refreshed-fresh-token")

    _, _, _, kse_token = cli._load_credentials()
    assert kse_token == "refreshed-fresh-token"

