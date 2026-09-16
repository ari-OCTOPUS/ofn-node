# Board2 Painting+Lead GO + Studio unlock diagnosis — 2026-08-22

Auth: owner parallel priority + VERIFY READY_FOR_GO + Studio widget override (automation/scheduled from existing library only; no invent; no paid).

## Painting+Lead — PASS (reversible #1–#3)

### 1) Lead gap inventory (read-only from INDEX)
From INDEX «لید نقاشی — وضعیت اتصال»:
- Built: lead intake, scoring (`lead_priority`), 8 tables, rich owner dashboard, partner UI search/filter/status + quote sheet, boot partner path, HIGH-1 closed, outbox/consent for lead, quote/reply fail-closed.
- Still points to HANDOFF «لید نقاشی — شکاف‌ها» for remaining wiring details (not re-invented).
- Closed node gates still include tender/vendor/portal/terms (expected; not opened tonight).

### 2) Dry observability / outbox counts
- Legs healthz: ziman/lead/studio/panel all **200**
- `outbox.sqlite`: **2** rows, tenant=`lead`, status=`manual_completed` only (no pending/approved waiting)
- Owner observability endpoints require auth (401 without session) — expected fail-closed

### 3) Public catalog response-shape
- Flag `OFN_PUBLIC_CATALOG=1` / `public_catalog_enabled=true`
- With Host header, `GET /api/v1/public/catalog` → **200**:
```json
{"ok": true, "items": [
  {"sku":"ZM-0003","name":"ظرف آزمایشی","description":null,"price_primary_aud":22.0},
  {"sku":"ZM-0006","name":"ظرف آزمایشی","description":null,"price_primary_aud":22.0}
], "count": 2, "activated": false}
```
- Note: SKUs are ZM-* (GiftMesh/ziman catalog surface) even when Host is lead/panel/studio — documented shape, `activated: false`
- Without Host: `{"error":"unknown host"}` 404

## Studio/OF override — BLOCKED for live scheduled posts

Owner allows automation + scheduled posts from **existing library only**. Library exists:
- **66** media files under photos root, e.g. `studio/shot-0016|0017|0002|0005|0022/...` (jpg sizes recorded in RESULT)

### Why publish still locked (exact)
| Layer | State | File / env |
|---|---|---|
| `OFN_WIRE_OUTBOUND` | **0** | `node.env` |
| `wire_outbound` in `OFN_EXTRA_CLOSED_GATES` | **yes** | `node.env` |
| `live_publish` token | open (not in EXTRA) | EXTRA list |
| `OFN_WIRE_PUBLISH` | 1 | `node.env` |
| `secret_rotation` | **closed** (auto after `GATE_OPEN_UNTIL_UTC=2026-08-17`) | `ofn/config.py` |
| `partner_precondition` | **closed** (same expiry) | `ofn/config.py` |
| Owner two-step | required for real publish | `ofn/kernel/release_switch.py` (`RULE_OWNER_TWO_STEP`) |
| Transport | `sender_dryrun` has **no `send()`** — only `dry_run_diff()` until all gates green | `ofn/adapters/sender_dryrun.py` |

Conclusion: unlocking only `wire_outbound` is **insufficient**. Live schedule/post still blocked by `secret_rotation` + `partner_precondition` + owner two-step + missing send path until release context is green.

### Proposed unlock package (NOT executed — needs explicit ari/owner ack on secrets/partner)
1. Rotate CRITICAL secrets per runbook (or confirm already done) then `OFN_KEEP_GATES_OPEN=1`
2. Drop `wire_outbound` from `OFN_EXTRA_CLOSED_GATES`; set `OFN_WIRE_OUTBOUND=1`
3. Keep `auto_post`/`auto_dm`/`auto_email` **closed** (no blast)
4. Record partner_precondition per INDEX
5. Queue from existing `studio/shot-*` only + owner two-step; never invent captions/assets

Until that package is authorized, Studio action tonight = **inventory only** (no posts queued as live).

## ziman
Remains GiftMesh Sydney brand (not Master Painting). healthz 200; no mutate.

## READY / results
- Painting+Lead GO #1–#3: **PASS**
- Studio scheduled-from-library live: **BLOCKED** (gates above)
- No paid spend, no invent content, no customer blast