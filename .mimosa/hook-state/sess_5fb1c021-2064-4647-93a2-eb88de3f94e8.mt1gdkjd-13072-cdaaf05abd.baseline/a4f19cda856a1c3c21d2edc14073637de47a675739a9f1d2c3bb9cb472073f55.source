#!/usr/bin/env python3
"""
replication.py — STAGE 3 پک (نیمهٔ تکثیر): قفل branching_ratio (σ) ≈ 1. فقط آفلاین/پیشنهادی.

هندسه: spawn = جهش؛ human-gate = فشار انتخاب؛ آستانهٔ پذیرش ≥۴۰٪ = برش fitness.
  σ < 1  → انقراض تدریجی (rigidity) → ALERT rigidity + ذخیرهٔ EXPLORE_PCT فعال بماند
  σ > 1  → خودتکثیری بی‌مهار (سمت «سرطان» محور s) → ALERT + توقف spawn
  σ ≈ 1  → جمعیت خود-جایگزین پایدار (edge of chaos = هدف)

گاردهای مطلق:
  - MAX_CELLS=6، عمق spawn=1 (ساب‌ایجنت ساب‌ایجنت نمی‌سازد) — از budgets.yaml اگر بخش
    replication اضافه شود (diff پیشنهادی)، وگرنه پیش‌فرض پک [SPEC].
  - spawn = side-effect ⇒ همیشه human-gated: این ماژول فقط PROPOSAL می‌سازد
    (ledger + صف SURVIVORS)، هرگز چیزی اجرا/spawn نمی‌کند.
  - PROJECT_F از تکثیر مستثناست تا GATE 0 (اولویت فروش).
  - L5 EXTINCTION هرگز خودکار نیست — فقط verdict انسان.
  - فعال‌سازی زندهٔ پیشنهاددهی دوقفله: تاریخ ≥ 2026-07-21 + ACTIVATION-REPLICATION.flag
    مالک + fitness.authoritative=true. پیش از آن فقط would_propose گزارش می‌شود.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib   # noqa: E402
import fitness  # noqa: E402

DEFAULTS = {"max_cells": 6, "spawn_depth": 1, "accept_threshold": 0.40}  # پک [SPEC]
EXCLUDED_ORGANS = {"PROJECT_F"}      # تا GATE 0
EXCLUDED_CELLS = {"projectf"}


def _cfg() -> dict:
    r = opslib.load_budgets().get("replication") or {}
    return {**DEFAULTS, **r}


def _ledger_spawn_counts() -> dict:
    """σ صادق: فقط از رویدادهای ledger — spawn پیشنهادی (NOTE/subtype=SPAWN_PROPOSAL)
    و spawn تأییدشده (APPROVAL با payload.origin.loop=replication)."""
    path = opslib.GENOME_DIR / "ledger" / "ledger.jsonl"
    proposed, approved = 0, 0
    if not path.exists():
        return {"proposed": 0, "approved": 0}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            p = rec.get("payload") or {}
            if rec.get("type") == "NOTE" and p.get("subtype") == "SPAWN_PROPOSAL":
                proposed += 1
            if rec.get("type") == "APPROVAL" and (p.get("origin") or {}).get("loop") == "replication":
                approved += 1
    return {"proposed": proposed, "approved": approved}


def sigma_state(active_cells: int) -> dict:
    """σ_effective = ساب‌ایجنت مؤثر (تأییدشده) به‌ازای هر ایجنت فعال."""
    counts = _ledger_spawn_counts()
    parents = max(1, active_cells)
    sigma = counts["approved"] / parents
    zone = "healthy"
    alerts = []
    if sigma > 1.0:
        zone = "cancer-axis"
        alerts.append("[ALERT: instability→cancer-axis] σ>1 — spawn متوقف")
    elif counts["approved"] == 0 and counts["proposed"] == 0:
        zone = "pre-replication"   # هنوز جمعیتی زاده نشده — rigidity فقط بعد از داده معنا دارد
    return {"sigma_effective": round(sigma, 4), "zone": zone,
            "spawn_proposed": counts["proposed"], "spawn_approved": counts["approved"],
            "parents": parents, "alerts": alerts}


def evaluate(write: bool = True) -> dict:
    """چرخهٔ کامل تکثیر (سایه): fitness → واجدان شرایط → σ → پیشنهاد (فقط پشت گیت دوقفله)."""
    cfg = _cfg()
    fit = fitness.compute(write=write)
    cells = {k: v for k, v in fit["cells"].items()
             if not v.get("excluded") and k not in EXCLUDED_CELLS}
    active = len(cells)
    sig = sigma_state(active)

    eligible = []
    for name, c in cells.items():
        if (c.get("acceptance_rate") or 0) >= cfg["accept_threshold"] and c.get("judged", 0) >= 5:
            eligible.append(name)

    gate_ok, gate_why = opslib.live_gate_open(opslib.ACT_REPLICATION)
    can_propose = (gate_ok and fit["authoritative"] and not sig["alerts"]
                   and active < cfg["max_cells"] and not opslib.halted() and not opslib.frozen())
    proposals = []
    if can_propose:
        for name in eligible[: max(0, cfg["max_cells"] - active)]:
            prop = {
                "cell": name, "kind": "spawn-subagent", "depth": 1,
                "justification": f"acceptance_rate={cells[name]['acceptance_rate']} ≥ "
                                 f"{cfg['accept_threshold']} با {cells[name]['judged']} داوری انسانی",
                "human_gated": True, "origin": {"loop": "replication"},
            }
            proposals.append(prop)
            opslib.ledger_note("SPAWN_PROPOSAL", prop, actor="replication")
    idle = not eligible and active > 0 and fit["authoritative"]
    rigidity_alert = []
    if idle:
        rigidity_alert = [f"[ALERT: rigidity] هیچ cell واجد شرایط نیست — "
                          f"ذخیرهٔ EXPLORE_PCT برای cellهای اثبات‌نشده فعال بماند"]
        opslib.alert(rigidity_alert)
    if sig["alerts"]:
        opslib.alert(sig["alerts"])

    report = {
        "ts": opslib.now_iso(),
        "config": cfg, "excluded_organs": sorted(EXCLUDED_ORGANS),
        "sigma": sig,
        "fitness_authoritative": fit["authoritative"],
        "eligible_cells": eligible,
        "live_gate": {"open": gate_ok, "why": gate_why},
        "proposals_written": proposals,
        "would_propose": eligible if (eligible and not can_propose) else [],
        "alerts": sig["alerts"] + rigidity_alert,
        "note": "این ماژول هرگز spawn اجرا نمی‌کند؛ فقط PROPOSAL human-gated (تو propose، انسان dispose)",
    }
    if write:
        with opslib.LockedJson(opslib.STATE_DIR / "replication-latest.json") as lj:
            lj.write(report)
    return report


if __name__ == "__main__":
    print(json.dumps(evaluate(write="--dry" not in sys.argv), ensure_ascii=False, indent=2))
