"""Pluggable storage and caching abstraction for Deadliner.

Designed as an extensible repository layer so the Desktop GUI and CLI can operate
against an in-memory session store today (`InMemoryStore`) and seamlessly swap to
a persistent SQLite engine (`SQLiteStore`) in future milestones without changing
calling code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from deadliner.models import Assignment, ScheduleEvent


@dataclass
class SyncRecord:
    """Represents a single synchronization run summary."""

    timestamp_utc: datetime
    target: str  # "deadlines" | "schedule" | "all"
    created: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0
    warnings: list[str] = field(default_factory=list)
    success: bool = True


@runtime_checkable
class DataStore(Protocol):
    """Protocol for Deadliner data persistence and analytics."""

    @property
    def engine_name(self) -> str:
        """Human-readable identifier of the storage engine."""
        ...

    def get_deadlines(self) -> list[Assignment]:
        """Return cached assignments."""
        ...

    def save_deadlines(self, assignments: list[Assignment]) -> None:
        """Persist a batch of assignments."""
        ...

    def get_schedule(self) -> list[ScheduleEvent]:
        """Return cached schedule events."""
        ...

    def save_schedule(self, events: list[ScheduleEvent]) -> None:
        """Persist a batch of schedule events."""
        ...

    def record_sync(self, record: SyncRecord) -> None:
        """Record a sync operation in history."""
        ...

    def get_sync_history(self, limit: int = 20) -> list[SyncRecord]:
        """Return recent sync records, newest first."""
        ...

    def get_analytics_snapshot(self) -> dict:
        """Compute summary metrics for the dashboard and analytics placeholder."""
        ...


class InMemoryStore:
    """Zero-overhead in-memory implementation of DataStore for the current session."""

    def __init__(self) -> None:
        self._deadlines: list[Assignment] = []
        self._schedule: list[ScheduleEvent] = []
        self._sync_history: list[SyncRecord] = []
        self._last_deadlines_fetch: datetime | None = None
        self._last_schedule_fetch: datetime | None = None

    @property
    def engine_name(self) -> str:
        return "in-memory"

    @property
    def last_deadlines_fetch(self) -> datetime | None:
        return self._last_deadlines_fetch

    @property
    def last_schedule_fetch(self) -> datetime | None:
        return self._last_schedule_fetch

    def get_deadlines(self) -> list[Assignment]:
        return list(self._deadlines)

    def save_deadlines(self, assignments: list[Assignment]) -> None:
        self._deadlines = list(assignments)
        self._last_deadlines_fetch = datetime.now(timezone.utc)

    def get_schedule(self) -> list[ScheduleEvent]:
        return list(self._schedule)

    def save_schedule(self, events: list[ScheduleEvent]) -> None:
        self._schedule = list(events)
        self._last_schedule_fetch = datetime.now(timezone.utc)

    def record_sync(self, record: SyncRecord) -> None:
        self._sync_history.insert(0, record)
        if len(self._sync_history) > 100:
            self._sync_history = self._sync_history[:100]

    def get_sync_history(self, limit: int = 20) -> list[SyncRecord]:
        return self._sync_history[:limit]

    def get_analytics_snapshot(self) -> dict:
        now = datetime.now(timezone.utc)
        total_deadlines = len(self._deadlines)
        submitted_count = sum(1 for a in self._deadlines if a.is_submitted)
        pending_count = total_deadlines - submitted_count
        urgent_24h_count = sum(
            1
            for a in self._deadlines
            if not a.is_submitted and 0 <= (a.due_utc - now).total_seconds() <= 86400
        )
        overdue_count = sum(
            1
            for a in self._deadlines
            if not a.is_submitted and (a.due_utc - now).total_seconds() < 0
        )

        by_course: dict[str, dict[str, int]] = {}
        for a in self._deadlines:
            course = a.course_shortname or a.platform
            bucket = by_course.setdefault(course, {"total": 0, "submitted": 0, "pending": 0})
            bucket["total"] += 1
            if a.is_submitted:
                bucket["submitted"] += 1
            else:
                bucket["pending"] += 1

        lectures_count = sum(1 for e in self._schedule if e.event_type == "lecture")
        practices_count = sum(1 for e in self._schedule if e.event_type == "practice")

        completion_rate = (
            round((submitted_count / total_deadlines) * 100) if total_deadlines > 0 else 0
        )

        return {
            "engine": self.engine_name,
            "persistence_enabled": False,
            "total_deadlines": total_deadlines,
            "submitted_count": submitted_count,
            "pending_count": pending_count,
            "urgent_24h_count": urgent_24h_count,
            "overdue_count": overdue_count,
            "completion_rate": completion_rate,
            "total_classes": len(self._schedule),
            "lectures_count": lectures_count,
            "practices_count": practices_count,
            "courses_breakdown": [
                {"course": k, **v}
                for k, v in sorted(by_course.items(), key=lambda item: (-item[1]["pending"], item[0]))
            ],
            "sync_runs_session": len(self._sync_history),
            "last_sync_utc": (
                self._sync_history[0].timestamp_utc.isoformat() if self._sync_history else None
            ),
        }

