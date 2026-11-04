from __future__ import annotations

import html
import logging
from pathlib import Path
import platform
import subprocess

logger = logging.getLogger(__name__)

CREATE_NO_WINDOW = 0x08000000


def get_logo_path() -> Path | None:
    """Locate the Deadliner logo.png asset if available."""
    pkg_logo = Path(__file__).resolve().parent / "assets" / "logo.png"
    if pkg_logo.is_file():
        return pkg_logo

    repo_logo = Path(__file__).resolve().parent.parent.parent / "docs" / "assets" / "logo.png"
    if repo_logo.is_file():
        return repo_logo

    return None


def _notify_windows(title: str, message: str, logo: Path | None) -> bool:
    """Send a native Windows Toast notification that persists in Action Center."""
    safe_title = html.escape(title).replace("'", "''")
    safe_msg = html.escape(message).replace("'", "''")

    image_xml = ""
    reg_icon = ""
    if logo is not None:
        logo_posix = logo.resolve().as_posix()
        logo_win = str(logo.resolve()).replace("'", "''")
        image_xml = f'<image placement="appLogoOverride" src="file:///{html.escape(logo_posix)}"/>'
        reg_icon = f"Set-ItemProperty -Path $RegPath -Name 'IconUri' -Value '{logo_win}' -Force;"

    xml_body = (
        "<toast><visual><binding template=\"ToastGeneric\">"
        f"<text>{safe_title}</text><text>{safe_msg}</text>{image_xml}"
        "</binding></visual></toast>"
    )
    ps_script = (
        "$ErrorActionPreference = 'Stop'; "
        "$AppId = 'Deadliner'; "
        "$RegPath = 'HKCU:\\Software\\Classes\\AppUserModelId\\Deadliner'; "
        "if (-not (Test-Path $RegPath)) { New-Item -Path $RegPath -Force | Out-Null }; "
        "Set-ItemProperty -Path $RegPath -Name 'DisplayName' -Value 'Deadliner' -Force; "
        f"{reg_icon}"
        "$WinRT = 'Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime'; "
        "Invoke-Expression \"[$WinRT] | Out-Null\"; "
        "$XmlRT = 'Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, "
        "ContentType = WindowsRuntime'; "
        "Invoke-Expression \"[$XmlRT] | Out-Null\"; "
        f"$XmlStr = '{xml_body}'; "
        "$XmlDoc = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        "$XmlDoc.LoadXml($XmlStr); "
        "$Toast = [Windows.UI.Notifications.ToastNotification]::new($XmlDoc); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($Toast);"
    )

    is_win = hasattr(subprocess, "CREATE_NO_WINDOW") or platform.system().lower() == "windows"
    res = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_script],
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW if is_win else 0,
    )
    return res.returncode == 0


def _notify_macos(title: str, message: str) -> bool:
    """Send a native macOS Notification Center alert via osascript."""
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_msg = message.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "Deadliner" subtitle "{safe_title}" sound name "Basso"'
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return res.returncode == 0


def _notify_linux(title: str, message: str, logo: Path | None) -> bool:
    """Send a native Linux desktop notification via notify-send."""
    cmd = ["notify-send", "-u", "critical", "-a", "Deadliner"]
    if logo is not None:
        cmd.extend(["-i", str(logo.resolve())])
    cmd.extend([title, message])
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0


def notify(title: str, message: str) -> bool:
    """Send a cross-platform desktop notification.

    Never raises exceptions; returns True if the OS notification command succeeded.
    """
    system = platform.system().lower()
    logo = get_logo_path()

    try:
        if system == "windows":
            return _notify_windows(title, message, logo)
        if system == "darwin":
            return _notify_macos(title, message)
        if system == "linux":
            return _notify_linux(title, message, logo)
    except Exception as e:
        logger.debug("Failed to send OS notification: %s", e)

    return False
