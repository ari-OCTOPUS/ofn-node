#!/usr/bin/env python3
"""R-1 runner — first REAL restore drill (MP-ROOTFIX phase 2, from RCA-1).

Executes octopus_recovery/restore_drill.py end-to-end in DISPOSABLE temp
space only, with protected-roots guard armed, and emits RESTORE-DRILL-1.json.

Steps: fixture -> snapshot -> backup -> verify -> corrupt disposable copy
-> (corrupt-backup refusal proof) -> restore to FRESH dest -> independent
hash + ledger consistency -> guard-refusal proof -> verdict.
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from octopus_recovery.restore_drill import (  # noqa: E402
    DrillError, backup, build_fixture, corrupt, guard_target, restore,
    verify_backup, verify_restored)

PROTECTED = [
    r"F:\backup", r"F:\ofn-node", r"F:\wt-rootfix-20260916",
    r"C:\Users\Armin\.zcode",
]
os.environ["OCTOPUS_RESTORE_PROTECTED_ROOTS"] = os.pathsep.join(PROTECTED)

STEPS = {}


def step(name, fn):
    t0 = time.time()
    try:
        out = fn()
        STEPS[name] = {"ok": True, "ms": round((time.time() - t0) * 1000, 1),
                       "result": json.loads(json.dumps(out, default=str))}
        return out
    except DrillError as exc:
        STEPS[name] = {"ok": False, "refused": str(exc)[:200]}
        raise
    except Exception as exc:  # noqa: BLE001
        STEPS[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
        raise


def main() -> int:
    base = Path(tempfile.mkdtemp(prefix="octopus-restore-drill-r1-"))
    verdict = "FAIL"
    try:
        fixture_root = base / "fixture"
        backup_dir = base / "backup"
        work = base / "work"          # disposable copy that gets corrupted
        dest = base / "restored"      # FRESH restore destination

        fx = step("build_fixture", lambda: build_fixture(fixture_root))
        # snapshot the fixture state (pre-image)
        snap = step("snapshot",
                    lambda: {p.relative_to(fixture_root).as_posix():
                             (p.stat().st_size)
                             for p in sorted(fixture_root.rglob("*"))
                             if p.is_file()})
        step("backup", lambda: backup(fixture_root, backup_dir))
        step("verify_backup", lambda: verify_backup(backup_dir))
        # disposable copy of the fixture gets corrupted (NEVER the backup)
        step("make_disposable_copy",
             lambda: shutil.copytree(fixture_root, work))
        step("corrupt_disposable_copy",
             lambda: corrupt(work / "ledger.jsonl"))
        # fail-closed proof: a corrupted BACKUP entry must be refused
        bad_backup = base / "bad-backup"
        step("copy_backup_for_corruption_proof",
             lambda: shutil.copytree(backup_dir, bad_backup))
        corrupt(bad_backup / "ledger.jsonl")

        def _expect_refusal():
            try:
                restore(bad_backup, base / "dest-from-bad")
            except DrillError as exc:
                return {"refused_as_expected": str(exc)[:120]}
            raise DrillError("corrupt backup was NOT refused")
        step("corrupt_backup_refused", _expect_refusal)
        # the real restore from the good backup
        step("restore_to_fresh_dest", lambda: restore(backup_dir, dest))
        step("verify_restored", lambda: verify_restored(fixture_root, dest))

        def _guard_proof():
            try:
                guard_target(Path(r"F:\backup\some-restore-target"))
            except DrillError as exc:
                return {"protected_root_refused": str(exc)[:120]}
            raise DrillError("protected root was NOT refused")
        step("protected_root_guard_refused", _guard_proof)

        verdict = "PASS"
        return 0
    finally:
        receipt = {
            "schema": "restore-drill-receipt/1",
            "id": "RESTORE-DRILL-1",
            "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "order": "MP-ROOTFIX-EVIDENCE-EXECUTION-2026-09-16 R-1 (RCA-1)",
            "runner": "tools/run_restore_drill_r1.py",
            "module": "octopus_recovery/restore_drill.py (committed, not WIP)",
            "protected_roots_armed": PROTECTED,
            "disposable_root": str(base),
            "steps": STEPS,
            "verdict": verdict,
            "fail_condition": "any step not ok, or restored hash/ledger mismatch",
        }
        out = REPO / "rca" / "RESTORE-DRILL-1.json"
        out.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(json.dumps({"verdict": verdict, "steps": len(STEPS),
                          "all_ok": all(s.get("ok") for s in STEPS.values()),
                          "receipt": str(out)}))
        shutil.rmtree(base, ignore_errors=True)  # disposable only


if __name__ == "__main__":
    sys.exit(main())
