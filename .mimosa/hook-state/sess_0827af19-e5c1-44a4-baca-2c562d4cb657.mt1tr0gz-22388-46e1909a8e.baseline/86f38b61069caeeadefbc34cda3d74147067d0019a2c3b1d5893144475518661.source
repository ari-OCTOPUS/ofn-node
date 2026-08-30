#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_health_score.py — CH-07: Health score extractor for OCTOPUS.

منبع: _ops/state/ORGANISM-STATE.json + fitness-latest.json + telemetry-latest.json
سینک: nervous-system/health-data.js  →  OCTOPUS/worlds/octo-data.js (health)

Health score = ترکیبِ وزنیِ ۳ محور:
  • system_health   (wiring, frozen, halted, germline, chrono)
  • fitness_health  (cell fitness avg, integrity alerts, authoritative)
  • telemetry_health (budget, suspect_zero, divergence)

خروجی: 0..100 (مماسل: 100 = سالم، 0 = بحرانی)
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("health_score")

# ─── paths ─────────────────────────────────────────────────────────────────────
OPS_STATE = Path("F:/backup/_ops/state")
OPS_DIR = Path("F:/backup/_ops")
NS_DIR = Path("F:/backup/nervous-system")
ALERTS_MD = OPS_DIR / "governor" / "governor-alerts.md"

# ─── weights (configurable; external override via health-weights.json) ──────────
DEFAULT_WEIGHTS = {
    "system": 0.40,
    "fitness": 0.35,
    "telemetry": 0.25,
}


def _load_json(path: Path, default: Any = None) -> Any:
    """خواندنِ JSON با fail-soft؛ اگر فایل غایب → default."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("فایل غایب/خراب: %s — %s", path, e)
        return default


def _read_alert_count(hours: float = 24.0) -> int:
    """شمردنِ رکوردهای alert فعال در governor-alerts.md (آخرین N ساعت).

    هر بلوک با خطِ ## شروع می‌شود و یک timestamp ISO دارد.
    """
    if not ALERTS_MD.exists():
        return 0
    try:
        text = ALERTS_MD.read_text("utf-8")
    except OSError:
        return 0
    # هر بلوک alert با ## شروع می‌شود
    blocks = re.split(r"\n## ", text)
    cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    count = 0
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # استخراج timestamp از ابتدای بلوک: "2026-07-10T07:30:48 (metabolism)"
        m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", block)
        if not m:
            continue
        ts = _parse_iso(m.group(1))
        if ts and ts.timestamp() >= cutoff:
            count += 1
    return count


def _parse_iso(ts: str | None) -> datetime | None:
    """پارسِ timestamp ISO. اگر naive باشد → UTC فرض می‌شود."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _compute_system_score(org: dict) -> tuple[float, dict]:
    """محاسبهٔ system_health از ORGANISM-STATE."""
    score = 100.0
    details: dict[str, Any] = {}

    wiring = org.get("wiring", {})
    wires_on = sum(1 for v in wiring.values() if v is True)
    wires_total = sum(1 for k, v in wiring.items() if isinstance(v, bool))
    wires_pct = (wires_on / wires_total * 100) if wires_total else 0
    details["wires_on"] = wires_on
    details["wires_total"] = wires_total
    details["wires_pct"] = round(wires_pct, 2)
    # هر wire off = -3 امتیاز (تا سقف -30)
    score -= min(30, (wires_total - wires_on) * 3)

    if org.get("frozen"):
        score -= 40
        details["frozen"] = True
    else:
        details["frozen"] = False

    if org.get("halted"):
        score -= 30
        details["halted"] = True
    else:
        details["halted"] = False

    # germline lag: هر ساعت lag = -0.5 (تا سقف -15)
    germline_lag = org.get("germline_lag_h", 0) or 0
    details["germline_lag_h"] = round(germline_lag, 2)
    score -= min(15, germline_lag * 0.5)

    # chrono: اگر effects_pending > 10 → -5
    effects_pending = org.get("chrono", {}).get("effects_pending", 0) or 0
    details["effects_pending"] = effects_pending
    if effects_pending > 10:
        score -= 5

    # cardiac budget: اگر depleted → -10
    cardiac = org.get("cardiac", {}).get("budget", {})
    details["cardiac_depleted"] = bool(cardiac.get("depleted"))
    if cardiac.get("depleted"):
        score -= 10
    details["cardiac_remaining"] = cardiac.get("remaining", 0)

    # cartographer map stale → -5
    cart = org.get("cartographer", {})
    details["cartographer_stale"] = bool(cart.get("map_stale"))
    if cart.get("map_stale"):
        score -= 5
    details["cartographer_age_days"] = cart.get("map_age_days", 0)

    score = max(0.0, min(100.0, score))
    details["score"] = round(score, 2)
    return score, details


