"""End to end over real HTTP: a partner opens the app, is asked a question,
answers it, and the answer lands in the ledger as a verifiable fact.

Everything here is the production wiring — real SQLite files, the real gate
chain, the real HTTP handler. The only substitutions are the clock and the
bot token, because tests that depend on wall-clock time are tests that fail
at midnight for reasons nobody can reproduce.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap, serve
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_dir
from ofn.kernel.auth import data_check_string
from ofn.kernel.domain import Confidence
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

PACKS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packs")

NOW_S = 1_785_000_000
# Every partner shell now has a door list. These are the accounts the
# tests speak as; anybody else is a stranger, which is the point.
PARTNERS = {"ziman": ["777"], "lead": ["777"], "studio": ["777"]}
NOW_ISO = "2026-08-03T10:00:00Z"
TOKEN = "111:test-bot-token"
HOST = "ziman.test"
PORT = 8879


def signed_init_data(uid: str = "777") -> str:
    fields = {"auth_date": str(NOW_S),
              "user": f'{{"id":{uid},"username":"partner"}}'}
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, data_check_string(fields).encode(),
                              hashlib.sha256).hexdigest()
    return "&".join(f"{k}={v}" for k, v in fields.items())


class TestPartnerJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._dir = tempfile.TemporaryDirectory()
        d = cls._dir.name
        packs = load_dir(PACKS_DIR)
        registry = TenantRegistry(packs)
        cls.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=180_000_000,
                            utilisation=0.40,
                            shares={k: p.quota_share for k, p in packs.items()}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            base_closed_gates=("secret_rotation",))
        app = ApiApp(
            registry, HostMap(tenants={HOST: "ziman"}, owner_host="panel.test"),
            bot_tokens={"ziman": TOKEN, "__owner__": TOKEN},
            session_secret="e2e-secret", owner_user_ids=["5001"],
            partner_user_ids=PARTNERS,
            now=lambda: NOW_S,
            questions_for=cls.node.questions_for,
            submit_answer=cls.node.submit_answer,
            status_for=cls.node.status_for,
            owner_queue=cls.node.owner_queue,
            owner_decide=cls.node.owner_decide)
        cls.server = serve(app, PORT)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.node.close()
        cls._dir.cleanup()

    # ── helpers ───────────────────────────────────────────────────────────
    def call(self, path, method="GET", body=None, session=None, host=HOST):
        headers = {"Host": host, "Content-Type": "application/json"}
        if session:
            headers["Authorization"] = f"Bearer {session}"
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}{path}", method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers)
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                out = json.loads(resp.read())
                code = resp.status
        except urllib.error.HTTPError as exc:
            out, code = json.loads(exc.read()), exc.code
        return code, out, (time.perf_counter() - started) * 1000

    _session: str | None = None

    def login(self) -> str:
        """Log in once, then reuse the token — exactly what a real client does.

        Calling this per test would be rejected, because the launch blob is
        deterministic here and the replay guard refuses a blob it has already
        accepted. `test_11` below exercises that deliberately.
        """
        cls = type(self)
        if cls._session is None:
            code, out, _ = self.call("/api/v1/auth/session", "POST",
                                     {"init_data": signed_init_data()})
            self.assertEqual(code, 200, out)
            cls._session = out["session"]
        return cls._session

    # ── the journey ───────────────────────────────────────────────────────
    def test_01_health_is_open(self):
        code, out, _ = self.call("/healthz")
        self.assertEqual(code, 200)
        self.assertTrue(out["ok"])

    def test_02_unauthenticated_request_is_refused(self):
        code, _, _ = self.call("/api/v1/questions")
        self.assertEqual(code, 401)

    def test_03_partner_logs_in_and_is_asked_something(self):
        session = self.login()
        code, out, _ = self.call("/api/v1/questions", session=session)
        self.assertEqual(code, 200)
        self.assertGreater(len(out["questions"]), 0)
        first = out["questions"][0]
        self.assertIn("key", first)
        self.assertIn("why", first)
        self.assertTrue(first["missing"])

    def test_04_answer_becomes_a_verifiable_fact(self):
        session = self.login()
        _, before, _ = self.call("/api/v1/questions", session=session)
        key = before["questions"][0]["key"]

        code, out, _ = self.call("/api/v1/answers", "POST",
                                 {"key": key, "value": 42}, session=session)
        self.assertEqual(code, 200, out)
        self.assertTrue(out["ok"])
        self.assertEqual(out["readiness"]["done"], 1)

        scope = self.node.registry.scope("ziman")
        subject, _, predicate = key.partition(".")
        fact = self.node.facts.current(scope, subject, predicate)
        self.assertEqual(fact.value, 42)
        self.assertIs(fact.confidence, Confidence.OWNER_CONFIRMED)

        ok, why = self.node.ledger.verify(scope)
        self.assertTrue(ok, why)
        self.assertIn("FACT", [e.kind for e in self.node.ledger.read(scope)])

    def test_05_answered_question_is_not_asked_again(self):
        session = self.login()
        _, out, _ = self.call("/api/v1/questions", session=session)
        keys = [q["key"] for q in out["questions"]]
        scope = self.node.registry.scope("ziman")
        answered = [k for k in self.node.registry.pack("ziman").required_facts
                    if self.node.facts.current(scope, *k.split(".", 1))]
        for k in answered:
            self.assertNotIn(k, keys)

    def test_06_arbitrary_facts_cannot_be_written(self):
        session = self.login()
        code, out, _ = self.call("/api/v1/answers", "POST",
                                 {"key": "secret.backdoor", "value": "x"},
                                 session=session)
        self.assertEqual(code, 200)
        self.assertFalse(out["ok"])
        scope = self.node.registry.scope("ziman")
        self.assertIsNone(self.node.facts.current(scope, "secret", "backdoor"))

    def test_07_status_reflects_progress(self):
        session = self.login()
        code, out, _ = self.call("/api/v1/status", session=session)
        self.assertEqual(code, 200)
        self.assertEqual(out["tenant"], "ziman")
        self.assertEqual(out["capacity_per_week"], 6)
        self.assertGreaterEqual(out["readiness"]["done"], 1)

    def test_08_every_partner_call_is_fast(self):
        """A partner-facing request must never wait on a model. The budget is
        200ms; local reads should land two orders of magnitude below it."""
        session = self.login()
        for path in ("/api/v1/me", "/api/v1/questions", "/api/v1/status"):
            with self.subTest(path=path):
                _, _, ms = self.call(path, session=session)
                self.assertLess(ms, 200, f"{path} took {ms:.0f}ms")

    def test_09_wrong_host_gets_nothing(self):
        session = self.login()
        code, _, _ = self.call("/api/v1/questions", session=session,
                               host="attacker.test")
        self.assertEqual(code, 404)

    def test_10_partner_cannot_read_the_owner_queue(self):
        session = self.login()
        code, _, _ = self.call("/api/v1/queue", session=session)
        self.assertEqual(code, 404)

    def test_11_replaying_the_launch_blob_over_real_http_is_refused(self):
        """The blob used in test_03 is captured and re-sent. A signature stays
        valid for its whole freshness window, so without the guard this is a
        free session for anyone who observed one request."""
        self.login()                                   # ensures it was used once
        code, out, _ = self.call("/api/v1/auth/session", "POST",
                                 {"init_data": signed_init_data()})
        self.assertEqual(code, 401)
        self.assertEqual(out["error"], "unauthorised")

    def test_12_a_forged_blob_is_refused(self):
        forged = signed_init_data().replace('"id":777', '"id":999')
        code, _, _ = self.call("/api/v1/auth/session", "POST",
                               {"init_data": forged})
        self.assertEqual(code, 401)


if __name__ == "__main__":
    unittest.main()
