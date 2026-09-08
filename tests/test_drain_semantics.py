"""GAP-008 — retry/skip semantics of the drain loop, pinned as behaviour.

`Worker.drain` is the aggregator the daemon thread actually runs. The
per-job park/requeue policy has tests; the loop-level contract did not:

  * it stops when the queue is empty and reports how many jobs ran
  * `limit` is a safety rail, not a tuning knob — it binds even when more
    ready work remains, so a self-requeuing job cannot hold the loop forever
  * a `stop` set between jobs is honoured immediately
  * a job backed off into the future is skipped, not executed early
"""

from __future__ import annotations

import os
import tempfile
import threading
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
            return BrainReply("thought", visible_tokens=100)
        brains = {Rung.RULES: RulesBrain({}), Rung.REMOTE: type("B", (), {
            "answer": staticmethod(answer)})()}
        return Worker(self.q, ModelRouter(brains, self.quota),
                      self.registry, self.ledger,
                      now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO)

    def job(self, key: str) -> Job:
        return Job(tenant="ziman", task="analyse", prompt="p",
                   idem_key=key)


class TestDrain(Case):
    def test_empty_queue_returns_zero_without_touching_the_brain(self):
        self.assertEqual(self.worker().drain(), 0)
        self.assertEqual(self.remote_calls, [])

    def test_drains_until_empty_and_reports_the_count(self):
        w = self.worker()
        for i in range(3):
            self.assertTrue(self.q.submit(self.job(f"j{i}")))
        self.assertEqual(w.drain(), 3)
        self.assertEqual(len(self.remote_calls), 3)
        self.assertEqual(w.drain(), 0)          # empty again — no re-runs

    def test_limit_binds_even_when_ready_work_remains(self):
        w = self.worker()
        for i in range(5):
            self.assertTrue(self.q.submit(self.job(f"j{i}")))
        self.assertEqual(w.drain(limit=2), 2)
        self.assertEqual(len(self.q), 3)        # the rest stayed queued

    def test_stop_event_is_honoured_between_jobs(self):
        w = self.worker()
        for i in range(4):
            self.assertTrue(self.q.submit(self.job(f"j{i}")))
        stop = threading.Event()
        orig = w.step

        def step_then_stop():
            ran = orig()
            stop.set()
            return ran

        w.step = step_then_stop
        self.assertEqual(w.drain(stop=stop), 1)
        self.assertEqual(len(self.q), 3)

    def test_backed_off_job_is_skipped_not_run_early(self):
        w = self.worker()
        j = self.job("retry-me")
        j.attempts = 1
        j.not_before = NOW_S + 3600            # backed off an hour
        self.assertTrue(self.q.submit(j))
        self.assertEqual(w.drain(), 0)
        self.assertEqual(self.remote_calls, [])
        self.assertEqual(len(self.q), 1)       # still waiting, place kept


if __name__ == "__main__":                     # pragma: no cover
    unittest.main()
