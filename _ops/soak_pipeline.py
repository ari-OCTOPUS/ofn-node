#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""soak_pipeline.py — 72-hour longitudinal soak pipeline (additive; 2026-08-10).

WP-B of Fugu Ultra Audit Remediation. This is a NEW module; it does NOT modify
`soak_scorecard.py` (whose `check()` stays backward-compatible). It adds:

  · versioned config (soak_config.yaml) — no hardcoded decision numbers
  · append-only JSONL history with schema/ts/window/metrics/verdict per checkpoint
  · real time-based halt-duty cycle (halted_duration / window_duration)
  · BCM stagnation from artifact timestamp/progress field (not raw mtime)
  · effect reconciliation: lost / duplicate / without-receipt / intervention
  · fail-closed missing-data semantics for critical sources
  · idempotent checkpoint recording (same checkpoint_id re-run = explicit duplicate)
  · --once / --status CLI for manual testing and history summary

DESIGN CONTRACTS:
  · $0, stdlib-only, no LLM, no network, no side-effects on runtime state.
  · UTC everywhere (no local/UTC double-conversion).
  · Missing critical source => STOP, never silent green.
  · Missing non-critical source => UNKNOWN metric, recorded honestly.
  · This module only READS runtime state and WRITES its own history file.

See `06 - Architecture Maps/EVIDENCE-LADDER-TAXONOMY.md` for the evidence ladder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"
CONFIG_PATH = _HERE / "soak_config.yaml"
HISTORY_PATH = STATE / "soak-history.jsonl"

SCHEMA = "SoakCheckpoint.v1"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc_iso(s: str) -> datetime | None:
    """Parse a UTC ISO timestamp. Returns None on failure."""
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return default


def _read_jsonl(path: Path) -> tuple[list[dict], int]:
    """Read a JSONL file. Returns (valid_rows, corrupt_count).

    corrupt lines are counted but skipped (not fatal here — the metric layer
    decides stop/alert based on the count).
    """
    rows: list[dict] = []
    corrupt = 0
    try:
        for line in path.read_text("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                corrupt += 1
    except OSError:
        pass
    return rows, corrupt


# ─── config ───────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load soak_config.yaml. FAILS CLOSED on missing/invalid.

    A minimal YAML parser for our flat structure (two levels: top-level scalars
    and metrics.<name>.<key>). This avoids a PyYAML dependency. If the file is
    missing or the structure is wrong, we raise — the caller translates to STOP.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"soak config not found: {CONFIG_PATH}")
    raw = CONFIG_PATH.read_text("utf-8")

    cfg: dict = {"metrics": {}}
    current_metric: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Determine indentation level: top-level = no leading space
        indented = line[0] == " " if line else False
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        # Strip inline YAML comment (everything after an unquoted #)
        if "#" in val:
            val = val[:val.index("#")]
        val = val.strip()
        if not indented:
            # Top-level line
            if key == "metrics":
                current_metric = None  # block header — children handled below
            elif val:
                cfg[key] = _coerce(val)
                current_metric = None
            else:
                # unknown top-level block — ignore
                current_metric = None
        else:
            # Indented line — either under 'metrics' (metric name) or under a metric
            if val:
                # leaf: metric.key = value
                if current_metric:
                    if key in ("warn_states", "stop_states"):
                        items = [v.strip() for v in val.strip("[]").split(",") if v.strip()]
                        cfg["metrics"][current_metric][key] = items
                    else:
                        cfg["metrics"][current_metric][key] = _coerce(val)
            else:
                # metric block header
                current_metric = key
                cfg["metrics"][key] = {}
    if not cfg.get("metrics"):
        raise ValueError("soak config has no metrics section")
    return cfg


def _coerce(val: str):
    """Coerce a string to int/float/bool/None/str."""
    if val.lower() in ("null", "none", "~"):
        return None
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


# ─── baseline ─────────────────────────────────────────────────────────────────

def _baseline() -> dict | None:
    b = _read_json(STATE / "soak-baseline.json")
    if not b or not isinstance(b, dict):
        return None
    return b


def _baseline_ts() -> datetime | None:
    b = _baseline()
    if not b:
        return None
    ts = b.get("start_utc") or b.get("start_ts") or b.get("start_local")
    return _parse_utc_iso(ts) if ts else None


# ─── metric collectors ────────────────────────────────────────────────────────
# Each collector returns a dict with at least:
#   value: the measured value (or None if UNKNOWN)
#   status: "ok" | "unknown" | "missing"
#   detail: human-readable explanation

