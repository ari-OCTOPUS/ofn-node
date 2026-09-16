---
tags: [octopus, owner-brief, laptop-agent, decision-table, node-pack, connector-gap, 2026-08-22]
date: 2026-08-22
timezone: Australia/Sydney
status: OWNER_BRIEF_ACTIVE
audience: laptop-agent
SoT: F:\backup
---

# OWNER BRIEF — Laptop Agent (OCTOPUS)

**Written (AEST):** 2026-08-22 ~23:05 Australia/Sydney  
**Role:** Source of Truth on `F:\backup`. Produce ADR / NODE-PACK / CONNECTOR-GAP artifacts.  
**Parallel tracks (do not divert):** Board2 marketing + Orange Pi (sensoriom).  
**Do not divert into:** physical e-stop purchases, mining, WAVE0 actuator unlock.

Evidence package: `F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22\`  
Obsidian: `F:\backup\07 - Knowledge\octopus\93-LAPTOP-AGENT-OWNER-BRIEF.md`

---

## 1) Canonical businesses (do not invent)

| # | Business | People | Board2 lane | Status |
|---|---|---|---|---|
| 1 | **Master Painting** (building painting, Sydney) | owner + Abbas | `lead` — `lead.master-painting.com` :8792 | LIVE |
| 2 | **Ziman** (personalized / handmade gifts) | Maliheh | `ziman` — `ziman.master-painting.com` :8791 (GiftMesh) | LIVE |
| 3 | **Studio / OnlyFans** | Saba | `studio` — `studio.master-painting.com` + `app.*` :8793 | LIVE (library-only posts) |
| 4 | **Mining** | — | — | **SEPARATE; DEFERRED — do not work** |

If anyone says “four businesses,” the fourth is Mining and it stays **off**. Three live brands only.  
Canonical map: `07 - Knowledge\octopus\01-BUSINESS-MAP-CANONICAL.md`

---

## 2) Decision table (signable — ADOPT these)

| Domain | Decision | Execution condition |
|---|---|---|
| **Similarweb Premium Connector** | **ADOPT** | Estimates only: label `estimate` + register `evidence_id` + `captured_at` (+ required: `confidence` + `valid_for`) |
| **GA4 / GSC / Ads** | **GAP** | Until OAuth + owner signature: record only as `CONNECTOR-GAP` — no invent metrics |
| **Telegram Mini App** | **ADOPT (Read-Only First)** | Same primary state machine; **parallel path forbidden** |
| **Telegram Payment** | **TRIAL (limited)** | One business only + real auditable receipt |
| **Three-node messaging** | **TRIAL (JetStream)** | Inbox/Outbox + idempotency first; JetStream only with pass criteria below |
| **Sensorium Governance** | **ADOPT Shared Policy** | Shared allowlist/policy; **separate namespaces** |

### Why this lock

- Keeps three-model consensus; closes dual-source-of-truth risk.
- Compatible with owner gates **D1 / D7**; no early irreversible action.
- JetStream neither forced early nor deferred forever — measurable TRIAL with rollback.
- Preserves the core rule: **runtime evidence > claim/document**.

---

## 3) Evidence-first rules (non-negotiable)

1. **Runtime evidence > claim/document.** Narrative alone is not PASS.
2. Any datum missing valid `evidence_id` or `source_type` → auto-classified **`unverified`**.
3. Evidence Store for Similarweb (and any estimate): **`confidence` + `valid_for` required** (prevent downstream overfit).
4. Owner gates **D1 / D7** bind; no early irreversible action.
5. **One SoT** on `F:\backup` — dual sources of truth forbidden.
6. External research is **connector-first** only (Similarweb Premium, Statista, CB Insights, Finance, …). No invented numbers; estimate + evidence only.
7. Do **not** invent PASS for CHG/MQTT/WAVE0/hardware.

---

## 4) JetStream TRIAL pass criteria

Promote JetStream only when **all** hold:

1. At least **two real independent consumers** need replay.
2. Laptop-offline scenario would drop events and Inbox/Outbox is **not** enough.
3. Duplicate handling with `idempotency_key` is tested.
4. Rollback is documented **and** tested (disable JetStream without breaking flow).

Until then: Inbox/Outbox + idempotency remains the default path.

---

## 5) Tonight live state (build on this; do not re-litigate)

| Item | Honest state | Notes / evidence |
|---|---|---|
| Inet feeds Phase A | **PASS** | Expand **7/7**: OPENMETEO, AQI, TIME, FX-AUD, BOM-SYD, NEWS-AU Guardian, USGS-QUAKE; timer **15m**; ABC skipped 500 |
| ESP32 Phase B | **DEFERRED** | Wait for hardware; no invent UART/pins |
| Physical e-stop buy | **LATER** | Knowledge `91` / PARTS-LIST deferred; Path H still `BLOCKED_NEED_ESTOP` |
| WAVE0 hardware | **KEEP_LOCKED** | Deferring buy does **not** unlock |
| MQTT 1883 | **PARKED / CLOSED** | Enable ABD may exist; listener not open — no invent PASS |
| Studio | Consent + one-item **shot-0001** Telegram publish **PASS** | `BOARD2-STUDIO-CONSENT-RELEASE-2026-08-22`, `BOARD2-STUDIO-PUBLISH-DRAIN-2026-08-22` |
| Ziman | Public catalog **`activated=true`** | `BOARD2-ZIMAN-ACTIVATE-LEAD-CAMPAIGN-2026-08-22` |
| Lead / Painting | Live campaign on **existing 8 CRM leads** running | same evidence folder |
| Season SoT | Rollup + CURRENT-TRUTH | `90-SEASON-ROLLUP-2026-08-22.md`; `OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\` |

---

## 6) Required outputs (produce now)

1. **ADR** — decisions table above + evidence-first principles + JetStream pass criteria.
2. **Three NODE-PACK schemas** (inventory + hash each separately):
   - Business Node
   - Sensorium Node
   - Laptop Node  
   Final synthesis **only after all three** packs are received/hashed. Order: **Business → Sensorium → Laptop**.
3. **CONNECTOR-GAP registry** with standard statuses (must include **GA4 / GSC / Ads** as GAP until OAuth+owner sign).
4. External research only via approved connectors; every figure tagged estimate+evidence.

Suggested evidence landing (under this package or sibling folders you create with receipts):

- `ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md` (+ `.json` if used)
- `NODE-PACK-BUSINESS.schema.json` / `NODE-PACK-SENSORIUM.schema.json` / `NODE-PACK-LAPTOP.schema.json`
- `CONNECTOR-GAP-REGISTRY.md` (+ `.json`)

---

## 7) Explicit non-actions (forbidden)

- Mining work
- Unlock WAVE0 actuators / invent PWM / GPIO / pin maps
- Forge consent
- Paid spend without owner GO
- Scrape paywalls
- Parallel Telegram Mini App path (must stay on primary RO-first state machine)
- `git add -A`, export/rewrite keys, remove `.git/index.lock`
- Invent PASS for MQTT / WAVE0 hardware / CHG-E full cutover

---

## 8) Read order

1. This OWNER-BRIEF
2. `01-BUSINESS-MAP-CANONICAL.md`
3. `90-SEASON-ROLLUP-2026-08-22.md`
4. `92-ESP32-INET-DATA-FIRST-STRATEGY.md`
5. `06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md`
6. Board2 evidence folders for Studio / Ziman / Lead as listed above

When ADR + CONNECTOR-GAP registry + three NODE-PACKs are ready, return absolute paths to ari.

---

## Cross-links

- Obsidian: [[93-LAPTOP-AGENT-OWNER-BRIEF]]
- Business map: [[01-BUSINESS-MAP-CANONICAL]]
- Season: [[90-SEASON-ROLLUP-2026-08-22]]
- ESP32 strategy: [[92-ESP32-INET-DATA-FIRST-STRATEGY]]