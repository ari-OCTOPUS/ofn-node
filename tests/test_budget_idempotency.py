"""GAP-032 — one verdict (job) must not become N executions and N debits.

The H1 seam: a caller retrying a submit after a timeout must not buy the
same thinking twice. The queue's idem_key dedupe plus one THINK_DONE per
landed answer is the guard. This pins the whole chain at the worker level:

  * a second submit of the same (tenant, idem_key) is refused
  * after a drain, the hosted brain ran exactly once and exactly one
    THINK_DONE row exists — a crash between submit and done cannot
    double-charge
  * a retry-backed-off job is not executed (and not debited) before its
    backoff elapses, even across a drain
"""

from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.ledger import Ledger
from ofn.adapters.router import BrainReply, ModelRouter, RulesBrain
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.routing import Rung
from ofn.kernel.tenancy import TenantRegistry
from ofn.worker import Job, WorkQueue, Worker

NOW_S = 1_785_000_000
NOW_ISO = "2026-09-09T00:00:00Z"


class Case(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.registry = TenantRegistry({
            "ziman": PackSpec(tenant=TenantId("ziman"),
                              capacity_units_per_week=6, quota_share=1.0)})
        self.ledger = Ledger(os.path.join(self._d.name, "l.sqlite"))
        self.quota = NodeQuota(estimated_capacity_tokens=10_000_000,
                               utilisation=1.0, shares={"ziman": 1.0})
        self.q = WorkQueue()
        self.remote_calls = []

    def tearDown(self):
        self.ledger.close()
        self._d.cleanup()

    @property
    def scope(self):
        return self.registry.scope("ziman")

    def worker(self) -> Worker:
        def answer(task, prompt):
            self.remote_calls.append(task)
            return BrainReply("answer", visible_tokens=100)
        brains = {Rung.RULES: RulesBrain({}), Rung.REMOTE: type("B", (), {
            "answer": staticmethod(answer)})()}
        return Worker(self.q, ModelRouter(brains, self.quota),
                      self.registry, self.ledger,
                      now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO)

    def job(self, key: str) -> Job:
        return Job(tenant="ziman", task="analyse", prompt="p", idem_key=key)

    def think_done_rows(self):
        return [e for e in self.ledger.read(self.scope)
                if e.kind == "THINK_DONE"]


class TestBudgetIdempotency(Case):
    def test_duplicate_submit_is_refused_and_charged_once(self):
        w = self.worker()
        self.assertTrue(w.submit(self.scope, self.job("v1")))
        # the caller retries the same verdict after a timeout
        self.assertFalse(w.submit(self.scope, self.job("v1")))
        self.assertEqual(w.drain(), 1)
        self.assertEqual(len(self.remote_calls), 1)
        self.assertEqual(len(self.think_done_rows()), 1)

    def test_distinct_verdicts_stay_distinct_charges(self):
        w = self.worker()
        for k in ("v1", "v2"):
            self.assertTrue(w.submit(self.scope, self.job(k)))
        self.assertEqual(w.drain(), 2)
        self.assertEqual(len(self.remote_calls), 2)
        self.assertEqual(len(self.think_done_rows()), 2)

    def test_backed_off_retry_is_not_debited_twice_in_one_drain(self):
        w = self.worker()
        j = self.job("retry")
        j.attempts = 1
        j.not_before = NOW_S + 600            # still cooling down
        self.assertTrue(self.q.submit(j))
        self.assertEqual(w.drain(), 0)
        self.assertEqual(self.remote_calls, [])
        self.assertEqual(self.think_done_rows(), [])


if __name__ == "__main__":                     # pragma: no cover
    unittest.main()
