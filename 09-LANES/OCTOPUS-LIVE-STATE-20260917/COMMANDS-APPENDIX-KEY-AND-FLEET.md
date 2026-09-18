---
merge_domain: live-state
merge_key: commands-appendix:octopus-live-state-20260917T0137Z-fleet
lane: OCTOPUS-LIVE-STATE-20260917
mode: READ_ONLY
mutations_performed: 0
revision: 2
---

# COMMANDS APPENDIX — fleet registry + SSH key discovery

The owner asked why three boards were reported unreachable. These are the exact commands
that answered it. All read-only. Kept as a separate file so `LIVE-STATE-COMMANDS.log`
(revision 1) stays intact as the historical audit trail.

---

## A1 — ICMP reachability, all 7 candidate addresses

```
$ for ip in 191 100 160 138 180 182 193; do ping -n 2 -w 1500 192.168.0.$ip; done
192.168.0.191  =>  TTL=128 TTL=128 0% loss      <-- TTL=128 = Windows (this laptop)
192.168.0.100  =>  TTL=64  TTL=64  0% loss      <-- alive, Linux
192.168.0.160  =>  TTL=64  TTL=64  0% loss      <-- alive, Linux
192.168.0.138  =>  TTL=64  TTL=64  0% loss
192.168.0.180  =>  TTL=64  TTL=64  0% loss
192.168.0.182  =>  TTL=64  TTL=64  0% loss
192.168.0.193  =>  TTL=64  TTL=64  0% loss
```
Every address answers ICMP. Nothing was ever "down".

## A2 — ARP identifies the questioning interface as .191

```
$ arp -a
Interface: 192.168.0.191 --- 0x1c            <-- the laptop IS .191
  192.168.0.100   c0-74-2b-f9-7f-fc   dynamic
  192.168.0.138   c0-74-2b-f9-72-d5   dynamic
  192.168.0.160   c0-74-2b-f9-7f-ef   dynamic
  192.168.0.180   c0-74-2b-f9-72-90   dynamic
  192.168.0.182   c0-74-2b-f9-86-64   dynamic
  192.168.0.193   c0-74-2b-fa-fc-8c   dynamic
```

## A3 — port 22 state vs. auth state (the distinction revision 1 missed)

```
$ for ip in 100 160 191 193; do timeout 6 bash -c "echo > /dev/tcp/192.168.0.$ip/22"; done
192.168.0.100  PORT22_OPEN
192.168.0.160  PORT22_OPEN
192.168.0.191  Connection refused        <-- no sshd on this laptop, as expected
192.168.0.193  PORT22_OPEN

$ ssh -v root@192.168.0.100
debug1: Remote protocol version 2.0, remote software version OpenSSH_10.0p2 Debian-7+deb13u2
debug1: Authentications that can continue: publickey,keyboard-interactive
debug1: Offering public key: /c/Users/Armin/.ssh/id_ed25519 ED25519 SHA256:IrKVkKK9SwcdlmrtAiLiUakNQFX8Fb88zuNUBmJIUwg
debug1: Authentications that can continue: publickey,keyboard-interactive
root@192.168.0.100: Permission denied (publickey,keyboard-interactive).
```
Port open + sshd answering + one key rejected ⇒ **auth failure, not unreachability.**

## A4 — the right key: `piggybank_id_ed25519`

```
$ for ip in 100 160; do ssh -i ~/.ssh/piggybank_id_ed25519 root@192.168.0.$ip "echo OK; hostname"; done
192.168.0.100 piggybank => octopus-compute-100
192.168.0.160 piggybank => octopus-compute-160
```
This key appears in the `ls ~/.ssh/` output taken during preflight and was never tried.

## A5 — vitals for the two recovered boards

```
$ ssh -i ~/.ssh/piggybank_id_ed25519 root@192.168.0.100 '<vitals>'
HOSTNAME=octopus-compute-100   UPTIME=up 2 days, 58 minutes   UP_SINCE=2026-09-15 00:39:08
LOAD=0.00 0.00 0.00   OS="Debian GNU/Linux 13 (trixie)"   MODEL=Orange Pi 5 Pro
Mem 3.8Gi total / 249Mi used / 3.6Gi available      Swap 4.0Gi (0B used)
/dev/mmcblk0p1 58G 7.0G 48G 13% /

$ ssh -i ~/.ssh/piggybank_id_ed25519 root@192.168.0.160 '<vitals>'
HOSTNAME=octopus-compute-160   UPTIME=up 2 days, 22 minutes   UP_SINCE=2026-09-15 01:14:52
LOAD=0.00 0.00 0.00   OS="Debian GNU/Linux 13 (trixie)"
Mem 3.8Gi total / 231Mi used / 3.6Gi available      Swap 0B
/dev/mmcblk0p1 58G 2.6G 53G 5% /
```
Both: 5 timers, `octopus-worker-heartbeat.timer` ticking every ~60s, **0 failed units**.
Heartbeat payload self-reports `commander: false`, `may_authorize: false`.

