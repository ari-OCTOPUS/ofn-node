"""The Node: question derivation, the answer→fact→ledger sequence, and the
owner's decision path end to end.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import HELD, Outbox
from ofn.kernel.domain import Action, Confidence, PackSpec, RiskTier, TenantId
from ofn.kernel.questions import (
    DEFAULT_MAX_QUESTIONS, Kind, is_ready, plan, readiness,
)
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

NOW_S = 1_785_000_000
NOW_ISO = "2026-08-03T10:00:00Z"


def pack(name="alpha", **kw) -> PackSpec:
    base = dict(
        tenant=TenantId(name), capacity_units_per_week=6, quota_share=1.0,
        required_facts={"offer.cogs": Confidence.OWNER_CONFIRMED,
                        "ops.delivery_model": Confidence.OWNER_CONFIRMED},
        # A pack must declare the gate for a node-wide closure to reach it.
        # Every real pack lists secret_rotation; test_packs.py enforces that.
        gates=("secret_rotation",),
        risk_overrides={"publish_price": RiskTier.RED,
                        "send_reply": RiskTier.YELLOW,
                        "classify": RiskTier.GREEN},
    )
    base.update(kw)
    return PackSpec(**base)


# ══ question planning ═══════════════════════════════════════════════════
class TestQuestionPlanning(unittest.TestCase):
    def test_missing_facts_become_questions(self):
        qs = plan(pack(), {})
        self.assertEqual({q.key for q in qs},
                         {"offer.cogs", "ops.delivery_model"})

    def test_satisfied_facts_are_not_asked_again(self):
        qs = plan(pack(), {"offer.cogs": Confidence.OWNER_CONFIRMED})
        self.assertEqual([q.key for q in qs], ["ops.delivery_model"])

    def test_weak_fact_is_still_asked(self):
        qs = plan(pack(), {"offer.cogs": Confidence.GUESSED,
                           "ops.delivery_model": Confidence.OWNER_CONFIRMED})
        self.assertEqual([q.key for q in qs], ["offer.cogs"])
        self.assertFalse(qs[0].is_missing)

    def test_missing_outranks_weak(self):
        qs = plan(pack(), {"offer.cogs": Confidence.MEASURED})
        self.assertEqual(qs[0].key, "ops.delivery_model")   # missing first

    def test_list_is_capped_so_a_screen_stays_answerable(self):
        p = pack(required_facts={f"a.f{i}": Confidence.MEASURED
                                 for i in range(20)})
        self.assertEqual(len(plan(p, {})), DEFAULT_MAX_QUESTIONS)
        self.assertEqual(len(plan(p, {}, max_questions=1)), 1)

    def test_cap_must_be_positive(self):
        with self.assertRaises(ValueError):
            plan(pack(), {}, max_questions=0)

    def test_input_kind_is_inferred(self):
        p = pack(required_facts={
            "ops.crew_count": Confidence.MEASURED,
            "ops.delivery_model": Confidence.MEASURED,
            "brand.story": Confidence.MEASURED})
        kinds = {q.key: q.kind for q in plan(p, {}, max_questions=9)}
        self.assertIs(kinds["ops.crew_count"], Kind.NUMBER)
        self.assertIs(kinds["ops.delivery_model"], Kind.CHOICE)
        self.assertIs(kinds["brand.story"], Kind.TEXT)

    def test_why_is_a_readable_sentence(self):
        q = plan(pack(), {})[0]
        self.assertIn("ثبت", q.why)
        self.assertGreater(len(q.why), 10)

    def test_determinism(self):
        first = [q.key for q in plan(pack(), {})]
        for _ in range(15):
            self.assertEqual([q.key for q in plan(pack(), {})], first)

    def test_readiness_is_a_fraction(self):
        self.assertEqual(readiness(pack(), {}), (0, 2))
        self.assertEqual(
            readiness(pack(), {"offer.cogs": Confidence.OWNER_CONFIRMED}), (1, 2))
        full = {"offer.cogs": Confidence.OWNER_CONFIRMED,
                "ops.delivery_model": Confidence.OWNER_CONFIRMED}
        self.assertEqual(readiness(pack(), full), (2, 2))
        self.assertTrue(is_ready(pack(), full))

    def test_pack_with_no_required_facts(self):
        p = pack(required_facts={})
        self.assertEqual(plan(p, {}), ())
        self.assertEqual(readiness(p, {}), (0, 0))
        self.assertFalse(is_ready(p, {}))


# ══ the node ════════════════════════════════════════════════════════════
class NodeCase(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        d = self._d.name
        self.packs = {"alpha": pack("alpha")}
        self.node = Node(
            registry=TenantRegistry(self.packs),
            quota=NodeQuota(estimated_capacity_tokens=10_000_000,
                            utilisation=1.0, shares={"alpha": 1.0}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            base_closed_gates=("secret_rotation",))
        self.scope = self.node.registry.scope("alpha")

    def tearDown(self):
        self.node.close()
        self._d.cleanup()


class TestAnswerFlow(NodeCase):
    def test_answer_becomes_a_fact_and_a_ledger_entry(self):
        r = self.node.submit_answer(self.scope, "u1",
                                    {"key": "offer.cogs", "value": 42})
        self.assertTrue(r["ok"])
        fact = self.node.facts.current(self.scope, "offer", "cogs")
        self.assertEqual(fact.value, 42)
        self.assertIs(fact.confidence, Confidence.OWNER_CONFIRMED)
        kinds = [e.kind for e in self.node.ledger.read(self.scope)]
        self.assertIn("FACT", kinds)

    def test_answer_records_who_said_it(self):
        self.node.submit_answer(self.scope, "u42",
                                {"key": "offer.cogs", "value": 1})
        self.assertEqual(
            self.node.facts.current(self.scope, "offer", "cogs").source,
            "partner:u42")

    def test_answering_advances_readiness_and_shortens_the_list(self):
        before = self.node.questions_for(self.scope, "u1")
        r = self.node.submit_answer(self.scope, "u1",
                                    {"key": "offer.cogs", "value": 42})
        self.assertEqual(r["readiness"], {"done": 1, "total": 2})
        self.assertLess(len(r["remaining"]), len(before))

    def test_a_question_the_pack_never_asked_is_refused(self):
        """Otherwise this endpoint is a way to write arbitrary facts."""
        r = self.node.submit_answer(self.scope, "u1",
                                    {"key": "secret.backdoor", "value": "x"})
        self.assertFalse(r["ok"])
        self.assertIsNone(self.node.facts.current(self.scope, "secret",
                                                  "backdoor"))

    def test_malformed_answers(self):
        for body in ({}, {"key": "nodot", "value": 1}, {"key": "offer.cogs"}):
            with self.subTest(body=body):
                self.assertFalse(
                    self.node.submit_answer(self.scope, "u1", body)["ok"])

    def test_correcting_an_answer_supersedes_rather_than_overwrites(self):
        self.node.submit_answer(self.scope, "u1", {"key": "offer.cogs",
                                                   "value": 10})
        self.node.submit_answer(self.scope, "u1", {"key": "offer.cogs",
                                                   "value": 20})
        history = self.node.facts.history(self.scope, "offer", "cogs")
        self.assertEqual(len(history), 2)
        self.assertEqual(self.node.facts.current(self.scope, "offer",
                                                 "cogs").value, 20)


class TestStatus(NodeCase):
    def test_status_shape(self):
        s = self.node.status_for(self.scope)
        self.assertEqual(s["tenant"], "alpha")
        self.assertEqual(s["capacity_per_week"], 6)
        self.assertEqual(s["readiness"], {"done": 0, "total": 2})
        self.assertFalse(s["safe_mode"])


class TestProposeAndDecide(NodeCase):
    # An action that leaves the node without its required facts is RED by
    # design (C11). These tests are about the *decision path*, so they supply
    # the evidence; `test_missing_facts_force_red` below covers the other case.
    EVIDENCE = {"offer.cogs": Confidence.OWNER_CONFIRMED,
                "ops.delivery_model": Confidence.OWNER_CONFIRMED}

    def _propose(self, name="send_reply", evidence=None, **kw):
        action = Action(tenant=TenantId("alpha"), name=name, leaves_node=True,
                        evidence=self.EVIDENCE if evidence is None else evidence,
                        **kw)
        return self.node.propose(self.scope, action, {"to": "someone"},
                                 f"idem-{name}")

    def test_missing_facts_force_red_even_for_a_yellow_action(self):
        self.node.base_closed_gates = ()
        d = self._propose(evidence={})
        self.assertIs(d.tier, RiskTier.RED)
        self.assertIn("fact", d.reason)

    def test_green_never_enters_the_queue(self):
        action = Action(tenant=TenantId("alpha"), name="classify")
        d = self.node.propose(self.scope, action, {}, "idem-classify")
        self.assertIs(d.tier, RiskTier.RED)   # a closed gate lifts even this
        self.assertEqual(len(self.node.outbox.pending(self.scope)), 1)

        # With no closed gates the same action is GREEN and skips the outbox.
        self.node.base_closed_gates = ()
        d2 = self.node.propose(self.scope, action, {}, "idem-classify-2")
        self.assertIs(d2.tier, RiskTier.GREEN)
        self.assertFalse(d2.needs_human)
        self.assertEqual(len(self.node.outbox.pending(self.scope)), 1)

    def test_yellow_is_queued_for_the_owner(self):
        self.node.base_closed_gates = ()
        d = self._propose()
        self.assertIs(d.tier, RiskTier.YELLOW)
        self.assertEqual(len(self.node.outbox.pending(self.scope)), 1)

    def test_every_proposal_is_ledgered_even_when_denied(self):
        self.node.killed = True
        d = self._propose()
        self.assertFalse(d.allowed)
        kinds = [e.kind for e in self.node.ledger.read(self.scope)]
        self.assertIn("PROPOSE", kinds)

    def test_owner_sees_the_queue_with_tenant_labels(self):
        self.node.base_closed_gates = ()
        self._propose()
        q = self.node.owner_queue()
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["tenant"], "alpha")
        self.assertEqual(q[0]["tier"], "yellow")

    def test_red_needs_the_second_confirmation(self):
        self.node.base_closed_gates = ()
        self._propose(name="publish_price")
        item_id = self.node.owner_queue()[0]["id"]
        once = self.node.owner_decide(item_id, approve=True,
                                      confirmed_twice=False)
        self.assertFalse(once["ok"])
        twice = self.node.owner_decide(item_id, approve=True,
                                       confirmed_twice=True)
        self.assertTrue(twice["ok"])

    def test_yellow_needs_only_one(self):
        self.node.base_closed_gates = ()
        self._propose()
        item_id = self.node.owner_queue()[0]["id"]
        self.assertTrue(self.node.owner_decide(item_id, True, False)["ok"])

    def test_rejection_is_recorded(self):
        self.node.base_closed_gates = ()
        self._propose()
        item_id = self.node.owner_queue()[0]["id"]
        r = self.node.owner_decide(item_id, approve=False, confirmed_twice=False)
        self.assertEqual(r["status"], "rejected")
        kinds = [e.kind for e in self.node.ledger.read(self.scope)]
        self.assertIn("VERDICT", kinds)

    def test_unknown_item_is_refused(self):
        self.assertFalse(self.node.owner_decide("nope:x", True, True)["ok"])
        self.assertFalse(self.node.owner_decide("alpha:absent", True, True)["ok"])


class TestSafeModeReachesTheGates(NodeCase):
    def test_safe_mode_appears_in_closed_gates(self):
        from ofn.adapters.boot import BootReport, Severity
        rep = BootReport()
        rep.add("clock", Severity.CRITICAL, "unsynced")
        self.node.boot = rep
        self.assertIn("safe_mode", self.node.closed_gates)
        self.assertTrue(self.node.status_for(self.scope)["safe_mode"])


class TestHealthProbe(NodeCase):
    def test_healthy_when_stores_answer(self):
        self.assertTrue(self.node.healthy())

    def test_unhealthy_when_the_database_is_gone(self):
        self.node.ledger.close()
        self.assertFalse(self.node.healthy())


if __name__ == "__main__":
    unittest.main()
