# Megaprompt pack — 2026-08-31

Nine ask-first megaprompts, one per open problem. Read `00-ASK-PROTOCOL.md`
before any of them; it carries the asking rules, the three-lineage rule, and the
forbidden-actions list.

| id | problem | current status |
|---|---|---|
| MP-01 | pilot thresholds | OPEN — deferred behind P0, which has now closed |
| MP-02 | Ziman GST half of the delivery ruling | OPEN — margin not computable |
| MP-03 | which send gates open conditionally | OPEN — six gates closed, none named |
| MP-04 | Studio paid-platform policy | OPEN — path chosen, policy absent |
| MP-05 | register the ruling record in the decision log | OPEN — two candidate homes |
| MP-06 | finish the score arithmetic correction | PR open, unmerged |
| MP-07 | reconcile the third lineage (vault export) | partially done, C outstanding |
| MP-08 | locate the evidence body before any verdict | BLOCKED — body not on this host |
| MP-09 | close the hermetic boundary leak | OPEN — 12 tracked writes, 57 failures untriaged |

## How to run one

1. Paste `00-ASK-PROTOCOL.md`, then the single `MP-xx` file. Never two at once.
2. The agent reports observations first, then asks question 1 and stops.
3. Answer. The agent records the answer verbatim, recomputes what is missing,
   asks question 2.
4. At the end: one receipt file, one PR to `main`, one of four verdicts.

## Order

MP-08 first: while the evidence body is on another host, no measurement verdict
from any other prompt can be trusted. Then MP-06 and MP-07 to make the canonical
record internally consistent. Then MP-01, MP-02, MP-04, MP-05 in any order.
MP-03 last among the revenue prompts, because it is the only one that touches
external-effect authority. MP-09 runs independently and does not block revenue.

## Non-negotiable

Silence is not consent. An unanswered row is `OPEN`. No agent in this pack
chooses a number, a gate, a threshold, a platform, a host or a merge.
