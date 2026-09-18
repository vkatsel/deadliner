"""Utility to detect and configure system PATH for Deadliner.

Ensures users can run `deadliner` from any directory or terminal window
without needing manual environment variable editing.
"""

from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import site
import sys

try:
    import winreg
except ImportError:
    winreg = None


def is_on_path() -> bool:
    """Check if the `deadliner` executable is currently resolvable in PATH."""
    exe_name = "deadliner.exe" if platform.system().lower() == "windows" else "deadliner"
    found = shutil.which("deadliner") or shutil.which(exe_name)
    if not found:
        return False

    # On Windows, shutil.which checks cwd. Ensure it's in PATH or cwd is in PATH
    try:
        found_path = Path(found).resolve()
        cwd = Path.cwd().resolve()
        if found_path.parent == cwd:
            env_paths = [Path(d).resolve() for d in os.environ.get("PATH", "").split(os.pathsep) if d.strip()]
            if cwd not in env_paths:
                path_match = shutil.which(exe_name, path=os.environ.get("PATH", ""))
                return path_match is not None
    except Exception:
        pass

    return True


def find_deadliner_executable() -> Path | None:
    """Find the deadliner executable or fallback script location."""
    exe_name = "deadliner.exe" if platform.system().lower() == "windows" else "deadliner"

    found = shutil.which("deadliner") or shutil.which(exe_name)
    if found:
        return Path(found).resolve()

    # Candidate 1: Python environment Scripts or bin folder
    py_dir = Path(sys.executable).resolve().parent
    candidates = [
        py_dir / "Scripts" / exe_name,
        py_dir / "Scripts" / "deadliner",
        py_dir / "bin" / exe_name,
        py_dir / "bin" / "deadliner",
        py_dir / exe_name,
        py_dir / "deadliner",
    ]

    # Candidate 2: User site-packages bin / Scripts folder
    try:
        user_base = Path(site.getuserbase()).resolve()
        candidates.extend([
            user_base / "Scripts" / exe_name,
            user_base / "bin" / "deadliner",
        ])
    except Exception:
        pass

    # Candidate 3: Current project directory (deadliner.bat / deadliner)
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidates.extend([
        repo_root / "deadliner.bat",
        repo_root / "deadliner",
    ])

    for cand in candidates:
        if cand.is_file():
            return cand

    return None


def _broadcast_windows_environment_change() -> None:
    """Broadcast WM_SETTINGCHANGE message on Windows so new consoles pick up the updated PATH."""
    try:
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002

        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            5000,
            None,
        )
    except Exception:
        pass


def add_to_path() -> tuple[bool, str]:
    """Add Deadliner's directory to the user's permanent environment PATH.

    Returns:
        (success: bool, message: str)
    """
    exe_path = find_deadliner_executable()
    if not exe_path:
        return False, "Could not locate the deadliner executable. Please install deadliner via pip first."

    target_dir = str(exe_path.parent.resolve())
    system = platform.system().lower()

    if system == "windows":
        if not winreg:
            return False, "Windows registry module is unavailable."

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE,
            )
            try:
                current_path, reg_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path, reg_type = "", winreg.REG_EXPAND_SZ

            path_entries = [p.strip() for p in current_path.split(";") if p.strip()]

            # Case-insensitive comparison for Windows paths
            if any(p.lower() == target_dir.lower() for p in path_entries):
                winreg.CloseKey(key)
                return True, f"'{target_dir}' is already in your User PATH."

            new_path = f"{current_path};{target_dir}" if current_path else target_dir
            winreg.SetValueEx(key, "Path", 0, reg_type, new_path)
            winreg.CloseKey(key)

            # Update current running process PATH as well
            os.environ["PATH"] = f"{os.environ.get('PATH', '')}{os.pathsep}{target_dir}"

            _broadcast_windows_environment_change()
            return (
                True,
                f"Successfully added '{target_dir}' to your Windows User PATH.\n"
                "Please restart your terminal or open a new window to use the `deadliner` command anywhere.",
            )
        except Exception as e:
            return False, f"Failed to modify Windows User PATH: {e}"

    else:
        # Linux / macOS: append to ~/.bashrc and/or ~/.zshrc
        home = Path.home()
        export_line = f'export PATH="{target_dir}:$PATH"\n'
        modified_files = []

        targets = [home / ".bashrc", home / ".zshrc"]
        found_existing = False

        for conf in targets:
            if conf.exists():
                content = conf.read_text(encoding="utf-8")
                if target_dir in content:
                    found_existing = True
                    continue
                with conf.open("a", encoding="utf-8") as f:
                    f.write(f"\n# Added by Deadliner\n{export_line}")
                modified_files.append(str(conf))

        if not modified_files and not found_existing:
            # If neither existed, create ~/.bashrc
            default_conf = home / ".bashrc"
            default_conf.write_text(f"# Added by Deadliner\n{export_line}", encoding="utf-8")
            modified_files.append(str(default_conf))

        if found_existing and not modified_files:
            return True, f"'{target_dir}' is already configured in your shell profile."

        # Update current process PATH
        os.environ["PATH"] = f"{target_dir}{os.pathsep}{os.environ.get('PATH', '')}"

        files_str = ", ".join(modified_files)
        return (
            True,
            f"Successfully added '{target_dir}' to {files_str}.\n"
            f"Run `source {modified_files[0]}` or open a new terminal window to use `deadliner` anywhere.",
        )
