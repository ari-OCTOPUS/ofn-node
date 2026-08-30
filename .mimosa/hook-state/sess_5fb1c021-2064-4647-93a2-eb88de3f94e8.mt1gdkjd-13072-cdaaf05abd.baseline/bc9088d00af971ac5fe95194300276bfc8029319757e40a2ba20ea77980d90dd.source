"""Contract tests for the marketing scout.

The scout is the weekly trend-research gate. Its rules are the structural
defence against the two failure modes that eat agent-driven research:
looping on the same rejected ideas, and presenting predictions as
observations. Every test pins one rule that must hold forever.
"""

import unittest

from ofn.kernel.marketing_scout import (
    Candidate, Memory, Note, TrendObservation, Disposition,
    SOFT_REJECT_COOLDOWN_S, screen, triage, research_focus, brief,
)


def _obs(term="t", **kw):
    base = dict(source_id="s", term=term, observed_at=1000,
                count_value=1.0)
    base.update(kw)
    return TrendObservation(**base)


def _cand(key="k", **kw):
    base = dict(key=key, title="T", style_id="educational",
                framing="beauty", observations=(_obs(),), confidence=0.8)
    base.update(kw)
    return Candidate(**base)


class TestObservationContract(unittest.TestCase):
    def test_observation_without_observed_at_refused_at_construction(self):
        with self.assertRaises(Exception):
            TrendObservation(source_id="s", term="t", observed_at=0,
                             count_value=1.0)

    def test_observation_without_count_or_rank_refused(self):
        with self.assertRaises(Exception):
            TrendObservation(source_id="s", term="t", observed_at=1000)


class TestScreen(unittest.TestCase):
    def test_no_observations_refused(self):
        v = screen(_cand(observations=()))
        self.assertFalse(v.accepted)
        self.assertEqual(v.rule, "scout:no-evidence")

    def test_low_confidence_refused(self):
        v = screen(_cand(confidence=0.2))
        self.assertFalse(v.accepted)
        self.assertEqual(v.rule, "scout:low-confidence")

    def test_good_candidate_accepted(self):
        v = screen(_cand())
        self.assertTrue(v.accepted)
        self.assertEqual(v.rule, "scout:ok")


class TestMemoryRatchet(unittest.TestCase):
    def test_hard_rejection_cannot_be_softened(self):
        mem = Memory()
        mem.record(Note("k", Disposition.REJECTED_HARD, "structural", 100))
        # A later 'accepted' note must not overwrite a hard rejection.
        mem.record(Note("k", Disposition.ACCEPTED, "now ok", 200))
        self.assertEqual(mem.disposition("k"), Disposition.REJECTED_HARD)

    def test_soft_rejection_can_be_replaced(self):
        mem = Memory()
        mem.record(Note("k", Disposition.REJECTED_SOFT, "circumstantial", 100))
        mem.record(Note("k", Disposition.PROPOSED, "re-proposed", 200))
        self.assertEqual(mem.disposition("k"), Disposition.PROPOSED)


class TestTriage(unittest.TestCase):
    def test_already_final_is_refused_not_dropped(self):
        mem = Memory()
        mem.record(Note("k", Disposition.REJECTED_HARD, "banned", 100))
        fresh, refused = triage([_cand()], mem, now_epoch_s=1000)
        self.assertEqual(len(fresh), 0)
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0][1].rule, "scout:already-final")

    def test_soft_rejected_within_cooldown_is_refused(self):
        mem = Memory()
        mem.record(Note("k", Disposition.REJECTED_SOFT, "beta", 1000))
        fresh, refused = triage([_cand()], mem, now_epoch_s=1000 + 10)
        self.assertEqual(len(fresh), 0)
        self.assertEqual(refused[0][1].rule, "scout:cooling-off")

    def test_soft_rejected_after_cooldown_returns_to_fresh(self):
        mem = Memory()
        mem.record(Note("k", Disposition.REJECTED_SOFT, "beta", 1000))
        fresh, refused = triage(
            [_cand()], mem,
            now_epoch_s=1000 + SOFT_REJECT_COOLDOWN_S + 1)
        self.assertEqual(len(fresh), 1)
        self.assertEqual(len(refused), 0)

    def test_proposed_is_refused_as_duplicate(self):
        mem = Memory()
        mem.record(Note("k", Disposition.PROPOSED, "shown", 1000))
        fresh, refused = triage([_cand()], mem, now_epoch_s=1000)
        self.assertEqual(len(fresh), 0)
        self.assertEqual(refused[0][1].rule, "scout:duplicate")

    def test_low_confidence_goes_to_refused_not_fresh(self):
        mem = Memory()
        fresh, refused = triage([_cand(confidence=0.1)], mem,
                                now_epoch_s=1000)
        self.assertEqual(len(fresh), 0)
        self.assertEqual(refused[0][1].rule, "scout:low-confidence")


class TestResearchFocus(unittest.TestCase):
    def test_untried_style_becomes_a_question(self):
        mem = Memory()
        qs = research_focus(mem, last_week_style=None,
                            tried_styles={"a": 0, "b": 3}, max_questions=3)
        self.assertTrue(any("'a'" in q for q in qs))

    def test_open_ended_question_includes_no_predict_instruction(self):
        mem = Memory()
        qs = research_focus(mem, last_week_style=None,
                            tried_styles={}, max_questions=3)
        joined = " ".join(qs)
        self.assertIn("do not predict", joined.lower())


class TestBrief(unittest.TestCase):
    def test_brief_lists_rejected_keys(self):
        mem = Memory()
        mem.record(Note("bad", Disposition.REJECTED_HARD, "x", 100))
        b = brief(mem)
        self.assertIn("bad", b["already_rejected"])

    def test_brief_states_no_predictions_rule(self):
        b = brief(Memory())
        self.assertIn("no predictions", b["rule"].lower())


if __name__ == "__main__":
    unittest.main()
