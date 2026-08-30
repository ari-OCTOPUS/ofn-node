"""تست وصل عضو مدلِ واقعی به شورای سایه (2026-08-16، رأی مالک).

پوشش: قرارداد JSON عضو · بودجهٔ اتمی عضو · fail-soft (parse/خطا/بی‌بودجه) ·
بستهٔ councils همچنان import-پاک می‌ماند (wiring بیرون از بسته) ·
شورای تقویت‌شده هنوز سایه است (token=None) و رأی استاب را نمی‌بلعد.
"""
from tests import _bootstrap  # noqa: F401

import json
import unittest
from pathlib import Path
from unittest import mock

import councils_real as cr
from councils.base import CouncilMember


class TestLlmMemberContract(unittest.TestCase):
    def test_parses_valid_json_opinion(self):
        reply = '{"opinion": "سازگار است", "evidence": ["DA-4"], "confidence": 0.7}'
        with mock.patch.object(cr, "_router_ask", create=True), \
             mock.patch("llm.router.LLMRouter") as Router:
            Router.return_value.ask.return_value = reply
            m = cr.make_llm_member()
            out = m.opine({"task": {"kind": "architecture", "q": "مرز؟"}})
        self.assertEqual(out["opinion"], "سازگار است")
        self.assertEqual(out["evidence"], ["DA-4"])
        self.assertAlmostEqual(out["confidence"], 0.7)
        self.assertFalse(out["policy_violation"])

    def test_budget_exhausted_after_max_calls(self):
        with mock.patch("llm.router.LLMRouter") as Router:
            Router.return_value.ask.return_value = '{"opinion": "اول"}'
            m = cr.make_llm_member(max_calls=1)
            first = m.opine({"task": {}})
            second = m.opine({"task": {}})
        self.assertEqual(first["opinion"], "اول")
        self.assertEqual(second["opinion"], "__member_budget_exhausted__")

    def test_unparseable_reply_is_honest_stub(self):
        with mock.patch("llm.router.LLMRouter") as Router:
            Router.return_value.ask.return_value = "من فقط حرف می‌زنم بدون JSON"
            out = cr.make_llm_member().opine({"task": {}})
        self.assertEqual(out["opinion"], "__member_unparseable__")
        self.assertIn("raw", str(out.get("dissent")))

    def test_router_error_never_kills_member(self):
        with mock.patch("llm.router.LLMRouter", side_effect=RuntimeError("boom")):
            out = cr.make_llm_member().opine({"task": {}})
        self.assertEqual(out["opinion"], "__member_error__")
        self.assertIn("RuntimeError", str(out.get("dissent")))


class TestPackagePurity(unittest.TestCase):
    def test_councils_package_still_import_clean(self):
        pkg = Path(__file__).resolve().parent.parent / "councils"
        banned = ("subprocess", "socket", "requests", "urllib", "http.client",
                  "llm.router", "councils_real")
        for f in pkg.glob("*.py"):
            src = f.read_text(encoding="utf-8")
            for b in banned:
                self.assertNotIn(f"import {b}", src, f"{f.name} → {b}")

    def test_augmented_council_still_shadow(self):
        with mock.patch("llm.router.LLMRouter") as Router:
            Router.return_value.ask.return_value = '{"opinion": "نظر مدل"}'
            c = cr.augment_architecture_council()
            art = c.decide({"kind": "architecture", "q": "تست"})
        self.assertIsNone(art.capability_token)
        self.assertTrue(art.shadow)
        self.assertEqual(len(c.members), 3)   # دو استاب + یک مدل
        # رأی استاب‌ها هم در claims هست — بلعیده نشده
        joined = json.dumps([cl.text for cl in art.claims], ensure_ascii=False)
        self.assertIn("نظر مدل", joined)


if __name__ == "__main__":
    unittest.main()
