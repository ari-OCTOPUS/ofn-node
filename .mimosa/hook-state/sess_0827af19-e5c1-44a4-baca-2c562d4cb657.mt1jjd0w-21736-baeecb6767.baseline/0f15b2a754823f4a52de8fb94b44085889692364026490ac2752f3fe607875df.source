#!/usr/bin/env python3
"""تستِ گیتِ ماشین‌خوان.

قانونی که این تست محافظت می‌کند: **گیت هرگز نباید بدونِ عدد سبز شود.**
یک ارگانیسمِ خودکدنویس که سبزِ دروغین بخواند، کدِ خراب را merge می‌کند.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_report as gr  # noqa: E402


PYTEST_GREEN = "....                                             [100%]\n4 passed in 0.31s\n"
PYTEST_RED = "..F.                                             [100%]\n1 failed, 3 passed in 0.44s\n"
PYTEST_MIXED = "2 failed, 10 passed, 1 skipped, 1 error in 2.10s\n"
UNITTEST_GREEN = "test_a (m.T) ... ok\n\n----\nRan 14 tests in 0.011s\n\nOK\n"
UNITTEST_RED = ("Ran 9 tests in 0.02s\n\n"
                "FAILED (failures=2, errors=1)\n")
UNITTEST_SKIP = "Ran 5 tests in 0.01s\n\nOK (skipped=2)\n"


class ParseCountsTests(unittest.TestCase):
    def test_pytest_green(self):
        c = gr.parse_counts(PYTEST_GREEN, "", 0)
        self.assertEqual((c["passed"], c["failed"]), (4, 0))
        self.assertEqual(c["granularity"], "test")

    def test_pytest_red(self):
        c = gr.parse_counts(PYTEST_RED, "", 1)
        self.assertEqual((c["passed"], c["failed"]), (3, 1))

    def test_pytest_mixed_counts_errors_and_skips(self):
        c = gr.parse_counts(PYTEST_MIXED, "", 1)
        self.assertEqual((c["passed"], c["failed"], c["errors"], c["skipped"]),
                         (10, 2, 1, 1))

    def test_unittest_green(self):
        c = gr.parse_counts(UNITTEST_GREEN, "", 0)
        self.assertEqual((c["passed"], c["failed"]), (14, 0))
        self.assertEqual(c["granularity"], "test")

    def test_unittest_red_splits_failures_and_errors(self):
        c = gr.parse_counts("", UNITTEST_RED, 1)
        self.assertEqual((c["failed"], c["errors"]), (2, 1))
        self.assertEqual(c["passed"], 6, "9 - 2 failures - 1 error = 6")

    def test_unittest_skipped_is_not_counted_as_passed(self):
        c = gr.parse_counts(UNITTEST_SKIP, "", 0)
        self.assertEqual(c["passed"], 5)

    def test_silent_success_is_file_granularity_not_a_test_count(self):
        """هیچ عددی چاپ نشد و exit صفر بود → ادعای «N تست پاس شد» ممنوع."""
        c = gr.parse_counts("", "", 0)
        self.assertEqual(c["granularity"], "file")
        self.assertEqual(c["source"], "exitcode")

    def test_silent_failure_is_recorded_as_one_failure(self):
        c = gr.parse_counts("", "Traceback...\n", 1)
        self.assertEqual((c["passed"], c["failed"]), (0, 1))
        self.assertEqual(c["granularity"], "file")

    def test_ambiguous_unittest_with_red_exit_never_claims_passes(self):
        c = gr.parse_counts("Ran 20 tests in 1s\n", "", 1)
        self.assertEqual(c["passed"], 0)
        self.assertEqual(c["granularity"], "file")


class GateTests(unittest.TestCase):
    @staticmethod
    def _res(file, passed, failed, gran="test", rc=0, errors=0):
        return {"file": file, "passed": passed, "failed": failed, "errors": errors,
                "skipped": 0, "granularity": gran, "source": "x",
                "returncode": rc, "duration_s": 0.1}

    def test_all_green_is_green(self):
        rep = gr.build_report([self._res("a.py", 5, 0), self._res("b.py", 3, 0)], [], 1.0)
        self.assertEqual(rep["gate"], "green")
        self.assertEqual(rep["passed"], 8)

    def test_unexpected_red_is_red(self):
        rep = gr.build_report([self._res("a.py", 5, 1, rc=1)], [], 1.0)
        self.assertEqual(rep["gate"], "red")
        self.assertEqual(rep["files_unexpected_red"], ["a.py"])

    def test_the_one_intentional_red_does_not_turn_the_gate_red(self):
        rep = gr.build_report(
            [self._res("test_paid_router_dark_config.py", 2, 1, rc=1),
             self._res("b.py", 4, 0)], [], 1.0)
        self.assertEqual(rep["gate"], "green")
        self.assertIn("test_paid_router_dark_config.py", rep["files_failed"])
        self.assertEqual(rep["files_unexpected_red"], [])

    def test_file_granularity_alone_can_never_be_green(self):
        """ستونِ فقراتِ §۱۴ — «هیچ خطایی ندیدم» سبز نیست."""
        rep = gr.build_report([self._res("a.py", 1, 0, gran="file"),
                               self._res("b.py", 1, 0, gran="file")], [], 1.0)
        self.assertEqual(rep["gate"], "unknown")

    def test_mixed_granularity_is_reported_and_lists_unparsed(self):
        rep = gr.build_report([self._res("a.py", 9, 0),
                               self._res("b.py", 1, 0, gran="file")], [], 1.0)
        self.assertEqual(rep["granularity"], "mixed")
        self.assertEqual(rep["unparsed"], ["b.py"])

    def test_unreadable_dynamic_list_forces_unknown_even_if_all_green(self):
        rep = gr.build_report([self._res("a.py", 9, 0)], ["EXTRA_TESTS"], 1.0)
        self.assertEqual(rep["gate"], "unknown",
                         "اگر بخشی از سوئیت خوانده نشد، ادعای پوشش دروغ است")

    def test_render_never_raises(self):
        for dyn in ([], ["EXTRA_TESTS"]):
            rep = gr.build_report([self._res("a.py", 1, 1, gran="file", rc=1)], dyn, 1.0)
            self.assertIsInstance(gr.render(rep), str)


class ReadTestListsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_literal_lists_are_read_without_import(self):
        f = self.tmp / "run_all.py"
        f.write_text(
            'raise SystemExit("این فایل هرگز نباید اجرا شود")\n'
            'TESTS = ["test_a.py", "test_b.py"]\n'
            'PYTEST_TESTS = {"test_b.py"}\n', encoding="utf-8")
        tests, pyt, dyn = gr.read_test_lists(f)
        self.assertEqual(tests, ["test_a.py", "test_b.py"])
        self.assertEqual(pyt, {"test_b.py"})
        self.assertEqual(dyn, [])

    def test_dynamic_list_is_reported_not_silently_dropped(self):
        f = self.tmp / "run_all.py"
        f.write_text('TESTS = ["test_a.py"]\n'
                     'EXTRA_TESTS = [HERE / "x" / "test_z.py"]\n', encoding="utf-8")
        _t, _p, dyn = gr.read_test_lists(f)
        self.assertIn("EXTRA_TESTS", dyn)

    def test_real_run_all_is_parsed_if_present(self):
        real = Path(__file__).resolve().parent / "run_all.py"
        if not real.exists():
            self.skipTest("run_all.py در این درخت نیست")
        tests, pyt, dyn = gr.read_test_lists(real)
        self.assertGreater(len(tests), 50, "فهرستِ TESTS باید ده‌ها فایل باشد")
        self.assertTrue(all(t.endswith(".py") for t in tests))
        self.assertIn("test_paid_router_dark_config.py", tests + list(pyt) + [""] or [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
