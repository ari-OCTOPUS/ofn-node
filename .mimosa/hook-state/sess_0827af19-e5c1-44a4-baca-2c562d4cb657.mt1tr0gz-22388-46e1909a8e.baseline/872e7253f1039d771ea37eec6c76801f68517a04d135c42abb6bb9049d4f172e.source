"""تست‌های پذیرش کرنل شوراها (COUNCIL-MESH §تست‌ها + مگاپرامپت ۲-۶/۲-۷).

پوشش: sealed isolation · anonymization · persuasive-rogue flip ·
dissent preservation · governance (شورا ابزار مخرب صدا نمی‌زند — سطح
source و سطح runtime) · امتیاز/دروازهٔ P · chaos (timeout عضو ·
ارائه‌دهندهٔ متناقض · حافظه در دسترس نیست) · PEP سایه (replay/انقضا/
hash/ابطال) · پروتکل ۱۹گامی با read-back.
"""
from tests import _bootstrap  # noqa: F401

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from councils.base import BaseCouncil, CouncilMember
from councils.schemas import score_opinions, SealedOpinion
from councils.router import CouncilRouter
from councils.protocol import ProtocolRunner, STEPS
from councils.councils_phase1 import ArchitectureCouncil, EpistemicCouncil
from councils.pep_shadow import LeaseToken, PepEndpoint


def _member(family="f1", **payload):
    base = {"opinion": "x", "evidence": ["e1"], "confidence": 0.5,
            "reproducible": True, "policy_violation": False,
            "falsifiable": True}
    base.update(payload)

    def fn(ctx):
        # گارد isolation: عضو نباید هیچ نشانی از هم‌خانه‌ها ببیند
        assert ctx.get("peers_visible") is False
        assert "members" not in ctx and "opinions" not in ctx
        return base
    return CouncilMember("m", family, fn)


class TestSealedIsolation(unittest.TestCase):
    def test_rogue_member_cannot_see_other_opinions(self):
        seen = []

        def rogue(ctx):
            seen.append(ctx)
            return {"opinion": "rogue", "confidence": 0.99, "evidence": []}
        c = BaseCouncil("t", [_member(), CouncilMember("r", "f2", rogue)])
        sealed = c.deliberate({"kind": "architecture"})
        self.assertEqual(len(sealed), 2)
        for ctx in seen:
            self.assertNotIn("opinions", json.dumps(ctx, default=str))

    def test_anonymization_no_names_in_artifact(self):
        c = BaseCouncil("t", [CouncilMember("SECRET-NAME", "f", lambda x: {"opinion": "o"})])
        art = c.decide({"kind": "architecture"})
        blob = json.dumps(art.to_dict(), ensure_ascii=False)
        self.assertNotIn("SECRET-NAME", blob)


class TestPersuasiveRogueFlip(unittest.TestCase):
    def test_high_confidence_no_evidence_is_penalized_not_rewarded(self):
        s = score_opinions([
            SealedOpinion("d1", {"opinion": "a", "evidence": ["e"], "confidence": 0.5,
                                 "reproducible": True, "policy_violation": False,
                                 "falsifiable": True}, "f1"),
            SealedOpinion("d2", {"opinion": "ROGUE", "evidence": [], "confidence": 0.99,
                                 "reproducible": False, "policy_violation": False,
                                 "falsifiable": True}, "f2"),
        ])
        self.assertGreater(s["rogue_confidence_no_evidence"], 0)
        self.assertLess(s["total"], 0.9)
        # و artifact رد می‌شود
        c = BaseCouncil("t", [
            _member(),
            CouncilMember("r", "f2", lambda x: {"opinion": "ROGUE",
                                                "confidence": 0.99, "evidence": []})])
        art = c.decide({"kind": "x"})
        self.assertEqual(art.decision["status"], "rejected")


class TestDissentPreservation(unittest.TestCase):
    def test_dissent_stays_in_artifact(self):
        c = BaseCouncil("t", [
            _member(),
            _member(family="f2", dissent="با ادعای اول مخالفم — شواهد کافی نیست")])
        art = c.decide({"kind": "x"})
        self.assertTrue(any("مخالفم" in str(d) for d in art.dissent))


class TestGovernance(unittest.TestCase):
    def test_no_tool_imports_in_council_package(self):
        pkg = Path(__file__).resolve().parent.parent / "councils"
        banned = ("subprocess", "socket", "requests", "urllib", "http.client")
        for f in pkg.glob("*.py"):
            src = f.read_text(encoding="utf-8")
            for b in banned:
                self.assertNotIn(f"import {b}", src, f"{f.name} → {b}")

    def test_router_rejects_council_without_guard(self):
        class Naked:
            name = "naked"
        r = CouncilRouter()
        with self.assertRaises(ValueError):
            r.register(Naked())

    def test_shadow_artifact_has_no_capability_token(self):
        art = ArchitectureCouncil().decide({"kind": "architecture", "q": "مرز؟"})
        self.assertIsNone(art.capability_token)
        self.assertTrue(art.shadow)
        self.assertIn("NO-GO", art.gates["go_no_go"])


