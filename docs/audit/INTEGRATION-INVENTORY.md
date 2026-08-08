# Integration Inventory

> Verified against code 2026-08-08.

| Integration | Current status (2026-08-08) | Safe mode | Notes |
|---|---:|---|---|
| Telegram Owner Bot | ✅ Configured | approval/read | `OFN_BOT_TOKEN_OWNER` + `OFN_OWNER_USER_IDS` populated; owner allowlist active |
| Telegram Lead Bot | ✅ FIXED — allowlist populated | partner CRM | Previously "locked" — `OFN_PARTNER_USER_IDS_LEAD` now set. ⚠️ However, partner CRM UI (`refreshLeadCrm` in lead.html) is NOT called in `boot()` — see AUDIT-2026-08-08 HIGH-1. |
| Instagram | ⚠️ ABSENT — no adapter | — | No read-only audit adapter exists. Only a "planned" row in `painting_source_registry.json`. Previous doc's "read-only first" was an intent, not wiring. |
| Google Business Profile | ⚠️ ABSENT — no adapter | — | Same as Instagram: planned in registry, no code. |
| Cloudflared tunnel | ✅ Configured | routes only | `config.yml` maps panel/ziman/lead/studio/app/hypno. Does NOT route port 8090 (backup server) — good. |
| Email | ⚠️ DEAD FLAG | blocked | `OFN_WIRE_EMAIL=1` in node.env but **no code reads it**. Email is off because the flag is ignored + wire_outbound=False, not because the flag works. |
| Publish | ⚠️ DEAD FLAG | blocked | `OFN_WIRE_PUBLISH=1` in node.env but **no code reads it**. Publish is off via hardcoded `"off"` at `node.py:842` + OwnerRelease. |
| B2B directories | ✅ Planned registry | research only | 44 sources in `painting_source_registry.json`; all `read_only_first` + `approval_required` |
| Tender portals | ✅ Planned registry | alert only | No submit automation (`lead_store.py:924` blocks) |
| Kill switch | ✅ NEW (2026-08-08) | panic button | `POST /api/v1/owner/kill` (engage), `/release` (two-step) |
| Board metrics | ✅ NEW (2026-08-08) | read-only | `GET /api/v1/owner/metrics` — temp/RAM/load/disk |
| Alert notifier | ✅ NEW (2026-08-08) | log + opt-in | `OFN_ALERT_TELEGRAM=1` enables Telegram (default off); log always |
