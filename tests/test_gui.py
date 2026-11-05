from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
import types

import pytest

from deadliner import auth, cli, gui, gui_bridge
from deadliner.models import Assignment, AuthError, ScheduleEvent
from deadliner.storage import DataStore, InMemoryStore, SyncRecord


def test_in_memory_store_satisfies_protocol():
    store = InMemoryStore()
    assert isinstance(store, DataStore)
    assert store.engine_name == "in-memory"
    assert store.get_deadlines() == []
    assert store.get_schedule() == []

    now = datetime.now(timezone.utc)
    a1 = Assignment(
        platform="moodle",
        course_shortname="SE-202",
        title="Lab 5",
        due_utc=now + timedelta(hours=10),
        url="https://teaching.kse.org.ua/mod/assign/view.php?id=10",
        is_submitted=False,
    )
    a2 = Assignment(
        platform="classroom",
        course_shortname="LIN-ALG",
        title="Homework 3",
        due_utc=now + timedelta(days=4),
        is_submitted=True,
    )
    store.save_deadlines([a1, a2])
    assert len(store.get_deadlines()) == 2
    assert store.last_deadlines_fetch is not None

    ev = ScheduleEvent(
        event_id="ev-1",
        discipline="SE",
        course_name="Software Engineering",
        event_type="lecture",
        subgroup=None,
        date="2026-11-06",
        period=2,
        start_utc=now + timedelta(hours=2),
        end_utc=now + timedelta(hours=3, minutes=20),
        room="204",
        shelter="B1",
        teacher="Prof. K",
    )
    store.save_schedule([ev])
    assert len(store.get_schedule()) == 1

    store.record_sync(SyncRecord(timestamp_utc=now, target="all", created=2, updated=1))
    assert len(store.get_sync_history()) == 1

    snap = store.get_analytics_snapshot()
    assert snap["total_deadlines"] == 2
    assert snap["submitted_count"] == 1
    assert snap["pending_count"] == 1
    assert snap["urgent_24h_count"] == 1
    assert snap["completion_rate"] == 50
    assert snap["total_classes"] == 1
    assert snap["lectures_count"] == 1
    assert snap["sync_runs_session"] == 1
    assert len(snap["courses_breakdown"]) == 2


def test_serialize_assignment_urgency_and_midnight():
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    # Midnight in UTC
    midnight_due = datetime(2026, 11, 6, 0, 0, tzinfo=timezone.utc)
    a_crit = Assignment(
        platform="moodle",
        course_shortname="ALGO",
        title="Quiz",
        due_utc=midnight_due,
        is_submitted=False,
    )
    ser = gui_bridge.serialize_assignment(a_crit, now=now, local_tz=timezone.utc)
    assert ser["urgency"] == "critical"
    assert ser["is_midnight_cutoff"] is True
    assert ser["countdown_en"] == "12h 0m"

    a_sub = Assignment(
        platform="moodle",
        course_shortname="ALGO",
        title="Done Task",
        due_utc=midnight_due,
        is_submitted=True,
    )
    ser_sub = gui_bridge.serialize_assignment(a_sub, now=now, local_tz=timezone.utc)
    assert ser_sub["urgency"] == "submitted"
    assert ser_sub["countdown_en"] == "Submitted"
    assert ser_sub["countdown_ua"] == "Здано"

    a_overdue = Assignment(
        platform="classroom",
        course_shortname="HIST",
        title="Essay",
        due_utc=now - timedelta(hours=5),
        is_submitted=False,
    )
    ser_over = gui_bridge.serialize_assignment(a_overdue, now=now, local_tz=timezone.utc)
    assert ser_over["urgency"] == "overdue"
    assert ser_over["countdown_en"].startswith("-")


def test_serialize_schedule_event_semantics():
    start = datetime(2026, 11, 6, 8, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 6, 9, 20, tzinfo=timezone.utc)
    lec = ScheduleEvent(
        event_id="1",
        discipline="CS",
        course_name="Algorithms",
        event_type="lecture",
        subgroup=None,
        date="2026-11-06",
        period=1,
        start_utc=start,
        end_utc=end,
        room="302",
        is_shifted=True,
    )
    s_lec = gui_bridge.serialize_schedule_event(lec, local_tz=timezone.utc)
    assert s_lec["semantic_color"] == "sage"
    assert s_lec["type_label_en"] == "Lecture"
    assert s_lec["is_shifted"] is True

    prac = ScheduleEvent(
        event_id="2",
        discipline="CS",
        course_name="Algorithms Lab",
        event_type="practice",
        subgroup=2,
        date="2026-11-06",
        period=2,
        start_utc=start,
        end_utc=end,
    )
    s_prac = gui_bridge.serialize_schedule_event(prac, local_tz=timezone.utc)
    assert s_prac["semantic_color"] == "peacock"
    assert s_prac["subgroup"] == 2