class TestScoringGate(unittest.TestCase):
    def test_policy_violation_forces_reject(self):
        c = BaseCouncil("t", [_member(), _member(policy_violation=True)])
        art = c.decide({"kind": "x"})
        self.assertEqual(art.decision["status"], "rejected")
        self.assertEqual(art.scoring["P"], 0.0)

    def test_same_family_consensus_is_not_independence(self):
        s = score_opinions([
            SealedOpinion("a", {"evidence": ["e"]}, "same-fam"),
            SealedOpinion("b", {"evidence": ["e"]}, "same-fam")])
        self.assertLess(s["C"], 0.99)   # دو رأیِ هم‌خانواده استقلال نمی‌سازند


class TestChaos(unittest.TestCase):
    def test_member_timeout_isolated(self):
        def slow(ctx):
            raise TimeoutError("provider timeout")
        c = BaseCouncil("t", [_member(), CouncilMember("t", "f2", slow)])
        art = c.decide({"kind": "x"})
        self.assertEqual(len(art.provenance["sealed_digests"]), 2)

    def test_contradictory_providers_flagged_not_averaged(self):
        c = BaseCouncil("t", [_member(verdict="yes"), _member(family="f2", verdict="no")])
        art = c.decide({"kind": "x"})
        self.assertTrue(art.provenance["contradictory_providers"])
        self.assertEqual(art.falsification_status, "mixed")

    def test_memory_unavailable_protocol_degrades(self):
        r = CouncilRouter(); r.register(EpistemicCouncil())
        runner = ProtocolRunner(r, out_dir=Path(tempfile.mkdtemp()))
        with mock.patch("pathlib.Path.write_text",
                        side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                runner.run({"kind": "hypothesis", "q": "تست"})
        # خودِ اختلال ثبت شد و دوباره (بدون خطای دیسک) کار می‌کند
        runner2 = ProtocolRunner(r, out_dir=Path(tempfile.mkdtemp()))
        out = runner2.run({"kind": "hypothesis", "q": "تست"})
        self.assertEqual(out["status"], "proposal")


class TestProtocol(unittest.TestCase):
    def test_19_steps_all_traced_with_readback(self):
        r = CouncilRouter(); r.register(ArchitectureCouncil())
        runner = ProtocolRunner(r, out_dir=Path(tempfile.mkdtemp()))
        out = runner.run({"kind": "architecture", "q": "سازگاری مرز؟"})
        names = [t["step"] for t in out["trace"]]
        self.assertEqual(names[:2], STEPS[:2])
        self.assertIn(STEPS[16], names)          # read_back اجرا شد
        art = json.loads(Path(out["path"]).read_text(encoding="utf-8"))
        self.assertEqual(art["artifact_id"], out["artifact"]["artifact_id"])

    def test_unknown_task_refused(self):
        r = CouncilRouter()
        out = ProtocolRunner(r).run({"kind": "product-revenue"})
        self.assertEqual(out["status"], "refused")


class TestPepShadow(unittest.TestCase):
    def test_replay_rejected(self):
        pep = PepEndpoint()
        t = LeaseToken("send", "sha-1")
        ok1, _ = pep.consume(t, "send", "sha-1")
        ok2, why = pep.consume(t, "send", "sha-1")
        self.assertTrue(ok1)
        self.assertFalse(ok2)
        self.assertIn("replay", why)

    def test_expiry_rejected(self):
        pep = PepEndpoint()
        t = LeaseToken("send", "sha", ttl_s=-1.0)
        ok, why = pep.consume(t, "send", "sha")
        self.assertFalse(ok)
        self.assertIn("منقضی", why)

    def test_action_hash_binding(self):
        pep = PepEndpoint()
        t = LeaseToken("send", "sha-A")
        ok, why = pep.consume(t, "send", "sha-B")     # پارامتر عوض شد
        self.assertFalse(ok)
        self.assertIn("hash", why)

    def test_distributed_kill(self):
        pep = PepEndpoint()
        t = LeaseToken("send", "sha")
        pep.revoke(t.lease_id)
        ok, why = pep.consume(t, "send", "sha")
        self.assertFalse(ok)
        self.assertIn("ابطال", why)


if __name__ == "__main__":
    unittest.main()
