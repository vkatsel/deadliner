import json

import pytest

from deadliner import google_auth


# ---------------------------------------------------------------------------
# run_oauth_flow
# ---------------------------------------------------------------------------


def test_run_oauth_flow_raises_when_secrets_missing(tmp_path):
    missing = str(tmp_path / "does_not_exist.json")
    with pytest.raises(FileNotFoundError, match="not found"):
        google_auth.run_oauth_flow(missing)


def test_run_oauth_flow_calls_installed_app_flow(monkeypatch, tmp_path):
    secrets_file = tmp_path / "client_secret.json"
    secrets_file.write_text("{}")

    token_path = tmp_path / "token.json"
    monkeypatch.setattr(google_auth, "get_token_path", lambda: token_path)

    class FakeCreds:
        token = "fake-access-token"
        refresh_token = "fake-refresh-token"
        valid = True
        expired = False

        def to_json(self):
            return json.dumps({"token": self.token, "refresh_token": self.refresh_token})

    class FakeFlow:
        @staticmethod
        def from_client_secrets_file(path, scopes):
            return FakeFlow()

        def run_local_server(self, port=0):
            return FakeCreds()

    monkeypatch.setattr(google_auth, "InstalledAppFlow", FakeFlow)

    creds = google_auth.run_oauth_flow(str(secrets_file))
    assert creds.token == "fake-access-token"
    assert token_path.exists(), "Token file should be saved after successful flow"


# ---------------------------------------------------------------------------
# load_google_credentials
# ---------------------------------------------------------------------------


def test_load_returns_none_when_no_token_file(monkeypatch, tmp_path):
    monkeypatch.setattr(google_auth, "get_token_path", lambda: tmp_path / "missing.json")
    assert google_auth.load_google_credentials() is None


def test_load_returns_none_on_corrupt_token_file(monkeypatch, tmp_path):
    bad_file = tmp_path / "token.json"
    bad_file.write_text("not valid json {{{{")
    monkeypatch.setattr(google_auth, "get_token_path", lambda: bad_file)
    assert google_auth.load_google_credentials() is None


def test_load_returns_valid_credentials(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"token": "abc", "refresh_token": "def"}))

    class FakeCreds:
        valid = True
        expired = False
        token = "abc"
        refresh_token = "def"

    monkeypatch.setattr(google_auth, "get_token_path", lambda: token_path)
    monkeypatch.setattr(
        google_auth.Credentials,
        "from_authorized_user_file",
        staticmethod(lambda path, scopes: FakeCreds()),
    )

    result = google_auth.load_google_credentials()
    assert result is not None
    assert result.token == "abc"


def test_load_refreshes_expired_credentials(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"token": "old", "refresh_token": "rr"}))

    class FakeCreds:
        valid = False
        expired = True
        token = "old"
        refresh_token = "rr"

        def refresh(self, request):
            self.token = "refreshed"
            self.valid = True

        def to_json(self):
            return json.dumps({"token": self.token, "refresh_token": self.refresh_token})

    fake = FakeCreds()
    monkeypatch.setattr(google_auth, "get_token_path", lambda: token_path)
    monkeypatch.setattr(
        google_auth.Credentials,
        "from_authorized_user_file",
        staticmethod(lambda path, scopes: fake),
    )
    monkeypatch.setattr(google_auth, "Request", lambda: None)

    result = google_auth.load_google_credentials()
    assert result is not None
    assert result.token == "refreshed"


def test_load_returns_none_when_refresh_fails(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"token": "old", "refresh_token": "rr"}))

    class FakeCreds:
        valid = False
        expired = True
        token = "old"
        refresh_token = "rr"

        def refresh(self, request):
            raise RuntimeError("network error")

    monkeypatch.setattr(google_auth, "get_token_path", lambda: token_path)
    monkeypatch.setattr(
        google_auth.Credentials,
        "from_authorized_user_file",
        staticmethod(lambda path, scopes: FakeCreds()),
    )
    monkeypatch.setattr(google_auth, "Request", lambda: None)

    assert google_auth.load_google_credentials() is None


# ---------------------------------------------------------------------------
# is_google_authenticated
# ---------------------------------------------------------------------------


def test_is_authenticated_true(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"token": "x", "refresh_token": "y"}))

    class FakeCreds:
        valid = True
        expired = False

    monkeypatch.setattr(google_auth, "get_token_path", lambda: token_path)
    monkeypatch.setattr(
        google_auth.Credentials,
        "from_authorized_user_file",
        staticmethod(lambda path, scopes: FakeCreds()),
    )

    assert google_auth.is_google_authenticated() is True


def test_is_authenticated_false_no_token(monkeypatch, tmp_path):
    monkeypatch.setattr(google_auth, "get_token_path", lambda: tmp_path / "nope.json")
    assert google_auth.is_google_authenticated() is False
