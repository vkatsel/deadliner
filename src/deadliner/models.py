from dataclasses import dataclass
from datetime import datetime

@dataclass
class Assignment:
    platform: str
    course_shortname: str
    title: str
    due_utc: datetime
    url: str = ""
