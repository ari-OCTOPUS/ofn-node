# OWNER RO — Deep architecture wiring map (business × fleet)

**mode:** MAP ONLY · **no implement** · **HOLD_EXTERNAL** · HOLD customer_send  
**stamp_aest:** 2026-09-16  
**from:** OCTOPUS_COMMANDER DEEP PARALLEL RO → ARCHITECT  
**prior maps:** OWNER-RO-7BOARD `a15a86bc…` · Scope E dirs `a2c18264…`  
**extract:** `_extract-deep-arch-e-20260916.md` sha `dbfe89c341205eb584374821422e27b5fb94bd01b1c6ac814ea3f6fac5dc5677`

---

## 0 · Verdict (one screen)

| lane | Architecture Maps evidence | Wired to fleet 138/180/182/100/160/193/114? |
|------|----------------------------|---------------------------------------------|
| **Telegram** | Dominant control plane (dual-bot, MiniApp, dual-outbox, TG-SPLIT) | **ABSENT** as fleet job_type / lease consumer — laptop/_ops plane, not P5 jsonl path |
| **Ziman** | Domain D4 · capacity-guard · `ziman_beat`/`ziman_leg` · drafts-only · publish/send **hard-blocked** | **ABSENT** fleet bind — no `target_node_id` / capability for Ziman commerce |
| **Studio / Saba / Project-F** | MiniApp tab `studio` · `studio_pf` · `saba_studio.py` **DORMANT** · bridge scaffold | **ABSENT** fleet bind — no Studio/Saba worker role on 7-board |
| **OnlyFans** | Forever **BLOCKED_PREFIXES** | N/A — DENY wire |
| **Shopify / Nova / GiftMesh / Maliheh** | **ABSENT** (depth≤2 Architecture Maps) | **ABSENT** |
| **OFN marketing** | No SoT lane; `ofn-node` UI string only | **ABSENT** |

**Persistent fleet (P0–P6)** remains organism compute path: retrieve→prep→infer→eval under **138 sole commander**. Business publish/send paths are **not** claimed on those boards.

---

## 1 · Source hashes (sealed reads)

| source | sha256 |
|--------|--------|
| ARCHITECTURE-SOT.md | `69dbb193f222d5486ea87bf27aa1d152614b29cedf4f2ee8d8b6a8c1e4b7c919` |
| SYSTEM_MAP.md | `429c1e600ed1e1e16d563ee31d3ee7719bda0aa3081b7b6395239c7d7ab10a54` |
| OCTOPUS-CURRENT-TRUTH.md | `480d0bb9d2c28bde52652abf6ee400a175b639d070458e3044c29b9b5e7a0309` |
| MASTER-ARCHITECTURE-2026-07-09.md | `88c466fd28a60d9b2b43f1848e9d5791d3be8db105babbec254b99557b9f3a73` |
| MASTER-ARCHITECTURE-2026-07-29.md | `44673e13c2415d3f0dec157f9b51190726312cf374d5b043edec1416a878f46f` |
| ZIMAN-GALLERY-CONCEPT-REVIEW-v1.md | `237e03ffbd75366e25a73bac810c2f8804678f413c138a536d4574cfb54d7696` |
| octopus-build-prompts/00-INDEX.md | `3b672c6088122fff75369d0517e964500e27b9f3263b6eae534cb571ee4ef085` |
| OCTOPUS-CHANNEL-REGISTRY.md | `6eb7d24ff216dc1fe986703ab7da6f2dee5c5682ac65d1cb08f5572236c04a84` |
| TELEGRAM-DUAL-OUTBOX-CONTRACT.md | `c32bdaaf4f52029c5a8d407a26184fa94ab28dadc6c001fd285deeec3d56cd46` |
| TG-SPLIT-INNER-OUTER-2026-07-29.md | `cd59c954b0000c845dbeda7942138435c051e1f0bf874bf4f80e53c89dedce0b` |
| P4 aligned / P5 contract / P6 design | `8b0a5e03…` / `5d12e068…` / `4dea6030…` |

---

## 2 · Interfaces extracted (doc evidence only)

### 2.1 Telegram
- Bot #1 private approval (`approval_channel.py`) · Bot #2 group centre (`telegram_center/center.py`) — LIVE in SOT
- TG-SPLIT inner `@Robo2725_bot` / outer `@intergrade2725_Bot` · `OCTOPUS_TG_SPLIT_V1`
- Dual-outbox contract · CH-15 stub / CH-15b RO · MiniApp `127.0.0.1:8774` (public URL BLOCKED)
- doctor_link LIVE; held-stream gap noted in MASTER-ARCH 07-29
- Build index: P3-TELEGRAM before money; human-append for irreversible effects

