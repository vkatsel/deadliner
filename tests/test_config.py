import json
from datetime import datetime, timezone
import pytest

from deadliner import cli
from deadliner.models import Assignment


def test_is_classroom_sync_enabled_default_true(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)

    # Config file does not exist -> defaults to True
    assert cli.is_classroom_sync_enabled() is True

    # Config file exists but has no sync_classroom key -> defaults to True
    test_cfg.write_text(json.dumps({"moodle_token": "abc"}))
    assert cli.is_classroom_sync_enabled() is True

    # When passing explicit cfg dict without key -> True
    assert cli.is_classroom_sync_enabled({}) is True
    assert cli.is_classroom_sync_enabled({"other": 123}) is True


def test_is_classroom_sync_enabled_explicit_values(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)

    test_cfg.write_text(json.dumps({"sync_classroom": False}))
    assert cli.is_classroom_sync_enabled() is False

    test_cfg.write_text(json.dumps({"sync_classroom": True}))
    assert cli.is_classroom_sync_enabled() is True

    assert cli.is_classroom_sync_enabled({"sync_classroom": False}) is False
    assert cli.is_classroom_sync_enabled({"sync_classroom": True}) is True


def test_set_classroom_sync_enabled_persists(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)

    # Starts with existing credentials
    test_cfg.write_text(json.dumps({"moodle_token": "my-token", "google_access_token": "g-token"}))

    cli.set_classroom_sync_enabled(False)
    saved = json.loads(test_cfg.read_text())
    assert saved["sync_classroom"] is False
    assert saved["moodle_token"] == "my-token"
    assert saved["google_access_token"] == "g-token"
    assert cli.is_classroom_sync_enabled() is False

    cli.set_classroom_sync_enabled(True)
    saved = json.loads(test_cfg.read_text())
    assert saved["sync_classroom"] is True
    assert cli.is_classroom_sync_enabled() is True


def test_cli_config_classroom_off(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)

    with pytest.raises(SystemExit) as exc:
        cli.main(["config", "classroom", "off"])
    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert "Google Classroom sync disabled." in out
    assert cli.is_classroom_sync_enabled() is False

    saved = json.loads(test_cfg.read_text())
    assert saved["sync_classroom"] is False


def test_cli_config_classroom_on(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)
    cli.set_classroom_sync_enabled(False)

    with pytest.raises(SystemExit) as exc:
        cli.main(["config", "classroom", "on"])
    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert "Google Classroom sync enabled." in out
    assert cli.is_classroom_sync_enabled() is True

    saved = json.loads(test_cfg.read_text())
    assert saved["sync_classroom"] is True


def test_cli_config_classroom_status(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)

    # Status without argument (default enabled)
    with pytest.raises(SystemExit) as exc:
        cli.main(["config", "classroom"])
    assert exc.value.code == 0
    assert "Google Classroom sync is currently: ENABLED" in capsys.readouterr().out

    # Disable and check status via 'status' arg
    cli.set_classroom_sync_enabled(False)
    with pytest.raises(SystemExit) as exc:
        cli.main(["config", "classroom", "status"])
    assert exc.value.code == 0
    assert "Google Classroom sync is currently: DISABLED" in capsys.readouterr().out


def test_collect_assignments_skips_classroom_when_disabled(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)
    cli.set_classroom_sync_enabled(False)

    from deadliner import classroom_fetcher, moodle_fetcher

    classroom_called = False

    def mock_classroom(creds):
        nonlocal classroom_called
        classroom_called = True
        return []

    monkeypatch.setattr(classroom_fetcher, "fetch_classroom", mock_classroom)
    monkeypatch.setattr(moodle_fetcher, "fetch_moodle", lambda u, t: [])

    assignments, warnings = cli._collect_assignments("https://moodle.example.com", "tok", "g-tok")
    assert classroom_called is False
    assert assignments == []


def test_collect_assignments_calls_classroom_when_enabled(tmp_path, monkeypatch):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)
    cli.set_classroom_sync_enabled(True)

    from deadliner import classroom_fetcher, moodle_fetcher

    classroom_called = False
    fake_assignment = Assignment(
        platform="classroom",
        course_shortname="Math",
        title="Homework 1",
        due_utc=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        url="https://classroom.google.com/c/1",
    )

    def mock_classroom(creds):
        nonlocal classroom_called
        classroom_called = True
        return [fake_assignment]

    monkeypatch.setattr(classroom_fetcher, "fetch_classroom", mock_classroom)
    monkeypatch.setattr(moodle_fetcher, "fetch_moodle", lambda u, t: [])

    assignments, warnings = cli._collect_assignments("https://moodle.example.com", "tok", "g-tok")
    assert classroom_called is True
    assert assignments == [fake_assignment]


def test_cli_fetch_honors_sync_classroom_false(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)
    cli.set_classroom_sync_enabled(False)

    monkeypatch.setattr(
        cli, "_load_credentials", lambda: ("https://moodle.example.com", "m-tok", "g-tok", "")
    )

    from deadliner import classroom_fetcher, moodle_fetcher

    classroom_called = False

    def mock_classroom(creds):
        nonlocal classroom_called
        classroom_called = True
        return []

    moodle_assignment = Assignment(
        platform="moodle",
        course_shortname="CS101",
        title="Project 1",
        due_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        url="https://moodle.example.com/1",
    )

    monkeypatch.setattr(classroom_fetcher, "fetch_classroom", mock_classroom)
    monkeypatch.setattr(moodle_fetcher, "fetch_moodle", lambda u, t: [moodle_assignment])

    with pytest.raises(SystemExit) as exc:
        cli.main(["fetch"])
    assert exc.value.code == 0
    assert classroom_called is False
    out = capsys.readouterr().out
    assert "Project 1" in out


def test_cli_sync_honors_sync_classroom_false(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)
    cli.set_classroom_sync_enabled(False)

    monkeypatch.setattr(
        cli, "_load_credentials", lambda: ("https://moodle.example.com", "m-tok", "g-tok", "")
    )

    from deadliner import calendar_sync, classroom_fetcher, moodle_fetcher

    classroom_called = False

    def mock_classroom(creds):
        nonlocal classroom_called
        classroom_called = True
        return []

    moodle_assignment = Assignment(
        platform="moodle",
        course_shortname="CS101",
        title="Project 1",
        due_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        url="https://moodle.example.com/1",
    )

    synced_assignments = []
    def mock_sync(assignments, token):
        synced_assignments.extend(assignments)
        return 1, 0, 0

    monkeypatch.setattr(classroom_fetcher, "fetch_classroom", mock_classroom)
    monkeypatch.setattr(moodle_fetcher, "fetch_moodle", lambda u, t: [moodle_assignment])
    monkeypatch.setattr(calendar_sync, "sync_to_calendar", mock_sync)

    with pytest.raises(SystemExit) as exc:
        cli.main(["sync"])
    assert exc.value.code == 0
    assert classroom_called is False
    assert synced_assignments == [moodle_assignment]
    out = capsys.readouterr().out
    assert "Created:   1" in out


def test_cli_menu_toggle_classroom_sync(tmp_path, monkeypatch, capsys):
    test_cfg = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", test_cfg)

    # Initial state is True (default)
    assert cli.is_classroom_sync_enabled() is True

    # Menu flow: 7 (Configure) -> d (Toggle sync) -> 7 -> d (Toggle back) -> 8 (Exit)
    inputs = iter(["7", "d", "7", "d", "8"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert "Google Classroom sync disabled." in out
    assert "Google Classroom sync enabled." in out
    assert cli.is_classroom_sync_enabled() is True
