---
type: contradiction
id: HOLD-EXTERNAL-vs-M5
status: open
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# Phase B — paper contradiction (Season 5 not overwritten)

`01-TRUTH/SEASON-5-2026-09-04.md` was **not** rewritten. `SEASON-5-BOARD-MIRROR.md` was not rewritten.

Both Season-5 markdown files are byte-identical this session:

| Path | sha256 |
|---|---|
| `01-TRUTH/SEASON-5-2026-09-04.md` | `9A9D7E1207906D7A3DA637A2EBF72988D9BF8601598516233D20D0D2E07F0CA7` |
| `01-TRUTH/SEASON-5-BOARD-MIRROR.md` | `9A9D7E1207906D7A3DA637A2EBF72988D9BF8601598516233D20D0D2E07F0CA7` |

## Value A

`HOLD_EXTERNAL` still true for Telegram / live OF / paid ads without a separate GO.

Source: `01-TRUTH/SEASON-5-2026-09-04.md` line 12 (same bytes as the board mirror).

## Value B

Key `HOLD_EXTERNAL` is **absent** from `season5-gates-final.json`. Key present: `m5_owner_release = ACTIVE_REAL_SEND_AUTHORIZED`.

Source this session: not a fresh 138 read. Cited prior receipt `09-LANES/U-WHY-NOT-LIVE-20260905/PLAN-EXECUTE-RECEIPT.json` `gates_probe` stdout (keys listed; `has_HOLD_EXTERNAL_key=false` in `PLAN-EXECUTE-CONTINUE.json`). The JSON file itself is **not on this vault** (`glob **/season5-gates-final.json` → 0).

`resolution: null` · `status: open`

Runbook step 1 («change chapter 5 to lift HOLD») has no subject on the 138 gates object. Confirmed by the runbook §0 and by the U-WHY probe.

## B3 validators

Lane-local files in this directory were written with frontmatter. Full-vault validators were **not** re-run this session (triage 2026-09-05 parked historical 484 frontmatter / 67 link errors as a separate project). Two claims stay separate: this lane vs whole vault. Whole-vault pass/fail = `unverified` here.
