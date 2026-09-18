---
type: scope
lane: P-PAINTING-B2B-LEADS-20260905
created: 2026-09-05
status: done
owner_instruction: "Register PR #201 lead list on board138, verify each company as a painting customer, score 1-10 + call priority, find missing phone numbers (owner message 2026-09-05)."
---

# Lane P-PAINTING-B2B-LEADS-20260905 — Scope

## Mission
Ingest the 55-lead B2B painting list from ofn-node branch `feature/owner-digest` (PR #201, unmerged)
into the live `painting.sqlite` on board138, verify every company as a genuine painting-services
customer, assign RELEVANCE 1-10 + call priority P1/P2/P3, enrich the 6 missing phone numbers,
and close with LANE-REPORT.md.

## Owns (may write)
- `09-LANES/P-PAINTING-B2B-LEADS-20260905/` (this lane dir in the vault, additive files only)
- ofn-node worktree `F:\wt-leads-verify-20260905` on NEW branch `feat/leads-verify-20260905`
  (derived from `origin/feature/owner-digest`; the PR branch itself is never modified locally)
- board138: `~/lanes/painting-b2b-20260905/` (ad-hoc lane dir; scp + python execution)
- board138 DB rows in `painting_b2b_accounts` via idempotent `LeadStore.create_account` upsert,
  account_id prefix `lead:acct:` — this write is explicitly owner-authorized ("run it on board138").

## Forbidden
- No merge / push / approve of any PR (PR #201 review+merge is an owner decision — stays open)
- No commits to the vault; no `rm -rf`; no synthetic data
- No outbound of any kind: `auto_email` closed, no flags `OCTOPUS_WIRE_*` / `OFN_WIRE_*` /
  `OBSERVATORY` / `CORTEX_HYPOTHESIS` enabled
- `outreach_permission` stays `unknown` on every row — scoring never grants permission to act
- On board138: no service restarts, no flag/env changes, no changes to `~/ofn` checkout,
  read-only SQL except the authorized upsert
- No writes outside the owned paths above; other lanes' files untouched

## Truth sources
- Live DB on board138 `~/.local/share/ofn/painting.sqlite` (level 1)
- Branch content `origin/feature/owner-digest` (level 2 once ingested)
- Contradiction log: "39 leads in DB" (owner claim) vs 0 rows measured 2026-09-05 —
  resolved: list lived only in PR #201 branch, never ingested. Recorded in LANE-REPORT.

## Rollback anchor
All inserted rows carry deterministic `account_id = lead:acct:<slug(business_name)>`;
selective rollback = DELETE of exactly those ids (full list in LANE-REPORT).
