# S2-DEMAND-RECEIPT-20260918 — first demand receipt of season 2 (ORDER-LAW gate)

- stamp: 2026-09-18T07:25Z (17:25 AEST)
- actor: ZCode session (lane S2-OPEN-20260918) · GOV_VERSION=V8 · LADDER=L2
- method: live read-only probes on 138 (sqlite + jsonl ledgers), vault grep for path-C surfaces
- season goal (S2-OPENING-PROMPT-20260918.md): VERIFIED_CASH > 0 with a V4 witness

## A. Demand receipt — raw numbers (sources in brackets)

| metric | value | source |
|---|---|---|
| email leads identified | **68** | state/revenue-drive/lead-emails.jsonl |
| phone-only leads (no email) | **29** | state/revenue-drive/phone-only-queue.jsonl |
| separate NSW OCP buyer track | 6 emails, 5 contacted 2026-09-01 | painting.sqlite + outbox.sqlite |
| **email leads CONTACTED (set ∩ sent targets)** | **0 of 68** | lead-emails.jsonl ∩ (sent-log.jsonl ∪ outbox payloads), computed live |
| distinct customer send targets ever | ≈6 | sent-log (43 rows / 22 packets) + outbox |
| last real outbound send | **2026-09-16T06:15:59Z** (reply_1) | sent-log.jsonl last live row |
| sends in last 7 days | **0** (4 rows dated 09-18 are `backfilled_by: ledger-fix`, not sends) | sent-log.jsonl |
| inbound customer replies ever | 2: Transport auto-reply 09-01 (archived); **DoE `needs_reply` since 09-02 — unanswered 16 days** | painting_interactions |
| replies in last 7 days | **0** | painting_interactions |
| orders / inquiries / payments / sale_events | **0 / 0 / 0 / 0** | products.sqlite |
| VERIFIED_CASH | **0** | consistent with honest ledger |

## B. Path B — ziman shop (shortest cycle)

- products.sqlite: 40 products = **35 for_sale** + 3 gifted + 2 in_progress.
- Shopify readiness sealed 2026-08-23 (SHOPIFY-READY.json exists; contents include banking details —
  NOT copied here, key-name-only per AGENTS.md §7).
- shopify-watch timer ACTIVE (30-min) but **zero order/inquiry events recorded** →
  views→clicks→order measurement is NOT yet producing numbers. Gap for the runtime lane.

## C. Path C — studio consent reconcile (read-only, DONE)

- `docs/consent/SABA-RELEASE-STATUS.json` sha `f8bed322…` (matches SURGEON-BRIEF citation, unchanged):
  subject **saba**, document saba-release-20260902, **signed=false**, record_release_called=false,
  owner-reported scan jpg (sha c5046a18…) staged but four_corners/signature/date ALL unverified.
- consent.sqlite live: subject `self` has TWO SIGNED releases (telegram_channel 08-22,
  album-unlock 09-16, signed_at populated).
- **Reconcile verdict: NO data contradiction.** The "signed=false vs HQ attests" clash is two
  DIFFERENT subjects: album-unlock (self) IS signed and attested; the SABA track is genuinely
  unsigned and uninspected. Path C remains gated on the owner physically verifying the SABA scan —
  an owner-only act (the file's own note forbids passing uninspected hashes to record_release).

## D. What blocks item #2 (answer every unanswered lead) — the ONLY gate

- customer_send=false + go_b3 customer_contact cards: **3 pending on Telegram right now**
  (SMARTER-COMMUNITIES, BCS-PICA → ACK_SEEN/PARK; INDEX-BATCH → ACK_BATCH/PARK) — live-confirmed
  pending on 138 at 06:43Z.
- The DoE reply (needs_reply, 16 days) is also an outbound customer send → same card path.
- Runtime legs for drafts (demand_runner / followup_runner / call_runner) were being modified on
  138 TODAY 07:02–07:08Z by the runtime lane — left untouched by this lane (lane discipline).

## E. Honest season-open verdict

Capability is not the constraint (store buyable, brains wired, approval loop live — S2 doc §"why now").
The constraint is exactly what the receipt shows: **68+29 leads, 0 contacted, 0 replies in 7 days,
0 orders.** One owner tap on the three cards unblocks the first outbound cycle; after that the
number that matters is replies (V1), not sends (V0).
