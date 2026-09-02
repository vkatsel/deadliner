from datetime import datetime

from deadliner.models import Assignment, ScheduleEvent


def format_assignment(assignment: Assignment, now: datetime, local_tz) -> str:
    # Convert to local time BEFORE any classification — a 21:00 UTC deadline
    # is 00:00 in Kyiv, and it is the LOCAL midnight that matters to the user.
    local_due = assignment.due_utc.astimezone(local_tz)

    platform_prefix = f"\033[94m[{assignment.platform}]\033[0m "
    if assignment.course_shortname:
        prefix = f"{platform_prefix}\033[96m[{assignment.course_shortname}]\033[0m "
    else:
        prefix = platform_prefix

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


def format_schedule_event(event: ScheduleEvent, local_tz) -> str:
    local_start = event.start_utc.astimezone(local_tz)
    local_end = event.end_utc.astimezone(local_tz)

    type_ua = (
        "Лекція"
        if event.event_type == "lecture"
        else "Практика"
        if event.event_type == "practice"
        else event.event_type.capitalize()
    )

    prefix = "\033[94m[kse]\033[0m "
    if event.discipline:
        prefix += f"\033[96m[{event.discipline}]\033[0m "

    title_str = f"\033[1m{event.course_name}\033[0m ({type_ua})"
    if event.subgroup is not None:
        title_str += f" [Група {event.subgroup}]"

    date_str = local_start.strftime("%a %d %b")
    time_str = f"\033[95m{local_start.strftime('%H:%M')}-{local_end.strftime('%H:%M')}\033[0m"

    details = []
    if event.room:
        details.append(f"Ауд. {event.room}")
    if event.shelter:
        details.append(f"Укриття {event.shelter}")
    if event.teacher:
        details.append(event.teacher)

    details_str = f" — {' | '.join(details)}" if details else ""
    return f"{prefix}{title_str} — \033[92m{date_str}\033[0m — {time_str}{details_str}"


def sort_schedule_events(events: list[ScheduleEvent]) -> list[ScheduleEvent]:
    return sorted(events, key=lambda e: (e.start_utc, e.period, e.discipline, e.course_name))

