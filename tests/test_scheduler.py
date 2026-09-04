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
        stdout = "TaskName: DeadlinerDailySync\nNext Run Time: 08:00:00, 04.09.2026\nStatus: Ready\nStart Time: 08:00\n"
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


def test_enable_schedule_failure(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    class MockRun:
        returncode = 1
        stdout = ""
        stderr = "ERROR: Access is denied."

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockRun())

    success, msg = scheduler.enable_schedule("08:30")
    assert success is False
    assert "Access is denied" in msg


def test_enable_schedule_unix_crontab(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")

    written_crontab = []

    def mock_run(cmd, *args, **kwargs):
        class MockRun:
            returncode = 0
            stdout = "0 7 * * * /usr/bin/some_job\n"
            stderr = ""

        if cmd == ["crontab", "-l"]:
            return MockRun()
        elif cmd == ["crontab", "-"]:
            written_crontab.append(kwargs.get("input", ""))
            return MockRun()
        return MockRun()

    monkeypatch.setattr("subprocess.run", mock_run)

    success, msg = scheduler.enable_schedule("09:45")
    assert success is True
    assert "45 9 * * *" in written_crontab[0]
    assert scheduler.TASK_NAME in written_crontab[0]


def test_disable_schedule_unix_crontab(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")

    written_crontab = []

    def mock_run(cmd, *args, **kwargs):
        class MockRun:
            returncode = 0
            stdout = f"0 7 * * * /usr/bin/some_job\n0 8 * * * deadliner # {scheduler.TASK_NAME}\n"
            stderr = ""

        if cmd == ["crontab", "-l"]:
            return MockRun()
        elif cmd == ["crontab", "-"]:
            written_crontab.append(kwargs.get("input", ""))
            return MockRun()
        return MockRun()

    monkeypatch.setattr("subprocess.run", mock_run)

    success, msg = scheduler.disable_schedule()
    assert success is True
    assert scheduler.TASK_NAME not in written_crontab[0]
    assert "/usr/bin/some_job" in written_crontab[0]


def test_get_schedule_status_unix(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    class MockRun:
        returncode = 0
        stdout = f"0 8 * * * deadliner # {scheduler.TASK_NAME}\n"
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockRun())

    status = scheduler.get_schedule_status()
    assert status["enabled"] is True
    assert scheduler.TASK_NAME in status["cron_entry"]


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


def test_append_sync_log_and_read_logs(tmp_path, monkeypatch):
    log_dir = tmp_path / ".deadliner"
    log_file = log_dir / "sync.log"
    monkeypatch.setattr(scheduler, "DEADLINER_DIR", log_dir)
    monkeypatch.setattr(scheduler, "LOG_FILE", log_file)

    scheduler.append_sync_log("Test log entry 1")
    scheduler.append_sync_log("Test log entry 2")

    logs = scheduler.get_recent_logs()
    assert len(logs) == 2
    assert "Test log entry 1" in logs[0]
    assert "Test log entry 2" in logs[1]


def test_cli_cron_logs_command(monkeypatch, capsys):
    monkeypatch.setattr(
        scheduler,
        "get_recent_logs",
        lambda max_lines=30: ["[2026-09-04 08:00:00] [SYNC-ALL] Completed successfully"],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main(["cron", "logs"])
    assert exc.value.code == 0
    assert "Completed successfully" in capsys.readouterr().out


def test_cli_logs_shortcut_command(monkeypatch, capsys):
    monkeypatch.setattr(
        scheduler,
        "get_recent_logs",
        lambda max_lines=30: ["[2026-09-04 08:00:00] [SYNC-ALL] Completed successfully"],
    )

    with pytest.raises(SystemExit) as exc:
        cli.main(["logs"])
    assert exc.value.code == 0
    assert "Completed successfully" in capsys.readouterr().out


def test_cli_menu_auto_sync_submenu(monkeypatch, capsys):
    inputs = iter(["6", "a", "07:30", "6", "b", "6", "c", "6", "d", "8"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    monkeypatch.setattr(scheduler, "enable_schedule", lambda t: (True, f"Task set for {t}"))
    monkeypatch.setattr(scheduler, "get_schedule_status", lambda: {"enabled": True, "next_run": "07:30"})
    monkeypatch.setattr(
        scheduler, "get_recent_logs", lambda max_lines=30: ["[2026-09-04 07:30:00] [SYNC-ALL] Log test"]
    )
    monkeypatch.setattr(scheduler, "disable_schedule", lambda: (True, "Task disabled"))

    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Task set for 07:30" in out
    assert "Log test" in out
    assert "Task disabled" in out

