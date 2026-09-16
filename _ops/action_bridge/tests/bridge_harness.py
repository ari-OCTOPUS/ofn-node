#!/usr/bin/env python3
"""bridge_harness — sandbox موقتِ کاملاً ایزوله برای تست‌های پلِ اقدام.

عمداً از `_ops/tests/harness.py` استفاده **نمی‌کند**: آن هارنس یک مینی-vault
می‌سازد و `ORG_ROOT`/`OPS_DIR` را ست می‌کند، یعنی به قراردادِ ارگانیسم گره
می‌خورد. پلِ اقدام هیچ وابستگی‌ای به آن ندارد و نباید پیدا کند — این‌جا فقط یک
پوشهٔ موقت لازم است.

هیچ تستی نباید بیرون از `root` بنویسد؛ بندِ اولِ هر فایلِ تست همین را می‌سنجد.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG = _HERE.parent                      # _ops/action_bridge
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))        # ماژول‌ها هم‌سطح import می‌شوند


def setup(name: str) -> dict:
    root = Path(tempfile.mkdtemp(prefix=f"abridge-{name}-")).resolve()
    for sub in ("workspace", "reports", "receipts", "fixtures"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return {"root": root,
            "receipts": root / "receipts",
            "ledger": root / "receipts" / "ledger.jsonl",
            "workspace": root / "workspace"}


def teardown(env: dict) -> None:
    try:
        shutil.rmtree(env["root"], ignore_errors=True)
    except OSError:
        pass


def run(checks) -> int:
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    return failed
