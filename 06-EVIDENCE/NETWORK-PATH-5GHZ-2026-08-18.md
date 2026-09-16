---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, network, wifi, ssh, handshake]
author: "laptop agent — WAVE0 network-path + SSH .138 + envelope cycle-2"
---

# Network path 5 GHz + SSH .138 (2026-08-18 ~02:45 +10)

Host `DESKTOP-KA9RFN5` (192.168.0.191). Sidecar `_ops/handshake/` — **not** TCB.
schema `octopus-handshake-envelope/1`. autonomy_delta=0. WAVE0_OBSERVE_ONLY.
Timezone: OS local AEST **UTC+10** (megaprompt UTC+11 was wrong).

## Claim

Wi-Fi switched `Tenda_EBBAA0` (2.4 GHz n ch11) → `Tenda_EBBAA0_5G` (5 GHz ac ch36);
Ethernet stayed Disconnected; local 200×4KB write-bench 53452.7ms → 73387.0ms
(recheck 40411.9ms, size-verified); `octopus_key` absent; exact ssh command
exit 0 via fallback; `id_ed25519` IdentitiesOnly also OK; GITWRITE-FAILED still held.

## Before / after

| item | before | after |
|---|---|---|
| SSID | Tenda_EBBAA0 | Tenda_EBBAA0_5G |
| band / radio / ch | 2.4 GHz 802.11n ch11 | 5 GHz 802.11ac ch36 |
| Ethernet | Disconnected, 0 bps | Disconnected, 0 bps |
| Wi-Fi LinkSpeed | 144.4 Mbps | 260 Mbps (later 162–390 Mbps, radio varies) |
| IPv4 | 192.168.0.191/24 | 192.168.0.191/24 |
| 200×4KB local write | **53452.7 ms** (baseline this session) | 73387.0 ms; recheck **40411.9 ms** |

Ethernet had no cable. Agent cannot plug one. 5 GHz used.

No saved profile named `Tenda_EBBAA0_5G`. First `netsh wlan connect name=Tenda_EBBAA0_5G` → `There is no profile "Tenda_EBBAA0_5G" assigned to the specified interface.` (exit 1). Second try with 2.4 GHz profile + 5 GHz SSID → `SSID "Tenda_EBBAA0_5G" does not exist in profile "Tenda_EBBAA0".` (exit 1). Then a Current User profile was cloned in `%TEMP%` from `Tenda_EBBAA0` (PSK never written into vault/notes); XML deleted after add. Connect succeeded.

GITWRITE-FAILED.flag **not** cleared. `.138` `cache=none` **not** touched.

## Write bench method

200 files × 4096 bytes under `F:\backup\_ops\state\handshake\netbench-*`, each
`mkstemp` + `write` + `flush` + `fsync` + `os.replace` + re-read size==4096, then delete.
Zero-byte was **not** observed. Owner-stated prior **1080ms** was not reproduced
(Uncertainty: owner-stated prior, not re-verified this session). Local F: writes
did not get faster from the radio change.

## Envelope files (verifier hashes these JSON files, not this paragraph)

| receiver | bytes | sha256 | path |
|---|---|---|---|
| continuity `agent://octopus/continuity-board/main` | 9619 | `e9fad1de21bf2ca72a689adfb59aee0feaa60c2e0c4898276f99a5622db27d3f` | `06-EVIDENCE/envelopes/cycle-02-continuity.json` |
| sensorium `agent://octopus/sensorium-board/main` | 9618 | `2cc65012332051c47472cac63140fdddebc5b22f9219aea24c50b5326927f8fd` | `06-EVIDENCE/envelopes/cycle-02-sensorium.json` |
| feet `agent://octopus/feet-board/main` | 9613 | `ce0e588b567a650ad275fd72e6aaec4dc20dbd6eefebd8c1bc312c0e90b34819` | `06-EVIDENCE/envelopes/cycle-02-feet.json` |

Companion `*.json.sha256` sits next to each file (hash is **not** inside the JSON).
Live copies: `_ops/state/handshake/` (gitignored).

## Raw — netsh BEFORE (2.4 GHz, first live capture)

```
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    GUID                   : dae9b794-6711-4b4f-bb99-bb4cc90bac39
    Physical address       : 70:9c:d1:e0:30:4e
    Interface type         : Primary
    State                  : connected
    SSID                   : Tenda_EBBAA0
    AP BSSID               : 08:40:f3:eb:ba:a4
    Band                   : 2.4 GHz
    Channel                : 11
    Connected Akm-cipher   : [ akm = 00-0f-ac:02, cipher =  00-0f-ac:04 ]
    Network type           : Infrastructure
    Radio type             : 802.11n
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Auto Connect
    Receive rate (Mbps)    : 43.3
    Transmit rate (Mbps)   : 115.6
    Signal                 : 81%
    Rssi                   : -62
    Profile                : Tenda_EBBAA0
```

Adapters at before: Wi-Fi Up 144.4 Mbps; Ethernet Disconnected 0 bps.

Live scan (same window): `Tenda_EBBAA0_5G` visible 5 GHz ac ch36 signal 65% util 0%;
`Tenda_EBBAA0` 2.4 GHz n ch11 signal 82% util 1% (owner-stated 99% util not seen this session).

