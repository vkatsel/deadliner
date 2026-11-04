from __future__ import annotations

import pytest

from deadliner import scheduler


@pytest.fixture(autouse=True)
def _isolate_notifications_and_logs(monkeypatch, tmp_path, request):
    """Prevent tests from spawning real OS notifications or writing to ~/.deadliner/sync.log."""
    log_dir = tmp_path / ".deadliner"
    monkeypatch.setattr(scheduler, "DEADLINER_DIR", log_dir)
    monkeypatch.setattr(scheduler, "LOG_FILE", log_dir / "sync.log")

    if request.node.fspath.basename != "test_notifier.py":
        monkeypatch.setattr("deadliner.notifier.notify", lambda title, message: False)
