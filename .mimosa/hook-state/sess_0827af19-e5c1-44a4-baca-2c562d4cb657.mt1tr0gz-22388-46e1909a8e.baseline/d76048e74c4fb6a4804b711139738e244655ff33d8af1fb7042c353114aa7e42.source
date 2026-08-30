"""A temp directory that is actually removed when the test finishes.

Sixteen test modules called `tempfile.mkdtemp()` and nothing ever deleted the
result. Each suite run left roughly seventeen hundred directories in `/tmp`,
which on this board is a 2 GB tmpfs; after some days there were 14,548 of them
holding 1.8 GB, tmpfs hit 93%, and the boot supervisor's disk check went
CRITICAL. Eight tests then failed — in `test_survival` and `test_schema_drift`,
which assert that boot reaches NORMAL mode. The suite had poisoned its own
environment, and the failures pointed at boot rather than at the leak.

`mkdtemp` is the wrong default for a test: it hands back a path and no owner.
This helper ties the directory to the test that asked for it.

Cleanup registration order matters. Call this first in `setUp`, so its removal
is registered before any store is opened; `addCleanup` runs last-in-first-out,
so every store closes before the directory holding it is removed.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest


def temp_dir(case: unittest.TestCase) -> str:
    """Make a temp directory owned by `case`, removed when the case ends.

    `ignore_errors` because a test that already failed must not be reported as
    a second, more confusing failure in teardown — the point here is to stop
    the leak, not to add a new way to go red.
    """
    path = tempfile.mkdtemp()
    case.addCleanup(shutil.rmtree, path, ignore_errors=True)
    return path