def _compute_fitness_score(fit: dict) -> tuple[float, dict]:
    """محاسبهٔ fitness_health از fitness-latest.json."""
    score = 100.0
    details: dict[str, Any] = {}

    cells = fit.get("cells", {})
    if cells:
        fit_values = [c.get("fitness", 0) for c in cells.values() if isinstance(c, dict)]
        avg_fit = sum(fit_values) / len(fit_values) if fit_values else 0
        details["cell_count"] = len(fit_values)
        details["fitness_avg"] = round(avg_fit, 4)
        # fitness avg به [0,1] نگاشت شده → امتیاز ۰..۱۰۰
        score = avg_fit * 100
    else:
        details["cell_count"] = 0
        details["fitness_avg"] = None
        score = 50.0  # هنوز دادهٔ fitness کافی نیست → خنثی

    integrity = fit.get("integrity_alerts", [])
    details["integrity_alert_count"] = len(integrity)
    # هر integrity alert = -15 امتیاز (تا سقف -30)
    score -= min(30, len(integrity) * 15)

    # authoritative: اگر نباشد → -5 (shadow mode)
    authoritative = bool(fit.get("authoritative", False))
    details["authoritative"] = authoritative
    if not authoritative:
        score -= 5

    details["experience_span_days"] = fit.get("experience_span_days", 0)

    score = max(0.0, min(100.0, score))
    details["score"] = round(score, 2)
    return score, details


def _compute_telemetry_score(tel: dict, org: dict) -> tuple[float, dict]:
    """محاسبهٔ telemetry_health از telemetry-latest.json."""
    score = 100.0
    details: dict[str, Any] = {}

    suspect = tel.get("suspect_zero_total", 0) or 0
    details["suspect_zero_total"] = suspect
    # هر suspect_zero = -3 (تا سقف -15)
    score -= min(15, suspect * 3)

    # month spend vs cap: اگر > 80% → -10, > 95% → -20
    month_aud = tel.get("month", {}).get("aud", 0) or 0
    cap_monthly = 30.0  # از budgets.yaml (opslib نیاز نداریم چون فقط خواندنی است)
    spend_pct = (month_aud / cap_monthly * 100) if cap_monthly else 0
    details["month_spend_aud"] = round(month_aud, 4)
    details["cap_monthly_aud"] = cap_monthly
    details["spend_pct"] = round(spend_pct, 2)
    if spend_pct > 95:
        score -= 20
    elif spend_pct > 80:
        score -= 10
    elif spend_pct > 50:
        score -= 3

    # divergence: اگر conflicts > 0 → -15
    conflicts = org.get("conflicts", [])
    details["conflict_count"] = len(conflicts)
    if conflicts:
        score -= 15

    # unmapped spend
    unmapped = tel.get("unmapped_musd", {})
    details["unmapped_count"] = len(unmapped)
    if unmapped:
        score -= 5

    score = max(0.0, min(100.0, score))
    details["score"] = round(score, 2)
    return score, details


def compute_health(
    org_path: Path = OPS_STATE / "ORGANISM-STATE.json",
    fit_path: Path = OPS_STATE / "fitness-latest.json",
    tel_path: Path = OPS_STATE / "telemetry-latest.json",
) -> dict:
    """محاسبهٔ health score ترکیبی."""
    org = _load_json(org_path, default={})
    fit = _load_json(fit_path, default={})
    tel = _load_json(tel_path, default={})

    # load external weights
    weights_path = NS_DIR / "health-weights.json"
    weights = DEFAULT_WEIGHTS.copy()
    if weights_path.exists():
        try:
            weights.update(_load_json(weights_path, default={}))
        except Exception as e:  # noqa: BLE001
            logger.warning("weights load failed: %s", e)

    sys_score, sys_details = _compute_system_score(org)
    fit_score, fit_details = _compute_fitness_score(fit)
    tel_score, tel_details = _compute_telemetry_score(tel, org)

    overall = (
        weights["system"] * sys_score
        + weights["fitness"] * fit_score
        + weights["telemetry"] * tel_score
    )

    alert_count = _read_alert_count()
    # هر alert فعال = -2 (تا سقف -10)
    overall -= min(10, alert_count * 2)
    overall = max(0.0, min(100.0, overall))

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "generated": generated,
        "overall": round(overall, 2),
        "status": _status_label(overall),
        "status_emoji": _status_emoji(overall),
        "subscores": {
            "system": round(sys_score, 2),
            "fitness": round(fit_score, 2),
            "telemetry": round(tel_score, 2),
        },
        "details": {
            "system": sys_details,
            "fitness": fit_details,
            "telemetry": tel_details,
        },
        "alerts": {
            "governor_alert_count": alert_count,
            "integrity_alerts": fit.get("integrity_alerts", []),
            "conflicts": org.get("conflicts", []),
        },
        "weights": weights,
        "source": {
            "organism_state": str(org_path),
            "fitness_latest": str(fit_path),
            "telemetry_latest": str(tel_path),
        },
    }


def _status_label(score: float) -> str:
    if score >= 80:
        return "سالم"
    if score >= 60:
        return "هشدار سبک"
    if score >= 40:
        return "هشدار متوسط"
    if score >= 20:
        return "بحرانی"
    return "بحران"


def _status_emoji(score: float) -> str:
    if score >= 80:
        return "🟢"
    if score >= 60:
        return "🟡"
    if score >= 40:
        return "🟠"
    if score >= 20:
        return "🔴"
    return "💀"


def emit_js(health: dict, out_dir: Path = NS_DIR) -> Path:
    """نوشتنِ health-data.js به فرمتِ OCTOPUS."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "health-data.js"
    js = "window.HEALTH_DATA = " + json.dumps(health, ensure_ascii=False, default=str) + ";\n"
    out_path.write_text(js, encoding="utf-8")
    logger.info("health-data.js refreshed: %s chars (%s)", len(js), out_path)
    return out_path


def main() -> int:
    health = compute_health()
    emit_js(health)
    print(json.dumps(health, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
