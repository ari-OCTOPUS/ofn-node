"""The deployment probe, exercised against a stub provider.

The probe is the one script in this repository that spends real money, and it
runs on a board where a failure is expensive to diagnose. So it is tested here
against a local HTTP server that impersonates the provider — including the
ways the provider fails.

The test that matters most is `test_canary_never_reaches_the_wire`: the probe
plants an email address in its prompt precisely so a leak is loud, and this
asserts that the address does not arrive at the endpoint. If scrubbing ever
moves to the wrong side of the router, this goes red before anyone's data
does.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, "deploy", "brain-probe.py")

RECEIVED: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    mode = "ok"

    def log_message(self, *args):        # noqa: ARG002 — silence in test output
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            RECEIVED.append(json.loads(body))
        except json.JSONDecodeError:
            RECEIVED.append({"unparseable": body.decode("utf-8", "replace")})

        if Handler.mode == "unauthorised":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error":"bad key"}')
            return

        payload = {
            "choices": [{"message": {"content":
                                     "Ask when they need the work finished."}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 30},
        }
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class ProbeCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        RECEIVED.clear()
        Handler.mode = "ok"

    def probe(self, *args, key="test-key-not-a-real-one", **env):
        e = dict(os.environ)
        e.update({
            "OFN_REMOTE_API_KEY": key,
            "OFN_REMOTE_BASE_URL": f"http://127.0.0.1:{self.port}/v1",
            "OFN_STATE_DIR": os.path.join(ROOT, ".probe-state"),
        })
        e.update(env)
        return subprocess.run([sys.executable, PROBE, *args],
                              capture_output=True, text=True, timeout=120, env=e)


class TestUnarmed(ProbeCase):
    def test_refuses_without_a_key_and_spends_nothing(self):
        r = self.probe(key="")
        self.assertEqual(r.returncode, 1)
        self.assertIn("OFN_REMOTE_API_KEY is empty", r.stdout)
        self.assertEqual(RECEIVED, [])

    def test_never_prints_the_key(self):
        secret = "sk-do-not-print-me-0123456789"
        out = (lambda r: r.stdout + r.stderr)(self.probe(key=secret))
        self.assertNotIn(secret, out)
        # Nor any fragment of it. A partial key in a log is still a key in a
        # log, and "we only printed the first eight characters" has never once
        # been a defence. Eight is the window because shorter runs start
        # colliding with ordinary English and with the endpoint URL.
        for i in range(len(secret) - 8):
            with self.subTest(fragment=i):
                self.assertNotIn(secret[i:i + 8], out)


class TestHappyPath(ProbeCase):
    def test_a_successful_probe_reports_and_exits_clean(self):
        r = self.probe()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("measured latency", r.stdout)
        self.assertIn("interactive still safe : yes", r.stdout)

    def test_canary_never_reaches_the_wire(self):
        """The whole reason the prompt contains a planted address."""
        self.probe()
        self.assertTrue(RECEIVED, "the stub provider was never called")
        sent = json.dumps(RECEIVED)
        self.assertNotIn("canary.probe@example.invalid", sent)
        self.assertNotIn("example.invalid", sent)
        self.assertIn("[EMAIL]", sent)

    def test_the_fast_rung_is_used_not_the_deep_one(self):
        self.probe()
        models = [m.get("model") for m in RECEIVED]
        self.assertEqual(models, ["fugu"])

    def test_billed_tokens_include_the_invisible_multiplier(self):
        r = self.probe()
        # 150 visible x 2.6 = 390
        self.assertIn("390", r.stdout)

    def test_one_call_only(self):
        """A probe that quietly retries is a probe that quietly costs more."""
        self.probe()
        self.assertEqual(len(RECEIVED), 1)


class TestProviderFailure(ProbeCase):
    def test_a_rejected_key_fails_loudly_and_nonzero(self):
        Handler.mode = "unauthorised"
        r = self.probe()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("did not succeed", r.stdout)
        # And it says what to check, rather than just failing.
        self.assertIn("wrong key", r.stdout)


class TestDeepRung(ProbeCase):
    def test_deep_is_skipped_unless_asked(self):
        r = self.probe()
        self.assertIn("skipped", r.stdout)
        self.assertEqual([m.get("model") for m in RECEIVED], ["fugu"])

    def test_deep_flag_uses_the_deep_model(self):
        r = self.probe("--deep")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([m.get("model") for m in RECEIVED],
                         ["fugu", "fugu-ultra"])

    def test_deep_call_carries_the_reasoning_effort(self):
        self.probe("--deep")
        deep = RECEIVED[-1]
        self.assertEqual(deep.get("reasoning_effort"), "high")

    def test_the_deep_result_is_reported_as_the_deep_rung(self):
        """A regression guard with a story: the first version of this script
        read the ledger newest-first and sliced it oldest-first, so it printed
        the fast rung's numbers under the deep rung's heading. The wire was
        right and the report was wrong, which is the worse of the two."""
        r = self.probe("--deep")
        deep_section = r.stdout.split("── 4 ")[1].split("── 5")[0]
        self.assertIn("rung=remote_deep", deep_section)
        self.assertIn("remote:absent", deep_section)

    def test_the_deep_call_is_billed_at_the_deep_multiplier(self):
        r = self.probe("--deep")
        deep_section = r.stdout.split("── 4 ")[1].split("── 5")[0]
        # Same 150 visible tokens, but the estimate that gated it was 4x.
        self.assertIn("390", deep_section)


if __name__ == "__main__":
    unittest.main()
