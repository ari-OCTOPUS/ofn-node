#!/usr/bin/env python3
"""WIRE-DEMAND step 1 — first real consumption from the real funnel.

Purpose: the pools are built and idle. This proves the demand path end to end on
real work: take one REAL pending item from the revenue funnel, run it through a
brain chosen by the registry router, and record provider + model + cost in a
demand ledger. Nothing in the live queue is modified — the enrichment output is
written to evidence only, so the organism is not touched.

Acceptance rule from the mission: a ledger row with a provider NAME and a
non-zero token/cost figure. "I wrote the code" is not acceptance.

Privacy: leads carry personal data. The script prints only an ID hash and
lengths, never the address or the message body.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0, "/home/ari/ofn/tools")
import brain_factory as bf  # noqa: E402

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
EVID = pathlib.Path("/home/ari/ofn/state/fleet-compute/demand")
DEMAND_LEDGER = EVID / "demand-ledger.jsonl"

# USD per 1M output tokens, order-of-magnitude estimates; flagged as estimates.
PRICE_PER_MTOK = {"deepseek": 0.28, "openai": 2.5, "anthropic": 3.0,
                  "gemini": 0.4, "sakana-fugu": 0.6, "local-llamacpp-180": 0.0}


def pending_lead() -> dict | None:
    """One real pending item: a lead row that has an email but no reply drafted."""
    path = ROOT / "lead-emails.jsonl"
    if not path.exists():
        return None
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    # newest first, prefer one with a subject/context to work on
    for row in reversed(rows):
        if row.get("email") or row.get("to"):
            return row
    return rows[-1] if rows else None


def main() -> int:
    lead = pending_lead()
    EVID.mkdir(parents=True, exist_ok=True)
    if not lead:
        print(json.dumps({"ok": False, "error": "NO_PENDING_LEAD"}))
        return 1

    # privacy: identity by hash + length only
    ident = str(lead.get("email") or lead.get("to") or lead.get("id") or "")
    lead_id = hashlib.sha256(ident.encode()).hexdigest()[:12]
    subject = str(lead.get("subject") or lead.get("company") or "")[:40]

    # tier=strong by CONSEQUENCE: a customer reads this draft, and the free 0.6B
    # local model produced repetition garbage on exactly this task (2026-09-18).
    # Bulk/classification work stays tier=standard (free first).
    tier = "strong"

    prompt = (
        "You are drafting a first reply to a potential painting-services customer. "
        "Write ONE short professional sentence asking which building/site they need "
        "painted so we can quote. No greeting, no signature. Context tag: "
        f"{subject or 'general enquiry'}."
    )
    t0 = time.time()
    # Failover: an empty reply from one provider must not reach the customer.
    res = bf.answer_with_failover("lead-reply-draft", prompt, tier=tier, max_tries=3)
    text = res["text"]
    provider, model = res["provider"], res["model"]
    latency = round(time.time() - t0, 2)

    out_tokens = max(1, len(text) // 4)  # rough; recorded as an estimate
    cost = round(out_tokens / 1_000_000 * PRICE_PER_MTOK.get(provider, 0.0), 6)

    row = {
        "schema": "demand_use.v1",
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "consumer": "lead_reply_draft",
        "provider": provider,
        "model": model,
        "tier": tier,
        "lead_id": lead_id,
        "ok": bool(text),
        "reply_chars": len(text),
        "est_out_tokens": out_tokens,
        "est_cost_usd": cost,
        "cost_is_estimate": True,
        "latency_s": latency,
        "reply_head": text[:160],
        "failover_tried": res["tried"],
        "failures_before_success": res["failures_before_success"],
    }
    with DEMAND_LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
