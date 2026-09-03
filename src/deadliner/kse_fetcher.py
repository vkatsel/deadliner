import logging
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
import requests

from deadliner.models import AuthError, ScheduleEvent

logger = logging.getLogger(__name__)

KSE_API_BASE = "https://api.kse.today"
KYIV_TZ = ZoneInfo("Europe/Kyiv")

PERIODS_TIMETABLE: dict[int, tuple[str, str]] = {
    1: ("08:30", "09:50"),
    2: ("10:00", "11:20"),
    3: ("11:30", "12:50"),
    4: ("13:30", "14:50"),
    5: ("15:00", "16:20"),
    6: ("16:30", "17:50"),
    7: ("18:00", "19:20"),
    8: ("19:30", "20:50"),
}


def _period_to_datetimes(date_str: str, period: int) -> tuple[datetime, datetime]:
    """Convert a date string YYYY-MM-DD and period number to UTC start and end datetimes."""
    period_times = PERIODS_TIMETABLE.get(period, ("08:30", "09:50"))
    start_str, end_str = period_times

    date_obj = date.fromisoformat(date_str)
    start_h, start_m = map(int, start_str.split(":"))
    end_h, end_m = map(int, end_str.split(":"))

    start_local = datetime.combine(date_obj, time(start_h, start_m), tzinfo=KYIV_TZ)
    end_local = datetime.combine(date_obj, time(end_h, end_m), tzinfo=KYIV_TZ)

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _extract_teacher_name(raw_teacher: object) -> str:
    if isinstance(raw_teacher, str):
        return raw_teacher
    if isinstance(raw_teacher, dict):
        if "name" in raw_teacher and isinstance(raw_teacher["name"], dict):
            first = raw_teacher["name"].get("first", "")
            last = raw_teacher["name"].get("last", "")
            return f"{first} {last}".strip()
        if "name" in raw_teacher and isinstance(raw_teacher["name"], str):
            return raw_teacher["name"]
        first = raw_teacher.get("first", "")
        last = raw_teacher.get("last", "")
        if first or last:
            return f"{first} {last}".strip()
    return ""


def _parse_single_event(raw_event: dict, default_date: str = "") -> ScheduleEvent | None:
    start_str = raw_event.get("start")
    end_str = raw_event.get("end")

    if start_str and end_str:
        if start_str.endswith("Z"):
            start_str = start_str[:-1] + "+00:00"
        if end_str.endswith("Z"):
            end_str = end_str[:-1] + "+00:00"
        try:
            start_utc = datetime.fromisoformat(start_str)
            end_utc = datetime.fromisoformat(end_str)
            date_str = raw_event.get("date") or start_utc.astimezone(KYIV_TZ).date().isoformat()
        except Exception:
            start_utc, end_utc = None, None
            date_str = raw_event.get("date") or default_date
    else:
        start_utc, end_utc = None, None
        date_str = raw_event.get("date") or default_date

    if not date_str:
        logger.warning(f"Skipping event due to missing date: {raw_event}")
        return None

    try:
        period = int(raw_event.get("period", 1))
        if not start_utc or not end_utc:
            start_utc, end_utc = _period_to_datetimes(date_str, period)
    except Exception as e:
        logger.warning(f"Error parsing period/date for event {raw_event}: {e}")
        return None

    discipline = raw_event.get("discipline") or ""
    course_name = raw_event.get("course_name") or raw_event.get("title") or discipline or "KSE Class"
    event_type = raw_event.get("event_type") or "lecture"
    subgroup = raw_event.get("subgroup")
    if subgroup is not None:
        try:
            subgroup = int(subgroup)
        except (ValueError, TypeError):
            subgroup = None

    event_id = str(raw_event.get("event_id") or raw_event.get("id") or f"{date_str}_{period}_{discipline}_{subgroup}")
    room = raw_event.get("room") or ""
    shelter = raw_event.get("shelter") or ""
    teacher = raw_event.get("teacher_name") or _extract_teacher_name(
        raw_event.get("teacher") or raw_event.get("instructor")
    )
    zoom_url = (
        raw_event.get("online_link")
        or raw_event.get("zoom_url")
        or raw_event.get("zoom")
        or raw_event.get("link")
        or ""
    )
    comment = raw_event.get("comment") or raw_event.get("passcode") or ""
    is_shifted = bool(raw_event.get("is_evening_slot_shifted") or raw_event.get("is_shifted"))

    return ScheduleEvent(
        event_id=event_id,
        discipline=discipline,
        course_name=course_name,
        event_type=event_type,
        subgroup=subgroup,
        date=date_str,
        period=period,
        start_utc=start_utc,
        end_utc=end_utc,
        room=room,
        shelter=shelter,
        teacher=teacher,
        zoom_url=zoom_url,
        comment=comment,
        is_shifted=is_shifted,
    )


def fetch_kse_schedule(
    token: str = "",
    from_date: str | date | None = None,
    till_date: str | date | None = None,
) -> list[ScheduleEvent]:
    """Fetch schedule from KSE API (https://api.kse.today/schedule).

    Automatically chunks date queries to comply with KSE API's max range limits.
    Raises AuthError on 401/403 and ConnectionError on network failures.
    """
    if from_date is None:
        from_date = date.today()
    if till_date is None:
        from datetime import timedelta

        till_date = (from_date if isinstance(from_date, date) else date.fromisoformat(from_date)) + timedelta(days=6)

    start_d = from_date if isinstance(from_date, date) else date.fromisoformat(from_date)
    end_d = till_date if isinstance(till_date, date) else date.fromisoformat(till_date)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_events: list[ScheduleEvent] = []
    seen_ids: set[str] = set()

    from datetime import timedelta

    curr_start = start_d
    while curr_start <= end_d:
        curr_end = min(curr_start + timedelta(days=6), end_d)
        from_str = curr_start.isoformat()
        till_str = curr_end.isoformat()

        url = f"{KSE_API_BASE}/schedule"
        params = {"from": from_str, "till": till_str}

        logger.info(f"Fetching KSE schedule chunk {from_str} to {till_str}")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
        except requests.RequestException as e:
            logger.debug(f"KSE schedule connection failed: {e}")
            raise ConnectionError(f"Failed to connect to KSE API: {e}")

        if response.status_code in (401, 403):
            logger.debug(f"KSE token rejected by API with status {response.status_code}")
            raise AuthError(f"KSE authentication failed: status {response.status_code}")

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise ConnectionError(f"KSE API returned error: {e}")

        try:
            data = response.json()
        except ValueError:
            logger.debug("KSE returned invalid JSON")
            raise ConnectionError("Invalid JSON from KSE API")

        raw_events_container = data.get("events", [])
        if isinstance(raw_events_container, list):
            for item in raw_events_container:
                if isinstance(item, list):
                    for sub_item in item:
                        if isinstance(sub_item, dict):
                            ev = _parse_single_event(sub_item)
                            if ev and ev.event_id not in seen_ids:
                                seen_ids.add(ev.event_id)
                                all_events.append(ev)
                elif isinstance(item, dict):
                    ev = _parse_single_event(item)
                    if ev and ev.event_id not in seen_ids:
                        seen_ids.add(ev.event_id)
                        all_events.append(ev)

        curr_start = curr_end + timedelta(days=1)

    logger.info(f"Successfully fetched and parsed {len(all_events)} KSE schedule events")
    return all_events
