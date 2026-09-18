---
type: architecture-note
lane: D-S0-HUNT
measured_at: 2026-09-03T20:10:29+10:00
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
ip_source: Get-NetIPAddress Wi-Fi
scope: this_host_only
claim_type: observation
owner_decision: "ا) معماری ofn-node محلی — بدون fetch"
accounting: not_done
---

# OFN local architecture — `F:\ofn-node` (this host only)

Lane: **D-S0-HUNT**. Files on this laptop. No fetch, no pull, no clone, no unzip, no server start, no flag enable, no accounting.

This host is `DESKTOP-KA9RFN5` / Wi-Fi `192.168.0.191` (`hostname` + `Get-NetIPAddress` this session). Not board 180. Absence here = `body_not_on_this_host`, not system-wide `body_missing`.

Owner also said books are incomplete. This note maps modules only. No money figures. `$306.90` / payment counts are not treated as complete.

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: this_host_only
  scope: this_host_only
  claim_type: observation
```

## 0. Git identity (re-verified; no fetch)

| field | value | source |
|---|---|---|
| branch | `fix/demand-harvest` | `git -C F:\ofn-node rev-parse --abbrev-ref HEAD` this session |
| HEAD | `34e63a04c5df4a948361f48b306e2a3f5188d42f` | `git rev-parse HEAD` this session |
| status first line | `## fix/demand-harvest...origin/fix/demand-harvest [behind 2]` | `git status -sb` this session |
| remotes | `origin` `https://github.com/ari-OCTOPUS/ofn-node.git` · `fork` `https://github.com/ari322/ofn-node.git` · `board138` `ari@192.168.0.138:/home/ari/ofn` | `git remote -v` this session |
| behind-2 | `status: local_behind_remote_unverified` | local remote-tracking pointer only; no fetch |

`[behind 2]` is git’s comparison of this HEAD to the **already-on-disk** `origin/fix/demand-harvest` pointer. This session did not fetch. The two remote commits are **not known**. Do not treat the local tracking SHA as live origin.

## 1. Top-level layout — what each tree is for

Source of intent: `F:\ofn-node\README.md` (frontmatter `updated: 2026-08-07`) plus `Get-ChildItem` this session. README’s drawn tree is older than the directories now on disk.

### 1.1 `ofn/` — the package

`F:\ofn-node\ofn\__init__.py`: “OFN — a multi-tenant field node. One kernel decides; several business packs configure; one human rules.” `__version__` in that file = `0.1.0` (141 B).

README title says **v0.8.0**. Those two version strings disagree.

| value | source | status |
|---|---|---|
| `0.8.0` | `F:\ofn-node\README.md` line 7 | FILE_VERIFIED |
| `0.1.0` | `F:\ofn-node\ofn\__init__.py` | FILE_VERIFIED |
| resolution | null | open |

Subdirectories actually present (`Get-ChildItem F:\ofn-node\ofn -Directory` this session):

| dir | role (from module doc / README) |
|---|---|
| `ofn/kernel/` | stdlib, no I/O, no clock. `admit()` in `gates.py` is the choke-point. README §1. |
| `ofn/adapters/` | SQLite stores, HTTP API, outbox, router, boot. README §1. |
| `ofn/doctor/` | Lane LB self-completing doctor: read-only diagnosis, prescriptions, backlog, destiny. `ofn/doctor/__init__.py`. **Not** a repair HTTP API. |
| `ofn/learning/` | Shadow-only economic learning. “never sends, never authorizes, never merges.” `ofn/learning/__init__.py`. |
| `ofn/agents/` | Side processes: harvest, IMAP poll, quotes, heartbeat. Not imported by `ofn.run`. |
| `ofn/budget/` | Present on disk (listed `??` in `git status -sb`). `imap_listener.py` inserts it on `sys.path` and imports `opslib`. |
| `ofn/helpers/` | `brainport.py` (present in glob this hunt). |

Top-level package files (`Get-ChildItem F:\ofn-node\ofn -File -Filter *.py`):

| file | bytes | role |
|---|---|---|
| `run.py` | 28701 | Service: boot, **four** loopback HTTP listeners, watchdog, worker. `main()` at line 577. |
| `node.py` | 215938 | Wiring: answer → fact → ledger. README §1. |
| `worker.py` | 15749 | Slow-brain queue. README: only place the slow model may run. |
| `config.py` | 13706 | Env → `Config`. Default ports `ziman=8791` `lead=8792` `studio=8793` `owner=8794` (`config.py` line 283). |
| `marketing_run.py` | 4128 | Builds the same node as `ofn.run`, then a marketing cycle. File docstring. |
| `preflight.py` / `backup_job.py` / `restore_job.py` / `assistant_update.py` | 2823 / 1942 / 1024 / 2469 | Install / backup / restore / assistant helpers. |

