#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BIZ-LEGS teach probe — owner order 2026-09-05: teach the organism its business legs.

Same sanctioned production path proven by IGN-3 (mem_146ce4d77967df69):
MemoryGate.submit on the real MemoryStore (F:\\backup\\_ops\\state\\memory\\memory.db),
flags armed in-process only (mirror OCTOPUS-flags.cmd:359), provenance + evidence_ref
on every row, readback + retrieval verification, JSON receipt. Stdlib only.

Every fact taught here is level-1/level-2 verified in THIS scan session:
  - painting digest + lane report (09-LANES/P-PAINTING-B2B-LEADS-20260905/)
  - board138 LEDGER.jsonl tail (read over SSH 2026-09-05)
  - _ops/budget/budget-state.json, _ops/state/owner-goal.json
  - paid-calls 90-_meta (3 days x 1 call), GOV-V8-ACK.json
Unverified items are marked UNVERIFIED inside the content itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

OPS = Path(r"F:\backup\_ops")
for p in (OPS / "memory", OPS / "outcomes"):
    sys.path.insert(0, str(p))
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"        # in-process only, IGN-3 precedent
os.environ["OCTOPUS_WIRE_MEMORY_DECISION"] = "1"

NS = "episodic"
AGENT = "doctor-agent"
TASK = "BIZ-LEGS-20260905"
LANE = Path(r"F:\backup\09-LANES\BIZ-LEGS-TEACH-20260905")
RECEIPT = LANE / "receipts" / "TEACH-BUSINESS-LEGS.json"

ROWS = [
    {
        "mkey": "bizleg-painting-leads-20260905",
        "confidence": 0.9,
        "ev": "09-LANES/P-PAINTING-B2B-LEADS-20260905/EVIDENCE-digest-20260905.md "
              "(owner_digest on live board138 DB 2026-09-05T02:35Z)",
        "content": (
            "BUSINESS LEG painting-B2B (verified 2026-09-05): 55 researched leads in "
            "board138:~/.local/share/ofn/painting.sqlite table painting_b2b_accounts, "
            "all stage=researched, outreach_permission=unknown on every row (a relevance "
            "score never grants permission to act). 26 direct+phone callable today; top "
            "9/10: Whelan Property Group 02 9219 4111, Excel Building Management (02) 9518 "
            "8577, National FM 1300 820 330, Montano Strata (02) 9053 7637, IB Property "
            "(02) 9221 3333, Strata Republic 1300 884 104, CF Strata (02) 9313 6255. 9 "
            "panel/tender path: Downer, Dexus, Delux BMG, RD Facilities, City of "
            "Parramatta, Woolworths, Sydney Water, Canterbury-Bankstown, NSW DPHI. 20 "
            "whale/intel groups (Strata Choice 10/10, Bright and Duggan, Smarter "
            "Communities, BCS/PICA, Savills, CBRE...). Agent cannot phone (human-only) "
            "and email stays closed; system action = pitch/call cards to OWNER channel."
        ),
    },
    {
        "mkey": "bizleg-shelf1-products-20260905",
        "confidence": 0.85,
        "ev": "SSH scan 2026-09-05: board138:~/.local/share/ofn/products.sqlite stat "
              "204800B mtime 2026-08-27; shelf1_readiness_probe.py absent on 138+vault+"
              "Downloads; IGN-3 memory mem_146ce4d77967df69 names REV-1 SHELF-1 next work",
        "content": (
            "BUSINESS LEG shelf1-products (scanned 2026-09-05): products DB exists on "
            "board138 (~/.local/share/ofn/products.sqlite, 204800 bytes, mtime "
            "2026-08-27) but shelf readiness is UNMEASURED - shelf1_readiness_probe.py "
            "was never delivered to any host (absent on 138, in vault, in Downloads). "
            "IGN-3 closure memory lists 'REV-1 SHELF-1 Ziman shelf completion' as next "
            "work. Next single action: write/obtain the read-only probe (sqlite mode=ro), "
            "run it ON 138 (DB is there, not on laptop), then wire business_source."
        ),
    },
    {
        "mkey": "bizleg-traffic1-owner-channel-20260905",
        "confidence": 0.9,
        "ev": "board138:~/ops-ign1/ops/LEDGER.jsonl tail read via SSH 2026-09-05; "
              "ops-ign1 receipts IGN1-CLOSEOUT-RECEIPT.json + TRAFFIC1-SEND1-RECEIPT.json",
        "content": (
            "BUSINESS LEG owner-telegram-channel (receipt level-1 2026-09-05): TRAFFIC-1 "
            "arm A LIVE - board138 ~/ops-ign1/ops/LEDGER.jsonl: kind=external_effect, "
            "arm=A, channel=telegram_channel, chat_id=-1004440663399, message_id=31, "
            "send_no=1, ts_utc=2026-09-05T08:19:19Z, utm traffic1 content A. L1 decision "
            "window ends 2026-09-07T08:19Z; outcome score due 2026-09-08; arm B queued "
            "AFTER the window. ign1_telegram_ignite.py repeat guard: never bypass; a "
            "fresh send = change the card text, HALT-probe first, EXTERNAL_ACTIONS set."
        ),
    },
    {
        "mkey": "bizleg-checkout1-payment-20260905",
        "confidence": 0.85,
        "ev": "paid-calls 90-_meta/state 2026-09-05 (1/day on 09-03/04/05); doctor/"
              "checkout1_poll.py mtime 2026-09-05; GOV-V8-ACK.json L0 VERIFIED_CASH=0",
        "content": (
            "BUSINESS LEG checkout-payment (2026-09-05): CHECKOUT-1 = AU$25 cup, awaiting "
            "OWNER purchase to prove the payment rail; checkout1_poll.py present on "
            "laptop doctor (mtime 2026-09-05) and poller heartbeat fresh today. "
            "VERIFIED_CASH=0. Paid LLM usage pattern: exactly 1 doctor call/day (sakana "
            "fugu-ultra, ~AU$0.11) on 09-03/09-04/09-05 per 90-_meta/state/paid-calls."
            "jsonl. No customer-side transport exists on laptop doctor (no smtplib in "
            "doctor/*.py); ofn-node send code state: UNVERIFIED from this host."
        ),
    },
    {
        "mkey": "bizleg-goal-attribution-20260905",
        "confidence": 0.9,
        "ev": "_ops/state/owner-goal.json (declared_by owner 2026-08-12) + 06-EVIDENCE/"
              "OCTOPUS-OWNER-BOARD-2026-08-24/GOV-V8-ACK.json",
        "content": (
            "OWNER GOAL (owner-goal.json): measurable_goal_month = first attribution."
            "claimed from zero with a REAL fresh lead; lead 667951 is SET_ASIDE by owner "
            "vote - never resurrect, never claim it. Standing directions: organism "
            "self-analyzes/improves autonomously as far as safe, persistent memory loses "
            "nothing on power cycle, parallel brains per work class, reportable spend. "
            "GOV-V8: ladder=L0, VERIFIED_CASH=0; three absolutes (secrets, receipt-chain, "
            "PASS-without-receipt) never open. End goal context: self-funding autonomy."
        ),
    },
    {
        "mkey": "bizleg-plan-20260905",
        "confidence": 0.8,
        "ev": "owner order 2026-09-05 'teach legs, plan, act' + the four leg rows above",
        "content": (
            "PLAN business-legs 2026-09-05 (owner order: teach, plan, act): P1 deliver "
            "CALL-TODAY card (top-5 callable painting leads with phones) to OWNER "
            "telegram channel via the ign1 sanctioned path, one receipted send, then "
            "owner phones - agent cannot call. P2 shelf1: read-only readiness probe on "
            "138, unblocks REV-1 shelf work. P3 TRAFFIC-1: no arm B before 09-07T08:19Z "
            "window close; outcome score 09-08. P4 CHECKOUT-1: keep polling until owner "
            "buys AU$25 cup. HARD CONSTRAINTS: no email/message to CUSTOMERS leaves the "
            "machine (AGENTS-4 + outreach_permission=unknown on all 55 rows), phone is "
            "human-only, ladder L0 until witness promotion, every external effect needs "
            "a same-domain receipt. SUCCESS METRIC (owner-goal): first attribution."
            "claimed from a fresh real lead."
        ),
    },
]


