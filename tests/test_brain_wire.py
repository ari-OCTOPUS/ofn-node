"""Phase A of the brain wiring: the owner's surface, and nothing else.

The router, the rungs and the worker have existed since the beginning and
nothing ever put a job in the queue — the worker looped over an empty one.
The panel was not "partly wired to the brain"; it had no path to it at all.

Two things are asserted here beyond "it works":

    the first question asked has a known answer
    the partner surfaces are still disconnected

The second is the one worth guarding. The extraction layer that stops a
pixel reaching a model does not exist yet, and the window in which the pipe
is connected and the guard is not is exactly the window a bug needs.
"""

from __future__ import annotations

import unittest

from ofn.kernel.callbudget import DEFAULT_CAPS, CallBudget, day_index
from ofn.kernel.errors import FailClosedError
from ofn.kernel.probe import (
    QUESTIONS, Grade, ProbeResult, summarise,
)
from ofn.kernel.routing import Rung

NOW = 1_785_000_000
DAY = 86_400


class TestTheFirstQuestionHasAKnownAnswer(unittest.TestCase):
    """Cryptography does not believe an implementation because it looks
    right; it believes one that reproduces published vectors. Here the
    vectors come from the kernel, whose answers are already under test."""

    def test_every_question_carries_its_own_answer(self):
        for q in QUESTIONS:
            with self.subTest(key=q.key):
                self.assertTrue(q.expected)
                self.assertIs(q.grade(q.expected), Grade.AGREED)

    def test_a_correct_answer_wrapped_in_prose_still_agrees(self):
        """Grading a right answer as wrong because it came in a sentence
        blames the model for the grader's rigidity."""
        q = QUESTIONS[0]
        self.assertIs(q.grade("جواب ۴۲۵ می‌شود."), Grade.AGREED)

    def test_persian_digits_are_read(self):
        """A model answering a Persian prompt may answer in Persian digits.
        Reading that as "no number found" grades a correct answer as
        unreadable."""
        self.assertIs(QUESTIONS[0].grade("۴۲۵"), Grade.AGREED)

    def test_a_wrong_answer_disagrees(self):
        self.assertIs(QUESTIONS[0].grade("426"), Grade.DISAGREED)

    def test_an_answer_with_no_number_is_unreadable_not_wrong(self):
        """Three outcomes, not two: "answered something ungradeable" and
        "answered incorrectly" need different fixes."""
        self.assertIs(QUESTIONS[0].grade("نمی‌دانم"), Grade.UNREADABLE)

    def test_silence_is_refusal(self):
        self.assertIs(QUESTIONS[0].grade(""), Grade.REFUSED)
        self.assertIs(QUESTIONS[0].grade("   "), Grade.REFUSED)

    def test_the_questions_are_trivial_on_purpose(self):
        """A hard question would confound "the wiring is broken" with "the
        model is not good enough", and those need different fixes."""
        for q in QUESTIONS:
            self.assertLess(len(q.prompt), 200, q.key)


class TestTheSummaryDoesNotOverclaim(unittest.TestCase):
    def result(self, grade, model="fugu", requested="fugu"):
        return ProbeResult("k", grade, model, requested, "")

    def test_all_agreed_is_usable(self):
        out = summarise([self.result(Grade.AGREED) for _ in range(3)])
        self.assertTrue(out["usable"])

    def test_one_disagreement_is_not_usable(self):
        """A partial pass reported as a pass is exactly the self-confirming
        claim this file exists to avoid."""
        out = summarise([self.result(Grade.AGREED),
                         self.result(Grade.DISAGREED)])
        self.assertFalse(out["usable"])

    def test_nothing_asked_is_not_usable(self):
        self.assertFalse(summarise([])["usable"])

    def test_a_substitution_is_named(self):
        out = summarise([self.result(Grade.AGREED, model="glm-4-plus")])
        self.assertEqual(out["substituted"], ["k"])

    def test_a_silent_provider_is_not_called_a_substitution(self):
        """Unknown is not agreement, and it is not disagreement either."""
        r = ProbeResult("k", Grade.AGREED, "", "fugu", "")
        self.assertIsNone(r.model_substituted)
        self.assertEqual(summarise([r])["substituted"], [])


