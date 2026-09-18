# OWNER-RO-OFN-INJECT-SURFACES-20260916 (ARCHITECT)

**mode:** MAP ONLY · **no implement** · **HOLD_EXTERNAL** · **do not enqueue** · **do not mutate live ofn state**  
**stamp_aest:** 2026-09-16 ~09:31+  
**from:** PRIORITY OWNER RO → ARCHITECT  
**extract:** `_extract-ofn-inject-surfaces-20260916.md` sha `a457312d780d784fb5e7d38633f320ab8e7a52441e116a92cfcd6c6431982c1c`  
**SEC gate (design):** `SEC-RO-INTEL-INJECT-GATE-20260916.md` sha `4b9158bf1c1db72df7e6f69e8b84ba8a2bb8e3cdefbc86e1193d86480a53ad6e` · **CONDITIONAL_PASS** · EXECUTE blocked until COMMANDER cites that sha  
**commander:** **138 sole** · dual-commander **DENY** · **customer_send HOLD** · `may_authorize=false`

---

## 0 · Verdict (one screen)

| ask | answer |
|-----|--------|
| Safe place for RO deep packs in organism memory? | **YES (design):** append-only **fleet-memory** facts/decisions/hypotheses + **receipt** lines (glass / owner_dialogue intel_ingest) — **138 writer only** |
| May ARCH/laptop write live ofn? | **NO** this turn — map only; live mutate DENY |
| May packs land in `fleet_jobs.jsonl` or JetStream? | **DENY_WRITE** — breaks P0–P6 jsonl_138 / lease SM / dual-poll invariants |
| Ready to inject now? | **NO** — SEC EXECUTE not relayed; HOLD_EXTERNAL intact |

---

## 1 · Packs located (sha prefix → full sha → paths)

