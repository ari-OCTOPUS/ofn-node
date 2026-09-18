# P6 measure fold (ARCH · 2026-09-15)

**matrix:** `P6/ACCEPTANCE-MATRIX.json` sha `5de63c27613822d5f6cacfcc32e65bafd81887d15ef499d0eb04697a7446d938`  
**design:** `4dea6030…` · **SEC:** `9cd862ef…` · **align:** `b9b11af9…`  
**bus:** `jsonl_138` · `nats_durability=NOT_CLAIMED` · jetstream_consumers=0  
**overall:** **OPEN** (STOP for QA) · HOLD customer_send

## Row status

| ID | status | witness sha (prefix) | notes |
|----|--------|----------------------|-------|
| PB-1 | **IN_PROGRESS** | `c5753aad…` | watch `started_at=2026-09-15T04:03:36Z` · wall_clock_hours=0 · **no early 24h PASS** |
| PB-2 | **PASS** | `dde89381…` | kill mid-lease on 100 · UNKNOWN · side_effects=0 |
| PB-3 | **PASS** | `a01027b6…` | reverify P3 9/9 · RPO/RTO from addendum |
| PB-4 | **NOT_RUN** | `845e0c3c…` | no retrieval A/B harness — honest |
| PB-5 | **PASS** | `d2ca81a1…` | T2 fold · DENY usable-42 · 138 NOT_RUN retained |
| PB-6 | **PASS** | `7cfd9a14…` | 7-row fixed denominator · 193 ≠ T3 service |

## Schema note

PC matrix includes additive control fields (`bus`, `controls`, `blockers`, …). Core `acceptance_matrix.v1` rows present. QA may require strict schema validate or schema widen — ARCH does not invent PASS.

## Next

QA seal. PB-1 remains IN_PROGRESS until ≥24.0h. No laptop-free / durable fleet claim. ARCH idle.
