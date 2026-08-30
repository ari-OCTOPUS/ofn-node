"""test_interview_organism_20260816 — MEGAPROMPT-INTERVIEW-OCTOPUS-ORGANISM.

ایده ۱ حوزه G · ایده ۴ S6 سایه · ایده ۶ observation.v1
ثبت در run_all.py نشده (WORKLOCK).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("interview-organism")
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "budget"))

import importlib  # noqa: E402
import improve  # noqa: E402
importlib.reload(improve)

from observatory.observation_v1 import PARSE_DRIFT, parse_body, SCHEMA  # noqa: E402
from predictor.persistence import brier, exponential_smoother, transition_indices  # noqa: E402


def _signals_math(identity_health: float, delta: int) -> dict:
    return {
        "matrix": {"gaps": [], "maturity_pct": 0},
        "doctor_rfcs": [],
        "synthesis": {},
        "smallest_fix": "",
        "math_control": {
            "enabled": True,
            "autotune": True,
            "identity_health": identity_health,
            "pain_pressure": 0.0,
            "spectral_sigma_true": None,
            "assoc_strength": 0.99,
            "knob_deltas": {"CHRONO_NUDGE_EVERY_N_BEATS": delta},
            "rank_bias": 0.0,
            "effects": ["autotune_propose"],
        },
    }


def t_identity_rationale_names_health():
    """ایده ۱/G: rationale هویت را پنهان نمی‌کند (DA-5: ذکر، نه گیت)."""
    knob_path = Path(ENV["ops"]) / "state" / "cortex" / "auto-knobs.json"
    knob_path.parent.mkdir(parents=True, exist_ok=True)
    knob_path.write_text(json.dumps({"CHRONO_NUDGE_EVERY_N_BEATS": 600}), encoding="utf-8")
    props = improve.generate_proposals(_signals_math(0.672, -60))
    math_props = [p for p in props if p.get("source") == "math_spine"]
    assert math_props, f"باید math_spine بسازد: { [p.get('source') for p in props][:8] }"
    p = math_props[0]
    assert "identity_health=0.672" in p["rationale"], p["rationale"]
    assert p.get("identity_health") == 0.672


def t_persistence_beats_constant_on_clusters_loses_on_transitions():
    """ایده ۴: مسیر پایداری روی رژیم جاری بهتر است؛ روی گذار بدتر — p_base عوض نشد."""
    ys = [0.0] * 40 + [1.0] * 40 + [0.0] * 40
    p0 = sum(ys) / len(ys)
    preds = exponential_smoother(ys, alpha=0.5, p0=p0)
    pairs = list(zip(preds, ys))
    const = [(p0, y) for y in ys]
    assert brier(pairs) < brier(const)
    trans = transition_indices(ys)
    assert trans == [40, 80]
    t_pairs = [(preds[i], ys[i]) for i in trans]
    t_const = [(p0, ys[i]) for i in trans]
    assert brier(t_pairs) > brier(t_const)


def t_observation_v1_usgs_ok_and_drift():
    """ایده ۶: پارس قطعی؛ بدنه‌ی خراب حدس نمی‌زند؛ به تصمیم وصل نیست."""
    body = json.dumps({
        "features": [{
            "properties": {"mag": 4.2, "place": "test", "time": 1},
        }],
    }).encode("utf-8")
    ok = parse_body(url="https://earthquake.usgs.gov/x", fetched_at="2026-08-16T00:00:00Z",
                    body=body)
    assert ok["ok"] is True and ok["schema"] == SCHEMA
    assert ok["n_events"] == 1 and ok["feeds_organism_decision"] is False
    bad = parse_body(url="https://earthquake.usgs.gov/x", fetched_at="2026-08-16T00:00:00Z",
                     body=b"not-json")
    assert bad["ok"] is False and bad["error"] == PARSE_DRIFT and bad["events"] == []
    missing = parse_body(url="https://earthquake.usgs.gov/x", fetched_at="2026-08-16T00:00:00Z",
                         body=json.dumps({"features": [{"properties": {"mag": 1}}]}).encode())
    assert missing["ok"] is False and missing["error"] == PARSE_DRIFT


if __name__ == "__main__":
    failed = 0
    for fn in (
        t_identity_rationale_names_health,
        t_persistence_beats_constant_on_clusters_loses_on_transitions,
        t_observation_v1_usgs_ok_and_drift,
    ):
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", fn.__name__, type(e).__name__, e)
    raise SystemExit(1 if failed else 0)
