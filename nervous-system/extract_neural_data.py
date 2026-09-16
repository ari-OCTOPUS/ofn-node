#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_neural_data.py — CH-16: Neural telemetry extractor.

این extractor دادهٔ neural stack را از `_ops/neural/` و `_ops/chrono_rhythm/`
می‌خواند و یک `neural-data.js` واحد می‌سازد که OCTOPUS worlds مصرف می‌کنند.

Source → Transform → Sink:
  _ops/neural/*.json  +  _ops/chrono_rhythm/rhythm.py  +  _ops/neural/circadian.py
  → extract_neural_data.py
  → nervous-system/neural-data.js  →  OCTOPUS/worlds/01-cockpit + 06-time

Rules:
  • Read-only — هیچ mutation
  • Graceful fallback — اگر فایل/ماژول نبود، null/defaults
  • Farsi comments + English technical terms
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── paths ────────────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
OPS_DIR = HERE.parent / "_ops"
NS_DIR = HERE
OCTOPUS_DIR = HERE.parent / "OCTOPUS" / "worlds"
STATE_FILE = OPS_DIR / "state" / "ORGANISM-STATE.json"

# ─── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract_neural")


def _read_json(path: Path, default: Any = None) -> Any:
    """خواندنِ JSON با fallback."""
    if not path.exists():
        logger.debug("file missing: %s", path)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("read error %s: %s", path, exc)
        return default


def _compute_circadian() -> dict | None:
    """compute circadian readiness از ماژولِ `_ops/neural/circadian.py`."""
    try:
        sys.path.insert(0, str(OPS_DIR / "neural"))
        from circadian import CircadianMap  # noqa: E402

        cmap = CircadianMap()
        now = datetime.now().hour
        return {
            "hour": now,
            "phase": cmap.phase(now),
            "readiness": round(cmap.readiness(now), 2),
            "is_maintenance": cmap.is_maintenance(now),
            "best_platform": cmap.best_platform(now),
            "source": "CircadianMap",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("circadian compute failed: %s", exc)
        return None


def _compute_rhythm() -> dict | None:
    """compute rhythm state از ماژولِ `_ops/chrono_rhythm/rhythm.py`."""
    try:
        sys.path.insert(0, str(OPS_DIR / "chrono_rhythm"))
        from rhythm import Rhythm  # noqa: E402

        r = Rhythm()
        st = r.step(readiness=0.6, stress=0.2, novelty=0.3, sigma=0.5)
        return {
            "mode_color": st.mode_color,
            "mode_focus": st.mode_focus,
            "T_beat": round(st.T_beat, 2),
            "hrv": round(st.hrv, 4),
            "tau": round(st.tau, 3),
            "gamma": round(st.gamma, 3),
            "coherence_r": round(st.coherence_r, 3),
            "readiness": round(st.readiness, 2),
            "stress": round(st.stress, 2),
            "novelty": round(st.novelty, 2),
            "source": "Rhythm.step",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("rhythm compute failed: %s", exc)
        return None


def _read_hebbian() -> dict | None:
    """خواندنِ hebbian state از `_ops/neural/hebbian.json`."""
    data = _read_json(OPS_DIR / "neural" / "hebbian.json", [])
    if not data:
        return None
    latest = data[-1] if isinstance(data, list) else data
    return {
        "signals": latest.get("signals", []),
        "strength": latest.get("strength", 0.0),
        "co_occurrences": latest.get("co_occurrences", 0),
        "last_seen": latest.get("last_seen"),
        "source": "hebbian.json",
    }


def _read_consolidation() -> dict | None:
    """خواندنِ consolidation state از `_ops/neural/consolidation.json`."""
    data = _read_json(OPS_DIR / "neural" / "consolidation.json", [])
    if not data:
        return None
    latest = data[-1] if isinstance(data, list) else data
    cycles = len(data) if isinstance(data, list) else 0
    return {
        "cycles_total": cycles,
        "latest_cycle": latest.get("cycle"),
        "insights": latest.get("insights", []),
        "verified_sources": latest.get("verified_sources", []),
        "discarded_sources": latest.get("discarded_sources", []),
        "timestamp": latest.get("timestamp"),
        "source": "consolidation.json",
    }


def _read_organism_neural() -> dict:
    """خواندنِ فیلدهای neural از ORGANISM-STATE.json (اگر وجود داشته باشند)."""
    org = _read_json(STATE_FILE, {})
    neural_fields = {}

    # wiring flags
    w = org.get("wiring", {})
    neural_fields["wiring_on"] = {
        "wire_neural": w.get("wire_neural", False),
        "wire_rhythm": w.get("wire_rhythm", False),
        "wire_circadian": w.get("wire_circadian", False),
        "wire_sprint": w.get("wire_sprint", False),
    }

    # protective state
    if "protective_mode" in org:
        neural_fields["protective_mode"] = org["protective_mode"]
    if "protective_reason" in org:
        neural_fields["protective_reason"] = org["protective_reason"]

    # chrono beat (shared with neural)
    ch = org.get("chrono", {})
    neural_fields["chrono_beat"] = ch.get("beat")
    neural_fields["metabolic_age"] = ch.get("metabolic_age")

    # cardiac-budget stress proxy
    card = org.get("cardiac", {})
    budget = card.get("budget", {})
    if budget:
        neural_fields["budget_stress_proxy"] = {
            "spent": budget.get("spent"),
            "daily_cap": budget.get("daily_cap"),
            "remaining": budget.get("remaining"),
            "depleted": budget.get("depleted", False),
        }

    return neural_fields


def _compute_vitals(rhythm: dict | None, circadian: dict | None,
                    organism: dict) -> dict:
    """ترکیبِ داده‌ها → vitals bar برای cockpit."""
    mode_color = (rhythm or {}).get("mode_color", "GREEN")
    readiness = (circadian or {}).get("readiness", 0.7)
    stress = (rhythm or {}).get("stress", 0.0)

    # protective mode override
    protective = organism.get("protective_mode", False)
    if protective:
        mode_color = "RED"

    # advisory text (Farsi)
    if mode_color == "GREEN":
        advisory = "سیستم در حالتِ پایدار — ضربانِ سبز"
    elif mode_color == "AMBER":
        advisory = "احتیاط — استرس/نوآوری بالا؛ ضربانِ کهربایی"
    else:
        advisory = "توقفِ حفاظتی — فقط observation؛ ضربانِ قرمز"

    return {
        "mode_color": mode_color,
        "readiness": readiness,
        "stress": stress,
        "protective": protective,
        "advisory": advisory,
        "bar_color": {"GREEN": "#34d399", "AMBER": "#f59e0b", "RED": "#ef4444"}.get(mode_color, "#34d399"),
    }


def main() -> None:
    """entrypoint: read sources → compute → write neural-data.js."""
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── read sources ──────────────────────────────────────────────────────────
    organism_neural = _read_organism_neural()
    circadian = _compute_circadian()
    rhythm = _compute_rhythm()
    hebbian = _read_hebbian()
    consolidation = _read_consolidation()

    # ── compute derived ───────────────────────────────────────────────────────
    vitals = _compute_vitals(rhythm, circadian, organism_neural)

    # ── assemble payload ──────────────────────────────────────────────────────
    neural_data = {
        "generated": generated,
        "source": {
            "organism_state": str(STATE_FILE),
            "hebbian_json": str(OPS_DIR / "neural" / "hebbian.json"),
            "consolidation_json": str(OPS_DIR / "neural" / "consolidation.json"),
            "circadian_module": "_ops.neural.circadian",
            "rhythm_module": "_ops.chrono_rhythm.rhythm",
        },
        "vitals": vitals,
        "rhythm": rhythm,
        "circadian": circadian,
        "hebbian": hebbian,
        "consolidation": consolidation,
        "organism": organism_neural,
    }

    # ── write JS ──────────────────────────────────────────────────────────────
    js_path = NS_DIR / "neural-data.js"
    js = "window.NEURAL_DATA = " + json.dumps(neural_data, ensure_ascii=False, default=str) + ";\n"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)
    logger.info("neural-data.js refreshed — %d chars (%s)", len(js), generated)

    # ── optional: also write into OCTOPUS dir for standalone use ──────────────
    octo_js_path = OCTOPUS_DIR / "neural-data.js"
    try:
        with open(octo_js_path, "w", encoding="utf-8") as f:
            f.write(js)
        logger.info("OCTOPUS/worlds/neural-data.js mirrored")
    except OSError as exc:
        logger.warning("mirror to OCTOPUS failed (non-fatal): %s", exc)


if __name__ == "__main__":
    main()
