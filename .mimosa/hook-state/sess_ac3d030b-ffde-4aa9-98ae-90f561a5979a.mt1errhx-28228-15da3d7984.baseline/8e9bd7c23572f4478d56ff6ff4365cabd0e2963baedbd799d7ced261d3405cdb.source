#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_guard.py — scan + repair JSONL state files (quarantine-based, propose-only).

قرارداد (Seed Agent v1 — قدمِ ۱، ۲۰۲۶-۰۸-۰۸):
  · scan-only پیش‌فرض — repair فقط با arm token صریح (OCTOPUS_STATE_GUARD_ARM=1).
  · repair فقط روی allowlist صریح (REPAIR_TARGETS) — نه repair_all کور.
  · هیچ فایل حذف نمی‌شود — خطوطِ null/invalid به‌صورت raw bytes به `.quarantined`
    منتقل می‌شوند و فایل اصلی atomic rewrite می‌شود (tmp+fsync+replace+retry).
  · هر repair یک receipt با sha256 قبل/بعد، timestamp، و متادیتای forensic می‌نویسد.
  · receipts به فایلِ جدا `state_guard-receipts.jsonl` می‌رود — هرگز به effect-shadow.
  · maintenance lock قبل از repair set می‌شود تا race condition با writerهای زنده نباشد.

Patch‌های Kimi K3 (۲۰۲۶-۰۸-۰۸) اعمال‌شده (۶ patch):
  ۱. _atomic_rewrite: last_error به‌جای bare raise.
  ۲. repair_known_targets: allowlist صریح به‌جای repair_all.
  ۳. sha256_before قبل از rewrite محاسبه می‌شود.
  ۴. arm gate: repair بدون OCTOPUS_STATE_GUARD_ARM=1 رد می‌شود.
  ۵. receipt: schema + sha256_before + mode + operator + quarantine meta.
  ۶. maintenance lock: repair قبل از شروع lock را set می‌کند.

CLI:
  python -X utf8 _ops/state_guard.py --scan
  $env:OCTOPUS_STATE_GUARD_ARM = "1"
  python -X utf8 _ops/state_guard.py --repair-known-targets
  Remove-Item Env:OCTOPUS_STATE_GUARD_ARM
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    from budget import opslib  # noqa: E402
    STATE_ROOT = opslib.STATE_DIR
except Exception:  # noqa: BLE001 — standalone-safe
    opslib = None  # type: ignore
    STATE_ROOT = _HERE / "state"

RECEIPTS = STATE_ROOT / "state_guard-receipts.jsonl"
MAINTENANCE_LOCK = STATE_ROOT / "maintenance-lock.json"
QUAR_SUFFIX = ".quarantined"
QUAR_META_SUFFIX = ".meta.json"
ARM_ENV = "OCTOPUS_STATE_GUARD_ARM"

# allowlist صریح — فقط این فایل‌ها (تأییدشده با scan_all زنده) repair می‌شوند.
# saba-bridge.jsonl عمداً اینجا نیست: خطوطِ invalid آن کامنت (#) هستند، نه corrupt.
REPAIR_TARGETS = {
    "cortex/calibration-log.jsonl",
    "cortex/route-decisions.jsonl",
    "pulse/arbiter-shadow.jsonl",
    "pulse/fuel-stream.jsonl",
    "pulse/tick-timing.jsonl",
    "reach/ledger.jsonl",
    # 2026-08-08: miniapp-hits — ۳ خطِ شکسته (crash mid-write)
    "telegram/miniapp-hits.jsonl",
}


@dataclass
class ScanResult:
    path: str
    total: int = 0
    valid: int = 0
    null_lines: int = 0
    invalid_json: int = 0
    sha256: str = ""


@dataclass
class RepairResult:
    path: str
    quarantined_to: str = ""
    removed_null: int = 0
    removed_invalid: int = 0
    kept_valid: int = 0
    valid_before: int = 0
    sha256_before: str = ""
    sha256_after: str = ""
    ok: bool = False
    error: str = ""


