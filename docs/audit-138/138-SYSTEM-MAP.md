# 138 SYSTEM MAP (audited 2026-08-28T00:14:00Z, read-only)
- **ofn.service**: `/usr/bin/python3 -m ofn.run`, User=ari, WorkingDirectory=/home/ari/ofn. Four shells 8791(ziman)/8792(lead)/8793(studio)/8794(owner). Owner shell serves legacy `/` + **live `/cockpit-v2/`**.
- **scheduler**: `octopus-scheduler.timer` → `octopus_scheduler.py --once` every 15min (verified ExecStart).
- **bridges**: active = `octopus-bridge` (:8796, board_cp pull protocol, principals/scopes, outbound mTLS to cloud). `octopus-telegram-bridge` = inactive, no unit fragment installed — consistent with TELEGRAM_BLOCKED_CONFIG (no owner envs). Exactly **zero** Telegram pollers active.
- **owner-decision renderers**: legacy panel (web/panel.html, Telegram WebApp session) + Cockpit V2 (read-only M1; no command UI). No production Telegram card renderer exists.
- **hypno-fugu-mini** (`hypno.run`, :8895 loopback): separate product; NOT in the owner-decision path (loopback, own DBs).
- **executor**: effects flow only through `ofn/run.py` → Node callbacks → outbox (sole egress per CLAUDE.md); mesh effects via CLI/transport tools, tier-gated by action_tiers (YELLOW needs approval, RED disabled) — unit-proven in tests/test_runtime.py.
- **money ledger**: `ledger.sqlite` = audit event ledger (hash-chain verified); authoritative cash = provenance-valid payment receipts only (products/audience stores). VERIFIED_CASH = AUD 0 (audience.revenue_events=0; no valid receipts).
- **packs/DBs**: Painting→painting.sqlite (8 leads), Ziman→products.sqlite (40), Studio→studio.sqlite (24 drafts); hypno outside revenue portfolio.
