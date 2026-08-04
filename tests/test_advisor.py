"""ST-4 phase B — the extraction layer, and what it structurally cannot do.

The promise is that no pixel leaves this board. A promise kept by everybody
remembering is not kept, so these tests are about the *type* refusing rather
than the code declining: there is nowhere in `Evidence` to put an image, and
a bug in a caller cannot invent a field.

The second half is provenance. A suggestion without a source cannot be
argued with, and a suggestion that cannot be rejected is not advice — so a
`Finding` with no evidence is refused at construction.
"""

from __future__ import annotations

import unittest

from ofn.adapters.advisor import (
    MIN_SAMPLE, Advisor, AdvisorRequest, render_for_screen,
)
from ofn.kernel.advisor import (
    Disposition, Evidence, Finding, Memory, Provenance, extract,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.routing import Rung

RAW = {"posts_counted": 38, "window_days": 90, "median_caption_chars": 120,
       "retention_pct": 42.5, "single_subject_share": 0.61}


def request() -> AdvisorRequest:
    return Advisor().prepare(RAW, sample=38, window_days=90)


class TestThereIsNowhereToPutAnImage(unittest.TestCase):
    def test_evidence_holds_only_numbers(self):
        for bad in (b"\x89PNG", "data:image/jpeg;base64,AAA", [1], {"a": 1},
                    None, True):
            with self.subTest(value=type(bad).__name__):
                with self.assertRaises(FailClosedError):
                    Evidence(name="x", value=bad)      # type: ignore[arg-type]

    def test_a_label_cannot_be_long_enough_to_hide_one(self):
        """A field that could hold a base64 image makes every other rule
        here decorative."""
        with self.assertRaises(FailClosedError):
            Evidence(name="x", value=1, label="A" * 400)

    def test_a_label_must_be_a_label_not_a_sentence(self):
        """A caption is content, and content is what this file keeps in."""
        with self.assertRaises(FailClosedError):
            Evidence(name="x", value=1, label="سه فریم از نور بعدازظهر")

    def test_extraction_is_whitelisted_by_name(self):
        """Blacklisting needs somebody to have thought of every kind of
        thing that must not travel."""
        out = extract({"posts_counted": 5, "secret_note": 9},
                      allowed=("posts_counted",))
        self.assertEqual([e.name for e in out], ["posts_counted"])

    def test_a_non_numeric_measurement_is_dropped_not_fatal(self):
        """One odd row must not stop a whole weekly summary."""
        out = extract({"posts_counted": 5, "caption": "hello"},
                      allowed=("posts_counted", "caption"))
        self.assertEqual([e.name for e in out], ["posts_counted"])

    def test_raw_input_containing_bytes_is_refused_outright(self):
        with self.assertRaises(FailClosedError):
            Advisor().prepare({**RAW, "thumb": b"\x89PNG"},
                              sample=38, window_days=90)

    def test_a_data_url_nested_anywhere_is_refused(self):
        with self.assertRaises(FailClosedError):
            Advisor().prepare({**RAW, "x": {"y": ["data:image/png;base64,AA"]}},
                              sample=38, window_days=90)

    def test_the_prompt_has_no_slot_for_free_text(self):
        """A caller cannot append a sentence: there is nowhere to append it.

        Asserted as the shape of every data line, not by looking for a word.
        The first version searched for "caption" and failed on the measure
        named `median_caption_chars` — which is a count, not a caption. A
        test that matches substrings of legitimate names finds words, not
        leaks.
        """
        import re
        rendered = request().render()
        names = {e.name for e in request().evidence}
        data_lines = [ln for ln in rendered.splitlines()
                      if re.match(r"^[a-z0-9_]+=", ln)]
        self.assertEqual(len(data_lines), len(names))
        for line in data_lines:
            name, _, value = line.partition("=")
            self.assertIn(name, names)
            # Numbers only. Anything else here would be content.
            self.assertRegex(value.strip(), r"^-?[0-9.]+$")

    def test_the_advisor_does_not_import_the_media_layer(self):
        import ofn.adapters.advisor as mod
        src = open(mod.__file__, encoding="utf-8").read()
        for forbidden in ("media", "photos", "MediaStore", "photos_root"):
            self.assertNotIn(f"import {forbidden}", src)
        self.assertNotIn("from ..kernel.photos", src)


class TestEverySuggestionCarriesItsSource(unittest.TestCase):
    def test_a_finding_without_evidence_is_refused(self):
        """A claim with nothing under it cannot be argued with, and a
        suggestion that cannot be rejected is not advice."""
        with self.assertRaises(FailClosedError):
            Finding(key="k", claim="این کار را بکن", evidence=(),
                    provenance=Provenance(38, 90))

    def test_provenance_needs_both_numbers(self):
        """"Based on your data" is a sentence that sounds like a source."""
        for sample, window in ((0, 90), (38, 0), (-1, 90), (38, -1)):
            with self.subTest(sample=sample, window=window):
                with self.assertRaises(FailClosedError):
                    Provenance(sample, window)

    def test_the_source_is_rendered_beside_the_claim(self):
        f = Finding(key="k", claim="جمله", evidence=request().evidence,
                    provenance=Provenance(38, 90))
        out = render_for_screen(f)
        self.assertIn("38", out["source"])
        self.assertIn("90", out["source"])
        self.assertEqual(out["claim"], "جمله")

    def test_claim_and_source_come_back_together(self):
        """A template that can print one without the other will eventually
        be written."""
        out = render_for_screen(
            Finding(key="k", claim="ج", evidence=request().evidence,
                    provenance=Provenance(38, 90)))
        self.assertIn("source", out)
        self.assertIn("claim", out)

    def test_too_small_a_sample_says_nothing(self):
        with self.assertRaises(FailClosedError):
            Advisor().prepare(RAW, sample=MIN_SAMPLE - 1, window_days=90)


class TestDecliningIsNotFailing(unittest.TestCase):
    def test_not_enough_returns_nothing(self):
        a = Advisor()
        self.assertIsNone(a.interpret(request(), "کافی نیست", key="k"))

    def test_silence_returns_nothing(self):
        a = Advisor()
        self.assertIsNone(a.interpret(request(), "   ", key="k"))

    def test_a_real_answer_becomes_a_finding_with_the_evidence_attached(self):
        f = Advisor().interpret(request(), "تک‌سوژه بهتر نگه می‌دارد.", key="k")
        self.assertIsNotNone(f)
        self.assertTrue(f.evidence)
        self.assertEqual(f.provenance.sample, 38)

    def test_only_the_first_line_is_kept(self):
        """A model writing three paragraphs has stopped answering the
        question that was asked."""
        f = Advisor().interpret(request(), "خط اول\nخط دوم\nخط سوم", key="k")
        self.assertEqual(f.claim, "خط اول")


class TestTheRatchet(unittest.TestCase):
    def finding(self, key="k"):
        return Finding(key=key, claim="ج", evidence=request().evidence,
                       provenance=Provenance(38, 90))

    def test_a_hard_rejection_never_comes_back(self):
        """Without this the advisor offers the same three suggestions every
        week and she stops opening it after the third."""
        a = Advisor()
        a.record("k", Disposition.REJECTED_HARD)
        self.assertEqual(a.offer([self.finding()]), ())

    def test_a_soft_rejection_may_come_back(self):
        a = Advisor()
        a.record("k", Disposition.REJECTED_SOFT)
        self.assertEqual(len(a.offer([self.finding()])), 1)

    def test_opinions_do_not_soften(self):
        m = Memory()
        m.remember("k", Disposition.REJECTED_HARD)
        m.remember("k", Disposition.ACCEPTED)
        self.assertIs(m.disposition("k"), Disposition.REJECTED_HARD)

    def test_offering_is_remembered(self):
        a = Advisor()
        a.offer([self.finding()])
        self.assertIs(a.memory.disposition("k"), Disposition.OFFERED)


class TestNoImplicitEscalation(unittest.TestCase):
    def test_the_rung_is_always_the_standard_one(self):
        """Silence means do not spend. A rung reached because a cheaper one
        was merely brief is a rung reached constantly."""
        self.assertIs(Advisor.rung_for(request()), Rung.REMOTE)

    def test_the_default_on_a_request_is_the_standard_rung(self):
        self.assertIs(request().rung, Rung.REMOTE)

    def test_nothing_in_this_module_names_the_expensive_rung(self):
        import ofn.adapters.advisor as mod
        src = open(mod.__file__, encoding="utf-8").read()
        self.assertNotIn("REMOTE_DEEP", src)

    def test_tier_one_is_absent_not_disabled(self):
        """Saba has not been asked, the answer is hers, and code that exists
        gets run."""
        import ofn.adapters.advisor as mod
        src = open(mod.__file__, encoding="utf-8").read().lower()
        for word in ("send_image", "tier1", "tier_1", "attach_image"):
            self.assertNotIn(word, src)


if __name__ == "__main__":
    unittest.main()