`ofn.run` does **not** import `ofn.agents` or `ofn.doctor` (`Select-String` on `F:\ofn-node\ofn\run.py` this session: zero matches).

### 1.2 `tests/`

| claim | value | source |
|---|---|---|
| `test_*.py` file count | **155** | `(Get-ChildItem F:\ofn-node\tests -File -Filter test_*.py).Count` this session |
| README tree | “`tests/` ۱۷ فایل تست” | `F:\ofn-node\README.md` §1 |
| INDEX instruction | do not write a test number; use `tools/repo_baseline.py --tests` | `F:\ofn-node\INDEX.md` lines 24–29 |
| `repo_baseline.py --tests` | **not run** this session | — |
| resolution README-17 vs 155 | null | open |

Subdirs under `tests/`: `fixtures\`, `__pycache__\` only (`Get-ChildItem F:\ofn-node\tests -Directory`).

`tests/test_repair_api.py`: `Test-Path` → **False**. Recurse for `repair_api|test_repair` excluding `.git`/`__pycache__` → **zero files**.

Closest doctor tests (same `Get-ChildItem` as prior hunt; sizes re-read):

| file | bytes | mtime |
|---|---|---|
| `test_doctor_lane_backlog.py` | 2472 | 2026-09-02T23:19:01 |
| `test_doctor_lane_cli.py` | 3327 | 2026-09-02T23:19:01 |
| `test_doctor_lane_contract_map.py` | 9461 | 2026-09-02T23:19:01 |
| `test_doctor_lane_destiny.py` | 4581 | 2026-09-02T23:19:01 |
| `test_doctor_lane_round.py` | 6456 | 2026-09-02T23:19:01 |

Untracked tests on this worktree include `tests/test_lane_e_q.py` (6325 B) which `import imap_listener` — present on disk, **not** in `git ls-files` for the listener itself.

### 1.3 `docs/lanes/`

Not a runtime package. Two lane evidence folders (`Get-ChildItem -Recurse -File`):

| path | bytes |
|---|---|
| `docs/lanes/ECONOMIC-LEARNING/DRAFT-REPLY-det-nsw-2026-09-02.md` | 2779 |
| `docs/lanes/ECONOMIC-LEARNING/VERIFIED-ECONOMIC-STATES-DESIGN.md` | 2792 |
| `docs/lanes/LA-SELF-AWARENESS/DoD.md` | 3453 |
| `docs/lanes/LA-SELF-AWARENESS/RECEIPT.md` | 2391 |
| `docs/lanes/LA-SELF-AWARENESS/evidence/SYSTEM-SELF-MODEL-20260902T0825Z.json` | 9272 |

DET draft is on this tree. This lane does **not** copy it into `F:\backup\docs\lanes\`.

### 1.4 `tools/`

| item | bytes / kind | role |
|---|---|---|
| `buynsw-harvester/` | dir | Chrome MV3 extension: read the buy.nsw page the human opened. `tools/buynsw-harvester/README.md`. |
| `ingest_buynsw_batch.py` | 2142 | File ingest of extension JSON onto a node (README points at board138). |
| `repo_baseline.py` | 4429 | Derive tenant/gate/test counts instead of prose. |
| `install_systemd.sh` | 1817 | **Untracked** recipe: oneshot units `octopus-{imap,followup,digest,heartbeat,backup,drill,quote}` + timers. |
| `backup_ofn.sh` / `restore_drill.sh` / `reconcile.py` / `smoke.sh` | 1005 / 1123 / 5001 / 1938 | Backup, restore drill, invariants, smoke. `smoke.sh` imports `imap_listener` (untracked chain). |
| `pilot_*.py` / `seed_pilot.py` / `capture_golden.py` / `check_rotation.py` / `gen_evidence_pack.py` | files | Pilot / evidence helpers. |
| `mcp/` | dir | Listed `??` in `git status -sb`. Not opened this increment. |

`Test-Path F:\ofn-node\tools\buynsw-harvester\ingest_server.py` → **False**. This tree’s harvester folder is extension JS only (`background.js`, `content.js`, `popup.*`, `mapping.js`, `manifest.json`). The process name `ingest_server.py --port 8791 --allow-no-auth` is from Lane B’s this-host listen receipt, not from a file in this checkout.

### 1.5 Other top-level dirs (names only)

Present on `Get-ChildItem F:\ofn-node`: `web/` (four HTML shells per README), `deploy/` (systemd `ofn.service` → `python3 -m ofn.run`), `packs/`, `data/`, `migrations/`, `scripts/`, `09-LANES/`, `06-EVIDENCE/`, plus several `octopus_*` / notes trees. Not mapped further this increment.

## 2. `imap_listener.py` — role, ports, wiring

### 2.1 What the file is

| field | value | source |
|---|---|---|
| path | `F:\ofn-node\ofn\agents\imap_listener.py` | `Get-Item` |
| bytes | 15875 | same |
| mtime | 2026-09-02T00:34:41 | same |
| git | **untracked** (`??`) | `git status -sb`; `git ls-files --error-unmatch` → pathspec not known |
| started this session | no | — |

Module docstring: Lane E inbox poll (“هر ۱۵ دقیقه”). Classifies `reply` / `bounce` / `optout` against known lead emails. `--dry` classifies only. JSON on stdout for systemd/journal. “هرگز raise نمی‌کند”.

### 2.2 Entrypoints (do not start)

| symbol | role | line (this file) |
|---|---|---|
| `lead_emails()` | SQLite `painting_leads` → email→lead_id | 83 |
| `classify(msg, sender, known)` | `(kind, intent, detail)` | 103 |
| `_act(...)` | writes leads / receipts / optional `owner_notify` | 162 |
| `cycle(dry=False, limit=60)` | one IMAP poll | 281 |
| `__main__` | `cycle(dry="--dry" in argv)` → `print(json.dumps(...))` | 345–350 |

### 2.3 Ports: client 993, not a local IMAP server

`cycle()` opens **`imaplib.IMAP4_SSL("imap.gmail.com", 993)`** (line 297), `select("INBOX")`, UID search/fetch, optional `\Seen`. There is **no** bind of 143 or 993 on this host in this file.

That matches Lane B: this host had no process matching imap/dovecot and no listen on 143/993; 138 had `octopus-imap` **oneshot** last-success + timer, and **no** 143/993 / dovecot (`F:\backup\09-LANES\B-PULSE-IMAP\PULSE_IMAP_DIAGNOSIS.md`, `SSH-RO-RECEIPT.md`). IMAP here is a **client poll**, not an IMAP daemon.

### 2.4 Relation to `octopus-imap` on 138

| layer | this tree (`F:\ofn-node`) | 138 (not re-probed this session) |
|---|---|---|
| unit recipe | untracked `tools/install_systemd.sh`: `mk_svc imap "python3 $AGENTS/imap_listener.py"` → `octopus-imap.service` `Type=oneshot`; `mk_timer imap "*:0/15"` | Lane B SSH: `octopus-imap.service` oneshot success `2026-09-03T09:30:34Z`; timer active. `claim_type: runtime` **then**, FILE_VERIFIED in B receipts now |
| env name in recipe | `Environment=OCTOPUS_WIRE_LEAD_OUTBOUND=1` in the **template** (line 19). Not enabled by this lane. | B receipt: `systemctl cat` showed the same env **name**. This lane did not cat 138. |
| imported by `ofn.run` | no | 138 `:8791-8794` was `python3 -m ofn.run` — a different process than the oneshot |
| this-host runtime | listener not running (B listen + this session did not start it) | body_not_on_this_host |

`docs/DISCOVERY.md` (untracked, `??`) describes `octopus-imap` every 15 min as “Real and verified” on a board path (`~/ofn/...`). That is a **file claim in this clone**, not a this-session SSH. Prefer Lane B runtime receipts for 138.

**Verdict:** on this worktree the listener is **source on disk + untracked-only**. It is **not** wired into `python -m ofn.run`. The systemd recipe that *would* register `octopus-imap` is also untracked. Whether 138’s oneshot executes **this exact 15875 B file** is unverified from this host (no fetch, no SSH this session).

## 3. `fix/demand-harvest` — harvester ≠ `ofn.run`

The branch name matches a **demand-side tender harvester**, not the four-shell HTTP service.

| body | what it is | wired to `ofn.run`? |
|---|---|---|
| `ofn/agents/demand_harvest.py` (13259 B) | OCDS GET + direction/403/score gates. File header: **DEAD SOURCE** (NSW eTendering ended Feb 2025; AusTender empty for painting). `USER_AGENT = "octopus-demand-harvester/1.0 ..."`. Entry: `cycle(...)` — **no** `if __name__ == "__main__"` in this file. | no (`run.py` / `node.py` have zero `demand_harvest` hits) |
| `ofn/agents/nsw_ocp_harvest.py`, `h1_harvest.py`, `h1_buysw.py`, `h1_buysw_dom.py`, `seek_harvest.py` | Other harvest adapters. `docs/octopus-os/02-AGENT-CONTRACTS.yaml` lists them; same file says `demand_harvest` + `nsw_ocp` parked / dead-source labeled. | no |
| `tools/buynsw-harvester/` | Browser extension. Default: local JSON, no auto-POST. Ingest path = `tools/ingest_buynsw_batch.py` on a board worktree per README. | no |
| `python3 -m ofn.run` | One process, four loopback sockets from `cfg.ports` (8791–8794). Prints `listening on 127.0.0.1: ...`. `deploy/systemd/ofn.service` `ExecStart=/usr/bin/python3 -m ofn.run`. | this **is** `ofn.run` |

**8791 collision (do not collapse):**

| host | what owned `:8791` | source | status |
|---|---|---|---|
| this laptop `.191` | `tools/buynsw-harvester/ingest_server.py --port 8791 --allow-no-auth` | `F:\backup\09-LANES\B-PULSE-IMAP\SSH-RO-RECEIPT.md` listen table (2026-09-03T09:29Z) | FILE_VERIFIED prior B; **not re-listened** this session |
| 138 | `python3 -m ofn.run` (ziman shell default port) | same B receipt + `ofn/config.py:283` | FILE_VERIFIED prior B |
| this `F:\ofn-node` tree | `ingest_server.py` **absent** | `Test-Path` this session | verified |

Same port number, different bodies. This checkout does not even contain the ingest server that B saw on `.191`.

## 4. Doctor / repair API

### 4.1 Doctor modules that exist

All under `F:\ofn-node\ofn\doctor\` (`Get-ChildItem` this session):

| file | bytes | role |
|---|---|---|
| `__init__.py` | 872 | Package: read-only diagnosis; organs do not patch themselves. |
| `cli.py` | 5238 | `python -m ofn.doctor.cli` → `contract-map` / `round` / `backlog` / `destiny`. |
| `round.py` | 15285 | Read-only vault walk. “There is no write mode and no flag that enables one.” |
| `contract_map.py` | 15470 | Maps `LAB-DOCTOR-CONTRACT.yaml` → symbols/tests. |
| `backlog.py` | 4787 | Self-backlog from contract gaps. |
| `destiny.py` | 9264 | Proposal outcomes. Mentions `secret_rotation` as a **forbidden action name**, not an enable. |
| `prescription.py` | 2771 | Prescription validation. |
| `receipts.py` | 3907 | Receipt log / hashes. |
| `miniyaml.py` | 6739 | YAML subset loader. |

CLI writes only under `--out`. It is not an HTTP repair surface.

### 4.2 `repair_api` still absent

| probe | result | source |
|---|---|---|
| `F:\ofn-node\tests\test_repair_api.py` | absent | `Test-Path` this session |
| `repair_api` / `test_repair_api` under `F:\ofn-node` (`ofn`, `tests`, `docs`, `tools` + recurse name match) | zero paths | prior hunt `Select-String` + this session recurse |
| `F:\backup` grep `repair_api` in `F:\ofn-node` | no matches | this session |

Closest: the five `test_doctor_lane_*.py` files (§1.2). Doctor ≠ repair API.

### 4.3 What would be needed (owner-only; fetch still closed)

To have a `test_repair_api` / `repair_api` **on this host**, the owner would have to authorize one of:

1. `git fetch` (or clone) of a remote that actually contains those paths — **still closed** unless asked. This lane cannot know whether origin’s two-ahead commits add them.
2. Adding a new HTTP/module surface here. That is an owner product decision, not a hunt finding. Doctor today is explicitly non-mutating.

This lane does not fetch and does not write that module.

## 5. Gates / flags referenced in this tree (names only — not enabled)

Read from files. Values were not flipped.

### 5.1 Closed-gate **names** (`config.py` / `gates.py` / `AGENTS.md`)

- `miner_isolation` — default closed list in `ofn/config.py` (`gates: list[str] = ["miner_isolation"]`)
- `secret_rotation`
- `partner_precondition`
- `OFN_KEEP_GATES_OPEN` — override **name**; after `GATE_OPEN_UNTIL_UTC = "2026-08-17"` the two rotation/partner gates re-close unless this flag is `1`
- `OFN_EXTRA_CLOSED_GATES` — comma list append
- `D1`, `D7`, `OWNER_KEY` — named in `F:\ofn-node\AGENTS.md` §4 as blocked; not opened here
- `auto_email` — named closed for agents in `AGENTS.md` §4; addendum records a **board** ruling #63 as a separate runtime story. This lane does not enable it.
- Kernel choke: `admit()` / `executable()` in `ofn/kernel/gates.py`
- `advisor_gate.py` — image-leave-board gate (no enable parameter)

### 5.2 Wire / commerce **flag names** (`config.load()`)

- `OFN_WIRE_OUTBOUND`
- `OFN_PUBLIC_CATALOG`
- `OFN_COMMERCE_ROUTES`
- `OFN_COMMERCE_AUDITED_RECEIPTS`
- `OFN_COMMERCE_PROVIDER_WEBHOOK`
- `OFN_SHOPIFY_WIRE` (`ofn/adapters/platforms/shopify.py`)

Dead / drift names (code does not read them as send permission per docs/tests): `OFN_WIRE_EMAIL`, `OFN_WIRE_PUBLISH` (`docs/audit/AUDIT-2026-08-08.md`, `tests/test_octopus_wire_drift.py`).

### 5.3 `OCTOPUS_WIRE_*` **names** (`CLAUDE.md` §2)

- `OCTOPUS_WIRE_LEAD_OUTBOUND` — **read** by `ofn/agents/followup_worker.py` (must equal `"1"` to send). Also appears as an Environment= line in untracked `install_systemd.sh`.
- `OCTOPUS_WIRE_EMAIL`
- `OCTOPUS_WIRE_LEAD_VERDICT_EFFECT`
- `OCTOPUS_WIRE_HARVEST`
- `OCTOPUS_WIRE_LEAD_DRAFT`
- `OCTOPUS_WIRE_PROJECTF_*`
- `OCTOPUS_WIRE_SABA_BRIDGE`

`tests/test_octopus_wire_drift.py`: `config.py` must **not** `os.environ.get("OCTOPUS_WIRE_...")`. Policy names ≠ `config.load()` readers.

### 5.4 Other names in `AGENTS.md` / hook (do not enable)

- `OBSERVATORY`, `CORTEX_HYPOTHESIS`
- `.cursor/hooks/guard_flags.py` also lists `D1_EXECUTION_AUTHORIZED`, `PRODUCTION`

Demand-harvest **code** gates (not env flags): direction / 403-never-retry / non-compensatory score inside `demand_harvest.py`.

## 6. Behind-2

```
status: local_behind_remote_unverified
```

`git status -sb` still prints `[behind 2]` vs `origin/fix/demand-harvest`. Without fetch we do not know what those two commits are, whether they still exist on the remote, or whether they contain `repair_api`. Local tracking objects may exist from an earlier fetch; they are not a current remote read.

## 7. Contradictions (`resolution: null`, `status: open`)

1. **Package version:** README `v0.8.0` vs `ofn/__init__.py` `0.1.0`.
2. **Test file count:** README “۱۷ فایل” vs 155 `test_*.py` this session. INDEX forbids a prose test-pass number without `repo_baseline.py --tests` (not run).
3. **8791 body:** B receipt = `ingest_server.py --allow-no-auth` on `.191`; this tree has no `ingest_server.py`; 138 = `ofn.run`. Three facts, not one process.
4. **IMAP “live” wording:** untracked `docs/DISCOVERY.md` vs B oneshot+no-143/993. Different definitions.
5. **Lane matrix:** `F:\backup\09-LANES\LANE-MATRIX.csv` still L0–L9 only; this folder exists (`SCOPE.md`). Same open item as prior hunt.
6. **DET hashes** (prior D, not re-hashed this increment): `aa98fff…` vs `d7aeb3eb…`. See `DET-DRAFT-DIFF.md`.

## 8. Not done (still closed)

- No `git fetch` / pull / clone / unzip.
- No pytest, no `python -m ofn.run`, no `imap_listener` start.
- No flag or gate enable.
- No accounting; books incomplete per owner.
- No copy of DET into vault `docs/lanes/`.
- No edit of C packet or A identity files.
- No commit.
