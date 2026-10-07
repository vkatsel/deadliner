import argparse
import base64
import json
import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import requests

from deadliner.models import AuthError

logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".deadliner.json"
KSE_AUTH_REFRESH_URL = "https://api.kse.today/auth/refresh"
KSE_SCHEDULE_VERIFY_URL = "https://api.kse.today/schedule"
KSE_SYNC_PORT = 8484
KSE_SYNC_URL = f"http://127.0.0.1:{KSE_SYNC_PORT}/token"


def _copy_to_clipboard(text: str) -> bool:
    """Copy a string to the system clipboard (Windows, macOS, Linux)."""
    try:
        if sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode("utf-8"), check=True, creationflags=0x08000000)
            return True
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
        if sys.platform.startswith("linux"):
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True)
            return True
    except Exception:
        pass
    return False


def _read_clipboard() -> str:
    """Read current text from system clipboard."""
    try:
        import tkinter
        r = tkinter.Tk()
        r.withdraw()
        text = r.clipboard_get()
        r.destroy()
        return text or ""
    except Exception:
        pass

    try:
        if sys.platform == "win32":
            p = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=0x08000000,
            )
            return p.stdout.strip()
        if sys.platform == "darwin":
            p = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
            return p.stdout.strip()
        if sys.platform.startswith("linux"):
            p = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=2)
            return p.stdout.strip()
    except Exception:
        pass
    return ""


def _extract_credentials_from_text(raw_val: str) -> tuple[str, str, str, str] | None:
    """Extract (token, refresh_token, session_id, user_name) from raw text or JSON."""
    if not raw_val or not isinstance(raw_val, str):
        return None
    raw_val = raw_val.strip()

    token = ""
    refresh_token = ""
    session_id = ""
    user_name = ""

    if raw_val.startswith("{") and raw_val.endswith("}"):
        try:
            parsed = json.loads(raw_val)
            if "auth" in parsed and isinstance(parsed["auth"], str):
                inner = json.loads(parsed["auth"])
                user_obj = inner.get("user", inner)
            else:
                user_obj = parsed.get("user", parsed)

            token = user_obj.get("token") or user_obj.get("jwt") or parsed.get("token", "")
            refresh_token = (
                user_obj.get("refreshToken")
                or user_obj.get("refresh_token")
                or parsed.get("refreshToken")
                or parsed.get("refresh_token", "")
            )
            session_id = str(
                parsed.get("sessionId")
                or parsed.get("session_id")
                or parsed.get("sess")
                or user_obj.get("sessionId")
                or user_obj.get("session_id")
                or ""
            )
            profile = user_obj.get("profile", {})
            user_name = profile.get("name") or parsed.get("name", "")
        except Exception:
            pass

    if not token and raw_val.count(".") == 2 and raw_val.startswith("eyJ"):
        token = raw_val

    if token and token.count(".") == 2:
        return token, refresh_token, session_id, user_name
    return None


WEBVIEW_CACHE_DIR = Path.home() / ".deadliner" / "webview_cache"
DESKTOP_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/133.0.0.0 Safari/537.36"
)


