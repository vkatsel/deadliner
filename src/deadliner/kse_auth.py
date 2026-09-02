import argparse
import json
import logging
import os
import sys
from pathlib import Path
import requests

from deadliner.models import AuthError

logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".deadliner.json"
KSE_AUTH_REFRESH_URL = "https://api.kse.today/auth/refresh"
KSE_SCHEDULE_VERIFY_URL = "https://api.kse.today/schedule/groups"


def load_kse_credentials() -> tuple[str, str, str]:
    """Read KSE credentials from env vars or ~/.deadliner.json.

    Returns:
        (kse_token, kse_refresh_token, kse_session_id)
    """
    token = os.environ.get("DEADLINER_KSE_TOKEN", "")
    refresh_token = os.environ.get("DEADLINER_KSE_REFRESH_TOKEN", "")
    session_id = os.environ.get("DEADLINER_KSE_SESSION_ID", "")

    if (not token or not refresh_token) and CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except (OSError, ValueError):
            cfg = {}
        token = token or cfg.get("kse_token", "")
        refresh_token = refresh_token or cfg.get("kse_refresh_token", "")
        session_id = session_id or cfg.get("kse_session_id", "")

    return token, refresh_token, session_id


def save_kse_credentials(token: str, refresh_token: str = "", session_id: str = "") -> None:
    """Save KSE credentials into ~/.deadliner.json."""
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except (OSError, ValueError):
            cfg = {}

    cfg["kse_token"] = token
    if refresh_token:
        cfg["kse_refresh_token"] = refresh_token
    if session_id:
        cfg["kse_session_id"] = session_id

    CONFIG_PATH.write_text(json.dumps(cfg, indent=4))


def refresh_kse_token(refresh_token: str, session_id: str = "") -> str | None:
    """Call api.kse.today to refresh the JWT access token.

    Returns:
        New access token, or None if refresh failed.
    """
    if not refresh_token:
        return None

    try:
        response = requests.post(
            KSE_AUTH_REFRESH_URL,
            headers={"Content-Type": "application/json"},
            json={"refresh_token": refresh_token, "session_id": session_id or None},
            timeout=10,
        )
        if response.status_code != 200:
            logger.debug(f"KSE token refresh failed with status {response.status_code}")
            return None

        data = response.json()
        new_token = data.get("token")
        new_refresh = data.get("refresh_token") or refresh_token
        if new_token:
            save_kse_credentials(new_token, new_refresh, session_id)
            return new_token
    except Exception as e:
        logger.debug(f"Error during KSE token refresh: {e}")
        return None

    return None


import time


def is_kse_token_expired(token: str) -> bool:
    """Check if the JWT token is expired or close to expiring (within 60s)."""
    if not token:
        return True
    payload = _decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        return False
    return time.time() >= (exp - 60)


def get_valid_kse_token() -> str:
    """Return a valid KSE token, attempting refresh if expired or missing."""
    token, refresh_token, session_id = load_kse_credentials()
    if (not token or is_kse_token_expired(token)) and refresh_token:
        refreshed = refresh_kse_token(refresh_token, session_id)
        if refreshed:
            return refreshed
    return token


import base64


def _decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            return json.loads(decoded_bytes.decode("utf-8"))
    except Exception:
        pass
    return {}


def _cmd_login_kse(args: argparse.Namespace) -> int:
    """CLI handler for `deadliner login kse`."""
    print("\n" + "=" * 65)
    print("  KSE Schedule Login")
    print("=" * 65)
    print("To connect your KSE Schedule in 10 seconds:")
    print("1. Open https://schedule.kse.ua in your browser (signed in with @kse.org.ua).")
    print("2. Press F12 -> Console.")
    print("3. Paste this command and hit Enter (it copies the token automatically):")
    print("\n   copy(localStorage.getItem(\"__NEXUS_REACT_ADMIN_AUTH__\"))\n")
    print("4. Paste the copied text below.")
    print("=" * 65)

    raw_input_val = input("\nPaste your KSE Token or JSON: ").strip()
    if not raw_input_val:
        print("Error: Token cannot be empty.", file=sys.stderr)
        return 1

    token = raw_input_val
    refresh_token = ""
    session_id = ""
    user_name = ""

    # Check if user pasted the entire localStorage JSON
    if raw_input_val.startswith("{"):
        try:
            parsed = json.loads(raw_input_val)
            user_obj = parsed.get("user", parsed)
            token = user_obj.get("token", token)
            refresh_token = user_obj.get("refreshToken", "")
            session_id = user_obj.get("sessionId", "")
            profile = user_obj.get("profile", {})
            user_name = profile.get("name", "")
        except Exception:
            print("Error: Malformed JSON provided.", file=sys.stderr)
            return 1

    # Validate JWT structure (must contain 2 dots separating header.payload.signature)
    if not isinstance(token, str) or token.count(".") != 2:
        print(
            "Error: Invalid JWT format. Expected a 3-part token (xxx.yyy.zzz) or full localStorage JSON.",
            file=sys.stderr,
        )
        return 1

    payload = _decode_jwt_payload(token)
    email = payload.get("email", "")
    program = payload.get("program", "")

    print("Verifying token with KSE API...")
    try:
        res = requests.get(
            KSE_SCHEDULE_VERIFY_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"search": "test"},
            timeout=10,
        )
        if res.status_code in (401, 403):
            print("Error: The supplied KSE token was rejected (401 Unauthorized).", file=sys.stderr)
            return 1
        elif res.status_code != 200:
            print(f"Error: KSE API returned status {res.status_code}.", file=sys.stderr)
            return 1
    except requests.RequestException as e:
        print(f"Error: Could not connect to KSE API ({e}).", file=sys.stderr)
        return 1

    save_kse_credentials(token, refresh_token, session_id)
    print("\n\033[92mSuccessfully verified and saved KSE credentials to ~/.deadliner.json!\033[0m")
    user_display = user_name or email or "KSE Student"
    details_str = f" ({email})" if email and user_name else ""
    prog_str = f" — Program: {program}" if program else ""
    print(f"Logged in as: \033[1m{user_display}{details_str}\033[0m{prog_str}\n")
    return 0


