"""تست‌های R13/C-013 — مرزِ اعتمادِ امضاشدنی + فیکسِ REFERENCE_DIR.

پوشش:
  ۱. رگرسیونِ C-013: REFERENCE_DIR هرگز خودِ ریشه/جدِّ ریشه نمی‌شود.
  ۲. manifest موجود، کامل (همهٔ CODE_TCB_FILES) و digestها هم‌خوان.
  ۳. تشخیصِ دستکاری: digestِ غلط ⇒ mismatches/tampered (حتی بدون enforce).
  ۴. اجرا (enforce): دستکاری ⇒ check_invariants.ok=False؛ بدون enforce فقط سایه‌ای.
  ۵. پاکتِ NO-GO (R0a) با digest در manifest.
  ۶. وریفایِ امضای Ed25519 با جفت‌کلیدِ آزمایشی (کلید مالک دست‌نخورده).
"""
from tests import _bootstrap  # noqa: F401

import json
import os
import unittest
from pathlib import Path
from unittest import mock

import config.settings as settings
from brain import guardrails


class TestReferenceDirBoundary(unittest.TestCase):
    """C-013: مرجعِ محافظت‌شده نباید کلِ پروژه را ببلعد."""

    def test_reference_dir_is_not_system_root_or_ancestor(self):
        ref = settings.REFERENCE_DIR.resolve()
        root = settings.SYSTEM_ROOT.resolve()
        self.assertNotEqual(ref, root)
        self.assertFalse(root.is_relative_to(ref),
                         "REFERENCE_DIR جدِّ SYSTEM_ROOT است — کل پروژه TCB می‌شد")

    def test_invalid_env_value_falls_back_to_missing_child(self):
        # even with REFERENCE_DIR='./' (مقدارِ فعلی .env) مرز معتبر می‌ماند
        with mock.patch.dict(os.environ, {"REFERENCE_DIR": "./"}):
            p = settings._resolve_reference_dir()
            root = settings.SYSTEM_ROOT.resolve()
            self.assertNotEqual(p.resolve(), root)
            self.assertFalse(root.is_relative_to(p.resolve()))

    def test_leaf_files_allowed_after_fix(self):
        # رگرسیونِ ۴ شکستِ پیشین: برگ‌ها باید مجاز باشند
        for rel in ["data/real_api.py", "ui/visuals.py", "memory/store.py",
                    "memory/embeddings.py"]:
            ok, reason = guardrails.assert_code_target_allowed(rel)
            self.assertTrue(ok, f"{rel} باید مجاز باشد (got: {reason})")

    def test_tcb_files_still_denied_after_fix(self):
        for rel in ["brain/guardrails.py", "config/settings.py", "core/model.py",
                    "run.py"]:
            ok, _ = guardrails.assert_code_target_allowed(rel)
            self.assertFalse(ok, f"{rel} همچنان TCB است")


