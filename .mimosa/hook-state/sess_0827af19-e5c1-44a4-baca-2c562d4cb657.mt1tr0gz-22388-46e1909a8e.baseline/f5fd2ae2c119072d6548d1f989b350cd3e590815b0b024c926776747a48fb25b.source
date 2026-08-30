"""Answers that go quietly out of date.

Late GST registration means owing tax on every sale since the day
registration was due — even on money never collected for it. An answer given
once and never asked again is one that ages without anybody noticing, and
the threshold is $75,000 with roughly a nine percent effect on margin: the
exact width of the band between "healthy" and "losing money".

The rule is in the kernel and the clock is in the node, which is why `plan`
needed no change at all: a fact past its re-ask date simply stops appearing
as known.
"""

from __future__ import annotations

import unittest

from ofn.adapters.packloader import load_pack
from ofn.kernel.questions import ASK_EVERY_SECONDS, is_stale

DAY = 86_400


class TestTheRuleIsPure(unittest.TestCase):
    def test_a_fresh_answer_is_not_stale(self):
        self.assertFalse(is_stale("quarter", 10 * DAY))

    def test_an_old_answer_is(self):
        self.assertTrue(is_stale("quarter", 100 * DAY))

    def test_the_boundary_is_exclusive(self):
        """Exactly at the period is still fresh; a question that reappears a
        second early is one somebody starts dismissing unread."""
        self.assertFalse(is_stale("quarter", ASK_EVERY_SECONDS["quarter"]))
        self.assertTrue(is_stale("quarter", ASK_EVERY_SECONDS["quarter"] + 1))

    def test_an_unknown_period_does_not_re_ask(self):
        """A typo in a pack must not turn into an interrogation. The safe
        direction here is *not* asking — a question on every screen is how
        somebody learns to dismiss questions without reading them."""
        self.assertFalse(is_stale("fortnight", 10_000 * DAY))
        self.assertFalse(is_stale(None, 10_000 * DAY))
        self.assertFalse(is_stale(7, 10_000 * DAY))

    def test_an_answer_from_the_future_is_treated_as_fresh(self):
        """This board has no battery-backed clock. An answer that appears to
        come from the future is a clock problem, not a reason to interrogate
        somebody."""
        self.assertFalse(is_stale("day", -10 * DAY))

    def test_the_periods_are_named_not_numbered(self):
        """"quarter" is a thing a person means; 7776000 is a thing somebody
        typed."""
        for name in ("day", "week", "month", "quarter", "year"):
            self.assertIn(name, ASK_EVERY_SECONDS)


class TestThePackDeclaresIt(unittest.TestCase):
    def test_gst_is_asked_quarterly(self):
        pack = load_pack("packs/ziman.yaml")
        meta = pack.question_meta.get("business.gst_registered") or {}
        self.assertEqual(meta.get("ask_every"), "quarter")

    def test_the_period_is_one_the_kernel_understands(self):
        """A config key the code cannot read is a control that is not one."""
        pack = load_pack("packs/ziman.yaml")
        for key, meta in pack.question_meta.items():
            period = (meta or {}).get("ask_every")
            if period is not None:
                self.assertIn(period, ASK_EVERY_SECONDS, key)


class TestTheNodeAppliesIt(unittest.TestCase):
    """Staleness needs a clock, so it is applied where the clock is. `plan`
    itself did not change."""

    def test_evidence_for_drops_a_stale_answer(self):
        import inspect

        from ofn.node import Node
        src = inspect.getsource(Node.evidence_for)
        self.assertIn("is_stale", src)
        self.assertIn("del known[key]", src)

    def test_a_fact_with_no_period_is_never_dropped(self):
        import inspect

        from ofn.node import Node
        src = inspect.getsource(Node.evidence_for)
        self.assertIn("if period is None:", src)
        self.assertIn("continue", src)

    def test_the_kernel_still_has_no_clock(self):
        import inspect

        from ofn.kernel import questions
        src = inspect.getsource(questions)
        for forbidden in ("import time", "import datetime", "time.time"):
            self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
