#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI for the shadow economic learning loop.

    python -m ofn.learning.cli run \
        --evidence evidence.json --claims claims.json \
        --ledger runs/economic-learning-ledger.jsonl --out runs/

`run` executes the full loop on a receipt snapshot and writes machine
outputs (scores.json, lessons.json, proposals.json) plus ledger rows.
`render-obsidian` rebuilds the three Obsidian files FROM the ledger +
run outputs (never from agent prose).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import datetime as _dt
from pathlib import Path

from . import (ActionChainLinker, EconomicLearningLedger, ExperimentProposer,
               LessonExtractor, OutcomeScorer, ReceiptVerifier)

STALE_AFTER_H = 24


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _code_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                   # noqa: BLE001
        return "UNKNOWN"


def cmd_run(args) -> int:
    ev_path = Path(args.evidence)
    evidence = json.loads(ev_path.read_text(encoding="utf-8"))
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8")) \
        if args.claims else []
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    verifier = ReceiptVerifier(evidence.get("receipt_lookup") or (lambda _pid: None))
    ledger = EconomicLearningLedger(args.ledger)

    snapshot_sha = evidence.get("snapshot_sha256", "UNKNOWN")
    chains, scores, lessons, proposals = [], [], [], []
    verified_payments = 0
    unverified_claims = 0

    for lead in evidence.get("leads", []):
        lead_id = lead["lead_id"]
        chain = ActionChainLinker().build(
            evidence.get("campaign_id", "UNKNOWN"), lead_id,
            lead.get("events", []))
        claim = next((c for c in claims if c.get("lead_id") == lead_id), None)
        payment = None
        if claim:
            payment = verifier.verify(claim, linked_to_lead=True)
            if payment.verification_status == "VERIFIED":
                verified_payments += 1
            else:
                unverified_claims += 1
            ledger.append({"record_id": f"PAY-{payment.payment_id or 'no-id'}",
                           "kind": "payment_claim", "lead_id": lead_id,
                           "verification_status": payment.verification_status,
                           "snapshot_sha256": snapshot_sha, "outcome": "RECORDED"})
        score = OutcomeScorer().score(chain, payment)
        chains.append({"lead_id": lead_id, "complete": chain.complete,
                       "unknown": chain.unknown_links()})
        scores.append(score.as_dict())
        ledger.append({"record_id": f"SCORE-{score.campaign_id}-{lead_id}",
                       "kind": "outcome_score", "lead_id": lead_id,
                       "level": score.level, "snapshot_sha256": snapshot_sha,
                       "outcome": "RECORDED"})
        for lesson in LessonExtractor().extract(score, lead.get("events", [])):
            ldict = lesson.as_dict()
            lessons.append(ldict)
            ledger.append({"record_id": ldict["lesson_id"], "kind": "lesson",
                           "lead_id": lead_id, "lesson": ldict["lesson"],
                           "confidence": ldict["confidence"],
                           "sample_size": ldict["sample_size"],
                           "snapshot_sha256": snapshot_sha, "outcome": "RECORDED"})
            prop = ExperimentProposer().propose_from_lesson(lesson)
            if prop.title:
                proposals.append({"proposal_id": prop.proposal_id, "title": prop.title,
                                  "target": prop.target, "outcome": prop.outcome,
                                  "reason": prop.reason})
                ledger.append({"record_id": prop.proposal_id, "kind": "proposal",
                               "lead_id": lead_id, "title": prop.title,
                               "outcome": prop.outcome, "reason": prop.reason,
                               "snapshot_sha256": snapshot_sha})

    payload = {
        "generated_at": _now_iso(), "code_sha": _code_sha(),
        "snapshot_sha256": snapshot_sha,
        "campaign_id": evidence.get("campaign_id", "UNKNOWN"),
        "verified_payments": verified_payments,
        "unverified_payment_claims": unverified_claims,
        "payment_received_verified": verified_payments > 0,
        "chains_total": len(chains),
        "chains_complete": sum(1 for c in chains if c["complete"]),
        "scores": scores, "lessons": lessons, "proposals": proposals,
    }
    (out / "run-summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = ledger.counts()
    print(json.dumps({**payload, "ledger": counts,
                      "ledger_valid": ledger.verify()["valid"],
                      "orphans": ledger.orphans()}, ensure_ascii=False, indent=2,
                     default=str))
    return 0 if ledger.orphans() == 0 and ledger.verify()["valid"] else 1


def _stale(generated_at: str) -> str:
    try:
        gen = _dt.datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        age_h = (_dt.datetime.now(_dt.timezone.utc) - gen).total_seconds() / 3600
        return "" if age_h <= STALE_AFTER_H else "STALE"
    except ValueError:
        return "STALE"


def cmd_render_obsidian(args) -> int:
    run_dir = Path(args.run_dir)
    run = json.loads((run_dir / "run-summary.json").read_text(encoding="utf-8"))
    ledger = EconomicLearningLedger(Path(run_dir) / "economic-learning-ledger.jsonl")
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)
    stale = _stale(run["generated_at"])
    unkn = "UNKNOWN" if run.get("snapshot_sha256", "UNKNOWN") == "UNKNOWN" else ""

    lines = [
        "---",
        "type: economic-learning-current",
        f"generated_at: {run['generated_at']}",
        f"code_sha: {run['code_sha']}",
        f"board_runtime_snapshot_sha256: {run['snapshot_sha256']}",
        f"campaign: {run['campaign_id']}",
        "mode: shadow-only",
        "---",
        "",
        "# ECONOMIC-LEARNING-CURRENT (generated from receipts, not agent prose)",
        "",
        f"state: {stale or 'FRESH'}{(' · ' + unkn) if unkn else ''}",
        "",
        "## Verified payments",
        f"- verified: **{run['verified_payments']}**",
        f"- unverified claims: **{run['unverified_payment_claims']}**",
        f"- payment_received_verified = **{str(run['payment_received_verified']).lower()}**",
        "",
        "## Action chains",
        f"- total: {run['chains_total']} · complete: {run['chains_complete']}",
        "",
        "## Active hypotheses / experiments",
    ]
    for p in run["proposals"]:
        lines.append(f"- [{p['outcome']}] {p['title']} — {p['reason']}")
    lines += ["", "## Lessons"]
    for l in run["lessons"]:
        lines.append(f"- {l['lesson_id']} ({l['confidence']}, n={l['sample_size']}, "
                     f"recheck {l['recheck_at']}): {l['lesson']}")
    lines += ["", f"ledger: {ledger.counts()} · valid={ledger.verify()['valid']} "
                  f"· orphans={ledger.orphans()}"]
    (dst / "ECONOMIC-LEARNING-CURRENT.md").write_text("\n".join(lines), encoding="utf-8")

    ledger_text = (run_dir / "economic-learning-ledger.jsonl").read_text(encoding="utf-8")
    (dst / "ECONOMIC-LEARNING-LEDGER.jsonl").write_text(ledger_text, encoding="utf-8")

    q = ["---", "type: economic-learning-queue", f"generated_at: {run['generated_at']}",
         "---", "", "# ECONOMIC-LEARNING-QUEUE", "",
         "| id | title | outcome | reason |", "|---|---|---|---|"]
    for p in run["proposals"]:
        q.append(f"| {p['proposal_id']} | {p['title']} | {p['outcome']} | {p['reason']} |")
    q.append("")
    (dst / "ECONOMIC-LEARNING-QUEUE.md").write_text("\n".join(q), encoding="utf-8")

    import hashlib
    for name in ("ECONOMIC-LEARNING-CURRENT.md", "ECONOMIC-LEARNING-LEDGER.jsonl",
                 "ECONOMIC-LEARNING-QUEUE.md"):
        digest = hashlib.sha256((dst / name).read_bytes()).hexdigest()
        print(f"{name}: sha256={digest}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ofn.learning")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--evidence", required=True)
    p_run.add_argument("--claims")
    p_run.add_argument("--ledger", required=True)
    p_run.add_argument("--out", required=True)
    p_run.set_defaults(func=cmd_run)
    p_obs = sub.add_parser("render-obsidian")
    p_obs.add_argument("--run-dir", required=True)
    p_obs.add_argument("--dst", required=True)
    p_obs.set_defaults(func=cmd_render_obsidian)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
