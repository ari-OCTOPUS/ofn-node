"""Reply-queue bridge — brain replies land in OWNER-QUEUE.

CI on #182 @4a5257fd10104483730c85a3007c5bafa40f12b5 failed because
`test_append_to_queue` restored QUEUE to the default home path and then
asserted `.exists()` on that restored path (Ubuntu job 100899044307,
Windows job 100899044206). Existence of the default path is not proof
the append wrote, and absence is not proof it did not. Assert the
injected tmp path while the patch is still applied.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from reply_queue_bridge import append_to_queue, extract_proposals  # noqa: E402
from tests.tmpdir import temp_dir

import reply_queue_bridge as _rqb  # noqa: E402


def _seed_inbox(tmp: Path, entries: list[dict]) -> Path:
    inbox = tmp / "inbox"
    inbox.mkdir()
    for i, e in enumerate(entries):
        (inbox / f"{i}.json").write_text(json.dumps(e), encoding="utf-8")
    return inbox


class TestReplyQueueBridge(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(temp_dir(self))
        self.queue = self.tmp / "OWNER-QUEUE.md"
        self.seen = self.tmp / "seen.json"
        self._orig_queue = _rqb.QUEUE
        self._orig_seen = _rqb.SEEN_FILE
        _rqb.QUEUE = self.queue
        _rqb.SEEN_FILE = self.seen

    def tearDown(self) -> None:
        _rqb.QUEUE = self._orig_queue
        _rqb.SEEN_FILE = self._orig_seen

    def test_proposal_extraction(self) -> None:
        inbox = _seed_inbox(self.tmp, [
            {"idempotency_key": "abc", "payload": {"response": {
                "claim_type": "proposal", "confidence": 0.3,
                "evidence": ["painting:BLOCKED"]}, "businesses": ["painting"]}},
            {"idempotency_key": "def", "payload": {"response": {
                "claim_type": "observation"}}},
        ])
        props = extract_proposals(inbox)
        self.assertEqual(len(props), 1)
        self.assertEqual(props[0]["idempotency_key"], "abc")
        self.assertTrue(self.seen.exists())
        self.assertFalse(self._orig_seen.exists())

    def test_dedup_second_pass(self) -> None:
        inbox = _seed_inbox(self.tmp, [
            {"idempotency_key": "abc", "payload": {"response": {
                "claim_type": "proposal", "confidence": 0.5, "evidence": []}}},
        ])
        p1 = extract_proposals(inbox)
        self.assertEqual(len(p1), 1)
        p2 = extract_proposals(inbox)
        self.assertEqual(len(p2), 0)

    def test_append_to_queue(self) -> None:
        n = append_to_queue([
            {"confidence": 0.3, "evidence": ["painting:BLOCKED_HONEST:sha"]},
        ])
        self.assertEqual(n, 1)
        self.assertTrue(self.queue.exists())
        text = self.queue.read_text(encoding="utf-8")
        self.assertIn("0.3", text)
        self.assertIn("painting:BLOCKED_HONEST:sha", text)
        self.assertFalse(self._orig_queue.exists())

    def test_append_does_not_claim_default_path_after_restore(self) -> None:
        """The #182 CI failure: assert-after-restore on the home QUEUE path."""
        n = append_to_queue([
            {"confidence": 0.3, "evidence": ["painting:BLOCKED_HONEST:sha"]},
        ])
        self.assertEqual(n, 1)
        self.assertTrue(self.queue.exists())
        _rqb.QUEUE = self._orig_queue
        self.assertFalse(
            _rqb.QUEUE.exists(),
            "restored default QUEUE must stay unwritten; exists() after "
            "restore is not evidence the append succeeded",
        )
        self.assertTrue(self.queue.exists())

    def test_empty_proposals_do_not_create_queue(self) -> None:
        n = append_to_queue([])
        self.assertEqual(n, 0)
        self.assertFalse(self.queue.exists())
        self.assertFalse(self._orig_queue.exists())

    def test_malformed_proposal_is_skipped_not_written(self) -> None:
        n = append_to_queue([
            {"confidence": 0.9},
            "not-a-dict",
            {"confidence": "bad", "evidence": ["x"]},
            {"confidence": 0.4, "evidence": ["ok-item"]},
        ])
        self.assertEqual(n, 1)
        text = self.queue.read_text(encoding="utf-8")
        self.assertIn("ok-item", text)
        self.assertNotIn("0.9", text)

    def test_bridge_does_not_grant_send(self) -> None:
        self.assertFalse(getattr(_rqb, "grants_send", False))
        self.assertFalse(getattr(_rqb, "ready_is_authorized", False))
        self.assertNotEqual("send_authorized", "campaign_envelope_ready")
        src = Path(_rqb.__file__).read_text(encoding="utf-8")
        for name in ("smtplib", "http.client", "urllib.request", "socket"):
            self.assertNotIn(f"import {name}", src)
            self.assertNotIn(f"from {name}", src)
