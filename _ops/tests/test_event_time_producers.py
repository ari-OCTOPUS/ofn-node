# -*- coding: utf-8 -*-
"""T48 (دستور #۸ §۳): dual-write افزودنی event-time در spine.

میکرد: migration idempotent · legacy flag خودکار · clock-skew بدون اصلاح ·
گذر occurred_at/منبع از آداپتور · بدون منبع = legacy (نه تزریق ساعت)."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sys

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "spine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ["OCTOPUS_WIRE_SPINE"] = "1"

import event_spine  # noqa: E402

NOW = datetime.now(timezone.utc)


def _mk(tmp_path):
    return event_spine.EventSpine(path=tmp_path / "spine-test.db")


def test_migration_additive_and_idempotent(tmp_path):
    sp = _mk(tmp_path)
    cols = [c[1] for c in sp._conn.execute("PRAGMA table_info(events)")]
    for c in ("occurred_at_real", "event_time_source", "time_precision",
              "legacy_no_event_time", "clock_skew"):
        assert c in cols
    sp.close()
    sp2 = _mk(tmp_path)          # دفعهٔ دوم بدون خطا
    sp2.close()


def test_publish_with_real_source_marks_non_legacy(tmp_path):
    sp = _mk(tmp_path)
    sp.publish({"event_type": "delivered", "domain": "telegram",
                "correlation_id": "c1", "producer": "t",
                "occurred_at": NOW.isoformat(),
                "event_time_source": "telegram_message_date",
                "time_precision": "1s", "payload": {}})
    row = sp.events(domain="telegram")[0]
    assert row["legacy_no_event_time"] == 0
    assert row["event_time_source"] == "telegram_message_date"
    assert row["schema_version"] == 2
    assert row["clock_skew"] == ""


def test_publish_without_source_is_legacy_not_injected(tmp_path):
    sp = _mk(tmp_path)
    sp.publish({"event_type": "failed", "domain": "provider",
                "correlation_id": "c2", "producer": "t", "payload": {}})
    row = sp.events(domain="provider")[0]
    assert row["legacy_no_event_time"] == 1
    assert row["event_time_source"] == "write_clock_derived"
    assert row["occurred_at_real"] is None


def test_clock_skew_suspected_without_autocorrect(tmp_path):
    sp = _mk(tmp_path)
    future = (NOW + timedelta(minutes=2)).isoformat()   # ساعت منبع جلوتر
    sp.publish({"event_type": "delivered", "domain": "telegram",
                "correlation_id": "c3", "producer": "t",
                "occurred_at": future,
                "event_time_source": "telegram_message_date",
                "time_precision": "1s", "payload": {}})
    row = sp.events(domain="telegram")[0]
    assert row["clock_skew"] == "CLOCK_SKEW_SUSPECTED"
    assert row["occurred_at"].startswith(future[:19])    # بدون اصلاح خودکار


def test_adapter_passes_event_time(tmp_path):
    import spine_adapters as sa
    sp = _mk(tmp_path)
    out = sa.emit_event(event_type="accepted-measurement", domain="provider",
                        correlation_id="c4", producer="router", trust="DETERMINISTIC",
                        occurred_at=NOW.isoformat(),
                        event_time_source="router_request_ts", time_precision="ms",
                        payload={"x": 1}, spine=sp)
    assert out["published"] is True
    row = sp.events(domain="provider")[0]
    assert row["event_time_source"] == "router_request_ts" and row["legacy_no_event_time"] == 0
    sp.close()


def test_adapter_without_source_keeps_legacy_path(tmp_path):
    import spine_adapters as sa
    sp = _mk(tmp_path)
    sa.emit_event(event_type="failed", domain="provider", correlation_id="c5",
                  producer="legacy_caller", payload={}, spine=sp)
    row = sp.events(domain="provider")[0]
    assert row["legacy_no_event_time"] == 1
    sp.close()
