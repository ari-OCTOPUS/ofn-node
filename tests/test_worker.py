"""The background worker: the only place the slow brain runs.

Every test here is really about one question — if the owner is asleep and the
hosted brain misbehaves, does this loop cost money, lose work, or lie about
what happened?
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
from ofn.worker import MAX_ATTEMPTS, Job, WorkQueue, Worker

NOW_S = 1_785_000_000
NOW_ISO = "2026-08-04T10:00:00Z"


class Scripted:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def answer(self, task, prompt):
        self.calls.append((task, prompt))
        return self.replies.pop(0) if self.replies else BrainReply("", True)


class Boom:
    def answer(self, task, prompt):
        raise RuntimeError("provider exploded")


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

    def tearDown(self):
        self.ledger.close()
        self._d.cleanup()

    def worker(self, brains, on_result=None) -> Worker:
        router = ModelRouter(brains, self.quota)
        return Worker(self.q, router, self.registry, self.ledger,
                      now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
                      on_result=on_result)

    def job(self, **kw) -> Job:
        base = dict(tenant="ziman", task="analyse", prompt="why no leads?",
                    idem_key="j1")
        base.update(kw)
        return Job(**base)

    @property
    def scope(self):
        return self.registry.scope("ziman")


class TestQueue(Case):
    def test_duplicate_idem_key_is_refused(self):
        self.assertTrue(self.q.submit(self.job()))
        self.assertFalse(self.q.submit(self.job()))
        self.assertEqual(len(self.q), 1)

    def test_same_key_in_two_tenants_is_two_jobs(self):
        self.assertTrue(self.q.submit(self.job()))
        self.assertTrue(self.q.submit(self.job(tenant="other")))
        self.assertEqual(len(self.q), 2)

    def test_fifo(self):
        self.q.submit(self.job(idem_key="a"))
        self.q.submit(self.job(idem_key="b"))
        self.assertEqual(self.q.take().idem_key, "a")
        self.assertEqual(self.q.take().idem_key, "b")

    def test_requeue_goes_to_the_tail(self):
        """A failing job must not starve the queue by retrying at the head."""
        first = self.job(idem_key="a")
        self.q.submit(first)
        self.q.submit(self.job(idem_key="b"))
        taken = self.q.take()
        self.q.requeue(taken)
        self.assertEqual(self.q.take().idem_key, "b")


class TestNeverInteractive(Case):
    def test_worker_always_marks_work_non_interactive(self):
        """If a job were ever marked interactive, the router would refuse the
        hosted rung and the whole background path would silently stop."""
        rules = RulesBrain({})
        remote = Scripted(BrainReply("thought", visible_tokens=500))
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote})
        w.submit(self.scope, self.job())
        self.assertTrue(w.step())
        self.assertEqual(len(remote.calls), 1)


class TestHappyPath(Case):
    def test_result_is_ledgered_with_cost_and_path(self):
        rules = RulesBrain({})
        remote = Scripted(BrainReply("here is why", visible_tokens=1000))
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote})
        w.submit(self.scope, self.job())
        w.step()
        kinds = [e.kind for e in self.ledger.read(self.scope)]
        self.assertIn("THINK_QUEUED", kinds)
        self.assertIn("THINK_DONE", kinds)
        done = next(e for e in self.ledger.read(self.scope)
                    if e.kind == "THINK_DONE")
        self.assertEqual(done.payload["billed_tokens"], 2600)   # 1000 x 2.6
        self.assertEqual(done.payload["rung"], "remote")

    def test_callback_receives_the_result(self):
        got = {}
        rules = RulesBrain({})
        remote = Scripted(BrainReply("answer", visible_tokens=10))
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote},
                        on_result=lambda s, j, r: got.update(
                            {"tenant": s.tenant.value, "text": r.text}))
        w.submit(self.scope, self.job())
        w.step()
        self.assertEqual(got, {"tenant": "ziman", "text": "answer"})

    def test_rules_answer_costs_nothing(self):
        rules = RulesBrain({"analyse": lambda p: "answered by rule"})
        w = self.worker({Rung.RULES: rules})
        w.submit(self.scope, self.job())
        w.step()
        self.assertEqual(self.quota.spent(NOW_S), 0)

    def test_pii_findings_are_recorded_without_the_values(self):
        rules = RulesBrain({})
        remote = Scripted(BrainReply("ok", visible_tokens=10))
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote})
        w.submit(self.scope, self.job(prompt="mail sara@example.com now"))
        w.step()
        done = next(e for e in self.ledger.read(self.scope)
                    if e.kind == "THINK_DONE")
        self.assertEqual(done.payload["scrubbed"], {"email": 1})
        # The address itself must not appear anywhere in the ledger.
        for event in self.ledger.read(self.scope):
            self.assertNotIn("sara@example.com", str(event.payload))


class TestFailureIsBounded(Case):
    def test_a_failing_job_is_parked_not_retried_forever(self):
        """An unbounded retry against a metered brain is an unbounded bill."""
        rules = RulesBrain({})
        remote = Scripted(*[BrainReply("", insufficient=True)
                            for _ in range(10)])
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote})
        w.submit(self.scope, self.job())
        for _ in range(MAX_ATTEMPTS + 2):
            w.step()
        self.assertEqual(len(w.parked), 1)
        self.assertEqual(len(self.q), 0)
        kinds = [e.kind for e in self.ledger.read(self.scope)]
        self.assertIn("THINK_PARKED", kinds)

    def test_retries_are_ledgered_individually(self):
        # P0 fix semantics: only TRANSIENT failures retry, each with bounded
        # backoff, and each attempt lands its own THINK_RETRY row. A policy
        # cap ("route:capped") is deterministic and must park, not retry.
        w = self.worker({Rung.RULES: RulesBrain({}), Rung.REMOTE: Boom()})
        w.submit(self.scope, self.job())
        w.step()
        w._now_s = lambda: NOW_S + 60      # the backoff elapses
        w.step()
        retries = [e for e in self.ledger.read(self.scope)
                   if e.kind == "THINK_RETRY"]
        self.assertEqual(len(retries), 2)

    def test_deterministic_route_denial_parks_without_retry(self):
        rules = RulesBrain({})
        remote = Scripted(*[BrainReply("", insufficient=True) for _ in range(5)])
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote})
        w.submit(self.scope, self.job())
        w.step(); w.step()                 # nothing left to retry into
        kinds = [e.kind for e in self.ledger.read(self.scope)]
        self.assertNotIn("THINK_RETRY", kinds)
        self.assertIn("THINK_PARKED", kinds)

    def test_a_raising_brain_does_not_kill_the_worker(self):
        w = self.worker({Rung.RULES: RulesBrain({}), Rung.REMOTE: Boom()})
        w.submit(self.scope, self.job())
        self.assertTrue(w.step())        # survives
        self.assertEqual(len(self.q), 1) # and requeued

    def test_unknown_tenant_is_parked_not_guessed(self):
        w = self.worker({Rung.RULES: RulesBrain({})})
        self.q.submit(self.job(tenant="ghost"))
        w.step()
        self.assertEqual(len(w.parked), 1)

    def test_exhausted_quota_parks_rather_than_spinning(self):
        self.quota.record("ziman", __import__(
            "ofn.kernel.domain", fromlist=["TokenSpend"]).TokenSpend(
                visible=10_000_000), NOW_S)
        rules = RulesBrain({})
        remote = Scripted(BrainReply("never", visible_tokens=1))
        w = self.worker({Rung.RULES: rules, Rung.REMOTE: remote})
        w.submit(self.scope, self.job())
        for _ in range(MAX_ATTEMPTS + 1):
            w.step()
        self.assertEqual(len(remote.calls), 0)   # brain never called
        self.assertEqual(len(w.parked), 1)


class TestDrainAndLoop(Case):
    def test_drain_empties_the_queue(self):
        rules = RulesBrain({"analyse": lambda p: "ok"})
        w = self.worker({Rung.RULES: rules})
        for i in range(5):
            w.submit(self.scope, self.job(idem_key=f"j{i}"))
        self.assertEqual(w.drain(), 5)
        self.assertEqual(len(self.q), 0)

    def test_drain_respects_the_limit(self):
        rules = RulesBrain({"analyse": lambda p: "ok"})
        w = self.worker({Rung.RULES: rules})
        for i in range(10):
            w.submit(self.scope, self.job(idem_key=f"j{i}"))
        self.assertEqual(w.drain(limit=3), 3)
        self.assertEqual(len(self.q), 7)

    def test_drain_stops_when_asked(self):
        """Shutdown must not wait for a queue of slow calls to finish."""
        rules = RulesBrain({"analyse": lambda p: "ok"})
        w = self.worker({Rung.RULES: rules})
        for i in range(10):
            w.submit(self.scope, self.job(idem_key=f"j{i}"))
        stop = threading.Event()
        stop.set()
        self.assertEqual(w.drain(stop=stop), 0)

    def test_status_reports_both_queues(self):
        w = self.worker({Rung.RULES: RulesBrain({})})
        w.submit(self.scope, self.job())
        self.assertEqual(w.status(), {"queued": 1, "parked": 0})


if __name__ == "__main__":
    unittest.main()
