# MP-06 — Finish the accounting correction (PR open, unmerged)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

The score table carried Recovery = 38 while the formula under it multiplied
10 x 34, and the announced figure was a third value. Owner rulings fixed this:
valid Recovery = 34, official announced figure stays 45.70, the exact
34-weighted raw is 45.75, delta -0.05 is recorded, all three files stay
consistent, the local wave-1 total is not exported, and the three split scores
stay numerically unchanged but marked stale. The correction PR exists and is
not merged, so `main` still shows the contradictory table.

## Forbidden

Writing 49.15 anywhere. Recomputing the split scores. Changing the announced
figure. Merging without an explicit merge answer. Promoting a raw figure to
official.

## Steps

1. Re-verify the arithmetic independently: recompute the weighted sum with
   Recovery = 34 and with Recovery = 38, confirm the weights total 100, and
   report all three candidate figures beside the announced one.
2. Search all three score-bearing files plus the gates file for any remaining
   occurrence of the old Recovery value or of an unofficial total. Report
   file+line for each hit.
3. Report whether the manifest and the risk register carry any figure that must
   move in step, and whether moving them is inside this correction's scope.
4. ASK Q1: merge the correction PR now, or hold it behind another review?
5. ASK Q2: the split scores are marked stale — does a re-score task get created
   now, or does it wait for the gate list?
6. ASK Q3: does the `-0.05` rounding delta get a standing rule ("announced
   figures are rounded down to two decimals") or stay a one-off note?
7. ASK Q4: the local wave-1 export was deferred to a separate PR — is that PR
   in scope for the next session or parked?

## Expected output

An updated correction receipt with the independent recomputation, the full hit
list, and the four answers. No new total written without an answer.

## Done when

`main` shows one internally consistent arithmetic, and every other figure is
labelled raw, stale, or local-only.