### 2.2 Ziman
- SYSTEM_MAP domain **Ziman — capacity ceiling (D4)** · guard `ziman-capacity-guard`
- Legs: `ziman_beat` / `ziman_leg.py` — drafts-only; **publish/send hard-blocked**
- ECOSYSTEM: **"Ziman Gift"** (≠ GiftMesh — do not conflate)
- Gallery review: concept/claims only; **primary concept doc missing**; **no commerce/TG/Shopify wiring**
- Build index: "Ziman branding cherry-pick" flag-off

### 2.3 Studio / Saba / Project-F
- MiniApp tab **`studio`** · WAVE2 CRM Studio panel · spine topic **`studio_pf`**
- `saba_studio.py` **DORMANT** · `saba-bridge.jsonl` scaffold · `/api/pf/*` owner auth · credentials BLOCKED in MiniApp
- BlackBox: Project-F studio ingests ZERO media/PII; separate TG bot/chat pattern

### 2.4 OnlyFans / OFN / ABSENT lanes
- OnlyFans/Fansly: `BLOCKED_PREFIXES` forever — login/automation/scrape/mass-DM DENY
- OFN: `ofn-node` / adapters in OPS-CONSOLE HTML only — **no OFN marketing architecture SoT**
- **ABSENT depth≤2:** Nova, Shopify, GiftMesh, Maliheh

---

## 3 · Cross-map → 7-board fleet roles

Prior SoT: OWNER-RO-7BOARD-P0P6-MAP `a15a86bc…` · P4 `8b0a5e03…` · P5 `5d12e068…`

| node | fleet bind_role | Business-lane wire from Architecture Maps? |
|------|-----------------|--------------------------------------------|
| **138** | commander | Docs put **Telegram HITL / legs dispatch** on laptop/_ops organism — **not** described as fleet_job producer for Ziman/Studio Shopify. Fleet P5 producer is organism jobs only. |
| **180** | quality + restore_RO | **ABSENT** Ziman/Studio review lane in maps as 180 duty; gallery review is Architect System doc, not 180 service. |
| **182** | lab_witness / NATS | **ABSENT** business channel; JetStream ≠ TG dual-outbox. |
| **100** | knowledge_retrieve | **ABSENT** Ziman catalog / Studio media retrieve job_type in sealed maps. |
| **160** | knowledge_prep | **ABSENT** Ziman prep / Studio ingest prep on fleet. |
| **193** | model_infer (≠ T3) | **ABSENT** Studio/OF model path; OF blocked forever. |
| **114** | eval_batch | **ABSENT** business A/B eval wired to fleet. |

### ABSENT business wires (explicit)

1. No `fleet_job.type` ∈ {ziman_*, studio_*, shopify_*, saba_*} in P5 contract / live schema `49eb6c0b…`.  
2. No registry `bind_role` for commerce/publish on any of 100/160/193/114.  
3. No Shopify connector in Architecture Maps SoT (count=0).  
4. No Nova Sole / GiftMesh filename or SoT citation in Scope E deep read.  
5. Telegram LIVE stack is **orthogonal** to P5 `jsonl_138` pilot retrieve→100 — dual-plane; do not claim unification without new design.  
6. Ziman publish/send remains **hard-blocked** in wiring-debug — aligns HOLD_EXTERNAL / customer_send HOLD.

```
[Architecture Maps plane]     Telegram CP · legs (ziman/studio_pf) · MiniApp
        ↕  DOC ONLY / NOT FLEET-WIRED
[Persistent fleet plane]      138 jsonl SM → 100/160/193/114 · 180 RO · 182 witness
```

---

## 4 · Risks / honesty

- Do not invent Shopify or Nova maps — **ABSENT**.  
- Do not treat ECOSYSTEM "Ziman Gift" as GiftMesh.  
- Do not treat gallery concept review as runtime wiring.  
- Do not claim Saba studio LIVE — **DORMANT**.  
- Dual-commander still **DENY**; 193 ≠ T3 model-server.  
- HOLD_EXTERNAL · no customer_send · no ARCH implement this turn.

---

## 5 · Artifacts

| file | role |
|------|------|
| This packet | COMMANDER priority deliverable |
| `_extract-deep-arch-e-20260916.md` | Evidence extract `dbfe89c3…` |
| OWNER-RO-7BOARD-P0P6-MAP-20260916.md | Fleet topology `a15a86bc…` |
| OWNER-RO-DIR-ARCH-E-20260916.md | Directory map `a2c18264…` |

**ARCH standing:** map sealed · idle unless COMMANDER assigns next RO.
