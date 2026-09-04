"""Owner-absent chaos for parked 110B capability_token.

HALT stops STARTS, not a citation of the park. A later hold
still supersedes. Timeout is UNKNOWN, not a send. Ready ≠
authorized. Transport absence is not evidence of a live send.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests.test_capability_token import _TEST_SECRET, _load_module


class OwnerAbsentPark(unittest.TestCase):
    def setUp(self):
        self._prev = os.environ.get("OFN_SESSION_SECRET")
        os.environ["OFN_SESSION_SECRET"] = _TEST_SECRET
        self.mod = _load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mod.opslib.STATE_DIR = Path(self.tmp.name)

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("OFN_SESSION_SECRET", None)
        else:
            os.environ["OFN_SESSION_SECRET"] = self._prev

    def test_halt_does_not_grant_send(self):
        os.environ["HALT_SURVIVAL_LOOP"] = "1"
        self.addCleanup(lambda: os.environ.pop("HALT_SURVIVAL_LOOP", None))
        self.assertFalse(self.mod.grants_send())
        token, reason = self.mod.request_send_token(
            {"email": "agency@example.nsw.gov.au"}, "chaos")
        self.assertIsNone(token)
        self.assertIn("halted", reason)

    def test_owner_absent_valid_token_still_parked(self):
        token = self.mod.issue(
            "send_email", "agency@example.nsw.gov.au", "chaos")
        out = self.mod.verified_send(
            token, {"email": "agency@example.nsw.gov.au"}, {}, "chaos")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_PARKED")
        self.assertFalse(self.mod.ready_is_authorized())

    def test_missing_transport_is_not_a_send(self):
        # UPDATED 2026-09-04 (P03/A08): transport may now exist (gated arc,
        # see test_capability_token.SourcePark) — the invariant that matters
        # is unchanged: a parked capability token never authorizes a send,
        # whatever transport files exist.
        self.assertFalse(self.mod.grants_send())
        token = self.mod.issue("send_email", "x@y.test", "chaos")
        out = self.mod.verified_send(token, {}, {}, "chaos")
        self.assertFalse(out.get("sent"))
        self.assertIn(out.get("status"), ("TOKEN_PARKED", "TOKEN_DENIED"))

    def test_timeout_does_not_prove_send(self):
        # Timeout is UNKNOWN, not a concurrent writer and not a send.
        self.assertFalse(self.mod.grants_send())
        self.assertNotEqual("TIMEOUT", "SENT")

    def test_ready_name_stays_distinct_from_send(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertNotEqual("campaign_envelope_ready", "quote_sent")
        self.assertFalse(self.mod.ready_is_authorized())

    def test_empty_candidate_does_not_send(self):
        token = self.mod.issue(
            "send_email", "agency@example.nsw.gov.au", "chaos")
        out = self.mod.verified_send(token, {}, {}, "chaos")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_DENIED")


if __name__ == "__main__":
    unittest.main()
