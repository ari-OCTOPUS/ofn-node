# 🐙 TELEGRAM DEEP SCAN — Octopus Sync Handoff Report

> **تاریخ:** 2026-07-17
> **هدف:** نقشه کامل تمام ربات‌ها، دکمه‌ها، پل‌های ارتباطی و سیم‌کشی‌های تلگرام برای agent ای که می‌خواد سیستم جدید رو sync کنه.
> **محدوده:** `F:\backup` (کل مخزن)

---

## ⚡ TL;DR — خلاصه اجرایی

این سیستم **dual-bot architecture** داره با **۹ ربات تلگرامی مجزا** (اما فقط ۶ تا فعال)، **~۱۵۰ دکمه اینلاین** و **~۸۰ دستور اسلش**. تمام ارتباط بین organ‌ها و تلگرام از طریق **فایل‌های JSON/JSONL bridge** انجام می‌شه (هیچ message broker یا DB سروری نیست).

**نکته بحرانی:** دو ربات دارن از **همان bot ID (8187434784)** با **tokenهای متفاوت** استفاده می‌کنن — این یعنی خطر `409 Conflict` اگه هر دو همزمان poll کنن.

---

## 🤖 فهرست کامل ربات‌ها (۹ ربات)

| # | نام | Bot ID | Token Env | وضعیت کد | فایل اصلی |
|---|-----|--------|-----------|----------|-----------|
| 1 | **Octopus Unified Bot** (approval channel) | `8187434784` | `TELEGRAM_BOT_TOKEN` (.env:21) | ✅ فعال | `_ops/budget/approval_channel.py` |
| 2 | **TG Center Bot** (command center) | `7992324219` | `TG_CENTER_BOT_TOKEN` (OCTOPUS-flags.cmd:111) | ✅ فعال | `_ops/telegram_center/center.py` |
| 3 | **Ziman Studio Bot** ("مامان") | `8861821707` | `TG_ZIMAN_STUDIO_BOT_TOKEN` (.env:24) | ⚠️ توقف — کد مصرف‌کننده پیدا نشد | (دوران تجاری؟) |
| 4 | **Saba Bot** | `8928856177` | `SABA_CHAT_ID` (control-brain/.env:4 — نام گمراه‌کننده) | ❌ مرده — هیچ کد اشاره‌ای ندارد | - |
| 5 | **Painting Bot** | `8824797527` | `PAINTING_TELEGRAM_TOKEN` (control-brain/.env:8) | ✅ فعال | `_launchpad/.../painting-bot/telegram_bot.py` |
| 6 | **Accounting Bot** (Node.js) | `7992324219` | `ACCOUNTING_TELEGRAM_TOKEN` (control-brain/.env:9) | ✅ فعال | `_launchpad/.../accounting-bot/bot.js` |
| 7 | **Control Brain Bot** | `8187434784` (مشترک با #1!) | `TELEGRAM_TOKEN` (control-brain/.env:2) | ✅ فعال | `_launchpad/.../control-brain/adapters/telegram_bot.py` |
| 8 | **LangarBot** (داخل Unified) | — | از bridge میاد → `TELEGRAM_BOT_TOKEN` | ✅ فعال (embedded) | `_ops/legs/langar_bridge.py` + `03 - Projects/اونلی فنز/langar/langar_bot.py` |
| 9 | **LangarBot Standalone** | — | `TELEGRAM_LANGAR_BOT_TOKEN` (تنها در کد) | ❌ مرده — مقدار env تنظیم نشده | `langar_bot.py:313` |

---

### 🚨 تله‌های بحرانی (Critical Pitfalls)

| ریسک | توضیح | توصیه |
|------|-------|-------|
| **409 Conflict** | ربات‌های #1 (Unified) و #7 (Control Brain) هر دو از bot ID `8187434784` با tokenهای متفاوت استفاده می‌کنن. اگه هر دو همزمان `getUpdates` کنند، تلگرام یکی رو 409 می‌زنه. | فقط یکیشون رو فعال نگه دار یا token رو unify کن. کد `control-brain/adapters/telegram_bot.py:28-33` این رو با sampling 409 مدیریت می‌کنه ولی پایدار نیست. |
| **Duplicate Bot ID** | ربات‌های #2 (TG Center) و #6 (Accounting) هر دو از bot ID `7992324219` استفاده می‌کنن. | هم‌_token‌شون کن یا یکی رو بکش. |
| **نام‌های گمراه‌کننده env** | `SABA_CHAT_ID` و `MOM_CHAT_ID` در `control-brain/.env` در واقع **bot token** هستن نه chat ID. | rename کنن به `*_TOKEN`. |
| **دوگاهی token** | Unified bot دو بار تعریف شده: `.env:21` و `control-brain/.env:2`. کدوم رو revoke کردن؟ | فقط یکی canonical باشه. |

---

## 🎛 نقشه دکمه‌ها و Handler‌ها

### کانال Approval (ربات #1) — `_ops/budget/approval_channel.py`

این ربات قدیمی‌ترین و پیچیده‌ترین‌هاست: **~۱۲۰ دکمه** با ۱۰ prefix مختلف برای callback_data.

| Prefix | کاربرد | handler |
|--------|--------|---------|
| `app:<verb>:<effect_id>:<token>` | تأیید مالی (approve/deny/later) | money gate |
| `rfc:<verb>:<rfc_id>:<token>` | RFC evolution approval | `_dispatch_rfc()` |
| `menu:<page>` | ناوبری تب‌های cockpit | `_render_tab()` |
| `home:<verb>:<id>:<token>` | تصمیمات ساده yes/no | - |
| `card:<tab>:<key>` | رندر کارت جزئیات | - |
| `pg:<tab>:<key>:<n>` | ناوبری صفحات صفحه‌بندی‌شده | - |
| `act:<verb>:<key>:<token>` | اجرای اکشن cockpit (control plane) | `_dispatch_act()` → `_run_act()` |
| `rev:<verb>:<txn_id>:<...>` | گردش حساب review | `_dispatch_review()` |
| `jrn:<verb>:<txn_id>` | journal entry approve/reject | `_dispatch_books()` |
| `acct:<verb>` | میان‌برهای حسابداری | - |

**دستورات اسلش** (~۳۰+): `/start`, `/status`, `/stop`, `/resume`, `/panic`, `/budget`, `/now`, `/overview`, `/doctor`, `/money`, `/wiring`, `/health`, `/neworgan`, `/review`, `/books`, `/sync`, `/pf_*`, `/saba`, `/drafts`, `/dm_*`, `/fan_*`, `/vault_*`, `/guards`, `/kpi*`

**Dead handlers (۴ تا):** `ideas`, `school`, `ingest:crypto`, `ingest:acct` — handler کد دارن ولی دکمه UI براشون حذف شده.
**Orphan buttons:** صفر ✅ (هر دکمه‌ای تعریف شده handler داره).

---

### Telegram Center (ربات #2) — `_ops/telegram_center/center.py`

جدیدتر، سبک‌تر، **~۳۰ دکمه** با ۷ prefix:

| Prefix | کاربرد | handler |
|--------|--------|---------|
| `mn:<page>` | ناوبری منو (edit-in-place) | `_edit_page()` |
| `lg:<key>:<p\|r>` | pause/resume leg (power module) | `_handle_center_callback()` → `power.py` |
| `pw:<action>` | arm اکشن حساس (two-click) | - |
| `pwc:<action>` | تأیید اکشن حساس (کلیک دوم) | - |
| `ok:<id>` | verdict تأیید تصمیم | `_record_approval()` |
| `no:<id>` | verdict رد | - |
| `later:<id>` | verdict تعویق | - |

**دستورات:** `/menu`, `/now`, `/budget`, `/revenue`, `/start` (ثبت شده با `setMyCommands` در `center.py:96-101`)

**Topics سازماندهی شده** در سوپرگروه `-1004475788460`:

| Leg | Topic ID |
|-----|----------|
| lead | 22 |
| ziman | 23 |
| mining | 24 |
| crypto | 25 |
| accounting | 26 |
| studio_pf | 27 |
| system | 28 |
| knowledge | 29 |
| cartographer | 65 |

---

### ربات‌های پروژه‌ای (۵، ۶)

- **Painting Bot** (`_launchpad/.../painting-bot/telegram_bot.py`): `python-telegram-bot` v21. دستورات: `/help`, `/leads`, `/status`, `/score`.
- **Accounting Bot** (`_launchpad/.../accounting-bot/bot.js`): `node-telegram-bot-api`. دستورات: `/personal`, `/business` + dashboards.

---

## 🔌 مسیرهای ارسال و دریافت (Send/Receive Paths)

### Outbound (سیستم → تلگرام)

| فرستنده | فایل:خط | چه می‌فرسته |
|---------|---------|-------------|
| `TelegramApprovalChannel.send_text()` | `approval_channel.py:993` | متن + کیبورد (هر پیام خروجی این ربات) |
| `TelegramApprovalChannel.request_approval_card()` | `approval_channel.py:517` | کارت approval با ۳ دکمه |
| `TelegramApprovalChannel._answer_callback_query()` | `approval_channel.py:406` | toast پاسخ به کلیک |
| `wiring._tg_ack()` | `wiring.py:1080` | ack اجرای cockpit request |
| `wiring.needs_nudge_beat()` | `wiring.py:2017` | نوتیف "I need you" (هر ~۶ ساعت) |
| `wiring.discovery_nudge_beat()` | `wiring.py:2239` | نوتیف "N new things learned" (هر ~۸ ساعت) |
| `Center.beat()` | `center.py:359` | digest دوره‌ای هر ۵ دقیقه + pinned status edit |
| `TgClient.send/edit/pin_message/create_topic` | `tg_api.py:235/261/276/288` | تمام API call‌های TG Center |

### Inbound (تلگرام → سیستم)

| گیرنده | فایل:خط | مکانیزم |
|--------|---------|---------|
| `TelegramApprovalChannel.poll_once()` | `approval_channel.py:285` | `getUpdates` long-poll (۳۰ ثانیه) |
| `TelegramApprovalChannel.run_forever()` | `approval_channel.py:420` | حلقه اصلی، daemon thread در organism |
| `Center.run_once()` | `center.py:748` | `getUpdates` long-poll (۲۵ ثانیه) |
| `Center.run_forever()` | `center.py:780` | حلقه اصلی TG Center |

---

## 🌉 فایل‌های پل (Bridge / Queue) — قلب wiring

این فایل‌ها دو دنیای async (تلگرام و حلقه organism) رو وصل می‌کنن. **برای sync سیستم جدید، این‌ها مفصل‌های اصلی هستن.**

| فایل | نویسنده | خواننده | نقش |
|------|---------|---------|-----|
| **`state/cockpit-requests.jsonl`** | `approval_channel._append_request()` | `wiring.cockpit_requests_beat()` | 🎯 **پل اصلی**: دکمه cockpit → اجرای واقعی. cursor در `cockpit-requests.cursor`، split-brain lock در `cockpit-requests.lock`. فقط verbهای `doctor` و `consolidate` اجرا می‌شن (whitelist `_TG_EXEC_SAFE`). پشت `OCTOPUS_TG_EXEC=1`. |
| `state/telegram-offset.json` | `_save_offset()` (approval_channel:396) | `TelegramApprovalChannel.__init__()` | offset poll ربات #1 |
| `state/pulse/telegram-poll.json` | `poll_once()` (approval_channel:312) | `live/server.py` (dashboard) | heartbeat اینکه thread poll زنده‌ست |
| `state/needs-nudge.json` | `wiring.needs_nudge_beat()` (wiring:2064) | wiring خودش، dashboard، cockpit "Now" | anti-spam dedup |
| `state/telegram/center-config.json` | `Center.ensure_setup()` + `beat()` | Center | chat_id، topics map، status_message_id، last_digest، last_offset، seen، pw_arm |
| `state/telegram/approvals/*.json` + `approvals.jsonl` | `Center._record_approval()` (center:722) | `_approvals_text()` | verdictهای تصمیم |
| `state/telegram/proposals/` | `Center._persist_proposal()` (center:529) | (archival فقط) | snapshot بودجه |
| `state/telegram/power-audit.jsonl` | `power._audit()` (power.py:56) | audit | لاگ اکشن‌های power |
| `state/leg-*-paused.flag` | `power.py` (از تلگرام) | `wiring.py` | pause flag هر leg |
| `STOP-ORGANISM`, `STOP-TG-CENTER`, `HALT-ALL` | انسان / dashboard | organism، center | kill-switch |

---

## 🎬 Driver و حلقه‌های اصلی

| فرآیند | فایل ورودی | پورت | دوره |
|--------|-----------|------|------|
| **Organism main loop** | `_ops/RUN-ORGANISM.bat` → `organism.py` | 8771 (singleton lock) | tick ۳۰۰ ثانیه |
| **Cortex (مغز)** | `_ops/RUN-CORTEX.bat` → `cortex/cortex.py` | 8772 | - |
| **Live cockpit UI** | `_ops/RUN-LIVE.bat` → `live/server.py` | 8773 | - |
| **Telegram Center** | `_ops/telegram_center/RUN-TG-CENTER.bat` → `center.py` | long-poll | beat ۳۰۰ ثانیه |
| **Pacemaker** | `organism.py:299` → `chrono.start_pacemaker_thread()` | daemon thread | ۶۰ ثانیه |
| **Telegram poll thread** | `organism.py:259` → `_chan.run_forever()` (daemon) | داخل organism | پیوسته |

**ساختار داخلی organism.py:**
```
organism.py main (port 8771 singleton)
├── daemon thread: telegram-poll → TelegramApprovalChannel.run_forever()
├── daemon thread: pacemaker → chrono.run_forever() (60s)
└── while True: tick (300s)
    ├── wiring.cockpit_requests_beat()  ← consumes cockpit-requests.jsonl
    ├── wiring.needs_nudge_beat()       ← sends nudges
    ├── wiring.discovery_nudge_beat()   ← sends discoveries
    └── wiring.heartbeat_summary_beat() ← emits events (no TG send)
```

---

## 🔧 تنظیمات Env و Token

### `.env` (مسیر ریشه `F:\backup\.env`)
| خط | متغیر | مقدار | یادداشت |
|-----|-------|-------|---------|
| 21 | `TELEGRAM_BOT_TOKEN` | `8187434784:...` | ربات Unified |
| 22 | `TELEGRAM_OWNER_CHAT_ID` | `6150431610` | Armin (owner) |
| 24 | `TG_ZIMAN_STUDIO_BOT_TOKEN` | `8861821707:...` | ربات مامان |
| 25 | `TG_ZIMAN_STUDIO_ALLOWED_IDS` | `227957900,6150431610` | - |

### `_ops/OCTOPUS-flags.cmd`
| خط | متغیر | نقش |
|-----|-------|-----|
| 111 | `TG_CENTER_BOT_TOKEN` | ربات TG Center |
| 112 | `TG_CENTER_CHAT_ID` | `-1004475788460` (سوپرگروه) |
| — | `OCTOPUS_TG_EXEC=1` | فعال‌سازی اجرای cockpit requests |
| — | `OCTOPUS_WIRE_NEEDS_NUDGE=1` | فعال‌سازی ناج نودج |

### `_launchpad/second-brain-live/control-brain/.env`
| خط | متغیر | یادداشت |
|-----|-------|---------|
| 2 | `TELEGRAM_TOKEN` | ربات Control Brain (همان ID 8187434784!) |
| 4 | `SABA_CHAT_ID` | **در واقع token ربات Saba** (نام گمراه‌کننده) |
| 5 | `MOM_CHAT_ID` | **در واقع token ربات Ziman** (نام گمراه‌کننده) |
| 8 | `PAINTING_TELEGRAM_TOKEN` | ربات Painting |
| 9 | `ACCOUNTING_TELEGRAM_TOKEN` | ربات Accounting |
| 18 | `TELEGRAM_CHAT_ID=6150431610` | chat مالک |

---

## 📋 چک‌لیست sync برای agent جدید

### قبل از deploy سیستم جدید:
- [ ] **resolve تعارض bot ID 8187434784** — Unified (#1) و Control Brain (#7) نمی‌تونن همزمان poll کنن. یکی رو غیرفعال کن یا token رو unify کن.
- [ ] **resolve تعارض bot ID 7992324219** — TG Center (#2) و Accounting (#6) مشترکن.
- [ ] **rename envهای گمراه‌کننده** — `SABA_CHAT_ID` و `MOM_CHAT_ID` به `*_TOKEN`.
- [ ] **بررسی dead bots** — ربات‌های #3 (Ziman)، #4 (Saba)، #9 (Langar standalone) یا مرده‌ان یا consumer ندارن. تصمیم بگیر حذف یا وصل بشن.
- [ ] **backup از state files** قبل از migration: `cockpit-requests.jsonl`، `telegram-offset.json`، `center-config.json`، `needs-nudge.json`.

### هنگام deploy:
- [ ] **پل cockpit-requests.jsonl رو حفظ کن** — این رابط اصلی بین تلگرام و اجرای واقعیه. schema: `{"ts","verb","key","source":"telegram-cockpit","status":"requested"}`.
- [ ] **whitelist `_TG_EXEC_SAFE` رو update کن** اگه verbهای جدید اضافه می‌کنی (فعلاً فقط `doctor` و `consolidate`).
- [ ] **offset persistence** رو حفظ کن (`telegram-offset.json` برای ربات #1، `center-config.json:last_offset` برای ربات #2) — بدون این، restart باعث replay duplicate می‌شه.
- [ ] **allowlist gating** رو حفظ کن — فقط `6150431610` (owner) + `TELEGRAM_ALLOWED_CHAT_IDS` مجازن.
- [ ] **kill-switch files** رو شناخته داشته باش: `STOP-ORGANISM`، `STOP-TG-CENTER`، `HALT-ALL`.
- [ ] **topic IDs** (`22,23,...,65`) رو در `center-config.json` بازنویسی نکن — تلگرام اون‌ها رو ثابت نگه می‌داره.

### بعد از deploy:
- [ ] تست `poll_once()` زنده‌ست: چک `state/pulse/telegram-poll.json` باید ts تازه داشته باشه.
- [ ] تست دکمه‌ها از تلگرام: هر prefix callback (`app:`, `act:`, `mn:`, `lg:`, `ok:`) رو دستی امتحان کن.
- [ ] تست bridge: یک دکمه `act:doctor:run` بزن و ببین تو `cockpit-requests.jsonl` اضافه می‌شه و تو tick بعد اجرا می‌شه.
- [ ] no 409 conflict: log هر دو ربات poll‌کننده رو چک کن.

---

## 📂 فایل‌های کلیدی (مرجع سریع)

| نقش | فایل |
|-----|------|
| Organism main loop | `_ops/organism.py` |
| ربات Unified (approval) | `_ops/budget/approval_channel.py` |
| Wiring (پل تلگرام↔organism) | `_ops/wiring.py` |
| ربات TG Center | `_ops/telegram_center/center.py` |
| HTTP client TG Center | `_ops/telegram_center/tg_api.py` |
| رندر کارت‌های TG Center | `_ops/telegram_center/render.py` |
| کنترل power TG Center | `_ops/telegram_center/power.py` |
| Langar bridge | `_ops/legs/langar_bridge.py` |
| Pacemaker | `_ops/chrono.py` |
| Env loader | `_ops/budget/env_loader.py` |
| Flags | `_ops/OCTOPUS-flags.cmd` |
| پل cockpit queue | `_ops/state/cockpit-requests.jsonl` |
| پل offset | `_ops/state/telegram-offset.json` |
| پل center config | `_ops/state/telegram/center-config.json` |

---

*گزارش تولید شده توسط deep-scan در 2026-07-17. مبنای اسکن: کل `F:\backup` با ۴ agent کاوشگر موازی.*
