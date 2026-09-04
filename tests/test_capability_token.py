"""E3 park tests for 110B capability_token (authorization primitive).

verified_send never imports transport. grants_send is structurally
False. campaign_envelope_ready ≠ send_authorized. Transport file
and D-26 kernel/adapters copies stay absent.
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "ofn" / "agents"

# Test-only HMAC material. Name-only. Never a live secret.
_TEST_SECRET = "unit-test-capability-token-not-a-live-secret"


def _load_module():
    env = os.environ.get("OFN_SESSION_SECRET")
    os.environ["OFN_SESSION_SECRET"] = _TEST_SECRET
    try:
        import importlib
        import sys

        sys.path.insert(0, str(AGENTS))
        sys.path.insert(0, str(AGENTS.parent / "budget"))
        if "capability_token" in sys.modules:
            return importlib.reload(sys.modules["capability_token"])
        return importlib.import_module("capability_token")
    finally:
        if env is None:
            os.environ.pop("OFN_SESSION_SECRET", None)
        else:
            os.environ["OFN_SESSION_SECRET"] = env


class SourcePark(unittest.TestCase):
    def test_transport_file_absent(self):
        self.assertFalse((AGENTS / "lead_outbound_transport.py").exists())

    def test_source_has_no_transport_import(self):
        source = (AGENTS / "capability_token.py").read_text(encoding="utf-8")
        self.assertNotIn("lead_outbound_transport", source)
        self.assertNotIn("smtplib", source)
        self.assertNotIn("import smtp", source)

    def test_d26_kernel_adapters_copies_absent(self):
        self.assertFalse((ROOT / "ofn" / "kernel" / "capability_token.py").exists())
        self.assertFalse((ROOT / "ofn" / "adapters" / "capability_token.py").exists())

    def test_grants_send_structurally_false(self):
        mod = _load_module()
        self.assertFalse(mod.grants_send())
        self.assertIs(mod.grants_send(), False)

    def test_ready_is_not_authorized(self):
        mod = _load_module()
        self.assertFalse(mod.ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class VerifiedSendPark(unittest.TestCase):
    def setUp(self):
        self._prev = os.environ.get("OFN_SESSION_SECRET")
        os.environ["OFN_SESSION_SECRET"] = _TEST_SECRET
        self.mod = _load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.mod.opslib.STATE_DIR = self.state

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("OFN_SESSION_SECRET", None)
        else:
            os.environ["OFN_SESSION_SECRET"] = self._prev

    def _issue(self, subject: str = "agency@example.nsw.gov.au"):
        return self.mod.issue("send_email", subject, "unit-park")

    def test_good_token_still_parked(self):
        token = self._issue()
        out = self.mod.verified_send(
            token, {"email": "agency@example.nsw.gov.au"}, {"body": "x"},
            "unit-park",
        )
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_PARKED")
        self.assertEqual(out.get("detail"), "send-path-parked")
        self.assertIs(out.get("grants_send"), False)

    def test_bad_mac_denied_not_sent(self):
        token = self._issue()
        token = dict(token)
        token["mac"] = "0" * 64
        out = self.mod.verified_send(
            token, {"email": "agency@example.nsw.gov.au"}, {}, "unit-park")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_DENIED")
        self.assertEqual(out.get("detail"), "bad-mac")

    def test_subject_mismatch_denied(self):
        token = self._issue("one@example.nsw.gov.au")
        out = self.mod.verified_send(
            token, {"email": "two@example.nsw.gov.au"}, {}, "unit-park")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_DENIED")
        self.assertEqual(out.get("detail"), "subject-mismatch")

    def test_expired_denied(self):
        token = self.mod.issue(
            "send_email", "agency@example.nsw.gov.au", "unit-park", ttl_s=-1)
        # ttl_s=-1 sets exp = now-1; freeze a later clock for the check
        with mock.patch.object(self.mod.time, "time", return_value=time.time() + 5):
            out = self.mod.verified_send(
                token, {"email": "agency@example.nsw.gov.au"}, {}, "unit-park")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_DENIED")
        self.assertEqual(out.get("detail"), "expired")

    def test_action_mismatch_denied(self):
        import hashlib
        import hmac
        import json

        token = self.mod.issue(
            "send_email", "agency@example.nsw.gov.au", "unit-park")
        body = {k: token[k] for k in
                ("action", "subject", "purpose", "iat", "exp", "nonce")}
        body["action"] = "other_action"
        mac = hmac.new(
            _TEST_SECRET.encode(),
            json.dumps(body, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()
        other = {**body, "mac": mac}
        out = self.mod.verified_send(
            other, {"email": "agency@example.nsw.gov.au"}, {}, "unit-park")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_DENIED")
        self.assertEqual(out.get("detail"), "action-mismatch")

    def test_missing_secret_fail_closed(self):
        os.environ.pop("OFN_SESSION_SECRET", None)
        empty_home = Path(self.tmp.name) / "no-home"
        empty_home.mkdir()
        with mock.patch.object(self.mod.Path, "home", return_value=empty_home):
            with self.assertRaises(RuntimeError) as ctx:
                self.mod.issue("send_email", "a@b.c", "x")
        self.assertIn("no-token-secret", str(ctx.exception))

    def test_wire_closed_still_parked(self):
        os.environ["OFN_WIRE_OUTBOUND"] = "0"
        self.addCleanup(lambda: os.environ.pop("OFN_WIRE_OUTBOUND", None))
        token = self._issue()
        out = self.mod.verified_send(
            token, {"email": "agency@example.nsw.gov.au"}, {}, "unit-park")
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_PARKED")

    def test_verified_send_does_not_call_transport(self):
        token = self._issue()
        with mock.patch.dict("sys.modules", {"lead_outbound_transport": mock.Mock()}):
            fake = mock.Mock()
            fake.send = mock.Mock(return_value={"sent": True, "status": "SENT"})
            with mock.patch.dict("sys.modules", {"lead_outbound_transport": fake}):
                out = self.mod.verified_send(
                    token, {"email": "agency@example.nsw.gov.au"}, {},
                    "unit-park")
        fake.send.assert_not_called()
        self.assertFalse(out.get("sent"))
        self.assertEqual(out.get("status"), "TOKEN_PARKED")


class IssueVerify(unittest.TestCase):
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

    def test_issue_verify_roundtrip(self):
        token = self.mod.issue(
            "send_email", "Agency@Example.nsw.gov.au", "unit")
        ok, reason = self.mod.verify(
            token, "send_email", "agency@example.nsw.gov.au")
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")

    def test_request_send_token_halted(self):
        with mock.patch.object(self.mod.opslib, "master_halted", return_value="HALT"):
            token, reason = self.mod.request_send_token(
                {"email": "agency@example.nsw.gov.au"}, "unit")
        self.assertIsNone(token)
        self.assertTrue(reason.startswith("halted:"))


if __name__ == "__main__":
    unittest.main()
