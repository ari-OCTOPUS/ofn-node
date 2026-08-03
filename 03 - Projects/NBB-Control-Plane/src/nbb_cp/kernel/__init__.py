"""Kernel: pure domain logic. stdlib-only by invariant (enforced by tests/test_import_lint.py).

Nothing in this package may import third-party code, perform I/O, read the
clock, or read environment variables. All effects live in adapters; the kernel
only decides.
"""
