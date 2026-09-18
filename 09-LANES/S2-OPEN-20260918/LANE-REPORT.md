# LANE-REPORT — S2-OPEN-20260918

GOV_VERSION=V8 · LADDER=L2 · lane: S2-OPEN-20260918 (season-2 opener: demand receipt + path audit)

## What was done
Executed the 48-hour plan's measurable items from S2-OPENING-PROMPT-20260918.md on live 138 data
(read-only; runtime lane files touched today by others were not modified):

1. **Demand receipt BUILT** (ORDER-LAW gate satisfied) — see
   F:\backup\06-EVIDENCE\S2-DEMAND-RECEIPT-20260918\S2-DEMAND-RECEIPT-20260918.md
2. **Path C consent reconcile DONE** (read-only): signed=false belongs to the SABA track
   (genuinely unsigned, scan uninspected — owner-only verification gate); album-unlock (self) IS
   signed in consent.sqlite. No data contradiction; two different subjects.
3. **Path B audited**: 35 products for_sale, Shopify ready since 08-23, but zero
   orders/inquiries/events → views→clicks measurement not producing numbers yet.

## Headline numbers (live, 07:25Z)
- 68 email leads + 29 phone-only identified; **0 of 68 email leads ever contacted** (set
  intersection with all send targets = 0)
- last real send 2026-09-16T06:15:59Z; last 7 days: 0 sends, 0 replies, 0 orders
- 1 real buyer reply (NSW Dept of Education, 09-02) sitting `needs_reply` for 16 days
- VERIFIED_CASH = 0

## Remains / blocked
- Item #2 (answer unanswered leads): blocked ONLY on owner Telegram taps — 3 go_b3 cards pending
  (SMARTER-COMMUNITIES, BCS-PICA: ACK_SEEN/PARK; INDEX-BATCH: ACK_BATCH/PARK). DoE reply goes
  through the same card path.
- Path B measurement (views→clicks) needs the runtime lane to expose links + count; not started.
- SABA consent verification = owner physical inspection of scan jpg (never automatable).

## Failed
- Nothing failed; no mutations on 138 (read-only probes only).

## Evidence
- 06-EVIDENCE/S2-DEMAND-RECEIPT-20260918/S2-DEMAND-RECEIPT-20260918.md (committed this lane)
- Live sources: painting.sqlite, outbox.sqlite, products.sqlite, consent.sqlite,
  state/revenue-drive/{lead-emails,phone-only-queue,sent-log}.jsonl, docs/consent/SABA-RELEASE-STATUS.json

## Rollback
- Delete the two files of this lane + `git reset HEAD~1`. No remote effects to undo.
