# ROLLBACK — Orange Pi CHG-E EXECUTE

**Authorization:** `OCTOPUS-ORANGEPI-CHG-E-20260822`  
**Safe state:** hot set consistent; cold restored if READY/index regresses

## Steps

1. Stop further cold deletion/archive expansion.
2. Restore cold objects from archive using **sha256 manifest** (verify each file on extract).
3. Rebuild index again after restore (or restore pre-E index snapshot if taken and verified).
4. Restart sensorium if needed; confirm READY / WatchdogSec behavior healthy.
5. Leave archive retained until owner confirms discard (do not auto-delete archive).
6. Receipt ROLLBACK-ACK with restored paths + digests.

## If archive incomplete / corrupt

- Do not invent replacements; STOP; report missing members; keep whatever hot set remains; escalate to owner.
