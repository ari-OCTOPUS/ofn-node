"""P0 Owner → Brain round-trip: admission, scope, delivery, receipts.

Written from the Round-1 black-box incident on board138 (2026-08-31):

    POST /owner/ask answered 200 {"ok": true} in 7ms, billed the question to
    the first business tenant ("hypno"), never consulted the brain, retried a
    deterministic quota denial three times inside one second, parked, and
    told the owner none of it. The answer, had one existed, had nowhere to
    land: no owner-visible surface ever carried response text.

Every test here pins one property of the fixed loop. The names under each
class are the acceptance contract; the incident reproductions come first.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters.owner_asks import OwnerAskStore
from ofn.adapters.router import BrainReply, ModelRouter, RulesBrain
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, RiskTier, TenantId
from ofn.kernel.estimate import estimate_request
from ofn.kernel.quota import CONTROL_SCOPE, NodeQuota
from ofn.kernel.routing import Rung
from ofn.kernel.tenancy import TenantRegistry, TenantScope
from ofn.node import Node
from ofn.worker import Job, WorkQueue, Worker

MULTIPLIER = 2.6


def scope_of(name: str) -> TenantScope:
    return TenantScope(TenantId(name))

NOW = 1_800_000_000
NOW_ISO = "2027-01-15T08:00:00Z"
SECRET = "p0-roundtrip-secret"
OWNER_ID = "5001"
OWNER_HOST = "panel.test"
SIX_CLAUSE_PROMPT = (
    "یک سیستم نرم‌افزاری سه ماه توسعه یافته، چند repository، چند node، "
    "تعداد زیادی تست و چند کسب‌وکار نیمه‌کاره دارد؛ اما مالک نتیجهٔ قابل‌مشاهده "
    "نمی‌بیند. بدون فرض‌کردن اینکه معماری فعلی درست است:\n"
    "۱) مدل حقیقت وضعیت را بساز؛\n"
    "۲) بین مشکل فنی، مشکل هماهنگی و مشکل انتخاب بازار تفکیک کن؛\n"
    "۳) سه فرضیهٔ رقیب با روش ابطال بده؛\n"
    "۴) یک اقدام داخلی کم‌ریسک انتخاب کن که ظرف چهار ساعت artifact قابل‌بررسی "
    "تولید کند؛\n"
    "۵) هر ادعای بدون شاهد را صریحاً UNKNOWN علامت بزن؛\n"
    "۶) هیچ اقدام خارجی انجام نده."
)


def _packs() -> dict[str, PackSpec]:
    return {
        name: PackSpec(tenant=TenantId(name), capacity_units_per_week=8,
                       quota_share=share)
        for name, share in (("hypno", 0.10), ("lead", 0.35),
                            ("studio", 0.20), ("ziman", 0.35))
    }


class Scripted:
    """A brain that answers from a script, like the hosted one never does."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def answer(self, task, prompt):
        self.calls.append((task, prompt))
        if not self.replies:
            return BrainReply("", True)
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class Case(unittest.TestCase):
    """One node, one owner session, control quota enabled."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.registry = TenantRegistry(_packs())
        self.ledger = Ledger(os.path.join(self.tmp.name, "ledger.sqlite"))
        self.facts = FactStore(os.path.join(self.tmp.name, "facts.sqlite"))
        self.outbox = Outbox(os.path.join(self.tmp.name, "outbox.sqlite"))
        self.addCleanup(self.ledger.close)
        self.addCleanup(self.facts.close)
        self.addCleanup(self.outbox.close)
        self.quota = NodeQuota(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=5_000)
        self.store = OwnerAskStore(
            os.path.join(self.tmp.name, "owner", "asks.jsonl"))
        self.node = Node(
            registry=self.registry, quota=self.quota, ledger=self.ledger,
            facts=self.facts, outbox=self.outbox,
            now_epoch_s=lambda: NOW, now_iso=lambda: NOW_ISO,
            owner_asks=self.store)
        # A default wiring so submit-path tests can ask immediately;
        # tests needing specific brains re-attach their own worker.
        self.attach_worker({})
        self.worker = None

    # ── wiring helpers ────────────────────────────────────────────────────
    def attach_worker(self, brains, *, result_sink=None, on_failure=None,
                      backoff_base_s=30):
        router = ModelRouter({Rung.RULES: RulesBrain({}), **brains},
                             self.quota, on_event=lambda *a, **k: None)
        if result_sink is None:
            result_sink = lambda *a: self.node.record_owner_answer(*a)
        if on_failure is None:
            on_failure = lambda *a, **k: self.node.mark_owner_job_failed(
                *a, **k)
        self.worker = Worker(
            WorkQueue(), router, self.registry, self.ledger,
            now_epoch_s=lambda: NOW, now_iso=lambda: NOW_ISO,
            result_sink=result_sink, on_failure=on_failure,
            on_start=self.node.mark_owner_job_running,
            backoff_base_s=backoff_base_s)
        self.node.worker = self.worker
        return self.worker

    def drain(self, limit=10):
        return self.worker.drain(limit=limit)

    def ask(self, **overrides):
        data = {"prompt": SIX_CLAUSE_PROMPT, "principal_id": OWNER_ID}
        data.update(overrides)
        return self.node.ask_owner_question(data)

    def status(self, job_id, principal_id=OWNER_ID):
        return self.node.owner_ask_status(job_id, principal_id)

    def control_events(self):
        return self.ledger.read(scope_of(CONTROL_SCOPE), limit=100)

    def outbox_total(self):
        return sum(self.outbox.counts(self.registry.scope(t)).get("pending", 0)
                   + self.outbox.counts(self.registry.scope(t)).get("held", 0)
                   + self.outbox.counts(self.registry.scope(t)).get("sent", 0)
                   for t in self.registry)


class TestIncidentReproduction(Case):
    """Round-1 findings, each pinned as a property the fix must keep."""

    def test_owner_ask_does_not_use_first_tenant(self):
        """A: registry order puts hypno first; the ask must never land there."""
        self.assertEqual(sorted(t.value for t in self.registry)[0], "hypno")
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.assertNotEqual(out["target_scope"], "hypno")
        # The queued/receipt chain belongs to the control scope, not a leg.
        events = self.ledger.read(scope_of(CONTROL_SCOPE), limit=10)
        self.assertTrue(any(e.kind == "THINK_QUEUED" for e in events))
        hypno = self.ledger.read(scope_of("hypno"), limit=10)
        self.assertFalse(any(str(e.kind).startswith("THINK_") for e in hypno))

    def test_owner_ask_defaults_to_owner_control_scope(self):
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.assertEqual(out["target_scope"], CONTROL_SCOPE)

    def test_explicit_target_scope_must_be_allowlisted(self):
        ok = self.ask(target_scope="lead")
        self.assertTrue(ok.get("ok"), ok)
        self.assertEqual(ok["target_scope"], "lead")
        bad = self.ask(target_scope="does-not-exist")
        self.assertFalse(bad.get("ok"))
        self.assertEqual(bad.get("code"), "UNKNOWN_TARGET_SCOPE")
        self.assertFalse(bad.get("job_created", True))

    def test_owner_ask_rejects_empty_prompt(self):
        for prompt in ("", "   "):
            with self.subTest(prompt=repr(prompt)):
                out = self.ask(prompt=prompt)
                self.assertFalse(out.get("ok"))
                self.assertFalse(out.get("job_created", True))

    def test_request_larger_than_ceiling_returns_422(self):
        """B: spent=0, ceiling small, estimate honest — the quote must show
        why, and the HTTP answer must say no before any job exists."""
        self.node.quota = NodeQuota(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=700)
        out = self.ask()
        self.assertFalse(out.get("ok"))
        self.assertEqual(out.get("code"), "REQUEST_EXCEEDS_SCOPE")
        self.assertFalse(out.get("retryable", True))
        self.assertFalse(out.get("job_created", True))
        quote = out["quote"]
        self.assertGreater(quote["request_estimate"], quote["ceiling"])
        self.assertEqual(quote["spent"], 0)
        self.assertEqual(quote["remaining"], 700)

    def test_rejected_admission_creates_no_runnable_job(self):
        self.node.quota = NodeQuota(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=700)
        self.attach_worker({})
        out = self.ask()
        self.assertFalse(out.get("ok"))
        self.assertEqual(len(self.worker._q), 0)
        self.assertEqual(len(self.worker.parked), 0)

    def test_rejected_job_never_returns_ok_true(self):
        self.node.quota = NodeQuota(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=700)
        out = self.ask()
        self.assertIsNot(out.get("ok"), True)

    def test_non_transient_quota_denial_is_not_retried(self):
        """D: a mid-flight deterministic denial parks once; no retry storm."""
        self.attach_worker({})

        class ExplodingQuota(NodeQuota):
            def check(self, tenant, est, now):
                from ofn.kernel.domain import Decision, RiskTier
                return Decision(False, RiskTier.RED, "tenant share exhausted: "
                                "999 > 5 tokens this week",
                                rule="quota:tenant-share")

        self.worker._router._quota = ExplodingQuota(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=5_000)
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.drain()
        kinds = [e.kind for e in self.control_events()]
        self.assertNotIn("THINK_RETRY", kinds)
        self.assertIn("THINK_PARKED", kinds)
        parked = [e for e in self.control_events()
                  if e.kind == "THINK_PARKED"][0]
        self.assertEqual(parked.payload.get("retryable"), False)
        job = self.status(out["job_id"])["job"]
        self.assertEqual(job["status"], "PARKED")
        self.assertFalse(job["retryable"])

    def test_transient_retry_has_bounded_backoff(self):
        """One failure requeues with a future not_before; the frozen clock
        proves the loop cannot hammer the provider three times a second."""
        self.attach_worker(
            {Rung.REMOTE: Scripted(RuntimeError("provider exploded"))},
            backoff_base_s=30)
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.drain()
        job = self.status(out["job_id"])["job"]
        self.assertEqual(job["status"], "RETRY_WAIT")
        self.assertGreater(job.get("not_before", 0), NOW)
        retries = [e for e in self.control_events() if e.kind == "THINK_RETRY"]
        self.assertEqual(len(retries), 1)
class TestAdmissionAndQuote(Case):

    def test_owner_ask_quotes_before_queue(self):
        seen = {}

        class Recording(NodeQuota):
            def quote(self, *a, **k):
                seen["quote"] = super().quote(*a, **k)
                return seen["quote"]

        self.node.quota = Recording(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=5_000)
        self.attach_worker({})
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.assertIn("quote", seen)
        self.assertEqual(seen["quote"]["request_estimate"],
                         out["quote"]["request_estimate"])

    def test_status_and_admission_use_same_quote(self):
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        snap = self.node.quota.snapshot(NOW)
        quote = out["quote"]
        self.assertEqual(quote["ceiling"],
                         snap["control"]["ceiling"])
        self.assertEqual(quote["spent"], snap["control"]["spent"])

    def test_quote_exposes_estimate_and_remaining(self):
        q = self.node.quota.quote(
            CONTROL_SCOPE,
            estimated_input=302, reserved_output=800, now_epoch_s=NOW)
        for key in ("scope", "spent", "ceiling", "remaining",
                    "estimated_input", "reserved_output", "multiplier",
                    "request_estimate", "fits", "code"):
            self.assertIn(key, q)
        self.assertEqual(q["code"], "ADMITTED")
        self.assertTrue(q["fits"])

    def test_persian_prompt_estimate_is_explainable(self):
        est = estimate_request(SIX_CLAUSE_PROMPT)
        self.assertEqual(est["chars"], len(SIX_CLAUSE_PROMPT))
        # Explainable arithmetic: input is chars/chars_per_token, rounded up,
        # never zero; the request estimate is input plus reserved output.
        import math
        expected_input = max(
            1, math.ceil(len(SIX_CLAUSE_PROMPT) / 2.0))
        self.assertEqual(est["estimated_input"], expected_input)
        self.assertEqual(est["reserved_output"], 800)
        self.assertEqual(est["request_estimate"],
                         expected_input + 800)
        # And the node's admission used that same estimator, not a constant.
        out = self.ask()
        self.assertEqual(out["quote"]["estimated_input"],
                         est["estimated_input"])

    def test_successful_submit_returns_202_and_job_id(self):
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.assertEqual(out.get("_http_status"), 202)
        self.assertTrue(out.get("job_id", "").startswith("job_"))
        self.assertTrue(out.get("request_id", "").startswith("req_"))
        self.assertEqual(out.get("status"), "QUEUED")

    def test_job_id_is_server_minted(self):
        a = self.ask()
        b = self.ask()
        self.assertNotEqual(a["job_id"], b["job_id"])

    def test_duplicate_request_id_is_idempotent(self):
        first = self.ask(request_id="req_owner_1")
        again = self.ask(request_id="req_owner_1")
        self.assertTrue(first.get("ok"))
        self.assertTrue(again.get("ok"))
        self.assertEqual(first["job_id"], again["job_id"])
        self.assertTrue(again.get("duplicate"))

    def test_call_budget_exhaustion_is_explicit(self):
        from ofn.kernel.callbudget import CallBudget
        self.node.call_budget = CallBudget()
        # Burn the remote allowance for the day.
        while self.node.call_budget.allows(Rung.REMOTE, NOW):
            self.node.call_budget.record(Rung.REMOTE, NOW)
        out = self.ask()
        self.assertFalse(out.get("ok"))
        self.assertEqual(out.get("code"), "CALL_BUDGET_EXHAUSTED")


class TestResponseDelivery(Case):

    def _wired_roundtrip(self, replies, backoff_base_s=30):
        self.attach_worker(
            {Rung.REMOTE: Scripted(*replies)},
            backoff_base_s=backoff_base_s)

    def test_fake_brain_answer_roundtrip_owner_visible(self):
        """E, post-fix: KNOWN_ANSWER goes in, the owner can read it out."""
        self._wired_roundtrip([
            BrainReply("KNOWN_ANSWER_آزمون", insufficient=False,
                       visible_tokens=120, model="fugu", requested="fugu")])
        out = self.ask()
        self.assertTrue(out.get("ok"), out)
        self.drain()
        got = self.status(out["job_id"])
        self.assertTrue(got.get("ok"), got)
        job = got["job"]
        self.assertEqual(job["status"], "COMPLETED")
        self.assertEqual(job["response_text_scrubbed"], "KNOWN_ANSWER_آزمون")
        self.assertEqual(job["billed_tokens"], round(120 * MULTIPLIER))

    def test_response_is_persisted_before_think_done(self):
        self._wired_roundtrip([
            BrainReply("ANSWER", visible_tokens=10)])
        out = self.ask()
        self.drain()
        done = [e for e in self.control_events() if e.kind == "THINK_DONE"]
        self.assertEqual(len(done), 1)
        payload = done[0].payload
        job = self.status(out["job_id"])["job"]
        self.assertTrue(payload.get("response_id"))
        self.assertEqual(payload.get("response_sha256"),
                         job["response_sha256"])
        # The record was completed BEFORE the ledger event could exist.
        self.assertIsNotNone(job["completed_at"])

    def test_response_hash_matches_delivered_text(self):
        self._wired_roundtrip([BrainReply("HASH-ME", visible_tokens=5)])
        out = self.ask()
        self.drain()
        job = self.status(out["job_id"])["job"]
        digest = hashlib.sha256(
            job["response_text_scrubbed"].encode("utf-8")).hexdigest()
        self.assertEqual(job["response_sha256"], digest)

    def test_response_survives_restart(self):
        self._wired_roundtrip([BrainReply("DURABLE", visible_tokens=5)])
        out = self.ask()
        self.drain()
        # A fresh process reopens the same store file.
        reopened = OwnerAskStore(
            os.path.join(self.tmp.name, "owner", "asks.jsonl"))
        record = reopened.get(out["job_id"])
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "COMPLETED")
        self.assertEqual(record["response_text_scrubbed"], "DURABLE")

    def test_cross_owner_job_access_denied(self):
        self._wired_roundtrip([BrainReply("SECRET-OWNER", visible_tokens=5)])
        out = self.ask()
        self.drain()
        denied = self.status(out["job_id"], principal_id="9999")
        self.assertFalse(denied.get("ok"))
        self.assertEqual(denied.get("code"), "FORBIDDEN_JOB")
        self.assertNotIn("job", denied)

    def test_cross_tenant_response_leak_denied(self):
        """The answer lives only in the owner's own store; no leg's ledger
        row ever carries the response text."""
        self._wired_roundtrip(
            [BrainReply("OWNER-ONLY-TEXT", visible_tokens=5)])
        out = self.ask()
        self.drain()
        for tenant in self.registry:
            for event in self.ledger.read(self.registry.scope(tenant)):
                blob = json.dumps(event.payload)
                self.assertNotIn("OWNER-ONLY-TEXT", blob)
            for event in self.ledger.read(scope_of(CONTROL_SCOPE)):
                # The control chain may reference ids and hashes, not text.
                self.assertNotIn("OWNER-ONLY-TEXT",
                                 json.dumps(event.payload))

    def test_secret_scrubbed_before_persist(self):
        self._wired_roundtrip([
            BrainReply("your key is sk-abcdefghijklmnopqrst and 0412 345 678",
                       visible_tokens=30)])
        out = self.ask()
        self.drain()
        job = self.status(out["job_id"])["job"]
        text = job["response_text_scrubbed"]
        self.assertNotIn("sk-abcdefghijklmnopqrst", text)
        self.assertNotIn("0412 345 678", text)
        self.assertIn("[SECRET]", text)
        self.assertIn("[PHONE]", text)
        # The hash covers the bytes that will actually be delivered.
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(job["response_sha256"], digest)

    def test_failed_response_persist_never_marks_completed(self):
        def broken_sink(scope, job, result, elapsed_ms):
            raise RuntimeError("disk gone")

        self.attach_worker({Rung.REMOTE: Scripted(BrainReply("LOST", 5))},
                           result_sink=broken_sink)
        out = self.ask()
        self.drain()
        job = self.status(out["job_id"])["job"]
        self.assertNotEqual(job["status"], "COMPLETED")
        self.assertIsNone(job.get("response_text_scrubbed"))
        kinds = [e.kind for e in self.control_events()]
        self.assertNotIn("THINK_DONE", kinds)

    def test_timeout_never_becomes_completed(self):
        self._wired_roundtrip([TimeoutError("provider timed out")] * 3,
                              backoff_base_s=0)
        out = self.ask()
        self.drain(limit=5)
        job = self.status(out["job_id"])["job"]
        self.assertNotEqual(job["status"], "COMPLETED")
        self.assertIn(job["status"], ("PARKED", "FAILED"))

    def test_model_failure_is_owner_visible(self):
        self._wired_roundtrip([BrainReply("", True)] * 3)
        out = self.ask()
        self.drain(limit=5)
        got = self.status(out["job_id"])
        job = got["job"]
        self.assertEqual(job["status"], "PARKED")
        self.assertTrue(job.get("error_detail_safe"))

    def test_no_external_effect_from_owner_ask(self):
        before = self.outbox_total()
        self._wired_roundtrip([BrainReply("NO SIDE EFFECTS", visible_tokens=5)])
        out = self.ask()
        self.drain()
        self.status(out["job_id"])
        self.assertEqual(self.outbox_total(), before)


class TestContractCompat(Case):

    def test_legacy_brain_status_remains_read_only(self):
        self.attach_worker({})
        events_before = len(self.control_events())
        a = self.node.brain_status()
        b = self.node.brain_status()
        self.assertEqual(a, b)
        self.assertEqual(events_before, len(self.control_events()),
                         "reading brain status wrote a ledger event")

    def test_partner_path_estimate_unchanged(self):
        """Partner jobs keep their existing fixed estimate semantics; only
        the owner ask estimates from its own prompt."""
        job = Job(tenant="lead", task="classify", prompt="hi",
                  idem_key="i1")
        self.assertEqual(job.estimated_tokens, 2000)


class TestOwnerHttpContract(Case):
    """The same node behind the real ApiApp routing, over HTTP semantics."""

    def setUp(self):
        super().setUp()
        self.attach_worker(
            {Rung.REMOTE: Scripted(
                BrainReply("HTTP-ROUNDTRIP", visible_tokens=10))},
            result_sink=lambda *a: self.node.record_owner_answer(*a),
            on_failure=lambda *a, **k: self.node.mark_owner_job_failed(
                *a, **k))
        self.app = ApiApp(
            self.registry,
            HostMap(tenants={"lead.test": "lead"}, owner_host=OWNER_HOST),
            bot_tokens={"__owner__": "owner-token"},
            session_secret=SECRET,
            owner_user_ids=(OWNER_ID,),
            partner_user_ids={"lead": ()},
            now=lambda: NOW,
            owner_ask=self.node.ask_owner_question,
            owner_ask_status=self.node.owner_ask_status,
        )
        self.session = issue_session("owner", OWNER_ID, SECRET,
                                     now_epoch_s=NOW)

    def _post(self, path, body):
        return self.app.handle(
            "POST", path,
            {"host": OWNER_HOST, "authorization": "Bearer " + self.session},
            json.dumps(body).encode())

    def _get(self, path):
        return self.app.handle(
            "GET", path,
            {"host": OWNER_HOST, "authorization": "Bearer " + self.session},
            b"")

    def test_http_submit_is_202_with_job_id(self):
        r = self._post("/api/v1/owner/ask",
                       {"prompt": SIX_CLAUSE_PROMPT})
        self.assertEqual(r.status, 202, r.body)
        self.assertTrue(r.body["job_id"].startswith("job_"))
        self.assertEqual(r.body["status"], "QUEUED")

    def test_http_rejection_is_422_not_ok(self):
        self.node.quota = NodeQuota(
            estimated_capacity_tokens=100_000, utilisation=0.4,
            shares={name: p.quota_share for name, p in _packs().items()},
            control_ceiling_tokens=700)
        r = self._post("/api/v1/owner/ask",
                       {"prompt": SIX_CLAUSE_PROMPT})
        self.assertEqual(r.status, 422)
        self.assertFalse(r.body["ok"])
        self.assertEqual(r.body["code"], "REQUEST_EXCEEDS_SCOPE")
        self.assertFalse(r.body["retryable"])

    def test_http_roundtrip_delivery(self):
        r = self._post("/api/v1/owner/ask",
                       {"prompt": SIX_CLAUSE_PROMPT})
        job_id = r.body["job_id"]
        self.drain()
        g = self._get(f"/api/v1/owner/asks/{job_id}")
        self.assertEqual(g.status, 200, g.body)
        self.assertEqual(g.body["job"]["status"], "COMPLETED")
        self.assertEqual(g.body["job"]["response_text_scrubbed"],
                         "HTTP-ROUNDTRIP")

    def test_http_unknown_job_is_404(self):
        g = self._get("/api/v1/owner/asks/job_nope")
        self.assertEqual(g.status, 404)

    def test_no_first_tenant_scope_argument_exists(self):
        """The route cannot be pointed at a leg by argument; the handler
        receives the payload, not a registry-derived scope."""
        r = self._post("/api/v1/owner/ask",
                       {"prompt": "سؤال کوتاه", "tenant": "lead",
                        "scope": "lead"})
        self.assertEqual(r.status, 202)
        self.assertEqual(r.body["target_scope"], CONTROL_SCOPE)


if __name__ == "__main__":
    unittest.main()
