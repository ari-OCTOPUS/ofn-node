
import os, sys, tempfile, time, unittest, json
from pathlib import Path
sys.path.insert(0, "/opt/octopus/lab")
from ofn.organism.persistence.db import connect
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.contracts.events import make_event, validate_event
from ofn.organism.homeostasis.core import measure, transition
from ofn.organism.memory.episodic import remember, recall
from ofn.organism.identity.heartbeat import beat

class KernelTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.con = connect(Path(self.dir)/"o.db")
        self.k = EventKernel(self.con, maxsize=8)
        self.seen = []
        self.k.register("*", lambda ev: self.seen.append(ev["event_id"]))

    def test_duplicate_same_hash(self):
        ev = make_event("note", {"x": 1}, priority=40)
        a = self.k.accept(ev)
        b = self.k.accept(ev)
        self.assertEqual(a["status"], "committed")
        self.assertEqual(b["status"], "duplicate")

    def test_duplicate_id_different_hash(self):
        ev = make_event("note", {"x": 1}, priority=40)
        self.k.accept(ev)
        ev2 = dict(ev)
        ev2["payload"] = {"x": 2}
        ev2.pop("hash", None)
        r = self.k.accept(ev2)
        self.assertEqual(r["status"], "rejected")

    def test_unknown_schema(self):
        ev = make_event("note", {"x": 1})
        ev["schema_version"] = 99
        ev.pop("hash", None)
        r = self.k.accept(ev)
        self.assertEqual(r["status"], "rejected")
        self.assertIn("unknown_schema", r["error"])

    def test_invalid_quality(self):
        r = self.k.accept({"schema_version": 1})
        self.assertEqual(r["status"], "rejected")

    def test_crash_after_commit_before_dispatch(self):
        ev = make_event("note", {"x": 3}, priority=20)
        r = self.k.accept(ev)
        self.assertEqual(r["status"], "committed")
        # pending outbox exists; replay after "restart"
        k2 = EventKernel(self.con, maxsize=8)
        seen = []
        k2.register("*", lambda e: seen.append(e["event_id"]))
        n = k2.replay_pending()
        self.assertGreaterEqual(n, 1)
        self.assertIn(ev["event_id"], seen)

    def test_queue_saturation_safety_not_dropped(self):
        # fill queue after commits by putting dummy items
        for i in range(8):
            self.k.q.put_nowait((90, time.time(), f"dummy{i}", "h"))
        ev = make_event("safety", {"halt": True}, priority=1)
        r = self.k.accept(ev)
        self.assertEqual(r["status"], "committed")
        # outbox still has it even if queue was full
        row = self.con.execute("SELECT status FROM outbox WHERE event_id=?", (ev["event_id"],)).fetchone()
        self.assertEqual(row[0], "pending")

    def test_replay_idempotent(self):
        ev = make_event("note", {"x": 9})
        self.k.accept(ev)
        self.k.replay_pending()
        n2 = self.k.replay_pending()
        self.assertEqual(n2, 0)
        self.assertEqual(self.seen.count(ev["event_id"]), 1)

    def test_homeostasis_measure(self):
        m = measure()
        self.assertIn(m["health_state"], ("BOOTSTRAP","OBSERVING","STABLE","DEGRADED","SAFE_HALT","RECOVERING"))
        names = [s["name"] for s in m["signals"]]
        self.assertIn("MemAvailable_kB", names)

    def test_state_machine_pure(self):
        self.assertEqual(transition("BOOTSTRAP", "OBSERVING"), "OBSERVING")
        self.assertEqual(transition("OBSERVING", "SAFE_HALT"), "SAFE_HALT")
        self.assertEqual(transition("SAFE_HALT", "OBSERVING"), "RECOVERING")

    def test_episode_requires_source(self):
        ev = make_event("note", {"z": 1})
        self.k.accept(ev)
        eid = remember(self.con, ev["event_id"], "note", {"z": 1})
        rec = recall(self.con)
        self.assertEqual(rec[0]["source_event_id"], ev["event_id"])
        with self.assertRaises(ValueError):
            remember(self.con, "", "note", {"z": 1})

    def test_heartbeat(self):
        body = beat(self.con, {"health_state": "OBSERVING", "boot_id": "x"})
        self.assertEqual(body["organism_id"], "board-life-001")
        self.assertEqual(body["autonomy_state"], "PROPOSE_ONLY")

if __name__ == "__main__":
    unittest.main()
