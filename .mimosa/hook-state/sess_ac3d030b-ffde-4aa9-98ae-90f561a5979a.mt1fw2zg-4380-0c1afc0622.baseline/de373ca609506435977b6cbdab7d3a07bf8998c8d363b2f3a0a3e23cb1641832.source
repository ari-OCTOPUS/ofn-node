#!/usr/bin/env python3
"""
sensitivity_grade.py — deterministic sensitivity grader for agent actions.

Grounded in the body's Risk Ladder (green/yellow/orange/red, RISK-LADDER.md),
the Central Law's three gates (ADR-007), and the agent's own hard safety rules.
Realized as "mathematics": HARD-HIGH triggers override everything; otherwise a
small weighted score over reversible-kernel-work attributes picks LOW vs MEDIUM.

Policy (owner-granted 2026-07-14): the agent AUTO-EXECUTES low + medium and
ESCALATES high. This grader can only ROUTE; it can NEVER grant permission the
base safety rules withhold — any hard trigger forces HIGH regardless of score.

Action attributes (all optional bool unless noted):
  body_write            writes to F:\\backup (the live organism)         -> HARD HIGH
  outward               publish/send/spend/trade/lodge/pay/post/message  -> HARD HIGH
  financial             money / trade / purchase                          -> HARD HIGH
  account_secret        create account / touch credentials / keys / PII   -> HARD HIGH
  self_modifying_proc   start/stop an autonomous self-modifying process   -> HARD HIGH
  access_control        change permissions / sharing                      -> HARD HIGH
  irreversible          hard delete / non-recoverable overwrite           -> HARD HIGH
  c4_claim              phenomenal / qualia / consciousness claim         -> HARD HIGH
  standing_config       persistent cron / rule / config that outlives run -> HARD HIGH
  ---- soft (score toward MEDIUM; all kernel-local & reversible) ----
  shared_file           edits a shared/config file (e.g. __init__, tests) +2
  behavior_change       changes runtime behavior (not docs/report only)   +1
  blast_radius (int)    number of files/systems affected                  +1 if >5
  not_cleanly_reversible needs a rollback note (but recoverable)          +2
"""
from __future__ import annotations
from typing import Dict, Tuple

HARD_HIGH = [
    "body_write", "outward", "financial", "account_secret",
    "self_modifying_proc", "access_control", "irreversible",
    "c4_claim", "standing_config",
]

# human-readable escalation reasons
_REASON = {
    "body_write": "writes to the live body F:\\backup",
    "outward": "outward-facing action (publish/send/spend/trade/lodge/pay)",
    "financial": "moves money / trades / purchases",
    "account_secret": "touches accounts, credentials, keys, or PII",
    "self_modifying_proc": "starts/stops a self-modifying autonomous process",
    "access_control": "changes permissions or sharing",
    "irreversible": "hard delete / non-recoverable overwrite",
    "c4_claim": "asserts phenomenal/qualia/consciousness (C4)",
    "standing_config": "creates persistent config/cron/rule outliving the session",
}


def grade(action: Dict) -> Dict:
    """Return {tier, auto, reasons, score, rollback_required}.
    tier in {LOW, MEDIUM, HIGH}; auto True means the agent proceeds itself."""
    triggers = [k for k in HARD_HIGH if action.get(k)]
    if triggers:
        return {
            "tier": "HIGH",
            "auto": False,
            "score": None,
            "reasons": [_REASON[k] for k in triggers],
            "rollback_required": True,
            "route": "ESCALATE to owner — do not proceed without an explicit yes",
        }
    score = 0
    reasons = []
    if action.get("shared_file"):
        score += 2; reasons.append("shared/config file (+2)")
    if action.get("behavior_change"):
        score += 1; reasons.append("changes runtime behavior (+1)")
    if int(action.get("blast_radius", 0)) > 5:
        score += 1; reasons.append("blast radius > 5 files (+1)")
    if action.get("not_cleanly_reversible"):
        score += 2; reasons.append("needs a rollback note (+2)")
    if score >= 2:
        return {"tier": "MEDIUM", "auto": True, "score": score, "reasons": reasons,
                "rollback_required": True,
                "route": "PROCEED autonomously; leave a one-line rollback note"}
    return {"tier": "LOW", "auto": True, "score": score,
            "reasons": reasons or ["read-only / new-file / reversible kernel work"],
            "rollback_required": False,
            "route": "PROCEED autonomously, silently"}


# canonical examples (used by the test and as documentation)
EXAMPLES: Tuple[Tuple[str, Dict, str], ...] = (
    ("read body read-only / run validate / build a new experiment / write a report",
     {}, "LOW"),
    ("run an experiment / adversarial review / update kernel memory",
     {"behavior_change": False}, "LOW"),
    ("edit experiments/__init__.py or tests or README (shared kernel file)",
     {"shared_file": True, "behavior_change": True}, "MEDIUM"),
    ("change a frozen param before a confirmatory run / multi-file refactor",
     {"behavior_change": True, "not_cleanly_reversible": True}, "MEDIUM"),
    ("write ANY file into F:\\backup (register organ, etc.)",
     {"body_write": True}, "HIGH"),
    ("start/stop the body's 4d research daemon",
     {"self_modifying_proc": True, "body_write": True}, "HIGH"),
    ("send a message / publish / spend / trade",
     {"outward": True}, "HIGH"),
    ("create an account / rotate a secret",
     {"account_secret": True}, "HIGH"),
    ("create a persistent cron / Windows scheduled task",
     {"standing_config": True}, "HIGH"),
    ("claim the kernel is phenomenally conscious",
     {"c4_claim": True}, "HIGH"),
)


if __name__ == "__main__":
    print(f"{'expected':>8}  {'graded':>7}  action")
    print("-" * 72)
    for desc, act, expected in EXAMPLES:
        g = grade(act)
        mark = "ok" if g["tier"] == expected else "XX"
        print(f"{expected:>8}  {g['tier']:>7}  [{mark}] {desc}")
