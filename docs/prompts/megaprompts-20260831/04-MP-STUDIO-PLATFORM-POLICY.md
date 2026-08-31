# MP-04 — Studio paid-platform policy (owner ruling 5, prerequisite OPEN)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

Ruling 5 selected path D — paid platform — for S1. The source document
qualifies that path as "with policy", and the policy does not exist. Ruling 7
("activate all three") also depends on a Studio payment rail that is still
absent, so O9 is not genuinely open despite the ruling.

## Forbidden

Selecting a platform. Selecting a payment provider. Writing a price. Enabling a
publish path. Treating consent as implied.

## Steps

1. Read the S0/S1/S2 requirements and report which S0 items are actually
   satisfied in code, with test evidence, and which are documentation only.
2. Report the current publish chain (draft → media → consent → outbox →
   confirm → send) and mark each hop `implemented` / `partial` / `absent` with
   file references.
3. ASK Q1: which paid-platform model — subscription, per-item, commission, or
   licence?
4. ASK Q2: which payment rail, given ruling 2 established PayID plus cash for
   the painting leg? Is the Studio rail the same or separate?
5. ASK Q3: what is the refund and cancellation stance?
6. ASK Q4: subject-consent rule for paid content — per-item written, blanket,
   or no third-party subjects at all?
7. ASK Q5: maximum two platforms is a standing constraint — which two, or one?
8. Write the policy document only from answers. Every unanswered clause stays
   `OPEN` and blocks S1.

## Expected output

`docs/operations/STUDIO-PLATFORM-POLICY-<date>.md` with a clause-by-clause
ownership table: clause, owner answer verbatim, status.

## Done when

S1 is either unblocked by a complete policy or explicitly recorded as
`BLOCKED: policy_incomplete` with the missing clauses listed.
