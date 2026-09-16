"""Routing policy, PII scrubbing, and the budget-leak the router exists to stop."""

from __future__ import annotations

import unittest

from ofn.adapters.remote_brain import RemoteBrain
from ofn.adapters.router import BrainReply, ModelRouter, RulesBrain
from ofn.kernel.domain import TenantId
from ofn.kernel.errors import FailClosedError
from ofn.kernel import routing
from ofn.kernel.quota import NodeQuota
from ofn.kernel.routing import (
    INTERACTIVE_BUDGET_MS, RouteRequest, Rung, fits_interactive, may_escalate,
    start_rung, token_estimate,
)
from ofn.kernel.scrub import assert_clean, has_identifying_data, scrub

T = TenantId("alpha")
NOW = 0


def quota(capacity=10_000_000, utilisation=1.0, mult=2.6) -> NodeQuota:
    return NodeQuota(estimated_capacity_tokens=capacity, utilisation=utilisation,
                     shares={"alpha": 1.0}, orchestration_multiplier=mult)


class Scripted:
    """A brain that says exactly what the test tells it to."""

    def __init__(self, *replies: BrainReply):
        self.replies = list(replies)
        self.calls: list[tuple[str, str]] = []

    def answer(self, task, prompt):
        self.calls.append((task, prompt))
        return self.replies.pop(0) if self.replies else BrainReply("", True)


# ══ scrubbing ═══════════════════════════════════════════════════════════
class TestScrub(unittest.TestCase):
    def test_email(self):
        r = scrub("write to sara@example.com today")
        self.assertNotIn("sara@example.com", r.text)
        self.assertEqual(r.findings["email"], 1)

    def test_australian_mobile(self):
        for n in ["0412 345 678", "0412345678", "+61 412 345 678"]:
            with self.subTest(number=n):
                self.assertFalse(scrub(f"call me on {n}").clean)

    def test_card_number(self):
        r = scrub("card 4111 1111 1111 1111 expires soon")
        self.assertIn("[CARD]", r.text)

    def test_api_key_shapes(self):
        for s in ["sk-abcdefghijklmnopqrstuvwx",
                  "api_ABCDEFGHIJKLMNOPQRST",
                  "Bearer abcdefghijklmnopqrstuvwxyz"]:
            with self.subTest(secret=s[:8]):
                self.assertIn("[SECRET]", scrub(f"use {s} please").text)

    def test_credentials_in_url_are_stripped(self):
        r = scrub("https://user:hunter2@example.com/x")
        self.assertNotIn("hunter2", r.text)

    def test_ip_address(self):
        self.assertIn("[IP]", scrub("host is 192.168.0.138").text)

    def test_clean_text_is_untouched(self):
        text = "چند باکس این هفته آماده می‌شود؟"
        r = scrub(text)
        self.assertEqual(r.text, text)
        self.assertTrue(r.clean)

    def test_counts_every_occurrence(self):
        r = scrub("a@b.com and c@d.com and e@f.com")
        self.assertEqual(r.findings["email"], 3)

    def test_summary_is_human_readable(self):
        self.assertIn("redacted", scrub("x@y.com").summary)
        self.assertIn("no identifying data", scrub("hello").summary)

    def test_predicate_and_assertion(self):
        self.assertTrue(has_identifying_data("a@b.com"))
        self.assertFalse(has_identifying_data("hello"))
        assert_clean("hello")
        with self.assertRaises(ValueError):
            assert_clean("a@b.com")

    def test_empty_input(self):
        self.assertTrue(scrub("").clean)


# ══ routing policy ══════════════════════════════════════════════════════
class TestRungOrdering(unittest.TestCase):
    def test_only_remote_rungs_cost_money(self):
        self.assertFalse(Rung.RULES.costs_quota())
        self.assertFalse(Rung.LOCAL.costs_quota())
        self.assertTrue(Rung.REMOTE.costs_quota())
        self.assertTrue(Rung.REMOTE_DEEP.costs_quota())

    def test_interactive_fit(self):
        self.assertTrue(fits_interactive(Rung.RULES))
        self.assertTrue(fits_interactive(Rung.LOCAL))
        self.assertFalse(fits_interactive(Rung.REMOTE))
        self.assertFalse(fits_interactive(Rung.REMOTE_DEEP))

    def test_deep_costs_four_times(self):
        req = RouteRequest(task="t", estimated_tokens=1000)
        self.assertEqual(token_estimate(req, Rung.RULES), 0)
        self.assertEqual(token_estimate(req, Rung.LOCAL), 0)
        self.assertEqual(token_estimate(req, Rung.REMOTE), 1000)
        self.assertEqual(token_estimate(req, Rung.REMOTE_DEEP), 4000)


