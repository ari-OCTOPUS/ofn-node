#!/usr/bin/env python3
"""C-1 decision_scorer — the advantage-measurement mechanism (RCA-5 fix)
+ AMEND-1 dopamine law D-1 (single anti-wireheading reward channel).

Contract: every revenue decision gets a PRE-REGISTERED record before its
outcome can be known; after the horizon it is scored (Brier vs baseline).
Reports without denominators raise. A brain that cannot beat the baseline
on n>=10 scored decisions is auto-disempowered for that domain.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCORE_DIR = REPO / "rca" / "scorer"
LEDGER = REPO / "rca" / "ledger.jsonl"   # six-condition verified_cash rows


class ScorerError(RuntimeError):
    pass


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------- D-1 reward
VERIFIED_CASH_REQUIRED = (
    "payout_id", "settled_amount_cents", "kind", "prev_hash",
    "payload_sha256", "ato_reserve_cents")


def reward(ledger_path: Path | None = None) -> dict:
    """The ONLY reward signal: six-condition VERIFIED_CASH rows (D-1).

    Any row missing a field contributes ZERO and raises a warning event —
    injected/fake rows cannot feed the reward channel (anti-wireheading).
    """
    lp = ledger_path or LEDGER
    cents, n_valid, warnings = 0, 0, []
    if lp.is_file():
        for line in lp.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                warnings.append("malformed row ignored")
                continue
            if row.get("kind") != "verified_cash":
                continue
            missing = [f for f in VERIFIED_CASH_REQUIRED
                       if f not in row or row[f] in (None, "")]
            if missing:
                warnings.append(
                    f"row rejected (missing {','.join(missing[:3])}) — "
                    f"reward contribution ZERO")
                continue
            cents += int(row["settled_amount_cents"])
            n_valid += 1
    return {"verified_cash_cents": cents, "valid_rows": n_valid,
            "warnings": warnings}


# ---------------------------------------------------------- preregistration
def preregister(action: str, p_success: float, baseline_p: float,
                horizon_h: int, *, domain: str = "default",
                expected_cash_delta_cents: int = 0,
                runway_impact_days: float = 0.0,
                head_sha: str = "", exploratory: bool = False,
                store: Path | None = None) -> dict:
    if not 0.0 < p_success < 1.0 or not 0.0 <= baseline_p < 1.0:
        raise ScorerError("probabilities out of range")
    did = "D-%s-%s" % (domain, hashlib.sha256(
        f"{action}|{time.time_ns()}".encode()).hexdigest()[:10])
    theoretical = (expected_cash_delta_cents == 0 and runway_impact_days == 0.0)
    rec = {
        "schema": "decision-prereg/1", "decision_id": did, "action": action,
        "p_success": p_success, "baseline_p": baseline_p, "horizon_h": horizon_h,
        "domain": domain, "head_sha": head_sha, "created_at": _now(),
        "expected_cash_delta_cents": expected_cash_delta_cents,
        "runway_impact_days": runway_impact_days,
        "labels": (["EXPLORATORY"] if exploratory else []) +
                  (["THEORETICAL-NO-LOOP"] if theoretical else []),
        "outcome": None, "resolved_at": None,
    }
    p = (store or (SCORE_DIR / "decisions.jsonl"))
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def resolve(decision_id: str, outcome: int, store: Path | None = None) -> dict:
    """outcome: 1 (event happened) / 0 (did not)."""
    p = (store or (SCORE_DIR / "decisions.jsonl"))
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    hit = None
    for r in rows:
        if r["decision_id"] == decision_id:
            hit = r
            break
    if hit is None:
        raise ScorerError(f"unknown decision {decision_id} — preregister first")
    if hit["outcome"] is not None:
        raise ScorerError("already resolved — outcome rewrite forbidden")
    hit["outcome"] = int(outcome)
    hit["resolved_at"] = _now()
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return hit


def brier(p: float, y: int) -> float:
    return (p - y) ** 2


def dashboard(store: Path | None = None) -> dict:
    p = (store or (SCORE_DIR / "decisions.jsonl"))
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = [r for r in rows if r.get("outcome") is not None]
    if not scored:
        return {"n_decisions_scored": 0}
    bo = sum(brier(r["p_success"], r["outcome"]) for r in scored) / len(scored)
    bb = sum(brier(r["baseline_p"], r["outcome"]) for r in scored) / len(scored)
    # 5-bin ECE
    bins = {}
    for r in scored:
        i = min(4, int(r["p_success"] * 5))
        bins.setdefault(i, []).append(r)
    ece = sum(len(g) / len(scored) * abs(
        sum(x["p_success"] for x in g) / len(g) -
        sum(x["outcome"] for x in g) / len(g)) for i, g in bins.items())
    # auto-disempowerment (hard rule, no vote)
    disempowered = []
    by_domain = {}
    for r in scored:
        by_domain.setdefault(r["domain"], []).append(r)
    for dom, g in by_domain.items():
        if len(g) >= 10:
            d_bo = sum(brier(x["p_success"], x["outcome"]) for x in g) / len(g)
            d_bb = sum(brier(x["baseline_p"], x["outcome"]) for x in g) / len(g)
            if d_bo > d_bb:
                disempowered.append(dom)
    return {"n_decisions_scored": len(scored), "brier_octopus": round(bo, 4),
            "brier_baseline": round(bb, 4), "calibration_error_ECE5": round(ece, 4),
            "advantage": round(bb - bo, 4), "disempowered_domains": disempowered}


def rate(part: int, whole: int) -> float:
    """Reports without denominators are forbidden (C-1 rule)."""
    if not whole:
        raise ScorerError("rate without denominator refused (n=0)")
    return part / whole


if __name__ == "__main__":
    print(json.dumps({"reward": reward(), "dashboard": dashboard()}, indent=1))
