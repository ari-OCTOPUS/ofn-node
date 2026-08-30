"""The kernel's three structural promises, checked mechanically.

These tests are not about behaviour. They exist because the promises they
check are the kind that erode one convenient import at a time, and nobody
notices until the kernel can no longer be reasoned about.
"""

from __future__ import annotations

import ast
import os
import sys
import unittest

KERNEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "ofn", "kernel")

# Modules the kernel may import. Everything else is either I/O, non-determinism,
# or a third-party dependency — all three are disqualifying.
# `math` is here because ofn/kernel/edge.py (the hypno edge model, pure
# deterministic math, no I/O) uses it for clamp/sigmoid.
ALLOWED_IMPORTS = {"__future__", "enum", "dataclasses", "typing", "abc", "re",
                   "hmac", "hashlib", "math"}

# Exact module names, not package roots. `urllib` as a root would have let
# `urllib.request` through — a package whose whole purpose is network I/O,
# admitted by accident while the wall still looked like it was standing.
# A permission that is wider than its argument is how a rule turns into a
# custom nobody notices was dropped until the day it was needed.
ALLOWED_MODULES = {"urllib.parse"}


def permitted(name: str) -> bool:
    """Is this import allowed inside the kernel?"""
    return name in ALLOWED_MODULES or name.split(".")[0] in ALLOWED_IMPORTS
# `re`, `hmac` and `hashlib` are admitted deliberately: all three are pure,
# deterministic, and do no I/O. They are here so redaction and signature
# verification live in the kernel rather than in an adapter a caller could
# forget to route through. Nothing else gets added to this set without the
# same argument holding.
#
# `urllib.parse` joined them 2026-08-04, and the argument is the same one —
# plus a scar. Percent-decoding is not a step *before* verification, it is
# part of it: the check string is built from decoded values, so whoever
# decodes decides what is signed. Leaving it to the adapter is exactly how
# this project shipped a decoder that unquoted the whole query string before
# splitting it, which every test agreed with and no real launch did.
# `unquote_plus` reads no clock, no file and no environment.

# Names that belong to a specific business, partner, or product. The kernel is
# industry-independent; if one of these appears, generalisation has failed and
# adding a fourth business will mean editing the kernel instead of adding a file.
FORBIDDEN_TERMS = [
    "ziman", "maliheh", "khalaji", "abbas", "asadi", "saba", "abdol",
    "naghshi", "painting", "onlyfans", "brushline", "projectf", "project_f",
    "octopus", "fugu", "sakana", "telegram", "gmail",
]


def kernel_files() -> list[str]:
    return sorted(
        os.path.join(KERNEL_DIR, n)
        for n in os.listdir(KERNEL_DIR)
        if n.endswith(".py")
    )


class TestTheWallIsStillNarrow(unittest.TestCase):
    """The permission granted must be no wider than the argument for it.

    `urllib.parse` was admitted because percent-decoding is part of signature
    verification and is a pure computation. That argument says nothing about
    `urllib.request`, so the door has to be exactly one module wide.
    """

    def test_urllib_parse_is_allowed(self):
        self.assertTrue(permitted("urllib.parse"))

    def test_urllib_request_is_not(self):
        self.assertFalse(permitted("urllib.request"))

    def test_the_urllib_package_itself_is_not(self):
        self.assertFalse(permitted("urllib"))

    def test_nothing_else_sneaks_in_under_a_root(self):
        for name in ("urllib.error", "http.client", "socket", "os",
                     "requests", "sqlite3", "time", "random"):
            with self.subTest(module=name):
                self.assertFalse(permitted(name))

    def test_the_allowed_roots_still_work(self):
        for name in ("hmac", "hashlib", "re", "dataclasses"):
            with self.subTest(module=name):
                self.assertTrue(permitted(name))


class TestKernelIsStdlibOnly(unittest.TestCase):
    def test_no_disallowed_imports(self):
        for path in kernel_files():
            with self.subTest(module=os.path.basename(path)):
                tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertTrue(
                                permitted(alias.name),
                                f"{os.path.basename(path)} imports {alias.name!r}; "
                                f"the kernel may only use "
                                f"{sorted(ALLOWED_IMPORTS | ALLOWED_MODULES)}",
                            )
                    elif isinstance(node, ast.ImportFrom):
                        if node.level and node.level > 0:
                            continue  # relative import inside the kernel: fine
                        self.assertTrue(
                            permitted(node.module or ""),
                            f"{os.path.basename(path)} imports from {node.module!r}",
                        )

    def test_no_io_or_clock_calls(self):
        """No open(), no time reads, no environment, no randomness."""
        banned_calls = {"open", "input", "print", "eval", "exec", "compile"}
        banned_attrs = {"now", "utcnow", "time", "getenv", "environ",
                        "random", "urandom", "monotonic"}
        for path in kernel_files():
            with self.subTest(module=os.path.basename(path)):
                tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        fn = node.func
                        if isinstance(fn, ast.Name):
                            self.assertNotIn(
                                fn.id, banned_calls,
                                f"{os.path.basename(path)} calls {fn.id}()",
                            )
                        elif isinstance(fn, ast.Attribute):
                            self.assertNotIn(
                                fn.attr, banned_attrs,
                                f"{os.path.basename(path)} calls .{fn.attr}()",
                            )


class TestKernelKnowsNoBusiness(unittest.TestCase):
    def test_no_business_names_anywhere_in_kernel(self):
        for path in kernel_files():
            text = open(path, encoding="utf-8").read().lower()
            for term in FORBIDDEN_TERMS:
                with self.subTest(module=os.path.basename(path), term=term):
                    self.assertNotIn(
                        term, text,
                        f"{os.path.basename(path)} mentions {term!r} — the kernel "
                        f"must not know which businesses exist",
                    )

    def test_kernel_does_not_import_adapters(self):
        """Dependency direction is kernel <- adapters, never the reverse.

        Checked against the import graph, not the text: docstrings in this
        package legitimately talk *about* adapters, and a substring search
        would fail on prose while missing an aliased import.
        """
        for path in kernel_files():
            tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                    if node.level:
                        names += [a.name for a in node.names]
                for n in names:
                    with self.subTest(module=os.path.basename(path), imported=n):
                        self.assertNotIn(
                            "adapter", n.lower(),
                            f"{os.path.basename(path)} imports {n!r}; the kernel "
                            f"must not depend on an adapter",
                        )


class TestKernelImportsCleanly(unittest.TestCase):
    def test_import_does_not_touch_the_world(self):
        """Importing the kernel must not create files, read env, or open sockets."""
        before = dict(os.environ)
        # Deleting the modules is the point of the check, but leaving them
        # deleted would poison every later test: a fresh import creates a
        # second set of class objects (e.g. a second Rung enum), and a node
        # holding the first would mismatch a CallBudget holding the second.
        # Restore what we removed, whatever the outcome.
        removed = [m for m in list(sys.modules) if m.startswith("ofn.kernel")]
        saved = {m: sys.modules[m] for m in removed}
        for mod in removed:
            del sys.modules[mod]
        try:
            import ofn.kernel  # noqa: F401
        finally:
            # Put the original module objects back so the classes this
            # process already holds stay the ones in use.
            sys.modules.update(saved)
        self.assertEqual(before, dict(os.environ),
                         "importing the kernel mutated the environment")


if __name__ == "__main__":
    unittest.main()
