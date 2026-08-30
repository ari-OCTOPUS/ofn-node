#!/usr/bin/env python3
"""W-D: disposable restore drill tests.

Full happy path (fixture -> backup -> verify -> corrupt disposable copy ->
restore to fresh destination -> independent hash comparison -> ledger
consistency) plus fail-closed modes: missing backup file, corrupt backup
(hash mismatch), path traversal in manifest, refusal of protected targets,
non-fresh destination. Everything runs under temporary directories only.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from octopus_recovery import restore_drill as rd  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    assert cond, f"{name}: {detail}"


def expect_raises(name: str, fn, *a, **kw):
    try:
        fn(*a, **kw)
        check(name, False, "no exception raised")
    except rd.DrillError:
        check(name, True)
    except Exception as e:  # noqa: BLE001
        check(name, False, f"wrong exception {type(e).__name__}: {e}")


def test_full_drill():
    print("[1] full disposable drill")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fixture = tmp_path / "fixture"
        spec = rd.build_fixture(fixture)
        check("fixture built",
              spec["files"] == 12 and spec["ledger_records"] == 40)

        backup_dir = tmp_path / "backup"
        manifest = rd.backup(fixture, backup_dir)
        check("backup manifest entries", manifest and len(manifest["entries"]) == 13,
              str(len(manifest.get("entries", []))))
        v = rd.verify_backup(backup_dir)
        check("backup verified", v["verified_entries"] == 13)

        # damage a DISPOSABLE copy of the fixture (simulated data loss);
        # the backup and the restore path never touch it
        damaged = tmp_path / "damaged-copy"
        damaged.mkdir()
        (damaged / "data-005.txt").write_text("important-live-data", encoding="utf-8")
        rd.corrupt(damaged / "data-005.txt")
        check("disposable copy damaged",
              (damaged / "data-005.txt").read_bytes()
              != b"important-live-data")

        dest = tmp_path / "restored"
        r = rd.restore(backup_dir, dest)
        check("restore count", r["restored_files"] == 13, str(r))
        vr = rd.verify_restored(fixture, dest)
        check("independent hash match", vr["hash_match"] is True)
        check("ledger consistency", vr["ledger_records"] == 40)


def test_missing_backup_file():
    print("[2] missing backup entry refuses")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fixture = tmp_path / "fixture"
        rd.build_fixture(fixture, n_files=3, n_ledger=5)
        backup_dir = tmp_path / "backup"
        rd.backup(fixture, backup_dir)
        victim = backup_dir / "data-001.txt"
        victim.unlink()
        expect_raises("missing entry", rd.verify_backup, backup_dir)
        expect_raises("missing entry on restore", rd.restore, backup_dir,
                      tmp_path / "fresh")


def test_corrupt_backup_detected():
    print("[3] corrupt backup refuses (hash mismatch)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fixture = tmp_path / "fixture"
        rd.build_fixture(fixture, n_files=3, n_ledger=5)
        backup_dir = tmp_path / "backup"
        rd.backup(fixture, backup_dir)
        rd.corrupt(backup_dir / "data-002.txt")
        expect_raises("corrupt detected", rd.verify_backup, backup_dir)


def test_path_traversal_rejected():
    print("[4] manifest path traversal rejected")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fixture = tmp_path / "fixture"
        rd.build_fixture(fixture, n_files=2, n_ledger=3)
        backup_dir = tmp_path / "backup"
        rd.backup(fixture, backup_dir)
        manifest_path = backup_dir / rd.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["entries"].append({"path": "../evil.txt", "sha256": "0" * 64,
                                    "bytes": 1})
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        expect_raises("traversal refused", rd.verify_backup, backup_dir)
        expect_raises("traversal refused on restore", rd.restore, backup_dir,
                      tmp_path / "fresh2")


def test_protected_targets_refused():
    print("[5] protected roots refused")
    import os
    key = "OCTOPUS_RESTORE_PROTECTED_ROOTS"
    saved = os.environ.get(key)
    root = Path.cwd()
    os.environ[key] = str(root) + os.pathsep + str(root.parent)
    try:
        expect_raises("protected root", rd.guard_target, root)
        expect_raises("protected child", rd.guard_target, root / "state")
        expect_raises("protected parent-path", rd.guard_target, root.parent / "x")
    finally:
        if saved is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = saved

def test_non_fresh_destination_refused():
    print("[6] non-fresh destination refused")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fixture = tmp_path / "fixture"
        rd.build_fixture(fixture, n_files=2, n_ledger=3)
        backup_dir = tmp_path / "backup"
        rd.backup(fixture, backup_dir)
        busy = tmp_path / "busy"
        busy.mkdir()
        (busy / "occupied.txt").write_text("x", encoding="utf-8")
        expect_raises("non-fresh dest", rd.restore, backup_dir, busy)


def main() -> int:
    for fn in (
        test_full_drill,
        test_missing_backup_file,
        test_corrupt_backup_detected,
        test_path_traversal_rejected,
        test_protected_targets_refused,
        test_non_fresh_destination_refused,
    ):
        fn()
    if FAILURES:
        print(f"\nRESTORE-DRILL: {len(FAILURES)} failure(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nRESTORE-DRILL: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
