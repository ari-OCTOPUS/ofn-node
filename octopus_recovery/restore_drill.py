#!/usr/bin/env python3
"""W-D: disposable backup/restore drill.

Proves that a backup actually restores: deterministic fixture -> hash ->
backup -> verify manifest -> corrupt disposable copy -> restore to a FRESH
destination -> independent hash comparison -> schema/ledger consistency.

Hard boundaries (owner Q7=A, 2026-08-30):
- only disposable temporary directories are touched;
- protected roots are refused fail-closed (configured via the
  OCTOPUS_RESTORE_PROTECTED_ROOTS environment path-list: vaults, bare
  repositories, production state);
- path traversal inside a backup manifest is rejected;
- corrupt or missing backup entries are refused (hash mismatch), never
  silently skipped.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

SCHEMA = "restore-drill/1"
MANIFEST_NAME = "backup-manifest.json"

def _protected_roots() -> tuple:
    """Protected roots from OCTOPUS_RESTORE_PROTECTED_ROOTS (path-list).
    Deployment-specific private roots are never hardcoded here."""
    import os
    raw = os.environ.get("OCTOPUS_RESTORE_PROTECTED_ROOTS", "")
    return tuple(p for p in raw.split(os.pathsep) if p)


class DrillError(RuntimeError):
    """Refuse-before-touch failure (fail closed)."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(p: Path) -> str:
    return str(p.resolve()).lower().replace("/", "\\")


def guard_target(target: Path) -> None:
    # Containment by pathlib parents, not string prefixes: a Windows drive
    # root like F:\ normalizes to "f:\" and a startswith(r + "\") check
    # never matches its children (f:\x), so protecting a drive root used to
    # protect nothing. pathlib handles the anchor case natively.
    t = target.resolve()
    for root in _protected_roots():
        r = Path(root).resolve()
        if t == r or r in t.parents:
            raise DrillError(f"protected target refused: {target}")


def _safe_rel(rel: str) -> Path:
    if ".." in Path(rel).parts or Path(rel).is_absolute():
        raise DrillError(f"path traversal entry refused: {rel!r}")
    return Path(rel)


def build_fixture(root: Path, n_files: int = 12, n_ledger: int = 40) -> dict:
    """Deterministic disposable fixture: files + ordered ledger.jsonl."""
    root.mkdir(parents=True, exist_ok=True)
    for i in range(n_files):
        (root / f"data-{i:03d}.txt").write_text(
            f"drill-file-{i:03d}\n" + "x" * (i + 1), encoding="utf-8")
    ledger = root / "ledger.jsonl"
    with ledger.open("w", encoding="utf-8") as fh:
        for i in range(n_ledger):
            fh.write(json.dumps({"id": i, "seq": i * 2,
                                 "note": f"record-{i:03d}"}) + "\n")
    return {"root": root, "files": n_files, "ledger_records": n_ledger}


def backup(src: Path, backup_dir: Path) -> dict:
    """Copy fixture into backup_dir and write a hash manifest."""
    guard_target(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for p in sorted(src.rglob("*")):
        if p.is_file():
            rel = p.relative_to(src).as_posix()
            _safe_rel(rel)
            dest = backup_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            entries.append({"path": rel, "sha256": sha256_file(dest),
                            "bytes": dest.stat().st_size})
    manifest = {"schema": SCHEMA, "entries": entries,
                "fixture_sha256_root": None}
    manifest_path = backup_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def verify_backup(backup_dir: Path) -> dict:
    """Re-hash every manifest entry; refuse on any mismatch or missing file."""
    manifest_path = backup_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise DrillError(f"missing backup manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise DrillError("unknown backup manifest schema")
    for e in manifest["entries"]:
        f = backup_dir / _safe_rel(e["path"])
        if not f.is_file():
            raise DrillError(f"missing backup file: {e['path']}")
        if sha256_file(f) != e["sha256"]:
            raise DrillError(f"corrupt backup file (hash mismatch): {e['path']}")
    return {"verified_entries": len(manifest["entries"]),
            "total_bytes": sum(e["bytes"] for e in manifest["entries"])}


def restore(backup_dir: Path, dest: Path) -> dict:
    """Restore into a FRESH destination from the verified backup manifest."""
    guard_target(dest)
    if dest.exists() and any(dest.iterdir()):
        raise DrillError(f"restore destination not fresh: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((backup_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    for e in manifest["entries"]:
        src = backup_dir / _safe_rel(e["path"])
        if not src.is_file():
            raise DrillError(f"missing backup file: {e['path']}")
        if sha256_file(src) != e["sha256"]:
            raise DrillError(f"corrupt backup file (hash mismatch): {e['path']}")
        out = dest / _safe_rel(e["path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, out)
    return {"restored_files": len(manifest["entries"]),
            "dest": str(dest)}


def verify_restored(fixture_root: Path, dest: Path) -> dict:
    """Independent comparison: per-file hash equality + ledger consistency."""
    fixture_files = sorted(p.relative_to(fixture_root).as_posix()
                           for p in fixture_root.rglob("*") if p.is_file())
    restored_files = sorted(p.relative_to(dest).as_posix()
                            for p in dest.rglob("*")
                            if p.is_file() and p.name != MANIFEST_NAME)
    if fixture_files != restored_files:
        raise DrillError("restored file set differs from fixture")
    mismatches = [
        rel for rel in fixture_files
        if sha256_file(fixture_root / rel) != sha256_file(dest / rel)
    ]
    if mismatches:
        raise DrillError(f"restored hash mismatch: {mismatches[:3]}")
    ledger = dest / "ledger.jsonl"
    ids = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)              # malformed line -> ValueError
        ids.append(rec["id"])
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        raise DrillError("ledger ids not strictly increasing/unique")
    return {"hash_match": True, "files": len(fixture_files),
            "ledger_records": len(ids)}


def corrupt(path: Path) -> None:
    """Deterministic corruption of a DISPOSABLE copy (never the backup)."""
    data = bytearray(path.read_bytes())
    data[len(data) // 2] ^= 0xFF
    path.write_bytes(bytes(data))