class TestCallBudgetIsPerRung(unittest.TestCase):
    """One number covering both rungs is the "get the unit right" mistake: a
    thousand cheap calls and a thousand expensive ones are not the same
    event, and a shared counter lets the cheap rung exhaust the budget the
    expensive one needed."""

    def test_the_rungs_are_counted_separately(self):
        b = CallBudget(caps={Rung.REMOTE: 2, Rung.REMOTE_DEEP: 1})
        b.record(Rung.REMOTE, NOW)
        b.record(Rung.REMOTE, NOW)
        self.assertFalse(b.allows(Rung.REMOTE, NOW))
        self.assertTrue(b.allows(Rung.REMOTE_DEEP, NOW))

    def test_a_rung_with_no_declared_cap_is_refused(self):
        """The one default that must never be the permissive one."""
        b = CallBudget(caps={Rung.REMOTE: 1})
        with self.assertRaises(FailClosedError):
            b.allows(Rung.REMOTE_DEEP, NOW)
        with self.assertRaises(FailClosedError):
            b.record(Rung.REMOTE_DEEP, NOW)

    def test_zero_means_uncapped_and_only_free_rungs_have_it(self):
        b = CallBudget()
        self.assertIsNone(b.remaining(Rung.RULES, NOW))
        self.assertIsNotNone(b.remaining(Rung.REMOTE, NOW))

    def test_the_ceiling_is_exclusive(self):
        """"Ten a day" that permits an eleventh is a limit somebody has to
        read the code to understand."""
        b = CallBudget(caps={Rung.REMOTE: 1})
        self.assertTrue(b.allows(Rung.REMOTE, NOW))
        b.record(Rung.REMOTE, NOW)
        self.assertFalse(b.allows(Rung.REMOTE, NOW))

    def test_a_failed_call_still_counts(self):
        """Counting only successes turns a failing loop into an uncounted
        one — the loop most worth stopping."""
        b = CallBudget(caps={Rung.REMOTE: 2})
        b.record(Rung.REMOTE, NOW)      # the caller does not say if it worked
        self.assertEqual(b.spent(Rung.REMOTE, NOW), 1)

    def test_a_new_day_starts_again(self):
        b = CallBudget(caps={Rung.REMOTE: 1})
        b.record(Rung.REMOTE, NOW)
        self.assertFalse(b.allows(Rung.REMOTE, NOW))
        self.assertTrue(b.allows(Rung.REMOTE, NOW + DAY))

    def test_old_days_do_not_accumulate_for_ever(self):
        b = CallBudget(caps={Rung.REMOTE: 100})
        for d in range(30):
            b.record(Rung.REMOTE, NOW + d * DAY)
        self.assertLessEqual(len(b._counts), 4)

    def test_a_negative_or_bool_cap_is_refused(self):
        for bad in (-1, True, 1.5, "5"):
            with self.assertRaises(FailClosedError):
                CallBudget(caps={Rung.REMOTE: bad})

    def test_the_expensive_rung_has_the_tighter_ceiling(self):
        self.assertLess(DEFAULT_CAPS[Rung.REMOTE_DEEP],
                        DEFAULT_CAPS[Rung.REMOTE])

    def test_day_index_moves_at_the_boundary(self):
        self.assertEqual(day_index(NOW) + 1, day_index(NOW + DAY))


class TestThePartnerSurfacesAreStillDisconnected(unittest.TestCase):
    """Phase A is the owner only. The extraction layer that stops a pixel
    reaching a model does not exist yet, and "we will add the guard later"
    is the sentence guards do not get added after."""

    def test_no_partner_route_reaches_the_brain(self):
        import inspect

        from ofn.adapters import http_api
        src = inspect.getsource(http_api.ApiApp._partner_route)
        for word in ("brain", "worker", "ask", "probe"):
            self.assertNotIn(word, src.lower(),
                             f"the partner surface mentions {word}")

    def test_the_brain_routes_are_owner_only(self):
        import inspect

        from ofn.adapters import http_api
        src = inspect.getsource(http_api.ApiApp._owner_route)
        self.assertIn("/api/v1/owner/brain", src)
        self.assertIn("/api/v1/owner/ask", src)

    def test_the_studio_surface_does_not_call_a_model(self):
        import inspect

        from ofn.node import Node
        for name in ("studio_board", "create_draft", "attach_media",
                     "publish_draft", "record_felt"):
            src = inspect.getsource(getattr(Node, name))
            self.assertNotIn("worker", src, f"{name} reaches the worker")


if __name__ == "__main__":
    unittest.main()
