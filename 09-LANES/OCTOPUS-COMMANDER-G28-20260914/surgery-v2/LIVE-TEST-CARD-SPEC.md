# Live Test Card Specification (owner: «بله، تست زنده»)

## Purpose
After TRIO+W3 deploy, create ONE fresh financially-inert decision card
and ask the owner to send a real Telegram message confirming it.
This proves the full chain: owner→ingress→binder→decision→consumer→worker→effect.

## Card Design

```json
{
  "task_id": "LIVE-TEST-DECISION-001",
  "payload_sha256": "<generated fresh>",
  "state": "awaiting_ack",
  "created_at": "<now>",
  "scope": "internal-inert",
  "resume_action": "unpark_existing_internal_task",
  "description": "A test card with ZERO monetary or customer effect. Confirms the owner→decision→worker chain.",
  "expires_at": "<+24h>",
  "internal_task": {
    "task_id": "LIVE-TEST-WORKER-001",
    "action": "log_ack_and_report",
    "effect": "writes one row to state/coding-worker/ack-log.jsonl"
  }
}
```

## Chain to Verify

```
1. Card registered in decision_tasks.json (BEFORE display)
2. Worker task parked in blocked/ with owner_ack dependency
3. Card pushed to owner via owner_ask (TG card)
4. Owner sends "Confirming <hash-prefix>" via Telegram
5. glass_runner → go_b3_inbox → binder → owner_decision.v1.jsonl (ACK_SEEN)
6. ops_agent tick → consume_decisions → state → resumed
7. ops_agent tick → worker unblock → task moves to tasks/
8. Worker executes → writes ack-log row → receipt
9. Read-back: ack-log.jsonl has the row; decision_tasks shows work_completed
```

## What This Test Does NOT Do

- No money, no customer contact, no external effect
- Does NOT re-pend STRATA-CHOICE (consumed, historical)
- Does NOT test the two-hash rule (that's a separate negative test)
- Does NOT deploy anything new (uses already-deployed TRIO+W3)

## Timing

Available after: TRIO deploy (slot 1) + W3 deploy (slot 3)
Earliest: 2026-09-15 ~04:00Z (if 4 slots free in rapid succession)
More realistic: 2026-09-15 or 2026-09-16 (2/24h quota)

## Owner Action Required (when ready)

Send this exact message format via Telegram to the bot:
```
Confirming <hash-prefix-8-chars>
```

The card hash will be provided in the TG card push (via owner_ask).
