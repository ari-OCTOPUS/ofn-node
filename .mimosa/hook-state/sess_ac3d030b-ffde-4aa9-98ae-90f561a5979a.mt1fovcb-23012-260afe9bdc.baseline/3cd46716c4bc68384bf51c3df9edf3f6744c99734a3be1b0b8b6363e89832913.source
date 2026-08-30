#!/usr/bin/env python3
"""baseline.py — ضبط و مقایسهٔ snapshot قبل/بعد از هر فاز.

فاز ۰ زیرساخت ایمنی: بدون baseline قابل‌بازگشت، هیچ تغییری اثبات‌پذیر نیست.

API:
  capture_baseline(phase_id, label, state_dir) -> str  (مسیر فایل)
  compare_baseline(baseline_path, state_dir) -> dict
  pre_register_metric(phase_id, metric_name, threshold, direction, state_dir)
  check_pre_registered(phase_id, state_dir, current_snapshot) -> dict

طراحی: stdlib-only، $0، بدون side-effect روی production.
فایل‌ها: state_dir/baseline-<phase>-<ts>.json + state_dir/phase-metrics.jsonl
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

# ─── fields کلیدی که در هر snapshot ذخیره و مقایسه می‌شوند ──────────────────────
SNAPSHOT_FIELDS = (
    "halted", "frozen", "stop_organism",
    "conflicts", "suspect_zero_total",
    "germline_lag_h", "germline_alert",
    "sigma_effective", "sigma_zone",
    "fitness_authoritative",
    "month", "today",
    "last_epoch", "pressure", "next_epoch_minutes",
)

# فایل‌های پولی که fingerprint می‌گیریم (همان الگوی capability_gate)
MONEY_SOURCE_FILES = (
    "budget/money_gate.py",
    "budget/capability_gate.py",
    "budget/organ_gate.py",
    "budget/budget_gate.py",
    "budget/fitness.py",
)


def _read_json_safe(path: Path) -> dict | None:
    """خواندن JSON با fail-soft."""
    try:
        if path.is_file():
            return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _fingerprint_money_sources(ops_dir: Path) -> str:
    """SHA-256 fingerprint فایل‌های پول (فقط‌خواندنی)."""
    parts: list[str] = []
    for rel in sorted(MONEY_SOURCE_FILES):
        p = ops_dir / rel
        if p.is_file():
            parts.append(f"{rel}:{hashlib.sha256(p.read_bytes()).hexdigest()}")
    blob = "|".join(parts)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def _take_snapshot(state_dir: Path, ops_dir: Path) -> dict:
    """snapshotِ فعلی از ORGANISM-STATE + fitness + telemetry."""
    state = _read_json_safe(state_dir / "ORGANISM-STATE.json") or {}
    fitness = _read_json_safe(state_dir / "fitness-latest.json") or {}

    # فقط fields کلیدی
    snap: dict[str, Any] = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    for f in SNAPSHOT_FIELDS:
        if f in state:
            snap[f] = state[f]

    # fitness per-cell (خلاصه)
    if "cells" in fitness:
        snap["fitness_cells"] = {
            k: round(v.get("fit", 0), 4) if isinstance(v, dict) else v
            for k, v in fitness["cells"].items()
            if isinstance(v, dict)
        }
    else:
        snap["fitness_cells"] = {}

    # money fingerprint
    snap["money_fingerprint"] = _fingerprint_money_sources(ops_dir)
    return snap


def capture_baseline(phase_id: str, label: str,
                      state_dir: Path | str | None = None,
                      ops_dir: Path | str | None = None) -> str:
    """ضبط snapshot + metadata و ذخیره در فایل JSON.

    خروجی: مسیر فایلِ ذخیره‌شده.
    هر baseline فایلِ جداگانه — append-only، هرگز overwrite نمی‌شود."""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)
    if ops_dir is None:
        ops_dir = Path(__file__).resolve().parent
    else:
        ops_dir = Path(ops_dir)

    state_dir.mkdir(parents=True, exist_ok=True)

    snap = _take_snapshot(state_dir, ops_dir)
    ts = snap["iso"].replace(":", "-")
    fname = f"baseline-{phase_id}-{label}-{ts}.json"
    fpath = state_dir / fname

    doc = {
        "phase_id": phase_id,
        "label": label,
        "snapshot": snap,
    }
    fpath.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
    return str(fpath)


def compare_baseline(baseline_path: str | Path,
                     state_dir: Path | str | None = None,
                     ops_dir: Path | str | None = None) -> dict:
    """مقایسهٔ snapshotِ ذخیره‌شده با وضعیت فعلی.

    خروجی: {passed, diffs: [{field, before, after}], verdict, money_changed}"""
    baseline_path = Path(baseline_path)
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)
    if ops_dir is None:
        ops_dir = Path(__file__).resolve().parent
    else:
        ops_dir = Path(ops_dir)

    doc = _read_json_safe(baseline_path)
    if doc is None:
        return {"passed": False, "diffs": [], "verdict": "baseline-file-not-found",
                "money_changed": False}

    old_snap = doc.get("snapshot", {})
    new_snap = _take_snapshot(state_dir, ops_dir)

    diffs: list[dict] = []
    for key in SNAPSHOT_FIELDS:
        old_val = old_snap.get(key)
        new_val = new_snap.get(key)
        if old_val != new_val:
            diffs.append({"field": key, "before": old_val, "after": new_val})

    # money fingerprint change = خطرناک (code changed)
    money_changed = old_snap.get("money_fingerprint") != new_snap.get("money_fingerprint")
    if money_changed:
        diffs.append({"field": "money_fingerprint",
                       "before": old_snap.get("money_fingerprint"),
                       "after": new_snap.get("money_fingerprint")})

    # verdict: اگر conflicts جدید یا money تغییر یا freeze → fail
    new_conflicts = new_snap.get("conflicts") or []
    old_conflicts = old_snap.get("conflicts") or []
    new_conflict_count = len(new_conflicts)
    old_conflict_count = len(old_conflicts)
    regression = new_conflict_count > old_conflict_count

    passed = not money_changed and not regression and not new_snap.get("frozen")
    verdict = "pass" if passed else "regression-detected"
    if money_changed:
        verdict = "money-code-changed"

    return {"passed": passed, "diffs": diffs, "verdict": verdict,
            "money_changed": money_changed}


# ─── pre-registered metrics ────────────────────────────────────────────────────────
_METRICS_FILE = "phase-metrics.jsonl"


def pre_register_metric(phase_id: str, metric_name: str, threshold: float,
                        direction: str, state_dir: Path | str | None = None,
                        baseline_value: float | None = None,
                        description: str = "") -> str:
    """ثبت معیارِ pre-registered قبل از شروع فاز.

    direction: "below" (باید زیر threshold بیاید) یا "above" (باید بالاتر بیاید)
    خروجی: ردیفِ JSONL (for audit)."""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "phase_id": phase_id,
        "metric_name": metric_name,
        "threshold": threshold,
        "direction": direction,
        "baseline_value": baseline_value,
        "description": description,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    line = json.dumps(record, ensure_ascii=False)
    fpath = state_dir / _METRICS_FILE
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def check_pre_registered(phase_id: str,
                        state_dir: Path | str | None = None,
                        current_values: dict | None = None) -> dict:
    """آستانه‌های pre-registered را با مقادیر فعلی مقایسه کن.

    current_values: dict {metric_name: actual_value}
    خروجی: {metrics: [...], all_passed: bool}"""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)
    current_values = current_values or {}

    fpath = state_dir / _METRICS_FILE
    if not fpath.is_file():
        return {"metrics": [], "all_passed": True, "note": "no-metrics-registered"}

    results: list[dict] = []
    all_passed = True
    for raw_line in fpath.read_text("utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            rec = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if rec.get("phase_id") != phase_id:
            continue

        mname = rec["metric_name"]
        actual = current_values.get(mname)
        if actual is None:
            results.append({"metric": mname, "status": "skip",
                           "reason": "no-current-value"})
            continue

        threshold = rec["threshold"]
        direction = rec["direction"]
        if direction == "below":
            passed = actual < threshold
        elif direction == "above":
            passed = actual > threshold
        else:
            passed = False

        if not passed:
            all_passed = False
        results.append({
            "metric": mname, "threshold": threshold, "actual": actual,
            "direction": direction, "passed": passed,
        })

    return {"metrics": results, "all_passed": all_passed}


def get_all_baselines(state_dir: Path | str | None = None) -> list[dict]:
    """لیست تمام baselineهای ثبت‌شده (metadata-only، بدون snapshot)."""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    baselines = []
    for p in sorted(state_dir.glob("baseline-*.json")):
        doc = _read_json_safe(p)
        if doc:
            baselines.append({
                "path": str(p),
                "phase_id": doc.get("phase_id"),
                "label": doc.get("label"),
                "ts": (doc.get("snapshot") or {}).get("iso"),
            })
    return baselines
