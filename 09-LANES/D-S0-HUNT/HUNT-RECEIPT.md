---
type: hunt-receipt
lane: D-S0-HUNT
measured_at: 2026-09-03T19:41:36+10:00
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
ip_source: Get-NetIPAddress Wi-Fi
scope: this_host_only
claim_type: observation
---

# D-S0-HUNT increment — ofn-node / test_repair_api / DET (2026-09-03 19:41+10)

Lane: **D-S0-HUNT**. Local filesystem only. No clone, fetch, pull, unzip-extract, flag flip, email, merge, SSH write.

Host: `DESKTOP-KA9RFN5` / Wi-Fi `192.168.0.191` (`Get-NetIPAddress`). Absence here = `body_not_on_this_host`, not system-wide `body_missing`.

## Verdict (this host)

| target | this_host_only |
|---|---|
| `tests/test_repair_api.py` | **absent** on every tree opened (including live `F:\ofn-node`) |
| live ofn-node clone | **present** `F:\ofn-node` HEAD `34e63a04c5df4a948361f48b306e2a3f5188d42f` branch `fix/demand-harvest` |
| DET draft | **present** on several ofn-node worktrees; **absent** on `F:\backup\docs\lanes\ECONOMIC-LEARNING\` (not copied) |

## 1. Re-verify of prior eight roots

Dir mtimes from `Get-Item` this session. HEADs from `git rev-parse` this session. `repair` = `Test-Path <root>\tests\test_repair_api.py`.

| root | dir mtime | HEAD / note | repair | DET `docs/lanes/ECONOMIC-LEARNING/DRAFT-REPLY-det-nsw-2026-09-02.md` |
|---|---|---|---|---|
| `C:\Users\Armin\.cursor\projects\f-backup\w1-spine` | 2026-09-02T00:31:17+10:00 | `feat/w1-spine-20260902` `3a7ca66829a66f9449fb9dc23a836722e0bedab6` | absent | absent (filename recurse) |
| `...\w1-money` | 2026-09-02T00:56:53+10:00 | `feat/w1-money-20260902` `2d6f95bd2f29f5695e5cc083b3c945b35d2ec8a0` | absent | absent |
| `...\w1-scale` | 2026-09-02T01:39:46+10:00 | `feat/w1-scale-20260902-b` `55cd1b39c77e96cf12f7e634c244268fc9b8f40b` | absent | absent |
| `...\w1-free` | 2026-09-02T01:36:10+10:00 | `feat/w1-free-20260902` `55cd1b39c77e96cf12f7e634c244268fc9b8f40b` | absent | absent |
| `F:\wt-self-awareness` | 2026-09-02T21:24:27+10:00 | detached `00e9b9150e55e960880a5d6907bafb20a85184b3` | absent | **present** 2779 B sha256 `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` mtime 2026-09-02T21:25:16+10:00 |
| `C:\Users\Armin\ofn` | 2026-09-02T23:20:39+10:00 | no `.git`; children = `data\` only | absent | absent |
| `F:\backup\_github-export\ofn-node` | 2026-08-30T19:24:00+10:00 | `export/octopus-surgery-20260830` `526613e2483f8cfe572cfd3f96ed57766690bb02` | absent | absent (filename recurse) |
| `F:\backup\_github-export\ofn-node-20260830-193052` | 2026-08-31T10:08:44+10:00 | `hygiene/audit-20260831` `14357e7affa3b4dbd574c21bddc88f54a2060733` | absent | absent |
| `F:\backup` | 2026-09-03T01:04:21+10:00 | `rescue/octopus-live-tree-20260821` `8d8be71f1afb697ed1c80c40435c1e404be73368` | absent (`F:\backup\tests\test_repair_api.py`) | absent (`F:\backup\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md`) |

Prior-session HEADs for those eight match this session (same SHAs as `09-LANES/D-S0-HUNT/HUNT-RECEIPT.md` previous body).

## 2. NEW ofn-node tree (prior hunt missed)

`F:\ofn-node` exists. Dir mtime 2026-09-03T15:36:55 (from `F:\` listing). `.git` present.

- `git -C F:\ofn-node rev-parse --abbrev-ref HEAD` → `fix/demand-harvest`
- `git -C F:\ofn-node rev-parse HEAD` → `34e63a04c5df4a948361f48b306e2a3f5188d42f`
- `git status -sb` first line: `## fix/demand-harvest...origin/fix/demand-harvest [behind 2]`
  - `[behind 2]` is **local remote-tracking state already on disk**. This session did **not** fetch.
