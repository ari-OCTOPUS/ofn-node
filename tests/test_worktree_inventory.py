"""Read-only worktree inventory — parse + classify contracts.

The tool must never prune. UNKNOWN is not FALSE. A timeout is UNKNOWN,
not proof of concurrent writing.
"""

from __future__ import annotations

import ast
import os
import unittest

from tools.worktree_inventory import (
    SUSPECTED, UNKNOWN, VERIFIED, classify, parse_porcelain,
)

SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "worktree_inventory.py",
)

PORCELAIN = """\
worktree /repo
HEAD abcdef0123456789abcdef0123456789abcdef01
branch refs/heads/main

worktree /repo/.wt-feature
HEAD 1111111111111111111111111111111111111111
branch refs/heads/feat/x
locked maybe-someone

worktree /repo/.wt-detached
HEAD 2222222222222222222222222222222222222222
detached
prunable gitdir file points to non-existent location

"""


class ParsePorcelain(unittest.TestCase):
    def test_three_entries(self):
        rows = parse_porcelain(PORCELAIN)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["worktree"], "/repo")
        self.assertEqual(rows[0]["branch"], "refs/heads/main")
        self.assertEqual(rows[1]["locked"], "maybe-someone")
        self.assertEqual(rows[2]["detached"], "1")
        self.assertIn("prunable", rows[2])

    def test_empty_input(self):
        self.assertEqual(parse_porcelain(""), [])


class ClassifyLockZone(unittest.TestCase):
    def test_clean_unlocked_is_verified(self):
        self.assertEqual(
            classify({}, status_ok=True, lock_present=False, timeout=False),
            VERIFIED)

    def test_dirty_or_locked_is_suspected(self):
        self.assertEqual(
            classify({}, status_ok=False, lock_present=False, timeout=False),
            SUSPECTED)
        self.assertEqual(
            classify({}, status_ok=True, lock_present=True, timeout=False),
            SUSPECTED)
        self.assertEqual(
            classify({"locked": "1"}, status_ok=True, lock_present=False,
                     timeout=False),
            SUSPECTED)

    def test_timeout_is_unknown_not_false(self):
        self.assertEqual(
            classify({}, status_ok=None, lock_present=False, timeout=True),
            UNKNOWN)
        self.assertNotEqual(
            classify({}, status_ok=None, lock_present=False, timeout=True),
            SUSPECTED)
        self.assertNotEqual(UNKNOWN, "FALSE")

    def test_unreadable_status_is_unknown(self):
        self.assertEqual(
            classify({}, status_ok=None, lock_present=False, timeout=False),
            UNKNOWN)


class NeverPrunes(unittest.TestCase):
    def test_source_has_no_prune_or_remove_calls(self):
        tree = ast.parse(open(SRC, encoding="utf-8").read(), filename=SRC)
        invoked = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                invoked.append(node.value)
        self.assertNotIn("worktree remove", " ".join(invoked))
        self.assertNotIn("worktree prune", " ".join(invoked))
        # subprocess args are lists of constants
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for arg in node.args:
                    if isinstance(arg, ast.List):
                        words = [
                            el.value for el in arg.elts
                            if isinstance(el, ast.Constant)
                        ]
                        self.assertNotIn("prune", words)
                        self.assertNotIn("remove", words)


if __name__ == "__main__":
    unittest.main()
