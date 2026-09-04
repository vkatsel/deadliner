"""Google OAuth2 flow for Classroom (read) + Calendar (write) access.

Handles:
- First-time authorization (browser-based consent)
- Token storage (credentials file with access + refresh tokens)
- Token refresh on expiry (called by _load_credentials before any API call)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import warnings

# Relax strict scope matching because Google sometimes returns slightly different scopes
# (e.g. classroom.student-submissions.me.readonly instead of coursework)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
warnings.filterwarnings("ignore", message=".*missing scopes.*")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes: read Classroom coursework + read/write Calendar events
SCOPES = [
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

# Default paths
_DEFAULT_CLIENT_SECRETS = "client_secret.json"  # downloaded from Google Cloud Console
_DEFAULT_TOKEN_PATH = ".deadliner_google_token.json"


def get_token_path() -> Path:
    """Return the path where Google OAuth tokens are stored."""
    return Path.home() / _DEFAULT_TOKEN_PATH


def find_client_secrets_path(explicit_path: str | Path | None = None) -> Path | None:
    """Find client_secret.json across common locations or return None."""
    if explicit_path:
        p = Path(explicit_path)
        return p if p.is_file() else None

    env_path = os.environ.get("DEADLINER_CLIENT_SECRETS") or os.environ.get("GOOGLE_CLIENT_SECRETS")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    candidates = [
        Path.home() / ".deadliner" / "client_secret.json",
        Path.cwd() / "client_secret.json",
        Path(__file__).resolve().parent.parent.parent / "client_secret.json",
        Path.home() / "client_secret.json",
    ]

    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def run_oauth_flow(client_secrets_path: str | None = None) -> Credentials:
    """Run the full interactive OAuth2 flow (opens browser).

    Args:
        client_secrets_path: path to client_secret.json from Google Cloud Console.

    Returns:
        Authorized Credentials object.

    Raises:
        FileNotFoundError: if client_secrets_path does not exist.
    """
    secrets = find_client_secrets_path(client_secrets_path)
    if not secrets:
        target = client_secrets_path or _DEFAULT_CLIENT_SECRETS
        raise FileNotFoundError(
            f"Google client secrets file not found at {target}. "
            f"Download it from Google Cloud Console → APIs & Services → Credentials "
            f"and place it in ~/.deadliner/client_secret.json or in the project root."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    try:
        creds = flow.run_local_server(port=0)  # opens browser, runs local redirect
    except KeyboardInterrupt:
        raise

    _save_token(creds)
    return creds


def load_google_credentials() -> Credentials | None:
    """Load stored Google credentials, refreshing if expired.

    Returns:
        Valid Credentials object, or None if no stored token exists.
        Automatically refreshes expired tokens using the stored refresh_token.
    """
    token_path = get_token_path()
    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except (json.JSONDecodeError, ValueError, KeyError):
        return None

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)  # persist the new access token
            return creds
        except Exception:
            return None  # refresh failed — user must re-login

    return None


def is_google_authenticated() -> bool:
    """Check if valid Google credentials exist (without triggering a flow)."""
    return load_google_credentials() is not None


def _save_token(creds: Credentials) -> None:
    """Persist credentials to the token file."""
    token_path = get_token_path()
    token_path.write_text(creds.to_json())
