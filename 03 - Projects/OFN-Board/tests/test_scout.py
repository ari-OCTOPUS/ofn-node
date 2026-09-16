"""The daily scout. Every test asks the same question a different way:

if this runs unattended every morning for a year, does it get smarter, or does
it just get louder?
"""

from __future__ import annotations

import unittest

from ofn.kernel.allocation import Trial
from ofn.kernel.errors import FailClosedError
from ofn.kernel.scout import (
    SOFT_REJECT_COOLDOWN_S, STALE_TRIAL_S, Candidate, Constraints, Disposition,
    Memory, Note, brief, research_focus, screen, triage,
)

NOW = 1_785_000_000
OPI = "opi5pro"
ESP = "esp32"
LIMITS = Constraints(known_classes=(OPI, ESP))


def cand(**kw) -> Candidate:
    base = dict(key="thing", title="A thing", classes=(OPI,))
    base.update(kw)
    return Candidate(**base)


class TestValidation(unittest.TestCase):
    def test_key_must_be_a_safe_slug(self):
        with self.assertRaises(FailClosedError):
            cand(key="../etc/passwd")

    def test_untitled_candidate_is_refused(self):
        with self.assertRaises(FailClosedError):
            cand(title="   ")

    def test_constraints_without_classes_are_refused(self):
        """A screen that matches everything is decoration."""
        with self.assertRaises(FailClosedError):
            Constraints(known_classes=())


class TestScreen(unittest.TestCase):
    def test_private_key_on_device_is_a_hard_no(self):
        v = screen(cand(needs_private_key=True), LIMITS)
        self.assertFalse(v.accepted)
        self.assertTrue(v.hard)
        self.assertEqual(v.rule, "scout:no-key-on-device")

    def test_capital_is_a_hard_no(self):
        v = screen(cand(needs_capital=True), LIMITS)
        self.assertFalse(v.accepted)
        self.assertTrue(v.hard)

    def test_kyc_is_a_hard_no(self):
        self.assertFalse(screen(cand(needs_kyc=True), LIMITS).accepted)

    def test_hardware_we_do_not_own_is_refused(self):
        v = screen(cand(classes=("nvidia-gpu",)), LIMITS)
        self.assertFalse(v.accepted)
        self.assertIn("do not have", v.reason)

    def test_no_class_named_is_refused_but_softly(self):
        """Vagueness may be the researcher's fault, not the thing's."""
        v = screen(cand(classes=()), LIMITS)
        self.assertFalse(v.accepted)
        self.assertFalse(v.hard)

    def test_a_good_candidate_passes_and_says_where_it_runs(self):
        v = screen(cand(classes=(OPI, "nvidia-gpu")), LIMITS)
        self.assertTrue(v.accepted)
        self.assertIn(OPI, v.reason)

    def test_every_refusal_names_its_rule(self):
        for c in [cand(needs_capital=True), cand(needs_kyc=True),
                  cand(classes=()), cand(classes=("x",))]:
            with self.subTest(candidate=c.key):
                self.assertTrue(screen(c, LIMITS).rule.startswith("scout:"))


class TestMemoryRatchet(unittest.TestCase):
    def test_a_hard_rejection_cannot_be_softened_later(self):
        """The failure this prevents: an agreeable second opinion quietly
        reopening something that was closed for a structural reason."""
        m = Memory()
        m.record(Note("x", Disposition.REJECTED_HARD, "needs capital", NOW))
        m.record(Note("x", Disposition.ACCEPTED, "looks great actually", NOW + 10))
        self.assertIs(m.disposition("x"), Disposition.REJECTED_HARD)

    def test_other_dispositions_do_update(self):
        m = Memory()
        m.record(Note("x", Disposition.PROPOSED, "waiting", NOW))
        m.record(Note("x", Disposition.ACCEPTED, "owner pinned it", NOW + 10))
        self.assertIs(m.disposition("x"), Disposition.ACCEPTED)

    def test_unseen_is_the_default(self):
        self.assertIs(Memory().disposition("nothing"), Disposition.UNSEEN)


class TestTriage(unittest.TestCase):
    def test_a_fresh_good_candidate_reaches_the_owner(self):
        fresh, refused = triage([cand()], Memory(), LIMITS, now_epoch_s=NOW)
        self.assertEqual(len(fresh), 1)
        self.assertEqual(refused, ())

    def test_a_settled_candidate_costs_nothing_to_refuse_again(self):
        m = Memory()
        m.record(Note("thing", Disposition.REJECTED_HARD, "needs capital", NOW))
        fresh, refused = triage([cand()], m, LIMITS, now_epoch_s=NOW)
        self.assertEqual(fresh, ())
        self.assertEqual(refused[0][1].rule, "scout:already-final")

    def test_a_thing_that_ran_and_failed_does_not_come_back(self):
        m = Memory()
        m.record(Note("thing", Disposition.TRIED_FAILED, "produced nothing", NOW))
        fresh, _ = triage([cand()], m, LIMITS, now_epoch_s=NOW)
        self.assertEqual(fresh, ())

    def test_soft_rejection_cools_off_then_returns(self):
        """A network in closed beta is a fact about a moment, not forever."""
        m = Memory()
        m.record(Note("thing", Disposition.REJECTED_SOFT, "was in closed beta", NOW))

        fresh, refused = triage([cand()], m, LIMITS, now_epoch_s=NOW + 86400)
        self.assertEqual(fresh, ())
        self.assertEqual(refused[0][1].rule, "scout:cooling-off")

        later = NOW + SOFT_REJECT_COOLDOWN_S + 1
        fresh, _ = triage([cand()], m, LIMITS, now_epoch_s=later)
        self.assertEqual(len(fresh), 1)

    def test_something_already_in_front_of_the_owner_is_not_re_proposed(self):
        m = Memory()
        m.record(Note("thing", Disposition.PROPOSED, "waiting", NOW))
        fresh, refused = triage([cand()], m, LIMITS, now_epoch_s=NOW)
        self.assertEqual(fresh, ())
        self.assertEqual(refused[0][1].rule, "scout:duplicate")

    def test_refusals_are_returned_not_swallowed(self):
        """A scout that silently drops nine of ten proposals looks exactly like
        a scout that found one thing."""
        cands = [cand(key="a", needs_capital=True), cand(key="b"),
                 cand(key="c", needs_kyc=True)]
        fresh, refused = triage(cands, Memory(), LIMITS, now_epoch_s=NOW)
        self.assertEqual(len(fresh), 1)
        self.assertEqual(len(refused), 2)

    def test_triage_is_deterministic(self):
        cands = [cand(key=k) for k in ("c", "a", "b")]
        first = triage(cands, Memory(), LIMITS, now_epoch_s=NOW)
        for _ in range(3):
            self.assertEqual(triage(cands, Memory(), LIMITS, now_epoch_s=NOW), first)


