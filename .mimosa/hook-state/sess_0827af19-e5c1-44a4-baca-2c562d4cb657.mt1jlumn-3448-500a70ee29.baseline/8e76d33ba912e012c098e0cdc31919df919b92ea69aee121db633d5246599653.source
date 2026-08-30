"""Math Control Spine — gather LIVE equation signals → pulse + soft effects.

Owner 2026-08-12: soft ceiling, shadow non-blocking, arm-now.
Fail-soft everywhere. Never authorizes money/send/ledger/code-apply.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_STATE = Path(os.environ.get("OCTOPUS_STATE_DIR") or (_OPS / "state"))
_PULSE = _STATE / "pulse" / "math-control-latest.json"
_OBSERVE = _STATE / "pulse" / "math-control-observe.jsonl"

FLAG_SPINE = "OCTOPUS_MATH_CONTROL_SPINE"
FLAG_AUTOTUNE = "OCTOPUS_MATH_AUTOTUNE_KNOBS"
FLAG_OBSERVE = "OCTOPUS_MATH_CONTROL_OBSERVE"

# Soft clamps (env-overridable)
RANK_BIAS_CAP = float(os.environ.get("OCTOPUS_MATH_RANK_BIAS_CAP", "1.0"))
THINK_DELTA_CAP = int(os.environ.get("OCTOPUS_MATH_THINK_DELTA_CAP", "4"))


def _flag(name: str, default: bool = True) -> bool:
    """Soft-ceiling default ON; explicit 0/false/off wins."""
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def enabled() -> bool:
    return _flag(FLAG_SPINE, True)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _read_json(path: Path) -> Any:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _hebbian_assoc() -> dict:
    path = _OPS / "neural" / "hebbian.json"
    data = _read_json(path)
    if not isinstance(data, list) or not data:
        return {"assoc_strength": 0.0, "top_pair": None, "n_pairs": 0}
    best = None
    best_s = -1.0
    for row in data:
        if not isinstance(row, dict):
            continue
        try:
            s = float(row.get("strength") or 0.0)
        except (TypeError, ValueError):
            continue
        if s > best_s:
            best_s = s
            best = row
    pair = None
    if isinstance(best, dict):
        sigs = best.get("signals") or []
        if isinstance(sigs, list) and len(sigs) >= 2:
            pair = f"{sigs[0]}+{sigs[1]}"
    return {
        "assoc_strength": _clamp(best_s if best_s >= 0 else 0.0, 0.0, 1.0),
        "top_pair": pair,
        "n_pairs": len(data),
    }


def _bcm_forgetting() -> dict:
    path = _STATE / "bcm-weights.json"
    data = _read_json(path)
    if not isinstance(data, dict):
        return {"bcm_forgetting": 0.0, "n_weights": 0, "mean_w": None}
    weights = data.get("weights") if isinstance(data.get("weights"), dict) else data
    vals = []
    if isinstance(weights, dict):
        for v in weights.values():
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
    if not vals:
        return {"bcm_forgetting": 0.0, "n_weights": 0, "mean_w": None}
    mean_w = sum(vals) / len(vals)
    # Near saturation (cap≈4) → high forgetting pressure signal
    sat = _clamp(mean_w / 4.0, 0.0, 1.0)
    return {"bcm_forgetting": round(sat, 4), "n_weights": len(vals), "mean_w": round(mean_w, 4)}


def _spectral_true() -> dict:
    """Prefer wiring._real_spectral_sigma; never invent sigma on empty graph."""
    try:
        import sys
        if str(_OPS) not in sys.path:
            sys.path.insert(0, str(_OPS))
        import wiring as _w  # noqa: WPS433
        s = _w._real_spectral_sigma()
        if s is None:
            return {"spectral_sigma_true": None, "sigma_source": "unavailable"}
        return {
            "spectral_sigma_true": float(s),
            "sigma_source": "doctor.spectral.estimate_sigma",
            "sigma_is_replication_ratio": False,
        }
    except Exception:  # noqa: BLE001
        return {"spectral_sigma_true": None, "sigma_source": "error"}


def _organism_slice() -> dict:
    org = _read_json(_STATE / "ORGANISM-STATE.json") or {}
    if not isinstance(org, dict):
        org = {}
    pain = 0.0
    try:
        pa = org.get("pain_assessment") or {}
        if isinstance(pa, dict):
            pain = float(pa.get("pain") or pa.get("level") or 0.0)
    except (TypeError, ValueError):
        pain = 0.0
    rhythm_color = None
    arb = org.get("arbiter") if isinstance(org.get("arbiter"), dict) else {}
    if arb:
        rhythm_color = arb.get("color")
    chrono = org.get("chrono") if isinstance(org.get("chrono"), dict) else {}
    if rhythm_color is None and chrono:
        rhythm_color = chrono.get("mode_color")
    period = None
    try:
        if arb.get("effective_period_s") is not None:
            period = float(arb["effective_period_s"])
    except (TypeError, ValueError):
        period = None
    return {
        "pain_pressure": _clamp(pain, 0.0, 1.0),
        "rhythm_color": str(rhythm_color or "") or None,
        "schedule_period_s": period,
        "protective_skip": bool(org.get("protective_skip")),
        "beat": org.get("beat"),
        "halted": bool(org.get("halted")),
    }


def _identity_health() -> dict:
    try:
        import sys
        if str(_OPS) not in sys.path:
            sys.path.insert(0, str(_OPS))
        import identity_equations as ie  # noqa: WPS433
        rep = ie.evaluate()
        ids = (rep or {}).get("identities") or {}
        vals = []
        for key in ("learner", "earner", "guardian", "creator", "organism"):
            node = ids.get(key) or {}
            try:
                vals.append(float(node.get("value")))
            except (TypeError, ValueError):
                continue
        if not vals:
            return {"identity_health": None, "identities": {}}
        mean = sum(vals) / len(vals)
        return {
            "identity_health": round(mean, 4),
            "identities": {k: (ids.get(k) or {}).get("value") for k in
                           ("learner", "earner", "guardian", "creator", "organism")},
        }
    except Exception:  # noqa: BLE001
        return {"identity_health": None, "identities": {}}


def _sog_voi() -> dict:
    lock = _read_json(_STATE / "sim" / "PULSE-EQUATIONS-LOCKED.json")
    if not isinstance(lock, dict):
        return {"sog_voi": None, "sog_locked": False}
    # Locked bundle exists → cite presence; do not invent VoI number
    return {
        "sog_voi": None,
        "sog_locked": True,
        "sog_keys": list((lock.get("locked") or lock.get("equations") or []))[:8]
        if isinstance(lock.get("locked") or lock.get("equations"), list)
        else list(lock.keys())[:8],
    }


def suggest_knob_deltas(snap: dict) -> dict[str, int]:
    """Soft AUTO_KNOBS deltas from math snap. Bounded; never code/money."""
    deltas: dict[str, int] = {}
    sigma = snap.get("spectral_sigma_true")
    pain = float(snap.get("pain_pressure") or 0.0)
    health = snap.get("identity_health")
    color = str(snap.get("rhythm_color") or "").upper()

    # High fragility / pain → think less often (higher EVERY_N)
    think_delta = 0
    if isinstance(sigma, (int, float)) and float(sigma) >= 1.2:
        think_delta += 2
    if pain >= 0.7:
        think_delta += 2
    elif pain >= 0.5:
        think_delta += 1
    if color in ("RED",):
        think_delta += 1
    think_delta = int(_clamp(think_delta, -THINK_DELTA_CAP, THINK_DELTA_CAP))
    if think_delta:
        deltas["CORTEX_THINK_EVERY_N"] = think_delta

    # Healthy + green → slightly denser heart samples / chrono nudge (negative = more often)
    if isinstance(health, (int, float)) and float(health) >= 0.6 and color == "GREEN" and pain < 0.4:
        deltas["CHRONO_NUDGE_EVERY_N_BEATS"] = -60
        deltas["HEART_SAMPLE_INTERVAL_S"] = -300
    elif color in ("AMBER", "YELLOW", "RED") or pain >= 0.6:
        deltas["CHRONO_NUDGE_EVERY_N_BEATS"] = 120
        deltas["HEART_SAMPLE_INTERVAL_S"] = 600

    return deltas


def _rank_bias(snap: dict) -> float:
    """Positive bias raises priority numerically lower _rank after subtract... 

    improve sorts ascending by _rank. We return a value to SUBTRACT from _rank
    for math-urgent items (higher urgency → larger positive return).
    """
    urgency = 0.0
    sigma = snap.get("spectral_sigma_true")
    if isinstance(sigma, (int, float)) and float(sigma) >= 1.2:
        urgency += 0.4
    pain = float(snap.get("pain_pressure") or 0.0)
    urgency += 0.5 * pain
    assoc = float(snap.get("assoc_strength") or 0.0)
    if assoc >= 0.8:
        urgency += 0.2
    health = snap.get("identity_health")
    if isinstance(health, (int, float)) and float(health) < 0.35:
        urgency += 0.3
    return _clamp(urgency, 0.0, RANK_BIAS_CAP)


def collect() -> dict:
    """Read-only gather of equation signals. Safe when disabled (still returns stub)."""
    heb = _hebbian_assoc()
    bcm = _bcm_forgetting()
    sig = _spectral_true()
    org = _organism_slice()
    ident = _identity_health()
    sog = _sog_voi()

    # Soft schedule bias hint (seconds); consumers may ignore
    period_bias = 0.0
    color = str(org.get("rhythm_color") or "").upper()
    if color == "RED":
        period_bias = 15.0
    elif color in ("AMBER", "YELLOW"):
        period_bias = 5.0
    elif color == "GREEN":
        period_bias = -2.0
    if float(org.get("pain_pressure") or 0) >= 0.7:
        period_bias += 10.0

    snap = {
        "schema": "math-control.v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "enabled": enabled(),
        "autotune": _flag(FLAG_AUTOTUNE, True),
        "external_effect": False,
        "may_authorize": False,
        "shadow_blocks_effects": False,
        **org,
        **heb,
        **bcm,
        **sig,
        **ident,
        **sog,
        "schedule_period_bias": round(period_bias, 3),
        "rank_bias": round(_rank_bias({**org, **heb, **sig, **ident}), 4),
        "knob_deltas": suggest_knob_deltas({**org, **heb, **sig, **ident}),
        "effects": [],
        "equations_touching": [],
    }
    touching = []
    if heb.get("n_pairs"):
        touching.append("#2_hebbian")
    if bcm.get("n_weights"):
        touching.append("#1_bcm")
    if org.get("pain_pressure") is not None:
        touching.append("#3_pain")
    if sig.get("spectral_sigma_true") is not None:
        touching.append("#14_sigma")
    if ident.get("identity_health") is not None:
        touching.append("#5-9_identity")
    if org.get("schedule_period_s") is not None:
        touching.append("#17_rhythm")
        touching.append("#11_control_law")
    if sog.get("sog_locked"):
        touching.append("#10_sog")
    snap["equations_touching"] = touching

    effects = []
    if snap.get("protective_skip"):
        effects.append("protective_skip")
    if snap.get("knob_deltas") and snap.get("autotune"):
        effects.append("autotune_propose")
    if snap.get("rank_bias", 0) > 0:
        effects.append("improve_rank_bias")
    if abs(float(snap.get("schedule_period_bias") or 0)) > 0:
        effects.append("schedule_bias_hint")
    snap["effects"] = effects
    return snap


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _observe_append(payload: dict) -> None:
    """Parallel telemetry — must never gate effects. Fail-soft."""
    if not _flag(FLAG_OBSERVE, True):
        return
    try:
        _OBSERVE.parent.mkdir(parents=True, exist_ok=True)
        line = {
            "ts": payload.get("ts"),
            "rank_bias": payload.get("rank_bias"),
            "pain_pressure": payload.get("pain_pressure"),
            "spectral_sigma_true": payload.get("spectral_sigma_true"),
            "assoc_strength": payload.get("assoc_strength"),
            "identity_health": payload.get("identity_health"),
            "knob_deltas": payload.get("knob_deltas"),
            "effects": payload.get("effects"),
            "shadow_observe": True,
        }
        with _OBSERVE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def load_latest() -> dict:
    data = _read_json(_PULSE)
    return data if isinstance(data, dict) else {}


def beat(write: bool = True) -> dict:
    """Collect + persist pulse. When spine disabled, still writes enabled=false stub
    so consumers see honest state — effects should no-op on enabled=false."""
    snap = collect()
    if not enabled():
        snap["effects"] = []
        snap["knob_deltas"] = {}
        snap["rank_bias"] = 0.0
    if write:
        try:
            _atomic_write(_PULSE, snap)
        except Exception:  # noqa: BLE001
            pass
        # Observe NEVER blocks — even if this fails, snap already computed
        _observe_append(snap)
    return snap
