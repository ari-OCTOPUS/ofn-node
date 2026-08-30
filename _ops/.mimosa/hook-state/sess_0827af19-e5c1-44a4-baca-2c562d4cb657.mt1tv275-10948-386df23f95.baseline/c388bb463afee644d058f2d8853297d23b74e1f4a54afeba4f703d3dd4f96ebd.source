#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pain_triage.py — قابلیت نخست‌زاده (first-born capability) از مسیر Organogenesis.

ورودی: ردیف‌های `_ops/state/neural/pain-assessment.jsonl` + `ORGANISM-STATE.json`.
خروجی: دیجستِ triage (اولویتبندیشده) — فقط‌خواندنی پیش‌فرض؛ نوشتن فقط با --write.

قرارداد:
  - صفر اثر بیرونی؛ هیچ نوشتی بدون --write.
  - هر عدد: path + روش + زمان؛ برچسب MEASURED (نه VERIFIED).
  - ردیفِ ناشناخته skip نمیشود؛ در bucket جدا ثبت میشود (LAW-03).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

SCHEMA = "pain-triage.v1"
GRADE = "MEASURED"


def parse_pain_rows(path: Path) -> dict:
    """خواندن دفاعی؛ ردیف‌های خراب در bucket جدا. خروجی: {rows, malformed, latest}."""
    rows, malformed = [], 0
    latest = None
    if not Path(path).exists():
        return {"rows": [], "malformed": 0, "latest": None}
    for line in Path(path).read_text("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if not isinstance(d, dict):
            malformed += 1
            continue
        try:
            pain = float(d.get("pain"))
        except (TypeError, ValueError):
            malformed += 1
            continue
        thr = None
        try:
            thr = float(d.get("threshold"))
        except (TypeError, ValueError):
            thr = None
        row = {"ts": str(d.get("ts") or ""), "pain": pain, "threshold": thr,
               "status": str(d.get("status") or ""),
               "reason_codes": list(d.get("reason_codes") or []),
               "evidence_level": str(d.get("evidence_level") or ""),
               "proposal": str(d.get("proposal") or "none"),
               "above": bool(thr is not None and pain > thr),
               "trace_id": str(d.get("trace_id") or "")}
        rows.append(row)
        if latest is None or row["ts"] > latest["ts"]:
            latest = row
    return {"rows": rows, "malformed": malformed, "latest": latest}


def signals_from_organism(state: dict) -> list:
    """سیگنال‌های ساختاری از ORGANISM-STATE (بدون خواندن مقادیر مالی/PII)."""
    out = []
    cart = (state or {}).get("cartographer") or {}
    if cart.get("map_stale"):
        out.append({"signal": "cartographer-map-stale", "severity": "MED",
                    "age_days": cart.get("map_age_days"),
                    "drift_files": cart.get("drift_files")})
    chrono = (state or {}).get("chrono") or {}
    for leg_id, diag in (chrono.get("legs_diag") or {}).items():
        st = (diag or {}).get("state")
        if st == "alive":
            out.append({"signal": f"leg:{leg_id}", "severity": "OK", "state": st})
        else:
            out.append({"signal": f"leg:{leg_id}", "severity": "WARN", "state": st})
    return out


def triage(pain_path: Path, state: dict) -> dict:
    p = parse_pain_rows(pain_path)
    rows = p["rows"]
    above = [r for r in rows if r["above"]]
    signals = signals_from_organism(state)
    ordered = sorted(rows, key=lambda r: (r["above"], r["pain"]), reverse=True)[:10]
    return {
        "schema": SCHEMA, "grade": GRADE, "as_of": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "method": "pain-assessment.v1 rows + ORGANISM-STATE signals",
        "counts": {"rows": len(rows), "malformed": p["malformed"],
                   "above_threshold": len(above)},
        "latest_pain": p["latest"],
        "signals": signals,
        "triage": [{"ts": r["ts"], "pain": r["pain"], "above": r["above"],
                    "status": r["status"], "reason_codes": r["reason_codes"],
                    "evidence_level": r["evidence_level"], "proposal": r["proposal"]}
                   for r in ordered],
        "priority": ("HIGH" if (above or any(s["severity"] == "MED" for s in signals))
                     else "LOW"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pain-file", default=str(
        Path(__file__).resolve().parent.parent / "state" / "neural" / "pain-assessment.jsonl"))
    ap.add_argument("--state-file", default=str(
        Path(__file__).resolve().parent.parent / "state" / "ORGANISM-STATE.json"))
    ap.add_argument("--write", action="store_true",
                    help="دیجست را در state/pulse/pain-triage-latest.json بنویسد")
    args = ap.parse_args()
    state = {}
    try:
        state = json.loads(Path(args.state_file).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        state = {}
    out = triage(Path(args.pain_file), state)
    if args.write:
        dst = Path(__file__).resolve().parent.parent / "state" / "pulse" / "pain-triage-latest.json"
        tmp = dst.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
        import os
        os.replace(tmp, dst)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
