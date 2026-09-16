# ROLLBACK - Orange Pi GAP-002 registry close

**Authorization:** `OCTOPUS-ORANGEPI-GAP002-CLOSE-20260822`  
**Safe state:** `open-gaps.json` restored to pre-edit backup; doctor reflects prior registry truth honestly

## Steps

1. Stop further edits to `open-gaps.json` / related manifests.
2. Restore `open-gaps.json` from the timestamped backup taken in EXECUTION-ORDER Step 3.
3. Verify restored file sha256 matches **before** hash from BEFORE receipt.
4. Re-run doctor **readonly**; record that gap002_registry may again show NEED_OWNER / `signature_does_not_close_registry` (expected if rollback undoes the close).
5. Do **not** invent alternate registry files or zero-fill to "force green".
6. Write `ROLLBACK-ACK.json` with restored path, digests, doctor excerpt; copy summary to TO-LAPTOP exchange.

## If backup missing / corrupt

- STOP. Do not reconstruct from memory. Report missing backup; escalate to owner with current file sha256 and doctor excerpt.