| label | sha256 (full) | canonical path(s) | also found |
|-------|---------------|-------------------|------------|
| **INTEGRATE** | `06a3ea9bc2d6c6081fe07cf1d46ed04059365bafc73a2cfd5a68801e6f2d0133` | `/workspace/octopus-hq/research/OWNER-RO-DEEP-INTEGRATE-20260916.md` | `C:\Users\Armin\Desktop\ro-deep-20260916\` **MATCH** |
| **SEASON-BIZ** | `575e1713589c06ad0b32adfbdc701b39151a9369c8e06aa7e5189e45a6bbe5aa` | `/workspace/octopus-hq/research/OWNER-RO-DEEP-SEASON-BIZ-20260916.md` (+ `.sha256` sidecar) | Desktop mirror **MATCH** |
| **STUDIO** | `83d955fe346879b2ff3f3670af9943f3bd0d109182f8c1c066dcfd1fd5fe0ef7` | **`F:\backup\research\OWNER-RO-DEEP-STUDIO-EVIDENCE-20260916.md`** | JSON sidecar `cc65723b…` (≠ md); **NOT** under HQ `research/` |
| **EVIDENCE-ZIMAN** | `be8d8c726d20eb85ea48aa08c04d2df3e35864a3cb1fcb3b26fd6caf57afa6cc` | `/workspace/octopus-hq/research/OWNER-RO-DEEP-EVIDENCE-ZIMAN-20260916.md` (+ sidecar; content_without_footer `68fe5aaf…`) | Desktop / F:\backup\09-LANES / Temp: **ABSENT** this scan |
| **SEC** | `d93d73dff094e56f93c016d72ffec6b6a1060c1eeb25d1e98934304c4986e53d` | `/workspace/octopus-hq/wiring/OWNER-RO-DEEP-SEC-HOLD-AUDIT-20260916.md` | Desktop / Temp: **ABSENT** this scan |
| **ARCH** | `8149d40f876730cbf5c2759f9467453682ba24394f3f45b9fe604e57f390b0f5` | `/workspace/octopus-hq/wiring/fleet-brain/OWNER-RO-DEEP-ARCH-WIRING-20260916.md` | `F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-EXEC-20260915\` **MATCH**; `C:\Users\Armin\AppData\Local\Temp\arch-fleet-p0\` **MATCH** |

### STUDIO caution (DENY wrong body)

| file | sha | inject? |
|------|-----|---------|
| `OWNER-RO-DEEP-STUDIO-EVIDENCE-20260916.md` | `83d955fe…` | **ALLOWLIST** (SEC gate) |
| `/workspace/octopus-hq/research/OWNER-RO-DEEP-STUDIO-20260916.md` | `23a723f2…` | **DENY** for this GO |
| STUDIO ADDENDA A/B/C under research | `a012f37b…` / `9a48b214…` / `b598be70…` | **DENY** (≠ allowlist) |

Optional Desktop mirrors OK **only if** re-hash MATCHES allowlist row (SEC §1).

---

## 2 · Surface table (live ofn / organism memory)

Classification keys: `SAFE_APPEND_RO_PACK` · `SAFE_READ` · `DENY_WRITE` · `UNKNOWN`  
Evidence = sealed P0–P6 docs + Architecture Maps + SEC inject gate. **No live SSH mutate this turn.**

| surface | path / cite | class | writer | why |
|---------|-------------|-------|--------|-----|
| **P1 fleet_facts** | `/home/ari/ofn/state/fleet-memory/fleet_facts.jsonl` | **SAFE_APPEND_RO_PACK** (post-EXECUTE) | **138 only** | P1 dry persist SoT; append-only tier A; QA matched live `adff9efb…` |
| **P1 decisions** | `…/fleet-memory/` + `fleet_decision.v1` schema on 138 | **SAFE_APPEND_RO_PACK** (post-EXECUTE) | **138** | Tier B; require `expires_at` + `hold_external`; bind to pack sha |
| **P1 hypotheses** | `…/fleet-memory/` + `fleet_hypothesis.v1` | **SAFE_APPEND_RO_PACK** (gated) | 138 persist · **180 quality gate** before promote | Tier C; need `source_fact_ids`; **DENY** C→A without gate |
| **P1 schemas** | `…/fleet-memory/schemas/*.json` (also HQ `wiring/fleet-brain/schemas/`) | **SAFE_READ** | n/a | Validate before append; do not overwrite without GO |
| **fleet_jobs ledger** | `/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl` + `idempotency_index.json` + `fleet_job_sm.py` | **DENY_WRITE** (RO packs) | 138 SM only for real jobs | P5 canonical bus; pack rows ≠ `retrieve`/`prep`/… jobs |
| **JetStream / NATS-182** | engine YES · **consumers=0** · no `FLEET_JOB` stream | **DENY_WRITE** | n/a | Dual-poll vs jsonl_138; hijack SENSORIUM/AUDIT/COMMAND **DENY** |
| **182 Class-B witness** | receipt artifact witness only | **SAFE_READ** (witness path) · **DENY_WRITE** as memory SoT | 182 never second memory writer | P4/P5: lab_witness only |
| **180 restore copies** | `/opt/octopus-restore-copies/…` · `fleet-memory-restore-copies/` | **SAFE_READ** | 180 RO copy after 138 persist | Dual-commander **DENY**; never sole SoT |
| **memory.sqlite** | backup_job / organism DB | **DENY_WRITE** (overwrite) · **UNKNOWN** scoped table append | restore_job / Online Backup API only | P1/P3: do not overwrite sole DB without scoped GO |
| **owner_dialogue** | `/home/ari/ofn/state/owner_dialogue/` (+ mesh twin under `octopus-mesh/state/owner_dialogue/`) | **SAFE_APPEND_RO_PACK** for `intel_ingest.v1` / glass note only | **138** | SEC allowlist; **DENY** treat as GO-B4 / widen APPROVE_PAT |
| **glass ingest** | (index/receipt — path not pinned in fleet-brain P5) | **SAFE_APPEND_RO_PACK** (receipt/index row) | organism/PC under EXECUTE | Pointers to pack sha; no customer fan-out |
| **autonomy queue** | `/home/ari/ofn/state/autonomy/queue.jsonl` | **DENY_WRITE** (RO packs) | autonomy-supervisor | Separate task SM — keep separate (P0) |
| **revenue-drive /** | `/home/ari/ofn/state/revenue-drive/*` | **DENY_WRITE** · OBSERVE ONLY | n/a | Not brain memory; customer_send adjacent |
| **genome ledger** | Architecture Maps: `07 - Knowledge/genome-system/ledger/ledger.jsonl` (vault plane) | **SAFE_READ** · **DENY_WRITE** for RO-pack inject | genome-system / opslib only | Heart/Ring-0 adjacent; not fleet-memory; stuffing packs breaks ledger semantics |
| **vault / Obsidian graph** | `_memory/graph/{nodes,edges}.jsonl` (MULTI-AGENT-MEMORY-GRAPH-DESIGN) | **UNKNOWN** on live 138 ofn | design/workspace | Doc plane; **not** claimed as P1 fleet-memory SoT |
| **research_ingest / self_loop_ingest** | OCTOPUS-INTEGRATION-STATUS: **PARTIAL→WIRED pending reload**; Index cites `OCTOPUS-MEMORY-TRUTH-MAP` | **UNKNOWN** | organism heart/brain | Exact ofn path **not** in P0–P6 sealed contracts; Memory Truth Map **ABSENT** under `F:\backup\06 - Architecture Maps` this scan (vault link only) |
| **F:\ofn-node** (laptop tree) | code/docs mirror; **no** `F:\ofn-node\state` | **SAFE_READ** docs · **DENY_WRITE** as if live 138 | laptop | Not live `/home/ari/ofn/state` |

### P0–P6 path reminder (do not break)

```
[P0] 182 JetStream YES · consumers=0 · NATS durability NOT_CLAIMED
[P1] 138 …/fleet-memory/fleet_facts(+decisions/hyp)  ← RO pack landing zone
[P2] 138 …/fleet-jobs/fleet_jobs.jsonl               ← DENY pack inject
[P3] 180 restore RO copies
[P4] registry auth · lease_eligible workers
[P5] CANONICAL bus = jsonl_138 · pilot type=retrieve→100
[P6] measure; HOLD customer_send
```

---

## 3 · WHY writing packs into `fleet_jobs.jsonl` or JetStream breaks the fleet

1. **Wrong schema / wrong bus** — `fleet_job.v1` is a lease state machine (`QUEUED→LEASED→RUNNING→PERSISTED→CLOSED`), not a knowledge document. Pack markdown/sha rows would fail schema or be misread as work items.  
2. **False work / worker side effects** — Workers 100/160/193/114 lease by `type` + `worker_node_id`. Spurious QUEUED rows can trigger retrieve/prep/infer/eval against garbage payloads.  
3. **Idempotency corruption** — `idempotency_index.json` is the uniqueness spine; ad-hoc pack lines risk key collisions or index drift → retry/poison loops.  
4. **Commander invariant** — Only **138** may produce/lease. Laptop/ARCH enqueue of “jobs” that are really docs creates a **shadow commander** path (dual-commander class failure).  
5. **JetStream specifically** — Proven engine with **0 consumers** and **no** `FLEET_JOB` stream. Publishing pack payloads or creating a consumer without SEC+proof yields: (a) dual-poll with jsonl_138 (**explicit DENY**), (b) risk of stuffing SENSORIUM/AUDIT/COMMAND, (c) false durability claims (`NATS_DURABILITY` must stay `NOT_CLAIMED` until proof).  
6. **P6 honesty** — Acceptance assumes bus=`jsonl_138`. Mixing doc-ingest into the job bus falsifies PB measurements and receipt chains.

---

## 4 · Fail-closed inject recipe (DOCS ONLY — do not run this turn)

**Preconditions (all required):**

1. COMMANDER relays **EXECUTE** citing SEC gate sha `4b9158bf…` + allowlist table.  
2. Re-hash **6/6** (or 7/7 with QA) packs; any drift → **STOP** that pack.  
3. `customer_send=false` · `may_authorize=false` · dual-commander **DENY** · never power off 138.  
4. HOLD_EXTERNAL unchanged; no marketing/OF/Shopify unlock.

**Where packs land (preferred order):**

| step | where | who writes | what |
|------|-------|------------|------|
| A | Laptop/HQ: keep sealed sources + sha sidecars | anyone RO | no live ofn |
| B | 138 `…/fleet-memory/fleet_facts.jsonl` | **138 only** | One `fleet_fact.v1` per pack: `kind=owner_ro_deep_pack`, `body_hash=<pack sha>`, `source_refs=[path]`, `source=owner_ro_deep_20260916`, `external_effects=0`, `customer_send=false`, `commander_node_id=138` |
| C | Optional same dir decisions/hypotheses | 138 (+180 gate for C) | Decision binds pack sha + `hold_external=true` + expiry; hypothesis only with `source_fact_ids` |
| D | glass ingest index + `owner_dialogue` `intel_ingest.v1` | **138** | Receipt `{schema, at, pack_label, source_path, sha256, targets[], customer_send:false, may_authorize:false}` |
| E | 180 restore copy | 180 RO | After B succeeds — verified copy only |
| F | 182 Class-B | 182 | Optional witness of **receipt artifact** only — not second SoT |

**Who must not write:** laptop ARCH agent, Desktop mirrors alone, 180-as-commander, dual pollers, JetStream publishers for this GO.

**Idempotency:** same sha already ingested → `ACK_SEEN`, zero bytes.  
**Sanitize:** secret-like → quarantine, do not append body.  
**Rollback:** tombstone/delete only new receipt lines by `inject_id`; never wipe fleet-jobs / never `reset --hard`.  
**Explicit DENY list:** fleet_jobs.jsonl · JetStream consumer create · memory.sqlite overwrite · genome ledger pack dump · revenue-drive · autonomy queue · customer Telegram · OF/Shopify · dual-commander.

---

## 5 · Blockers

| id | blocker | severity |
|----|---------|----------|
| B1 | SEC EXECUTE not relayed (design CONDITIONAL_PASS only) | **P0** |
| B2 | HOLD_EXTERNAL / customer_send HOLD / may_authorize=false | standing |
| B3 | STUDIO allowlist body lives only on `F:\backup\research\…EVIDENCE…` — HQ research STUDIO drafts are **wrong sha** | P1 |
| B4 | EVIDENCE-ZIMAN + SEC packs not mirrored on Desktop / Temp this scan — box canonical OK | P2 |
| B5 | `research_ingest` / `self_loop_ingest` + Memory Truth Map path **UNKNOWN/ABSENT** on Architecture Maps tree — do not invent ofn path | P2 |
| B6 | glass ingest concrete filesystem path not pinned in P5 contract | P3 |
| B7 | JetStream consumers=0 — must stay off for inject GO | standing DENY |
| B8 | This ARCH turn: **no implement / no enqueue / no live ofn mutate** | standing |

---

## 6 · Search receipts (RO)

| location | result |
|----------|--------|
| `/workspace/octopus-hq/` | All 6 packs except STUDIO evidence (STUDIO drafts ≠ allowlist) |
| `F:\backup\research\` | STUDIO evidence `83d955fe…` **FOUND** |
| `F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-EXEC-20260915\` | ARCH `8149d40f…` + P0–P6 path evidence |
| `F:\backup\00-SEASON\` | season/studio historical docs; **not** the 6 deep-pack allowlist bodies |
| `F:\backup\06 - Architecture Maps\` | genome / research_ingest status / memory-graph design cites |
| `F:\ofn-node\` | code/docs; **no** local `state/` twin of `/home/ari/ofn/state` |
| `C:\Users\Armin\AppData\Local\Temp\arch-fleet-p0\` | ARCH + SEC P5/P4/P6 folds; OK for temp copies |
| `C:\Users\Armin\Desktop\ro-deep-20260916\` | INTEGRATE + SEASON-BIZ MATCH; STUDIO/EVIDENCE-ZIMAN/SEC/ARCH allowlist bodies **not** present as matching hashes |

---

## 7 · Standing

- **Map sealed** · ARCH idle unless COMMANDER assigns EXECUTE-aligned apply (PC/organism) or further RO.  
- **Do not** implement inject · **do not** modify `F:\ofn-node` live state · Temp copies under `arch-fleet-p0` OK.  
- Aligns SEC-RO-INTEL-INJECT-GATE · P1 memory · P5 job-path · OWNER-RO-DEEP-ARCH-WIRING.

— ARCHITECT · PRIORITY OWNER RO · MAP ONLY · 2026-09-16
