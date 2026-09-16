# 182 inbox leftover classify 2026-08-27 ~12:35 AEST

PC GO: relocate only expired or already_processed so 04af67d5 becomes FIRST_CLAIMABLE. If leftovers are not that class, report blocker. Do not stampede. Do not raise max_n. Do not DM.

## Worker rule
FIRST_CLAIMABLE = first scan item with classification=verification_accepted.
expired/ping/generic rejected CONTINUE (do not consume max_n).
already_processed = verdict_recorded (processing file or verdicts_log phase=final).

## Classify (live Worker.scan)
- inbox scanned: 256
- already_processed: 0
- expired-reason: 239 (rejected; do not block cap)
- verification_accepted: 16

## FIRST_CLAIMABLE now
5ed83e5d-ec56-4df6-8e55-e16319d77fd1 type=verification_task run=verify-6ac25b31-c07 VALID unprocessed

## Valid accepted AHEAD of 04af67d5 (12)
5ed83e5d verify-6ac25b31-c07
662304ed verify-7950c2f6-ba8
ae47caa1 verify-854d25e1-0af
05b67293 verify-ecb9d63c-c35
f2911ad1 verify-5834522f-a8c
94d01dd2 verify-831bf290-83a
e0909fef verify-58d93eb6-528
ebacb424 verify-c6870486-b33
afc0e754 verify-f3d4dd9e-8a0
23efdc65 verify-5dc9f4c0-9a4
ecc1f043 verify-5412cc1c-c5c
c3f085a8 verify-2884079c-3b8  (B1 leftover verify, still valid not expired)

Then 04af67d5 verify-be612088-715 (B2) still verification_accepted.

## Action
MOVED: 0
Did not relocate the 12: they are valid unprocessed, not expired/already_processed.
Did not relocate 239 expired: they do not block FIRST_CLAIMABLE.
Did not raise max_n. Did not DM 182. Did not stampede.

BLOCKER: leftovers that block 04af67d5 are valid verification_accepted, not the 2884079c class.
B OPEN. No PERSISTENT_GREEN.