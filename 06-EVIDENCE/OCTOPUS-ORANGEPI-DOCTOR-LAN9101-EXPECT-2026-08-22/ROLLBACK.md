# ROLLBACK - Orange Pi doctor LAN:9101 expected PASS

**Authorization:** `OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-20260822`  
**Safe state:** doctor expected/allowlist files restored to pre-edit backup; **LAN:9101 remains OPEN** (do not use this rollback to close the port)

## Steps

1. Stop further edits to doctor script/config/allowlist files.
2. Restore **only** the doctor encode files edited in EXECUTION-ORDER Step 4 from their timestamped backups.
3. Verify restored file sha256 matches **before** hash from BEFORE receipt.
4. Confirm `ss` still shows LAN OPEN for :9101 (`0.0.0.0` or `192.168.0.182`) — if somehow closed during mistaken ops, **re-open per LAN-9101-EXECUTE** (do not leave closed as "rollback").
5. Re-run doctor **readonly**; expect `metrics_bind` / `unexpected_listeners` may again FAIL (honest pre-allowlist SoT). Confirm `gap002_registry` still passed.
6. Do **not** invent alternate doctor files or close 9101 to "force green".
7. Write `ROLLBACK-ACK.json` with restored paths, digests, doctor excerpt, listen address; copy summary to TO-LAPTOP exchange.

## If backup missing / corrupt

- STOP. Do not reconstruct from memory. Report missing backup; escalate to owner with current file sha256, doctor excerpt, and current `ss` :9101 line.
