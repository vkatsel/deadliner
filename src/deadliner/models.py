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
