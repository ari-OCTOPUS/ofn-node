"""تستِ گیت‌های ایمنیِ خودتغییریِ کد (brain/self_code + guardrails TCB).

اینجا مسیرِ سریع تست می‌شود (اعتبارسنجی/TCB/scan/عدمِ‌تغییرِ زنده)؛ گیتِ سنگینِ
test_proposal (کپیِ کل پروژه + اجرای سوییت در subprocess) اینجا اجرا نمی‌شود.
"""
from tests import _bootstrap  # noqa: F401

import os
import tempfile
import unittest
from pathlib import Path

import config.settings as settings
from brain import guardrails, self_code


class TestTCB(unittest.TestCase):
    def test_tcb_files_and_dirs_denied(self):
        for p in ["core/model.py", "tests/test_budget.py", "brain/guardrails.py",
                  "brain/self_code.py", "brain/self_evolve.py", "brain/budget.py",
                  "brain/automation.py", "brain/daemon.py", "brain/events.py",
                  "llm/router.py", "llm/glm_client.py", "llm/fugu_client.py",
                  "run.py", "config/settings.py"]:
            ok, _ = guardrails.assert_code_target_allowed(p)
            self.assertFalse(ok, f"{p} باید TCB باشد")

    def test_leaf_files_allowed(self):
        for p in ["data/real_api.py", "ui/visuals.py", "memory/store.py"]:
            ok, _ = guardrails.assert_code_target_allowed(p)
            self.assertTrue(ok, f"{p} باید مجاز باشد")

    def test_non_py_and_outside_denied(self):
        self.assertFalse(guardrails.assert_code_target_allowed("outputs/x.md")[0])
        self.assertFalse(guardrails.assert_code_target_allowed("../4D/model.py")[0])

    def test_is_tcb_failsafe_true_on_bad_path(self):
        # مسیرِ خارج از پروژه → محافظت‌شده (fail-safe)
        self.assertTrue(guardrails.is_tcb("/etc/passwd"))

    def test_init_files_and_config_are_tcb(self):
        # فرارِ config/__init__.py و هر __init__.py (اجرا در import)
        for p in ["config/__init__.py", "data/__init__.py", "brain/__init__.py",
                  "config/settings.py", "config/foo.py"]:
            self.assertFalse(guardrails.assert_code_target_allowed(p)[0],
                             f"{p} باید TCB باشد")

    def test_rebinding_public_is_tcb_does_not_widen(self):
        # rebindِ درون‌فرایندیِ نامِ عمومی نباید گیت را باز کند
        orig = guardrails.is_tcb
        try:
            guardrails.is_tcb = lambda p: False
            ok, _ = guardrails.assert_code_target_allowed("brain/guardrails.py")
            self.assertFalse(ok, "rebind نباید TCB را دور بزند")
        finally:
            guardrails.is_tcb = orig


class TestProposeGate(unittest.TestCase):
    def setUp(self):
        self._orig_out = settings.OUTPUT_DIR
        self._td = tempfile.TemporaryDirectory()
        settings.OUTPUT_DIR = Path(self._td.name)
        os.environ["SELF_CODE_ENABLED"] = "1"
        self._leaf = "memory/embeddings.py"
        self._orig_leaf = (self_code._root() / self._leaf).read_text(encoding="utf-8")

    def tearDown(self):
        settings.OUTPUT_DIR = self._orig_out
        self._td.cleanup()
        os.environ.pop("SELF_CODE_ENABLED", None)
        # اطمینان: فایلِ زنده هرگز عوض نشد
        self.assertEqual(
            (self_code._root() / self._leaf).read_text(encoding="utf-8"),
            self._orig_leaf, "propose نباید کدِ زنده را عوض کند")

    def test_disabled_flag_blocks(self):
        os.environ["SELF_CODE_ENABLED"] = "0"
        r = self_code.propose_code_change(self._leaf, self._orig_leaf + "\n# x\n", "t")
        self.assertFalse(r["ok"])

    def test_tcb_target_refused(self):
        r = self_code.propose_code_change("core/model.py", "x = 1\n", "t")
        self.assertFalse(r["ok"])

    def test_syntax_error_refused(self):
        r = self_code.propose_code_change(self._leaf, "def broken(:\n", "t")
        self.assertFalse(r["ok"])

    def test_dangerous_pattern_refused(self):
        bad = self._orig_leaf + "\nimport os\nos.system('rm -rf /')\n"
        r = self_code.propose_code_change(self._leaf, bad, "t")
        self.assertFalse(r["ok"])
        self.assertIn("خطر", r["reason"])       # AST: «خطرناک» یا substring: «پرخطر»

    def test_no_change_refused(self):
        r = self_code.propose_code_change(self._leaf, self._orig_leaf, "t")
        self.assertFalse(r["ok"])

    def test_valid_propose_is_static_only_pending(self):
        r = self_code.propose_code_change(
            self._leaf, self._orig_leaf + "\n# harmless\n", "harmless comment")
        self.assertTrue(r["ok"])
        pid = r["pid"]
        meta = self_code._load_meta(pid)
        # گیتِ ایستا-پاس → مستقیم pending_approval (هیچ کدی اجرا نشد)
        self.assertEqual(meta["status"], "pending_approval")
        self.assertEqual(meta["target"], self._leaf)
        self.assertTrue((self_code._proposals_dir() / pid / "new.py").exists())

    def test_approve_refused_after_reject(self):
        r = self_code.propose_code_change(
            self._leaf, self._orig_leaf + "\n# y\n", "t")
        self_code.reject(r["pid"])                  # status → rejected
        res = self_code.approve(r["pid"])           # approve فقط روی pending
        self.assertFalse(res["ok"])

    def test_ast_scan_catches_new_import(self):
        # importِ شبکه‌ایِ تازه با AST گرفته می‌شود (نه فقط substring)
        bad = "import socket\n" + self._orig_leaf
        r = self_code.propose_code_change(self._leaf, bad, "t")
        self.assertFalse(r["ok"])


class TestTamperDetect(unittest.TestCase):
    """تشخیصِ دستکاری + بازگردانی — دفاع در برابرِ فرارِ مسیرِ مطلق هنگامِ اجرا."""

    def test_detect_and_restore(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "x.py"
            f.write_text("original\n", encoding="utf-8")
            snap = {str(f): "original\n"}
            self.assertEqual(self_code._detect_tamper(snap), [])   # هنوز سالم
            f.write_text("TAMPERED\n", encoding="utf-8")           # اجرای مخرب
            self.assertEqual(self_code._detect_tamper(snap), [str(f)])
            n = self_code._restore_py(snap)                        # بازگردانی
            self.assertEqual(n, 1)
            self.assertEqual(f.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(self_code._detect_tamper(snap), [])   # دوباره سالم

    def test_scrubbed_env_removes_secrets(self):
        import os
        os.environ["FAKE_API_KEY"] = "sk-secret"
        os.environ["MY_TOKEN"] = "t"
        try:
            env = self_code._scrubbed_env()
            self.assertNotIn("FAKE_API_KEY", env)
            self.assertNotIn("MY_TOKEN", env)
            self.assertEqual(env.get("MOCK_MODE"), "true")
            self.assertEqual(env.get("SELF_CODE_ENABLED"), "0")
        finally:
            os.environ.pop("FAKE_API_KEY", None)
            os.environ.pop("MY_TOKEN", None)


if __name__ == "__main__":
    unittest.main()
