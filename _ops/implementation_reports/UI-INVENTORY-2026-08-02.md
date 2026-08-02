---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, ui, inventory, miniapp, telegram, registry]
created: 2026-08-02
updated: 2026-08-02
method: git ls-files (lightweight, no F:\backup recursive scan)
---

# UI Inventory — Octopus (2026-08-02)

> منبع: `git ls-files` (۶۵۶۸ فایلِ tracked، بدونِ scan سنگین). هر وضعیت با evidence.
> هرگز `unknown` را `live` گزارش نکن.

## ۱. Telegram commands (live بعد از restart)

| command | status | owner_visible | فایل:نقش |
|---|---|---|---|
| `/ops` | live (flag-on) | yes | `telegram_center/center.py:2554` → `agi2027_control.integration.try_handle_control` |
| `/outbound status` | live (flag-on) | yes | `agi2027_control/runtime.py` ControlPlane.handle |
| `/outbound recover` | live | yes | ControlPlane → OutboundWriteAheadLedger.recover_pending |
| `/outbound mark-sent/cancel/retry <id>` | live | yes | ControlPlane._outbound_resolve |
| `/repair list/plan/execute/rollback` | live | yes | ControlPlane |
| `/impact <leg>` | live | yes | ControlPlane → AdaptiveValueLedger.score |
| `/now` | live (passthrough) | yes | `center.py` standard handler |
| `/ui` `/open` `/truth` `/legs` `/approvals` | **staged** (نه‌ساخته) | — | Phase 6 |

## ۲. MiniApp / gateway

| مورد | status | evidence |
|---|---|---|
| gateway HTTP server | **live (code-ready)** | `telegram_center/miniapp_gateway.py:230` (`MiniappGateway(HTTPServer)`، port از env) |
| route `/` (index) | live (proxied) | `_handle_core` fetch از `_default_fetch` |
| route `/api/miniapp` | live (proxied) | `_handle_core` → upstream fetch |
| route `/api/state` `/api/outbound` ... | **missing** | ساخته‌نشده — Phase 4 |
| frontend `miniapp/index.html` `app.js` `style.css` | **missing** | `telegram_center/miniapp/` وجود ندارد — Phase 5 |
| Telegram initData auth | live (code-ready) | `validate_init_data` HMAC (line 85) |
| tunnel (cloudflared) | staged | `run-miniapp-tunnel.ps1` موجود |
| public URL (`OCTOPUS_MINIAPP_URL`) | **CONFIG_NEEDED** | env فعلاً set نشده |

## ۳. render / card / status views

| فایل | role | status |
|---|---|---|
| `telegram_center/render.py` | canonical leg/card render → Telegram + dashboard | live |
| `telegram_center/center.py` beat status pin | `center-status` pinned message | live |
| `legs/mining_card.py` `mining_swap_card.py` | mining cards | live |
| `chord/adapters/telegram_cards.py` | chord cards | live |
| `outcomes/pending_card_recovery.py` | pending money/rfc card recovery | live |
| `legs/budget_frustration.py` | CLI report (frustration index) | staged (CLI، نه wired به TG) |
| `legs/organism_syndrome.py` | CLI report (cross-leg syndrome) | staged |
| `tests/test_audit.py` | CLI report (green-lie) | staged |

## ۴. dashboard / doctor / status

| فایل/مفهوم | role | status |
|---|---|---|
| `dashboard/` dir | (legacy/uncertain) | unknown |
| `doctor/` | doctor reports/cards | live (via doctor_link) |
| `organism.py` ORGANISM-STATE aggregate | single status source | live |
| `wiring.py business_legs_beat` | legs heartbeat → ORGANISM-STATE.business_legs | live |

## ۵. Obsidian truth

| فایل | role | status |
|---|---|---|
| `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` | current truth snapshot | live |
| `01 - Dashboard/HANDOFF.md` | session handoff | live |
| `00 - Inbox/SESSION-NOTES-2026-08-02.md` | today's session note | live |
| `_memory/EXPERIENCE-LEDGER.md` | lessons ledger | live |
| `_memory/HEARTBEAT.md` | fleet heartbeat (organism output) | live |

## ۶. UI Registry

| مورد | status |
|---|---|
| `_ops/agi2027_runtime/ui-registry.json` | **missing** — ساخته‌شده در Phase 3 |

## ریسک‌ها
- MiniApp اگر public شود بدونِ owner-gate، نشتِ data. → auth اجباری.
- `dashboard/` legacy نامشخص است — قبل از وصل‌کردن باید audit شود.
- frontend فعلاً صفر است — ساختنِ کامل از Phase 5.

## پیشنهاد serve برای MiniApp
۱. gateway روی port (env) با `index.html` از `miniapp/`.
۲. `/api/*` از helperهای Phase 4.
۳. auth: initData HMAC با `TG_CENTER_BOT_TOKEN` + owner_id match.
۴. public URL فقط بعد از auth-config، از طریق cloudflared tunnel.

## نباید fake-green شود
- `dashboard/` = unknown.
- public MiniApp URL = CONFIG_NEEDED.
- `/api/state` endpoints = missing تا Phase 4.
- frontend = missing تا Phase 5.
