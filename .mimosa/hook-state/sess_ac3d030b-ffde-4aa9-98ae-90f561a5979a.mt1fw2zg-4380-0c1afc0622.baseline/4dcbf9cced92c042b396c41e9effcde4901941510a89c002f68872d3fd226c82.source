"""Draft messages — text for a person to send, and nothing that can send it.

Two absences are the design, and both are asserted here rather than intended:

    nothing is stored        no table to drain, no row to mark pending
    no model is involved     the fact is arithmetic; only the prose is not

D-13 deleted automatic messaging rather than deferring it. A deferred feature
leaves a shape behind — a queue, a status column, a flag — and shapes get
filled in. This one leaves none.
"""

from __future__ import annotations

import unittest

from ofn.kernel.audience import DAY, Subscriber
from ofn.kernel.outreach import Draft, Moment, drafts_for, moment_for, summary

NOW = 1_785_000_000


def sub(sid="s1", *, joined_days_ago=2, contacted_days_ago=None,
        bought=False, status="active") -> Subscriber:
    first = NOW - joined_days_ago * DAY
    return Subscriber(
        sub_id=sid, first_seen_at=first, channel_source="x", status=status,
        last_contact_at=(None if contacted_days_ago is None
                         else NOW - contacted_days_ago * DAY),
        first_purchase_at=(first + DAY) if bought else None)


class TestWhySomebodyIsOnTheList(unittest.TestCase):
    def test_never_greeted_outranks_everything(self):
        """Somebody nobody has ever spoken to is both more urgent and easier
        to fix. Checking "quiet" first would label every new arrival as quiet
        and bury them."""
        self.assertIs(moment_for(sub(joined_days_ago=40), now_epoch_s=NOW),
                      Moment.NEVER_GREETED)

    def test_inside_the_first_week(self):
        self.assertIs(
            moment_for(sub(joined_days_ago=3, contacted_days_ago=3),
                       now_epoch_s=NOW),
            Moment.INSIDE_FIRST_WEEK)

    def test_gone_quiet_after_a_fortnight(self):
        self.assertIs(
            moment_for(sub(joined_days_ago=60, contacted_days_ago=20),
                       now_epoch_s=NOW),
            Moment.GONE_QUIET)

    def test_past_the_window_and_never_bought(self):
        self.assertIs(
            moment_for(sub(joined_days_ago=30, contacted_days_ago=2),
                       now_epoch_s=NOW),
            Moment.NO_PURCHASE_YET)

    def test_somebody_recently_spoken_to_who_has_bought_is_left_alone(self):
        self.assertIsNone(
            moment_for(sub(joined_days_ago=30, contacted_days_ago=1,
                           bought=True), now_epoch_s=NOW))

    def test_a_blocked_person_is_never_on_it(self):
        self.assertIsNone(
            moment_for(sub(status="blocked"), now_epoch_s=NOW))


class TestTheOrderIsTheOrderToWorkThrough(unittest.TestCase):
    def test_never_greeted_comes_first(self):
        out = drafts_for([sub("quiet", joined_days_ago=60,
                              contacted_days_ago=30),
                          sub("new", joined_days_ago=1)], now_epoch_s=NOW)
        self.assertEqual([d.sub_id for d in out], ["new", "quiet"])

    def test_within_a_reason_the_longest_wait_is_first(self):
        out = drafts_for([sub("a", joined_days_ago=2),
                          sub("b", joined_days_ago=9)], now_epoch_s=NOW)
        self.assertEqual([d.sub_id for d in out], ["b", "a"])

    def test_the_list_is_capped(self):
        """A list of two hundred is a list nobody starts, and the first ten
        are where nearly all of the value is."""
        many = [sub(f"s{i}", joined_days_ago=3) for i in range(50)]
        self.assertEqual(len(drafts_for(many, now_epoch_s=NOW)), 10)

    def test_a_zero_limit_is_refused(self):
        with self.assertRaises(ValueError):
            drafts_for([], now_epoch_s=NOW, limit=0)


class TestTheTextIsHers(unittest.TestCase):
    def test_every_reason_has_words(self):
        for moment in Moment:
            found = [d for d in drafts_for(
                [sub("s1", joined_days_ago=1)], now_epoch_s=NOW)]
            self.assertTrue(all(d.text.strip() for d in found))

    def test_nothing_in_it_sounds_like_a_tool(self):
        """A template that sounds like the tool is one she rewrites every
        time, which costs more than writing it herself."""
        out = drafts_for([sub(joined_days_ago=1)], now_epoch_s=NOW)
        for word in ("سیستم", "خودکار", "پیام خودکار", "ربات"):
            self.assertNotIn(word, out[0].text)

    def test_the_summary_gives_a_reason_not_a_chore(self):
        """"you have 12 drafts" is a chore; "12 people are inside their first
        week and nobody has written" is a reason to open it."""
        out = drafts_for([sub(f"s{i}", joined_days_ago=1) for i in range(12)],
                         now_epoch_s=NOW, limit=12)
        text = summary(out)
        self.assertIn("12", text)
        self.assertIn("هیچ پیامی نگرفته", text)

    def test_an_empty_list_says_so_plainly(self):
        self.assertIn("کسی منتظر", summary(()))


class TestNothingCanSendThese(unittest.TestCase):
    """The absences, asserted.

    Checked with `ast` rather than by searching the text. The first version
    searched for the word "send" and failed on a docstring that says nothing
    here sends — which is the same mistake made three times tonight: matching
    prose and calling it code. What matters is what the module imports and
    calls, and that is a question the parser answers.
    """

    def module(self):
        import ast

        import ofn.kernel.outreach as mod
        return ast.parse(open(mod.__file__, encoding="utf-8").read())

    def imports(self):
        import ast
        names = set()
        for node in ast.walk(self.module()):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        return names

    def called_names(self):
        import ast
        out = set()
        for node in ast.walk(self.module()):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name):
                    out.add(fn.id)
                elif isinstance(fn, ast.Attribute):
                    out.add(fn.attr)
        return out

    def test_there_is_no_store(self):
        """No table to drain, no row to mark pending, no queue a future flag
        could point at."""
        self.assertEqual(self.imports() & {"sqlite3", "ofn"}, set())
        self.assertEqual(
            self.called_names() & {"execute", "commit", "insert"}, set())

    def test_nothing_here_sends(self):
        self.assertEqual(
            self.imports() & {"urllib", "http", "socket", "requests"}, set())
        self.assertEqual(
            self.called_names() & {"urlopen", "post", "send", "request"}, set())

    def test_no_model_is_involved(self):
        """The valuable part is knowing twelve people are on day five. That
        is arithmetic, free, and available the day the first subscriber
        arrives."""
        from ofn.kernel import outreach
        for name in dir(outreach):
            self.assertNotIn("brain", name.lower())
            self.assertNotIn("rung", name.lower())
            self.assertNotIn("prompt", name.lower())

    def test_it_imports_only_the_kernel_beside_it(self):
        """One dependency, and it is the arithmetic."""
        self.assertEqual(self.imports() - {"__future__", "enum", "dataclasses",
                                           "typing"}, {"audience"})

    def test_a_draft_is_a_frozen_value_not_a_record(self):
        d = drafts_for([sub(joined_days_ago=1)], now_epoch_s=NOW)[0]
        self.assertIsInstance(d, Draft)
        self.assertTrue(d.is_editable_by_a_person)
        with self.assertRaises(Exception):
            d.text = "changed"          # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
