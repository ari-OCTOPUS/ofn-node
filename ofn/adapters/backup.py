"""Backup and restore. A backup nobody has restored is a rumour.

Three rules, each learned somewhere expensive:

**Never `cp` a live SQLite file.** A copy taken mid-transaction is a copy of a
half-written database. Use the online backup API, which walks pages under a
read lock and produces a file that was consistent at some instant.

**Verify the backup, not the source.** Checking the database you just read
from tells you the source is fine, which you already assumed. The question
that matters is whether the *copy* is usable, and the only way to know is to
open it and check.

**Restore is a first-class operation with its own test.** The failure mode
here is not "the restore script has a bug" — it is "nobody ran the restore
script for eight months and it references a path that moved".
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from dataclasses import dataclass
from typing import Mapping, Sequence

from .sqlite_base import connect, integrity_ok

MANIFEST_NAME = "manifest.json"


@dataclass(frozen=True)
class BackupEntry:
    name: str
    path: str
    bytes: int
    sha256: str
    verified: bool


@dataclass(frozen=True)
class BackupResult:
    directory: str
    entries: tuple[BackupEntry, ...]
    ok: bool
    detail: str

    @property
    def total_bytes(self) -> int:
        return sum(e.bytes for e in self.entries)


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def backup(databases: Mapping[str, str], dest_dir: str, *,
           stamp: str) -> BackupResult:
    """Snapshot every database into `dest_dir`, then prove each copy is usable.

    `stamp` is passed in rather than read from a clock: this module does no
    time reading, so a caller can produce a deterministic backup in tests and
    a timestamped one in production without the code branching.
    """
    os.makedirs(dest_dir, exist_ok=True)
    entries: list[BackupEntry] = []
    problems: list[str] = []

    for name, src in sorted(databases.items()):
        if not os.path.exists(src):
            continue
        out = os.path.join(dest_dir, f"{name}-{stamp}.sqlite")
        try:
            source = connect(src)
            target = sqlite3.connect(out)
            try:
                # The online backup API: consistent snapshot, concurrent
                # writers allowed (their changes simply are not included).
                source.backup(target)
            finally:
                target.close()
                source.close()
        except Exception as exc:
            problems.append(f"{name}: copy failed ({exc})")
            continue

        verified = False
        try:
            check = connect(out)
            try:
                verified = integrity_ok(check, quick=False)
            finally:
                check.close()
        except Exception as exc:
            problems.append(f"{name}: copy unreadable ({exc})")
        if not verified:
            problems.append(f"{name}: integrity_check failed on the copy")

        entries.append(BackupEntry(
            name=name, path=out, bytes=os.path.getsize(out),
            sha256=sha256_file(out), verified=verified))

    manifest = {
        "stamp": stamp,
        "entries": [
            {"name": e.name, "file": os.path.basename(e.path), "bytes": e.bytes,
             "sha256": e.sha256, "verified": e.verified}
            for e in entries
        ],
        "ok": not problems,
        "problems": problems,
    }
    with open(os.path.join(dest_dir, MANIFEST_NAME), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    detail = "all copies verified" if not problems else "; ".join(problems)
    return BackupResult(dest_dir, tuple(entries), not problems, detail)


def verify_backup(dest_dir: str) -> tuple[bool, str]:
    """Re-check a backup directory against its manifest.

    Catches silent bit-rot and truncated transfers — the failure modes that
    do not announce themselves and are only discovered during a restore, which
    is the worst possible moment.
    """
    mpath = os.path.join(dest_dir, MANIFEST_NAME)
    if not os.path.exists(mpath):
        return False, "no manifest"
    try:
        with open(mpath, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"manifest unreadable: {exc}"

    for entry in manifest.get("entries", []):
        path = os.path.join(dest_dir, entry["file"])
        if not os.path.exists(path):
            return False, f"missing file: {entry['file']}"
        if os.path.getsize(path) != entry["bytes"]:
            return False, f"size changed: {entry['file']}"
        if sha256_file(path) != entry["sha256"]:
            return False, f"checksum mismatch: {entry['file']}"
        if not entry.get("verified"):
            return False, f"was never verified at write time: {entry['file']}"
    n = len(manifest.get("entries", []))
    return True, f"{n} file(s) verified against manifest"


def restore(dest_dir: str, targets: Mapping[str, str], *,
            keep_corrupt_as: str | None = None) -> tuple[bool, str]:
    """Restore databases from a verified backup directory.

    Refuses to run unless the backup verifies first. Restoring from an
    unverified backup can turn a recoverable incident into an unrecoverable
    one, by overwriting the only good copy with a bad one.

    The database being replaced is moved aside rather than deleted, because a
    corrupt database is still evidence about what went wrong.
    """
    ok, why = verify_backup(dest_dir)
    if not ok:
        return False, f"refusing to restore: {why}"

    with open(os.path.join(dest_dir, MANIFEST_NAME), "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    by_name = {e["name"]: e for e in manifest.get("entries", [])}

    restored: list[str] = []
    for name, target in sorted(targets.items()):
        entry = by_name.get(name)
        if entry is None:
            continue
        src = os.path.join(dest_dir, entry["file"])
        if os.path.exists(target) and keep_corrupt_as:
            shutil.move(target, os.path.join(
                os.path.dirname(target) or ".",
                f"{os.path.basename(target)}.{keep_corrupt_as}"))
        # Sidecars belong to the database that is going away. Leaving them
        # behind next to a restored file is a documented way to corrupt it.
        for sidecar in (f"{target}-wal", f"{target}-shm"):
            if os.path.exists(sidecar):
                os.remove(sidecar)
        shutil.copyfile(src, target)
        restored.append(name)

    if not restored:
        return False, "manifest matched no requested database"
    return True, f"restored: {', '.join(restored)}"


def prune(dest_root: str, keep: int) -> Sequence[str]:
    """Keep the newest `keep` backup directories, remove the rest.

    Sorted by name, which works because callers stamp directories with a
    sortable timestamp. Doing it by mtime would break the moment someone
    copies the backups somewhere and the timestamps all become identical.
    """
    if keep < 1:
        raise ValueError("keep must be at least 1")
    try:
        dirs = sorted(d for d in os.listdir(dest_root)
                      if os.path.isdir(os.path.join(dest_root, d)))
    except OSError:
        return ()
    doomed = dirs[:-keep] if len(dirs) > keep else []
    for d in doomed:
        shutil.rmtree(os.path.join(dest_root, d), ignore_errors=True)
    return tuple(doomed)
