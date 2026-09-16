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
    # Media is counted rather than listed: hashing every image on an SBC
    # turns a nightly job into a long one, and a count is enough to notice a
    # tree that has silently stopped being copied.
    media_files: int = 0
    media_bytes: int = 0

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


def mirror_media(root: str, dest_dir: str) -> tuple[int, int]:
    """Copy the media tree beside the database copies.

    Photos live outside SQLite so that a 40 MB image does not turn every read
    of a row into a 40 MB read. The cost of that choice is this function: a
    backup of the databases alone restores a set of rows pointing at files
    that are not there, and for the studio leg those files *are* the content.

    Copies rather than links, and copies unconditionally. A cleverer
    incremental scheme is the right answer once there is enough media for it
    to matter; today there is none, and a backup whose correctness depends on
    change detection is a backup with a way to silently skip a file.

    Returns (files, bytes) so the caller can report what was taken.
    """
    if not os.path.isdir(root):
        return (0, 0)
    target = os.path.join(dest_dir, "media")
    files = written = 0
    for here, _, names in os.walk(root):
        rel = os.path.relpath(here, root)
        out_dir = target if rel == "." else os.path.join(target, rel)
        os.makedirs(out_dir, exist_ok=True)
        for name in names:
            if name.endswith(".part"):
                continue          # a write that was interrupted; not content
            src = os.path.join(here, name)
            shutil.copy2(src, os.path.join(out_dir, name))
            files += 1
            written += os.path.getsize(src)
    return (files, written)


def backup(databases: Mapping[str, str], dest_dir: str, *,
           stamp: str, media_root: str | None = None,
           required: Sequence[str] = ()) -> BackupResult:
    """Snapshot every database into `dest_dir`, then prove each copy is usable.

    `stamp` is passed in rather than read from a clock: this module does no
    time reading, so a caller can produce a deterministic backup in tests and
    a timestamped one in production without the code branching.

    `media_root` is optional only so that existing callers keep working. When
    it is given, the media tree is copied too and counted in the manifest —
    databases without their files restore to rows describing pictures that
    are gone.

    `required` names databases whose absence is a failure, not a skip. A
    database that is configured but missing on disk means something is wrong
    before the backup even ran; silently continuing would produce a backup
    that looks complete and restores to a world with rows missing.
    """
    os.makedirs(dest_dir, exist_ok=True)
    entries: list[BackupEntry] = []
    problems: list[str] = []

    for name, src in sorted(databases.items()):
        if not os.path.exists(src):
            if name in required:
                problems.append(f"{name}: configured but missing on disk")
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

    media_files = media_bytes = 0
    if media_root:
        try:
            media_files, media_bytes = mirror_media(media_root, dest_dir)
        except OSError as exc:
            problems.append(f"media: copy failed ({exc})")

    manifest = {
        "stamp": stamp,
        "entries": [
            {"name": e.name, "file": os.path.basename(e.path), "bytes": e.bytes,
             "sha256": e.sha256, "verified": e.verified}
            for e in entries
        ],
        # Counted, not hashed. Hashing every image on an SBC turns a nightly
        # job into a long one; the count is enough to notice a tree that
        # silently stopped being copied, which is the failure that matters.
        "media": {"files": media_files, "bytes": media_bytes,
                  "root": media_root or ""},
        "ok": not problems,
        "problems": problems,
    }
    with open(os.path.join(dest_dir, MANIFEST_NAME), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    detail = "all copies verified" if not problems else "; ".join(problems)
    return BackupResult(dest_dir, tuple(entries), not problems, detail,
                        media_files=media_files, media_bytes=media_bytes)


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

    # Media: the manifest records count + bytes of the media tree at backup
    # time. Verify them against what is actually on disk — a media tree that
    # silently stopped being copied is exactly the failure the count exists
    # to notice.
    media = manifest.get("media") or {}
    expected_files = media.get("files", 0)
    expected_bytes = media.get("bytes", 0)
    media_dir = os.path.join(dest_dir, "media")
    if expected_files:
        if not os.path.isdir(media_dir):
            return False, "media tree missing (manifest expects files)"
        actual_files = actual_bytes = 0
        for here, _, names in os.walk(media_dir):
            for name in names:
                p = os.path.join(here, name)
                actual_files += 1
                actual_bytes += os.path.getsize(p)
        if actual_files != expected_files:
            return False, (f"media count changed: manifest {expected_files}, "
                           f"on disk {actual_files}")
        if actual_bytes != expected_bytes:
            return False, (f"media bytes changed: manifest {expected_bytes}, "
                           f"on disk {actual_bytes}")

    n = len(manifest.get("entries", []))
    detail = f"{n} file(s) verified against manifest"
    if expected_files:
        detail += f", {expected_files} media file(s) verified"
    return True, detail


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


def restore_media(dest_dir: str, target_root: str) -> tuple[bool, str]:
    """Restore the media tree from a verified backup into target_root.

    Copies (not moves) the media directory into the target root, preserving
    the relative layout. The live media root is never replaced in place —
    the caller decides whether to point the node at the restored tree or
    merge it. Refuses to run unless the backup verifies first, same rule as
    `restore`.

    This is the code path; a live restore is a deliberate operator action
    covered by docs/runbooks/RESTORE.md, not something this function does
    implicitly.
    """
    ok, why = verify_backup(dest_dir)
    if not ok:
        return False, f"refusing to restore media: {why}"

    src = os.path.join(dest_dir, "media")
    if not os.path.isdir(src):
        return False, "backup contains no media tree"

    os.makedirs(target_root, exist_ok=True)
    files = bytes_copied = 0
    try:
        for here, _, names in os.walk(src):
            rel = os.path.relpath(here, src)
            out_dir = target_root if rel == "." else os.path.join(target_root, rel)
            os.makedirs(out_dir, exist_ok=True)
            for name in names:
                shutil.copy2(os.path.join(here, name),
                             os.path.join(out_dir, name))
                files += 1
                bytes_copied += os.path.getsize(os.path.join(here, name))
    except OSError as exc:
        return False, f"media restore failed: {exc}"
    return True, f"restored {files} media file(s), {bytes_copied} bytes"


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
