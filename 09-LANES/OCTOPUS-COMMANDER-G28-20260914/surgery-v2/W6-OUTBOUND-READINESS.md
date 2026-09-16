# W6 Outbound Readiness Package (2026-09-14, owner: «آماده کن»)

## Four Separated Concepts (per surgery megaprompt v2)

| concept | source | current value |
|---|---|---|
| proposal_value_aud | rate card + packet data | NULL (no valid rate card attached to specific packets) |
| dispatch_status | send receipts | CHANNEL_AUTHORIZED:17, SENT:3 (historical) |
| outcome_verified | customer response | 0 confirmed outcomes |
| verified_cash_aud | actual money received | 0.0 |

## Packet Inventory (from revenue-state.json)

| metric | value | source |
|---|---|---|
| total opportunities | 73 leads in master list | tools/leads_master.json |
| CHANNEL_AUTHORIZED | 17 packets ready | revenue-state.json counts |
| SENT (historical) | 3 emails | sent-log.jsonl |
| quote packets on disk | 55 files | quote-packets/ dir |
| verified_cash_aud | $0.00 | revenue-state.json |

## Recipient Selection (from lead-emails.jsonl + lead data)

The 17 CHANNEL_AUTHORIZED packets are B2B painting/decoration quotes for
NSW businesses. Recipients are business emails from the lead enrichment
process (the organism's own web-hunted leads, not purchased lists).

## SURG-OUTBOUND Card (initial — final details to follow per owner approval)

```
┌─────────────────────────────────────────────────────┐
│ SURG-OUTBOUND: ارسال quote به مشتری                 │
├─────────────────────────────────────────────────────┤
│ گیرنده: leadهای B2B با ایمیل تأییدشده               │
│ تعداد: [دقیق شمرده‌شده از 17 CHANNEL_AUTHORIZED]     │
│ محتوا: quote-packet (قیمت از rate card یا NULL)      │
│ کانال: ایمیل (Gmail SMTP از EnvironmentFile)         │
│ scope: فقط leadهای موجود در master-73، بدون contact جدید │
│ expiry: 48 ساعت پس از تأیید                          │
│ سقف هزینه: $0 (ایمیل موجود)                          │
│ retry: حداکثر 1 تلاش مجدد در صورت خطای transient     │
├─────────────────────────────────────────────────────┤
│ ⚠️ این کارت تأیید نهایی نیست — پس از آماده‌شدن      │
│ کامل بسته، کارت دقیق با شماره‌شده گیرنده‌ها می‌آید    │
└─────────────────────────────────────────────────────┘
```

## Pre-conditions (must be met before final card)

1. ~~TRIO deployed~~ (quota-bound, next slots 09-15 01:56/02:34Z)
2. ~~W3 ACK gate deployed~~ (behind TRIO)
3. Rate card attached or explicitly NULL (no invented prices)
4. Exact recipient list extracted and verified (no bounce-prone addresses)
5. Funnel authorization still valid (channel-authorization.json)
6. Kill-switch clear, customer_send path ready to flip for scoped send only

## What the Owner Already Approved (recorded in chain receipt 1655)

- **w6_outbound**: "PREPARE" — initial approval to build the package
- **live_test**: "YES" — fresh inert card after TRIO+W3 deploy
- **two_hash**: "REJECT_AMBIGUOUS" — implemented in W24 binder

## Next Concrete Step

After TRIO+W3 deploy (quota slots 09-15):
1. Extract exact recipient list from CHANNEL_AUTHORIZED packets
2. Verify each email against enrichment data (no bounces)
3. Attach rate card or mark proposal_value_aud as NULL per packet
4. Build final SURG-OUTBOUND card with numbered recipients
5. Ask owner for final confirmation
6. Execute through the authorized funnel path (not by the surgery agent directly)
