# OWNER RO — Scope E directory architecture map

**mode:** list / map only · **no implement**  
**stamp_aest:** 2026-09-16  
**from:** OCTOPUS_COMMANDER PARALLEL RO Scope E  
**HOLD:** customer_send · dual-commander DENY · no live apply

## Roots discovered (F:\backup)

| probed path | status |
|-------------|--------|
| `F:\backup\06 - Architecture Maps` | **EXISTS** (canonical; space after 06) |
| `F:\backup\06-Architecture Maps` | MISS |
| `F:\backup\04 - Architect System` | **EXISTS** |
| `F:\backup\04-SYSTEMS` | **EXISTS** |
| `F:\backup\04 - SYSTEMS` / `04-Architect System` | MISS |

Sibling noise (not in Scope E charter): `06-EVIDENCE`, `06-RISKS`.

---

## A. `F:\backup\06 - Architecture Maps`

**Top:** 2 dirs · 63 files (mtime cluster ~2026-09-09)

### Subdirs

| name | contents (evidence) |
|------|---------------------|
| `api-specs/` | 9× `BB-*.openapi.yaml` (Attribution, Germline, Leg, OpsLib, OrganGate, PocketSmith, Reconcile, Registry, Telemetry) |
| `نقشه-اختاپوس/` | GUIDE-FA, MANIFEST.yaml, REGISTRY.md, RUNBOOK.md, SYSTEM-PROMPT.md, vault-inventory.json, vault-report.md, vault_scanner.py, VERDICT_QUEUE.md |

### Notable top-level map files (sample / index anchors)

- `_Index - Architecture Maps.md` (MOC; updated 2026-08-12)
- `ARCHITECTURE-SOT.md`, `SYSTEM_MAP.md`, `SYSTEM-OVERVIEW.md`, `ECOSYSTEM.md`
- `MASTER-ARCHITECTURE-2026-07-09.md`, `MASTER-ARCHITECTURE-2026-07-29.md`
- `OCTOPUS-CURRENT-TRUTH.md`, `OCTOPUS-STRUCTURE.md`, `OCTOPUS-CHANNEL-REGISTRY.md`
- `OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md`, `OCTOPUS-EXTRACTOR-REGISTRY.md`
- Consoles: `OCTOPUS-ARCHITECTURE-CONSOLE-2026-08-28.html`, `OCTOPUS-OPS-CONSOLE-2026-08-28.html`
- Control/risk: `EFFECT-TAXONOMY-E0-E4-2026-07-20.md`, `RISK-LADDER-2026-07-11.md`, `WATCHDOG-TOPOLOGY-D5-2026-07-21.md`
- Heart / 4D: `HEART - Neuro Map & Direction.md`, `Octopus_Heart_Design_v1.md`, `4D.md`, `TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane.md`

**Ziman / Studio / Nova (filename scan depth≤4):** **none** under this root.

---

## B. `F:\backup\04 - Architect System`

**Top:** 9 dirs · 69 files

### Subdirs

| dir | note |
|-----|------|
| `4D-Obsidian-Foundation/` | 00–07 foundation / Obsidian IA / MLP doctrine |
| `ANALYSES/` | 2026-07 deep-scan / critique / CHORD / roadmap |
| `architect/` | Obsidian vault skeleton (`01-Project`…`04-Docs`, charter) |
| `learning-engine/` | ENGINE-PROMPT, LEARNING-CONTRACT, mutation ledgers |
| `octopus-build-prompts/` | HH-P0…P10, BASE-MAP v0/v1, P1–P6 build prompts |
| `octopus-completion-2026-07-24/` | parallel completion megaprompts |
| `prompts/` | debate / governor role texts |
| `scripts/` | germline backup, health, watchdog, constitution drift |
| `_intake-photos/` | intake notes |

### Ziman / Studio / Nova hits

| path | kind |
|------|------|
| `F:\backup\04 - Architect System\ZIMAN-GALLERY-CONCEPT-REVIEW-v1.md` | **Ziman** concept review (only dedicated Ziman hit in Scope E) |
| Studio / Nova dedicated map filenames | **ABSENT** (depth≤4) |

Other business-adjacent filename under this root: none for Studio/Nova/Saba/GiftMesh at scan depth.

---

## C. `F:\backup\04-SYSTEMS`

**Top:** 0 dirs · 27 files (flat)

Sample system specs: `OCTOPUS.md`, `OFN-NODE.md`, `NBB-CP.md`, `LEGS-LIVE.md`, `OWNER-CONSOLE.md`, `DUAL-BRAIN-CONSTITUTION.md`, `TYPED-EVENTS.md`, `TELEGRAM-LEASE-DESIGN-2026-08-16.md`, agent inventory / halt drill (2026-08-16).

**Ziman / Studio / Nova:** no filename hits. Closest: `OFN-NODE.md` (organism/node — not a Studio/Nova business map).

---

## Scope E verdict (honest)

| ask | finding |
|-----|---------|
| Architecture Maps root | use **`06 - Architecture Maps`** (spaced name) |
| Architect System + SYSTEMS | both present; SYSTEMS is flat docs; Architect System is vault + prompts |
| Ziman maps | **1** file: `ZIMAN-GALLERY-CONCEPT-REVIEW-v1.md` |
| Studio / Nova maps | **ABSENT** in these three roots by name (depth≤4) |
| Implement | **none** this turn |

**ARCH standing:** directory evidence map only. No file moves, no edits under F: trees, no enqueue.
