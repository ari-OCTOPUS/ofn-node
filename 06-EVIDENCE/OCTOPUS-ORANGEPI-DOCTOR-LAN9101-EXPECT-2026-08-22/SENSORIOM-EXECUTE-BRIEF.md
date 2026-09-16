# SENSORIOM-EXECUTE-BRIEF - doctor LAN:9101 expected PASS

OWNER EXECUTE GRANT `OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-20260822` (AEST 2026-08-22T21:19:00+10:00; **owner_fix_all=true**): on sensorium-opi5pro (192.168.0.182) fix doctor **FAIL** on `metrics_bind` + `unexpected_listeners` caused by intentional **LAN:9101 OPEN** (`0.0.0.0` / UFW LAN-only) after GAP-002 close.

**Intent:** doctor allowlist / expected listeners for **9101 only** — treat `0.0.0.0:9101` **or** `192.168.0.182:9101` as expected PASS; record UFW LAN-only note. **Do NOT close the port. Do NOT revert LAN OPEN.** Keep `gap002_registry` passed.

**Prefer:** DISCOVER-FIRST encode path under `/opt/octopus` (config/allowlist preferred; else script) → backup → minimal expected-bind patch → doctor **readonly** prove.

**Hard bounds:** `WAVE0_hardware=KEEP_LOCKED`; `MQTT=CLOSED`; **no** broad Doctor auto-patch; **no** WAN expose; laptop does **not** SSH — sensoriom executes.

**Package:** `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-2026-08-22/`  
**Rollback:** restore edited doctor allowlist/script from timestamped backup; leave LAN:9101 OPEN; re-run doctor readonly.