- remotes (`git remote -v`):
  - `origin` `https://github.com/ari-OCTOPUS/ofn-node.git`
  - `fork` `https://github.com/ari322/ofn-node.git`
  - `board138` `ari@192.168.0.138:/home/ari/ofn`
- `Test-Path F:\ofn-node\tests\test_repair_api.py` → False
- `Get-ChildItem F:\ofn-node\tests -File -Filter test_*.py` count = **155** (source: that command this session)
- `rg`/`Select-String` `repair_api|test_repair_api` under `F:\ofn-node\tests`, `ofn`, `docs`, `tools` → **zero paths**
- close names present (bytes + mtime from `Get-ChildItem F:\ofn-node\tests`):
  - `test_doctor_lane_backlog.py` 2472 B 2026-09-02T23:19:01
  - `test_doctor_lane_cli.py` 3327 B 2026-09-02T23:19:01
  - `test_doctor_lane_contract_map.py` 9461 B 2026-09-02T23:19:01
  - `test_doctor_lane_destiny.py` 4581 B 2026-09-02T23:19:01
  - `test_doctor_lane_round.py` 6456 B 2026-09-02T23:19:01
- no file matching `test_repair*.py` or `*repair_api*` under `F:\ofn-node` (recurse excluding `.git`/`__pycache__`)
- DET present (see §4) same sha256 as prior `aa98fff…`
- `F:\ofn-node\ofn\agents\imap_listener.py` **present** 15875 B mtime 2026-09-02T00:34:41 (listed `??` in `git status -sb`). Prior hunt marked imap_listener absent in the eight roots; this path is new.

## 3. ofn-node worktrees (`git -C F:\ofn-node worktree list`)

