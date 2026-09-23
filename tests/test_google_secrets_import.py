import json
from pathlib import Path
import pytest

from deadliner import google_auth


def test_parse_client_secrets_standard_installed():
    raw = json.dumps({
        "installed": {
            "client_id": "test-client-id.apps.googleusercontent.com",
            "client_secret": "test-client-secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    })
    res = google_auth.parse_client_secrets(raw)
    assert "installed" in res
    assert res["installed"]["client_id"] == "test-client-id.apps.googleusercontent.com"
    assert res["installed"]["client_secret"] == "test-client-secret"
    assert res["installed"]["auth_uri"] == "https://accounts.google.com/o/oauth2/auth"


def test_parse_client_secrets_web_config():
    raw = json.dumps({
        "web": {
            "client_id": "web-id.apps.googleusercontent.com",
            "client_secret": "web-secret",
        }
    })
    res = google_auth.parse_client_secrets(raw)
    assert "installed" in res
    assert res["installed"]["client_id"] == "web-id.apps.googleusercontent.com"
    assert res["installed"]["client_secret"] == "web-secret"


def test_parse_client_secrets_flat_dict():
    data = {
        "client_id": "flat-id.apps.googleusercontent.com",
        "client_secret": "flat-secret",
    }
    res = google_auth.parse_client_secrets(data)
    assert res["installed"]["client_id"] == "flat-id.apps.googleusercontent.com"
    assert res["installed"]["client_secret"] == "flat-secret"


def test_parse_client_secrets_markdown_fenced():
    raw = "```json\n" + json.dumps({
        "installed": {
            "client_id": "fenced-id",
            "client_secret": "fenced-secret",
        }
    }) + "\n```"
    res = google_auth.parse_client_secrets(raw)
    assert res["installed"]["client_id"] == "fenced-id"


def test_parse_client_secrets_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        google_auth.parse_client_secrets("{not valid json}")


def test_parse_client_secrets_missing_fields():
    with pytest.raises(ValueError, match="required"):
        google_auth.parse_client_secrets(json.dumps({"installed": {"other": "value"}}))


def test_construct_client_secrets_from_keys():
    res = google_auth.construct_client_secrets_from_keys("my-id", "my-secret")
    assert res["installed"]["client_id"] == "my-id"
    assert res["installed"]["client_secret"] == "my-secret"


def test_construct_client_secrets_from_keys_empty():
    with pytest.raises(ValueError, match="non-empty"):
        google_auth.construct_client_secrets_from_keys("", "my-secret")


def test_save_client_secrets_json(tmp_path):
    target = tmp_path / "subdir" / "client_secret.json"
    saved = google_auth.save_client_secrets_json(
        {"client_id": "id123", "client_secret": "sec123"},
        target_path=target,
    )
    assert saved == target
    assert target.is_file()
    loaded = json.loads(target.read_text())
    assert loaded["installed"]["client_id"] == "id123"
    assert loaded["installed"]["client_secret"] == "sec123"


def test_run_oauth_flow_uses_fallback_config(monkeypatch, tmp_path):
    monkeypatch.setattr(google_auth, "find_client_secrets_path", lambda path=None: None)
    monkeypatch.setattr(google_auth, "DEFAULT_CLIENT_ID", "default-cid")
    monkeypatch.setattr(google_auth, "DEFAULT_CLIENT_SECRET", "default-csec")

    token_path = tmp_path / "token.json"
    monkeypatch.setattr(google_auth, "get_token_path", lambda: token_path)

    captured_config = {}

    class FakeCreds:
        token = "fake-default-token"
        refresh_token = "fake-refresh"
        valid = True
        expired = False

        def to_json(self):
            return json.dumps({"token": self.token, "refresh_token": self.refresh_token})

    class FakeFlow:
        @classmethod
        def from_client_config(cls, client_config, scopes):
            captured_config.update(client_config)
            return cls()

        def run_local_server(self, port=0):
            return FakeCreds()

    monkeypatch.setattr(google_auth, "InstalledAppFlow", FakeFlow)

    creds = google_auth.run_oauth_flow()
    assert creds.token == "fake-default-token"
    assert captured_config["installed"]["client_id"] == "default-cid"
    assert token_path.is_file()


def test_interactive_setup_paste_json(monkeypatch, tmp_path):
    from deadliner import cli

    target_secrets = tmp_path / ".deadliner" / "client_secret.json"
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    json_payload = json.dumps({
        "installed": {
            "client_id": "pasted-id",
            "client_secret": "pasted-secret",
        }
    })

    # Choice 1 (Paste JSON) -> JSON lines -> blank line to finish
    inputs = iter(["1", json_payload, ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    res = cli._interactive_setup_client_secrets()
    assert res is True
    assert target_secrets.is_file()
    saved = json.loads(target_secrets.read_text())
    assert saved["installed"]["client_id"] == "pasted-id"


def test_interactive_setup_manual_keys(monkeypatch, tmp_path):
    from deadliner import cli

    target_secrets = tmp_path / ".deadliner" / "client_secret.json"
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Choice 3 (Manual keys) -> Client ID -> Client Secret
    inputs = iter(["3", "manual-client-id", "manual-client-secret"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    res = cli._interactive_setup_client_secrets()
    assert res is True
    assert target_secrets.is_file()
    saved = json.loads(target_secrets.read_text())
    assert saved["installed"]["client_id"] == "manual-client-id"
    assert saved["installed"]["client_secret"] == "manual-client-secret"


def test_interactive_setup_file_path(monkeypatch, tmp_path):
    from deadliner import cli

    source_file = tmp_path / "custom_secret.json"
    source_file.write_text(json.dumps({"installed": {"client_id": "file-id", "client_secret": "file-sec"}}))

    target_secrets = tmp_path / ".deadliner" / "client_secret.json"
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Choice 2 (File path) -> path string
    inputs = iter(["2", str(source_file)])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    res = cli._interactive_setup_client_secrets()
    assert res is True
    assert target_secrets.is_file()
    saved = json.loads(target_secrets.read_text())
    assert saved["installed"]["client_id"] == "file-id"


def test_cli_menu_import_secrets_flow(monkeypatch, tmp_path):
    from deadliner import cli

    target_secrets = tmp_path / ".deadliner" / "client_secret.json"
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Flow: 7 (Settings) -> e (Import Secrets) -> 3 (Manual keys) -> id -> sec -> 8 (Exit menu)
    inputs = iter(["7", "e", "3", "menu-id", "menu-sec", "8"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 0
    assert target_secrets.is_file()
    saved = json.loads(target_secrets.read_text())
    assert saved["installed"]["client_id"] == "menu-id"

