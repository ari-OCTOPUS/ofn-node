import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/opt/octopus/lab")
from ofn.organism.cognition.backend import AskCascade
from ofn.organism.cognition.voice import match_intent
from ofn.organism.contracts.events import make_event
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.growth.habits import heartbeat_interval_s, maybe_adapt_heartbeat, set_meta
from ofn.organism.persistence.db import connect
from ofn.organism.runtime.app import _remember_event
from ofn.organism.runtime.life_cycle import enrich_snapshot, tick


class LifeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.con = connect(Path(self.temp_dir.name) / "o.db")
        self.addCleanup(self.con.close)
        self.kernel = EventKernel(self.con)
        self.kernel.register("*", lambda ev: _remember_event(self.con, ev))
        self.lan_path = Path(self.temp_dir.name) / "lan.json"
        self.lan_path.write_text(
            json.dumps(
                {
                    "hosts": [
                        {
                            "id": "gateway",
                            "ip": "192.168.0.1",
                            "label": "default-router",
                            "status": "up",
                            "last_probe": {"reachable": True, "icmp_ok": True},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.measured = {
            "health_state": "OBSERVING",
            "alerts": [],
            "signals": [
                {
                    "name": "MemAvailable_kB",
                    "state": "MEASURED",
                    "value": 2800000,
                    "unit": "kB",
                },
                {
                    "name": "soc_temp_mC",
                    "state": "MEASURED",
                    "value": 29000,
                    "unit": "mC",
                },
                {
                    "name": "disk_free_bytes",
                    "state": "MEASURED",
                    "value": 8 * 1024 * 1024 * 1024,
                    "unit": "B",
                },
                {"name": "load1", "state": "MEASURED", "value": 1.2, "unit": "n"},
            ],
        }
        self.snapshot = {
            "organism_id": "board-life-001",
            "boot_id": "boot-test",
            "health_state": "OBSERVING",
            "autonomy_state": "PROPOSE_ONLY",
            "local_cortex": "AVAILABLE",
            "identity_chain_valid": True,
            "identity_chain_last_hash": "a" * 64,
            "external_api": "DISABLED",
        }

    def test_intent_and_grounded_speech(self):
        self.assertEqual(match_intent("ping"), "ping")
        self.assertEqual(match_intent("خودت کی هستی"), "self")
        enriched = enrich_snapshot(
            self.con,
            self.snapshot,
            self.measured,
            lan_path=self.lan_path,
        )
        cascade = AskCascade(self.con, cortex=FailedCortex())
        who = cascade.ask("خودت کی هستی", enriched)
        self.assertEqual(who["route"], "deterministic_rule")
        self.assertIn("board-life-001", who["answer"])
        self.assertIn("192.168.0.1", who["answer"])
        world = cascade.ask("دنیایت چیست", enriched)
        self.assertEqual(world["route"], "deterministic_rule")
        self.assertIn("192.168.0.1", world["answer"])
        ping = cascade.ask("ping", enriched)
        self.assertEqual(ping["answer"], "PONG")

    def test_tick_discovers_self_and_world_and_speaks_once(self):
        utterance_path = Path(self.temp_dir.name) / "last.json"
        life_path = Path(self.temp_dir.name) / "life.json"
        letters = Path(self.temp_dir.name) / "letters.jsonl"
        with patch("ofn.organism.runtime.life_cycle.LAST_UTTERANCE_PATH", utterance_path), patch(
            "ofn.organism.runtime.life_cycle.LIFE_STATE_PATH", life_path
        ), patch("ofn.organism.runtime.telegram_letter.LETTERS_PATH", letters), patch(
            "ofn.organism.runtime.life_cycle.append_local_letter"
        ) as letter, patch(
            "ofn.organism.runtime.life_cycle.notice_attention", return_value=None
        ), patch(
            "ofn.organism.runtime.life_cycle.export_vault"
        ), patch(
            "ofn.organism.runtime.life_cycle.write_attestation"
        ):
            first = tick(
                self.con,
                self.kernel,
                self.snapshot,
                self.measured,
                lan_path=self.lan_path,
            )
            second = tick(
                self.con,
                self.kernel,
                self.snapshot,
                self.measured,
                lan_path=self.lan_path,
            )
        self.assertIsNotNone(first["utterance"])
        self.assertIn("first_self_model", first["self_changes"])
        self.assertTrue(any("gateway" in item for item in first["world_changes"]))
        self.assertIsNone(second["utterance"])
        self.assertEqual(second["self_changes"], [])
        self.assertEqual(second["world_changes"], [])
        self.assertEqual(letter.call_count, 1)
        self.assertTrue(utterance_path.is_file())

    def test_growth_adapts_interval_from_body(self):
        set_meta(self.con, "heartbeat_interval_s", "180")
        set_meta(self.con, "consecutive_observing", "3")
        set_meta(self.con, "last_growth_at", "0")
        applied = maybe_adapt_heartbeat(self.con, "OBSERVING", self.measured)
        self.assertIsNotNone(applied)
        self.assertEqual(applied["to"], 210)
        self.assertEqual(heartbeat_interval_s(self.con), 210)
        again = maybe_adapt_heartbeat(self.con, "OBSERVING", self.measured)
        self.assertIsNone(again)

    def test_memory_payload_is_not_just_priority(self):
        event = make_event("utterance", {"summary": "hello", "text": "hello"})
        self.kernel.accept(event)
        self.kernel.replay_pending()
        row = self.con.execute(
            "SELECT body_json FROM episodes WHERE event_type='utterance'"
        ).fetchone()
        body = json.loads(row[0])
        self.assertEqual(body["text"], "hello")


class FailedCortex:
    def complete(self, _text):
        return {
            "status": "DEGRADED",
            "answer": None,
            "response_hash": "d" * 64,
            "http_status": None,
            "error": "unused",
        }


if __name__ == "__main__":
    unittest.main()
