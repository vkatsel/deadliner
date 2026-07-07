from datetime import datetime

from deadliner.models import Assignment


def format_assignment(assignment: Assignment, now: datetime, local_tz) -> str:
    # Convert to local time BEFORE any classification — a 21:00 UTC deadline
    # is 00:00 in Kyiv, and it is the LOCAL midnight that matters to the user.
    local_due = assignment.due_utc.astimezone(local_tz)

    if assignment.course_shortname:
        prefix = f"\033[96m[{assignment.course_shortname}]\033[0m "
    else:
        prefix = ""

    remaining = assignment.due_utc - now
    total_seconds = int(remaining.total_seconds())
    if total_seconds >= 0:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        countdown = f"\033[92m{days}d {hours}h\033[0m"
    else:
        countdown = "\033[91moverdue\033[0m"

    time_str = f"\033[95m{local_due.strftime('%H:%M')}\033[0m"
    title_str = f"\033[1m{assignment.title}\033[0m"

    line = f"{prefix}{title_str} — {countdown} — {time_str}"

    if local_due.hour == 0 and local_due.minute == 0:
        line += " \033[93mmidnight cutoff\033[0m"

    return line


def sort_assignments(assignments: list[Assignment]) -> list[Assignment]:
    return sorted(assignments, key=lambda a: (a.due_utc, a.course_shortname, a.title))
