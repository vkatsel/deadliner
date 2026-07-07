import getpass
import json
import sys
import requests
import argparse
from pathlib import Path

CONFIG_PATH = Path.home() / ".deadliner.json"


def _cmd_login_moodle(args: argparse.Namespace) -> int:
    base_url = input("Moodle Base URL (e.g. https://teaching.kse.org.ua): ").strip()
    if not base_url:
        print("Base URL is required.", file=sys.stderr)
        return 1

    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "https://" + base_url

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    url = f"{base_url.rstrip('/')}/login/token.php"
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
        cfg = {}
        if CONFIG_PATH.exists():
            try:
                cfg = json.loads(CONFIG_PATH.read_text())
            except (OSError, ValueError):
                pass

        cfg["moodle_base_url"] = base_url
        cfg["moodle_token"] = token

        CONFIG_PATH.write_text(json.dumps(cfg, indent=4))
        print("Successfully logged in and saved Moodle token!")
        return 0
    else:
        err = data.get("error", "Unknown error")
        if "Invalid login" in err or "wrong username or password" in err.lower():
            print("Error: Incorrect username or password. Please try again.", file=sys.stderr)
        else:
            print(f"Login failed: {err}", file=sys.stderr)
        return 1
