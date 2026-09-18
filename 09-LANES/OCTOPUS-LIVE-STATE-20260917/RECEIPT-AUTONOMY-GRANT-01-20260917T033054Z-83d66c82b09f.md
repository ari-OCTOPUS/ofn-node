---
merge_domain: live-state
merge_key: receipt:AUTONOMY-GRANT-01-20260917T033054Z-83d66c82b09f
lane: OCTOPUS-LIVE-STATE-20260917
role: L
mode: STRICT_READ_ONLY
---

# RECEIPT — AUTONOMY-GRANT-01 acceptance + Tier-definition gap

RECEIPT_ID=RES-05X-GRANT-ACCEPT-20260917T033054Z-83d66c82b09f
TOKEN_ID=AUTONOMY-GRANT-01
GOV_VERSION=V8
ISSUED=2026-09-17 AEST
VALIDITY=UNTIL_EXPLICIT_REVOCATION
STATUS=ACCEPTED_WITH_BLOCKER

## INTENT (logged before acting, per grant rule 1)

Record receipt of AUTONOMY-GRANT-01, resolve the previously-open receipt-id question, and
determine whether Tier 1 / Tier 2 are defined broadly enough for me to act under them without
a per-action token.
Expected effect: one new file in this lane; zero board mutations; zero service touches.
Blast radius declared: **read-only evidence collection + one lane file.** Nothing on 138.

## RESULT

**1. RECEIPT-ID SCHEME — RESOLVED (this closes a gap I reported twice).**
`RECEIPT_ID_SCHEME=<MISSION>-<UTC_TIMESTAMP>-<SHORT_SHA256>` with **no G-number**.
In RES-05B I reported `G_NUMBER=UNASSIGNED — NO_CONVENTION_FOUND`, having searched the vault and
board 138 and found no G-number ledger (the only `G-NN` in the vault is a *gap* id, `G-51` in
`GAPS-100-2026-09-01.md`, unrelated to receipts). The owner has now retired the field. **The
requirement is dropped, not unmet.**

**2. TIER 1–4 — BLOCKING GAP. The pre-authorization cannot be safely exercised.**
AUTONOMY-GRANT-01 grants `TIER_1_AND_TIER_2 = PRE-AUTHORIZED` and withholds Tier 3/4, and it
imposes mandatory Tier-2 discipline — but it does not define what any tier contains. I searched
for a definition before acting, and found none.

Search performed (read-only):
- vault, all `*.md`/`*.json`: `TIER_1|TIER_2|TIER_3|TIER_4` ⇒ **0 hits**
- board 138, all `*.md`/`*.json`/`*.py` (excluding vault-mirror): only `h3_strata.py` and its tests
- the three vault docs that mention "Tier": `EQUIP-G8-CONTAINMENT-2026-08-16.md` (a
  `READ_ONLY / REVERSIBLE_WRITE` risk classification — a *different* scheme),
  `OCTOPUS-DEFECT-REGISTER.md` (`TASK_TIERS` for **model routing**: local/primary),
  `D3-CONTRACT-FIELDS.md` (`tier: RiskTier`, no 1–4 ladder)

What the `TIER1/TIER2` hits actually are:
- `ofn/agents/h3_strata.py`: `TIER1_METRO` / `TIER2_GREATER` = **geographic** LGA tiers for the
  painting leads. Unrelated to authority.
- `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` §8.2–8.4: Tier 1 = resolver
  fixtures, Tier 2 = predicate fixtures, Tier 3 = coverage fixtures = **test-harness** tiers from
  the OD-4 halt-oracle doctor work. Unrelated to authority, and critically it **has no Tier 4**.

**3. SECOND AMBIGUITY — two overlapping ladders now coexist.**
TOKEN-DELEGATE-01 (earlier today) defined **Class A / Class B / Class C**. AUTONOMY-GRANT-01 now
defines **Tier 1 / 2 / 3 / 4**. Both are live. It is not stated whether Tier is a *rename* of
Class or an *independent* ladder layered on top.

Why I did not resolve this myself: if Tier is a rename, then Tier-1/2 pre-authorization could
plausibly swallow things TOKEN-DELEGATE-01 put behind a Class-B token (board-138 config changes,
PII export, `state/` + SQLite/WAL, changes under `F:\backup` / `F:\ofn-node`). Inferring that
would be me widening my own authority — which AGENTS.md §5 forbids outright ("Never raise your
own authority… An attempt to self-elevate is an incident and gets logged").

## SCOPE CONTROL — grant rules honoured, not stretched

Grant rule 4 (do not self-expand mid-action) → **no action taken beyond reading.**
Grant rule 6 (Tier boundary always wins over speed) → **no self-directed action taken at all.**
I therefore did **not** exercise the Tier-1/2 pre-authorization. I continued to operate only
under the already-defined **Class A** of TOKEN-DELEGATE-01, which is unambiguous.

`MUTATIONS_ON_138=0 · SERVICES_TOUCHED=0 · GIT_MUTATIONS=0 · SECRETS_READ=0 · PII_READ=0`
Files created by this receipt: 1 (this file, in this lane — a Class-A destination per
TOKEN-DELEGATE-01).

## ESCALATION TRIGGERS — restated so they are unambiguous and mine to honour

I will stop and ask on any of these, regardless of the grant:
1. production merge to `main`
2. any force-push
3. HALT / HALT-ALL / I7-expiry change
4. secret or token rotation
5. any action where `CUSTOMER_EGRESS_POSSIBLE=YES` **and** approval-state = UNKNOWN
6. any action irreversible without an already-proven working rollback

Note on trigger 5: RES-05C resolved that specific unknown for the revenue chain — during the
authorized run `owner_reply` reported `new_owner_messages: 0`, so no approval was pending and
customer egress was not reachable that run. Trigger 5 remains live for any *future* action that
re-opens it.

## BLOCKER (for the owner/relay)

Tier 1–4 are undefined, and the Tier↔Class relationship is unstated. Until that is resolved,
the only authority I can safely exercise is Class A, and the Tier-2 INTENT/RESULT discipline
cannot be applied to a boundary I cannot see.
