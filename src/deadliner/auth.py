"""Moodle authentication and credential management for Deadliner."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import logging
from pathlib import Path
import re
import secrets
import shutil
import sys
import threading
import time
from urllib.parse import unquote, urlparse

import requests

from deadliner.models import AuthError

logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".deadliner.json"
DEFAULT_MOODLE_URL = "https://teaching.kse.org.ua"
MOODLE_TOKEN_RE = re.compile(r"\b([0-9a-fA-F]{32})\b")


def authenticate_moodle_credentials(base_url: str, username: str, password: str) -> str:
    """Authenticate against Moodle token endpoint and return the web service token.

    Raises:
        ConnectionError: When network/server connection fails.
        AuthError: When Moodle rejects credentials or returns an error payload.
    """
    norm_url = normalize_moodle_url(base_url)
    url = f"{norm_url}/login/token.php"
    params = {"username": username.strip(), "password": password, "service": "moodle_mobile_app"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            "Could not connect to the Moodle server. Please check the Base URL and your internet connection."
        ) from e
    except requests.exceptions.Timeout as e:
        raise ConnectionError("Connection to Moodle timed out. Please try again later.") from e
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "unknown"
        raise ConnectionError(
            f"Received a bad response from the server ({code}). Are you sure this is a Moodle URL?"
        ) from e
    except requests.RequestException as e:
        raise ConnectionError("An unexpected network error occurred.") from e

    try:
        data = response.json()
    except ValueError as e:
        raise ConnectionError("Moodle returned invalid JSON.") from e

    if isinstance(data, dict) and "token" in data and data["token"]:
        return str(data["token"])

    err = data.get("error", "Unknown error") if isinstance(data, dict) else "Unknown error"
    err_lower = str(err).lower()
    errorcode = str(data.get("errorcode", "")).lower() if isinstance(data, dict) else ""
    if (
        "invalid login" in err_lower
        or "wrong username or password" in err_lower
        or errorcode == "invalidlogin"
    ):
        raise AuthError(
            "Incorrect username or password. "
            "Tip: Use Google SSO (`deadliner login moodle`) or check your local Moodle password."
        )
    raise AuthError(f"Login failed: {err}")


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


def parse_moodle_launch_token(uri: str) -> str | None:
    """Extract Moodle web service token from a `moodlemobile://token=<base64>` redirect URI.

    Moodle's `admin/tool/mobile/launch.php` redirects to:
        <urlscheme>://token=<base64(site_signature:::wstoken[:::privatetoken])>
    """
    if not uri or not isinstance(uri, str):
        return None

    match = re.search(r"://token=([^&#\s]+)", uri, flags=re.IGNORECASE)
    if not match:
        return None

    encoded = unquote(match.group(1)).strip()
    if not encoded:
        return None

    padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
    decoded_str = ""
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            decoded_bytes = decoder(padded)
            decoded_str = decoded_bytes.decode("utf-8")
            break
        except Exception:
            continue

    if not decoded_str or ":::" not in decoded_str:
        return None

    parts = decoded_str.split(":::")
    if len(parts) >= 2:
        token = parts[1].strip()
        if token:
            return token
    return None


def extract_moodle_token_from_managetoken_html(html: str) -> str | None:
    """Extract the `Moodle mobile web service` security key from `/user/managetoken.php` HTML.

    Supports both English ('Moodle mobile web service') and Ukrainian
    ('Мобільний вебсервіс Moodle' / 'Мобільний додаток') Moodle UI labels.
    """
    if not html or not isinstance(html, str):
        return None

    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    # Pass 1: Explicit Moodle mobile web service row (EN or UA)
    for row in rows:
        row_lower = row.lower()
        is_mobile_service = (
            "moodle mobile" in row_lower
            or "moodle_mobile_app" in row_lower
            or ("moodle" in row_lower and ("мобільн" in row_lower or "mobile" in row_lower))
        )
        if is_mobile_service:
            token_match = MOODLE_TOKEN_RE.search(row)
            if token_match:
                return token_match.group(1)

    # Pass 2: Fallback to any non-RSS/non-calendar web service key row in managetoken.php
    for row in rows:
        row_lower = row.lower()
        if any(skip in row_lower for skip in ("rss", "calendar", "календар")):
            continue
        if any(marker in row_lower for marker in ("web service", "вебсервіс", "веб-сервіс", "service", "сервіс")):
            token_match = MOODLE_TOKEN_RE.search(row)
            if token_match:
                return token_match.group(1)

    return None


def verify_moodle_token(base_url: str, token: str) -> tuple[bool, str]:
    """Verify a Moodle web service token via `core_webservice_get_site_info`.

    Returns:
        (True, display_name) when valid, or (False, error_message) when invalid/unreachable.
    """
    clean_token = (token or "").strip()
    if not clean_token:
        return False, "Moodle token cannot be empty."

    norm_url = normalize_moodle_url(base_url)
    url = f"{norm_url}/webservice/rest/server.php"
    params = {
        "wstoken": clean_token,
        "wsfunction": "core_webservice_get_site_info",
        "moodlewsrestformat": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to the Moodle server. Check the Base URL and internet connection."
    except requests.exceptions.Timeout:
        return False, "Connection to Moodle timed out. Please try again later."
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "unknown"
        return False, f"Moodle server returned HTTP {code}."
    except requests.RequestException as e:
        return False, f"Network error while verifying Moodle token: {e}"

    try:
        data = response.json()
    except ValueError:
        return False, "Moodle returned invalid JSON while verifying token."

    if not isinstance(data, dict):
        return False, "Unexpected response format from Moodle."

    if "exception" in data or "errorcode" in data:
        err_msg = data.get("message") or data.get("error") or data.get("errorcode") or "Invalid token"
        return False, str(err_msg)

    display_name = str(
        data.get("fullname") or data.get("username") or data.get("firstname") or "Moodle User"
    ).strip()
    return True, display_name


def login_moodle_webview(
    base_url: str = DEFAULT_MOODLE_URL,
    timeout: int = 180,
    clean: bool = False,
) -> str | None:
    """Open an interactive native WebView window for Moodle Google SSO and capture the long-lived wstoken.

    Uses Moodle's official mobile SSO handshake (`admin/tool/mobile/launch.php`) which issues
    the same long-lived `moodle_mobile_app` Web Service token as `login/token.php`. If `launch.php`
    does not redirect to `moodlemobile://`, automatically falls back to reading the user's
    Security Key from `/user/managetoken.php` using the authenticated WebView session.

    Returns:
        Captured Moodle web service token (`wstoken`), or None if cancelled/unavailable.
    """
    from deadliner.kse_auth import (
        DESKTOP_CHROME_UA,
        WEBVIEW_CACHE_DIR,
        _patch_edgechromium_for_oauth,
    )

    norm_url = normalize_moodle_url(base_url)
    moodle_host = (urlparse(norm_url).hostname or "").lower()

    if clean and WEBVIEW_CACHE_DIR.exists():
        try:
            shutil.rmtree(WEBVIEW_CACHE_DIR, ignore_errors=True)
            print("Cleared WebView cache.")
        except Exception as e:
            logger.debug(f"Failed to clear webview cache: {e}")

    captured: dict[str, str] = {}
    is_done = threading.Event()
    window_ref: list = []

    def _finish_with_token(tok: str) -> None:
        if not tok or is_done.is_set():
            return
        captured["token"] = tok
        is_done.set()
        if window_ref:
            try:
                window_ref[0].destroy()
            except Exception:
                pass

    def _on_custom_scheme(uri: str) -> bool:
        if "://token=" not in uri.lower():
            return False
        tok = parse_moodle_launch_token(uri)
        if tok:
            _finish_with_token(tok)
        return True

    try:
        import webview

        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
        _patch_edgechromium_for_oauth(on_custom_scheme=_on_custom_scheme)
    except ImportError:
        logger.debug("pywebview is not installed; falling back to manual Moodle token entry.")
        return None

    try:
        WEBVIEW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    managetoken_url = f"{norm_url}/user/managetoken.php"

    print("\n" + "=" * 68)
    print("  🔑 Moodle LMS — Native Google SSO Login")
    print("=" * 68)
    print(f"Opening secure browser window for {norm_url}...")
    print("👉 Sign in with your @kse.org.ua Google account in the window.")
    print("⚡ Deadliner will automatically capture your Moodle Security Key and close.")
    print("=" * 68 + "\n")

    def _poll_moodle_token(window: webview.Window) -> None:
        if timeout > 0:
            time.sleep(min(0.6, timeout))
        start_t = time.time()
        redirected_to_keys = False
        empty_keys_checks = 0

        while not is_done.is_set() and time.time() - start_t < timeout:
            try:
                cur_url = str(window.get_current_url() or "")
                lower_url = cur_url.lower()

                # 1. Custom scheme / token= safety net
                if "://token=" in lower_url:
                    tok = parse_moodle_launch_token(cur_url)
                    if tok:
                        _finish_with_token(tok)
                        return

                cur_host = (urlparse(cur_url).hostname or "").lower()
                if moodle_host and cur_host == moodle_host:
                    # 2. Directly on /user/managetoken.php -> extract Moodle mobile web service key
                    if "/user/managetoken.php" in lower_url:
                        html = window.evaluate_js(
                            "document.documentElement ? document.documentElement.outerHTML : ''"
                        )
                        if isinstance(html, str) and html:
                            tok = extract_moodle_token_from_managetoken_html(html)
                            if tok:
                                _finish_with_token(tok)
                                return

                        ready_and_logged_in = window.evaluate_js(
                            "Boolean(document.readyState === 'complete' && window.M && window.M.cfg && window.M.cfg.sesskey)"
                        )
                        if ready_and_logged_in:
                            empty_keys_checks += 1
                            if empty_keys_checks >= 3:
                                print(
                                    f"Moodle Mobile Web Services appear to be disabled on {norm_url} "
                                    "(no Security Keys found on /user/managetoken.php).",
                                    file=sys.stderr,
                                )
                                is_done.set()
                                try:
                                    window.destroy()
                                except Exception:
                                    pass
                                return

                    # 3. Logged in on another Moodle page (e.g. /my/ Dashboard because SSO ignored wantsurl)
                    elif "/login/" not in lower_url and not redirected_to_keys:
                        has_sesskey = window.evaluate_js(
                            "Boolean(window.M && window.M.cfg && window.M.cfg.sesskey)"
                        )
                        if has_sesskey:
                            redirected_to_keys = True
                            window.load_url(managetoken_url)
            except Exception:
                pass
            time.sleep(0.4)

        if not is_done.is_set():
            is_done.set()
            try:
                window.destroy()
            except Exception:
                pass

    try:
        window = webview.create_window(
            title="Deadliner — Moodle Google SSO Login",
            url=managetoken_url,
            width=900,
            height=680,
            min_size=(600, 480),
        )
        window_ref.append(window)
        try:
            window.events.closed += lambda: is_done.set()
        except Exception:
            pass

        webview.start(
            _poll_moodle_token,
            window,
            private_mode=False,
            storage_path=str(WEBVIEW_CACHE_DIR),
            user_agent=DESKTOP_CHROME_UA,
        )
    except Exception as e:
        logger.debug(f"Failed to launch Moodle pywebview window: {e}")
        return None

    return captured.get("token")


def _login_moodle_credentials_interactive(base_url_arg: str | None = None) -> int:
    """Legacy interactive username/password Moodle login via /login/token.php."""
    print("=== Moodle Login Setup (Credentials) ===")
    if base_url_arg:
        base_url = normalize_moodle_url(base_url_arg)
    else:
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
                "run `deadliner login moodle` (without --credentials) to sign in via Google SSO, "
                "or set a local password in Moodle profile settings.",
                file=sys.stderr,
            )
        else:
            print(f"Login failed: {err}", file=sys.stderr)
        return 1


def _cmd_login_moodle(args: argparse.Namespace | None = None) -> int:
    """Interactively log in to Moodle (Google SSO WebView by default) and save token to config."""
    use_credentials = bool(getattr(args, "credentials", False)) if args is not None else False
    use_manual = bool(getattr(args, "manual", False)) if args is not None else False
    clean = bool(getattr(args, "clean", False)) if args is not None else False
    raw_url = getattr(args, "url", None) if args is not None else None

    if use_credentials:
        return _login_moodle_credentials_interactive(base_url_arg=raw_url)

    base_url = normalize_moodle_url(raw_url or "")
    token = ""

    if not use_manual:
        captured = login_moodle_webview(base_url=base_url, clean=clean)
        if captured:
            token = captured
            print("\033[92m✓ Successfully received Moodle token via Native Google SSO!\033[0m")
        elif not sys.stdin.isatty():
            print("Error: Moodle WebView login was cancelled or unavailable.", file=sys.stderr)
            return 1

    if not token:
        print("\n" + "=" * 65)
        print("  Manual Moodle Security Key Entry")
        print("=" * 65)
        print(f"1. Open {base_url}/user/managetoken.php in your browser (signed in via Google).")
        print("2. Copy the key next to 'Moodle mobile web service'.")
        print("3. Paste the token below.")
        print("=" * 65)

        try:
            if not raw_url:
                entered_url = input(f"\nMoodle Base URL [{base_url}]: ").strip()
                if entered_url:
                    base_url = normalize_moodle_url(entered_url)
            token = input("Paste your Moodle Security Key token: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nLogin cancelled.")
            return 130

        if not token:
            print("Error: Moodle token cannot be empty.", file=sys.stderr)
            return 1

    print("Verifying token with Moodle API...")
    is_valid, info = verify_moodle_token(base_url, token)
    if not is_valid:
        print(f"Error: Moodle token verification failed: {info}", file=sys.stderr)
        return 1

    if save_moodle_config(base_url, token, CONFIG_PATH):
        print(f"\n\033[92mSuccessfully verified and saved Moodle token to {CONFIG_PATH}!\033[0m")
        print(f"Logged in as: \033[1m{info}\033[0m ({base_url})\n")
        return 0
    else:
        print(f"Error: Failed to save Moodle credentials to {CONFIG_PATH}.", file=sys.stderr)
        return 1
