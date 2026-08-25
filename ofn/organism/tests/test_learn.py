import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ofn.organism.cognition.backend import AskCascade
from ofn.organism.cognition.curiosity import propose_curiosity
from ofn.organism.cognition.learn import learn_topic, list_topics
from ofn.organism.cognition.policy import extract_learn_topic, topic_allowed
from ofn.organism.cognition.voice import match_intent
from ofn.organism.identity.attestation import write_attestation
from ofn.organism.persistence.db import connect
from ofn.organism.tools.discover import discover_senses


class FailedCortex:
    def complete(self, _text):
        return {
            "status": "DEGRADED",
            "answer": None,
            "response_hash": "e" * 64,
            "http_status": None,
            "error": "simulated",
        }


class LearnTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.con = connect(Path(self.temp_dir.name) / "o.db")
        self.addCleanup(self.con.close)
        os.environ.pop("OCTOPUS_LEARN_EXTERNAL", None)

    def test_policy_denies_live_or_dangerous_topics(self):
        self.assertFalse(topic_allowed("هوای سیدنی")[0])
        self.assertFalse(topic_allowed("قیمت دلار")[0])
        self.assertFalse(topic_allowed("geoip lookup")[0])
        self.assertFalse(topic_allowed("bitcoin")[0])
        self.assertFalse(topic_allowed("api_key please")[0])
        self.assertTrue(topic_allowed("کدک صوتی ES8323 چیست")[0])

    def test_extract_learn_topic(self):
        self.assertEqual(extract_learn_topic("یاد بگیر ES8323"), "ES8323")
        self.assertEqual(extract_learn_topic("learn: OUI"), "OUI")
        self.assertEqual(match_intent("یاد بگیر ES8323"), "learn")
        self.assertEqual(match_intent("چه یاد گرفتی"), "lesson")
        self.assertEqual(match_intent("موضوعات یادگرفته"), "topics")

    def test_learn_topic_mocked_teacher(self):
        fake = {
            "status": "OK",
            "answer": "کدک صوتی روی برد. دانش مدل است نه حسگر.",
            "response_hash": "f" * 64,
            "track": "flash",
            "model": "deepseek-chat",
            "latency_ms": 1,
        }
        with patch(
            "ofn.organism.cognition.learn.complete_flash",
            return_value=fake,
        ):
            result = learn_topic(self.con, "کدک صوتی ES8323 چیست", track="flash")
        self.assertEqual(result["status"], "LEARNED")
        self.assertEqual(result["claim_level"], "LEARNED_FROM_MODEL")
        self.assertEqual(list_topics(self.con)[0]["topic"], "کدک صوتی ES8323 چیست")
        recalled = learn_topic(self.con, "کدک صوتی ES8323 چیست", track="flash")
        self.assertEqual(recalled["status"], "RECALL")

    def test_ask_denied_weather_does_not_call_teacher(self):
        cascade = AskCascade(self.con, cortex=FailedCortex())
        with patch("ofn.organism.cognition.learn.complete_deep") as deep:
            denied = cascade.ask("یاد بگیر هوای سیدنی", {})
        deep.assert_not_called()
        self.assertEqual(denied["route"], "deterministic_rule")
        self.assertIn("یاد نمی‌گیرم", denied["answer"])

    def test_ask_learn_without_env_is_needs_owner(self):
        cascade = AskCascade(self.con, cortex=FailedCortex())
        with patch("ofn.organism.cognition.learn.complete_deep") as deep:
            result = cascade.ask("یاد بگیر OUI مشترک یعنی چه", {})
        deep.assert_not_called()
        self.assertEqual(result["label"], "NEEDS_OWNER")
        self.assertEqual(result["data"]["reason"], "LEARN_EXTERNAL_DISABLED")

    def test_unmatched_failure_stays_needs_owner_offline(self):
        cascade = AskCascade(self.con, cortex=FailedCortex())
        with patch("ofn.organism.cognition.learn.complete_flash") as flash:
            result = cascade.ask("unmatched failure probe", {})
        flash.assert_not_called()
        self.assertEqual(result["route"], "needs_owner")
        self.assertEqual(result["label"], "NEEDS_OWNER")

    def test_ask_learn_with_env_uses_mocked_teacher(self):
        fake = {
            "status": "OK",
            "answer": "OUI سه بایت اول MAC است. دانش مدل است.",
            "response_hash": "aa" * 32,
            "track": "deep",
            "model": "deepseek-chat",
            "latency_ms": 2,
        }
        cascade = AskCascade(self.con, cortex=FailedCortex())
        with patch.dict(os.environ, {"OCTOPUS_LEARN_EXTERNAL": "1"}), patch(
            "ofn.organism.cognition.learn.complete_deep",
            return_value=fake,
        ):
            result = cascade.ask("یاد بگیر OUI مشترک یعنی چه", {})
        self.assertEqual(result["route"], "teacher_deepseek")
        self.assertEqual(result["label"], "LEARNED_FROM_MODEL")
        self.assertIn("LEARNED_FROM_MODEL", result["answer"])
        self.assertIn("OUI", result["answer"])

    def test_curiosity_skips_already_learned(self):
        snapshot = {
            "discovery": {
                "senses": {
                    "microphone": "ES8323_CAPTURE",
                    "camera": "NOT_FOUND",
                    "gps": "NOT_FOUND",
                }
            },
            "place": {"wlan0_operstate": "down"},
            "world_hosts": [
                {"ip": "192.168.0.138", "given_name": "همسایه-هم‌خانواده"}
            ],
        }
        first = propose_curiosity(snapshot, self.con)
        self.assertIsNotNone(first)
        with patch(
            "ofn.organism.cognition.learn.complete_flash",
            return_value={
                "status": "OK",
                "answer": "مدل.",
                "response_hash": "bb" * 32,
                "track": "flash",
                "model": "deepseek-chat",
            },
        ):
            learn_topic(self.con, first, track="flash")
        second = propose_curiosity(snapshot, self.con)
        self.assertNotEqual(second, first)

    def test_attestation_writes_hash_without_secrets(self):
        path = Path(self.temp_dir.name) / "ATTESTATION.json"
        body = write_attestation(
            {
                "organism_id": "board-life-001",
                "development": {"given_name": "بچه-برد", "stage": "MATURE"},
                "health_state": "OBSERVING",
                "identity_chain_valid": True,
                "identity_chain_last_hash": "ab" * 32,
                "place": {"ipv4": "192.168.0.180"},
                "season": {"city": "Sydney", "source": "OWNER_STATED"},
                "school": {"all_passed": True},
                "external_api": "DISABLED",
            },
            path=path,
        )
        self.assertTrue(path.is_file())
        self.assertEqual(len(body["attestation_hash"]), 64)
        raw = path.read_text(encoding="utf-8")
        self.assertNotIn("sk-", raw)
        self.assertNotIn("API_KEY", raw)
        self.assertIn("board-life-001", raw)


class MicrophoneDiscoverTests(unittest.TestCase):
    def test_es8323_capture_from_pcm(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        pcm = root / "proc/asound"
        pcm.mkdir(parents=True)
        (pcm / "pcm").write_text(
            "02-00: ES8323 HiFi : ES8323 HiFi : capture 1\n",
            encoding="utf-8",
        )
        senses = discover_senses(root)
        self.assertEqual(senses["microphone"], "ES8323_CAPTURE")
        self.assertEqual(senses["camera"], "NOT_FOUND")
        self.assertEqual(senses["gps"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
