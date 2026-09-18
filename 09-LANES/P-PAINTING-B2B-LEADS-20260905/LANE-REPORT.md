---
type: report
lane: P-PAINTING-B2B-LEADS-20260905
status: done
created: 2026-09-05
updated: 2026-09-05
owner_instruction: "Register PR #201 lead list on board138, verify each company as a painting customer, score 1-10 + call priority, find missing phone numbers (owner message 2026-09-05, plan approved same day)."
---

# LANE REPORT — P-PAINTING-B2B-LEADS-20260905

## 1. What was done

1. **Contradiction resolved (39 vs 0).** Owner claimed 39 leads already in `painting.sqlite`;
   measured (read-only SSH, 2026-09-05 ~02:00 UTC): table `painting_b2b_accounts` on board138 had
   **0 rows**; every copy of `tools/ingest_manual_leads.py` on both machines held the same 13 leads;
   no 39-lead list existed anywhere. Actual source: unmerged PR #201 branch `feature/owner-digest`
   (head `6e387e4`) containing **55 leads** + new `tools/owner_digest.py`. Claimed-vs-measured
   numbers recorded per AGENTS.md §3; resolution: list lived only in the PR branch.
2. **Ingest on board138 (owner-authorized write).** Fetched `refs/pull/201/head`, worktree
   `F:\wt-leads-verify-20260905` on new branch `feat/leads-verify-20260905`; scp'd
   `ingest_manual_leads.py` to `board138:~/lanes/painting-b2b-20260905/`; ran against live DB.
   Receipt: **55/55 OK, 0 → 55 rows**, all 0.375/BACKLOG (no score_inputs).
3. **Verification of all 55 companies** (5 parallel web-research passes): existence, role,
   genuine-painting-customer verdict, evidence URL per company. Verdicts: direct customer,
   tender/panel-only, vendor-registration, watch, intel-only, or not-a-customer.
4. **Phone enrichment.** All 6 owner-named missing numbers FOUND (Strata Republic 1300 884 104,
   CF Strata (02) 9313 6255, Montano (02) 9053 7637, Neighbourly 02 8880 1040, NSW DPHI
   1300 305 695 (Planning Portal line — no general switchboard published), SOPA (02) 9714 7888).
   Plus 10 more found (Excel BM (02) 9518 8577, National FM 1300 820 330, Nation 02 9090 4606,
   Opera (02) 9699 1099, Savills +61 2 8215 8888, CBRE +61 2 9333 3333, News Corp (02) 9288 3000,
   Mission Australia 1800 951 123, Parramatta 1300 617 058, Downer 1800 369 637, Sydney Water
   supplier line 1300 690 399, Hays 02 8226 9600). 2 stored numbers corrected (Ace 02 9818 6842,
   Foreshew 02 8379 6631). Claim "33 with phone / 6 without" measured as **37 / 18** before
   enrichment; after enrichment 54/55 have a contact route (only TalentWeb's stored recruiter
   mobile remains unverified).
5. **Scoring.** RELEVANCE normalized to integers on the 1-10 scale + PRIORITY P1 (16) / P2 (32) /
   P3 (7) in notes; APPROACH tags normalized (8 leads had none; Downer non-standard; SOPA none);
   `score_inputs` supplied so the existing kernel `b2b_account_score` computes real scores
   (was uniform 0.375/BACKLOG): **22 HIGH_FIT / 25 QUALIFY / 8 BACKLOG**.
6. **Applied to live DB** via `tools/update_verified_leads.py` (new, on lane branch, commit
   `1c22295` — local only, not pushed): idempotent upsert, 55/55 OK.