def test_gui_api_fetch_and_sync_workflows(monkeypatch):
    now = datetime.now(timezone.utc)
    sample_assignment = Assignment(
        platform="moodle",
        course_shortname="SE",
        title="Project Milestone",
        due_utc=now + timedelta(days=2),
        is_submitted=False,
    )
    sample_event = ScheduleEvent(
        event_id="kse-10",
        discipline="SE",
        course_name="Software Engineering",
        event_type="practice",
        subgroup=1,
        date="2026-11-07",
        period=3,
        start_utc=now + timedelta(days=1),
        end_utc=now + timedelta(days=1, hours=1, minutes=20),
    )

    monkeypatch.setattr(
        cli,
        "_load_credentials",
        lambda: ("https://teaching.kse.org.ua", "m-tok", "g-tok", "kse-tok"),
    )
    monkeypatch.setattr(cli, "_collect_assignments", lambda *a, **kw: ([sample_assignment], []))
    monkeypatch.setattr(
        gui_bridge.kse_fetcher,
        "fetch_kse_schedule",
        lambda **kw: [sample_event],
    )
    monkeypatch.setattr(
        gui_bridge.calendar_sync,
        "sync_to_calendar",
        lambda items, tok, return_details=False: (
            1,
            0,
            0,
            [(sample_assignment, "created", None)],
        ),
    )
    monkeypatch.setattr(
        gui_bridge.calendar_sync,
        "sync_schedule_to_calendar",
        lambda events, tok, **kw: (
            1,
            0,
            0,
            0,
            [(sample_event, "created")],
        ),
    )
    monkeypatch.setattr(gui_bridge.scheduler, "append_sync_log", lambda msg: None)

    api = gui_bridge.DeadlinerGuiApi()

    d_res = api.fetch_deadlines()
    assert d_res["ok"] is True
    assert len(d_res["deadlines"]) == 1
    assert d_res["deadlines"][0]["title"] == "Project Milestone"

    s_res = api.fetch_schedule(days=7)
    assert s_res["ok"] is True
    assert len(s_res["schedule"]) == 1
    assert s_res["schedule"][0]["course_name"] == "Software Engineering"

    all_sync = api.sync_all(days=7)
    assert all_sync["ok"] is True
    assert all_sync["deadlines_sync"]["created"] == 1
    assert all_sync["schedule_sync"]["created"] == 1
    assert all_sync["analytics"]["sync_runs_session"] == 2


def test_gui_api_connect_moodle_and_kse_token(tmp_path, monkeypatch):
    cfg_file = tmp_path / ".deadliner.json"
    monkeypatch.setattr(cli, "CONFIG_PATH", cfg_file)
    monkeypatch.setattr(auth, "CONFIG_PATH", cfg_file)
    monkeypatch.setattr(gui_bridge.kse_auth, "CONFIG_PATH", cfg_file)
    monkeypatch.setattr(
        auth,
        "authenticate_moodle_credentials",
        lambda url, u, p: "verified-moodle-tok",
    )
    monkeypatch.setattr(gui_bridge.scheduler, "append_sync_log", lambda msg: None)
    monkeypatch.setattr(
        cli,
        "_load_credentials",
        lambda: ("https://teaching.kse.org.ua", "verified-moodle-tok", "", ""),
    )

    api = gui_bridge.DeadlinerGuiApi()
    res = api.connect_moodle("teaching.kse.org.ua", "student@kse.org.ua", "secret123")
    assert res["ok"] is True
    assert res["base_url"] == "https://teaching.kse.org.ua"

    monkeypatch.setattr(gui_bridge.kse_auth, "verify_kse_token", lambda tok: True)
    kse_res = api.save_kse_token("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig")
    assert kse_res["ok"] is True


def test_should_default_to_gui_and_cli_dispatch(monkeypatch):
    monkeypatch.delenv("DEADLINER_DEFAULT_GUI", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert gui.should_default_to_gui() is False

    monkeypatch.setenv("DEADLINER_DEFAULT_GUI", "1")
    assert gui.should_default_to_gui() is True

    monkeypatch.setenv("DEADLINER_DEFAULT_GUI", "0")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert gui.should_default_to_gui() is True


def test_launch_gui_invokes_pywebview(monkeypatch):
    created_windows = []
    started = []

    fake_webview = types.ModuleType("webview")

    def fake_create_window(**kwargs):
        created_windows.append(kwargs)
        return object()

    def fake_start(**kwargs):
        started.append(kwargs)

    fake_webview.create_window = fake_create_window
    fake_webview.start = fake_start
    monkeypatch.setitem(sys.modules, "webview", fake_webview)

    rc = gui.launch_gui(debug=True)
    assert rc == 0
    assert len(created_windows) == 1
    assert created_windows[0]["background_color"] == "#050508"
    assert started == [{"debug": True}]


def test_cli_gui_subcommand_routes_to_cmd_gui(monkeypatch):
    called = []
    monkeypatch.setattr(gui, "launch_gui", lambda debug=False, store=None: called.append(debug) or 0)
    with pytest.raises(SystemExit) as exc:
        cli.main(["gui", "--debug"])
    assert exc.value.code == 0
    assert called == [True]


def test_gui_error_classification_and_field_validation(monkeypatch):
    api = gui_bridge.DeadlinerGuiApi()

    # Empty username validation
    r1 = api.connect_moodle("https://teaching.kse.org.ua", "", "pass")
    assert r1["ok"] is False
    assert r1["error_code"] == "VALIDATION_ERROR"
    assert r1["field"] == "moodleUserInput"

    # Empty password validation with SSO hint
    r2 = api.connect_moodle("https://teaching.kse.org.ua", "student@kse.org.ua", "")
    assert r2["ok"] is False
    assert r2["field"] == "moodlePassInput"
    assert "Google SSO" in r2["hint"]

    # Invalid 24h time validation in scheduler
    r3 = api.configure_scheduler(True, "29:99")
    assert r3["ok"] is False
    assert r3["error_code"] == "VALIDATION_ERROR"
    assert r3["field"] == "cronTimeInput"

    # When all deadline sources fail with AuthError warning, promote to structured error
    monkeypatch.setattr(
        cli,
        "_load_credentials",
        lambda: ("https://teaching.kse.org.ua", "bad-tok", "", ""),
    )
    monkeypatch.setattr(
        cli,
        "_collect_assignments",
        lambda *a, **kw: ([], ["warning: moodle authentication failed: Invalid token"]),
    )
    r4 = api.fetch_deadlines()
    assert r4["ok"] is False
    assert r4["error_code"] == "AUTH_ERROR"
    assert r4["action_view"] == "connections"
    assert "Moodle" in r4["hint"]


