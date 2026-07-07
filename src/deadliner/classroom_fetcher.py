import logging
import requests
from datetime import datetime, timezone
from deadliner.models import Assignment, AuthError

logger = logging.getLogger(__name__)

CLASSROOM_API_BASE = "https://classroom.googleapis.com/v1"


def fetch_classroom(oauth_credentials: dict) -> list[Assignment]:
    if not oauth_credentials or not oauth_credentials.get("access_token"):
        logger.debug("Classroom fetch attempted without an access_token")
        raise AuthError("No access token provided")

    access_token = oauth_credentials.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    logger.info("Fetching Google Classroom courses")
    courses_data = _get(f"{CLASSROOM_API_BASE}/courses", headers, params={"courseStates": "ACTIVE"})
    courses = courses_data.get("courses", [])

    start_of_today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    assignments = []
    for course in courses:
        course_id = course.get("id")
        course_name = course.get("name", "")
        coursework_data = _get(f"{CLASSROOM_API_BASE}/courses/{course_id}/courseWork", headers)

        for work in coursework_data.get("courseWork", []):
            title = work.get("title", "Unknown Assignment")
            due_date = work.get("dueDate")
            if not due_date or not due_date.get("year"):
                logger.warning(f"Skipping courseWork '{title}' because it has no dueDate or year")
                continue
            due_time = work.get("dueTime", {})
            due_utc = datetime(
                due_date.get("year"),
                due_date.get("month"),
                due_date.get("day"),
                due_time.get("hours", 23),
                due_time.get("minutes", 59),
                tzinfo=timezone.utc,
            )
            if due_utc < start_of_today_utc:
                continue

            assignments.append(
                Assignment(
                    platform="classroom",
                    course_shortname=course_name,
                    title=title,
                    due_utc=due_utc,
                    url=work.get("alternateLink", ""),
                )
            )

    logger.info(f"Successfully parsed {len(assignments)} Classroom assignments")
    return assignments


def _get(url: str, headers: dict, params: dict | None = None) -> dict:

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.RequestException as e:
        logger.debug(f"Classroom connection failed: {e}")
        raise ConnectionError(f"Failed to connect to Classroom: {e}")

    if response.status_code == 401:
        logger.debug("Classroom OAuth token rejected by API")
        raise AuthError("token rejected")
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError:
        logger.debug("Classroom returned invalid JSON")
        raise ConnectionError("Invalid JSON from Classroom")

    return data