class TestNoImplicitEscalation(unittest.TestCase):
    """The budget leak this module was written to prevent."""

    def test_silence_does_not_authorise_spending(self):
        req = RouteRequest(task="t")
        d = may_escalate(Rung.LOCAL, req, lower_reported_insufficient=False)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "route:no-implicit-escalation")

    def test_explicit_insufficiency_does(self):
        req = RouteRequest(task="t")
        d = may_escalate(Rung.LOCAL, req, lower_reported_insufficient=True)
        self.assertTrue(d.allowed)
        self.assertIs(d.rung, Rung.REMOTE)

    def test_deep_rung_needs_the_owner(self):
        req = RouteRequest(task="t", max_rung=Rung.REMOTE_DEEP)
        d = may_escalate(Rung.REMOTE, req, lower_reported_insufficient=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "route:deep-needs-owner")

    def test_deep_rung_with_owner_approval(self):
        req = RouteRequest(task="t", owner_approved_deep=True,
                           max_rung=Rung.REMOTE_DEEP)
        d = may_escalate(Rung.REMOTE, req, lower_reported_insufficient=True)
        self.assertTrue(d.allowed)

    def test_caller_cap_is_honoured(self):
        req = RouteRequest(task="t", max_rung=Rung.LOCAL)
        d = may_escalate(Rung.LOCAL, req, lower_reported_insufficient=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "route:capped")

    def test_cannot_escalate_past_the_top(self):
        d = may_escalate(Rung.REMOTE_DEEP, RouteRequest(task="t"),
                         lower_reported_insufficient=True)
        self.assertFalse(d.allowed)


class TestInteractivePathIsProtected(unittest.TestCase):
    def test_slow_rung_refused_on_interactive_request(self):
        req = RouteRequest(task="t", interactive=True)
        d = may_escalate(Rung.LOCAL, req, lower_reported_insufficient=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "route:too-slow-for-interactive")
        self.assertIn("queue it", d.reason)

    def test_local_is_still_reachable_when_interactive(self):
        req = RouteRequest(task="t", interactive=True)
        d = may_escalate(Rung.RULES, req, lower_reported_insufficient=True)
        self.assertTrue(d.allowed)
        self.assertIs(d.rung, Rung.LOCAL)

    def test_budget_is_a_documented_number(self):
        self.assertEqual(INTERACTIVE_BUDGET_MS, 10_000)


