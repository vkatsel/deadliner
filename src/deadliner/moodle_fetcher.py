import requests
from datetime import datetime, timezone
from src.deadliner.models import Assignment, AuthError

def fetch_moodle(base_url: str, token: str) -> list[Assignment]:
    url = f"{base_url.rstrip('/')}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_calendar_get_action_events_by_timesort",
        "moodlewsrestformat": "json",
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to connect to Moodle: {e}")

    data = response.json()
    
    # Handle Moodle API errors
    if "exception" in data or "errorcode" in data:
        if data.get("errorcode") == "invalidtoken":
            raise AuthError("token rejected")
        raise AuthError(f"Moodle error: {data}")

    assignments = []
    for event in data.get("events", []):
        title = event.get("name", "Unknown Assignment")
        
        # Moodle course info can be structured differently depending on the endpoint version
        course_shortname = ""
        course = event.get("course")
        if isinstance(course, dict):
            course_shortname = course.get("shortname", "")
        if not course_shortname:
            course_shortname = event.get("coursename", "")
            
        due_timestamp = event.get("timestart", 0)
        due_utc = datetime.fromtimestamp(due_timestamp, tz=timezone.utc)
        url_link = event.get("url", "")
        
        assignments.append(Assignment(
            platform="moodle",
            course_shortname=course_shortname,
            title=title,
            due_utc=due_utc,
            url=url_link
        ))
        
    return assignments