7. **`owner_digest.py` run E2E on live data**: 26 callable / 9 panel-sub / 20 other — output saved
   as evidence. Major rescores recorded: Siemens 7→3 (tech vendor, not a paint buyer),
   Capstone 10→5 (recruiter = intel node, not a customer), BPS 7→2 (**competitor** — licensed
   painting/restoration tradesman firm), News Corp 9→7; Core Talent confirmed as the top intel
   call (90-lot Eastern Suburbs strata plan with waterproofing/cladding underway, live on the
   recruiter's own jobs page).

## 2. What remains (open items — mostly owner decisions)

- **PR #201 review + merge** — REVIEW_REQUIRED; overlaps PR #197 ("complete 51 B2B accounts",
  same content riding in #201). Merge/supersede decision is owner's; nothing merged or pushed here.
- **Digest filter bug (PR feedback):** `approach == "Direct"` exact match drops the highest-value
  group accounts ("Direct or Vendor Panel": Strata Choice 10/10, Smarter Communities, BCS/PICA,
  Bright & Duggan, STM, Savills, CBRE-Charter Hall…) out of "Call Today". Suggested fix:
  `startswith("Direct")`. Not changed by this lane (PR is not mine to edit).
- **Guardian Strata trading status**: both its domains fail DNS; number live on Aug-2026
  directories. Confirm by phone before investing effort.
- **TalentWeb**: stored recruiter contact unverified (site refuses automated fetch). Only lead
  without a verified contact route.
- **CBRE number** +61 2 9333 3333 came via search snippet (site blocked fetch) — confirm on call.
- **SOPA RFT SR01200** ($500K–$3.5M, closes 7-Sep-2026 3pm): status from TenderHub (1-Sep);
  buy.nsw page returned 403 to automated fetch — award outcome needs watching.
- **Remaining ~19 strata leads** the owner mentioned but never supplied: still missing; add via
  the same ingest/overlay pattern when provided.
- **Group dedupe strategy**: Smarter Communities ↔ STM share group line 1800 519 642;
  IB Property ↔ Montano ↔ Complete Strata are one group (ibgroup.au). One pitch per group;
  rows kept separate for traceability.

## 3. What failed / limits

- `git fetch origin feature/owner-digest` failed (ref not on origin) → used `refs/pull/201/head`.
  (PR head verified byte-identical: `6e387e4`.)
- `owner_digest.py --db` default is the RELATIVE name `painting.sqlite` → first run silently
  created an empty DB next to the script (Total: 0). Stray file deleted (`rm -f` single file,
  created by this lane); re-ran with absolute path. Logged as PR feedback.
- Web limits: buy.nsw opportunity page 403; talentweb.com.au and coretalent.com.au refused
  automated fetch; stratasense.com.au 403 (phone verified via search instead). Unverified claims
  are marked in notes: RD "est 2010/250+ sites", Smarter "$30B+", ESR "195 assets",
  Downer "300+ sites", Nation "~3,500 apartments" (press-reported), NationalFM "40+ vs 35 yrs".
- No email/message left the machine; no OCTOPUS_WIRE_*/OFN_WIRE_* flags touched;
  `outreach_permission` = `unknown` on all 55 rows (scores never grant permission to act).

## 4. Evidence paths

- Live DB: `board138:~/.local/share/ofn/painting.sqlite` → `painting_b2b_accounts` (55 rows,
  stage=researched, notes carry VERIFIED 2026-09-05 + RELEVANCE + APPROACH + PRIORITY + evidence)
- Board lane dir: `board138:~/lanes/painting-b2b-20260905/` (ingest + overlay + digest scripts)
- Code (local, not pushed): `F:\wt-leads-verify-20260905` branch `feat/leads-verify-20260905`,
  commit `1c22295` (overlay `tools/update_verified_leads.py`), parent `6e387e4` = PR #201 head
- Digest output: `09-LANES/P-PAINTING-B2B-LEADS-20260905/EVIDENCE-digest-20260905.md`
- PR: https://github.com/ari-OCTOPUS/ofn-node/pull/201 (open, unmerged, CI green, 22 checks)
- Vault lane dir: `09-LANES/P-PAINTING-B2B-LEADS-20260905/` (SCOPE.md, this report, evidence)

## 5. Rollback procedure

The table had 0 rows before this lane. Full rollback (removes exactly what this lane added):

```
ssh board138 "python3 -c \"import sqlite3; c=sqlite3.connect('/home/ari/.local/share/ofn/painting.sqlite'); c.execute(\\\"DELETE FROM painting_b2b_accounts WHERE tenant_id='lead'\\\"); c.commit(); print(c.execute('select count(*) from painting_b2b_accounts').fetchone())\""
```

Partial rollback: every row has deterministic `account_id = lead:acct:<slug(business_name)>`;
delete by id list. Rollback of code: `git worktree remove F:\wt-leads-verify-20260905` +
`git branch -D feat/leads-verify-20260905` (nothing pushed anywhere). Board lane dir removal is
owner's call (no deletions performed by this lane beyond the stray empty sqlite it created).
