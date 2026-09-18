---
merge_domain: live-state
merge_key: receipt:FLEET-138-NATS-DEPLOY-FINAL-ADDENDUM-20260917T0550Z
lane: OCTOPUS-LIVE-STATE-20260917
role: L
tier: 1 (= Class A, read-only follow-up)
mode: READ_ONLY
parent_receipt: FLEET-138-NATS-DEPLOY-FINAL-20260917T054314Z-1b798cd6330e
verdict: PASS_WITH_FOLLOWUPS
---

# ADDENDUM — FLEET-138-NATS-DEPLOY-FINAL

PARENT RECEIPT: FLEET-138-NATS-DEPLOY-FINAL-20260917T054314Z-1b798cd6330e (VERDICT=PASS)
THIS ADDENDUM: `PASS_WITH_FOLLOWUPS` — the deployment works, but the bundle's own deploy spec
was not fully visible when I executed, and two items need the owner's call.

Why an addendum and not an edit: the parent receipt is a signed record of what I did with what I
knew. I will not retro-edit it. What follows is what I learned **after** deploying.

## F-1 — THE UNIT I WROTE DIVERGES FROM THE FLEET STANDARD (needs a decision)

`bundles/leaf_138/DEPLOY-README.md` says `cat nats-leaf.service | ssh board138 ...` — but
`nats-leaf.service` was **not actually present in the bundle** (the bundle held only the .conf and
the README), so I authored the unit. The RECEIPT-PHASE2/3 notes call the deployed units
"hardened"; I could not see that pattern beforehand. Comparing against the live units on 180/193:

| property | fleet standard (180, 193) | what I deployed on 138 |
|---|---|---|
| `User` | `nobody` | **`root`** |
| `Group` | `nogroup` | (unset → root) |
| `Group=`/`ProtectSystem` | `strict` | **`no`** |
| `NoNewPrivileges` | `yes` | **`no`** |
| `StateDirectory` | `nats-leaf` | (unset) |
| `ReadWritePaths` | `/var/lib/nats-leaf` | (unset) |
| `/var/lib/nats-leaf` | exists, `nobody:nogroup` | **does not exist** |
| conf mode | `644` (world-readable) | **`600`** (root-only) |
| actual process uid | `nobody` | **`root`** |

So the leaf on the production revenue node currently runs **as root with no systemd hardening**,
whereas its siblings run as `nobody` under `ProtectSystem=strict` + `NoNewPrivileges=true`.

Honest trade-off, not a one-sided defect: the standard's `nobody` model requires the conf to be
**world-readable** (mode 644) so an unprivileged process can read the embedded credential, whereas
mine keeps that credential at 600 root-only. Each protects something the other exposes. But
consistency with the fleet standard matters, and the hardening directives are a real gap.

**I did NOT fix this.** Aligning requires changing the unit, `chmod 644` on the credential file,
`mkdir /var/lib/nats-leaf`, and **a second `systemctl daemon-reload`** — and this token authorised
**exactly one** reload, which is already spent. Per grant rule 6 (Tier boundary wins over speed) I
stopped and am reporting instead of self-expanding.

## F-2 — THE DEPLOY GATE REQUIRED A WITNESS I WAS NOT GIVEN

`DEPLOY-README.md` states, in its own words:

> DEPLOY GATE: board 138 = production revenue node. Deployment is Class B+
> (**token + independent witness 182** per fleet plan phase-4).

My token supplied the owner's Tier-3 authorisation but **no witness-182 attestation**. The owner's
explicit token is the higher authority and I acted under it, but the bundle's gate names a second,
independent requirement that was not satisfied and not mentioned in the token. Flagging it rather
than assuming it was waived — the fleet plan treats 182 as the witness of record precisely for
production nodes, and 182 is also my Class-B verdict authority elsewhere.

## F-3 — the heartbeat subject differed between spec and token (handled)

`DEPLOY-README.md` says publish `octopus.telemetry.138.inventory`; the owner's token said
`octopus.telemetry.138.heartbeat`. I used **`heartbeat`** because the token is authoritative, and
both fall inside the token's authorised publish scope `octopus.telemetry.138.*`. Recorded so the
difference is not later read as an error.

## F-4 — ⚠ CROSS-LANE UNBLOCK: nodes 100 and 160 are NOT actually credential-blocked

`RECEIPT-PHASE2.md` and `RECEIPT-PHASE3.md` mark **node 160 and node 100 as BLOCKED (credentials)**:

> ssh root@160 و ari@160: Permission denied … bundle آمادهٔ deploy … منتظر دسترسی
> root/ari هر دو Permission denied … bundle آماده: bundles/leaf_100/nats-leaf-100.conf

**Both are reachable.** I proved this earlier in this same session (see the live-state recon
correction): `~/.ssh/piggybank_id_ed25519` authenticates as `root` on both, and I completed full
citizenship probes:

```
ssh -i ~/.ssh/piggybank_id_ed25519 root@192.168.0.100  → octopus-compute-100
ssh -i ~/.ssh/piggybank_id_ed25519 root@192.168.0.160  → octopus-compute-160
```
Both: Debian 13 (trixie), OPi5 Pro, up ~2 days, 0 failed units, `octopus-worker-heartbeat.timer`
ticking every ~60s. The same key also opens **114**, which the nats lane did manage to deploy —
so the key was demonstrably in use; it simply was not tried for 100/160.

⇒ The nats phase-2/phase-3 "BLOCKED" verdicts for 100 and 160 are an **artefact of an untested key**,
not a real credential barrier. Their bundles already exist (`leaf_100`, `leaf_160`). Those two arms
can be completed with no new credential work.

## F-5 — I avoided the phase-2 trap (positive result)

`RECEIPT-PHASE2.md` records a self-inflicted lesson: *"باینری اولین بار با مسیر نسبی منتقل نشد
(سرویس restart-loop موقت) — همیشه absolute-path در pipe."* My deployment used absolute paths
throughout (`/usr/local/bin/nats-server`, `/etc/nats-leaf/...`, and an absolute `ExecStart`), so
no restart-loop occurred: `NRestarts=0`, `ExecMainStatus=0`, active since 05:41:34Z.

## Verified-still-true from the parent receipt

```
nats-leaf.service on 138 : active, enabled, NRestarts=0
leafnode to 192.168.0.191:7422 : connected (leaf journal + hub /leafz both confirm)
heartbeat : hub in_msgs 3→4 · in_bytes 566→706 (+140 = exact payload size)
revenue-drive : untouched (Result=success, last run 03:19:07Z)
board repo : HEAD=fe0c55e0 · dirty=42 · master_halted()=None
```

`THIS_ADDENDUM_MUTATIONS=0 · SERVICES_TOUCHED=0 · SECRETS_READ=0 · PII_READ=0`
