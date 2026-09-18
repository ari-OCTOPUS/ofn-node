---
type: design
lane: Q-QUALITY-SWARM-20260908
created: 2026-09-08
status: draft_only
code_executed: false
gap_id_requested: GAP-015
---

# GAP-015 — draft path for one ESP32 `board_events` (zero code run)

## Identity of the gap (do not collapse IDs)

| ID | What it is | Source | Relation to this draft |
|---|---|---|---|
| Prompt `GAP-015` | board_events / first ESP32 | this session prompt | requested |
| `GAP-LEDGER.md` 64-gap row | not found in this vault | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/SEASON-LOG.md` Round 20: generated `.md` reached here; **code stranded on cloud host, no PR** | **ledger row absent** → cannot PASS |
| SCAN-B item 18 | `board_events`: HMAC+SQLite contract, no producer/consumer on main, tests only | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/SCAN-B-REPO-MEMORY-SYSTEMS-2026-09-03.md` item 18 | nearest measured gap |
| `G-15` in CONCEPT-CODE-GAP | **Shadow mode** (different concept) | `07-HANDOFF/wave1-pack/CONCEPT-CODE-GAP.csv` line G-15 | **not** board_events |
| B-01 / B-02 | Edge envelope + board identity absent | same CSV; `07-HANDOFF/wave1-pack/EDGE-CONTRACT.md` | envelope this draft uses |

`verify_status` for prompt-GAP-015: **UNVALIDATED**. No same-domain PASS.

## Target board (not powered)

Owner has **not** named a first ESP32. This draft is a **template** keyed to skeleton slot `ESP-001` **without** authorizing power-on.

`powered_on` in roll-call: `false`.  
`first_esp32`: `OWNER_DECISION`.

## Event path (L-OBSERVE only)

Envelope fields from `EDGE-CONTRACT.md` (minimum a constrained board must send):

`board_id` · `firmware_hash` · `event_id` · `sequence` · `emitted_at` · `payload` · `may_authorize: false` · `applied: false`

Core fills `run_id` and `parent_event_id`. The board must not self-attach to a run.

### Sequence (design, not executed)

1. **Power** — owner only; not this lane. Blocked until OWNER_DECISION names the unit.
2. **Firmware identity** — `firmware_hash` allowlisted; unknown hash = deny (`EDGE-CONTRACT` fail-closed). O-3 (C3 vs S3) is still owner (`CONCEPT-CODE-GAP` B-04 `gate=owner`). This path therefore stays **Orange-Pi-first in policy**; ESP32 firmware contract is not decided.
3. **Payload** — `payload.schema = observation.v1` **or** PARSE_DRIFT. Existing parser (`_ops/observatory/observation_v1.py`) accepts USGS geojson or HN list only. A GPIO/serial sample is **not** a valid `observation.v1` today. The first legal synthetic payload for tests is therefore a **valid USGS-shaped body**, not a fake pin map.
4. **Ingress** — one in-process consumer: validate envelope → append `board_events` (HMAC+SQLite as SCAN-B describes) → **no** organism decision (`feeds_organism_decision: false`, matching `observation_v1.parse_body`).
5. **Caps** — per-board rate cap (`EDGE-CONTRACT` + B-06). Overflow → `BUFFER_OVERFLOW` event, drop oldest, do not halt the whole host.
6. **Never** — `L-NEVER`: no ledger write of money, no gate open, no `may_authorize: true`.

```
ESP32 (off) --[owner power]--> firmware_hash allowlist
        --> emit Envelope {L-OBSERVE, may_authorize:false, applied:false}
        --> parse payload as observation.v1 | PARSE_DRIFT
        --> board_events append (HMAC+SQLite)
        --> no organism decision, no GPIO invention
```

## Preconditions still open

| Precondition | Status | Source |
|---|---|---|
| H1 idempotency (one verdict ≠ N executions) | G-05 defect-open | CONCEPT-CODE-GAP |
| O-3 ESP32 C3/S3 | owner | B-04 |
| COUNTER-SOURCE-MAP (agent 2) | **not in vault this session** | grep 09-LANES / 06-EVIDENCE: zero files |
| GAP-LEDGER.jsonl / GAP-LEDGER.md | not in vault | SEASON-LOG Round 20 |
| Physical ESP32 | owner-stated off | Hardware Registry |

Zero code was executed for this design file.
