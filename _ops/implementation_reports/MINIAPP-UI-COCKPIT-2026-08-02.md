---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, miniapp, ui, cockpit, telegram]
created: 2026-08-02
updated: 2026-08-02
---

# MiniApp / UI Cockpit — Status Report (2026-08-02)

## چه ساخته شد

### Backend (read-only helpers + gateway wiring)
- **`_ops/telegram_center/miniapp_state.py`** — ۷ helper فقط‌خواندنی:
  `get_miniapp_state`، `get_outbound_state`، `get_approvals_state`، `get_legs_state`،
  `get_value_state`، `get_ui_registry`، `get_current_truth`. + `dispatch_api` برای gateway.
  - secret-scrubbed (token/email/key pattern)، fail-closed، JSON-safe.
- **`_ops/telegram_center/miniapp_gateway.py`** — additive patch: ۶ routeی `/api/*`
  جدید به gateway وصل شد (read-only، صفر POST/PUT/DELETE).

### Frontend (read-only dashboard)
- **`_ops/telegram_center/miniapp/index.html`** + **`app.js`** + **`style.css`** —
  داشبورد فقط‌خواندنی با ۷ تب: Home/Outbound/Approvals/Legs/Value/UI-Registry/Truth.
  - dev mode وقتی Telegram.WebApp غایب. actionها disabled.
  - صفر secret در frontend.

### Telegram commands (read-only)
- **`/ui` `/open`** — launcher؛ graceful `CONFIG_NEEDED` وقتی OCTOPUS_MINIAPP_URL غایب.
- **`/truth` `/legs` `/approvals`** — read-only.
- regression حفظ: `/ops` `/outbound status` `/now` (passthrough) همچنان کار می‌کنند.

## UI inventory / registry
- Inventory: `_ops/implementation_reports/UI-INVENTORY-2026-08-02.md`
- Registry: `_ops/agi2027_runtime/ui-registry.json` (۱۷ item: ۹ live، ۶ staged، ۱ unknown)

## API/helpers
- GET /api/state, /api/outbound, /api/approvals, /api/legs, /api/value, /api/ui-registry, /api/current-truth
- همگی secret-scrubbed + fail-closed.

## Auth status
- **`BLOCKED_NEEDS_AUTH_CONFIG`** برای actionها. `OCTOPUS_MINIAPP_URL`،
  `TG_CENTER_BOT_TOKEN`، `TELEGRAM_OWNER_CHAT_ID` در env فعلاً set نشده‌اند.
- read-only endpoints اگر public شوند، نشتِ data ندارند (scrub دو-لایه)، ولی
  actionها تا owner-gate آماده نشود، فعال نمی‌شوند.

## Action status
- **PHASE 7 = BLOCKED** — هیچ action endpointی ساخته نشد. (`/outbound mark-sent` و
  امثالش فقط از مسیرِ Telegram `ControlPlane` با owner-gate کار می‌کنند، نه از HTTP.)

## Tests
- `test_miniapp_state.py` — ۷/۷ سبز (scrub، fail-closed، unknown-not-fake، ۴۰۴، JSON-safe).
- Regression کامل: agi2027_control 23 + parity 13 + miniapp 7 + sync 10 + transport 17 + tg_center 39 = **۱۰۹ تست سبز**.
- `run_all.py` registration: ✅.

## Commits (scoped)
- `fdf4f62` update Octopus memory and agent handoff (PHASE 1)
- (commit 2) inventory Octopus UIs and add UI registry (PHASE 2+3)
- (commit 3) add Telegram MiniApp cockpit read-only surface (PHASE 4+5+6+9)
- (commit 4) document MiniApp cockpit status (PHASE 10)

## Remaining boundaries (صادقانه)
- **public MiniApp URL = CONFIG_NEEDED** (`OCTOPUS_MINIAPP_URL`).
- **Action HTTP endpoints = BLOCKED** تا owner auth آماده شود.
- **live customer email smoke** هنوز انجام نشده.
- **Project-F** = BLOCKED (بدون credential).
- **`dashboard/` legacy** = unknown (نباید قبل از audit وصل شود).
- **`test_blackbox_and_bridge.py`** در collectionِ pytest هنگ می‌کند (`sys.exit` در
  سطحِ module) — ولی در run_all (direct-run) درست کار می‌کند. gate معتبر = run_tests.py.