| path | HEAD (full where measured) | branch / state | `tests/test_repair_api.py` | DET draft |
|---|---|---|---|---|
| `F:\ofn-node` | `34e63a04c5df4a948361f48b306e2a3f5188d42f` | `fix/demand-harvest` | absent | present `aa98fff…` 2779 B |
| `C:\Users\Armin\AppData\Local\Temp\ofn-verify` | `60dce9617fcadec1e1cf2781aabc481121a98c17` | detached | absent | present `aa98fff…` 2779 B mtime 2026-09-03T15:55:36 |
| `F:\wt-buysw-v03` | `2aac8f3312e9f144f999c4023a915143a65f1a16` | `fix/buysw-bridge-v03` | absent | present `aa98fff…` 2779 B mtime 2026-09-03T12:15:10 |
| `F:\wt-docs` | `7337ddd9bcb5c337dc987b89ab6f995c23c7fe51` | `docs/octopus-os-pack-20260902` | absent | absent |
| `F:\wt-dsl` | `bbaac4c840c94fdf39d5158cbe0e9959f7d0904c` | `chore/dead-source-labels-20260902` status `-sb` `[behind 12]` (local refs; no fetch) | absent | absent |
| `F:\wt-economic-learning` | `45dd9133dc3677630b9a3606fc7a41f00f5458e0` | detached | absent | **present different hash** `d7aeb3ebc2cddcb7c01116c01e1a64d7843893a49a7ecd2e44c0ce15c07bda4b` 2731 B mtime 2026-09-02T20:54:33+10:00 |
| `F:\wt-halt` | `2ab1fe7ce0b875f3629ebd03ce13d638521457c1` | `feat/halt-run-gate-chaos-20260902` | absent | absent |
| `F:\wt-incidents` | `a753505ddc12760555fd47f5448717eb604e0ad1` | `docs/octopus-os-incidents-20260902` | absent | absent |
| `F:\wt-landing` | `c41df9372f78c81596fdcc4fc4427bbdf0736f74` | `landing/release-p0-20260902` | absent | absent |
| `F:\wt-p1` | `3d52d7d1aabc35a20f97ff23d9f6cabbc2ff8a8a` | `feat/p1-envelope-runstore-20260902` status `-sb` `[behind 9]` (local refs; no fetch) | absent | absent |
| `F:\wt-p37` | `0cf684d50b0ca1d746c23a43aedc02084642624d` | `fix/p37-final` | absent | absent |
| `F:\wt-rev` | `81f154f974e4c5a522c070540fd93de840e5222e` | `feat/campaign-envelope-20260902` | absent | absent |
| `F:\wt-self-awareness` | `00e9b9150e55e960880a5d6907bafb20a85184b3` | detached | absent | present `aa98fff…` |
| `F:\wt-self-completing-doctor` | `44129564c46a42ba7a21d2886d2eeb6a65b4c119` | `lane/self-completing-doctor` | absent | absent |
| `F:\wt-t04` | `b10f23f1545c30b4f80953b03f96a2a5ee1e5832` | `t04-gap-scan-tmp` | absent | absent |
| `F:\wt-waiver` | `a5f7a6c7067c99016b103d1d935100a57b06ae3a` | `feat/waiver-send-gate-test-20260902` | absent | absent |

Empty directories on `F:\` (exist, child count **0** from `Get-ChildItem`, no `.git`): `F:\wt-gate` mtime 2026-09-03T02:10:55, `F:\wt-gov6` 2026-09-03T00:44:13, `F:\wt-110v2` 2026-09-03T01:35:16, `F:\wt-sm` 2026-09-03T01:16:17. Status: empty.

## 4. DET drafts (hashes this session; not copied into vault canonical path)

| path | bytes | mtime | sha256 | newlines (`ReadAllBytes`) |
|---|---|---|---|---|
| `F:\wt-self-awareness\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | 2779 | 2026-09-02T21:25:16+10:00 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | crlf=48 lf_only=0 |
| `F:\ofn-node\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | 2779 | 2026-09-02T23:18:58+10:00 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | crlf=48 lf_only=0 |
| `F:\wt-buysw-v03\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | 2779 | 2026-09-03T12:15:10 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | (hash match; newlines not re-counted) |
| `C:\Users\Armin\AppData\Local\Temp\ofn-verify\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | 2779 | 2026-09-03T15:55:36 | `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` | (hash match) |
| `F:\wt-economic-learning\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | 2731 | 2026-09-02T20:54:33+10:00 | `d7aeb3ebc2cddcb7c01116c01e1a64d7843893a49a7ecd2e44c0ce15c07bda4b` | crlf=0 lf_only=48 |
| `F:\backup\docs\lanes\ECONOMIC-LEARNING\DRAFT-REPLY-det-nsw-2026-09-02.md` | — | — | — | status: absent |

Siblings under `docs/lanes/ECONOMIC-LEARNING` (hashed this session):

| tree | file | bytes | sha256 |
|---|---|---|---|
| `F:\wt-self-awareness` | `VERIFIED-ECONOMIC-STATES-DESIGN.md` | 2792 | `f415c3a2a2f57d117f548bd3e452c261b0703dc85c01255a8ae3607ff8d6fe5f` |
| `F:\ofn-node` | `VERIFIED-ECONOMIC-STATES-DESIGN.md` | 2792 | `f415c3a2a2f57d117f548bd3e452c261b0703dc85c01255a8ae3607ff8d6fe5f` |
| `F:\wt-economic-learning` | `VERIFIED-ECONOMIC-STATES-DESIGN.md` | 2739 | `ac3bf90f6375c8a9ec79a7b4394893477dc883c7d25b1f9452cb6a3c3974c743` |

