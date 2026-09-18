#!/usr/bin/env python3
"""DEMAND RUNNER — connect every real consumer through one pattern.

"Connect everything" done the scalable way: consumers are CONFIG, not code. Each
spec declares its tier by CONSEQUENCE (who reads the output) and pulls its work
from the real funnel. Every run appends a demand-ledger row with provider, model,
latency and cost — so "connected" always means "there is evidence of consumption".

Consumers:
  lead_reply_draft      strong  customer reads it          (lead-emails.jsonl)
  customer_reply_draft  strong  customer reads it          (tg-inbox customer rows)
  lead_classify         standard bulk, free brain first    (lead-emails.jsonl)
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
OUT = pathlib.Path("/home/ari/ofn/state/fleet-compute/demand")
LEDGER = OUT / "demand-ledger.jsonl"
PRICE = {"deepseek": 0.28, "openai": 2.5, "anthropic": 3.0, "gemini": 0.4,
         "sakana-fugu": 0.6, "local-llamacpp-180": 0.0}


def _rows(name: str) -> list[dict]:
    p = ROOT / name
    if not p.exists():
        return []
    out = []
    for line in p.read_text(errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def src_lead() -> tuple[str, str] | None:
    for row in reversed(_rows("lead-emails.jsonl")):
        ident = str(row.get("email") or row.get("to") or row.get("id") or "")
        if ident:
            return hashlib.sha256(ident.encode()).hexdigest()[:12], str(row.get("subject") or row.get("company") or "")[:40]
    return None


def src_customer() -> tuple[str, str] | None:
    """A real customer reply sitting in the spool (kind=REPLY_DETECTED)."""
    for row in reversed(_rows("tg-inbox.jsonl")):
        if str(row.get("kind")) == "REPLY_DETECTED":
            ident = str(row.get("uid") or row.get("subject") or "x")
            return hashlib.sha256(ident.encode()).hexdigest()[:12], str(row.get("subject") or "customer question")[:40]
    return None


def src_bulk() -> tuple[str, str] | None:
    """Bulk work: classify the newest lead enquiry. Free brain is fit for this."""
    for row in reversed(_rows("lead-emails.jsonl")):
        if row.get("subject"):
            ident = str(row.get("email") or row.get("id") or "y")
            return hashlib.sha256(ident.encode()).hexdigest()[:12], str(row["subject"])[:60]
    return None


CONSUMERS = [
    {"name": "lead_reply_draft", "tier": "strong", "min_chars": 40, "src": src_lead,
     "prompt": ("Draft ONE short professional sentence asking a prospective painting "
                "client which building or site they need painted so we can quote. "
                "No greeting, no signature. Context: {ctx}")},
    {"name": "customer_reply_draft", "tier": "strong", "min_chars": 40, "src": src_customer,
     "prompt": ("Draft ONE short professional reply to a customer who asked which "
                "building we service. Answer that we cover their area and will confirm "
                "the site details. No greeting, no signature. Subject: {ctx}")},
    {"name": "lead_classify", "tier": "standard", "min_chars": 3, "src": src_bulk,
     "prompt": ("Classify this painting enquiry in ONE word as either quote_request, "
                "spam or question. Enquiry subject: {ctx}")},
]


def run(spec: dict) -> dict:
    got = spec["src"]()
    if not got:
        return {"consumer": spec["name"], "skipped": "NO_SOURCE_ITEM"}
    item_id, ctx = got
    t0 = time.time()
    res = bf.answer_with_failover(f"demand-{spec['name']}", spec["prompt"].format(ctx=ctx),
                                  tier=spec["tier"], max_tries=3)
    text = res["text"].strip()
    latency = round(time.time() - t0, 2)
    provider = res["provider"] or "none"
    est_tokens = max(1, len(text) // 4)
    row = {"schema": "demand_use.v1", "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "consumer": spec["name"], "tier": spec["tier"], "item_id": item_id,
           "provider": provider, "model": res["model"], "ok": len(text) >= spec["min_chars"],
           "reply_chars": len(text), "est_out_tokens": est_tokens,
           "est_cost_usd": round(est_tokens / 1e6 * PRICE.get(provider, 0.0), 6),
           "cost_is_estimate": True, "latency_s": latency,
           "failures_before_success": res["failures_before_success"],
           "output_head": text[:150]}
    OUT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def main() -> int:
    rows = [run(s) for s in CONSUMERS]
    paid = [r for r in rows if r.get("est_cost_usd")]
    print(json.dumps({"consumers": len(rows), "ok": sum(1 for r in rows if r.get("ok")),
                      "paid_rows": len(paid),
                      "rows": [{k: r.get(k) for k in ("consumer", "provider", "model",
                                                      "ok", "reply_chars", "est_cost_usd",
                                                      "latency_s")} for r in rows]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
