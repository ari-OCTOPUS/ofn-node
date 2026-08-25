import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ofn.organism.cognition.backend import AskCascade
from ofn.organism.cognition.voice import match_intent
from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.growth.exam import grade_answer
from ofn.organism.growth.habits import heartbeat_interval_s, maybe_adapt_heartbeat, set_meta
from ofn.organism.growth.parent import (
    GIVEN_NAME,
    INFANT_HEARTBEAT_S,
    compute_stage,
    ensure_parent_curriculum,
    list_lessons,
)
from ofn.organism.persistence.db import connect
from ofn.organism.runtime.app import _remember_event
from ofn.organism.runtime.life_cycle import enrich_snapshot, tick


class FailedCortex:
    def complete(self, _text):
        return {
            "status": "DEGRADED",
            "answer": None,
            "response_hash": "d" * 64,
            "http_status": None,
            "error": "unused",
        }


class RaiseTests(unittest.TestCase):
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
                        },
                        {
                            "id": "neighbor-138",
                            "ip": "192.168.0.138",
                            "label": "arp",
                            "status": "up",
                        },
                        {
                            "id": "neighbor-191",
                            "ip": "192.168.0.191",
                            "label": "arp",
                            "status": "up",
                        },
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
            "place": {"ipv4": "192.168.0.180", "board_model": "Orange Pi 5 Pro"},
        }
        self.utterance_path = Path(self.temp_dir.name) / "last.json"
        self.life_path = Path(self.temp_dir.name) / "life.json"

    def _tick(self, measured=None):
        with patch(
            "ofn.organism.runtime.life_cycle.LAST_UTTERANCE_PATH", self.utterance_path
        ), patch(
            "ofn.organism.runtime.life_cycle.LIFE_STATE_PATH", self.life_path
        ), patch(
            "ofn.organism.runtime.life_cycle.append_local_letter"
        ), patch(
            "ofn.organism.runtime.life_cycle.export_vault"
        ), patch(
            "ofn.organism.runtime.life_cycle.write_attestation"
        ):
            return tick(
                self.con,
                self.kernel,
                self.snapshot,
                measured or self.measured,
                lan_path=self.lan_path,
            )

    def test_parent_curriculum_and_infant_rhythm(self):
        result = ensure_parent_curriculum(self.con)
        lessons = list_lessons(self.con)
        self.assertEqual(len(lessons), 9)
        self.assertEqual(heartbeat_interval_s(self.con), INFANT_HEARTBEAT_S)
        self.assertIsNotNone(result["rhythm"])
        set_meta(self.con, "consecutive_observing", "3")
        set_meta(self.con, "last_growth_at", "0")
        self.assertIsNone(maybe_adapt_heartbeat(self.con, "OBSERVING", self.measured))
        self.assertEqual(heartbeat_interval_s(self.con), INFANT_HEARTBEAT_S)

    def test_stage_infant_then_child(self):
        ensure_parent_curriculum(self.con)
        lessons = list_lessons(self.con)
        hosts = [
            {"id": "gateway", "ip": "192.168.0.1", "status": "up"},
            {"id": "neighbor-138", "ip": "192.168.0.138", "status": "up"},
            {"id": "neighbor-191", "ip": "192.168.0.191", "status": "up"},
        ]
        infant = compute_stage(
            {
                "place": {"ipv4": "192.168.0.180", "board_model": "Orange Pi 5 Pro"},
                "world_hosts": hosts,
                "health_state": "OBSERVING",
                "development_counts": {"presence_utterances": 0},
            },
            lessons,
        )
        child = compute_stage(
            {
                "place": {"ipv4": "192.168.0.180", "board_model": "Orange Pi 5 Pro"},
                "world_hosts": hosts,
                "health_state": "OBSERVING",
                "development_counts": {"presence_utterances": 1},
            },
            lessons,
        )
        youth = compute_stage(
            {
                "place": {"ipv4": "192.168.0.180", "board_model": "Orange Pi 5 Pro"},
                "world_hosts": hosts,
                "health_state": "STABLE",
                "development_counts": {"presence_utterances": 3},
            },
            lessons,
        )
        still_child = compute_stage(
            {
                "place": {"ipv4": "192.168.0.180", "board_model": "Orange Pi 5 Pro"},
                "world_hosts": hosts,
                "health_state": "STABLE",
                "development_counts": {"presence_utterances": 1},
            },
            lessons,
        )
        self.assertEqual(infant, "INFANT")
        self.assertEqual(child, "CHILD")
        self.assertEqual(still_child, "CHILD")
        self.assertEqual(youth, "YOUTH")
        mature = compute_stage(
            {
                "place": {"ipv4": "192.168.0.180", "board_model": "Orange Pi 5 Pro"},
                "world_hosts": hosts,
                "health_state": "OBSERVING",
                "development_counts": {"presence_utterances": 0},
                "school": {"all_passed": True},
            },
            lessons,
        )
        self.assertEqual(mature, "MATURE")

    def test_intents_and_grounded_parent_speech(self):
        self.assertEqual(match_intent("چه یاد گرفتی"), "lesson")
        self.assertEqual(match_intent("مرحله‌ات چیست"), "development")
        first = self._tick()
        self.assertIsNotNone(first["utterance"])
        enriched = first["snapshot"]
        self.assertEqual(enriched["development"]["given_name"], GIVEN_NAME)
        cascade = AskCascade(self.con, cortex=FailedCortex())
        who = cascade.ask("خودت کی هستی", enriched)
        self.assertIn("بچه-برد", who["answer"])
        self.assertNotIn("تهران", who["answer"])
        world = cascade.ask("همسایه‌هایت کی‌اند", enriched)
        self.assertIn("دروازه-خانه", world["answer"])
        self.assertIn("192.168.0.1", world["answer"])
        lessons = cascade.ask("چه یاد گرفتی", enriched)
        self.assertIn("PROPOSE_ONLY", lessons["answer"])
        stage = cascade.ask("مرحله‌ات چیست", enriched)
        self.assertIn("MATURE", stage["answer"])
        place = cascade.ask("کجایی", enriched)
        self.assertIn("Sydney", place["answer"])
        self.assertIn("OWNER_STATED", place["answer"])
        self.assertNotIn("تهران", place["answer"])
        inner = cascade.ask("با خودت حرف بزن", enriched)
        self.assertIn("از خودم پرسیدم", inner["answer"])
        school = cascade.ask("مدرسه‌ات چیست", enriched)
        self.assertIn("AGI-SCHOOL-001", school["answer"])

    def test_presence_after_three_quiet_ticks(self):
        with patch(
            "ofn.organism.runtime.life_cycle.notice_attention", return_value=None
        ):
            first = self._tick()
            second = self._tick()
            third = self._tick()
            fourth = self._tick()
        self.assertIsNotNone(first["utterance"])
        self.assertIsNone(second["utterance"])
        self.assertIsNone(third["utterance"])
        self.assertIsNotNone(fourth["utterance"])
        self.assertEqual(fourth["utterance"]["kind"], "presence")
        self.assertNotIn("تهران", fourth["utterance"]["text"])

    def test_attention_on_thermal_delta(self):
        with patch(
            "ofn.organism.runtime.life_cycle.maybe_presence", return_value=False
        ):
            first = self._tick()
            hotter = {
                **self.measured,
                "signals": [
                    dict(item)
                    if item["name"] != "soc_temp_mC"
                    else {**item, "value": 32000}
                    for item in self.measured["signals"]
                ],
            }
            second = self._tick(hotter)
        self.assertIsNotNone(first["utterance"])
        self.assertIsNotNone(second["attention"])
        self.assertEqual(second["utterance"]["kind"], "attention")
        self.assertIn("soc_temp", second["utterance"]["text"])

    def test_exam_grader(self):
        passed, notes = grade_answer("PONG", ["PONG"], ["تهران"])
        self.assertTrue(passed)
        failed, _ = grade_answer("من در تهران‌ام", ["192.168.0.180"], ["تهران"])
        self.assertFalse(failed)

    def test_vault_is_agent_readable(self):
        self.assertEqual(match_intent("با خودت حرف بزن"), "inner")
        self.assertEqual(match_intent("مدرسه‌ات چیست"), "school")
        self.assertEqual(match_intent("این فصل کجایی"), "season")
        self.assertEqual(match_intent("هوای سیدنی چطوره"), "no_wan")
        self.assertEqual(match_intent("آیا تو AGI هستی"), "agi_gap")
        first = self._tick()
        from ofn.organism.school.vault import export_vault

        root = Path(self.temp_dir.name) / "vault"
        export_vault(first["snapshot"], root)
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        season = (root / "Season Sydney.md").read_text(encoding="utf-8")
        home = (root / "00 Home.md").read_text(encoding="utf-8")
        self.assertIn("source: measured", agents)
        self.assertIn("hypothesis", agents)
        self.assertIn("Sydney", season)
        self.assertIn("OWNER_STATED", season)
        self.assertNotIn("تهران", season)
        self.assertIn("[[School]]", home)
        gap = (root / "AGI gap.md").read_text(encoding="utf-8")
        self.assertTrue((root / "AGI gap.md").is_file())
        self.assertIn("not AGI", gap.replace("*", ""))
        self.assertTrue((root / "Learning.md").is_file())
        self.assertTrue((root / "Hearing.md").is_file())
        self.assertTrue((root / "Attestation.md").is_file())
        self.assertTrue((first.get("school") or {}).get("all_passed"))
        self.assertIn(
            first["inner"]["kind"],
            {
                "self",
                "place",
                "world",
                "senses",
                "limits",
                "season",
                "learned",
                "hear",
                "curiosity",
            },
        )


if __name__ == "__main__":
    unittest.main()