## A6 — the missing node, found in the organism's own registry

```
$ ssh ari@192.168.0.138 'cat /home/ari/ofn/state/fleet-nodes/known_hosts.workers'
192.168.0.100 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBHRgFHKDRDiCqypfWp6xoIOFZuq3cHIUWLgW9/zRMGn
192.168.0.160 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM3S83s0o6eihrc6d7UJF4/pLW/aFhsx+jfbzVhA+ARo
192.168.0.193 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILXZSnpgoKKpbtM7GU8+s3EomN7OEWpWlmO679ONS/uR
192.168.0.114 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/HbnzHBFnTstZXvqcCZsJfVLjm1lHih9ROktOLFnrA   <-- MISSED in rev 1
192.168.0.180 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMtCFyems0rnzNeFCk+XbW6qDMYMNDrkdPeo+8mWbHiu
192.168.0.182 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDVEKircLeHCgRU72Ad+MENMFsAtGALCRFYniVYgfvAv

$ ssh ari@192.168.0.138 'python3 - <parse registry.jsonl>'
/home/ari/ofn/state/fleet-nodes/registry.jsonl   rows = 7   distinct nodes = 7
  DietPi                  -> node_id 138  bind_role commander               auth_status OK
  octopus-continuity-180  -> node_id 180  bind_role quality_restore_copy_RO auth_status OK
  sensorium-opi5pro       -> node_id 182  bind_role lab_witness             auth_status OK
  octopus-compute-100     -> node_id 100  bind_role knowledge_retrieve      auth_status OK
  octopus-compute-160     -> node_id 160  bind_role knowledge_prep          auth_status OK
  octopus-model-plus-193  -> node_id 193  bind_role model_infer             auth_status OK
  octopus-pro-114         -> node_id 114  bind_role eval_batch              auth_status OK
```
**This file is the ground truth for the fleet list.** It holds 7 nodes, all `auth_status: OK`,
and it is what revision 1 should have read first.

## A7 — probing the node revision 1 never knew about

```
$ ping -n 2 -w 1500 192.168.0.114          -> TTL=64 TTL=64 0% loss
$ ssh -i ~/.ssh/piggybank_id_ed25519 root@192.168.0.114 '<vitals>'
HOSTNAME=octopus-pro-114   UPTIME=up 1 day, 22 hours, 48 minutes   UP_SINCE=2026-09-15 02:48:58
LOAD=0.00 0.01 0.00   OS="Debian GNU/Linux 13 (trixie)"   MODEL=Orange Pi 5 Pro
Mem 3.8Gi / 237Mi used / 3.6Gi available
/dev/mmcblk0p1 58G 970M 54G 2%
5 timers (octopus-worker-heartbeat every ~60s)   0 failed units
```

## A8 — confirming that 191 is this machine

```
$ ipconfig | grep -A6 "Wireless LAN adapter Wi-Fi"
   IPv4 Address. . . . . . . . . . . : 192.168.0.191
$ hostname
DESKTOP-KA9RFN5
$ route print -4 | grep "0.0.0.0 "
  0.0.0.0  0.0.0.0  192.168.0.1  192.168.0.191  55
```
Default route via 192.168.0.1 on the 192.168.0.191 interface ⇒ this laptop is .191.

## A9 — corrected clock drift across all 7 nodes

```
$ for each node: drift = remote_epoch - (local_before + local_after)/2
board138  drift=+0.170s rtt=0.384s
board180  drift=+1.122s rtt=2.368s    <-- rtt-dominated outlier (pass 1 for same host: +0.170s)
board182  drift=+0.149s rtt=0.428s
board193  drift=+0.191s rtt=0.481s
board100  drift=+0.266s rtt=0.587s
board160  drift=+0.235s rtt=0.533s
board114  drift=+0.131s rtt=0.443s
```

## A10 — the fleet rebooted together, ~2 days before this snapshot

```
up_since, all 7:
100 2026-09-15T00:39:08    138 2026-09-15T00:39:09    180 2026-09-15T00:39:13
160 2026-09-15T01:14:52    182 2026-09-15T01:21:32    193 2026-09-15T02:24:59
114 2026-09-15T02:48:58
```
No node has rebooted since, so fleet membership yesterday and today are the same.

---

## What was still NOT run

No start/stop/restart/enable/disable on any node, including the two recovered ones. No write
to any file on any board. The only writes were this lane's own artifacts on the laptop.
