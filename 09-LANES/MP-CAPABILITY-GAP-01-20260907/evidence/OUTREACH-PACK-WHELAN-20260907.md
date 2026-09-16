# OUTREACH PACK — Lead #1: Whelan Property Group (READY TO CALL/SEND)

**Authority:** OWNER-GO-OWNER-ANSWERS-20260907 item 6 — «بله اجازه هست» (top-5 outreach GRANTED)
**Stamped:** `outreach_permission=approved_channel` on 5/5 rows (receipt: `board138:~/octopus-mesh/receipts/OUTREACH-TOP5-STAMP-20260907.json`)
**Qualification:** 7/7 checks PASS → QUALIFIED (receipt: `board138:~/octopus-mesh/receipts/LEAD1-QUALIFY-WHELAN-20260907.json`)

## Lead card (from live DB, verified 2026-09-05)

```text
business   : Whelan Property Group (est. 2005)
phone      : 02 9219 4111        ← primary channel (site-listed)
website    : https://www.whelanproperty.com.au/
segment    : strata / residential+commercial+industrial, NSW
score      : 0.914 (kernel b2b_account_score) — HIGH_FIT, P1, RELEVANCE 9/10
hook       : in-house maintenance desk commits to work orders within 2 hours
offices    : Ultimo + Merrylands (pitch both)
why us     : lead with speed-to-quote (their 2hr work-order culture = our fast quote turn)
```

## 30-second opener (call script)

> "Hi, this is [caller] — I'm a Sydney painting contractor. I noticed your maintenance
> desk turns work orders around in about two hours; we match that with quotes — most of
> ours go out same-day. Could I send you our two-page trade profile so you have us on
> file for the next repaint or make-good job in Ultimo or Merrylands?"

- If asked for paperwork → send trade profile + insurances (owner has these).
- If asked "how do you take payment?" → **O-5: PayPal Invoice** (Ziman gateway) —
  item 4 of owner answers 2026-09-07; deposit via invoice link, balance on completion.

## Quote skeleton (PayPal Invoice — O-5)

```text
Labor: repaint <scope> — $X (rate per owner schedule)
Paint/materials: passed-through at cost (receipts attached)
Deposit: 30% via PayPal Invoice link · balance on completion
Validity: 14 days · Site: <address> · Access: <notes>
```

## Next actions (in order)

1. **OWNER (human only):** call 02 9219 4111 with the opener above (phone = human per locks).
2. Agent: after the call, log outcome in `painting_interactions` (board138) — outcome row feeds OMLL baseline.
3. If email surfaces during the call → agent sends trade profile with dispatch receipt (L1: ≤10/day, pre-approved template only).

## Why not "sent" yet (honest blocker)

All 26 callable leads are **phone-first**; no email addresses in the DB, and phone is
human-only by the painting lane's locks. So the first REAL external contact is the
owner's call — everything machine-side is now prepared and permissioned. VERIFIED_CASH
remains 0 until a quote converts (deposit via PayPal Invoice = first rail proof, per
owner's item-1 cancellation of the self-buy).