def _patch_edgechromium_for_oauth() -> None:
    """Configure Edge WebView2 to support native Google OAuth popup flows.

    1. Sets Handled=False on NewWindowRequested so WebView2 opens the OAuth
       popup with window.opener preserved. This allows Google's authorization
       completion script (window.opener.postMessage) to communicate directly
       back to schedule.kse.ua and auto-close the popup window.
    2. Injects a standard desktop Chrome User-Agent into AdditionalBrowserArguments
       so Google does not flag the environment as an embedded webview.
    """
    try:
        from webview.platforms import edgechromium

        def patched_on_new_window_request(self, sender, args):
            # Allow WebView2 to create native popup with parent window.opener intact
            args.set_Handled(False)

        edgechromium.EdgeChrome.on_new_window_request = patched_on_new_window_request

        orig_init = edgechromium.EdgeChrome.__init__

        def patched_edge_init(self, form, window, cache_dir):
            self.pywebview_window = window
            self.webview = edgechromium.WebView2()
            props = edgechromium.CoreWebView2CreationProperties()

            runtime_path = edgechromium.webview_settings.get("WEBVIEW2_RUNTIME_PATH")
            if runtime_path:
                if not edgechromium.os.path.isabs(runtime_path):
                    runtime_path = edgechromium.os.path.join(edgechromium.get_app_root(), runtime_path)
                if edgechromium.os.path.exists(runtime_path):
                    props.BrowserExecutableFolder = runtime_path

            props.UserDataFolder = cache_dir
            self.user_data_folder = props.UserDataFolder
            props.set_IsInPrivateModeEnabled(edgechromium._state["private_mode"])

            # Pure desktop Chrome User-Agent without WebView or Edg markers
            props.AdditionalBrowserArguments = (
                f'--disable-features=ElasticOverscroll --user-agent="{DESKTOP_CHROME_UA}"'
            )

            if edgechromium.webview_settings.get("ALLOW_FILE_URLS"):
                props.AdditionalBrowserArguments += " --allow-file-access-from-files"

            if edgechromium.webview_settings.get("REMOTE_DEBUGGING_PORT") is not None:
                props.AdditionalBrowserArguments += (
                    f' --remote-debugging-port={edgechromium.webview_settings["REMOTE_DEBUGGING_PORT"]}'
                )

            self.webview.CreationProperties = props

            self.form = form
            form.Controls.Add(self.webview)

            self.js_results = {}
            self.js_result_semaphore = edgechromium.Semaphore(0)
            self.webview.Dock = edgechromium.WinForms.DockStyle.Fill
            self.webview.BringToFront()
            self.webview.CoreWebView2InitializationCompleted += self.on_webview_ready
            self.webview.NavigationStarting += self.on_navigation_start
            self.webview.NavigationCompleted += self.on_navigation_completed
            self.webview.WebMessageReceived += self.on_script_notify
            self.syncContextTaskScheduler = edgechromium.TaskScheduler.FromCurrentSynchronizationContext()
            self.webview.DefaultBackgroundColor = edgechromium.Color.FromArgb(
                255,
                int(window.background_color.lstrip("#")[0:2], 16),
                int(window.background_color.lstrip("#")[2:4], 16),
                int(window.background_color.lstrip("#")[4:6], 16),
            )

            if window.transparent:
                self.webview.DefaultBackgroundColor = edgechromium.Color.Transparent

            self.url = None
            self.ishtml = False
            self.html = edgechromium.DEFAULT_HTML

            self.webview.EnsureCoreWebView2Async(None)

        edgechromium.EdgeChrome.__init__ = patched_edge_init
    except Exception as e:
        logger.debug(f"EdgeChromium patching not applicable: {e}")


def login_kse_webview(timeout: int = 180) -> tuple[str, str, str, str] | None:
    """Open an interactive native WebView window for schedule.kse.ua and automatically capture credentials.

    Uses Edge WebView2 on Windows or WebKit on macOS/Linux. Persists session in
    ~/.deadliner/webview_cache so users stay signed into Google SSO across sessions.

    Returns:
        (token, refresh_token, session_id, user_name) or None if cancelled or unavailable.
    """
    try:
        import webview
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
        _patch_edgechromium_for_oauth()
    except ImportError:
        logger.debug("pywebview is not installed; falling back to alternative login methods.")
        return None

    try:
        WEBVIEW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    captured: dict[str, tuple[str, str, str, str]] = {}
    is_done = threading.Event()

    print("\n" + "=" * 68)
    print("  🔑 KSE Schedule — Native Web Login")
    print("=" * 68)
    print("Opening secure browser window for schedule.kse.ua...")
    print("👉 Sign in with your @kse.org.ua Google account in the window.")
    print("⚡ Deadliner will automatically detect your login and close the window.")
    print("=" * 68 + "\n")

    def _poll_credentials(window: webview.Window) -> None:
        start_t = time.time()
        time.sleep(1.0)
        while not is_done.is_set() and time.time() - start_t < timeout:
            try:
                # 1. Install postMessage listener on schedule.kse.ua if not present
                window.evaluate_js(
                    """(function() {
                        if (!window.__deadliner_listener_installed) {
                            window.__deadliner_listener_installed = true;
                            window.addEventListener("message", function(e) {
                                try {
                                    var d = e.data;
                                    var c = (d && d.response && d.response.code) || (d && d.code);
                                    if (c) window.__deadliner_oauth_code = c;
                                } catch(err) {}
                            });
                        }
                    })()"""
                )

                # 2. Check for completed authentication in localStorage
                raw_auth = window.evaluate_js(
                    "localStorage.getItem('__NEXUS_REACT_ADMIN_AUTH__') || localStorage.getItem('token')"
                )
                if raw_auth:
                    creds = _extract_credentials_from_text(raw_auth)
                    if creds:
                        captured["creds"] = creds
                        is_done.set()
                        window.destroy()
                        return

                # 3. Check if OAuth code was captured by listener or URL query/hash
                code_val = window.evaluate_js(
                    """(function() {
                        if (window.__deadliner_oauth_code) return window.__deadliner_oauth_code;
                        var m = window.location.search.match(/[?&]code=([^&]+)/) || window.location.hash.match(/[#&]code=([^&]+)/);
                        if (m) return decodeURIComponent(m[1]);
                        return null;
                    })()"""
                )
                if code_val and isinstance(code_val, str) and code_val.startswith("4/"):
                    try:
                        res = requests.post(
                            "https://api.kse.today/auth/google",
                            json={"code": code_val},
                            timeout=10,
                        )
                        if res.status_code == 200:
                            creds = _extract_credentials_from_text(res.text)
                            if creds:
                                captured["creds"] = creds
                                is_done.set()
                                window.destroy()
                                return
                    except Exception:
                        pass
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
            title="Deadliner — KSE Login",
            url="https://schedule.kse.ua",
            width=900,
            height=650,
            min_size=(600, 450),
        )
        webview.start(
            _poll_credentials,
            window,
            private_mode=False,
            storage_path=str(WEBVIEW_CACHE_DIR),
            user_agent=DESKTOP_CHROME_UA,
        )
    except Exception as e:
        logger.debug(f"Failed to launch pywebview window: {e}")
        return None

    return captured.get("creds")


