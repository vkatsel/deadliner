import logging
import re
import requests
from datetime import datetime, timezone
from deadliner.models import Assignment, AuthError

logger = logging.getLogger(__name__)


def _verify_submission_status(base_url: str, token: str, cmid: int) -> bool:
    """Verify strictly if an assignment is submitted via Moodle mod_assign web services.

    Prevents false positives on decorative events, announcements, or teacher/TA grading items.
    """
    url = f"{base_url.rstrip('/')}/webservice/rest/server.php"
    try:
        r_cm = requests.get(
            url,
            params={
                "wstoken": token,
                "wsfunction": "core_course_get_course_module",
                "moodlewsrestformat": "json",
                "cmid": cmid,
            },
            timeout=5,
        ).json()
        assignid = r_cm.get("cm", {}).get("instance")
        if not assignid:
            return False

        r_sub = requests.get(
            url,
            params={
                "wstoken": token,
                "wsfunction": "mod_assign_get_submission_status",
                "moodlewsrestformat": "json",
                "assignid": assignid,
            },
            timeout=5,
        ).json()
        status = r_sub.get("lastattempt", {}).get("submission", {}).get("status")
        return str(status).strip().lower() == "submitted"
    except Exception as e:
        logger.debug(f"Failed to verify submission status for cmid {cmid}: {e}")
        return False


def _is_assignment_submitted(event: dict, base_url: str = "", token: str = "") -> bool:
    """Determine whether an assignment has been explicitly submitted.

    Careful: We check for concrete positive submission indicators (e.g.
    'Edit submission', 'View submission') and ensure overdue or unsubmitted
    deadlines where 'Add submission' is simply missing never turn green.
    If action is missing/None for an assignment module, strictly queries
    Moodle's mod_assign_get_submission_status to avoid false positives.
    """
    action = event.get("action")
    if isinstance(action, dict):
        action_name = str(action.get("name") or "").strip().lower()
        if not action_name:
            return False

        # Never consider "Add submission" / "Додати" as submitted
        if any(negative in action_name for negative in ("add submission", "додати", "подати")):
            return False

        # Explicit positive submission markers from Moodle action events
        positive_markers = (
            "edit submission",
            "view submission",
            "remove submission",
            "submitted",
            "редагувати відповідь",
            "редагувати роботу",
            "переглянути відповідь",
            "переглянути роботу",
            "здано",
            "відповідь подано",
        )
        return any(marker in action_name for marker in positive_markers)

    # If action is None or not a dict, check if it's an assignment event
    if event.get("component") == "mod_assign" or event.get("modulename") == "assign" or event.get("eventtype") == "due":
        cmid = event.get("instance")
        if not cmid:
            match = re.search(r"[?&]id=(\d+)", str(event.get("url") or ""))
            if match:
                cmid = int(match.group(1))
        if cmid and base_url and token:
            try:
                return _verify_submission_status(base_url, token, int(cmid))
            except Exception:
                return False

    return False


def fetch_moodle(base_url: str, token: str) -> list[Assignment]:
    url = f"{base_url.rstrip('/')}/webservice/rest/server.php"
    start_of_today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    params = {
        "wstoken": token,
        "wsfunction": "core_calendar_get_action_events_by_timesort",
        "moodlewsrestformat": "json",
        "timesortfrom": int(start_of_today.timestamp()),
    }

    logger.info(f"Fetching Moodle deadlines from {base_url}")
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.debug(f"Moodle connection failed: {e}")
        raise ConnectionError(f"Failed to connect to Moodle: {e}")

    try:
        data = response.json()
    except ValueError:
        logger.debug("Moodle returned invalid JSON")
        raise ConnectionError("Invalid JSON from Moodle")

    # Note: Moodle's REST API almost always returns HTTP 200 OK even for errors like invalid tokens.
    # The actual error is embedded in the JSON body, which is why we must check "errorcode" manually.
    if "exception" in data or "errorcode" in data:
        if data.get("errorcode") == "invalidtoken":
            logger.debug("Moodle token rejected by API")
            raise AuthError("token rejected")
        logger.debug(f"Moodle returned an error: {data}")
        raise AuthError(f"Moodle error: {data}")

    events = list(data.get("events", []))

    # Also fetch upcoming calendar events to capture submitted assignments
    # whose action events are cleared by Moodle upon submission
    try:
        upcoming_resp = requests.get(
            url,
            params={
                "wstoken": token,
                "wsfunction": "core_calendar_get_calendar_upcoming_view",
                "moodlewsrestformat": "json",
            },
            timeout=5,
        )
        if upcoming_resp.status_code == 200:
            upcoming_data = upcoming_resp.json()
            if isinstance(upcoming_data, dict) and "events" in upcoming_data:
                seen_keys = {
                    e.get("url") or f"{e.get('course', {}).get('shortname')}:{e.get('name')}:{e.get('timestart')}"
                    for e in events
                }
                for u_ev in upcoming_data.get("events", []):
                    key = (
                        u_ev.get("url")
                        or f"{u_ev.get('course', {}).get('shortname')}:{u_ev.get('name')}:{u_ev.get('timestart')}"
                    )
                    if key not in seen_keys:
                        events.append(u_ev)
                        seen_keys.add(key)
    except Exception as e:
        logger.debug(f"Could not fetch Moodle upcoming view: {e}")

    assignments = []
    for event in events:
        title = event.get("name", "Unknown Assignment")

        course = event.get("course")
        course_shortname = course.get("shortname", "") if isinstance(course, dict) else ""
        if course_shortname:
            course_shortname = re.sub(r'[-_\s]20\d{2}$', '', course_shortname).strip()

        due_timestamp = event.get("timestart")
        if not due_timestamp or due_timestamp == 0:
            logger.warning(f"Skipping assignment '{title}' because timestart is missing or 0")
            continue

        due_utc = datetime.fromtimestamp(due_timestamp, tz=timezone.utc)
        url_link = event.get("url", "")
        is_submitted = _is_assignment_submitted(event, base_url=base_url, token=token)

        assignments.append(
            Assignment(
                platform="moodle",
                course_shortname=course_shortname,
                title=title,
                due_utc=due_utc,
                url=url_link,
                is_submitted=is_submitted,
            )
        )

    logger.info(f"Successfully parsed {len(assignments)} Moodle assignments")
    return assignments
