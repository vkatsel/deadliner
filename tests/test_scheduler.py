import platform
import pytest

from deadliner import cli, scheduler


def test_get_sync_command_includes_python():
    cmd = scheduler.get_sync_command()
    assert "sync-all" in cmd
    assert "-m deadliner" in cmd


def test_enable_schedule_windows(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    class MockRun:
        returncode = 0
        stdout = "SUCCESS: The scheduled task was successfully created."
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockRun())

    success, msg = scheduler.enable_schedule("08:30")
    assert success is True
    assert "08:30" in msg


def test_disable_schedule_windows(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    class MockRun:
        returncode = 0
        stdout = "SUCCESS: The scheduled task was successfully deleted."
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockRun())

    success, msg = scheduler.disable_schedule()
    assert success is True
    assert "disabled" in msg.lower()


def test_get_schedule_status_windows_enabled(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    class MockRun:
        returncode = 0
        stdout = (
            "TaskName: DeadlinerDailySync\n"
            "Next Run Time: 08:00:00, 04.09.2026\n"
            "Status: Ready\n"
            "Start Time: 08:00\n"
        )
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockRun())

    status = scheduler.get_schedule_status()
    assert status["enabled"] is True
    assert "08:00" in status["next_run"]


def test_get_schedule_status_disabled(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    class MockRun:
        returncode = 1
        stdout = ""
        stderr = "ERROR: The system cannot find the file specified."

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockRun())

    status = scheduler.get_schedule_status()
    assert status["enabled"] is False


def test_cli_cron_enable(monkeypatch, capsys):
    monkeypatch.setattr(scheduler, "enable_schedule", lambda time_str: (True, f"Scheduled for {time_str}"))

    with pytest.raises(SystemExit) as exc:
        cli.main(["cron", "enable", "--time", "09:15"])
    assert exc.value.code == 0
    assert "Scheduled for 09:15" in capsys.readouterr().out


def test_cli_cron_disable(monkeypatch, capsys):
    monkeypatch.setattr(scheduler, "disable_schedule", lambda: (True, "Auto-sync disabled"))

    with pytest.raises(SystemExit) as exc:
        cli.main(["cron", "disable"])
    assert exc.value.code == 0
    assert "Auto-sync disabled" in capsys.readouterr().out


def test_cli_cron_status(monkeypatch, capsys):
    monkeypatch.setattr(scheduler, "get_schedule_status", lambda: {"enabled": True, "next_run": "Tomorrow 08:00"})

    with pytest.raises(SystemExit) as exc:
        cli.main(["cron", "status"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "ENABLED" in out
    assert "Tomorrow 08:00" in out


def test_cli_sync_all(monkeypatch):
    synced = []
    monkeypatch.setattr(cli, "_cmd_sync", lambda args: (synced.append("deadlines"), 0)[1])
    monkeypatch.setattr(cli, "_cmd_schedule_sync", lambda args: (synced.append("schedule"), 0)[1])

    with pytest.raises(SystemExit) as exc:
        cli.main(["sync-all"])
    assert exc.value.code == 0
    assert synced == ["deadlines", "schedule"]
