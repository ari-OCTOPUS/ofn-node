---
type: owner-decision
lane: A-R0-IDENTITY
as_of: 2026-09-03T19:54+10
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
vantage: this_host_only
scope: this_host_only
claim_type: owner_decision
may_authorize: false
hold_external: true
send: none
winner: none
resolution: owner_on_request
status: decided_by_owner
applies_to: future_DET_letter_wording_only
requires: none
---

# حکم مالک — بیمه DET = «on request»

```
node_id: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191   # prior A session Get-NetIPAddress Wi-Fi; this host = laptop vault, not board 180
vantage: this_host_only
scope: this_host_only
claim_type: owner_decision
```

مالک این نشست صریحاً انتخاب کرد:

**ک) حکم مالک: بیمه = «on request» — رقم آلینز را در نامه نگذار**

این `owner_decision` است. نامه DET ارسال نشد. نامهٔ پرشدهٔ جدید ساخته نشد.

## Applies to

| surface | effect |
|---|---|
| future DET / letter wording | use on-request; do not put Allianz dollar figures in the letter |
| historical notes (`CURRENT-TRUTH`, R0-CLOSE receipts, OWNER-PACK, LANE-A identity note, SEASON-LOG) | unchanged FILE_VERIFIED claims; not rewritten this session |

`resolution: owner_on_request` applies to **outgoing wording**, not to deleting or “fixing” old files.

## value_A vs value_B (kept visible)

| claim | value_A | source_A | value_B | source_B | resolution | status |
|---|---|---|---|---|---|---|
| DET insurance wording | certificates on request; no insurance number invented | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` sha256 `b5bd72e4f360392f148ecc830d1aa12ed9375b43ccf21c4786e21272f0eeb67a` | cite Allianz PL figure (and policy id in some drafts) in DET text | `CURRENT-TRUTH.md` + `LANE-A-R0-BUSINESS-IDENTITY-2026-09-03.md` + `R0-CLOSE-EXECUTION-20260902T1340Z-RECEIPT.md` + `OWNER-PACK-R0-CLOSE-2026-09-02.md` (hashes in `INSURANCE-WORDING-OPEN.md`) | owner_on_request for future DET/letter only | decided_by_owner (outgoing); historical files remain as written |

Identity numbers (ABN / policy id) stay in source files. This note uses presence + path + hash only.

Pointer back: `09-LANES/A-R0-IDENTITY/INSURANCE-WORDING-OPEN.md`