def main() -> int:
    import gate as mg
    import memory_store as ms

    store = ms.MemoryStore()
    results = []
    try:
        before = store._conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        for row in ROWS:
            cand = {
                "namespace": NS, "mkey": row["mkey"], "content": row["content"],
                "source": "deterministic", "producer": "biz_legs_teach",
                "privacy": "scrubbed", "classification": "internal",
                "agent_id": AGENT, "task_id": TASK,
                "confidence": row["confidence"],
                "confidence_source": "receipt-chain",
                "confidence_method": "direct-observation",
                "evidence_ref": row["ev"],
            }
            res = mg.MemoryGate(store).submit(cand)
            mid = res.get("memory_id")
            readback = store.get(NS, row["mkey"]) if mid else None
            results.append({
                "mkey": row["mkey"],
                "verb": res.get("verb"), "reason": res.get("reason"),
                "memory_id": mid, "trust": res.get("trust"),
                "readback_ok": bool(readback and readback.get("content") == row["content"]),
            })
        after = store._conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        hits = store.search("business legs revenue plan", namespace=NS, k=8)
    finally:
        try:
            store.close()
        except Exception:  # noqa: BLE001
            pass

    out = {
        "schema": "biz-legs-teach.v1",
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": "laptop",
        "rows": results,
        "rows_before": before,
        "rows_after": after,
        "committed": sum(1 for r in results if r["verb"] == "commit"),
        "readback_all_ok": all(r["readback_ok"] for r in results),
        "search_hit_mkeys": [
            h.get("mkey") for h in hits
            if str(h.get("mkey", "")).startswith("bizleg-")
        ],
    }
    body = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(body.decode("utf-8"), encoding="utf-8")
    print(body.decode("utf-8"))
    print("receipt_sha256:", hashlib.sha256(body).hexdigest())
    ok = (out["committed"] == len(ROWS) and out["readback_all_ok"]
          and len(out["search_hit_mkeys"]) >= 3)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
