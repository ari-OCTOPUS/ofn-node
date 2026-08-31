# MP-01 — Pilot thresholds (owner ruling 1, status OPEN)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

Ruling 1 was deferred behind the P0 gate. P0 closed on 2026-08-31 (a lead was
carried to "quote sent" without the owner), so the ruling is now live and
unanswered. Until the numbers exist, the weekly report has no meaningful
threshold and `PILOT-14DAY` cannot score anything. Red gate 3 forbids invented
KPIs: a threshold must come from the panel or from the pilot default, never
from the agent.

## Forbidden

Choosing any number. Writing `3/1/1` because it appears as a default. Producing
a weekly report with a placeholder threshold. Backfilling past weeks.

## Steps

1. Read `docs/operations/PILOT-14DAY.md` and
   `docs/operations/REVENUE-WEEK-CHECKLIST.md`. Report the exact threshold
   fields that exist, their current stored values, and where each is read from.
2. Report which of the three legs currently has data capable of moving each
   threshold, with counts, not adjectives.
3. ASK Q1: which threshold set governs the pilot — the documented default, a
   new owner set, or per-leg values? Offer the exact fields as options.
4. If the answer is per-leg or new: ASK one question per field, sequentially,
   never batched.
5. ASK Q(n): does the 14-day window start today or is it backdated to the P0
   closure date?
6. ASK Q(n+1): if a threshold is missed, does the pilot pause, continue with a
   recorded miss, or escalate to the owner?
7. Write the answers into the threshold fields exactly as given. Emit the
   receipt. Open one PR.

## Expected output

`docs/operations/receipts/PILOT-THRESHOLD-<date>.yaml` containing every question
asked, the verbatim answer, the field written, and the file+line changed.

## Done when

Every threshold field is either owner-answered or explicitly `OPEN`. No field
holds an agent-chosen number.