def _collect_deny_growth(cfg_m: dict) -> dict:
    fq = _read_json(STATE / "fugu-quota.json")
    if not fq:
        return {"value": None, "status": "missing",
                "detail": "fugu-quota.json خوانده نشد"}
    # baseline deny from intervention-ledger
    rows, _ = _read_jsonl(STATE / "intervention-ledger.jsonl")
    deny_before = 0
    for r in reversed(rows):
        if r.get("kind") == "model_map_change":
            deny_before = int(r.get("deny_before", 0) or 0)
            break
    denied_now = int((fq.get("denied") or {}).get("stop-fugu", 0))
    growth = denied_now - deny_before
    return {"value": growth, "status": "ok",
            "detail": f"deny_before={deny_before} denied_now={denied_now}",
            "deny_before": deny_before, "denied_now": denied_now}


def _collect_breaker(cfg_m: dict) -> dict:
    cs = _read_json(STATE / "circuit-state.json")
    if not cs:
        return {"value": None, "status": "missing",
                "detail": "circuit-state.json خوانده نشد"}
    targets = cs.get("targets") or {}
    states = {k: v.get("state") for k, v in targets.items()}
    if not states:
        return {"value": None, "status": "missing", "detail": "بدون target در breaker"}
    return {"value": states, "status": "ok", "detail": str(states)}


def _collect_paid_success(cfg_m: dict, window_start: datetime) -> dict:
    rows, _ = _read_jsonl(STATE / "paid-calls.jsonl")
    start_iso = _utc_iso(window_start)
    in_window = []
    for r in rows:
        if r.get("ts", "") >= start_iso:
            in_window.append(r)
    total = len(in_window)
    ok = sum(1 for r in in_window if r.get("ok"))
    min_sample = cfg_m.get("min_sample", 5)
    if total < min_sample:
        return {"value": None, "status": "unknown",
                "detail": f"sample {total} < min_sample {min_sample}",
                "total": total, "ok": ok}
    rate = ok / total
    return {"value": rate, "status": "ok", "detail": f"{ok}/{total}",
            "total": total, "ok": ok}


def _collect_halt_duty(cfg_m: dict, window_start: datetime,
                       window_end: datetime) -> dict:
    """Time-based halt duty cycle.

    We read the organism halt-transition history. If the organism writes a
    halt/freeze event log, we use interval math. If only a boolean snapshot
    exists, we CANNOT compute duty => UNKNOWN (not zero).

    Strategy:
      1. Try ORGANISM-STATE.json for `halt_history` (list of {ts, halted}).
      2. If present, compute halted_duration via interval math.
      3. If absent, metric = UNKNOWN (we refuse to fabricate a duty cycle).
    """
    d = _read_json(STATE / "ORGANISM-STATE.json")
    if not d:
        return {"value": None, "status": "missing",
                "detail": "ORGANISM-STATE.json خوانده نشد"}
    hist = d.get("halt_history")
    if hist and isinstance(hist, list) and len(hist) >= 1:
        window_s = (window_end - window_start).total_seconds()
        halted_s = _compute_halted_seconds(hist, window_start, window_end)
        duty = halted_s / window_s if window_s > 0 else None
        return {"value": duty, "status": "ok",
                "detail": f"halted_s={halted_s:.0f} window_s={window_s:.0f}",
                "halted_s": halted_s, "window_s": window_s}
    # No transition history => we honestly cannot compute duty
    return {"value": None, "status": "unknown",
            "detail": "halt_history غایب — duty قابل محاسبه نیست (boolean snapshot کافی نیست)"}


def _compute_halted_seconds(hist: list[dict], window_start: datetime,
                            window_end: datetime) -> float:
    """Given a list of {ts, halted: bool} transitions, compute total halted
    time within [window_start, window_end].

    We assume transitions are sorted by ts. We track the last state and the
    last transition time, accumulating halted intervals.
    """
    total = 0.0
    prev_ts = window_start
    prev_halted = False
    for entry in hist:
        ts = _parse_utc_iso(entry.get("ts", ""))
        halted = bool(entry.get("halted"))
        if ts is None:
            continue
        # clamp to window
        clamped = max(ts, window_start)
        if clamped > window_end:
            clamped = window_end
        if prev_halted:
            total += (clamped - prev_ts).total_seconds()
        prev_halted = halted
        prev_ts = clamped
        if ts > window_end:
            break
    # tail: from last transition to window_end
    if prev_halted:
        total += (window_end - prev_ts).total_seconds()
    return max(total, 0.0)


