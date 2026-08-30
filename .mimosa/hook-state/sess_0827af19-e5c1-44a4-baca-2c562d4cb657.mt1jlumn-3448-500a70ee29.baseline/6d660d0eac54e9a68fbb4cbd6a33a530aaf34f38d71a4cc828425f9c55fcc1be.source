#!/usr/bin/env python3
"""wda_harness — sandbox موقتِ ایزوله برای تست‌های مرزِ ادغام."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG = _HERE.parent                       # world_discovery_action
_INTEGRATIONS = _PKG.parent               # _ops/integrations
_BRIDGE = _PKG.parents[1] / "action_bridge"
# ⚠️ ترتیب مهم است و درسِ همین جلسه است: هر دو پکیج فایلی به نامِ `contracts.py`
# دارند. اگر هر دو پوشه مسطح روی `sys.path` بروند، یکی دیگری را سایه می‌کند و
# `policy.py` ِ ما `contracts` ِ پل را می‌گیرد (ImportError واقعیِ ۲۰۲۶-۰۷-۳۰).
# راه‌حل: پکیجِ ادغام **دات‌دار** import می‌شود (importهای درونی‌اش نسبی‌اند)،
# و فقط پلِ اقدام مسطح می‌ماند — پس نامِ بارهٔ `contracts` مالِ پل است و بس.
for _p in (str(_INTEGRATIONS), str(_BRIDGE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FIXTURES = _PKG / "fixtures"
REAL_ARTIFACT = (_PKG.parents[1] / "world_discovery" / "artifacts"
                 / "world-discovery-latest.json")


def setup(name: str) -> dict:
    root = Path(tempfile.mkdtemp(prefix=f"wda-{name}-")).resolve()
    for sub in ("workspace", "receipts"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return {"root": root, "receipts": root / "receipts"}


def teardown(env: dict) -> None:
    shutil.rmtree(env["root"], ignore_errors=True)


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


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
