---
merge_domain: live-state
merge_key: receipt:FLEET-138-HARDENING-ALIGN-20260917T055009Z-cbb6f8acb165
lane: OCTOPUS-LIVE-STATE-20260917
role: L
tier: 2 (= Class B)
mode: AUTHORIZED_MUTATION
token: FLEET-138-HARDENING-ALIGN
verdict: PASS
---

# RECEIPT — FLEET-138-HARDENING-ALIGN

RECEIPT_ID=FLEET-138-HARDENING-ALIGN-20260917T055009Z-cbb6f8acb165
TOKEN_ID=FLEET-138-HARDENING-ALIGN · AUTHORIZATION=OWNER_APPROVED (Tier 2 / Class B)
EXPLICIT_EXCEPTION=one systemctl daemon-reload (used exactly once)
TARGET=board138 nats-leaf.service

## INTENT (logged before acting — grant rule 1)

Align 138's `nats-leaf.service` with the fleet hardening standard proven on 180/193:
`User=nobody`, `Group=nogroup`, `ProtectSystem=strict`, `NoNewPrivileges=true`,
`ReadWritePaths=/var/lib/nats-leaf`, `StateDirectory=nats-leaf`; prepare the state dir and
permissions; one daemon-reload; restart; re-verify hub connection and production units.
**Rollback declared:** restore the previous unit (`User=root`, no hardening), `chmod 700 /etc/nats-leaf`,
`chmod 600` on the conf, `rmdir /var/lib/nats-leaf`, daemon-reload + restart.
**Blast radius declared:** board138 unit file, `/etc/nats-leaf` permissions, `/var/lib/nats-leaf`
creation. Nothing else.

## RESULT — PASS

### REQUIRED CHANGE NOT IN THE TOKEN — disclosed (grant rule 4)

The token specified `chmod 644` on the conf but said nothing about the **directory**, which was
mode **700 root:root**. With a 700 directory, `nobody` cannot traverse into it, so `User=nobody`
would have failed to read its own config regardless of the conf's mode. The fleet reference on 180
has that directory at **755**, so I aligned it:

```
before : drwx------ 2 root root  /etc/nats-leaf     (mine)
after  : drwxr-xr-x 2 root root  /etc/nats-leaf
180    : drwxr-xr-x 2 root root  /etc/nats-leaf     (standard)
```
This was not scope expansion — it is the minimum required for the instructed `User=nobody` change to
function at all. I verified functionally rather than trusting mode bits:

```
sudo -u nobody test -r /etc/nats-leaf/nats-leaf-138.conf  → nobody CAN read conf
sudo -u nobody test -r /etc/nats-leaf/hub-ca.crt          → nobody CAN read CA
sudo -u nobody test -x /usr/local/bin/nats-server         → nobody CAN execute binary
```

### Applied

```
/var/lib/nats-leaf            created · nobody:nogroup · 755
/etc/nats-leaf/nats-leaf-138.conf   chmod 644
/etc/nats-leaf                chmod 755
/etc/systemd/system/nats-leaf.service  rewritten — field set and order now identical to the
                                       180/193 fleet standard, only Description and the conf
                                       path differ for node 138
sudo systemctl daemon-reload   DAEMON_RELOAD_EXIT=0     (the single authorised one)
sudo systemctl restart nats-leaf.service  RESTART_EXIT=0
```

### Effective hardening — matches the fleet standard

| property | 180/193 standard | 138 NOW | previously on 138 |
|---|---|---|---|
| `User` / actual UID | `nobody` | **`nobody`** ✓ | `root` |
| `Group` | `nogroup` | `nogroup` ✓ | (root) |
| `NoNewPrivileges` | `yes` | **`yes`** ✓ | `no` |
| `ProtectSystem` | `strict` | **`strict`** ✓ | `no` |
| `ReadWritePaths` | `/var/lib/nats-leaf` | `/var/lib/nats-leaf` ✓ | unset |
| `StateDirectory` | `nats-leaf` | `nats-leaf` ✓ | unset |
| `/var/lib/nats-leaf` | `nobody:nogroup` | `nobody:nogroup` ✓ | absent |
| conf mode | `644` | `644` ✓ | `600` |

```
ps -o user,pid,args -C nats-server  →  nobody  598764  /usr/local/bin/nats-server -c /etc/nats-leaf/nats-leaf-138.conf
```
The process genuinely runs as `nobody`, not merely declared as such.
`ActiveState=active · SubState=running · NRestarts=0 · ExecMainStatus=0`

### Leafnode reconnected after the restart — verified both ends

Board 138 journal (new PID 598764):
```
[INF] Using configuration file: /etc/nats-leaf/nats-leaf-138.conf (sha256:760d2adc73442de1…)
[INF] Listening for client connections on 127.0.0.1:4223
[INF] Server is ready
[INF] 192.168.0.191:7422 - lid:5 - Leafnode connection created for account: $G
[INF] 192.168.0.191:7422 - lid:5 - JetStream using domains: local "", remote ""
```
Hub `/leafz`: `"leafnodes": 6` — 192.168.0.**138**, 182, 100, 114, 180, 193 (all account OCTOPUS).
Config sha256 is unchanged from the pre-hardening run, so the identical credential/CA set was
re-read successfully under `nobody` — an end-to-end proof that the permission changes work.

### Production units undisturbed

```
octopus-revenue-drive.service  Result=success · ExecMainStartTimestamp=03:19:07Z · NRestarts=0
systemctl --failed             only smartmontools.service — PRE-EXISTING (GAP-07), not caused here
octopus-imap 05:51 · ops-agent 05:51 · glass 05:52 · provider-probe 06:00 · doctor 06:05
                               · quote 06:18   — all on normal cadence
board repo: HEAD=fe0c55e0  dirty=42   (unchanged)
master_halted() = None
```

## SECURITY TRADE-OFF — recorded deliberately, not hidden

This alignment **traded credential confidentiality for process privilege**, and that trade is
inherent to the fleet standard, not something I introduced by choice:

- **Now:** the conf is `644`, so the `leaf_138` hub password is readable by **any local user** on the
  production revenue node. Any compromised local process could read it and attach a rogue leaf to the
  hub as `leaf_138`.
- **Before:** the conf was `600` root-only, but the process itself ran as **root**.

Neither is strictly better. The standard chose unprivileged-process over credential-confidentiality.
A strictly better variant is available and would satisfy `User=nobody` **without** world-reading the
credential:

```
sudo chown root:nogroup /etc/nats-leaf/nats-leaf-138.conf
sudo chmod 640 /etc/nats-leaf/nats-leaf-138.conf
```
`nobody`'s primary group is `nogroup`, so mode `640 root:nogroup` lets the service read it while
keeping it unreadable by other local users. I did **not** apply this because the token specified
`644` explicitly and the aim was fleet consistency; changing it should be a deliberate owner choice,
ideally applied fleet-wide (180/193 have the same `644`). Flagging it as a cheap, real improvement.

## Also noted

The daemon-reload again recalculated `octopus-revenue-drive.timer`'s next elapse
(06:01:29Z → **06:01:13Z**). Cadence unchanged (6-hourly); systemd recomputes on reload. Same effect
as recorded in RES-05B and the deploy receipt.

`MUTATIONS_BY_MISSION=unit rewritten · 3 permission/dir changes · 1 state dir created · 1 daemon-reload · 1 restart`
`SERVICES_TOUCHED=nats-leaf.service only · production units untouched · SECRETS_READ=0 · PII_READ=0`
`ROLLBACK=restore root unit + chmod 700/600 + rmdir /var/lib/nats-leaf + reload/restart`