class TestResearchFocus(unittest.TestCase):
    def test_an_idle_hardware_class_is_the_first_question(self):
        qs = research_focus(Memory(), {}, [OPI, ESP], now_epoch_s=NOW)
        self.assertTrue(any(ESP in q for q in qs))
        self.assertTrue(any(OPI in q for q in qs))

    def test_a_long_running_producer_of_nothing_becomes_a_question(self):
        trials = {("a1", OPI): Trial("a1", OPI, seconds=STALE_TRIAL_S + 1,
                                     accepted=0)}
        qs = research_focus(Memory(), trials, [OPI], now_epoch_s=NOW)
        self.assertTrue(any("produced nothing" in q for q in qs))

    def test_a_working_arm_does_not_generate_a_question(self):
        trials = {("a1", OPI): Trial("a1", OPI, seconds=999_999, accepted=500)}
        qs = research_focus(Memory(), trials, [OPI], now_epoch_s=NOW)
        self.assertFalse(any("produced nothing" in q for q in qs))

    def test_open_ended_discovery_is_the_fallback_not_the_default(self):
        """When something specific is wrong, ask about that instead."""
        trials = {("a1", OPI): Trial("a1", OPI, seconds=STALE_TRIAL_S + 1,
                                     accepted=0)}
        qs = research_focus(Memory(), trials, [OPI], now_epoch_s=NOW,
                            max_questions=1)
        self.assertIn("produced nothing", qs[0])

    def test_questions_are_bounded(self):
        classes = [f"class{i}" for i in range(20)]
        qs = research_focus(Memory(), {}, classes, now_epoch_s=NOW, max_questions=3)
        self.assertEqual(len(qs), 3)

    def test_there_is_always_at_least_one_question(self):
        trials = {("a1", OPI): Trial("a1", OPI, seconds=999_999, accepted=9)}
        self.assertTrue(research_focus(Memory(), trials, [OPI], now_epoch_s=NOW))


class TestBrief(unittest.TestCase):
    def test_the_rejection_list_travels_with_the_question(self):
        """A few hundred tokens of 'we already said no to these' saves a whole
        call spent re-finding them."""
        m = Memory()
        m.record(Note("dead", Disposition.REJECTED_HARD, "needs capital", NOW))
        m.record(Note("live", Disposition.ACCEPTED, "pinned", NOW))
        m.record(Note("dud", Disposition.TRIED_FAILED, "no output", NOW))
        b = brief(m, LIMITS)
        self.assertEqual(b["already_rejected"], ["dead"])
        self.assertEqual(b["already_running"], ["live"])
        self.assertEqual(b["tried_and_failed"], ["dud"])

    def test_constraints_are_stated_as_facts_not_prose(self):
        b = brief(Memory(), LIMITS)
        self.assertTrue(b["no_capital"])
        self.assertTrue(b["no_private_key_on_device"])
        self.assertTrue(b["no_kyc"])
        self.assertEqual(b["hardware_classes"], [OPI, ESP])


if __name__ == "__main__":
    unittest.main()


class TestCoinAgeWindow(unittest.TestCase):
    """Both ends of the window are real constraints, and they fail differently."""

    def test_a_day_old_chain_is_set_aside_not_buried(self):
        v = screen(cand(age_weeks=0.2), LIMITS)
        self.assertFalse(v.accepted)
        self.assertFalse(v.hard, "next month it will be exactly the right age")
        self.assertEqual(v.rule, "scout:too-new")

    def test_an_established_chain_is_refused_permanently(self):
        v = screen(cand(age_weeks=200), LIMITS)
        self.assertFalse(v.accepted)
        self.assertTrue(v.hard, "difficulty does not come back down")
        self.assertEqual(v.rule, "scout:too-old")

    def test_the_window_passes(self):
        for weeks in (1, 4, 8):
            with self.subTest(weeks=weeks):
                self.assertTrue(screen(cand(age_weeks=weeks), LIMITS).accepted)

    def test_unknown_age_is_not_held_against_it(self):
        """The researcher failing to establish an age is a gap in the report,
        not evidence about the chain."""
        self.assertTrue(screen(cand(age_weeks=None), LIMITS).accepted)

    def test_the_window_travels_in_the_brief(self):
        self.assertEqual(brief(Memory(), LIMITS)["age_window_weeks"], [1, 8])
