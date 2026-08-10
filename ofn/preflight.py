"""Pre-flight CLI. Exit 0 = normal, 2 = SAFE MODE, 1 = could not even check.

Exit 2 rather than 1 for SAFE MODE so the systemd unit can treat it as a
recorded outcome rather than a failure — the node is meant to come up
degraded, not to be restarted in a loop.
"""

from __future__ import annotations

import os
import stat
import sys

from . import config
from .adapters.boot import BootSupervisor, Mode
from .adapters.ledger import Ledger
from .adapters.outbox import Outbox
from .adapters.packloader import load_dir
from .kernel.tenancy import TenantRegistry


def _check_state_dir_mode(path: str) -> list[str]:
    """Warn if the state directory is more permissive than 0700.

    This does NOT chmod — correcting the mode is a deliberate operator action.
    The check surfaces the problem so it can be fixed consciously.
    """
    warnings = []
    if not os.path.exists(path):
        return warnings
    mode = stat.S_IMODE(os.stat(path).st_mode)
    if mode != 0o700:
        warnings.append(
            f"state dir {path} has mode {oct(mode)} (expected 0700). "
            f"Run: chmod 0700 {path}")
    return warnings


def main() -> int:
    cfg = config.load()
    os.makedirs(cfg.state_dir, exist_ok=True)

    # Check permissions before anything else — a world-readable state dir
    # is a data-leak risk that boot checks do not cover.
    for warning in _check_state_dir_mode(cfg.state_dir):
        print(f"[ warn ] {warning}", file=sys.stderr)
    try:
        packs = load_dir(cfg.packs_dir)
        registry = TenantRegistry(packs)
    except Exception as exc:
        print(f"preflight: cannot load packs: {exc}", file=sys.stderr)
        return 1

    ledger = Ledger(cfg.ledger_path) if os.path.exists(cfg.ledger_path) else None
    outbox = Outbox(cfg.outbox_path) if os.path.exists(cfg.outbox_path) else None
    sup = BootSupervisor(db_paths=cfg.db_paths, tenants=list(registry),
                         now_epoch_s=config.epoch_seconds,
                         state_dir=cfg.state_dir)
    report = sup.run(ledger=ledger, outbox=outbox, now_iso=config.now_iso())
    for store in (ledger, outbox):
        if store is not None:
            store.close()

    print(report.summary())
    for check in report.checks:
        mark = {"ok": "  ok  ", "warn": " warn ", "critical": " CRIT "}[
            check.severity.value]
        print(f"[{mark}] {check.name}: {check.detail}")
    return 2 if report.mode is Mode.SAFE else 0


if __name__ == "__main__":
    raise SystemExit(main())
