#!/usr/bin/env python3
"""confidence_calibrator.py — Confidence Calibration with Outcome Ledger (EQUIP G10).

Ties predictions and hypotheses to actual outcomes via a calibration ledger.
Prevents confidence inflation: high confidence predictions that fail reduce
future calibration weight.

Key design:
  - Outcome ledger: append-only JSONL of (prediction_id, predicted, actual, ts).
  - Calibration score: Brier score + confidence-inflation detection.
  - No model can change policy/goal/identity based on high confidence alone.
  - Confidence is advisory, never authority.

Invariant: outcome feedback only from probes, tests, or owner verification.
Never self-report as outcome evidence.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

from structured_schemas import _now, _id

LEDGER_PATH = opslib.STATE_DIR / "cognition" / "confidence-ledger.jsonl"
SCHEMA_VERSION = "confidence-calibrator.v1"


# ── Brier Score ───────────────────────────────────────────────────────────────

def brier_score(pairs: list[tuple[float, float]]) -> float:
    """Compute Brier score from (predicted_probability, actual_outcome) pairs.

    Lower is better. 0 = perfect calibration. 1 = worst.
    Empty list = return 0.5 (maximum uncertainty).
    """
    if not pairs:
        return 0.5
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def calibration_bins(
    pairs: list[tuple[float, float]],
    n_bins: int = 10,
) -> list[dict[str, Any]]:
    """Compute calibration bins for reliability diagram.

    Returns list of {bin_center, mean_predicted, mean_actual, count}.
    """
    if not pairs:
        return []

    bins: list[list[tuple[float, float]]] = [[] for _ in range(n_bins)]
    for p, y in pairs:
        idx = min(int(p * n_bins), n_bins - 1)
        idx = max(0, min(idx, n_bins - 1))
        bins[idx].append((p, y))

    result = []
    for i, bin_pairs in enumerate(bins):
        if not bin_pairs:
            continue
        center = (i + 0.5) / n_bins
        mean_p = sum(p for p, _ in bin_pairs) / len(bin_pairs)
        mean_a = sum(y for _, y in bin_pairs) / len(bin_pairs)
        result.append({
            "bin_center": round(center, 3),
            "mean_predicted": round(mean_p, 3),
            "mean_actual": round(mean_a, 3),
            "count": len(bin_pairs),
        })
    return result


# ── Inflation Detection ────────────────────────────────────────────────────────

def detect_inflation(pairs: list[tuple[float, float]]) -> dict[str, Any]:
    """Detect confidence inflation: systematic over-estimation.

    Returns {inflated: bool, overconfidence_ratio, details}.
    """
    if len(pairs) < 5:
        return {"inflated": False, "overconfidence_ratio": 0.0,
                "detail": "insufficient_data"}

    high_conf = [(p, y) for p, y in pairs if p >= 0.7]
    if len(high_conf) < 3:
        return {"inflated": False, "overconfidence_ratio": 0.0,
                "detail": "insufficient_high_confidence"}

    mean_predicted = sum(p for p, _ in high_conf) / len(high_conf)
    mean_actual = sum(y for _, y in high_conf) / len(high_conf)

    if mean_actual < 1e-9:
        ratio = float("inf")
    else:
        ratio = mean_predicted / mean_actual

    inflated = ratio > 2.0  # predicted >> actual = inflation
    return {
        "inflated": inflated,
        "overconfidence_ratio": round(ratio, 3),
        "mean_predicted_high_conf": round(mean_predicted, 3),
        "mean_actual_high_conf": round(mean_actual, 3),
        "n_high_confidence": len(high_conf),
    }


# ── Outcome Ledger ────────────────────────────────────────────────────────────

def record_outcome(
    prediction_id: str,
    predicted_probability: float,
    actual_outcome: float,
    *,
    source: str = "probe",
    source_ref: str = "",
) -> dict[str, Any]:
    """Record an outcome in the calibration ledger.

    actual_outcome: 0.0 (failed) or 1.0 (succeeded), or probability.
    source must be probe/test/owner — never self-report.
    """
    entry = {
        "schema_version": SCHEMA_VERSION,
        "prediction_id": str(prediction_id),
        "predicted": float(max(0.0, min(1.0, predicted_probability))),
        "actual": float(max(0.0, min(1.0, actual_outcome))),
        "source": str(source),
        "source_ref": str(source_ref)[:200],
        "ts": _now(),
    }

    # Guard: reject self-reported outcomes
    if source in ("self_report", "model", "llm"):
        entry["rejected"] = True
        entry["rejection_reason"] = "self_report_not_allowed"
        return entry

    try:
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return entry


def read_ledger(limit: int = 1000) -> list[dict[str, Any]]:
    """Read calibration ledger entries."""
    try:
        if not LEDGER_PATH.is_file():
            return []
        lines = LEDGER_PATH.read_text("utf-8", errors="replace").splitlines()
        entries = []
        for line in lines[-limit:]:
            line = line.strip()
            if line:
                try:
                    d = json.loads(line)
                    if isinstance(d, dict) and not d.get("rejected"):
                        entries.append(d)
                except (json.JSONDecodeError, ValueError):
                    continue
        return entries
    except OSError:
        return []


def compute_calibration() -> dict[str, Any]:
    """Compute overall calibration metrics from ledger."""
    entries = read_ledger()
    pairs = [(e["predicted"], e["actual"]) for e in entries
             if "predicted" in e and "actual" in e]

    bs = brier_score(pairs)
    bins = calibration_bins(pairs)
    inflation = detect_inflation(pairs)

    return {
        "brier_score": round(bs, 6),
        "n_entries": len(pairs),
        "calibration_bins": bins,
        "inflation": inflation,
        "well_calibrated": 0.0 < bs < 0.25 and not inflation["inflated"],
        "ts": _now(),
    }


def adjust_confidence(
    raw_confidence: float,
    *,
    calibration: dict[str, Any] | None = None,
) -> float:
    """Adjust raw confidence based on calibration history.

    If model is overconfident, scale down. If well-calibrated, pass through.
    Returns adjusted confidence in [0, 1].
    """
    raw = float(max(0.0, min(1.0, raw_confidence)))
    cal = calibration or compute_calibration()

    if cal["n_entries"] < 10:
        return raw  # insufficient data to adjust

    ratio = cal["inflation"].get("overconfidence_ratio", 1.0)
    if ratio > 2.0:
        # Scale down proportionally
        adjusted = raw / min(ratio, 5.0)
    else:
        # Light calibration: nudge toward Brier-optimal
        adjusted = raw * 0.95 + 0.5 * 0.05

    return float(max(0.0, min(1.0, adjusted)))


if __name__ == "__main__":
    # Self-test with synthetic data
    print(f"Brier(empty): {brier_score([])}")
    print(f"Brier(perfect): {brier_score([(1.0, 1.0), (0.0, 0.0)])}")
    print(f"Brier(worst): {brier_score([(1.0, 0.0), (0.0, 1.0)])}")
    print(f"Brier(overconfident): {brier_score([(0.9, 0.0), (0.8, 0.0), (0.9, 1.0)])}")
    print(f"Inflation detect: {detect_inflation([(0.9, 0.0), (0.8, 0.0), (0.9, 0.1)])}")
    print(f"Adjust(0.9, no data): {adjust_confidence(0.9)}")