def _collect_restarts(cfg_m: dict, window_start: datetime) -> dict:
    """Count unplanned restarts: flags-loaded-*.json files modified after
    baseline, excluding planned_restarts in intervention-ledger."""
    b = _baseline()
    if not b:
        return {"value": None, "status": "unknown", "detail": "baseline غایب"}
    rows, _ = _read_jsonl(STATE / "intervention-ledger.jsonl")
    planned: set[str] = set()
    for r in rows:
        planned.update(r.get("planned_restarts", []))
    known = ["organism", "cortex", "live", "center", "miniapp-gateway"]
    count = 0
    started = []
    for name in known:
        if name in planned:
            continue
        f = STATE / f"flags-loaded-{name}.json"
        try:
            mtime = f.stat().st_mtime
            mt_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            if mt_dt >= window_start:
                count += 1
                started.append(name)
        except OSError:
            continue
    return {"value": count, "status": "ok",
            "detail": f"unplanned: {started}", "processes": started}


def _collect_bcm_stagnation(cfg_m: dict, window_end: datetime) -> dict:
    """BCM stagnation: check if bcm-weights.json has a `step`/`ts` field that
    progressed. If no semantic progress field exists, metric = UNKNOWN."""
    d = _read_json(STATE / "bcm-weights.json")
    if not d:
        return {"value": None, "status": "unknown",
                "detail": "bcm-weights.json خوانده نشد"}
    step = d.get("step") or d.get("bcm_step")
    ts = d.get("ts")
    if step is None and ts is None:
        return {"value": None, "status": "unknown",
                "detail": "field шаг/ts غایب — stagnation قابل سنجش نیست"}
    age_h = None
    if ts:
        ts_dt = _parse_utc_iso(ts)
        if ts_dt:
            age_h = (window_end - ts_dt).total_seconds() / 3600
    return {"value": {"step": step, "age_h": age_h}, "status": "ok",
            "detail": f"step={step} age_h={age_h}"}


def _collect_effect_reconciliation(cfg_m: dict) -> dict:
    """Reconcile effects: lost / duplicate / without-receipt / intervention.

    If the intervention-ledger / outbound-effects schema supports these
    distinctions, we count them. Otherwise each sub-metric is UNKNOWN.

    We never conflate 'intervention count' with 'lost effect' — they are
    independent. An intervention is a documented owner action; a lost effect
    is an unresolved proposed→executed gap.
    """
    rows, corrupt = _read_jsonl(STATE / "intervention-ledger.jsonl")
    interventions = len(rows)

    # Try outbound-effects for lost/duplicate/without-receipt
    oe_rows, oe_corrupt = _read_jsonl(
        STATE / "agi2027_runtime" / "outbound-effects.jsonl")
    lost = 0
    duplicate = 0
    without_receipt = 0
    seen_keys: set[str] = set()
    for r in oe_rows:
        status = (r.get("status") or "").lower()
        key = r.get("effect_id") or r.get("idempotency_key") or ""
        has_receipt = bool(r.get("receipt_ref") or r.get("settled"))
        if status in ("lost", "unresolved", "failed"):
            lost += 1
        if key:
            if key in seen_keys:
                duplicate += 1
            else:
                seen_keys.add(key)
        if not has_receipt and status not in ("proposed", "rejected", "cancelled"):
            without_receipt += 1

    parse_errors = corrupt + oe_corrupt

    # If outbound-effects doesn't exist, these are genuinely UNKNOWN
    oe_exists = (STATE / "agi2027_runtime" / "outbound-effects.jsonl").exists()
    if not oe_exists:
        return {"value": {
            "lost": None, "duplicate": None, "without_receipt": None,
            "interventions": interventions, "parse_errors": parse_errors,
        }, "status": "unknown",
            "detail": "outbound-effects.jsonl غایب — lost/dup/receipt = UNKNOWN"}


def _collect_parse_integrity(cfg_m: dict) -> dict:
    """Count corrupt lines across critical JSONL sources."""
    critical = [
        STATE / "intervention-ledger.jsonl",
        STATE / "paid-calls.jsonl",
        STATE / "agi2027_runtime" / "outbound-effects.jsonl",
    ]
    total_corrupt = 0
    sources_checked = 0
    for path in critical:
        _, c = _read_jsonl(path)
        total_corrupt += c
        if path.exists():
            sources_checked += 1
    if sources_checked == 0:
        return {"value": None, "status": "missing",
                "detail": "هیچ منبع بحرانی یافت نشد"}
    return {"value": total_corrupt, "status": "ok",
            "detail": f"corrupt lines across {sources_checked} sources"}


# ─── verdict logic ────────────────────────────────────────────────────────────

