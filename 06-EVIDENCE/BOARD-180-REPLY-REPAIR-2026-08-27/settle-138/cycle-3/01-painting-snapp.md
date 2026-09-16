# Cycle-3 Painting (folded from late Cycle-2 correction)
run_id: revenue-cycle-3-20260827
source: 180 Cycle-2 painting CORRECTED (SHA 3cbcaf3b) after Cycle-2 CLOSE
Cycle-2 SoT remains 04-VERIFY sha256=8b40677f (do not reopen)
HOLD_EXTERNAL=yes may_authorize=false NO send

# Cycle-2 Painting pack (CORRECTION)
run_id: revenue-cycle-2-20260827
deadline_utc: 2026-08-27T06:00:00Z
baseline: Cycle-1 CLOSED. Cycle-1 painting pick (OFN pilots) is INVALID for Cycle-2. Do not reuse.
kill: HOLD_EXTERNAL; no customer send; no mesh-claim; no systemctl start/enable; B2 do not reopen
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

task_id: C2-PAINT-SNAPP
idempotency_key: cycle2:painting:snapp-fitness-0100A-0101B
lane: A
claim_level: OBSERVED from cited PDFs + Lead-نقاشی.md
bottleneck: Snapp quotes exist and are unsigned; no suburb/phone/email on the quotes so follow-up channel UNKNOWN

## Correction

Cycle-1 pick lead:pilot-pilot-2-... and the other 7 OFN CRM rows are pilots/test (مشتری آزمایشی یک/دو + empty manuals). Not real people. Cycle-1 pack stays closed. This pack does not reuse them.

## BEST — Snapp Fitness (current-year quote)

Embedded claims (empty would be INVALID):
- F:\\backup\\03 - Projects\\Lead-نقاشی\\Estimate 0100-A.pdf
- F:\\backup\\03 - Projects\\Lead-نقاشی\\Estimate 0101-B.pdf

From PDFs (OBSERVED):
- Client address line: Snapp Fitness
- Issuer: MASTER PAINTING AND DESIGN, 9 Cycas Place, STANHOPE GARDENS NSW 2768, ABN 46 673 280 030
- Quote date: 11/06/2026 (11 Jun 2026)
- Quote 0100-A total A$1,815.00 incl GST (net 1650 + GST 165)
  - supply and painting: timber protection rail along wall — 850.00
  - preparation and painting: feature wall, two finish coats colour-matched — 800.00
- Quote 0101-B total A$1,815.00 incl GST (net 1650 + GST 165)
  - aluminium skirting: additional black 5-bar checker-plate ~10 lm + refix existing — 1650.00
- Accepted By: blank on both
- Accepted Date: blank on both
- Client suburb: UNKNOWN
- Client phone/email: not cited on PDFs (issuer phone 0493577719 is ours, not theirs)

These are two scopes, each 1815 incl GST. Do not invent whether they are alternatives, a pair, or a 3630 bundle. Status: not marked accepted.

## Fallback — Romeo Blacktown (STALE)

Embedded claim: F:\\backup\\03 - Projects\\Lead-نقاشی\\Lead-نقاشی.md telegram-log 2023-10-04 16:59
- Name: Romeo
- Email: salrom67@gmail.com
- Number: 0422244996
- Service: Residential Painting
- Source: Google
- Message: onsite quote complete interior house paint (walls and ceilings) in Blacktown NSW. On site 18/19/20 October only.
- Visit window: 18-20 Oct 2023 — STALE (almost 3 years).
Qualify-first. Do not send.

## Next (Snapp) — no send

1) Owner/138 names the real follow-up channel (site manager / email / phone). UNKNOWN now.
2) Confirm whether 0100-A, 0101-B, or both are still live.
3) Confirm site suburb / access / equipment-move window.
4) Quote dollars already exist — do not rewrite them. This is accept/revise/kill, not a new skeleton from zero.

## Quote skeleton

Do not invent a third number. Use the two PDF totals as-is:
- 0100-A A$1,815 incl GST
- 0101-B A$1,815 incl GST
Acceptance lines empty. VERIFIED_CASH=0.

## Missing

Snapp contact channel, suburb, which quote is live, site access, Romeo recency (assume dead until owner says re-open).
