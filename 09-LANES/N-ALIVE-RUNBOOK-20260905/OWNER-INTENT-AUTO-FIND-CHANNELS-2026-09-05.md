---
type: owner-intent
status: recorded
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# Owner intent — Octopus finds channels itself

Owner this session: «داستان اینه اختاپوس باید خودش اتوماتیک کانال هارو پیدا کنه»

Earlier same day (other lane, not overwritten): «همه چیو از قبل داخل برد 138 ساختم خودت کانالاشو انتخاب کن»  
Source: `09-LANES/U-WHY-NOT-LIVE-20260905/LAYER4-CHANNEL-SELECTION.json` `owner_delegation`.

Two readings, both kept:

| Reading | Meaning | Already on disk? |
|---|---|---|
| A — find among built surfaces | Health-probe 138 loopback + already-receipted Telegram | Yes: LAYER4 selected 8791–8794+8796; TRAFFIC-1 channel `-1004440663399`; IGN-1 owner chat |
| B — invent new external audiences | Scrape/join groups, OF, ads, cold leads | No consumer, no receipt. Parked until L1 clock + consent. Not started here. |

This session adopts **A as the automatic rule** and leaves **B status: open, not authorized**.

## Automatic rule (no owner pick)

1. List surfaces that already have a same-domain receipt or a live `/healthz` on 138.
2. Drop any surface with no consumer (triage rule).
3. Rank: VERIFIED_CASH path first (Ziman / REV-1), then Telegram channel with `dispatch_receipt.v1`, then owner chat, then other mesh legs.
4. Do not ask which of those to use.
5. Finding ≠ sending. Send still needs D2=B clock or a filled GO-TOKEN on 138.

## Rank from files already cited (not a new probe)

| Rank | Surface | Why it counts | Source |
|---|---|---|---|
| 1 | Ziman storefront + 138 `:8791` | REV-1 cash path; owner parked accountant | GOV-V8 §۵ · LAYER4 |
| 2 | Telegram public channel | TRAFFIC-1 `dispatch_receipt.v1` · paper HOLD lift | `TRAFFIC1-SEND1-RECEIPT.json` · `PAPER-LIFT-HOLD-TELEGRAM-2026-09-05.md` |
| 3 | Telegram owner chat | IGN-1 `1676` | `IGN1-CLOSEOUT-RECEIPT.json` |
| 4 | 138 `:8792–8794`, `:8796` | LAYER4 healthz 200 | `LAYER4-CHANNEL-SELECTION.json` |

Paid ads / live OF / new groups: not in this list. No receipt that they are a live consumer.

## Forbidden from this intent

New broker, new bot, UI سوم, LangGraph, flag enable, send, lead expansion without consent.