Saved WLAN profiles had **no** `Tenda_EBBAA0_5G` until this session cloned it.

## Raw — netsh AFTER (first connected-5G capture)

```
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    GUID                   : dae9b794-6711-4b4f-bb99-bb4cc90bac39
    Physical address       : 70:9c:d1:e0:30:4e
    Interface type         : Primary
    State                  : connected
    SSID                   : Tenda_EBBAA0_5G
    AP BSSID               : 08:40:f3:eb:ba:a8
    Band                   : 5 GHz
    Channel                : 36
    Connected Akm-cipher   : [ akm = 00-0f-ac:02, cipher =  00-0f-ac:04 ]
    Network type           : Infrastructure
    Radio type             : 802.11ac
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Auto Connect
    Receive rate (Mbps)    : 526.5
    Transmit rate (Mbps)   : 260
    Signal                 : 80%
    Rssi                   : -64
    Profile                : Tenda_EBBAA0_5G
```

Double-check (no --quiet, before CHANGELOG): still `Tenda_EBBAA0_5G`, 5 GHz ac ch36,
RX 260 / TX 292.5 Mbps, signal 80%. Ethernet still Disconnected.

Envelope emit later (02:45+10) still on 5G (RX 390 / TX 162 — radio rate varies).

## Raw — ping after switch

```
ping -n 4 192.168.0.182
Reply ... time=2ms / 1ms / 2ms / 2ms   Lost=0   Average=1ms   exit=0

ping -n 4 192.168.0.138
Reply ... time=2ms / 2ms / 3ms / 3ms   Lost=0   Average=2ms   exit=0
```

## Raw — write bench

```
BEFORE_MS=53452.7
AFTER_MS=73387.0
AFTER_RECHECK_MS=40411.9
N=200 BYTES_EACH=4096 TOTAL=819200
VERIFIED_OK=True ZERO_BYTE=false
```

## Raw — SSH .138

Specified key path `$env:USERPROFILE\.ssh\octopus_key` — **file does not exist**.

`.ssh` filenames (not contents): `config`, `id_ed25519`, `id_ed25519.pub`,
`known_hosts`, `known_hosts.old`, `piggybank_id_ed25519`, `piggybank_id_ed25519.pub`.

Exact owner command:

```
ssh -o BatchMode=yes -o ConnectTimeout=8 -i $env:USERPROFILE\.ssh\octopus_key ari@192.168.0.138 "echo OK"
```

```
stderr: Warning: Identity file C:\Users\Armin\.ssh\octopus_key not accessible: No such file or directory.
stdout: OK
exit: 0
```

Fallback (octopus_key missing — different key, labeled Uncertainty):

```
ssh -o BatchMode=yes -o ConnectTimeout=8 -o IdentitiesOnly=yes -i $env:USERPROFILE\.ssh\id_ed25519 ari@192.168.0.138 "echo OK"
stdout: OK
stderr: (empty)
exit: 0
```

`authorized_keys` / `sshd_config` not modified.

## Raw — GITWRITE flag (still present, not cleared)

```
Get-Content F:\backup\_ops\backup\GITWRITE-FAILED.flag
GITWRITE-FAILED 2026-08-16_035024 : git-write lock TIMEOUT after 40 attempts on F:\backup\_ops\backup\gitwrite.lock
bytes=120  still present
```

## Reproduction (run on laptop; do not take this note as proof)

```
netsh wlan show interfaces
netsh wlan show profiles
Get-NetAdapter -Name Ethernet,Wi-Fi | Format-List Name,Status,LinkSpeed
ping -n 4 192.168.0.182
ping -n 4 192.168.0.138
ssh -o BatchMode=yes -o ConnectTimeout=8 -i $env:USERPROFILE\.ssh\octopus_key ari@192.168.0.138 "echo OK"
Test-Path F:\backup\_ops\backup\GITWRITE-FAILED.flag
python -X utf8 F:\backup\_ops\handshake\emit_cycle02.py
```

Hermetic tests (not the live path):

```
python -X utf8 F:\backup\_ops\tests\test_evidence_envelope_handshake.py
```

6/6 PASS. Green tests do not prove the radio path and do not clear GITWRITE-FAILED.

## Uncertainty

- Sydney August = AEST UTC+10; megaprompt UTC+11 was wrong.
- Owner-stated write-bench 1080ms: prior, not re-verified this session.
- Owner-stated 2.4 GHz channel util 99%: live scan this session showed ~1%.
- Exact ssh command exit 0 is **not** proof that `octopus_key` works; that file is missing; OpenSSH fell back.
- Write-bench after/recheck variance (73s vs 40s) is load, not zero-byte death.

## Escalation / owner-pending (unchanged)

If reproduction disagrees: ≤3 retries, then owner.
Do not delete GITWRITE-FAILED.flag. Do not ack `01a00d3d`. Do not set cache=none on .138.

Still owner-pending: `01a00d3d` · TCB ceremony (EQUIP-G2 + JOB-RESEARCH) · tag `pre-deploy-2026-07-25` · GITWRITE flag held.
