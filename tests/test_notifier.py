from __future__ import annotations

import platform
import pytest

from deadliner import cli, notifier, scheduler
from deadliner.models import AuthError


def test_get_logo_path_exists():
    logo = notifier.get_logo_path()
    assert logo is not None
    assert logo.is_file()
    assert logo.name == "logo.png"


def test_notify_windows_toast_xml_and_logo(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    captured = {}

    def mock_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr("subprocess.run", mock_run)

    ok = notifier.notify("Sync <Failed>", "Run 'deadliner login kse' & retry")
    assert ok is True
    cmd = captured["cmd"]
    assert cmd[0] == "powershell"
    ps_script = cmd[-1]
    assert "ToastNotificationManager" in ps_script
    assert "ToastGeneric" in ps_script
    assert "appLogoOverride" in ps_script
    assert "logo.png" in ps_script
    assert "Sync &lt;Failed&gt;" in ps_script
    assert "Run &#x27;deadliner login kse&#x27; &amp; retry" in ps_script
    assert captured["kwargs"].get("creationflags") == notifier.CREATE_NO_WINDOW


def test_notify_macos_osascript(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    captured = {}

    def mock_run(cmd, **kwargs):
        captured["cmd"] = cmd

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr("subprocess.run", mock_run)

    ok = notifier.notify("KSE Schedule Sync Failed", 'Token "expired"')
    assert ok is True
    assert captured["cmd"][0] == "osascript"
    assert 'Token \\"expired\\"' in captured["cmd"][2]
    assert 'subtitle "KSE Schedule Sync Failed"' in captured["cmd"][2]


def test_notify_linux_notify_send_with_icon(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    captured = {}

    def mock_run(cmd, **kwargs):
        captured["cmd"] = cmd

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr("subprocess.run", mock_run)

    ok = notifier.notify("Deadlines Sync Failed", "Moodle connection error")
    assert ok is True
    cmd = captured["cmd"]
    assert cmd[:5] == ["notify-send", "-u", "critical", "-a", "Deadliner"]
    assert "-i" in cmd
    assert cmd[-2:] == ["Deadlines Sync Failed", "Moodle connection error"]


def test_notify_handles_subprocess_exception_gracefully(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    def mock_run(*args, **kwargs):
        raise OSError("powershell not found")

    monkeypatch.setattr("subprocess.run", mock_run)
    assert notifier.notify("Title", "Message") is False


def test_cli_sync_notifies_and_logs_on_moodle_warning(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("https://moodle.example.com", "bad-tok", "g-tok", ""))
    monkeypatch.setattr(
        cli, "_collect_assignments", lambda *args: ([], ["warning: moodle authentication failed: invalid token"])
    )

    notifications = []
    monkeypatch.setattr(notifier, "notify", lambda title, msg: (notifications.append((title, msg)), True)[1])

    with pytest.raises(SystemExit) as exc:
        cli.main(["sync"])

    assert exc.value.code == 1
    assert len(notifications) == 1
    assert "Deadlines Sync Warning" in notifications[0][0]
    assert "moodle authentication failed" in notifications[0][1]

    logs = scheduler.get_recent_logs()
    assert any("[ERROR]" in line and "moodle authentication failed" in line for line in logs)


def test_cli_schedule_sync_notifies_and_logs_on_kse_auth_error(monkeypatch):
    monkeypatch.setattr(cli, "_load_credentials", lambda: ("", "", "g-tok", "expired-kse"))

    from deadliner import kse_fetcher

    def raise_auth(**kwargs):
        raise AuthError("401 Unauthorized")

    monkeypatch.setattr(kse_fetcher, "fetch_kse_schedule", raise_auth)

    notifications = []
    monkeypatch.setattr(notifier, "notify", lambda title, msg: (notifications.append((title, msg)), True)[1])

    with pytest.raises(SystemExit) as exc:
        cli.main(["schedule", "sync"])

    assert exc.value.code == 1
    assert len(notifications) == 1
    assert notifications[0][0] == "KSE Schedule Sync Failed"
    assert "401 Unauthorized" in notifications[0][1]
    assert "deadliner login kse" in notifications[0][1]

    logs = scheduler.get_recent_logs()
    assert any("[ERROR] KSE Schedule Sync Failed" in line and "401 Unauthorized" in line for line in logs)
