from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from deadliner.formatter import format_assignment, sort_assignments
from deadliner.models import Assignment
import re


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# --- TESTS for US-03 (midnight cutoff distinction) ---


def test_format_assignment_midnight_utc_kyiv_shows_midnight_cutoff():
    assignment = Assignment("moodle", "ECON101", "Final Exam", datetime(2024, 10, 14, 21, 0, 0, tzinfo=timezone.utc))
    now = datetime(2024, 10, 12, 10, 0, 0, tzinfo=timezone.utc)
    local_tz = ZoneInfo("Europe/Kyiv")

    result = format_assignment(assignment, now, local_tz)

    assert "00:00" in result, f"Expected '00:00' in output, got: {result!r}"
    assert "midnight cutoff" in result, f"Expected 'midnight cutoff' label, got: {result!r}"


def test_format_assignment_end_of_day_does_not_show_midnight_cutoff():
    assignment = Assignment("moodle", "ECON101", "Homework 3", datetime(2024, 10, 14, 20, 59, 0, tzinfo=timezone.utc))
    now = datetime(2024, 10, 12, 10, 0, 0, tzinfo=timezone.utc)
    local_tz = ZoneInfo("Europe/Kyiv")

    result = format_assignment(assignment, now, local_tz)

    assert "midnight cutoff" not in result, f"23:59 local must NOT be labeled 'midnight cutoff', got: {result!r}"


def test_format_assignment_includes_course_shortname_as_prefix():
    assignment = Assignment("moodle", "CS101", "Lab Report", datetime(2024, 11, 1, 12, 0, 0, tzinfo=timezone.utc))
    now = datetime(2024, 10, 30, 10, 0, 0, tzinfo=timezone.utc)
    local_tz = ZoneInfo("Europe/Kyiv")

    result = format_assignment(assignment, now, local_tz)

    assert "[CS101]" in result, f"Expected '[CS101]' prefix in output, got: {result!r}"


def test_format_assignment_empty_course_shortname_shows_fallback():
    assignment = Assignment("moodle", "", "Mystery Assignment", datetime(2024, 11, 5, 15, 0, 0, tzinfo=timezone.utc))
    now = datetime(2024, 11, 3, 10, 0, 0, tzinfo=timezone.utc)
    local_tz = ZoneInfo("Europe/Kyiv")

    result = strip_ansi(format_assignment(assignment, now, local_tz))

    assert "[Course ID:" not in result, f"Should not use fallback prefix, got: {result!r}"
    assert result.startswith("Mystery Assignment —"), f"Must start with title if no shortname, got: {result!r}"


# --- TESTS for US-02 (sorted deadline list) ---


def test_sort_assignments_out_of_order_returns_ascending():
    a1 = Assignment("moodle", "ECON101", "Quiz 1", datetime(2024, 10, 20, 10, 0, tzinfo=timezone.utc))
    a2 = Assignment("moodle", "CS101", "Lab 3", datetime(2024, 10, 15, 9, 0, tzinfo=timezone.utc))
    a3 = Assignment("moodle", "MATH201", "Homework 2", datetime(2024, 10, 18, 14, 0, tzinfo=timezone.utc))

    result = sort_assignments([a1, a2, a3])

    assert result == [a2, a3, a1], f"Expected sorted by due_utc ascending, got: {[r.title for r in result]}"


def test_sort_assignments_identical_due_dates_tiebreak_by_course_then_title():
    same_time = datetime(2024, 10, 20, 10, 0, tzinfo=timezone.utc)
    a1 = Assignment("moodle", "MATH201", "Homework", same_time)
    a2 = Assignment("moodle", "CS101", "Homework", same_time)
    a3 = Assignment("moodle", "CS101", "Assignment", same_time)

    result = sort_assignments([a1, a2, a3])

    # CS101 < MATH201; within CS101: "Assignment" < "Homework"
    assert result == [a3, a2, a1], f"Tiebreak failed, got: {[(r.course_shortname, r.title) for r in result]}"


def test_sort_assignments_empty_list_returns_empty():
    result = sort_assignments([])

    assert result == [], "sort_assignments([]) must return empty list, not raise"


def test_sort_assignments_single_item_returns_unchanged():
    a = Assignment("moodle", "CS101", "Lab 1", datetime(2024, 10, 15, 9, 0, tzinfo=timezone.utc))

    result = sort_assignments([a])

    assert result == [a], "Single-item list must be returned as-is"
