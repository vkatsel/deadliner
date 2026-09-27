import os
from pathlib import Path
import sys
import pytest

from deadliner import path_util


def test_is_on_path_true(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/deadliner")
    assert path_util.is_on_path() is True


def test_is_on_path_false(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    assert path_util.is_on_path() is False


def test_find_deadliner_executable_via_which(monkeypatch, tmp_path):
    fake_exe = tmp_path / "deadliner.exe"
    fake_exe.write_text("")
    monkeypatch.setattr("shutil.which", lambda cmd: str(fake_exe))
    found = path_util.find_deadliner_executable()
    assert found == fake_exe


def test_find_deadliner_executable_fallback_scripts(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    fake_exe = scripts_dir / ("deadliner.exe" if sys.platform == "win32" else "deadliner")
    fake_exe.write_text("")

    fake_py = tmp_path / "python.exe"
    monkeypatch.setattr("sys.executable", str(fake_py))

    found = path_util.find_deadliner_executable()
    assert found == fake_exe


def test_add_to_path_unix(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    home_dir = tmp_path / "userhome"
    home_dir.mkdir()
    bashrc = home_dir / ".bashrc"
    bashrc.write_text("# existing bashrc\n")

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)

    target_dir = tmp_path / "bin"
    target_dir.mkdir()
    fake_exe = target_dir / "deadliner"
    fake_exe.write_text("")
    monkeypatch.setattr(path_util, "find_deadliner_executable", lambda: fake_exe)

    success, msg = path_util.add_to_path()
    assert success is True
    assert str(target_dir) in bashrc.read_text()


def test_add_to_path_windows_mocked(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Windows")

    fake_reg_data = {"Path": "C:\\Existing\\Path"}

    class FakeWinreg:
        HKEY_CURRENT_USER = "HKCU"
        KEY_READ = 1
        KEY_WRITE = 2
        REG_EXPAND_SZ = 3

        @staticmethod
        def OpenKey(key, sub_key, reserved=0, access=0):
            return "fake_handle"

        @staticmethod
        def QueryValueEx(handle, name):
            if name in fake_reg_data:
                return fake_reg_data[name], FakeWinreg.REG_EXPAND_SZ
            raise FileNotFoundError()

        @staticmethod
        def SetValueEx(handle, name, reserved, reg_type, val):
            fake_reg_data[name] = val

        @staticmethod
        def CloseKey(handle):
            pass

    monkeypatch.setattr(path_util, "winreg", FakeWinreg)

    target_dir = tmp_path / "Scripts"
    target_dir.mkdir()
    fake_exe = target_dir / "deadliner.exe"
    fake_exe.write_text("")
    monkeypatch.setattr(path_util, "find_deadliner_executable", lambda: fake_exe)
    monkeypatch.setattr(path_util, "_broadcast_windows_environment_change", lambda: None)

    success, msg = path_util.add_to_path()
    assert success is True
    assert str(target_dir) in fake_reg_data["Path"]
    assert "C:\\Existing\\Path" in fake_reg_data["Path"]


def test_add_to_path_already_present(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    home_dir = tmp_path / "userhome"
    home_dir.mkdir()
    bashrc = home_dir / ".bashrc"

    target_dir = tmp_path / "bin"
    target_dir.mkdir()
    fake_exe = target_dir / "deadliner"
    fake_exe.write_text("")
    bashrc.write_text(f'export PATH="{target_dir}:$PATH"\n')

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr(path_util, "find_deadliner_executable", lambda: fake_exe)

    success, msg = path_util.add_to_path()
    assert success is True
    assert "already" in msg.lower()


def test_check_and_prompt_path_setup_not_tty(monkeypatch):
    from deadliner import cli

    called = False

    def fake_add():
        nonlocal called
        called = True
        return True, "ok"

    monkeypatch.setattr(path_util, "is_on_path", lambda: False)
    monkeypatch.setattr(path_util, "add_to_path", fake_add)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    cli._check_and_prompt_path_setup()
    assert called is False


def test_check_and_prompt_path_setup_already_on_path(monkeypatch):
    from deadliner import cli

    called = False

    def fake_add():
        nonlocal called
        called = True
        return True, "ok"

    monkeypatch.setattr(path_util, "is_on_path", lambda: True)
    monkeypatch.setattr(path_util, "add_to_path", fake_add)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    cli._check_and_prompt_path_setup()
    assert called is False


def test_check_and_prompt_path_setup_user_accepts(monkeypatch):
    from deadliner import cli

    called = False

    def fake_add():
        nonlocal called
        called = True
        return True, "Added successfully"

    monkeypatch.setattr(path_util, "is_on_path", lambda: False)
    monkeypatch.setattr(path_util, "add_to_path", fake_add)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")

    cli._check_and_prompt_path_setup()
    assert called is True


def test_check_and_prompt_path_setup_user_declines(monkeypatch):
    from deadliner import cli

    called = False

    def fake_add():
        nonlocal called
        called = True
        return True, "Added successfully"

    monkeypatch.setattr(path_util, "is_on_path", lambda: False)
    monkeypatch.setattr(path_util, "add_to_path", fake_add)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    cli._check_and_prompt_path_setup()
    assert called is False
