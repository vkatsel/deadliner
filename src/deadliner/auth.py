"""Moodle authentication and credential management for Deadliner."""

from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path
import sys

import requests

CONFIG_PATH = Path.home() / ".deadliner.json"
DEFAULT_MOODLE_URL = "https://teaching.kse.org.ua"


def normalize_moodle_url(raw_url: str) -> str:
    """Normalize Moodle URL.

    - Defaults to DEFAULT_MOODLE_URL if raw_url is empty.
    - Prepends 'https://' if no scheme is specified.
    - Strips any trailing slashes.
    """
    cleaned = raw_url.strip()
    if not cleaned:
        return DEFAULT_MOODLE_URL

    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        cleaned = f"https://{cleaned}"

    return cleaned.rstrip("/")


def save_moodle_config(base_url: str, token: str, config_path: Path | None = None) -> bool:
    """Save Moodle credentials into configuration file, preserving existing settings.

    Args:
        base_url: Normalized base URL for Moodle.
        token: Authenticated Moodle web service token.
        config_path: Path to configuration file (defaults to CONFIG_PATH).

    Returns:
        True if credentials were saved successfully, False otherwise.
    """
    target = config_path if config_path is not None else CONFIG_PATH
    cfg: dict = {}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg = loaded
        except (OSError, ValueError):
            cfg = {}

    cfg["moodle_base_url"] = base_url
    cfg["moodle_token"] = token

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
        return True
    except OSError:
        return False


def _cmd_login_moodle(args: argparse.Namespace | None = None) -> int:
    """Interactively log in to Moodle and save credentials to config."""
    print("=== Moodle Login Setup ===")
    raw_url = input(f"Moodle Base URL [{DEFAULT_MOODLE_URL}]: ")
    base_url = normalize_moodle_url(raw_url)

    username = input("Username (your KSE email e.g. name@kse.org.ua or Moodle login): ").strip()
    password = getpass.getpass("Password (your Moodle password, not Google SSO password): ")

    url = f"{base_url}/login/token.php"
    params = {"username": username, "password": password, "service": "moodle_mobile_app"}

    print("Authenticating...")
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(
            "Error: Could not connect to the Moodle server. Please check the Base URL and your internet connection.",
            file=sys.stderr,
        )
        return 1
    except requests.exceptions.Timeout:
        print("Error: Connection to Moodle timed out. Please try again later.", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as e:
        print(
            f"Error: Received a bad response from the server ({e.response.status_code}). "
            "Are you sure this is a Moodle URL?",
            file=sys.stderr,
        )
        return 1
    except requests.RequestException:
        print("Error: An unexpected network error occurred.", file=sys.stderr)
        return 1

    try:
        data = response.json()
    except ValueError:
        print("Error: Moodle returned invalid JSON.", file=sys.stderr)
        return 1

    if "token" in data:
        token = data["token"]
        if save_moodle_config(base_url, token, CONFIG_PATH):
            print("Successfully logged in and saved Moodle token!")
            return 0
        else:
            print(f"Error: Failed to save Moodle credentials to {CONFIG_PATH}.", file=sys.stderr)
            return 1
    else:
        err = data.get("error", "Unknown error")
        err_lower = str(err).lower()
        errorcode = str(data.get("errorcode", "")).lower()
        if (
            "invalid login" in err_lower
            or "wrong username or password" in err_lower
            or errorcode == "invalidlogin"
        ):
            print("Error: Incorrect username or password. Please try again.", file=sys.stderr)
            print(
                "Tip: If you normally sign into Moodle via the Google button on the web, "
                "Moodle requires setting a local password or checking your credentials in Moodle profile settings.",
                file=sys.stderr,
            )
        else:
            print(f"Login failed: {err}", file=sys.stderr)
        return 1
