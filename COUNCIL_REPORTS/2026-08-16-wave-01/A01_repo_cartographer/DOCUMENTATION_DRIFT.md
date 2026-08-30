# DOCUMENTATION DRIFT — filesystem vs documents (A01, 2026-08-16)

Method: compared live filesystem + running processes against the documents most likely to be
treated as authority: `4d_system/MANIFEST.yaml`, `4d_system/README.md`, `_ops/ARCHITECTURE-LAYERS-2026-07-27.md`
(incl. ERRATA 2026-08-12), `OCTOPUS/README.md`, `OCTOPUS/ARCHITECTURE-BIBLE.md`, `OCTOPUS/CURRENT-TRUTH.md`,
root `README.md`, `nbb-cp-kre/README.md`, `NBB-Control-Plane/RUNBOOK.md` (existence only).

## Drift items

| # | Document says | Filesystem/runtime says | Verdict |
|---|---------------|--------------------------|---------|
| DR-01 | Project brief claims "layers L0-L8" | `_ops/ARCHITECTURE-LAYERS-2026-07-27.md` defines **7 layers: 0 Body, 1 Senses, 2 Memory, 3 Understanding, 4 Decision, 5 Action, 6 Interface, S Safety**. No L0–L8 scheme exists in any current doc or code (only an old FIX-START log mentions it). | **Claim contradicted by project's own SoT** |
| DR-02 | `OCTOPUS/README.md`: "OCTOPUS is the visualization layer… static HTML/JS" | Correct — OCTOPUS/ is pure static viz. BUT external readers may assume it's the organism; the organism actually lives in `_ops/`. Naming inversion: folder named OCTOPUS is the least OCTOPUS-like directory. | Doc right, naming misleading |
| DR-03 | `4d_system/MANIFEST.yaml`: "STANDALONE RESEARCH BRAIN — NOT wired to Octopus projects" (2026-07-11) | Still true at runtime: no 4d_system process running; cortex sees it only via opt-in observe lane; MANIFEST is 5 weeks old yet accurate. | No drift (notable rarity) |
| DR-04 | `4d_system/README.md` architecture tree lists `ui/app.py`, `agents/orchestrator.py` etc. as the core layout | Present, but the directory has grown far beyond the README tree (brain/ 38 modules, src/nbb_cp embedded, nbb-cp-kre, control_plane 11 modules, 70 test files). | README understates scope |
| DR-05 | `organism.py` docstring: "8768 = brain lock (app.py)" | No `app.py` exists anywhere under `_ops/`. Port 8768 unowned. | **Stale lore inside live code** |
| DR-06 | `4d_system/start.bat` | `cd C:\Users\Armin\Desktop\4d_system` — path does not exist | Broken launcher |
| DR-07 | `ARCHITECTURE-LAYERS` ERRATA: "don't trust this doc for wire status — rg/disk first" | Honest and correct: `wiring.py` + live ORGANISM-STATE wiring map (≈40 wires all true) is the real SoT. | Self-aware doc; good |
| DR-08 | `OCTOPUS/CURRENT-TRUTH.md` | Updated 2026-08-12 era; references commits d81c7c1..2b47b90 (chat-honesty lane) — these predate current HEAD 028fe81. | Mildly stale; layer of truth files exists in 01-TRUTH/ too |
| DR-09 | Root `README.md` (Aug 15) | Describes vault orientation; not an architecture SoT. | OK |
| DR-10 | `nbb-cp-kre/README.md` install: `cd /d F:\kre-out\nbb-cp-kre` | Package actually lives at `F:\backup\4d_system\nbb-cp-kre`. Install doc points at an output dir. | Drift (cosmetic but confusing) |
| DR-11 | Genome ledger described in docs as "bitemporal" (per wave brief) | `ledger/ledger.py` v0.4.6: append-only SHA-256 hash chain with single event `ts` + monotonic `age_tick` (+is_human). **No valid-time/system-time bitemporal axes.** | **Contradicted** (unless "bitemporal" is redefined as ts+age_tick; that is nonstandard) |
| DR-12 | MANIFEST stats "141 tests green" (2026-07-11) | 4d_system/tests now ~70 files incl. l0/l1/l2 trees for nbb-cp — count grew; no fresh run evidence in cache | Unverifiable tonight (T1 needed) |
| DR-13 | `_ops/ARCHITECTURE-LAYERS` Layer-1 lists `_LEG_DEFAULT` for five business legs as unwired skeleton | Live state 2026-08-16: lead leg LIVE with inbox 0 pending / 22 processed, quotes+invoices on disk; ziman active; mining/crypto still skeleton | Doc (July 27) partially stale; disk wins |
| DR-14 | ADR-033 / ADR-034 tests exist (`test_adr033_control_plane.py`, `test_adr034_neural_demote.py`) | Code matches (`policy/policy_gate.py`, neural demotion). | Aligned |
| DR-15 | Various `_ops` MEGAPROMPT/discovery MDs claim Sensorium/viability-loop as features | Zero Python matches for "sensorium"/"viability" in any organism tree; only `homeostasis.py` experiment inside unrelated `research-spec-compiler` project | **Documented-not-implemented (at best)** |
| DR-16 | `07 - Knowledge/شناسایی-اختاپوس/` (octopus-identification) knowledge base with numbered notes (49-53) | Present and actively updated (note 51 WEBPANEL-REALITY, 52 OWNER-EASE, 53 OWNER-CLOSE dated 2026-08-16) | Aligned, active |
| DR-17 | Remote named `germline` → E:/germline/octopus.git | Exists (local bare). ORGANISM-STATE reports `germline_lag_h: 0.9, germline_alert: ok` — the loop itself watches this remote. | Aligned, live-monitored |
| DR-18 | Desktop `OCTOPUS-NBB-CP-WORKING` (outside repo) | Separate git repo whose remote is a **bundle file inside the vault**; active commit today 16:02 — governance history partially living outside the main repo | Structural drift risk |

## Bottom line
The project's own recent docs (ARCHITECTURE-LAYERS + ERRATA, MANIFEST) are unusually honest and
mostly match disk. The drift concentrates in (a) **stale lore inside live code comments** (DR-05),
(b) **broken/stale launchers** (DR-06, DR-10), (c) **claims imported from older megaprompt docs**
that never had implementations (DR-11, DR-15), and (d) **the multi-home NBB-CP situation** (DR-18, DUP-001).