def login_kse_clipboard_sync(timeout: int = 60) -> tuple[str, str, str, str] | None:
    """Open schedule.kse.ua and automatically capture credentials from clipboard.

    Returns:
        (token, refresh_token, session_id, user_name) or None if cancelled.
    """
    initial_cmd = 'copy(JSON.stringify({...JSON.parse(localStorage.getItem("__NEXUS_REACT_ADMIN_AUTH__")||"{}"),sessionId:sessionStorage.getItem("sessionId")}))'
    _copy_to_clipboard(initial_cmd)

    print("\n" + "=" * 68)
    print("  🔑 KSE Schedule 1-Click Login")
    print("=" * 68)
    print("Opening https://schedule.kse.ua in your default browser...")
    try:
        webbrowser.open("https://schedule.kse.ua")
    except Exception:
        pass

    print("\n👉 To connect your account in 3 seconds:")
    print("   1. On https://schedule.kse.ua, open Developer Tools (F12) -> Console.")
    print("   2. Press Ctrl+V then Enter.")
    print("\n📋 (The command is ALREADY in your clipboard!)")
    print("⏳ Deadliner is waiting for your clipboard... (Ctrl+C to enter manually)")
    print("=" * 68 + "\n")

    start_t = time.time()
    while time.time() - start_t < timeout:
        try:
            time.sleep(0.2)
            clip_text = _read_clipboard()
            if clip_text and clip_text != initial_cmd:
                creds = _extract_credentials_from_text(clip_text)
                if creds:
                    return creds
        except (KeyboardInterrupt, EOFError):
            break
        except Exception:
            pass

    return None


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
        req_body: dict = {
            "refresh_token": refresh_token,
            "refreshToken": refresh_token,
        }
        if session_id:
            req_body["session_id"] = session_id
            req_body["sessionId"] = session_id

        response = requests.post(
            KSE_AUTH_REFRESH_URL,
            headers={"Content-Type": "application/json"},
            json=req_body,
            timeout=10,
        )
        if response.status_code != 200:
            logger.debug(f"KSE token refresh failed with status {response.status_code}")
            return None

        data = response.json() if response.content else {}
        user_obj = data.get("user", data) if isinstance(data, dict) else {}
        if not isinstance(user_obj, dict):
            user_obj = {}

        new_token = (
            data.get("token")
            or data.get("jwt")
            or data.get("accessToken")
            or user_obj.get("token")
            or user_obj.get("jwt")
            or user_obj.get("accessToken")
        )
        new_refresh = (
            data.get("refreshToken")
            or data.get("refresh_token")
            or user_obj.get("refreshToken")
            or user_obj.get("refresh_token")
            or refresh_token
        )
        new_session = str(
            data.get("sessionId")
            or data.get("session_id")
            or user_obj.get("sessionId")
            or user_obj.get("session_id")
            or session_id
            or ""
        )
        if new_token:
            save_kse_credentials(new_token, new_refresh, new_session)
            return new_token
    except Exception as e:
        logger.debug(f"Error during KSE token refresh: {e}")
        return None

    return None


