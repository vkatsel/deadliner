from dataclasses import dataclass
from datetime import datetime


class AuthError(Exception):
    """Raised when a connector rejects the supplied credentials."""


@dataclass
class Assignment:
    platform: str
    course_shortname: str
    title: str
    due_utc: datetime
    url: str = ""


@dataclass(frozen=True)
class ScheduleEvent:
    event_id: str
    discipline: str
    course_name: str
    event_type: str  # "lecture" | "practice" | "other"
    subgroup: int | None
    date: str  # "YYYY-MM-DD"
    period: int  # 1..8
    start_utc: datetime
    end_utc: datetime
    room: str = ""
    shelter: str = ""
    teacher: str = ""
    zoom_url: str = ""
    comment: str = ""
    is_shifted: bool = False

