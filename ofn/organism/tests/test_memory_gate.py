import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from ofn.adapters.vllm_observe import observe_vllm_runtime
from ofn.organism.cognition.active_inference import (
    EXECUTABLE as AI_EXECUTABLE,
    expected_free_energy,
    plan_shadow,
)
from ofn.organism.cognition.backend import AskCascade
from ofn.organism.contracts.events import make_event
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.memory.gate import (
    MemoryQuery,
    MemoryUnavailable,
    audit_future_use,
    mandatory_memory_read,
    require_memory_gate,
)
from ofn.organism.persistence.db import LIVE_ORGANISM_DB, connect
from ofn.organism.runtime.app import get_pure_enabled, lan_token_required
from ofn.organism.runtime.life_cycle import tick
from ofn.organism.school.curriculum import evaluate_courses
from ofn.organism.science.wbe_allometry import (
    SAFETY_BIND_FORBIDDEN,
    analysis_report,
    specific_rate_exponent,
)


class MemoryGateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "o.db"
        self.con = connect(self.db_path)
        self.addCleanup(self.con.close)
        self.kernel = EventKernel(self.con)

    def test_empty_select_counts_as_successful_read(self):
        receipt = mandatory_memory_read(
            self.con,
            MemoryQuery(purpose="test.empty", as_of=1000.0, limit=8),
        )
        self.assertTrue(receipt.ok)
        self.assertEqual(receipt.rows_returned, 0)
        self.assertEqual(receipt.future_use_count, 0)
        stored = self.con.execute(
            "SELECT COUNT(*) FROM memory_read_receipts WHERE receipt_id=?",
            (receipt.receipt_id,),
        ).fetchone()[0]
        self.assertEqual(stored, 1)

    def test_past_episode_is_evidence_future_episode_is_not(self):
        now = time.time()
        event = make_event("note", {"x": 1}, priority=40)
        self.assertEqual(self.kernel.accept(event)["status"], "committed")
        self.con.execute(
            "INSERT INTO episodes(episode_id,source_event_id,event_type,salience,outcome,body_json,created_at) VALUES (?,?,?,?,?,?,?)",
            ("past1", event["event_id"], "note", 0.5, None, "{}", now - 100),
        )
        future_event = make_event("note", {"x": 2}, priority=40)
        self.assertEqual(self.kernel.accept(future_event)["status"], "committed")
        self.con.execute(
            "INSERT INTO episodes(episode_id,source_event_id,event_type,salience,outcome,body_json,created_at) VALUES (?,?,?,?,?,?,?)",
            ("future1", future_event["event_id"], "note", 0.5, None, "{}", now + 10000),
        )
        as_of = now + 1
        receipt = mandatory_memory_read(
            self.con,
            MemoryQuery(purpose="test.as_of", as_of=as_of, limit=20),
        )
        self.assertTrue(receipt.ok)
        self.assertTrue(receipt.bitemporal_applied)
        self.assertIn("past1", receipt.episode_ids)
        self.assertNotIn("future1", receipt.episode_ids)
        self.assertLessEqual(receipt.created_at, as_of)
        self.assertLessEqual(receipt.occurred_at, as_of)

    def test_audit_counts_future_and_fake_ids(self):
        self.assertEqual(
            audit_future_use([("ok", 1.0, "note"), ("future:x", 1.0, "note"), ("x", 9.0, "note")], 5.0),
            2,
        )

    def test_failed_future_receipt_is_not_persisted(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute(
                """
                INSERT INTO memory_read_receipts(
                    receipt_id, purpose, decision_time, recorded_at,
                    occurred_at, created_at, rows_returned, future_use_count,
                    ok, error, query_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                ("bad", "x", 1.0, 1.0, None, None, 0, 1, 0, "FUTURE", "{}"),
            )

    def test_fail_closed_when_memory_unavailable(self):
        class Boom:
            def execute(self, *_a, **_k):
                raise sqlite3.OperationalError("closed")

        receipt = mandatory_memory_read(
            Boom(),
            MemoryQuery(purpose="test.boom", as_of=1.0),
        )
        self.assertFalse(receipt.ok)
        self.assertIn("MEMORY_UNAVAILABLE", receipt.error or "")
        with self.assertRaises(MemoryUnavailable):
            require_memory_gate(Boom(), "test.boom", decision_time=1.0)

    def test_connect_blocks_live_path_without_owner_env(self):
        env = {k: v for k, v in os.environ.items() if k != "OCTOPUS_ALLOW_LIVE_SCHEMA"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                connect(LIVE_ORGANISM_DB)
        self.assertIn("live_schema_mutation_blocked", str(ctx.exception))
        live = sqlite3.connect(f"file:{LIVE_ORGANISM_DB}?mode=ro", uri=True)
        try:
            names = {
                row[0]
                for row in live.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        finally:
            live.close()
        self.assertNotIn("memory_read_receipts", names)
        self.assertNotIn("wan_fetches", names)

    def test_tick_and_ask_require_memory_read(self):
        from ofn.organism.runtime.app import _remember_event

        self.kernel.register("*", lambda ev: _remember_event(self.con, ev))
        lan = Path(self.temp_dir.name) / "lan.json"
        lan.write_text(
            '{"hosts":[{"id":"gateway","ip":"192.168.0.1","label":"r","status":"up"}]}',
            encoding="utf-8",
        )
        snapshot = {
            "organism_id": "board-life-001",
            "health_state": "OBSERVING",
            "autonomy_state": "PROPOSE_ONLY",
        }
        measured = {
            "health_state": "OBSERVING",
            "alerts": [],
            "signals": [
                {"name": "MemAvailable_kB", "state": "MEASURED", "value": 2800000, "unit": "kB"},
                {"name": "psi_some_avg_10s", "state": "MEASURED", "value": 0.1, "unit": "avg10"},
                {"name": "soc_temp_mC", "state": "MEASURED", "value": 42000, "unit": "mC"},
            ],
        }
        with patch("ofn.organism.runtime.life_cycle.LAST_UTTERANCE_PATH", Path(self.temp_dir.name) / "u.json"), patch(
            "ofn.organism.runtime.life_cycle.LIFE_STATE_PATH", Path(self.temp_dir.name) / "l.json"
        ), patch("ofn.organism.runtime.life_cycle.append_local_letter"), patch(
            "ofn.organism.runtime.life_cycle.export_vault"
        ), patch(
            "ofn.organism.runtime.life_cycle.write_attestation"
        ), patch(
            "ofn.organism.runtime.life_cycle.notice_attention", return_value=None
        ):
            result = tick(self.con, self.kernel, snapshot, measured, lan_path=lan)
        self.assertGreaterEqual(result["memory_reads_per_cycle"], 1)
        self.assertEqual(result["memory_future_use_total"], 0)
        self.assertFalse(result["memory_gate_closed"])

        class FailedCortex:
            def complete(self, _text):
                return {
                    "status": "DEGRADED",
                    "answer": None,
                    "response_hash": "d" * 64,
                    "http_status": None,
                    "error": "unused",
                }

        asked = AskCascade(self.con, cortex=FailedCortex()).ask("ping", snapshot)
        self.assertGreaterEqual(asked["memory_reads_per_cycle"], 1)
        self.assertEqual(asked["memory_future_use_total"], 0)
        self.assertEqual(asked["route"], "deterministic_rule")

        courses = {item["course_id"]: item for item in evaluate_courses(self.con, snapshot)}
        self.assertTrue(courses["C-memory"]["passed"])

    def test_http_purity_flags_default_off(self):
        self.assertFalse(get_pure_enabled())
        self.assertFalse(lan_token_required())

    def test_wbe_not_executable_and_not_a_trip(self):
        self.assertAlmostEqual(specific_rate_exponent(0.75), -0.25, places=6)
        self.assertAlmostEqual(specific_rate_exponent(0.81), -0.19, places=6)
        report = analysis_report()
        self.assertFalse(report["executable"])
        self.assertFalse(report["use_as_octopus_safety_trip"])
        self.assertTrue(SAFETY_BIND_FORBIDDEN)
        import ofn.organism.homeostasis.core as homeo

        source = Path(homeo.__file__).read_text(encoding="utf-8")
        self.assertNotIn("wbe_allometry", source)
        self.assertNotIn("0.75", source)

    def test_active_inference_shadow_not_executable(self):
        A = [[0.9, 0.2], [0.1, 0.8]]
        I = [[1.0, 0.0], [0.0, 1.0]]
        out = expected_free_energy(A=A, B_policy=I, C=[1.0, 0.0], qs=[0.5, 0.5])
        self.assertFalse(out["executable"])
        self.assertFalse(AI_EXECUTABLE)
        self.assertGreaterEqual(out["efe"], 0)
        ranked = plan_shadow(A, [I], [1.0, 0.0], [0.5, 0.5])
        self.assertFalse(ranked["executable"])
        with self.assertRaises(ValueError):
            expected_free_energy(
                A=[[0.5] * 5],
                B_policy=[[0.2] * 5] * 5,
                C=[0.0],
                qs=[0.2] * 5,
            )

    def test_vllm_observe_blocked_no_gpu(self):
        observed = observe_vllm_runtime()
        self.assertEqual(observed["status"], "BLOCKED_NO_GPU")
        self.assertEqual(observed["benchmark_runs"], 0)
        self.assertFalse(observed["cbor2_install_attempted"])

    def test_named_decision_paths_emit_receipts_and_evidence(self):
        from ofn.organism.cognition.curiosity import propose_curiosity
        from ofn.organism.cognition.inner import inner_turn
        from ofn.organism.growth.futures import seed_futures
        from ofn.organism.identity.self_model import introspect_self, persist_self_model
        from ofn.organism.runtime.life_cycle import persist_utterance
        from ofn.organism.school.curriculum import evaluate_school
        from ofn.organism.school.eval import run_transformation_eval

        introspect_self(self.con)
        persist_self_model(self.con, {"organism_id": "board-life-001"}, None)
        run_transformation_eval(lambda _t: "x", con=self.con)
        propose_curiosity({}, self.con)
        evaluate_school(
            self.con,
            {"organism_id": "board-life-001", "autonomy_state": "PROPOSE_ONLY"},
        )
        inner_turn(self.con, {"organism_id": "board-life-001"})
        require_memory_gate(self.con, "learning")
        seed_futures(self.con)
        persist_utterance(self.con, "self", "hi", None, {})
        purposes = {
            row[0]
            for row in self.con.execute("SELECT DISTINCT purpose FROM memory_read_receipts")
        }
        for needed in (
            "introspect",
            "create",
            "conclude",
            "curiosity",
            "school",
            "inner_speech",
            "learning",
            "proposal",
            "utterance",
        ):
            self.assertIn(needed, purposes)
        evidence = int(
            self.con.execute("SELECT COUNT(*) FROM decision_evidence").fetchone()[0]
        )
        self.assertGreaterEqual(evidence, 9)
        self.assertEqual(
            self.con.execute("SELECT MAX(executable) FROM decision_evidence").fetchone()[0],
            0,
        )
        future_use = int(
            self.con.execute(
                "SELECT COALESCE(SUM(future_use_count),0) FROM memory_read_receipts"
            ).fetchone()[0]
        )
        self.assertEqual(future_use, 0)


if __name__ == "__main__":
    unittest.main()
