---
type: evidence
status: active
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, custodian, contradiction, wave0]
sources:
  - "[[../NETWORK-PATH-5GHZ-2026-08-18]]"
  - "[[../HOURLY-PUSH-EMPTY-ERR-2026-08-18]]"
  - "[[../sensorium-d14-verify-2026-08-18/PENDING-CHARTER-V2]]"
  - "[[../../00 - Inbox/2026-08-18 NOTE — verification doctrine activation order (laptop first)]]"
---

# Contradictions preserved — custodian-191 2026-08-18T03:08+10

Do not resolve by guess. Both sides + evidence paths. Recorder `.191`, WAVE0_OBSERVE_ONLY.

## (a) write-bench 40–73s vs owner-stated 1080ms

| side | claim | evidence | this pass |
|---|---|---|---|
| A | Local 200×4KB write-bench 53452.7ms / 73387.0ms / recheck 40411.9ms | `06-EVIDENCE/NETWORK-PATH-5GHZ-2026-08-18.md` | **not re-run** (no experimental bench) |
| B | Owner-stated prior **1080ms** | same file, “not reproduced”; “not re-verified this session” | still **INSUFFICIENT_EVIDENCE** for a new number |

OPEN. This pass adds no new timing.

## (b) Wi-Fi 5 GHz up but local writes not faster

| side | claim | evidence | this pass |
|---|---|---|---|
| A | Radio on 5 GHz | live `netsh wlan show interfaces` 2026-08-18T03:07+10: Band **5 GHz**, Channel **36**, Radio type **802.11ac**, State connected. `Get-NetAdapter` Wi-Fi **Up** (LinkSpeed 195 Mbps at adapter snapshot). | VERIFIED live |
| B | Local F: writes did not get faster after the radio change | `NETWORK-PATH-5GHZ-2026-08-18.md` (40–73s class) | write-bench **not** repeated |
| C | Ethernet still unplugged | live `Get-NetAdapter`: Ethernet **Disconnected**, 0 bps, Realtek PCIe GbE | VERIFIED live |

OPEN as a causal claim (radio vs disk). Adapter facts are live.

## (c) SSH OK vs official key missing

| side | claim | evidence | this pass |
|---|---|---|---|
| A | Official key `$env:USERPROFILE\.ssh\octopus_key` **MISSING** | `Test-Path` both `octopus_key` and `octopus_key.pub` = False. SSH dir listing (names only): `config`, `id_ed25519`, `id_ed25519.pub`, `known_hosts`, `known_hosts.old`, `piggybank_id_ed25519`, `piggybank_id_ed25519.pub`. No `octopus_key`. | **SSH_OFFICIAL_KEY_MISSING = MISSING**. No private key material read. |
| B | Fallback `id_ed25519` exists; prior agent claimed SSH to `.138` exit 0 | live `id_ed25519` + `.pub` exist; `ssh-keygen -l -f id_ed25519.pub` → `256 SHA256:IrKVkKK9SwcdlmrtAiLiUakNQFX8Fb88zuNUBmJIUwg armin@DESKTOP-KA9RFN5 (ED25519)` | fingerprint VERIFIED. SSH session to `.138` **not** executed this pass → **INSUFFICIENT_EVIDENCE** for “SSH OK” as a live hop |

Official status is MISSING regardless of fallback. `authorized_keys` not edited.

## (d) Sensorium charter STAGED vs CHARTER_ACTIVATED seq 26

| side | claim | evidence |
|---|---|---|
| A | Charter v2 **STAGED, NOT active**; laptop-first gate | `06-EVIDENCE/sensorium-d14-verify-2026-08-18/PENDING-CHARTER-V2.md` (still on disk); `00 - Inbox/2026-08-18 NOTE — verification doctrine activation order (laptop first).md` |
| B | Owner delivered v2; **CHARTER_ACTIVATED** seq 26 | `06-EVIDENCE/sensorium-d14-verify-2026-08-18/CHANGELOG.jsonl` seq 26; `msg-evidence-162739.json` changelog_tail includes seq 26 `CHARTER_ACTIVATED`; Inbox `00 - Inbox/2026-08-18 SENSORIUM CHARTER v2 ACTIVE — packet format + .180 separation.md` |
| C | Copy named `msg-evidence-latest.json` changelog_tail **stops at seq 25** (no seq 26) | `06-EVIDENCE/sensorium-d14-verify-2026-08-18/msg-evidence-latest.json` |

Live `.182` not queried this pass. Vault copies disagree. OPEN.

## (e) GAP-001 id on board vs laptop

| side | claim | evidence |
|---|---|---|
| Board | GAP-001 closed at next signed checkpoint; payload `readiness: READY` | `sensorium-d14-verify-2026-08-18/OWNER-DECISIONS.md` D5; `msg-evidence-latest.json` / `msg-evidence-162739.json` `gaps.GAP-001` |
| Laptop verifier doctrine | WAVE0 + GITWRITE-FAILED stay until GAP-001 **formally closed** | `00 - Inbox/2026-08-18 NOTE — verification doctrine activation order (laptop first).md`; `agent-prompts/MEGAPROMPT-VERIFIER-00-SHARED-CONTRACT-2026-08-18.md` |
| Other homonym | Telegram redesign GAP-001 = `conversation_metadata_store_missing` | `agent-prompts/TELEGRAM-REDESIGN-MEGAPROMPT.md` |

Same id string, at least two ledgers. Do not merge meanings.

## Other standing reds (not contradictions; listed so they are not “closed” by this file)

- `01a00d3d-2b7f-7362-b283-275723a85b24` state=`dispatched` in `_ops/state/board_cp/commands.sqlite` (ids only; not acked).
- EQUIP-G2 + JOB-RESEARCH patches present in `00 - Inbox/`; distinctive strings absent from `4d_system/brain/automation.py` and `daemon.py`.
- Tag `pre-deploy-2026-07-25` local `dab81a828c9546ad7e36141b6f3a23858e6ce0a8` ≠ `E:/germline/vault.git` `9c49f17490ab466d9fe7a88458b0283e7b75cf39`. Dry-run reject verified.
- `GITWRITE-FAILED.flag` still present (not cleared).
- A2-001 remains `UNKNOWN_CANONICAL` (no single SoT path).
- `.180` lab not started as production (local artifacts absent; remote process state not probed).