`F:\wt-economic-learning\09-LANES\ECONOMIC-LEARNING\DoD.md` 3042 B sha256 `7ba911122658bb600fd1d3a0a3bccf07b80178086fa2bc2fcd85c9625de90954` mtime 2026-09-02T20:37:33.

`F:\ofn-node\09-LANES\ECONOMIC-LEARNING\`: `DoD.md` 3093 B mtime 2026-09-02T23:18:57 + `runs/2026-09-02/` (`economic-learning-ledger.jsonl` 7759 B, `evidence-paint-l5-001.json` 4677 B, `run-summary.json` 7285 B). Sizes from `Get-ChildItem`; hashes of those run files **unverified** (not hashed this session).

Visible draft body (both DET hashes): placeholders `[LEGAL BUSINESS NAME]` `[ABN]` `[NAME]` `[PHONE]` `[EMAIL]` `$[X]m`. Not copied into `F:\backup\docs\lanes\`.

## 5. Other roots checked this increment

### `F:\backup` git worktrees (`git -C F:\backup worktree list --porcelain`)

Additional vs prior hunt: `wt-acct-20260831` HEAD `1fd573e07b71010205dfd861dc96e6b109babab2` branch `docs/accounting-recovery-34-20260831`; `wt-s2b-claim` HEAD `6d815d707b364de37f043a1346a47c195e8b330c` branch `feat/s2b-claim-record-20260901`; many `F:\backup\.claude\worktrees\*` (vault branches, not ofn-node remotes); `F:\backup-island` HEAD `7bbec492f0890dbe509444d2ddc392eae5c96158`; `F:\octopus-campaign-20260830\wt-final` HEAD `a70200eeefb65ef50077693b98175048540f910b`. Filename recurse on island + wt-final + acct + s2b-claim: no `test_repair*` / `repair_api`. `Test-Path …\tests\test_repair_api.py` False on island, wt-final, acct, s2b-claim, w1-spine.

Claude worktrees HEADs from porcelain (short): `core-live-cl01` `1db88945` `cl01/p2-gate`; `fugu-ultra-remediation-d10abc` `803ce704`; `great-spence-d84352` `f9f294bd`; `hybrid-control-plane-megaprompt-bd4b21` `9ffa075c`; `octopus-docs-sync-20260830` `45c9f20b`; `octopus-docs-sync-20260830-200415` `56ba6f8f`; `octopus-p0-fixes-418a9a` detached `8b7e6e83`; `octopus-reality-20260830-160703` `bf6f45ec`; `organism-alive-69a5db` `e80acf2a`; `sul-brain` `1a6b433b`; `sul-heart` `0dabb288`; `sul-memory` `f314cb0e`. These are `F:\backup` worktrees, not `origin` ofn-node.

### `_github-export` third tree (prior missed)

`F:\backup\_github-export\ofn-node-pr6-base-c1969bc` detached `c1969bce5384f3371b916470299c991627c3d63c` remote `origin https://github.com/ari-OCTOPUS/ofn-node.git`. `test_repair_api.py` absent. DET draft absent.

### `C:\Users\Armin\ofn`

