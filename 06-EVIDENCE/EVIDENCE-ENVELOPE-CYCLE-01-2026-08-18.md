---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, handshake, verifier, envelope]
author: "laptop agent — WAVE0 Evidence Envelope cycle-1"
---

# Evidence Envelope cycle-1 (2026-08-18 ~02:10 +10)

Host `DESKTOP-KA9RFN5`. Sidecar `_ops/handshake/emit_cycle.py` — **not** TCB/daemon.
schema `octopus-handshake-envelope/1`. autonomy_delta=0. WAVE0_OBSERVE_ONLY.

## Claim

`:8801` returns 401 without bearer; 4d daemon is ticking; GITWRITE-FAILED remains;
hourly `--tags` is rejected on `pre-deploy-2026-07-25`; equip tip matches germline
`octopus.git`.

## Envelope files (verifier hashes these, not this paragraph)

| receiver | bytes | sha256 | path |
|---|---|---|---|
| sensorium | 6677 | `83d47f47b618efd231eb6c0bbe96818b41e42ea24e63e8da5a7fd26462ca2fa6` | `06-EVIDENCE/envelopes/cycle-01-sensorium.json` |
| feet | 6672 | `0cab6661c3723518384d877a2cf7b7482aa4589a4cba37a3d2d50d5d951bb24a` | `06-EVIDENCE/envelopes/cycle-01-feet.json` |

Companion `*.json.sha256` sits next to each file (self-hash is not inside the JSON).

## Raw (selected)

```
curl.exe … https://127.0.0.1:8801/api/board-cp/pull
{"ok": false, "reason": "board_bearer_required"} HTTP=401
exit=0  ts=2026-08-18T02:10:10+10:00
```

```
daemon_state slice: pid=24588 resumed_at=2026-08-17T21:08:26
last_tick_at=2026-08-18T02:09:37 tick_this_run=520 errors_this_run=0
```

```
GITWRITE-FAILED 2026-08-16_035024 : git-write lock TIMEOUT after 40 attempts
on F:\backup\_ops\backup\gitwrite.lock   (120 bytes, still present)
```

```
commands: 01a0096d/01a009d1/01a00b85 = unknown_outcome
          01a00d3d = dispatched
```

```
equip/g10-cognition-20260816
local=d10887cbb5c80ec2c3e347f070556ba8276d8a79
remote=d10887cbb5c80ec2c3e347f070556ba8276d8a79
```

```
git push --dry-run E:/germline/vault.git --tags   exit=1
 ! [rejected] pre-deploy-2026-07-25 (already exists)
```

## Reproduction (run on laptop; do not take this note as proof)

```
curl.exe -sk --max-time 8 -w " HTTP=%{http_code}" https://127.0.0.1:8801/api/board-cp/pull
git -C F:\backup push --dry-run E:/germline/vault.git --tags
git -C F:\backup rev-parse equip/g10-cognition-20260816
git --git-dir=E:/germline/octopus.git rev-parse refs/heads/equip/g10-cognition-20260816
```

Hermetic tests (not the live path):

```
python -X utf8 F:\backup\_ops\tests\test_evidence_envelope_handshake.py
```

6/6 PASS. Green tests do not clear GITWRITE-FAILED.

## Uncertainty

`daemon_state.json` hash in `artifacts[]` (`ef619818…`) differs from the hash
captured inside `raw` (`bb1b7b62…`) because the daemon wrote the file between
those two reads. That is live-tick drift, not SMB zero-byte. Verifier should
hash the envelope JSON, not expect daemon_state to freeze.

SSH to `.138` was publickey-denied in the prior session; feet mounts not
re-checked this cycle.

## Escalation

If reproduction disagrees: ≤3 retries, then owner. Do not delete the flag.
Do not ack `01a00d3d`.
