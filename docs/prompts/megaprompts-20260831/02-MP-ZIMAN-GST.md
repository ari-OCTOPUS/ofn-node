# MP-02 — Ziman GST and honest margin (owner ruling 4, half OPEN)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

Ruling 4 was answered half-way: delivery is "in person only", but GST status was
never stated. `REVENUE-STAGES.md` makes the GST/delivery facts a Z0
prerequisite, so the honest margin is not computable and Z1 stays shut. The
channel fee is separately locked at zero by ruling 3, which means margin error
now comes entirely from the tax side.

## Forbidden

Inferring GST registration from an ABN. Assuming a rate. Computing a margin
with a guessed tax treatment. Adding Instagram or Etsy — their absence is
deliberate until a percentage is recorded.

## Steps

1. Read the GST/delivery/`days_before_worry` fact fields and report their
   current stored values verbatim, plus the code path that consumes them.
2. Report every place a margin is computed and show whether it currently reads
   the GST fact or ignores it.
3. ASK Q1: is the Ziman leg GST-registered? Options must include
   `registered`, `not_registered`, `unknown_pending_accountant`.
4. ASK Q2: are listed prices GST-inclusive or GST-exclusive?
5. ASK Q3: does in-person delivery carry a fee or a distance limit, and does
   that fee enter the margin?
6. ASK Q4: with fee locked at zero, should the margin line display gross,
   net-of-GST, or both?
7. Write only the answered fields. Leave anything unanswered as `OPEN` in the
   fact file, never as a zero.

## Expected output

`docs/operations/receipts/ZIMAN-GST-<date>.yaml` with the four answers, the
fields written, and a worked margin example on one real listed piece — or an
explicit statement that no real piece has a packet yet.

## Done when

The margin formula either runs on owner-supplied tax facts or reports
`UNTESTABLE: gst_open`. Z1 is not opened by this prompt.
