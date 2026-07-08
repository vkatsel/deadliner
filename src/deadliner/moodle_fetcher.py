import logging
import requests
from datetime import datetime, timezone
from deadliner.models import Assignment, AuthError

logger = logging.getLogger(__name__)


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

    assignments = []
    for event in data.get("events", []):
        title = event.get("name", "Unknown Assignment")

        course = event.get("course")
        course_shortname = course.get("shortname", "") if isinstance(course, dict) else ""

        due_timestamp = event.get("timestart")
        if not due_timestamp or due_timestamp == 0:
            logger.warning(f"Skipping assignment '{title}' because timestart is missing or 0")
            continue

        due_utc = datetime.fromtimestamp(due_timestamp, tz=timezone.utc)
        url_link = event.get("url", "")

        assignments.append(
            Assignment(platform="moodle", course_shortname=course_shortname, title=title, due_utc=due_utc, url=url_link)
        )

    logger.info(f"Successfully parsed {len(assignments)} Moodle assignments")
    return assignments
