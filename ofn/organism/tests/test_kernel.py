
import json
import os
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/opt/octopus/lab")
from ofn.organism.cognition.backend import (
    AskCascade,
    LocalCortex,
    NoRedirectHandler,
)
from ofn.organism.persistence.db import connect
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.contracts.events import make_event, validate_event
from ofn.organism.homeostasis.core import measure, transition
from ofn.organism.memory.episodic import remember, recall
from ofn.organism.identity.heartbeat import beat
from ofn.organism.identity.ledger import (
    IdentityChainError,
    append_identity_event,
    ensure_identity_genesis,
    verify_identity_chain,
)
from ofn.organism.runtime.app import (
    Handler,
    create_server,
    effective_measurement,
    serve,
    start_server,
)
from ofn.organism.runtime.public_status import write_public_status

class KernelTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.con = connect(Path(self.temp_dir.name) / "o.db")
        self.addCleanup(self.con.close)
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
        duplicate_eid = remember(
            self.con,
            ev["event_id"],
            "note",
            {"z": "duplicate attempt"},
        )
        rec = recall(self.con)
        self.assertEqual(rec[0]["source_event_id"], ev["event_id"])
        self.assertEqual(duplicate_eid, eid)
        self.assertEqual(
            self.con.execute(
                "SELECT COUNT(*) FROM episodes WHERE source_event_id=?",
                (ev["event_id"],),
            ).fetchone()[0],
            1,
        )
        with self.assertRaises(ValueError):
            remember(self.con, "", "note", {"z": 1})
        with self.assertRaises(ValueError):
            remember(self.con, "missing", "note", {"z": 1})
        with self.assertRaises(ValueError):
            remember(self.con, ev["event_id"], "wrong_type", {"z": 1})

    def test_local_cortex_rejects_noncanonical_loopback_urls(self):
        for url in (
            "http://localhost:8081",
            "https://127.0.0.1:8081",
            "http://127.0.0.1:9000",
            "http://192.168.0.180:8081",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    LocalCortex(base=url)

    def test_local_cortex_malformed_response_degrades_explicitly(self):
        class Response:
            status = 200

            def __init__(self, raw):
                self.raw = raw

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return self.raw

        class Opener:
            def __init__(self, raw):
                self.raw = raw

            def open(self, *_args, **_kwargs):
                return Response(self.raw)

        for raw in (b"[]", b'{"choices":[1]}', b'{"choices":[{"message":"x"}]}'):
            with self.subTest(raw=raw):
                cortex = LocalCortex()
                cortex.opener = Opener(raw)
                result = cortex.complete("probe")
                self.assertEqual(result["status"], "DEGRADED")
                self.assertEqual(
                    result["error"],
                    "empty_or_invalid_model_content",
                )

    def test_local_cortex_redirects_are_disabled(self):
        handler = NoRedirectHandler()
        self.assertIsNone(
            handler.redirect_request(
                None,
                None,
                302,
                "Found",
                {},
                "http://192.0.2.1/",
            )
        )
        cortex = LocalCortex()
        self.assertTrue(
            any(
                isinstance(item, NoRedirectHandler)
                for item in cortex.opener.handlers
            )
        )

    def test_duplicate_episode_migration_requires_owner_without_deletion(self):
        path = Path(self.temp_dir.name) / "legacy-duplicates.db"
        con = connect(path)
        con.execute("DROP INDEX episodes_source_event")
        con.execute(
            """
            INSERT INTO events(
                event_id,event_type,priority,payload_json,created_at,
                schema_version,hash,node_seq
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            ("source", "note", 50, "{}", 1.0, 1, "h", 1),
        )
        for index in (1, 2):
            con.execute(
                """
                INSERT INTO episodes(
                    episode_id,source_event_id,event_type,salience,
                    outcome,body_json,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (f"episode-{index}", "source", "note", 0.5, None, "{}", index),
            )
        con.close()
        with self.assertRaisesRegex(
            RuntimeError,
            "requires_owner_data_decision",
        ):
            connect(path)
        check = sqlite3.connect(path)
        try:
            count = check.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        finally:
            check.close()
        self.assertEqual(count, 2)

    def test_threaded_commit_and_episode_dispatch_are_serialized(self):
        self.k.register(
            "*",
            lambda event: remember(
                self.con,
                event["event_id"],
                event["event_type"],
                {"threaded": True},
            ),
        )
        errors = []

        def worker(index):
            try:
                result = self.k.accept(
                    make_event("threaded", {"index": index})
                )
                if result["status"] != "committed":
                    errors.append(result)
                self.k.replay_pending(limit=2)
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.k.replay_pending()
        self.assertEqual(errors, [])
        self.assertEqual(
            self.con.execute(
                "SELECT COUNT(*) FROM events WHERE event_type='threaded'"
            ).fetchone()[0],
            16,
        )
        self.assertEqual(
            self.con.execute(
                "SELECT COUNT(*) FROM episodes WHERE event_type='threaded'"
            ).fetchone()[0],
            16,
        )

    def test_heartbeat(self):
        body = beat(self.con, {"health_state": "OBSERVING", "boot_id": "x"})
        self.assertEqual(body["organism_id"], "board-life-001")
        self.assertEqual(body["autonomy_state"], "PROPOSE_ONLY")
        self.assertTrue(body["identity_chain_valid"])
        self.assertGreaterEqual(body["identity_chain_entries"], 2)

    def test_identity_chain_detects_tampering(self):
        ensure_identity_genesis(self.con, "boot-a")
        append_identity_event(
            self.con,
            "boot-a",
            "test_event",
            {"value": 1},
        )
        self.assertTrue(verify_identity_chain(self.con)["valid"])
        self.con.execute(
            "UPDATE identity_ledger SET payload_json=? WHERE sequence=2",
            ('{"value":2}',),
        )
        verification = verify_identity_chain(self.con)
        self.assertFalse(verification["valid"])
        self.assertIn("ENTRY_HASH_MISMATCH", verification["error"])
        with self.assertRaises(IdentityChainError):
            ensure_identity_genesis(self.con, "boot-b")

    def test_identity_chain_requires_genesis(self):
        with self.assertRaisesRegex(
            IdentityChainError,
            "FIRST_ENTRY_MUST_BE_CHAIN_GENESIS",
        ):
            append_identity_event(
                self.con,
                "boot-a",
                "not_genesis",
                {"value": 1},
            )

    def test_ask_cascade_rule_cache_local_and_owner(self):
        class SuccessfulCortex:
            calls = 0

            def complete(self, _text):
                self.calls += 1
                return {
                    "status": "LOW_CONFIDENCE",
                    "answer": "local answer",
                    "response_hash": "a" * 64,
                    "latency_ms": 1,
                    "usage": None,
                    "http_status": 200,
                    "error": None,
                }

        status = {
            "health_state": "OBSERVING",
            "local_cortex": "AVAILABLE",
            "identity_chain_valid": True,
        }
        cortex = SuccessfulCortex()
        cascade = AskCascade(self.con, cortex=cortex)
        rule = cascade.ask("ping", status)
        self.assertEqual(rule["route"], "deterministic_rule")
        local = cascade.ask("unmatched question", status)
        self.assertEqual(local["route"], "local_qwen")
        cached = cascade.ask("unmatched question", status)
        self.assertEqual(cached["route"], "cache")
        self.assertEqual(cortex.calls, 1)

        class FailedCortex:
            def complete(self, _text):
                return {
                    "status": "DEGRADED",
                    "answer": None,
                    "response_hash": "b" * 64,
                    "http_status": None,
                    "error": "simulated",
                }

        owner = AskCascade(self.con, cortex=FailedCortex()).ask(
            "different unmatched question",
            status,
        )
        self.assertEqual(owner["label"], "NEEDS_OWNER")

        class BrokenCacheConnection:
            def __init__(self, inner):
                self.inner = inner

            def execute(self, sql, *args, **kwargs):
                if "ask_cache" in str(sql):
                    raise sqlite3.OperationalError("simulated_cache_failure")
                return self.inner.execute(sql, *args, **kwargs)

        uncached = AskCascade(
            BrokenCacheConnection(self.con),
            cortex=SuccessfulCortex(),
        ).ask("cache failure question", status)
        self.assertEqual(uncached["route"], "local_qwen")
        self.assertEqual(uncached["label"], "LOW_CONFIDENCE")
        self.assertIn(
            "simulated_cache_failure",
            uncached["data"]["cache_store_error"],
        )

    def test_recall_and_ask_http_endpoints(self):
        event = make_event("known", {"value": 7})
        self.k.accept(event)
        self.k.replay_pending()
        remember(
            self.con,
            event["event_id"],
            event["event_type"],
            {"value": 7},
        )
        httpd = serve(
            self.con,
            self.k,
            port=0,
            public_status_path=Path(self.temp_dir.name) / "http-public.json",
        )
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        base = f"http://127.0.0.1:{httpd.server_port}"

        with urllib.request.urlopen(
            base + "/api/v1/episodes?limit=20",
            timeout=3,
        ) as response:
            episodes = json.loads(response.read())
        self.assertTrue(episodes["provenance_complete"])
        self.assertIn(
            event["event_id"],
            [item["source_event_id"] for item in episodes["episodes"]],
        )

        request = urllib.request.Request(
            base + "/api/v1/ask",
            data=json.dumps({"text": "ping"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with patch(
            "ofn.organism.runtime.app.LocalCortex.available",
            return_value=False,
        ):
            with urllib.request.urlopen(request, timeout=3) as response:
                answer = json.loads(response.read())
        self.assertEqual(answer["route"], "deterministic_rule")
        self.assertEqual(answer["label"], "RULE_DEFINED")

        class FailedCortex:
            def complete(self, _text):
                return {
                    "status": "DEGRADED",
                    "answer": None,
                    "response_hash": "c" * 64,
                    "http_status": None,
                    "error": "simulated_model_failure",
                }

        Handler.asker = AskCascade(self.con, cortex=FailedCortex())
        failed_request = urllib.request.Request(
            base + "/api/v1/ask",
            data=json.dumps({"text": "unmatched failure probe"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with patch(
            "ofn.organism.runtime.app.LocalCortex.available",
            return_value=False,
        ):
            with urllib.request.urlopen(failed_request, timeout=3) as response:
                fallback = json.loads(response.read())
            with urllib.request.urlopen(
                base + "/api/v1/organism",
                timeout=3,
            ) as response:
                after_failure = json.loads(response.read())
        self.assertEqual(fallback["label"], "NEEDS_OWNER")
        self.assertEqual(fallback["route"], "needs_owner")
        self.assertEqual(after_failure["organism_id"], "board-life-001")
        self.assertGreaterEqual(self.k.metrics["last_seq"], 2)

    def test_server_does_not_accept_before_identity_marker(self):
        ensure_identity_genesis(self.con, "boot-order")
        httpd = create_server(
            self.con,
            self.k,
            port=0,
            bind_and_activate=False,
            public_status_path=(
                Path(self.temp_dir.name) / "ordered-public.json"
            ),
        )
        httpd.server_bind()
        port = httpd.socket.getsockname()[1]
        probe = socket.socket()
        try:
            probe.settimeout(0.2)
            self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)
        finally:
            probe.close()
        append_identity_event(
            self.con,
            "boot-order",
            "process_started",
            {"listen_state": "BOUND_NOT_ACCEPTING"},
        )
        httpd.server_activate()
        start_server(httpd)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v1/organism",
            timeout=3,
        ) as response:
            body = json.loads(response.read())
        self.assertTrue(body["identity_chain_valid"])

    def test_public_status_and_synthetic_degraded_signal(self):
        with self.con:
            self.con.execute(
                "INSERT INTO meta(k,v) VALUES(?,?)",
                ("lab_synthetic_health_state", "DEGRADED"),
            )
            self.con.execute(
                "INSERT INTO meta(k,v) VALUES(?,?)",
                ("lab_synthetic_health_reason", "unit-test"),
            )
        measured = effective_measurement(self.con)
        self.assertEqual(measured["health_state"], "DEGRADED")
        self.assertIn(
            "LAB_SYNTHETIC_DEGRADED:unit-test",
            measured["alerts"],
        )

        output = Path(self.temp_dir.name) / "ORGANISM-PUBLIC.json"
        body = {
            "organism_id": "board-life-001",
            "health_state": "DEGRADED",
            "autonomy_state": "PROPOSE_ONLY",
            "local_cortex": "AVAILABLE",
            "last_event_sequence": 10,
            "identity_chain_valid": True,
            "identity_chain_last_hash": "f" * 64,
            "first_stage_label": "NOT_EARNED",
            "alerts": ["LAB_SYNTHETIC_DEGRADED:unit-test"],
            "unknowns": [],
        }
        public = write_public_status(self.con, body, path=output)
        self.assertEqual(public["health_state"], "DEGRADED")
        self.assertTrue(public["alert"])
        self.assertEqual(output.stat().st_mode & 0o777, 0o644)

if __name__ == "__main__":
    unittest.main()
