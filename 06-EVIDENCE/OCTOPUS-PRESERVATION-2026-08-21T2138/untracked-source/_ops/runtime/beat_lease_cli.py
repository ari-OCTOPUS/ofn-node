# -*- coding: utf-8 -*-
"""
ابزار خط فرمان lease — چیزی که ساعت ۲ صبح لازم داری.

    python -m _ops.runtime.beat_lease_cli status
    python -m _ops.runtime.beat_lease_cli freeze   "reason"
    python -m _ops.runtime.beat_lease_cli unfreeze

مسیرها با متغیر محیطی قابل تغییرند:
    OCTOPUS_LEASE_PATH   (پیش‌فرض _ops/state/octopus.lease)
    OCTOPUS_FREEZE_PATH  (پیش‌فرض _ops/state/BEAT-FREEZE.flag)

این CLI نبض زنده را روشن نمی‌کند. freeze فقط وقتی اثر دارد که حلقهٔ beat
`assert_valid()` را صدا بزند — امروز هنوز رأی سیم لازم است.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from .beat_lease import FileLeaseStore

_OPS = Path(__file__).resolve().parents[1]
LEASE_PATH = Path(os.environ.get("OCTOPUS_LEASE_PATH", str(_OPS / "state" / "octopus.lease")))
FREEZE_PATH = Path(os.environ.get("OCTOPUS_FREEZE_PATH", str(_OPS / "state" / "BEAT-FREEZE.flag")))


def cmd_status() -> int:
    store = FileLeaseStore(LEASE_PATH)
    rec = store.read()
    frozen = FREEZE_PATH.exists()

    print(f"lease file : {LEASE_PATH}")
    print(f"freeze     : {'YES — nobody may beat' if frozen else 'no'}")

    if rec is None:
        print("state      : NO LEASE (fresh system, or file removed)")
        print("state      : VACANT — free to take")
        return 0
    if rec.vacant:
        print(f"state      : VACANT (last revision {rec.revision}) — free to take")
        return 0

    left = rec.expires_wall - time.time()
    print(f"owner      : {rec.owner}  @ {rec.host}  pid={rec.pid}")
    print(f"holder_id  : {rec.holder_id}")
    print(f"revision   : {rec.revision}   ← fencing token")
    print(f"expires in : {left:+.1f}s")
    if left < 0:
        print("state      : EXPIRED — another host may take over")
        return 2
    print("state      : HELD — do NOT start a second organism")
    return 0


def cmd_freeze(reason: str) -> int:
    FREEZE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FREEZE_PATH.write_text(
        f"frozen_at={time.strftime('%Y-%m-%dT%H:%M:%S%z')}\nreason={reason}\n",
        encoding="utf-8",
    )
    print(f"FROZEN. هیچ میزبانی beat نمی‌زند تا unfreeze.\n  {FREEZE_PATH}")
    return 0


def cmd_unfreeze() -> int:
    if FREEZE_PATH.exists():
        FREEZE_PATH.unlink()
        print("unfrozen.")
    else:
        print("already unfrozen.")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, *rest = argv
    if cmd == "status":
        return cmd_status()
    if cmd == "freeze":
        return cmd_freeze(rest[0] if rest else "manual")
    if cmd == "unfreeze":
        return cmd_unfreeze()
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