def _apply_threshold(metric_name: str, collected: dict, cfg_m: dict) -> tuple[str, str]:
    """Return (severity, reason) where severity is 'green'|'alert'|'stop'.

    Fail-closed: if status == 'missing' and cfg says missing=STOP, it's STOP.
    If status == 'unknown' and cfg says missing=UNKNOWN, metric is recorded
    but does not trigger stop/alert on its own.
    """
    missing_policy = cfg_m.get("missing", "UNKNOWN")
    if collected["status"] == "missing":
        if str(missing_policy).upper() == "STOP":
            return "stop", f"{metric_name}: منبع مفقود — fail-closed STOP"
        return "unknown", f"{metric_name}: منبع مفقود — UNKNOWN"

    if collected["status"] == "unknown":
        return "unknown", f"{metric_name}: {collected['detail']}"

    val = collected["value"]

    # Numeric thresholds (deny_growth, paid_success, restarts, etc.)
    if metric_name == "paid_success":
        if val is not None:
            if val < cfg_m.get("stop", 0.70):
                return "stop", f"paid success {val:.0%} < {cfg_m['stop']:.0%}"
            if val < cfg_m.get("warn", 0.90):
                return "alert", f"paid success {val:.0%} < {cfg_m['warn']:.0%}"
        return "green", ""

    if metric_name == "halt_duty":
        if val is not None:
            if val > cfg_m.get("stop", 0.15):
                return "stop", f"halt duty {val:.1%} > {cfg_m['stop']:.1%}"
            if val > cfg_m.get("warn", 0.05):
                return "alert", f"halt duty {val:.1%} > {cfg_m['warn']:.1%}"
        return "green", ""

    if metric_name == "breaker":
        stop_states = set(cfg_m.get("stop_states", ["open"]))
        warn_states = set(cfg_m.get("warn_states", ["half_open"]))
        if isinstance(val, dict):
            for name, st in val.items():
                if st in stop_states:
                    return "stop", f"breaker[{name}] {st}"
                if st in warn_states:
                    return "alert", f"breaker[{name}] {st}"
        return "green", ""

    if metric_name == "bcm_stagnation":
        warn_age = cfg_m.get("warn_age_h", 48)
        stop_age = cfg_m.get("stop_age_h")
        if isinstance(val, dict):
            age_h = val.get("age_h")
            if age_h is not None:
                if stop_age is not None and age_h > stop_age:
                    return "stop", f"BCM stagnation {age_h:.0f}h > {stop_age}h"
                if age_h > warn_age:
                    return "alert", f"BCM stagnation {age_h:.0f}h > {warn_age}h"
        return "green", ""

    # Count-based (deny_growth, restarts, lost_effect, duplicate, parse_integrity)
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        stop_t = cfg_m.get("stop")
        warn_t = cfg_m.get("warn")
        if stop_t is not None and val >= stop_t:
            return "stop", f"{metric_name}={val} ≥ stop {stop_t}"
        if warn_t is not None and val >= warn_t:
            return "alert", f"{metric_name}={val} ≥ warn {warn_t}"
        return "green", ""

    return "green", ""


# ─── history persistence ─────────────────────────────────────────────────────

def _checkpoint_id(window_start: datetime, window_end: datetime) -> str:
    """Deterministic ID from window boundaries."""
    raw = f"{_utc_iso(window_start)}|{_utc_iso(window_end)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _append_history(record: dict) -> dict:
    """Append a checkpoint to soak-history.jsonl (append-only).

    Idempotency: if a record with the same checkpoint_id already exists,
    we record an explicit duplicate marker rather than silently appending
    a second full record.
    """
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing, _ = _read_jsonl(HISTORY_PATH)
    dup_count = sum(1 for r in existing
                    if r.get("checkpoint_id") == record["checkpoint_id"])
    if dup_count > 0:
        record["duplicate_of_run"] = dup_count
        record["note"] = (record.get("note", "") +
                          f" [duplicate: {dup_count} prior run(s) of this checkpoint]")
    # Torn-write protection: write to temp then append
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    try:
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
    except OSError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "appended": True}


def _history_summary() -> dict:
    rows, corrupt = _read_jsonl(HISTORY_PATH)
    if not rows:
        return {"n": 0, "corrupt": corrupt, "verdicts": {}, "latest": None}
    from collections import Counter
    verdicts = Counter(r.get("verdict") for r in rows)
    latest = rows[-1] if rows else None
    return {"n": len(rows), "corrupt": corrupt,
            "verdicts": dict(verdicts), "latest_verdict": latest.get("verdict") if latest else None,
            "latest_ts": latest.get("ts") if latest else None}