class TestTrustBoundaryManifest(unittest.TestCase):
    def setUp(self):
        self.tb = guardrails.check_trust_boundary()

    def test_manifest_present_and_complete(self):
        self.assertTrue(self.tb["present"], "config/trust-boundary.json غایب است")
        self.assertTrue(self.tb["coverage_complete"],
                        "manifest همهٔ CODE_TCB_FILES را نمی‌پوشاند")

    def test_digests_match_live_tree(self):
        self.assertTrue(self.tb["digests_ok"],
                        f"ناهمخوانی: {self.tb['mismatches']} / مفقود: {self.tb['missing']}")

    def test_tamper_detected_in_shadow_mode(self):
        # شبیه‌سازیِ ویرایشِ فایل TCB: digestِ غلط برگردان
        with mock.patch.object(guardrails, "_sha256_file",
                               return_value="deadbeef" * 8):
            tb = guardrails.check_trust_boundary()
        self.assertTrue(tb["mismatches"], "ویرایش TCB باید mismatches بدهد")
        self.assertTrue(tb["tampered"])
        self.assertEqual(tb["enforcement"], False, "پیش‌فرض = سایه‌ای")

    def test_enforcement_halts_invariants_on_tamper(self):
        real_sha = guardrails._sha256_file
        with mock.patch.dict(os.environ,
                             {"OCTOPUS_TCB_MANIFEST_ENFORCE": "1"}), \
             mock.patch.object(guardrails, "_sha256_file",
                               side_effect=lambda p: "0" * 64
                               if p.name == "guardrails.py" else real_sha(p)):
            tb = guardrails.check_trust_boundary()
            inv = guardrails.check_invariants()
        self.assertTrue(tb["tampered"])
        self.assertFalse(inv["ok"], "زیرِ enforce، دستکاری باید ok=False دهد (halt)")

    def test_shadow_mode_does_not_halt_on_tamper(self):
        real_sha = guardrails._sha256_file
        with mock.patch.object(guardrails, "_sha256_file",
                               side_effect=lambda p: "0" * 64
                               if p.name == "guardrails.py" else real_sha(p)):
            inv = guardrails.check_invariants()
        self.assertFalse(inv["tcb"]["enforcement"])
        self.assertTrue(inv["tcb"]["tampered"])
        self.assertTrue(inv["ok"], "بدون enforce، دستکاری فقط گزارشِ سایه‌ای است")

    def test_no_go_envelope_covered(self):
        """R0a: تستِ پاکتِ NO-GO باید با digest در manifest محافظت شود."""
        mp = guardrails._trust_boundary_path()
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        entry = manifest.get("no_go_envelope", {})
        self.assertEqual(entry.get("file"),
                         "../_ops/tests/test_no_go_envelope.py")
        live = guardrails._sha256_file(
            settings.SYSTEM_ROOT / entry["file"])
        self.assertEqual(f"sha256:{live}", entry.get("sha256"),
                         "digest پاکت NO-GO با فایل زنده هم‌خوان نیست")
        self.assertIn("owner-only", entry.get("ownership", ""))


class TestSignatureVerification(unittest.TestCase):
    """وریفایِ Ed25519 با جفت‌کلیدِ آزمایشی — مکانیزم، بدون کلیدِ مالک."""

    def _make_signed_pair(self, tmpdir: Path):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PrivateFormat, NoEncryption, PublicFormat)
        key = Ed25519PrivateKey.generate()
        pub_pem = tmpdir / "test-pub.pem"
        pub_pem.write_bytes(key.public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
        payload = (tmpdir / "payload.json")
        payload.write_bytes(b'{"probe": "trust-boundary-signature-test"}')
        sig = tmpdir / "payload.sig"
        sig.write_bytes(key.sign(payload.read_bytes()))
        return key, pub_pem, payload, sig

    def test_valid_and_invalid_signature(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            _, pub, payload, sig = self._make_signed_pair(tmpdir)
            fake_root = tmpdir / "fake_root"
            fake_root.mkdir()
            (fake_root / "owner-signing").mkdir()
            # کلیدِ عمومی آزمایشی را در جایگاهِ موردِ انتظار بگذار
            import shutil
            shutil.copy(pub, fake_root / "owner-signing" / "test-pub.pem")
            with mock.patch.object(guardrails, "_OWNER_PUBKEY_CANDIDATES",
                                   ("owner-signing/test-pub.pem",)), \
                 mock.patch.object(guardrails, "_system_root",
                                   return_value=fake_root):
                status, _ = guardrails._verify_owner_signature(payload, sig)
                self.assertEqual(status, "valid")
                bad = tmpdir / "bad.sig"
                bad.write_bytes(b"\x00" * 64)
                status2, msg = guardrails._verify_owner_signature(payload, bad)
                self.assertEqual(status2, "invalid")

    def test_live_signature_state_is_reported_not_crashing(self):
        self.assertIn(self.tb_state(), ("none", "unsigned", "valid", "invalid",
                                        "no-key", "error"))

    @staticmethod
    def tb_state():
        return guardrails.check_trust_boundary()["signature"]


if __name__ == "__main__":
    unittest.main()
