# LANE-REPORT — A-R0-IDENTITY

Report date: 2026-09-03T19:54+10 (owner insurance ruling recorded).
Lane: A-R0-IDENTITY. Host: `DESKTOP-KA9RFN5` Wi-Fi `192.168.0.191` (Get-NetIPAddress prior A session; this host = laptop vault, not board 180). No send. No C-file edits. No commit. No painting winner. No new filled DET letter.

## 1. What was done

- Owner ک recorded as `owner_decision`: insurance wording for future DET/letter = «on request»; do not put Allianz dollar figures in the letter.
- Wrote `INSURANCE-OWNER-RULING-2026-09-03.md` (`resolution: owner_on_request`, `status: decided_by_owner`, `applies_to: future_DET_letter_wording_only`).
- Pointed `INSURANCE-WORDING-OPEN.md` at that ruling; kept value_A vs value_B and historical $20M citations visible; did not edit CURRENT-TRUTH, PRICE-RULING, R0-CLOSE receipts, or OWNER-PACK.
- Refreshed `VOTE-SLIP-FOR-C.md`: insurance is no longer pick-one; C packet files untouched.
- Optional HANDOFF wikilink + `07-HANDOFF/A-R0-INSURANCE-WORDING-RECORDED-2026-09-03.md` (`status: recorded`, `requires: none`).

## 2. What remains

- Workers compensation certificate file still missing on vault (prior A listing).
- Painter licence file still missing on vault (prior A listing).
- `[NAME]`, owner-hands DET send, $306.90: unchanged; not this slice.
- C may ingest the vote slip later. A did not touch C packets.
- Historical files still contain $20M / cite-Allianz wording. That is intended.

## 3. What failed

- Nothing blocked the ruling write.
- PDF page content not opened (PII/binary). Index figures remain file-cited, not re-extracted from PDF bytes this pass.
- Host IP not re-queried this slice; reused prior A session value (`192.168.0.191`).

## 4. Evidence paths

| Claim | Value | Source | Grade | Status |
|---|---|---|---|---|
| owner ruling | on-request for outgoing DET; no Allianz $ in letter | this session owner ک + `INSURANCE-OWNER-RULING-2026-09-03.md` | E2 | decided_by_owner |
| value_A wording | certificates on request; no insurance number invented | `PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` sha256 `b5bd72e4…f0eeb67a` | E2 | recorded |
| value_B wording (historical) | later notes cite Allianz PL figure in DET | `CURRENT-TRUTH.md` + `LANE-A-R0-BUSINESS-IDENTITY-2026-09-03.md` + `R0-CLOSE-EXECUTION-20260902T1340Z-RECEIPT.md` + `OWNER-PACK-R0-CLOSE-2026-09-02.md` | E2 | FILE_VERIFIED historical; not rewritten |
| Allianz PDF present | true | Test-Path prior A pass `company-docs/2026-PUBLIC-LIABILITY-ALLIANZ.pdf` | E2 | verified prior pass |
| Allianz sha256 | `53048a13a693d2364f771679a7fcaaf5c3c074e8321667687901c7635a138007` | Get-FileHash prior A pass | E2 | matches index |
| workers-comp PDF | absent | company-docs listing prior A pass | E2 | verified absent |
| painter licence PDF | absent | owner-board depth-2 name search prior A pass | E2 | verified absent |
| send | 0 | this session | E2 | verified |
| C packet edit | 0 | this session | E2 | verified |

## 5. Rollback steps

Move `09-LANES/A-R0-IDENTITY/INSURANCE-OWNER-RULING-2026-09-03.md` and `07-HANDOFF/A-R0-INSURANCE-WORDING-RECORDED-2026-09-03.md` to `99-ARCHIVE/` with `archive_` prefix. Restore prior `INSURANCE-WORDING-OPEN.md` / `LANE-REPORT.md` / `VOTE-SLIP-FOR-C.md` / HANDOFF pin from git if needed. Do not `rm -rf`. No flags, sends, or commits.

**Exit status:** owner ruling recorded for outgoing wording. Historical contradiction left visible. External effects none.
