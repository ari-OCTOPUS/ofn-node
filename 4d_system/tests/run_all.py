#!/usr/bin/env python3
"""اجرای کلِ سوییت بدونِ pytest:  python tests/run_all.py

خروجی: exit 0 = همه سبز، exit 1 = دست‌کم یک شکست.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests import _bootstrap  # noqa: F401,E402

suite = unittest.defaultTestLoader.discover(
    str(ROOT / "tests"), top_level_dir=str(ROOT))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
