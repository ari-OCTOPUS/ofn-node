"""Going back.

Two flows in these shells ask one thing per screen, and both of them used to
run one way only.

The piece form had seven steps and a button that read "برگرد" on some of them
and "ندارم، رد کن" on the others — the same button, two opposite jobs. On the
three optional steps it moved *forward*. So a partner who mistyped the
materials cost on step two had no way back to it: the only exit was to
abandon the piece and start again.

The kernel's question queue had the same shape. "بعداً" advanced past a
question and nothing returned to it.

Neither was caught by a test, and neither could have been: the suite asserted
that each screen said the right words, which is a question about *a* screen.
Being stuck is a property of the path between screens, and nothing here ever
walked one. It was found by watching somebody use it.

These tests read the shells as text. That is weak — they cannot prove the
buttons work — but it is strong enough to catch the specific thing that went
wrong, which was a control that did not exist at all.
"""

from __future__ import annotations

import os
import re
import unittest

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web")
PARTNER_SHELLS = ("ziman.html", "lead.html", "studio.html")


def read(name: str) -> str:
    return open(os.path.join(WEB, name), encoding="utf-8").read()


def js_of(name: str) -> str:
    """The script, with comments removed.

    Comments here legitimately describe the trap being closed, and matching
    them instead of the code would let this whole file pass on prose.
    """
    src = read(name)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return src


class TestTheQuestionQueueCanGoBack(unittest.TestCase):
    def test_every_partner_shell_can_return_to_a_deferred_question(self):
        for name in PARTNER_SHELLS:
            with self.subTest(shell=name):
                js = js_of(name)
                self.assertIn("at -= 1", js,
                              f"{name}: nothing walks the queue backwards")

    def test_going_back_is_offered_only_when_there_is_something_behind(self):
        """On the first question a back control would be a button that does
        nothing, which teaches that buttons sometimes do nothing."""
        for name in PARTNER_SHELLS:
            with self.subTest(shell=name):
                self.assertRegex(js_of(name), r"if \(at > 0\)")

    def test_deferring_still_moves_forward(self):
        for name in PARTNER_SHELLS:
            with self.subTest(shell=name):
                self.assertIn("at += 1", js_of(name))


class TestThePieceFormCanGoBack(unittest.TestCase):
    """Ziman only — it is the one shell with a multi-step form."""

    def setUp(self):
        self.js = js_of("ziman.html")

    def test_back_and_skip_are_different_controls(self):
        """The bug was one button with two meanings. Whatever else changes,
        the label that skips and the label that returns must not be the same
        control."""
        self.assertIn("'ندارم، رد کن'", self.js)
        self.assertIn("'قبلی'", self.js)

    def test_back_always_goes_back(self):
        """It used to go forward on optional steps."""
        back = re.search(
            r"const back = el\('button', 'back'.*?\n  bottom\.append\(back\);",
            self.js, re.S)
        self.assertIsNotNone(back, "no back control in the piece form")
        body = back.group(0)
        self.assertIn("step--", body)
        self.assertNotIn("step++", body,
                         "the back control still moves forward on some step")

    def test_skip_is_the_only_thing_that_skips(self):
        skip = re.search(r"const skip = el\('button'.*?\n  \}", self.js, re.S)
        self.assertIsNotNone(skip)
        self.assertIn("step++", skip.group(0))

    def test_the_furthest_step_reached_is_tracked_separately(self):
        """Going back must not un-answer what is already answered — otherwise
        the fix costs more than the bug."""
        self.assertIn("reached", self.js)
        self.assertRegex(self.js, r"let step = 0, reached = 0")

    def test_a_reached_step_can_be_jumped_to(self):
        self.assertRegex(self.js, r"if \(i <= reached\)")

    def test_an_unreached_step_cannot(self):
        self.assertIn("d.disabled = true", self.js)

    def test_the_progress_row_is_made_of_buttons(self):
        """It was `<i>` — decoration. A tappable target has to be an element
        that can take focus and a keyboard."""
        self.assertIn("el('button', null, '')", self.js)

    def test_every_step_reset_also_resets_the_furthest_reached(self):
        """A stale `reached` would leave the next piece's later steps open
        before they have been answered."""
        for m in re.finditer(r"step = 0", self.js):
            window = self.js[m.start():m.start() + 120]
            self.assertIn("reached = 0", window,
                          f"step reset without resetting reached: {window[:60]}")

    def test_the_edit_entry_point_finds_its_step_by_name(self):
        """It was `step = 5`, a count into a list that has since changed
        length twice. Counting into a list of questions is a bug with a
        delay on it."""
        self.assertIn("STEPS.findIndex(q => q.key === 'price_primary_aud')",
                      self.js)
        self.assertNotRegex(self.js, r"\n  step = \d+;")


class TestTheDraftRemembersWhereSheWas(unittest.TestCase):
    def test_the_saved_draft_carries_the_furthest_step(self):
        js = js_of("ziman.html")
        self.assertRegex(js, r"JSON\.stringify\(\{ step, reached, draft \}\)")

    def test_an_older_draft_without_it_still_opens(self):
        """Drafts written before today exist on a real phone right now."""
        js = js_of("ziman.html")
        self.assertIn("Math.max(saved.reached || 0, step)", js)


if __name__ == "__main__":
    unittest.main()