def is_kse_token_expired(token: str) -> bool:
    """Check if the JWT token is expired or close to expiring (within 60s)."""
    if not token:
        return True
    payload = _decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        return False
    try:
        exp_num = float(exp)
        if exp_num > 1e11:  # In case server returns millisecond timestamp
            exp_num = exp_num / 1000.0
        return time.time() >= (exp_num - 60)
    except (ValueError, TypeError):
        return False


def get_valid_kse_token(raise_on_failure: bool = False) -> str:
    """Return a valid KSE token, attempting refresh if expired or missing.

    If raise_on_failure is True:
        Raises AuthError if token is missing, expired without refresh, or refresh fails.
    If raise_on_failure is False:
        Returns empty string if token is invalid/expired and cannot be refreshed.
    """
    token, refresh_token, session_id = load_kse_credentials()
    if not token and not refresh_token:
        if raise_on_failure:
            raise AuthError("KSE credentials not found. Please run `deadliner login kse` to connect your account.")
        return ""

    if not token or is_kse_token_expired(token):
        if refresh_token:
            refreshed = refresh_kse_token(refresh_token, session_id)
            if refreshed:
                return refreshed
        # Expired and refresh failed or unavailable
        if raise_on_failure:
            raise AuthError(
                "KSE authentication expired and auto-refresh failed. Please run `deadliner login kse` to re-authenticate."
            )
        return ""

    return token


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
    token = ""
    refresh_token = ""
    session_id = ""
    user_name = ""

    manual = getattr(args, "manual", False)
    use_clipboard = getattr(args, "clipboard", False)

    if not manual and not use_clipboard:
        captured = login_kse_webview()
        if captured:
            token, refresh_token, session_id, user_name = captured
            print("\033[92m✓ Successfully received KSE credentials via Native Web Login!\033[0m")
        elif sys.stdin.isatty():
            print("\033[93mNotice: Native window closed or unavailable. Trying 1-click clipboard sync...\033[0m")
            captured = login_kse_clipboard_sync()
            if captured:
                token, refresh_token, session_id, user_name = captured
                print("\033[92m✓ Successfully received KSE credentials from clipboard!\033[0m")
    elif use_clipboard and not manual:
        captured = login_kse_clipboard_sync()
        if captured:
            token, refresh_token, session_id, user_name = captured
            print("\033[92m✓ Successfully received KSE credentials from clipboard!\033[0m")

    if not token:
        print("\n" + "=" * 65)
        print("  Manual KSE Token Entry")
        print("=" * 65)
        print("1. Open https://schedule.kse.ua in your browser (signed in with @kse.org.ua).")
        print("2. Press F12 -> Console.")
        print('3. Paste: copy(localStorage.getItem("__NEXUS_REACT_ADMIN_AUTH__"))')
        print("4. Paste the copied text below.")
        print("=" * 65)

        try:
            raw_input_val = input("\nPaste your KSE Token or JSON: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nLogin cancelled.")
            return 130

        if not raw_input_val:
            print("Error: Token cannot be empty.", file=sys.stderr)
            return 1

        creds = _extract_credentials_from_text(raw_input_val)
        if creds:
            token, refresh_token, session_id, user_name = creds
        else:
            token = raw_input_val

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

    # If token is expired and we have refresh token, refresh immediately
    if (is_kse_token_expired(token) or not token) and refresh_token:
        print("Access token expired, refreshing with KSE API...")
        refreshed = refresh_kse_token(refresh_token, session_id)
        if refreshed:
            token = refreshed

    print("Verifying token with KSE API...")
    from datetime import date
    today_str = date.today().isoformat()
    verify_params = {"from": today_str, "till": today_str}

    try:
        res = requests.get(
            KSE_SCHEDULE_VERIFY_URL,
            headers={"Authorization": f"Bearer {token}"},
            params=verify_params,
            timeout=10,
        )
        if res.status_code in (401, 403) and refresh_token:
            print("Token rejected, attempting refresh with KSE API...")
            refreshed = refresh_kse_token(refresh_token, session_id)
            if refreshed:
                token = refreshed
                res = requests.get(
                    KSE_SCHEDULE_VERIFY_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    params=verify_params,
                    timeout=10,
                )

        if res.status_code in (401, 403):
            print("Error: The supplied KSE token was rejected (401 Unauthorized).", file=sys.stderr)
            print(
                "Tip: If your session on schedule.kse.ua has expired, please log out and log in again on https://schedule.kse.ua.",
                file=sys.stderr,
            )
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