# ─── helpers ────────────────────────────────────────────────────────────────
def _sha256(p: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def _iter_raw_lines(p: Path) -> Iterator[bytes]:
    with open(p, "rb") as fh:
        for line in fh:
            yield line


def _is_armed() -> bool:
    return os.environ.get(ARM_ENV, "0") == "1"


# ─── maintenance lock ───────────────────────────────────────────────────────
def set_maintenance_lock(targets: list[str], reason: str = "jsonl repair") -> None:
    """set maintenance lock — writerهای زنده باید این فایل را قبل از write بخوانند.
    اگر lock فعال باشد، repair در حال انجام است و نباید هم‌زمان نوشته شود."""
    MAINTENANCE_LOCK.parent.mkdir(parents=True, exist_ok=True)
    lock = {
        "schema": "MaintenanceLock.v1",
        "active": True,
        "owner": "state_guard",
        "reason": reason,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "targets": targets,
    }
    tmp = MAINTENANCE_LOCK.with_suffix(".tmp")
    tmp.write_text(json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(MAINTENANCE_LOCK))


def release_maintenance_lock() -> None:
    """release maintenance lock — repair تمام شده، writerها می‌توانند بنویسند."""
    try:
        if MAINTENANCE_LOCK.exists():
            MAINTENANCE_LOCK.unlink()
    except OSError:
        pass


def is_maintenance_locked() -> bool:
    try:
        if not MAINTENANCE_LOCK.exists():
            return False
        d = json.loads(MAINTENANCE_LOCK.read_text("utf-8"))
        return bool(d.get("active"))
    except (OSError, ValueError):
        return False


# ─── scan ───────────────────────────────────────────────────────────────────
def scan_jsonl(path: Path) -> ScanResult:
    r = ScanResult(path=str(path))
    if not path.exists():
        return r
    r.sha256 = _sha256(path)
    for raw in _iter_raw_lines(path):
        stripped = raw.strip()
        # خطِ کامنت (# در ابتدا) یا خطِ خالی = نه valid نه invalid.
        # saba-bridge.jsonl و چند فایلِ دیگر header comment دارند — این‌ها
        # corruption نیستند، قراردادِ عمدی‌اند. بی‌صدا نادیده گرفته می‌شوند.
        if stripped and stripped[:1] in (b"#", b"//"):
            r.total += 1   # شمار می‌شود ولی نه corrupt
            continue
        if not stripped:
            r.total += 1
            continue
        r.total += 1
        if b"\x00" in raw:
            r.null_lines += 1
            continue
        try:
            json.loads(raw.decode("utf-8"))
            r.valid += 1
        except (ValueError, UnicodeDecodeError):
            r.invalid_json += 1
    return r


def scan_all(root: "Path | None" = None) -> list[ScanResult]:
    root = root or STATE_ROOT
    out: list[ScanResult] = []
    if not root.exists():
        return out
    for p in sorted(root.rglob("*.jsonl")):
        if p.name == RECEIPTS.name:
            continue
        out.append(scan_jsonl(p))
    return out


# ─── repair ─────────────────────────────────────────────────────────────────
def _atomic_rewrite(path: Path, lines: list[bytes]) -> None:
    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".sg_", suffix=".tmp"
    )
    last_error: "PermissionError | None" = None
    try:
        with os.fdopen(tmp_fd, "wb") as fh:
            for line in lines:
                fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        for attempt in range(5):
            try:
                os.replace(tmp_name, str(path))
                return
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.05 * (attempt + 1))
        raise last_error or OSError(f"atomic replace failed: {path}")
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def _write_receipt(record: dict) -> None:
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    enriched = {
        "schema": "StateGuardReceipt.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "epoch": time.time(),
        "operator": "state_guard",
        "mode": "quarantine_then_atomic_replace",
        **record,
    }
    with open(RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(enriched, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _write_quarantine_meta(qpath: Path, source: Path, res: RepairResult) -> None:
    meta = {
        "schema": "StateGuardQuarantineMeta.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_file": str(source),
        "removed_null": res.removed_null,
        "removed_invalid": res.removed_invalid,
    }
    mpath = qpath.with_name(qpath.name + QUAR_META_SUFFIX)
    try:
        mpath.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def repair_jsonl(path: Path) -> RepairResult:
    res = RepairResult(path=str(path))
    if not path.exists():
        res.ok, res.error = True, "missing"
        _write_receipt({"action": "repair_jsonl", "target": str(path),
                        "sha256_before": "", "repair": asdict(res)})
        return res

    sha_before = _sha256(path)
    res.sha256_before = sha_before

    try:
        keep: list[bytes] = []
        quar: list[bytes] = []
        for raw in _iter_raw_lines(path):
            stripped = raw.strip()
            # خطِ کامنت یا خالی = نگه‌دار (نه valid، نه corrupt — قراردادِ عمدی)
            if not stripped or stripped[:1] in (b"#", b"//"):
                keep.append(raw)
                continue
            if b"\x00" in raw:
                res.removed_null += 1
                quar.append(raw)
            else:
                try:
                    json.loads(raw.decode("utf-8"))
                    keep.append(raw)
                except (ValueError, UnicodeDecodeError):
                    res.removed_invalid += 1
                    quar.append(raw)

        res.kept_valid = len(keep)

        if quar:
            qpath = path.with_name(
                path.name + QUAR_SUFFIX + "." + time.strftime("%Y%m%dT%H%M%S")
            )
            with open(qpath, "wb") as fh:
                for ln in quar:
                    fh.write(ln)
            res.quarantined_to = str(qpath)
            _write_quarantine_meta(qpath, path, res)

        _atomic_rewrite(path, keep)
        res.sha256_after = _sha256(path)
        res.ok = True
    except Exception as e:  # noqa: BLE001
        res.error = repr(e)

    _write_receipt({"action": "repair_jsonl", "target": str(path),
                    "sha256_before": sha_before, "repair": asdict(res)})
    return res


def repair_known_targets(root: "Path | None" = None) -> list[RepairResult]:
    root = root or STATE_ROOT
    results: list[RepairResult] = []
    for relative_path in sorted(REPAIR_TARGETS):
        path = root / relative_path
        if not path.exists():
            results.append(RepairResult(path=str(path), ok=True, error="missing-target"))
            continue
        pre_scan = scan_jsonl(path)
        r = repair_jsonl(path)
        r.valid_before = pre_scan.valid
        results.append(r)
    return results


# ─── CLI ────────────────────────────────────────────────────────────────────
def _cmd_scan() -> int:
    results = scan_all()
    corrupt = [r for r in results if r.null_lines or r.invalid_json]
    for r in results:
        tag = ""
        if r.null_lines:
            tag += f" ⚠️ {r.null_lines} null"
        if r.invalid_json:
            tag += f" ⚠️ {r.invalid_json} invalid"
        print(f"  {r.path}: total={r.total} valid={r.valid}{tag}")
    print(f"\n{len(results)} files scanned, {len(corrupt)} corrupt.")
    if is_maintenance_locked():
        print("⚠️ MAINTENANCE LOCK ACTIVE — writers should pause.")
    return 0


def _cmd_repair() -> int:
    if not _is_armed():
        raise SystemExit(
            f"Refusing repair: set {ARM_ENV}=1 explicitly.\n"
            f"  powershell: $env:{ARM_ENV} = \"1\""
        )
    # maintenance lock set — race condition prevention
    targets_sorted = sorted(REPAIR_TARGETS)
    set_maintenance_lock(targets_sorted)
    print(f"🔒 Maintenance lock set ({MAINTENANCE_LOCK})")
    try:
        results = repair_known_targets()
    finally:
        release_maintenance_lock()
    print(f"🔓 Maintenance lock released")

    for r in results:
        status = "✅" if r.ok else "❌"
        detail = ""
        if r.removed_null:
            detail += f" null={r.removed_null}"
        if r.removed_invalid:
            detail += f" invalid={r.removed_invalid}"
        if r.quarantined_to:
            detail += " → quarantine"
        if r.error and r.error not in ("missing-target",):
            detail += f" err={r.error}"
        if r.ok and r.error != "missing-target":
            if r.valid_before != r.kept_valid:
                detail += f" ⚠️ valid {r.valid_before}→{r.kept_valid} (DATA LOSS!)"
            else:
                detail += f" ✓ valid preserved ({r.kept_valid})"
        print(f"  {status} {r.path}:{detail}")
    ok = sum(1 for r in results if r.ok)
    print(f"\n{ok}/{len(results)} repaired. Receipts → {RECEIPTS}")
    return 0 if all(r.ok for r in results) else 1


def main() -> int:
    p = argparse.ArgumentParser(description="StateGuard: scan/repair JSONL state files.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan", action="store_true", help="Scan all state JSONL files (read-only).")
    g.add_argument("--repair-known-targets", action="store_true",
                   help="Repair only the 6 known corrupt targets (requires OCTOPUS_STATE_GUARD_ARM=1).")
    args = p.parse_args()
    if args.scan:
        return _cmd_scan()
    return _cmd_repair()


if __name__ == "__main__":
    raise SystemExit(main())
