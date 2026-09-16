#!/usr/bin/env python3
"""run_tests.py — اجرای تست‌های mining_os با stdlib (بدونِ pytest).

اجرا:  python run_tests.py        (از داخلِ پوشهٔ mining_os)
یا:    python mining_os/run_tests.py   (از پوشهٔ والد)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)          # تا «import mining_os» کار کند
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(HERE, "tests"),
                            top_level_dir=PARENT, pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