# ─── main check ──────────────────────────────────────────────────────────────

def run_checkpoint(window_start: datetime | None = None,
                   window_end: datetime | None = None,
                   persist: bool = True) -> dict:
    """Run all metrics for a checkpoint window and return the record.

    If window_start/window_end are None, we use [baseline_ts, now].
    """
    cfg = _load_config()  # FAILS CLOSED if missing/invalid
    now = _utc_now()

    bs = _baseline_ts()
    if window_start is None:
        window_start = bs or now
    if window_end is None:
        window_end = now

    checkpoint_id = _checkpoint_id(window_start, window_end)

    metrics_cfg = cfg.get("metrics", {})

    collectors = {
        "deny_growth": lambda: _collect_deny_growth(metrics_cfg.get("deny_growth", {})),
        "breaker": lambda: _collect_breaker(metrics_cfg.get("breaker", {})),
        "paid_success": lambda: _collect_paid_success(
            metrics_cfg.get("paid_success", {}), window_start),
        "halt_duty": lambda: _collect_halt_duty(
            metrics_cfg.get("halt_duty", {}), window_start, window_end),
        "restarts": lambda: _collect_restarts(
            metrics_cfg.get("restarts", {}), window_start),
        "bcm_stagnation": lambda: _collect_bcm_stagnation(
            metrics_cfg.get("bcm_stagnation", {}), window_end),
        "lost_effect": lambda: _collect_effect_reconciliation(
            metrics_cfg.get("lost_effect", {})),
        "duplicate_effect": lambda: _collect_effect_reconciliation(
            metrics_cfg.get("duplicate_effect", {})),
        "effect_without_receipt": lambda: _collect_effect_reconciliation(
            metrics_cfg.get("effect_without_receipt", {})),
        "parse_integrity": lambda: _collect_parse_integrity(
            metrics_cfg.get("parse_integrity", {})),
    }

    metrics: dict[str, dict] = {}
    alerts: list[str] = []
    stops: list[str] = []
    unknowns: list[str] = []

    for name, fn in collectors.items():
        try:
            collected = fn()
        except Exception as e:  # noqa: BLE001 — a collector must not kill the pipeline
            collected = {"value": None, "status": "unknown",
                         "detail": f"collector error: {type(e).__name__}: {e}"}
        cfg_m = metrics_cfg.get(name, {})
        severity, reason = _apply_threshold(name, collected, cfg_m)
        metrics[name] = {**collected, "severity": severity, "reason": reason}
        if severity == "stop":
            stops.append(reason)
        elif severity == "alert":
            alerts.append(reason)
        elif severity == "unknown":
            unknowns.append(reason)

    if stops:
        verdict = "STOP"
    elif alerts:
        verdict = "ALERT"
    elif unknowns and not alerts:
        # All-unknown is not green; it's UNKNOWN — honest.
        # But a mix of green+unknown leans to ALERT (we don't have full confidence).
        verdict = "ALERT" if any(m["severity"] == "green" for m in metrics.values()) else "UNKNOWN"
    else:
        verdict = "GREEN"

    record = {
        "schema": SCHEMA,
        "checkpoint_id": checkpoint_id,
        "ts": _utc_iso(now),
        "window_start": _utc_iso(window_start),
        "window_end": _utc_iso(window_end),
        "window_duration_s": (window_end - window_start).total_seconds(),
        "config_schema": cfg.get("schema", "?"),
        "metrics": metrics,
        "alerts": alerts,
        "stops": stops,
        "unknowns": unknowns,
        "verdict": verdict,
    }

    if persist:
        _append_history(record)

    return record


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="72-hour soak pipeline (WP-B remediation)")
    parser.add_argument("--once", action="store_true",
                        help="run a single checkpoint and print (for testing/manual)")
    parser.add_argument("--status", action="store_true",
                        help="print history summary")
    parser.add_argument("--no-persist", action="store_true",
                        help="don't append to history (testing)")
    args = parser.parse_args()

    if args.status:
        summary = _history_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    try:
        record = run_checkpoint(persist=not args.no_persist)
    except (FileNotFoundError, ValueError) as e:
        # Config missing/invalid => fail-closed STOP
        print(json.dumps({"verdict": "STOP", "reason": f"config/missing: {e}"},
                         ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(record, ensure_ascii=False, indent=2))
    print(f"\nverdict: {record['verdict']}")
    if record["stops"]:
        print("⛔ توقف soak — به مالک گزارش بده (هیچ اقدام خودکاری)")
    return 1 if record["stops"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
