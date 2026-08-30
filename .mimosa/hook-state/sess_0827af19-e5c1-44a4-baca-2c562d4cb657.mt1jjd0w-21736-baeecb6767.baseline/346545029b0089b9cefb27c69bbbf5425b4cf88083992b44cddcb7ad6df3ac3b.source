#!/usr/bin/env python3
"""تستِ اسکنِ خودشناسی.

قانونی که محافظت می‌شود: هر یافته باید **درست‌مثبت** باشد و هر بررسی باید
حدودِ خودش را اعلام کند. یک اسکنرِ خودشناسی که مثبتِ کاذب بدهد، بدتر از
نداشتنش است — چون اعتماد را می‌سوزاند و بعد کسی نگاهش نمی‌کند.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
import self_scan as ss  # noqa: E402

CRLF = "\r\n"


def build_tree(files: dict) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".cmd"):
            p.write_bytes((CRLF.join(body.splitlines()) + CRLF).encode("utf-8"))
        else:
            p.write_text(body, encoding="utf-8")
    # عمداً هیچ فایلی از درختِ واقعی این‌جا کپی نمی‌شود: ورودیِ اسکنر باید
    # دقیقاً همان چیزی باشد که تست تعریف کرده، وگرنه یافته‌ها آلوده می‌شوند.
    return root


class FlagTests(unittest.TestCase):
    def test_armed_but_no_reader_is_found(self):
        root = build_tree({
            "OCTOPUS-flags.cmd": '@set "OCTOPUS_USED=1"\n@set "OCTOPUS_GHOST=1"',
            "a.py": 'import os\nos.environ.get("OCTOPUS_USED")\n',
        })
        r = ss.scan_flags(root)
        self.assertIn("OCTOPUS_GHOST", r["armed_unread"])
        self.assertNotIn("OCTOPUS_USED", r["armed_unread"])

    def test_read_but_never_defined_is_found(self):
        root = build_tree({
            "OCTOPUS-flags.cmd": '@set "OCTOPUS_USED=1"',
            "a.py": 'os.environ.get("OCTOPUS_UNDECLARED")\n',
        })
        r = ss.scan_flags(root)
        names = [x["flag"] for x in r["read_unarmed"]]
        self.assertIn("OCTOPUS_UNDECLARED", names)
        self.assertEqual(r["read_unarmed"][0]["modules"], ["a.py"])

    def test_secrets_are_skipped_not_reported_as_undeclared(self):
        """رازها در .env هستند نه flags.cmd — گزارششان مثبتِ کاذب است."""
        root = build_tree({
            "OCTOPUS-flags.cmd": '@set "OCTOPUS_USED=1"',
            "a.py": 'os.environ.get("OCTOPUS_CB_SECRET")\n'
                    'os.environ.get("TELEGRAM_BOT_TOKEN")\n',
        })
        r = ss.scan_flags(root)
        names = [x["flag"] for x in r["read_unarmed"]]
        self.assertNotIn("OCTOPUS_CB_SECRET", names)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", names)
        self.assertIn("OCTOPUS_CB_SECRET", r["secrets_skipped"])

    def test_missing_flags_file_is_reported_not_crashed(self):
        r = ss.scan_flags(build_tree({"a.py": "x = 1\n"}))
        self.assertFalse(r["flags_file_found"])
        self.assertEqual(r["armed"], 0)

    def test_limits_are_declared_in_every_result(self):
        r = ss.scan_flags(build_tree({"a.py": "x = 1\n"}))
        self.assertIn("falsified_by", r)


class StateTests(unittest.TestCase):
    def test_zero_reference_state_file_is_an_orphan(self):
        root = build_tree({"a.py": "x = 1\n", "state/nobody.json": "{}"})
        r = ss.scan_state(root)
        self.assertEqual(r["orphan_count"], 1)
        self.assertEqual(r["orphan"][0]["file"], "nobody.json")

    def test_single_referencer_is_the_write_only_signature(self):
        """امضایِ دقیقِ tg-send-log.jsonl: فقط نویسنده‌اش نامش را می‌برد."""
        root = build_tree({
            "writer.py": 'P = "only.jsonl"\n',
            "other.py": "x = 1\n",
            "state/only.jsonl": '{"a":1}\n',
        })
        r = ss.scan_state(root)
        self.assertEqual(r["single_count"], 1)
        self.assertEqual(r["single_referencer"][0]["by"], ["writer.py"])

    def test_two_referencers_is_not_flagged(self):
        root = build_tree({
            "writer.py": 'P = "shared.json"\n',
            "reader.py": 'Q = "shared.json"\n',
            "state/shared.json": "{}",
        })
        r = ss.scan_state(root)
        self.assertEqual(r["orphan_count"], 0)
        self.assertEqual(r["single_count"], 0)

    def test_tests_do_not_count_as_consumers(self):
        """اگر فقط یک تست نامش را ببرد، هنوز مصرف‌کنندهٔ واقعی ندارد."""
        root = build_tree({
            "writer.py": 'P = "x.json"\n',
            "tests/test_writer.py": 'P = "x.json"\n',
            "state/x.json": "{}",
        })
        r = ss.scan_state(root)
        self.assertEqual(r["single_count"], 1)


class TestCoverageTests(unittest.TestCase):
    def test_module_with_no_test_reference_is_listed(self):
        root = build_tree({"lonely.py": "def f():\n    return 1\n",
                           "tests/test_other.py": "import other\n"})
        r = ss.scan_tests(root)
        self.assertIn("lonely.py", [x["module"] for x in r["untested"]])

    def test_module_imported_by_a_test_is_covered(self):
        root = build_tree({"covered.py": "def f():\n    return 1\n",
                           "tests/test_covered.py": "import covered\n"})
        r = ss.scan_tests(root)
        self.assertNotIn("covered.py", [x["module"] for x in r["untested"]])

    def test_coverage_is_labelled_as_an_optimistic_ceiling(self):
        r = ss.scan_tests(build_tree({"a.py": "x=1\n"}))
        self.assertIn("سقفِ خوش‌بینانه", r["falsified_by"])


class MarkerTests(unittest.TestCase):
    def test_todo_and_fixme_are_found_with_line_numbers(self):
        root = build_tree({"a.py": "x = 1\n# TODO: بعداً\ny = 2  # FIXME broken\n"})
        r = ss.scan_markers(root)
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["hits"][0]["line"], 2)
        self.assertEqual(set(r["by_marker"]), {"TODO", "FIXME"})

    def test_noqa_lines_are_not_markers(self):
        root = build_tree({"a.py": "x = 1  # noqa: TODO\n"})
        self.assertEqual(ss.scan_markers(root)["count"], 0)

    def test_test_files_are_excluded_from_markers(self):
        root = build_tree({"tests/test_a.py": "# TODO nope\n"})
        self.assertEqual(ss.scan_markers(root)["count"], 0)


class SymbolTests(unittest.TestCase):
    def test_unused_public_function_is_flagged(self):
        body = "def orphan_fn():\n" + "".join(f"    x{i} = {i}\n" for i in range(8))
        root = build_tree({"a.py": body, "b.py": "y = 1\n"})
        r = ss.scan_symbols(root)
        self.assertEqual([d["symbol"] for d in r["dead"]], ["orphan_fn"])

    def test_symbol_used_elsewhere_is_not_flagged(self):
        body = "def used_fn():\n" + "".join(f"    x{i} = {i}\n" for i in range(8))
        root = build_tree({"a.py": body, "b.py": "from a import used_fn\n"})
        self.assertEqual(ss.scan_symbols(root)["count"], 0)

    def test_private_and_short_symbols_are_ignored(self):
        root = build_tree({"a.py": "def _hidden():\n    pass\n\ndef tiny():\n    pass\n"})
        self.assertEqual(ss.scan_symbols(root)["count"], 0)


class RunTests(unittest.TestCase):
    def test_run_produces_headline_without_a_composite_score(self):
        r = ss.run(build_tree({"a.py": "x=1\n"}))
        self.assertIn("headline", r)
        blob = str(r["headline"]).lower()
        for banned in ("score", "index", "percent", "grade"):
            self.assertNotIn(banned, blob,
                             "یک نمرهٔ مرکب پنهان می‌کند کدام بررسی خراب است")

    def test_a_broken_check_does_not_kill_the_others(self):
        root = build_tree({"a.py": "x=1\n"})
        orig = ss.scan_state

        def boom(_root):
            raise RuntimeError("منفجر شد")

        ss.scan_state = boom
        ss._CHECKS["state"] = boom
        try:
            r = ss.run(root)
            self.assertIn("state", r["errors"])
            self.assertIn("flags", r["checks"])
            self.assertEqual(r["headline"]["checks_failed"], 1)
        finally:
            ss.scan_state = orig
            ss._CHECKS["state"] = orig

    def test_forbidden_paths_are_structurally_excluded(self):
        root = build_tree({"a.py": "x=1\n",
                           "Identity/leak.py": "SECRET = 1\n",
                           "__pycache__/junk.py": "x=1\n"})
        names = {f.name for f in ss.py_files(root)}
        self.assertIn("a.py", names)
        self.assertNotIn("leak.py", names)
        self.assertNotIn("junk.py", names)

    def test_card_never_raises_and_states_its_own_limits(self):
        text = ss.card(build_tree({"a.py": "x=1\n"}))
        self.assertIsInstance(text, str)
        self.assertIn("هیچ نمرهٔ واحدی", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
