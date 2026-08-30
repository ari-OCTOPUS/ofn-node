#!/usr/bin/env python3
"""causal_guard.py — Causal Claim Guard (EQUIP G10).

ADR-013 (causal-selfmodel) is REJECTED in this vault.
Causal claims must NEVER be treated as authority.
Correlation != causation.

This module:
  1. Classifies claims as correlation, prediction, or causal.
  2. Marks causal claims with authority_level="advisory" (never authority).
  3. Detects spurious causal language in model output.
  4. Provides synthetic test data for acceptance scenario.

No model/agent can change policy/goal/identity based on causal claims.
"""
from __future__ import annotations

import re
from typing import Any


# ── Claim strength classification ──────────────────────────────────────────────
_CAUSAL_PATTERNS = re.compile(
    r"(causes?|because of|leads to|results in|produces|creates?|"
    r"دلیل|علت|سبب|منجر به|نتیجهٔ)",
    re.I,
)

_CORRELATION_PATTERNS = re.compile(
    r"(correlat|associated with|related to|linked to|tied to|"
    r"همبستگی|مربوط|مرتبط|связан)",
    re.I,
)

_PREDICTION_PATTERNS = re.compile(
    r"(predict|forecast|expect|likely|probability|chance|"
    r"پیش‌بینی|احتمال|انتظار)",
    re.I,
)

# ── Spurious causal language ─────────────────────────────────────────────────
_SPURIOUS_CAUSAL = re.compile(
    r"(therefore.*(must|should|will necessarily)|"
    r"this (clearly|obviously|definitely|certainly) (means|proves|shows)|"
    r"this is (clearly|obviously) caused by|"
    r"we can conclude.*because|"
    r"این (قطعا|مسلما|بدون شک) (نشان می‌دهد|ثابت می‌کند|معنی))",
    re.I,
)


def classify_claim(text: str) -> dict[str, Any]:
    """Classify a claim as correlation, prediction, or causal.

    Returns {claim_strength, confidence, markers, advisory_note}.
    """
    t = str(text or "")
    markers: list[str] = []

    has_causal = bool(_CAUSAL_PATTERNS.search(t))
    has_correlation = bool(_CORRELATION_PATTERNS.search(t))
    has_prediction = bool(_PREDICTION_PATTERNS.search(t))

    if has_causal:
        markers.append("causal_language")
    if has_correlation:
        markers.append("correlation_language")
    if has_prediction:
        markers.append("prediction_language")

    # Priority: causal > correlation > prediction > speculative
    if has_causal and has_correlation:
        # Mixed signal — default to correlation (safer)
        claim_strength = "correlation"
        confidence = 0.3
        advisory = ("Mixed causal/correlation language detected. "
                    "Defaulting to correlation (ADR-013 REJECTED: "
                    "causal claims are not authority).")
    elif has_causal:
        claim_strength = "causal"
        confidence = 0.2  # Low confidence for causal claims
        advisory = ("Causal claim detected. ADR-013 REJECTED: "
                    "this claim is advisory only, never authority. "
                    "Correlation does not imply causation.")
    elif has_correlation:
        claim_strength = "correlation"
        confidence = 0.5
        advisory = "Correlation claim. Does not imply causation."
    elif has_prediction:
        claim_strength = "prediction"
        confidence = 0.4
        advisory = "Predictive claim. Subject to calibration."
    else:
        claim_strength = "speculative"
        confidence = 0.1
        advisory = "No causal/predictive markers detected."

    return {
        "claim_strength": claim_strength,
        "confidence": confidence,
        "markers": markers,
        "advisory_note": advisory,
        "is_authority": False,  # NEVER authority
        "adr013_rejected": True,
    }


def detect_spurious_causal(text: str) -> dict[str, Any]:
    """Detect spurious causal reasoning patterns.

    Returns {detected, patterns_found, advisory}.
    """
    t = str(text or "")
    matches = list(_SPURIOUS_CAUSAL.finditer(t))
    patterns = [m.group() for m in matches]

    return {
        "detected": len(patterns) > 0,
        "patterns_found": patterns[:5],
        "advisory": ("Spurious causal reasoning detected. "
                     "Claims of necessity/certainty from correlation "
                     "are not supported.") if patterns else None,
    }


