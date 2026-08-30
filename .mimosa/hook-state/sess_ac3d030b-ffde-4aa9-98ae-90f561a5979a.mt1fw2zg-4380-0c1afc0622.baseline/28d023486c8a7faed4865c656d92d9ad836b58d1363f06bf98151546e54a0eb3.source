#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_tests.py — run the agi2027_control unittest suite.

Exit code 0 on success, 1 on any failure.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent            # _ops/agi2027_control
OPS = HERE.parent                                  # _ops
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

suite = unittest.defaultTestLoader.discover(
    start_dir=str(HERE / "tests"),
    top_level_dir=str(OPS),
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
