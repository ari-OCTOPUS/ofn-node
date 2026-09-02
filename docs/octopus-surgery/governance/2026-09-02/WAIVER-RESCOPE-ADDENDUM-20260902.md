# WAIVER RE-SCOPE ADDENDUM — 2026-09-02 (owner ruling, live session)

## What this is

Records the owner's 2026-09-02 evening ruling (live ZCode session; also recorded
in the owner board `CURRENT-TRUTH.md` update ix and on PR #71) re-scoping the
**SECRET-ROTATION-WAIVER-20260831** record. The signed waiver on board138
remains the authoritative instrument; this addendum is the in-repo record of
the scope interpretation. Nothing here re-arms anything.

## The ruling

1. **External-messaging clause, superseded in scope:** the waiver's
   "external messaging: not_authorized" line predates the owner's
   2026-09-02 ruling that the six PAINT-L5-001 first-contact sends
   (2026-09-01 13:16:59Z ×5 burst + 2026-09-02 ~02:00Z in-flight sixth)
   were authorized ("بله اجازه دادم"). For the PAINT-L5-001 first-contact
   campaign, the waiver's external-messaging clause is therefore recorded
   as satisfied-by-owner-authorization, not violated.
2. **Everything else in the waiver stands unchanged** — secret-rotation
   requirements included. Secrets remain `risk_accepted_unrotated` until
   the rotation work happens.
3. **The outbound WAL stays DISARMED** (`owner-disarm-armin-2026-09-02`,
   valid JSON `"0"`). Any re-arm is a deliberate owner act with a signed
   receipt — the Q-05 lesson, now standing policy.
4. **Sixth-send question closed by the same session:** the 2026-09-01 pause
   commit (110f6c0) intended only to prevent subsequent sends; the sixth
   send was in flight at pause time. Recorded as timing-inconsistency,
   NOT a pause-window violation. Ledger semantics of PAINT-L5-001:
   6 outbound contacts, 0 replies, 0 payments.

## Why this is a new file and not an edit

The repo's waiver fixture and its send-gate test
(`tests/fixtures/waiver/SECRET-ROTATION-WAIVER-20260831.json`,
`tests/test_no_external_send_while_waiver_active.py`) are inside **PR #72's
changeset**. Lane file-ownership forbids touching them from another branch;
the fixture/test re-scope lands stacked immediately after #72 merges. This
addendum intentionally touches no other file.

## Evidence pointers

- Owner board: `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\CURRENT-TRUTH.md`
  — update blocks "night" (incident resolved-authorized), "night, ii"
  (disarm clean), "night, ix" (this re-scope ruling).
- PR #71 comments 5504052540 (6-effects evidence) and 5504087004 (owner
  authorization ruling), and the 2026-09-02 timing-inconsistency comment.
- board138 `ofn/agi2027_runtime/outbound-effects.sqlite3` (machine-local,
  `owner_attested` from this machine's vantage; copy at
  `C:\Users\Armin\board138-outbound-effects.sqlite3`).
