---
merge_domain: live-state
merge_key: receipt:FLEET-138-TELEMETRY-AUTO-PULSE-20260917T055545Z-35a4bca98c60
lane: OCTOPUS-LIVE-STATE-20260917
role: L
tier: 2 (= Class B)
mode: AUTHORIZED_MUTATION
token: FLEET-138-TELEMETRY-AUTO-PULSE
verdict: PASS
---

# RECEIPT — FLEET-138-TELEMETRY-AUTO-PULSE

RECEIPT_ID=FLEET-138-TELEMETRY-AUTO-PULSE-20260917T055545Z-35a4bca98c60
TOKEN_ID=FLEET-138-TELEMETRY-AUTO-PULSE · AUTHORIZATION=OWNER_APPROVED (Tier 2 / Class B)
EXPLICIT_EXCEPTION=one systemctl daemon-reload (used exactly once)
TARGET=board138 periodic telemetry heartbeat

## INTENT (logged before acting — grant rule 1)

Install a stateless 60-second telemetry pulse on 138 that emits a fixed 140-byte JSON heartbeat on
`octopus.telemetry.138.heartbeat` into the local NATS leaf client port; register a service+timer;
one daemon-reload; verify delivery and that production loops are untouched.
**Rollback declared:** `systemctl disable --now octopus-138-pulse.timer` · remove
`/etc/systemd/system/octopus-138-pulse.{service,timer}` · remove
`/usr/local/bin/octopus-138-pulse.sh` · daemon-reload. Nothing else is touched.
**Blast radius declared:** two new unit files + one script on 138.

## RESULT — PASS

### 1. Time sync

```
Local time: Thu 2026-09-17 05:53:10 UTC        Time zone: UTC (UTC, +0000)
System clock synchronized: yes                 NTPSynchronized=yes
NTP service: inactive                          NTP=no
```
`TIME_SYNC_OK=YES` on the authoritative field (`System clock synchronized: yes`), with one caveat
recorded honestly below.

### 2. Pulse script — fixed 140-byte frame by construction

`/usr/local/bin/octopus-138-pulse.sh`, mode 755, stateless (writes nothing to disk). It builds the
JSON, then grows a `pad` field until the frame is **exactly 140 bytes**, so every pulse is the same
size — a fixed-frame contract rather than a variable-length one.

Test-run as the real service identity **before** installing any timer:
```
sudo -u nobody /usr/local/bin/octopus-138-pulse.sh
PULSE_SENT bytes=140 subject=octopus.telemetry.138.heartbeat ok=True     EXIT=0
```

### 3. Units installed

```
/etc/systemd/system/octopus-138-pulse.service   Type=oneshot · User=nobody · Group=nogroup
                                                NoNewPrivileges=true · ProtectSystem=strict
                                                After=network-online.target nats-leaf.service
/etc/systemd/system/octopus-138-pulse.timer     OnBootSec=1min · OnUnitActiveSec=60s
                                                AccuracySec=1s · WantedBy=timers.target
sudo systemctl daemon-reload                    DAEMON_RELOAD_EXIT=0    (the single authorised one)
sudo systemctl enable --now octopus-138-pulse.timer   ENABLE_EXIT=0
  Created symlink /etc/systemd/system/timers.target.wants/octopus-138-pulse.timer
```

### 4–6. Verified firing and delivery

```
octopus-138-pulse.timer   LAST 05:55:08Z · NEXT 05:56:08Z   → exact 60 s cadence
journal                   PULSE_SENT bytes=140 subject=octopus.telemetry.138.heartbeat ok=True
                          Result=success · ExecMainStatus=0 · User=nobody
```

**The earlier gap I flagged is now closed.** At the previous mission the hub had `"streams": 0`, so
telemetry had nowhere to go. A stream now exists:

```
stream OCTOPUS_EVENTS  subjects:["octopus.>"]  retention:limits  storage:file  max_bytes:2GB
  created 2026-09-17T05:46:16Z
```
It captures the heartbeat subject, and delivery is proven by counter growth, not assertion:
```
JetStream messages: 5 → 6   (bytes 1149)   over one 60 s pulse window
```
So the chain is complete: script → local leaf 127.0.0.1:4223 → leafnode → hub → **JetStream persisted**.

### 5. Production undisturbed

```
octopus-revenue-drive.service  Result=success · ExecMainStartTimestamp=03:19:07Z · NRestarts=0
systemctl --failed             only smartmontools.service — PRE-EXISTING (GAP-07)
octopus-ops-agent 05:56 · glass 05:57 · doctor 06:05 · imap 06:06 · quote 06:18 — normal cadence
board repo: HEAD=fe0c55e0  dirty=42   (unchanged)
master_halted() = None
```
`REVENUE_CHAIN_UNDISTURBED=YES`

## HONEST CAVEATS

### A. systemd explicitly flags `User=nobody` as unsafe

Every pulse logs:

```
/etc/systemd/system/octopus-138-pulse.service:8: Special user nobody configured, this is not safe!
```
This is **not** something I introduced — it is fleet-wide and inherent to the hardening standard the
previous token adopted:
```
138 nats-leaf.service : 3 occurrences
138 pulse.service     : 1 occurrence
180 nats-leaf.service : 1 occurrence   ← the reference "hardened" unit has it too
```
`nobody` is a shared account used by many daemons; systemd warns because multiple services sharing
one UID can read each other's files and signals (privilege confusion). The correct fix is a
**dedicated system user per service** (e.g. `octopus-nats-leaf`, `octopus-pulse`) with
`DynamicUser=` or a static `sysusers.d` entry. That would be strictly better than `nobody` **and**
would keep the credential at `640 root:nogroup` instead of world-readable `644` — closing both
weaknesses noted in the hardening receipt. Flagged, not changed: the fleet standard says `nobody`,
and changing it should be a deliberate fleet-wide decision.

### B. `NTP service: inactive` while the clock reports synchronized

`System clock synchronized: yes` but `NTP=no` / `NTP service: inactive`. The clock is currently
synced (and measured drift against the laptop earlier was ~0.17 s), but **no NTP daemon is actively
maintaining it**. For a telemetry stream whose value depends on its timestamp, a clock that is
correct now but unmaintained can silently drift. Worth pairing with the pulse stream: the hub could
alert if consecutive `utc` stamps from 138 diverge from the hub's own clock. Recorded as an
observation, not acted on.

### C. Known cosmetic note

The daemon-reload again recomputed `octopus-revenue-drive.timer`'s next elapse
(06:01:13Z → **06:00:59Z**). Cadence unchanged (6-hourly); same effect recorded in RES-05B and the
two prior receipts.

`MUTATIONS_BY_MISSION=1 script + 2 unit files on 138 · 1 daemon-reload · 1 timer enabled+started`
`SERVICES_TOUCHED=octopus-138-pulse (new).timer/service only · production loops untouched`
`SECRETS_READ=0 · PII_READ=0 · GIT_MUTATIONS=0`
`ROLLBACK=disable --now timer + rm units + rm script + daemon-reload; revenue chain unaffected`