# ══ the router itself ═══════════════════════════════════════════════════
class TestRouter(unittest.TestCase):
    def test_requires_a_free_rung(self):
        with self.assertRaises(FailClosedError):
            ModelRouter({}, quota())

    def test_rules_answer_costs_nothing(self):
        rules = RulesBrain({"classify": lambda p: "lead"})
        q = quota()
        r = ModelRouter({Rung.RULES: rules}, q).ask(
            T, RouteRequest(task="classify"), "some text", now_epoch_s=NOW)
        self.assertEqual(r.text, "lead")
        self.assertIs(r.rung, Rung.RULES)
        self.assertEqual(r.spend, 0)
        self.assertEqual(q.spent(NOW), 0)

    def test_falls_through_to_local_when_rules_cannot_help(self):
        rules = RulesBrain({})                      # no handler
        local = Scripted(BrainReply("local answer"))
        r = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local}, quota()).ask(
            T, RouteRequest(task="anything"), "text", now_epoch_s=NOW)
        self.assertEqual(r.text, "local answer")
        self.assertIs(r.rung, Rung.LOCAL)
        self.assertEqual(r.spend, 0)

    def test_prompt_is_scrubbed_before_any_brain_sees_it(self):
        rules = RulesBrain({})
        local = Scripted(BrainReply("ok"))
        router = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local}, quota())
        router.ask(T, RouteRequest(task="t"),
                   "email sara@example.com about 0412 345 678", now_epoch_s=NOW)
        _, seen = local.calls[0]
        self.assertNotIn("sara@example.com", seen)
        self.assertNotIn("0412", seen)

    def test_remote_spend_uses_the_multiplier_when_unreported(self):
        rules = RulesBrain({})
        local = Scripted(BrainReply("", insufficient=True))
        remote = Scripted(BrainReply("deep answer", visible_tokens=1000))
        q = quota()
        r = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local,
                         Rung.REMOTE: remote}, q).ask(
            T, RouteRequest(task="t", estimated_tokens=1000), "text",
            now_epoch_s=NOW)
        self.assertEqual(r.text, "deep answer")
        self.assertEqual(r.spend, 2600)           # 1000 x 2.6
        self.assertEqual(q.spent(NOW, T), 2600)

    def test_reported_orchestration_is_used_verbatim(self):
        rules = RulesBrain({})
        local = Scripted(BrainReply("", insufficient=True))
        remote = Scripted(BrainReply("x", visible_tokens=1000,
                                     orchestration_tokens=9000))
        q = quota()
        r = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local,
                         Rung.REMOTE: remote}, q).ask(
            T, RouteRequest(task="t", estimated_tokens=1000), "t", now_epoch_s=NOW)
        self.assertEqual(r.spend, 10_000)

    def test_quota_exhaustion_refuses_before_calling_the_brain(self):
        rules = RulesBrain({})
        local = Scripted(BrainReply("", insufficient=True))
        remote = Scripted(BrainReply("should never run", visible_tokens=1))
        q = quota(capacity=100, utilisation=1.0, mult=1.0)
        r = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local,
                         Rung.REMOTE: remote}, q).ask(
            T, RouteRequest(task="t", estimated_tokens=5000), "t", now_epoch_s=NOW)
        self.assertFalse(r.ok)
        self.assertEqual(len(remote.calls), 0)     # never reached
        self.assertEqual(q.spent(NOW), 0)

    def test_interactive_request_never_reaches_the_paid_rung(self):
        rules = RulesBrain({})
        local = Scripted(BrainReply("", insufficient=True))
        remote = Scripted(BrainReply("expensive", visible_tokens=99999))
        q = quota()
        r = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local,
                         Rung.REMOTE: remote}, q).ask(
            T, RouteRequest(task="t", interactive=True, estimated_tokens=1000),
            "t", now_epoch_s=NOW)
        self.assertEqual(len(remote.calls), 0)
        self.assertEqual(q.spent(NOW), 0)
        self.assertIn("too slow", r.refused)

    def test_missing_rung_is_not_routed_around_silently(self):
        """No LOCAL configured must not mean 'go straight to paid'."""
        rules = RulesBrain({})
        remote = Scripted(BrainReply("paid", visible_tokens=1000))
        q = quota()
        router = ModelRouter({Rung.RULES: rules, Rung.REMOTE: remote}, q)
        r = router.ask(T, RouteRequest(task="t", estimated_tokens=1000), "t",
                       now_epoch_s=NOW)
        # It may reach REMOTE, but only through an explicit insufficiency
        # chain, and the path must record that LOCAL was absent.
        self.assertIn("local:absent", r.path)

    def test_path_is_recorded_for_the_ledger(self):
        rules = RulesBrain({})
        local = Scripted(BrainReply("", insufficient=True))
        remote = Scripted(BrainReply("done", visible_tokens=10))
        r = ModelRouter({Rung.RULES: rules, Rung.LOCAL: local,
                         Rung.REMOTE: remote}, quota()).ask(
            T, RouteRequest(task="t", estimated_tokens=10), "t", now_epoch_s=NOW)
        self.assertEqual(r.path[0], "rules:insufficient")
        self.assertEqual(r.path[-1], "remote:ok")

    def test_events_are_emitted_for_audit(self):
        events: list[tuple[str, dict]] = []
        rules = RulesBrain({})
        local = Scripted(BrainReply("", insufficient=True))
        remote = Scripted(BrainReply("x", visible_tokens=100))
        ModelRouter({Rung.RULES: rules, Rung.LOCAL: local, Rung.REMOTE: remote},
                    quota(),
                    on_event=lambda k, p: events.append((k, dict(p)))).ask(
            T, RouteRequest(task="t", estimated_tokens=100),
            "mail me at a@b.com", now_epoch_s=NOW)
        kinds = [k for k, _ in events]
        self.assertIn("SCRUB", kinds)
        self.assertIn("ESCALATE", kinds)
        self.assertIn("SPEND", kinds)


