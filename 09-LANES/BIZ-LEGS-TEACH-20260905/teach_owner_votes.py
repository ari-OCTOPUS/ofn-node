#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""teach_owner_votes.py — record the 2026-09-05 owner Q&A votes as graded memory.

Same sanctioned MemoryGate path (IGN-3 / biz-legs teach precedent). Owner votes:
  1. CALL-TODAY card  -> send approved (blocked by DPI; armed)
  2. CHECKOUT-1       -> owner buys AU$25 cup (rail proof; VERIFIED_CASH needs SALE-1)
  3. MEMORY_GATE      -> permanent for daemon (run_doctor_day.py setdefault)
  4. L1 leg           -> painting B2B (card+call), 10/day, pre-approved template v1
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
os.environ.setdefault("OCTOPUS_WIRE_MEMORY_GATE", "1")
os.environ.setdefault("OCTOPUS_WIRE_MEMORY_DECISION", "1")

NS = "episodic"
LANE = Path(r"F:\backup\09-LANES\BIZ-LEGS-TEACH-20260905")
RECEIPT = LANE / "receipts" / "TEACH-OWNER-VOTES.json"

ROWS = [
    {
        "mkey": "bizvote-calltoday-card-20260905",
        "ev": "structured Q&A 2026-09-05 vote «بفرست»; blocker receipt "
              "board138:~/ops-ign1/ops/receipts/CALLTODAY-NETWORK-BLOCK-20260905.json",
        "content": (
            "OWNER VOTE 2026-09-05: CALL-TODAY card 1 (top-5 painting leads with "
            "phones) approved for owner telegram channel. 4 send attempts 10:16-10:31Z "
            "all aborted - upstream DPI RSTs api.telegram.org bot-path TLS from 138 "
            "(GET ok, POST bot*/ RST even invalid token); no partial send (getUpdates "
            "checked x3, found=false). calltoday_send.py + check_calltoday.py armed on "
            "138 with full guards; card lands in the next open window. L1 counter 4/10."
        ),
    },
    {
        "mkey": "bizvote-checkout1-l2-20260905",
        "ev": "structured Q&A 2026-09-05 vote «می‌خرم - L2 را باز کن»; "
              "checkout1_poll.py NO_ORDERS at 10:33Z (purchase pending)",
        "content": (
            "OWNER VOTE 2026-09-05: owner will personally buy the AU$25 Ziman cup "
            "(CHECKOUT-1) to prove the payment rail end-to-end. Honesty per GOV-V8 "
            "REV-1: the receipt is kind=REPORTED_NOT_VERIFIED buyer=owner — it proves "
            "the RAIL (order+txn+payout receipts), while the L2 ladder condition "
            "VERIFIED_CASH>=1 is defined as SALE-1 first STRANGER order. L2 opens at "
            "SALE-1 unless the owner explicitly amends the metric. refund_rate=0 and "
            "restore-drill 6/6 already green. checkout1_poll.py armed (idempotent)."
        ),
    },
    {
        "mkey": "bizvote-memory-gate-permanent-20260905",
        "ev": "structured Q&A 2026-09-05 vote «دائمی روشن شود»; patch: "
              "_ops/run_doctor_day.py setdefault (syntax-checked), effective next "
              "OCTOPUS-doctor-day run 07:00 AUSEST",
        "content": (
            "OWNER VOTE 2026-09-05: OCTOPUS_WIRE_MEMORY_GATE + MEMORY_DECISION are "
            "now permanently armed for the doctor daemon via run_doctor_day.py "
            "(setdefault; explicit external value still wins). Root cause found: "
            "flags.cmd line 359 already had =1 but the schtask launcher bypassed it, "
            "so daemon self-loop wrote skip/flag-off (e.g. 08:38:54Z). Same-day "
            "incident: a sparse re-apply dematerialized 43 tracked files under "
            "_ops/memory+_ops/outcomes+run_doctor_day.py; restored surgically from "
            "HEAD via git show (imports verified). The dangerous sparse pattern "
            "/* + !/*/ remains set — a full re-apply would collapse ALL dirs; do NOT "
            "run sparse-checkout reapply on this vault."
        ),
    },
    {
        "mkey": "bizvote-l1-leg-painting-20260905",
        "ev": "structured Q&A 2026-09-05 vote «painting B2B — کارت+تماس»",
        "content": (
            "OWNER VOTE 2026-09-05: designated L1 external-contact leg = painting B2B "
            "(card + owner phone call). Cap 10 external actions/day (4 used at vote "
            "time). First pre-approved template: CALL-TODAY card v1 (5 leads + phones, "
            "sha256 recorded in CALLTODAY receipts). Templates beyond v1 need owner "
            "sign-off before use. Drills 3/3 green same day: kill-switch "
            "(IGN1_ABORT KILL_SWITCH_PRESENT), idempotency (ALREADY_DONE x2), restore "
            "(RESTORE-DRILL-138-20260905.json 6/6)."
        ),
    },
    {
        "mkey": "bizleg-ladder-status-20260905",
        "ev": "GOV-V8 ruling ladder table + same-day drill receipts",
        "content": (
            "LADDER STATUS 2026-09-05 evening: L1 OPEN (owner variance; external "
            "counter 4/10; pre-approved template v1; leg=painting B2B). L2 conditions: "
            "refund_rate=0 OK, restore-drill OK, VERIFIED_CASH>=1 PENDING (rail proof "
            "in flight via owner cup purchase; SALE-1 stranger order is the ruling's "
            "VERIFIED_CASH definition). L3 needs net_margin_30d>0 + runway>=30d + 3 "
            "VERIFIED_CASH rows. L4 needs >=10 rows + 30 clean days + witness 182. "
            "Permanent locks (never open): secret_rotation, data deletion, "
            "silence=consent. Automated decay: complaint/block or 2 consecutive send "
            "errors -> drop L1 to L0."
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
                "agent_id": "doctor-agent", "task_id": "BIZ-LEGS-20260905",
                "confidence": 0.9, "confidence_source": "receipt-chain",
                "confidence_method": "direct-observation",
                "evidence_ref": row["ev"],
            }
            res = mg.MemoryGate(store).submit(cand)
            mid = res.get("memory_id")
            readback = store.get(NS, row["mkey"]) if mid else None
            results.append({
                "mkey": row["mkey"], "verb": res.get("verb"),
                "memory_id": mid,
                "readback_ok": bool(readback and readback["content"] == row["content"]),
            })
        after = store._conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        hits = store.search("owner votes ladder authority", namespace=NS, k=6)
    finally:
        try:
            store.close()
        except Exception:  # noqa: BLE001
            pass

    out = {
        "schema": "biz-votes-teach.v1",
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rows": results, "rows_before": before, "rows_after": after,
        "committed": sum(1 for r in results if r["verb"] == "commit"),
        "route_hit_mkeys": [h.get("mkey") for h in hits
                            if str(h.get("mkey", "")).startswith("bizvote-")
                            or str(h.get("mkey", "")).startswith("bizleg-")],
    }
    body = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
    RECEIPT.write_text(body.decode("utf-8"), encoding="utf-8")
    print(body.decode("utf-8"))
    print("receipt_sha256:", hashlib.sha256(body).hexdigest())
    return 0 if (out["committed"] == len(ROWS) and
                 all(r["readback_ok"] for r in results)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
