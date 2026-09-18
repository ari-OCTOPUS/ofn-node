# R — PR TRIAGE ORDER (measured CI, 2026-09-18)

Owner's rule: **green ⇒ merge under the standing pre-authorization; red ⇒ reply the exact cause, no action.**
Measured with `gh pr checks <n>` against `ari-OCTOPUS/ofn-node` (main = `ae187e03`).

| order | PR | what it does | measured CI | exact blocker |
|---|---|---|---|---|
| 1 | **#259** | `fix(lead_store)`: `accounts()` no longer caps at 100 — 14 customer leads invisible | fresh-base **fail**, independent-approval **fail**, hygiene pass | needs **rebase onto main** + **independent review** |
| 2 | **#261** | call log table + 10 seeded outcomes | fresh-base pass, hygiene pass, independent-approval **fail** | needs **independent review** only |
| 3 | **#260** | enrichment regex bugs + digest mobile regex | hygiene pass, independent-approval **fail**, **test (ubuntu) fail**, **test (windows) fail** | real test failures + review |
| 4 | **#248** | outcome logger for B2B call results | hygiene pass, independent-approval pass, fresh-base **fail** (two runs) | needs **rebase onto main** |
| 5 | **#262** | j1/j2 strata email draft generator | independent-approval **fail**, **test (ubuntu) fail**, **test (windows) fail** | real test failures + review |
| — | #251 #212 #242 #211 #215 | b2b discovery cleanup / leads sync / digest variants / strata-hub source | not yet triaged | after the five above |

## Notes for R
- `require-independent-approval` (`.github/workflows/independent-review-gate.yml`) cannot be satisfied by
  the author; it needs a second identity's review (past practice: Elahe). It is red on #259/#261/#260/#262
  and **pass** on #248.
- `require-fresh-base` is the cheapest to clear: rebase the branch onto current `main` and push.
- **#259 first** — it is the only one with a direct revenue effect (14 leads invisible to outreach).
- Do not merge #260/#262 until their test failures are explained; both fail on both OSes, which usually
  means the branch predates a main-side contract change rather than a flake.

## Related
- Runtime export PR (L): **#266** — head `50f8727708b8`, `require-fresh-base` pass, `hygiene` pass,
  tests `tests/test_runtime_export_20260918.py` 14/14; awaiting independent review.
- Evidence + per-file sha256: `RUNTIME-EXPORT-RECEIPT-20260918.json` in that branch.
