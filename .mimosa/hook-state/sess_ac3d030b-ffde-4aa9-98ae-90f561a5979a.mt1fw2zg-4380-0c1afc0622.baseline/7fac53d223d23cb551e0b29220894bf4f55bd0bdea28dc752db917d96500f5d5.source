"""شاهد ۳ (بازبینی 04:52): گیت عدم‌اختیار شورا — اجماع ≠ قابلیت.

حتی رأی اجماعیِ همهٔ اعضا نمی‌تواند: ارسال تلگرام، فراخوان مدل پولی، پرداخت،
تثبیت جهش، تغییر فلگ، یا push اجرا کند. شورا = دادهٔ مشورتی، نه capability.
"""
from tests import _bootstrap  # noqa: F401

import inspect
import unittest
from pathlib import Path

from councils.base import BaseCouncil, CouncilMember
from councils.router import CouncilRouter
from councils.councils_phase1 import ArchitectureCouncil, EpistemicCouncil


def _unanimous_council():
    def yes(ctx):
        return {"opinion": "اجماع: اجرا کن", "evidence": ["e1"], "confidence": 1.0,
                "verdict": "yes", "reproducible": True,
                "policy_violation": False, "falsifiable": True}
    return BaseCouncil("t", [CouncilMember(f"m{i}", f"f{i}", yes) for i in range(5)])


class TestCouncilCannotExecute(unittest.TestCase):
    def test_unanimous_artifact_has_no_capability(self):
        art = _unanimous_council().decide({"kind": "architecture", "q": "اجرا کن"})
        self.assertIsNone(art.capability_token)          # هیچ توکن قابلیتی صادر نمی‌شود
        self.assertTrue(art.shadow)
        self.assertIn("هیچ", art.decision["reason"])      # صلاحیت اجرا: هیچ

    def test_no_execution_surface_in_package(self):
        pkg = Path(__file__).resolve().parent.parent / "councils"
        banned = ("subprocess", "socket", "urllib", "requests", "http.client",
                  "webhook", "payout", "flag_drift", "git ")
        for f in pkg.glob("*.py"):
            src = f.read_text(encoding="utf-8")
            for b in banned:
                self.assertNotIn(f"import {b}".strip(), src, f"{f.name}→{b}")

    def test_router_refuses_execution_kinds(self):
        r = CouncilRouter()
        r.register(ArchitectureCouncil()); r.register(EpistemicCouncil())
        for kind in ("send", "pay", "spend", "mutate", "fixate", "push",
                     "flag-flip", "restart", "execute"):
            c, err = r.route({"kind": kind})
            self.assertIsNone(c, kind)
            self.assertIn("ناشناخته/غیرمجاز", err)

    def test_unanimous_decision_stays_proposal_worded_as_non_executive(self):
        art = _unanimous_council().decide({"kind": "architecture", "q": "x"})
        self.assertEqual(art.decision["status"], "proposal")   # نه execute/approved-for-exec
        self.assertEqual(art.gates["go_no_go"].startswith("NO-GO"), True)

    def test_module_api_exposes_no_sideeffect_callables(self):
        from councils import base, router, protocol, schemas
        for mod in (base, router, protocol, schemas):
            for name, fn in inspect.getmembers(mod, inspect.isfunction):
                low = name.lower()
                self.assertNotIn("send", low, (mod.__name__, name))
                self.assertNotIn("pay", low, (mod.__name__, name))
                self.assertNotIn("apply", low, (mod.__name__, name))
                self.assertNotIn("flip", low, (mod.__name__, name))


if __name__ == "__main__":
    unittest.main()
