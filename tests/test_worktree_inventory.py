"""Read-only worktree inventory — parse + classify contracts.

The tool must never prune. UNKNOWN is not FALSE. A timeout is UNKNOWN,
not proof of concurrent writing.
"""

from __future__ import annotations

import ast
import os
import unittest

from tools.worktree_inventory import (
    SUSPECTED, UNKNOWN, VERIFIED, classify, index_lock_present,
    parse_porcelain, read_gitdir_pointer,
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


class GitdirPointer(unittest.TestCase):
    def test_reads_gitdir_line(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            git_file = os.path.join(tmp, ".git")
            with open(git_file, "w", encoding="utf-8") as fh:
                fh.write("gitdir: /repo/.git/worktrees/feat\n")
            self.assertEqual(
                read_gitdir_pointer(git_file),
                "/repo/.git/worktrees/feat")

    def test_malformed_or_missing_is_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            git_file = os.path.join(tmp, ".git")
            with open(git_file, "w", encoding="utf-8") as fh:
                fh.write("not a pointer\n")
            self.assertIsNone(read_gitdir_pointer(git_file))
            self.assertIsNone(read_gitdir_pointer(os.path.join(tmp, "absent")))

    def test_index_lock_follows_gitdir_pointer(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            pointed = os.path.join(tmp, "real-gitdir")
            os.mkdir(pointed)
            wt = os.path.join(tmp, "linked-wt")
            os.mkdir(wt)
            with open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
                fh.write(f"gitdir: {pointed}\n")
            present, unknown = index_lock_present(wt)
            self.assertFalse(present)
            self.assertFalse(unknown)
            with open(os.path.join(pointed, "index.lock"), "w") as fh:
                fh.write("locked")
            present, unknown = index_lock_present(wt)
            self.assertTrue(present)
            self.assertFalse(unknown)

    def test_unreadable_pointer_is_unknown_not_no_lock(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            wt = os.path.join(tmp, "linked-wt")
            os.mkdir(wt)
            with open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
                fh.write("garbage\n")
            present, unknown = index_lock_present(wt)
            self.assertFalse(present)
            self.assertTrue(unknown)


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