Not a git clone. Top = `data\` only (mtime 2026-09-02T23:20). `data` children names only: `state`. No secrets read.

### Downloads / Documents / Desktop

- `C:\Users\Armin\Downloads`: many `OCTOPUS*` / `ofn-*` **files** (prompts, zips). No directory named `ofn-node`.
- Zip **listing only** (no extract) of `ofn-*.zip`: `ofn-mining-kernel.zip`, `ofn-v0.2.0.zip` … `ofn-v0.8.0.zip` (sizes 24625 / 52239 / 66573 / 80594 / 121219 / 163574 B; mtimes 2026-08-04). Zero zip entries matching `repair_api|test_repair`.
- `C:\Users\Armin\Documents\OCTOPUS-ATTESTATIONS` exists (dir mtime 2026-09-02T09:58:24). Not recursed for repair_api.
- Desktop: `octopus-byte-manifest-20260903.csv`, `OCTOPUS.md` — not clones.
- `C:\Users\Armin\source`, `\code`, `\repos`, `\Projects`: status: absent.

### Cursor project extras

`C:\Users\Armin\.cursor\projects\f-backup\w1-free-stage` exists, no `.git`, no filename hit.

## 6. Contradictions (`resolution: null`, `status: open`)

1. **DET byte-identity:** sha256 `aa98fff194fabbce35c6fd1bddcef2110f56f14fa4e70353098d8fdaf277ed39` (2779 B, crlf=48) vs `d7aeb3ebc2cddcb7c01116c01e1a64d7843893a49a7ecd2e44c0ce15c07bda4b` (2731 B, lf_only=48). Visible text both still placeholder. `resolution: null`. `status: open`.
2. **VERIFIED-ECONOMIC-STATES-DESIGN.md:** `f415c3a2…d6fe5f` 2792 B (`wt-self-awareness`, `F:\ofn-node`) vs `ac3bf90f…974c743` 2739 B (`wt-economic-learning`). `resolution: null`. `status: open`.
3. **Vault ruling letter vs draft:** `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` is a filled-letter receipt (prior D). Drafts above keep placeholders. `resolution: null`. `status: open`.
4. **Lane matrix vs this folder:** `F:\backup\09-LANES\LANE-MATRIX.csv` lists L0–L9 only (no `D-S0-HUNT` row). `09-LANES/D-S0-HUNT/SCOPE.md` claims owns `09-LANES/D-S0-HUNT/`. `resolution: null`. `status: open`. This session wrote only the SCOPE-owned folder + optional HANDOFF pin.
5. **Lane A vs disk:** A reported DET absent on `F:\backup` and `C:\Users\Armin\ofn` — still true. DET **is** on `F:\ofn-node` and several `F:\wt-*` (this host). Not a number clash; path-scope difference.

## 7. Searched vs skipped

**Searched (this increment):** prior eight roots; `F:\ofn-node` + its `worktree list`; `F:\backup` worktree porcelain; `_github-export` three children; `C:\Users\Armin\ofn`; Downloads top-level `ofn*`/`octopus*` + zip name-list; Documents top-level `ofn*`; Desktop `ofn|octopus` names; `F:\` top-level `ofn|wt-|octopus|backup`; `C:\Users\Armin` top-level `ofn*`; exact `Test-Path` for `tests\test_repair_api.py` on listed trees.

**Skipped (cap):** recursive scan of whole `F:\`, whole `C:\`, `F:\backup-Archive`, `F:\backup-SAFE-2026-07-19`, `F:\backup_snapshots`, `F:\backup-snapshot-20260723-121256`, `F:\backup-deploy-lab`, `F:\octopus-phase0-*`, `F:\OCTOPUS-SURVIVAL-BACKUP-2026-08-19`, `F:\octopus-test-runs`, `F:\octopus-untracked-safety-2026-07-22`, `F:\octopus-wire`, `F:\octopus-governance-final`, `F:\_octopus-*`, extracting any zip, `F:\backup\.claude\worktrees\*` deep filename recurse, `Documents\OCTOPUS-ATTESTATIONS` recurse, secret files (`.env`, credentials, keys), any `git fetch`/`clone`.

No path returned `permission_denied` this session.

## 8. Not done (still closed)

- No git fetch/clone to resolve `[behind 2]` on `F:\ofn-node`.
- No pytest of missing `test_repair_api.py`.
- No copy of DET into `F:\backup\docs\lanes\`.
- No GitHub/network confirmation that origin `main` contains `test_repair_api.py`.