# ══ remote client ═══════════════════════════════════════════════════════
class TestRemoteBrainFailsClosed(unittest.TestCase):
    def test_missing_key_is_not_armed_not_an_answer(self):
        r = RemoteBrain(api_key="", model="m").answer("t", "p")
        self.assertTrue(r.insufficient)
        self.assertIn("not-armed", r.model)
        self.assertEqual(r.text, "")

    def test_parse_extracts_tokens(self):
        b = RemoteBrain(api_key="k", model="m")
        reply = b._parse({
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        })
        self.assertEqual(reply.text, "hello")
        self.assertEqual(reply.visible_tokens, 15)
        self.assertEqual(reply.orchestration_tokens, 0)   # unknown, not zero-cost
        self.assertFalse(reply.insufficient)

    def test_parse_reads_orchestration_when_present(self):
        b = RemoteBrain(api_key="k", model="m")
        reply = b._parse({
            "choices": [{"message": {"content": "x"}}],
            "usage": {"total_tokens": 100, "orchestration_tokens": 900},
        })
        self.assertEqual(reply.visible_tokens, 100)
        self.assertEqual(reply.orchestration_tokens, 900)

    def test_malformed_body_is_insufficient_not_empty_success(self):
        b = RemoteBrain(api_key="k", model="m")
        self.assertTrue(b._parse({}).insufficient)
        self.assertTrue(b._parse({"choices": []}).insufficient)

    def test_blank_content_counts_as_insufficient(self):
        b = RemoteBrain(api_key="k", model="m")
        self.assertTrue(b._parse(
            {"choices": [{"message": {"content": "   "}}]}).insufficient)

    def test_timeout_default_matches_observed_latency(self):
        self.assertGreaterEqual(RemoteBrain(api_key="k", model="m").timeout_s, 180)


class TestLatencyCalibration(unittest.TestCase):
    """The shipped latency numbers are estimates. These tests are about what
    happens when reality disagrees with them — in both directions."""

    def setUp(self):
        self._saved = dict(routing.WORST_CASE_MS)

    def tearDown(self):
        routing.WORST_CASE_MS.clear()
        routing.WORST_CASE_MS.update(self._saved)

    def test_a_slower_observation_raises_the_worst_case(self):
        routing.calibrate_latency(Rung.REMOTE, 90_000)
        self.assertEqual(routing.WORST_CASE_MS[Rung.REMOTE], 90_000)

    def test_a_faster_observation_changes_nothing(self):
        """One fast call proves nothing about the tail. If a good sample could
        lower the worst case, a lucky Tuesday would put a rung that sometimes
        takes ninety seconds back on a partner's screen."""
        before = routing.WORST_CASE_MS[Rung.REMOTE]
        routing.calibrate_latency(Rung.REMOTE, 900)
        self.assertEqual(routing.WORST_CASE_MS[Rung.REMOTE], before)

    def test_calibration_cannot_make_a_slow_rung_interactive(self):
        routing.calibrate_latency(Rung.REMOTE, 12)
        self.assertFalse(fits_interactive(Rung.REMOTE))

    def test_calibration_can_take_a_rung_off_the_interactive_path(self):
        """The one direction that matters: evidence that LOCAL is slower than
        believed must be able to disqualify it."""
        self.assertTrue(fits_interactive(Rung.LOCAL))
        routing.calibrate_latency(Rung.LOCAL, INTERACTIVE_BUDGET_MS + 1)
        self.assertFalse(fits_interactive(Rung.LOCAL))

    def test_negative_latency_is_rejected(self):
        with self.assertRaises(ValueError):
            routing.calibrate_latency(Rung.REMOTE, -1)

    def test_the_two_hosted_rungs_are_not_treated_as_one(self):
        """The correction that produced this test: the fast model and the deep
        model are different animals, and a single shared number for both would
        either slander the fast one or under-time the slow one."""
        self.assertLess(routing.WORST_CASE_MS[Rung.REMOTE],
                        routing.WORST_CASE_MS[Rung.REMOTE_DEEP])
        self.assertLess(routing.WORST_CASE_MS[Rung.REMOTE], 60_000)

    def test_neither_hosted_rung_is_ever_interactive(self):
        for rung in (Rung.REMOTE, Rung.REMOTE_DEEP):
            with self.subTest(rung=rung):
                self.assertFalse(fits_interactive(rung))


if __name__ == "__main__":
    unittest.main()
