"""The cleanup helper cleans up, and nothing goes back to leaking.

Two different claims, so two different tests. The first proves the mechanism
works: a directory handed to a test case is gone once that case ends. The
second proves it is the only mechanism in use — which is the part that decayed
last time, silently, across sixteen files and several days of suite runs until
tmpfs filled and the boot supervisor started failing tests that had nothing to
do with any of it.
"""

from __future__ import annotations

import glob
import os
import re
import unittest

from tests.tmpdir import temp_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestTheDirectoryIsRemoved(unittest.TestCase):
    def test_it_exists_during_the_case_and_not_after(self):
        seen = {}

        class Inner(unittest.TestCase):
            def test_asks_for_one(self):
                path = temp_dir(self)
                seen["path"] = path
                seen["during"] = os.path.isdir(path)

        result = unittest.TextTestRunner(
            stream=open(os.devnull, "w"), verbosity=0).run(
                unittest.defaultTestLoader.loadTestsFromTestCase(Inner))

        self.assertTrue(result.wasSuccessful())
        self.assertTrue(seen["during"], "directory was not created")
        self.assertFalse(os.path.isdir(seen["path"]),
                         "directory outlived the test that owned it")

    def test_a_failing_test_still_gets_cleaned_up(self):
        """Teardown must not depend on the test passing — the leak was worst
        in exactly the runs where something else had already gone wrong."""
        seen = {}

        class Inner(unittest.TestCase):
            def test_fails_on_purpose(self):
                seen["path"] = temp_dir(self)
                self.fail("deliberate")

        unittest.TextTestRunner(
            stream=open(os.devnull, "w"), verbosity=0).run(
                unittest.defaultTestLoader.loadTestsFromTestCase(Inner))

        self.assertFalse(os.path.isdir(seen["path"]),
                         "a failed test left its directory behind")


class TestNobodyLeaksAgain(unittest.TestCase):
    """No unowned temporary path is created anywhere in the suite."""

    def modules(self):
        for path in sorted(glob.glob(os.path.join(ROOT, "tests", "*.py"))):
            # `tmpdir.py` is the one place mkdtemp is allowed to live, and this
            # file names the call in order to forbid it.
            if os.path.basename(path) in {"tmpdir.py", "test_tmpdir.py"}:
                continue
            with open(path, encoding="utf-8") as fh:
                yield os.path.relpath(path, ROOT), fh.read()

    def test_no_bare_mkdtemp(self):
        for name, body in self.modules():
            self.assertNotIn("tempfile.mkdtemp(", body,
                             f"{name} calls mkdtemp directly; use "
                             f"temp_dir(self) from tests.tmpdir")

    def test_mkstemp_always_names_a_directory(self):
        """`mkstemp()` with no `dir=` drops a file into /tmp with no owner."""
        for name, body in self.modules():
            for call in re.finditer(r"tempfile\.mkstemp\((.*?)\)", body,
                                    re.DOTALL):
                self.assertIn("dir=", call.group(1),
                              f"{name} calls mkstemp without dir=")


if __name__ == "__main__":
    unittest.main()
