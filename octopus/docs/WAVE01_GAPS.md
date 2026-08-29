# Wave 0.1 gaps — not tested

These items must not be recorded as PASS from the 14/14 resilience suite.

## GAP-001 `cold_boot_unverified`

`systemctl restart octopus-sensorium` is not a cold reboot. hym8563 RTC
invalidity at power-on is untested. Status: `DEFERRED_BY_OPERATOR`.

A session-preserving proxy exists: stop `systemd-timesyncd`, restart the
agent, expect G6 fail + `DEGRADED` + `time_unverified` observations, then
restore timesync. That is pre-NTP clock trust, still not power-loss recovery.

## GAP-002 `audit_head_unsigned`

Wave 0 audit records have `signature: null`. The hash-chain plus
`/var/lib/octopus/audit/head.hash` detects in-file rewrites of the past
when the head file is intact. It does not bind the tip to the operator
trust root. Wave 1 should add periodic Ed25519 checkpoints of
`(audit_sequence, head_hash)` signed on an offline host, every 100 records
or daily — not per-record signatures.