def guard_output(output: dict[str, Any]) -> dict[str, Any]:
    """Guard structured output for causal claim violations.

    Ensures causal claims are marked as non-authoritative.
    ADR-013: causal-selfmodel REJECTED.
    """
    guarded = dict(output)

    # Check text fields for causal language
    text_fields = ["description", "statement", "observation", "findings"]
    text = " ".join(str(guarded.get(f, "")) for f in text_fields)

    classification = classify_claim(text)
    guarded["_causal_guard"] = classification

    # Enforce: causal claims are never authority
    if classification["claim_strength"] == "causal":
        guarded["is_authority"] = False
        guarded["authority_level"] = "advisory"
        guarded["_adr013_note"] = ("ADR-013 REJECTED: causal claims "
                                   "are never authoritative in this vault")

    # Check for spurious causal reasoning
    spurious = detect_spurious_causal(text)
    if spurious["detected"]:
        guarded["_spurious_causal_detected"] = True
        guarded["_spurious_causal_advisory"] = spurious["advisory"]

    return guarded


# ── Synthetic data for acceptance scenario ────────────────────────────────────

CORRELATION_CAUSAL_FIXTURE = {
    "description": "Synthetic dataset to demonstrate correlation != causation",
    "data": [
        {"x": 10, "y": 25, "z": "A"},
        {"x": 20, "y": 50, "z": "A"},
        {"x": 30, "y": 75, "z": "B"},
        {"x": 40, "y": 100, "z": "B"},
        {"x": 50, "y": 125, "z": "A"},
        {"x": 60, "y": 150, "z": "A"},
        {"x": 70, "y": 175, "z": "B"},
        {"x": 80, "y": 200, "z": "B"},
    ],
    "ground_truth": {
        "x_and_y_correlated": True,
        "x_causes_y": False,
        "z_causes_y": False,
        "confound": "hidden variable W drives both x and y",
        "explanation": (
            "x and y are perfectly correlated (r=1.0) because both are "
            "driven by a hidden variable W (W = x/10, y = W*25). "
            "x does not cause y. z is independent noise. "
            "A causal claim 'x causes y' would be WRONG."
        ),
    },
}


def analyze_synthetic_causal() -> dict[str, Any]:
    """Analyze the synthetic fixture to demonstrate correlation != causation.

    Returns analysis with clear causal guard markings.
    """
    data = CORRELATION_CAUSAL_FIXTURE["data"]
    truth = CORRELATION_CAUSAL_FIXTURE["ground_truth"]

    # Compute correlation (x vs y)
    n = len(data)
    if n < 2:
        return {"error": "insufficient_data"}

    xs = [d["x"] for d in data]
    ys = [d["y"] for d in data]

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / n
    var_x = sum((x - mean_x) ** 2 for x in xs) / n
    var_y = sum((y - mean_y) ** 2 for y in ys) / n

    if var_x == 0 or var_y == 0:
        r = 0.0
    else:
        r = cov_xy / (var_x ** 0.5 * var_y ** 0.5)

    # Guard the analysis output
    analysis = {
        "correlation_r": round(r, 4),
        "x_causes_y": False,
        "claim_strength": "correlation",
        "is_authority": False,
        "ground_truth": truth["explanation"],
        "adr013_rejected": True,
    }

    return guard_output(analysis)


if __name__ == "__main__":
    # Test claim classification
    tests = [
        "Smoking causes lung cancer",
        "Ice cream sales and drowning deaths are correlated",
        "Rain is predicted tomorrow with 80% probability",
        "This obviously means the model is broken",
        "Regular text without causal claims",
    ]
    for t in tests:
        c = classify_claim(t)
        print(f"  [{c['claim_strength']:12s}] {t[:50]}")

    # Test causal analysis
    analysis = analyze_synthetic_causal()
    print(f"\nSynthetic analysis: r={analysis.get('correlation_r')}, "
          f"causal={analysis.get('x_causes_y')}, "
          f"guard={analysis.get('_causal_guard', {}).get('claim_strength')}")
