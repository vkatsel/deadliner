from datetime import datetime

from deadliner.models import Assignment


def format_assignment(assignment: Assignment, now: datetime, local_tz) -> str:
    # Convert to local time BEFORE any classification — a 21:00 UTC deadline
    # is 00:00 in Kyiv, and it is the LOCAL midnight that matters to the user.
    local_due = assignment.due_utc.astimezone(local_tz)

    if assignment.course_shortname:
        prefix = f"[{assignment.course_shortname}]"
    else:
        prefix = f"[Course ID: {assignment.title}]"

    remaining = assignment.due_utc - now
    total_seconds = int(remaining.total_seconds())
    if total_seconds >= 0:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        countdown = f"{days}d {hours}h"
    else:
        countdown = "overdue"

    time_str = local_due.strftime("%H:%M")
    line = f"{prefix} {assignment.title} — {countdown} — {time_str}"

    if local_due.hour == 0 and local_due.minute == 0:
        line += " midnight cutoff"

    return line


def sort_assignments(assignments: list[Assignment]) -> list[Assignment]:
    return sorted(assignments, key=lambda a: (a.due_utc, a.course_shortname, a.title))
