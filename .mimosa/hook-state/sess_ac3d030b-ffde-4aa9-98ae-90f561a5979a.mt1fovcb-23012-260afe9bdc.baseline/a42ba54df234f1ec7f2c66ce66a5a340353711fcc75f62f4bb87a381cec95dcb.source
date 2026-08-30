"""tests/test_event_bus.py — تست سیستم عصبی اختاپوس."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# import octopus_core
OCTOPUS_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(OCTOPUS_ROOT) not in sys.path:
    sys.path.insert(0, str(OCTOPUS_ROOT))

from octopus_core.event_bus import EventBus, SyncEventBus


class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_bus_")
        self.bus = EventBus(persist_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_publish_and_subscribe(self):
        received = []
        def handler(ev):
            received.append(ev)
        self.bus.subscribe("test.topic", handler)
        eid = self.bus.publish("test.topic", {"msg": "hello"}, correlation_id="cid-1")
        self.assertTrue(eid.startswith("EVT-"))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["payload"]["msg"], "hello")
        self.assertEqual(received[0]["correlation_id"], "cid-1")

    def test_persistence_jsonl(self):
        self.bus.publish("a.b", {"v": 1})
        self.bus.publish("a.b", {"v": 2})
        path = Path(self.tmpdir) / "a.b.jsonl"
        self.assertTrue(path.exists())
        lines = path.read_text("utf-8").strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["payload"]["v"], 1)

    def test_query(self):
        self.bus.publish("x.y", {"v": 10})
        self.bus.publish("x.y", {"v": 20})
        results = self.bus.query(topic="x.y", n=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["payload"]["v"], 10)

    def test_unsubscribe(self):
        received = []
        sid = self.bus.subscribe("t", lambda ev: received.append(ev))
        self.bus.publish("t", {"v": 1})
        self.assertEqual(len(received), 1)
        self.bus.unsubscribe("t", sid)
        self.bus.publish("t", {"v": 2})
        self.assertEqual(len(received), 1)  # no more delivery

    def test_fail_soft_handler_error(self):
        def bad_handler(ev):
            raise RuntimeError("boom")
        self.bus.subscribe("bad", bad_handler)
        # publish should not crash even if handler crashes
        eid = self.bus.publish("bad", {"v": 1})
        self.assertTrue(eid.startswith("EVT-"))


class TestSyncEventBus(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_syncbus_")
        self.bus = SyncEventBus(persist_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_queue_delivery(self):
        import queue as qmod
        q = self.bus.subscribe_queue("q.topic", maxsize=10)
        self.bus.publish("q.topic", {"msg": "queued"})
        item = q.get(timeout=1.0)
        self.assertEqual(item["payload"]["msg"], "queued")


if __name__ == "__main__":
    unittest.main()
