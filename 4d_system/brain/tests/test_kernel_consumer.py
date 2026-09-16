"""Tests for kernel_consumer.py (body-side)."""
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path("F:/backup/4d_system").resolve()))

from brain import kernel_consumer as kc


@pytest.fixture
def temp_bridge():
    """Create a temporary kernel bridge directory with sample outputs."""
    with tempfile.TemporaryDirectory() as tmp:
        kernel_root = Path(tmp) / "research-spec-compiler"
        out_dir = kernel_root / "body_bridge" / "output"
        out_dir.mkdir(parents=True)

        manifest = {
            "kernel_name": "Cognitive Kernel 0.1",
            "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "integrity": {"rsc.py": "a" * 64},
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        dashboard = {
            "tally": {"INTEGRATE": 2, "OPTIMIZE": 1, "REJECTED": 0, "FAIL": 0},
            "high_priority_adr": [],
            "body_bridge_status": {"fresh_events_available": True, "last_sync": "2026-07-14T12:00:00Z"},
        }
        (out_dir / "kernel_dashboard.json").write_text(json.dumps(dashboard), encoding="utf-8")

        adr_feed = {
            "adrs": [
                {"adr_number": 1, "title": "Test ADR", "verdict": "INTEGRATE"},
            ],
            "total": 1,
        }
        (out_dir / "adr_feed.json").write_text(json.dumps(adr_feed), encoding="utf-8")

        with (out_dir / "verdict_stream.jsonl").open("w", encoding="utf-8") as f:
            past_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
            f.write(json.dumps({"claim_id": "ADR-001", "verdict": "INTEGRATE", "timestamp": past_ts}) + "\n")

        # Write a dummy rsc.py for health check
        (kernel_root / "rsc.py").write_text("print('ok')\n", encoding="utf-8")

        yield kernel_root, out_dir


class TestKernelConsumer:
    def test_read_manifest(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        manifest = consumer.read_manifest()
        assert manifest is not None
        assert manifest["kernel_name"] == "Cognitive Kernel 0.1"

    def test_read_dashboard(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        dash = consumer.read_dashboard()
        assert dash is not None
        assert dash["tally"]["INTEGRATE"] == 2

    def test_read_adr_feed(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        feed = consumer.read_adr_feed()
        assert feed is not None
        assert feed["adrs"][0]["adr_number"] == 1

    def test_read_verdict_stream(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        events = consumer.read_verdict_stream()
        assert len(events) == 1
        assert events[0]["claim_id"] == "ADR-001"

    def test_read_verdict_stream_since(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        since = datetime.now(timezone.utc) + timedelta(hours=1)
        events = consumer.read_verdict_stream(since=since)
        assert events == []

    def test_check_kernel_health(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        health = consumer.check_kernel_health()
        assert health["reachable"] is True
        assert health["manifest_fresh"] is True
        assert health["integrity_ok"] is True

    def test_suggest_automation_action(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        action = consumer.suggest_automation_action()
        assert "action" in action
        assert "priority" in action

    def test_suggest_review_on_rejected(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        # Inject a rejected dashboard
        dashboard = {
            "tally": {"INTEGRATE": 0, "OPTIMIZE": 0, "REJECTED": 1, "FAIL": 0},
            "high_priority_adr": [],
            "body_bridge_status": {"fresh_events_available": True, "last_sync": "2026-07-14T12:00:00Z"},
        }
        (out_dir / "kernel_dashboard.json").write_text(json.dumps(dashboard), encoding="utf-8")
        consumer = kc.KernelConsumer(kernel_root)
        action = consumer.suggest_automation_action()
        assert action["action"] == "review"
        assert action["priority"] == "high"

    def test_import_no_side_effects(self, temp_bridge):
        # Just importing should not read files or emit events
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        # Before any method call, nothing should have happened
        assert consumer._manifest is None

    def test_lazy_event_import(self, temp_bridge):
        kernel_root, out_dir = temp_bridge
        consumer = kc.KernelConsumer(kernel_root)
        # publish_body_event should survive even if brain.events is missing
        try:
            consumer.publish_body_event("test.event", "summary")
        except Exception:
            pytest.fail("publish_body_event should not raise on missing events module")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
