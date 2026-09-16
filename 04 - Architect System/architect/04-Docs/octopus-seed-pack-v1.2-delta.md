---
pack_id: octopus_seed_pack_v1_2_delta
created: 2026-08-08
parent_pack: octopus_seed_pack_v1_1_delta
ingestion_target: vault_whole (tag: source:octopus_seed_pack_v1_2)
trust_tier: founder-verified
---

# SEED PACK v1.2 — DELTA (Owner-Cockpit Stack COMPLETE)

## [memory_type:trace] Owner-Cockpit Stack COMPLETE (2026-08-08)

8/8 WP done, 64 tests green, `_ops/owner_cockpit/` directory created.
- WP1: fugu_proxy.py (port 8787) + usage normalizer (model + orchestration tokens)
- WP2: otel_setup.py (JSON-lines spans, no SDK dep)
- WP3: db.py (4 tables, hash-chained audit ledger, tamper detection)
- WP4: owner_api.py (port 8788) + HMAC initData (official Telegram algorithm)
- WP5: approval consume-once + payload_hash tamper check
- WP6: miniapp/index.html (5 tabs, RTL, dark theme, auto-login)
- WP7: README + smoke checklist

Pricing VERIFIED from console.sakana.ai (2026-08-08):
- $5/1M input, $30/1M output, $0.50/1M cached (standard)
- $10/$45/$1.00 for context >272K
- Orchestration tokens tracked separately (Fugu-specific)

ADR: fugu_quota (attempt-based circuit breaker) vs provider_usage (token/cost
financial tracking) — reconciled: circuit breaker = gate, usage = ledger.
Not conflicting, complementary roles.

## [memory_type:fact] VERIFICATION RESULTS (2026-08-08)

| Check | Result |
|---|---|
| No duplicate implementations | ✅ single _ops/owner_cockpit/ |
| Flag OFF = zero effect | ✅ all None/False |
| HMAC logic | ✅ bad_hash/stale/empty rejected |
| Audit chain tamper | ✅ detected at tampered id |
| CRLF | ✅ all .py files LF |
| Secret scan | ✅ only mock tokens in tests |
| Live $0.10 call | ⏳ PENDING (FUGU_API_KEY not in env) |

## [memory_type:policy] OPEN ITEMS

1. Go-live checklist: 6/7 green, 1 pending (live Fugu call with real API key)
2. BotFather registration: Web App URL not yet set
3. Tunnel: cloudflared not yet configured for port 8788
4. approval_items table: schema exists in db.py but not yet populated by
   model_router (needs wiring in future WP)
