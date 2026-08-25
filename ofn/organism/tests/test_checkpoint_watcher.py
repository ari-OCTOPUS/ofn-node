import json
import tempfile
import unittest
from pathlib import Path

from ofn.organism.runtime.checkpoint import (
    CheckpointError,
    load_checkpoint_text,
    parse_checkpoint_payload,
    safe_load_checkpoint,
)


LEGACY_LIVE_SKIN = {
    "old_pid": 12748,
    "git_head": "013ec54",
    "latest_event": {"count": 388, "max_node_seq": 388},
    "latest_episode_count": 388,
    "latest_outbox_count": 388,
    "identity_head": {"sequence": 215, "entry_hash": "abc"},
    "database_schema": {
        "events": {"count": 388, "max_node_seq": 388},
        "episode_count": 388,
        "outbox_count": 388,
        "identity_head": {"sequence": 215, "entry_hash": "abc"},
    },
}

V1 = {
    "checkpoint_schema_version": 1,
    "old_pid": 34330,
    "source_hash": "deadbeef",
    "events": {"count": 406, "max_node_seq": 406},
    "episode_count": 406,
    "outbox_count": 406,
    "identity_head": {"sequence": 225, "entry_hash": "def"},
    "soak_samples": 300,
}


class CheckpointWatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.quarantine = self.root / "quarantine"

    def test_legacy_live_skin_checkpoint(self):
        parsed = parse_checkpoint_payload(LEGACY_LIVE_SKIN)
        self.assertEqual(parsed.schema_version, 0)
        self.assertEqual(parsed.payload["events"]["max_node_seq"], 388)
        self.assertEqual(parsed.payload["old_pid"], 12748)

    def test_v1_checkpoint(self):
        parsed = parse_checkpoint_payload(V1)
        self.assertEqual(parsed.schema_version, 1)
        self.assertEqual(parsed.optional.get("soak_samples"), 300)

    def test_missing_optional_key(self):
        payload = dict(V1)
        payload.pop("soak_samples")
        parsed = parse_checkpoint_payload(payload)
        self.assertNotIn("soak_samples", parsed.optional)

    def test_missing_mandatory_key(self):
        payload = dict(V1)
        payload.pop("identity_head")
        with self.assertRaises(CheckpointError) as ctx:
            parse_checkpoint_payload(payload)
        self.assertIn("missing_mandatory", str(ctx.exception))
        self.assertNotIn("invent", str(ctx.exception).lower())

    def test_malformed_json(self):
        with self.assertRaises(CheckpointError) as ctx:
            load_checkpoint_text("{not json}")
        self.assertEqual(str(ctx.exception), "malformed_json")

    def test_truncated_file(self):
        with self.assertRaises(CheckpointError) as ctx:
            load_checkpoint_text('{"old_pid": 1, "events":')
        self.assertEqual(str(ctx.exception), "truncated_or_empty")

    def test_unknown_schema_version(self):
        payload = dict(V1)
        payload["checkpoint_schema_version"] = 99
        with self.assertRaises(CheckpointError) as ctx:
            parse_checkpoint_payload(payload)
        self.assertEqual(str(ctx.exception), "unknown_schema_version")

    def test_recovery_after_one_invalid_checkpoint(self):
        bad = self.root / "checkpoint.json"
        bad.write_text("{", encoding="utf-8")
        parsed, error = safe_load_checkpoint(bad, self.quarantine)
        self.assertIsNone(parsed)
        self.assertEqual(error.kind, "truncated_or_empty")
        self.assertTrue(any(self.quarantine.iterdir()))
        bad.write_text(json.dumps(V1), encoding="utf-8")
        parsed, error = safe_load_checkpoint(bad, self.quarantine)
        self.assertIsNone(error)
        self.assertEqual(parsed.payload["old_pid"], 34330)

    def test_does_not_invent_mandatory_values(self):
        with self.assertRaises(CheckpointError):
            parse_checkpoint_payload({"old_pid": 1, "source_hash": "x"})

    def test_real_live_skin_receipt_if_present(self):
        path = Path(
            "/opt/octopus/lab/artifacts/completion-phase3/receipts/05_deployment_checkpoint.json"
        )
        if not path.is_file():
            self.skipTest("live receipt absent")
        parsed = parse_checkpoint_payload(json.loads(path.read_text(encoding="utf-8")))
        self.assertGreater(parsed.payload["old_pid"], 0)
        self.assertIn("max_node_seq", parsed.payload["events"])


if __name__ == "__main__":
    unittest.main()
