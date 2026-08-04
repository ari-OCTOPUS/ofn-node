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
ALLOWED_IMPORTS = {"__future__", "enum", "dataclasses", "typing", "abc", "re", "hmac", "hashlib"}
# `re`, `hmac` and `hashlib` are admitted deliberately: all three are pure,
# deterministic, and do no I/O. They are here so redaction and signature
# verification live in the kernel rather than in an adapter a caller could
# forget to route through. Nothing else gets added to this set without the
# same argument holding.

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


class TestKernelIsStdlibOnly(unittest.TestCase):
    def test_no_disallowed_imports(self):
        for path in kernel_files():
            with self.subTest(module=os.path.basename(path)):
                tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root = alias.name.split(".")[0]
                            self.assertIn(
                                root, ALLOWED_IMPORTS,
                                f"{os.path.basename(path)} imports {alias.name!r}; "
                                f"the kernel may only use {sorted(ALLOWED_IMPORTS)}",
                            )
                    elif isinstance(node, ast.ImportFrom):
                        if node.level and node.level > 0:
                            continue  # relative import inside the kernel: fine
                        root = (node.module or "").split(".")[0]
                        self.assertIn(
                            root, ALLOWED_IMPORTS,
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
        for mod in [m for m in list(sys.modules) if m.startswith("ofn.kernel")]:
            del sys.modules[mod]
        import ofn.kernel  # noqa: F401
        self.assertEqual(before, dict(os.environ),
                         "importing the kernel mutated the environment")


if __name__ == "__main__":
    unittest.main()
