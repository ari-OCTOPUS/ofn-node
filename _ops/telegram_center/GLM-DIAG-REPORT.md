# 🐙 GLM-DIAG-REPORT — فاز A

- **تاریخ:** 2026-07-18
- **نقش:** مهندس ارشد تکمیل و دیباگ مقر فرماندهیِ تلگرام
- **محدوده:** `F:\backup\_ops\telegram_center` + پل با `F:\backup\_octopus`
- **مبنای ادامه:** `GLM-LIVE-BUTTONS-HANDOFF.md` (ایجنت قبلی)

---

## ۱. نتیجهٔ تست‌ها (قبل از هر تغییری)

| تست | تعداد | وضعیت |
|-----|------:|------:|
| `test_tg_render.py` | 14 | ✅ سبز |
| `test_tg_center.py` | 14 | ✅ سبز |
| `test_tg_power.py` | 12 | ✅ سبز |
| `test_tg_api.py`    | 16 | ✅ سبز |
| **جمع** | **56** | ✅ **همه سبز** |

**نتیجه:** ایجنت قبلی ناوبری context-aware منو، intent کلیدواژه‌ای، دکمه‌های pause/resume، دوکلیک power، containment و fail-soft را درست پیاده کرده. **هیچ تست شکست‌خورده‌ای نیست** — نباید چیز سالم را دوباره ساخت.

---

## ۲. وضعیت Wiring (با env واقعی، بدون leak)

بررسی زنده با `env_loader.load_env()` (مثل `center.py`):

| سیگنال | مقدار | ارزیابی |
|--------|-------|---------|
| `TG_CENTER_BOT_TOKEN` | set، ۴۶ نویسه | ✅ باتِ مرکزِ مستقل |
| `TELEGRAM_BOT_TOKEN`  | set، ۴۶ نویسه | ✅ باتِ approval_channel |
| `TELEGRAM_OWNER_CHAT_ID` | `6150431610` | ✅ مالک پیکربندی‌شده |
| `TG_CENTER_CHAT_ID` | `-1004475788460` | ✅ سوپرگروهِ مرکز |
| `TgClient.wired()` | `True` | ✅ لوله وصل |
| `STOP-TG-CENTER` | غایب | ✅ حلقه می‌تواند بدود |
| `STOP-ORGANISM` | غایب | ✅ |
| `HALT-ALL` | غایب | ✅ |
| `RESTART-REQUESTED` | غایب | ✅ |
| `master_halted()` | `None` | ✅ |

---

## ۳. یافتهٔ حیاتی: ریسک 409 Conflict

دو long-pollerِ تولیدی روی `getUpdates` وجود دارد:

1. **`_ops/budget/approval_channel.py:299`** — باتِ اصلی، token = `TELEGRAM_BOT_TOKEN`.
2. **`_ops/telegram_center/tg_api.py:328`** — باتِ مرکز، token = `TG_CENTER_BOT_TOKEN` (با fallback به `TELEGRAM_BOT_TOKEN`).

**بررسی زنده:** `TG_CENTER_BOT_TOKEN` ≠ `TELEGRAM_BOT_TOKEN` → **هر دو بات مستقل‌اند و 409 رخ نمی‌دهد**. ✅

⚠️ **اما ریسک نهفته:** اگر روزی `TG_CENTER_BOT_TOKEN` از env حذف شود، `tg_api.py:161` به `TELEGRAM_BOT_TOKEN` fallback می‌کند و با approval_channel روی همان توکن 409 می‌زند. `approval_channel.py:308` این حالت را شناسایی و alert می‌زند، ولی طرفِ مرکز بی‌صدا می‌کشد (poll_updates → `[]` بی‌صدا، بدون alert).
**توصیه:** در `tg_api.py` هنگام fallback یک alert throttled بزن (از `_alert_soft` موجود استفاده کن) و در center-config نشانی بگذار که کدام توکن در حال استفاده است.

---

## 4. دکمه‌ها و callbackها — نقشهٔ کامل

### callbackهای handle می‌شوند (`center._handle_callback`)

| verb | الگو | عمل | وضعیت |
|------|------|-----|------:|
| `mn` | `mn:<page>` | ناوبریِ درجا (edit پیام) — pages: `menu/st/qr/ap/lg/bg/rv/sy/fl` | ✅ واقعی |
| `lg` | `lg:<leg>:p\|r` | مکث/ادامهٔ تک‌پا → فایل `leg-<key>-paused.flag` (runtime، برگشت‌پذیر) | ✅ واقعی، audit |
| `pw` | `pw:<act>` | مسلح‌کردنِ اکشنِ حساس (arm با timestamp در config) | ✅ واقعی |
| `pwc` | `pwc:<act>` | تأییدِ دوکلیک (≤180s) → اجرا از `POWER_ACTIONS` | ✅ واقعی، audit |
| `ok/no/later` | `<v>:<id>` | ثبتِ verdict به approval-file + event + توکنِ HA | ✅ واقعی، audit |
| (سایر) | — | `_answer("نادیده")` | ✅ fallback |

### دکمه‌های «همیشگی» منو (render_menu) — همه واقعی

| دکمه | callback | وضعیت |
|------|----------|------:|
| 📊 وضعیت/تازه‌سازی | `mn:st` | ✅ |
| 🦵 پاها | `mn:lg` | ✅ |
| 🐙 بودجه | `mn:bg` | ✅ |
| 💰 درآمد | `mn:rv` | ✅ |
| ⚙️ سیستم | `mn:sy` | ✅ |

### دکمه‌های context-aware (اولویت) — همه واقعی و عملگرا

| شرط | دکمه | callback | وضعیت |
|------|------|----------|------:|
| quarantined>0 | ☣️ قرنطینه — رسیدگی | `mn:qr` | 🟡 صفحه فقط شمارش دارد (content-free) |
| guidance.n>0 | 🧭 تصمیم‌ها | `mn:ap` | 🟡 صفحه فقط verdictهای قدیمی (pending queue واقعی نیست) |
| awaiting>0 | 🙋 منتظر پاسخ | `mn:ap` | 🟡 همان صفحهٔ ap |
| paused>0 | ▶️ پای متوقف | `mn:lg` | ✅ واقعی |

---

## ۵. دکمه‌ها/صفحه‌های نیمه‌وصل یا show-only

1. **`mn:qr` (قرنطینه)** — فقط شمارش می‌دهد (`_quarantine_text`). item-level قرنطینه و دکمه‌های `qr:<id>:inspect/release/keep` وجود ندارند. منبعِ itemهای قرنطینه در `execution_board` روشن نیست → طبق دستور، شمارش می‌ماند.
2. **`mn:ap` (صف تأیید)** — فقط verdictهای ثبت‌شدهٔ گذشته را نشان می‌دهد (از `_ops/state/telegram/approvals/*.json`). **pending queue واقعی ندارد** (یعنی job جدیدی که منتظر تأیید انسان باشد نمی‌سازد/نشان نمی‌دهد). این همان فاز E است.
3. **`mn:map` (نقشه‌برداری)** — اصلاً وجود ندارد. کل فاز D سبز است.
4. **`mn:fl` (فلگ‌ها)** — واقعی ولی پشتِ power-gate.
5. **دکمهٔ بودجهٔ `pw:ba`** — واقعی (surgical + validated)، پشتِ power-gate.

---

## ۶. پیام آزاد — intent فعلی

`center._handle_ask` این intentها را می‌فهمد (همه فقط دکمه/کارت می‌سازند، نه اجرای مستقیم):

- `وضعیت / چطوری / الان / حالت / status` → صفحهٔ st
- `درآمد / پول / مالی / revenue` → کارت درآمد
- `بودجه / budget` → صفحهٔ bg
- `راهنما / کمک / منو / help` → منو
- `مکث / متوقف / نگه‌دار / pause / stop` → کارت `lg:<leg>:p` (نه اجرا)
- `ادامه / resume / شروع` → کارت `lg:<leg>:r` (نه اجرا)
- تشخیص پا: `lead/ziman/mining/crypto/accounting/studio_pf/knowledge/cartographer`
- ناشناخته → کارت پیشنهاد با ۵ دکمه

**نبودها:** intent `scan_metadata` (نقشه/اسکن/manifest) وجود ندارد. این فاز C/D است.

---

## ۷. لیست bugها

| # | شدت | باگ | محل |
|---|-----|-----|-----|
| 1 | 🟡 متوسط | ریسک 409 نهفته: اگر `TG_CENTER_BOT_TOKEN` حذف شود، fallback بی‌صدا به توکنِ approval_channel | `tg_api.py:161` |
| 2 | 🟢 کم | `_quarantine_text` فقط شمارش، بدون per-item | `center.py:716` |
| 3 | 🔴 فاز | صف تأیید (pending) واقعی نیست — فقط verdictهای گذشته نمایش داده می‌شود | `center.py:731` |
| 4 | 🔴 فاز | `metadata_scan` / `mn:map` اصلاً وجود ندارد | — |
| 5 | 🔴 فاز | `intent.py` به‌عنوان ماژول جدا نیست (منطق در `_handle_ask`) | `center.py:519` |
| 6 | 🟡 متوسط | هیچ alertی نمی‌رود اگر poll_updates همیشه خالی برگردد (symptomِ 409 یا token خراب) | `tg_api.py:319` |

---

## ۸. نقشهٔ فایل‌هایی که باید تغییر کنند

| فایل | تغییر | فاز |
|------|-------|-----|
| `_ops/telegram_center/intent.py` | **جدید** — `classify(text) -> dict` خالص، stdlib-only | C |
| `_ops/telegram_center/metadata_scan.py` | **جدید** — `scan_metadata/write_manifest/summarize` | D |
| `_ops/telegram_center/approval_store.py` | **جدید** — bridge `_ops/state/telegram/approvals` ↔ `_octopus/state/approvals.json` | E |
| `_ops/telegram_center/actions.py` | **جدید** — registry skeleton | F |
| `_ops/telegram_center/render.py` | افزودن `mn:map` به منو + `render_map_page` + `render_approvals_queue` | B/E |
| `_ops/telegram_center/center.py` | `_handle_ask` به `intent.classify` واگذار + `_page("map"/"ap")` واقعی + callbackهای `map:*`/`ap:ok/no/detail:*` | C/D/E |
| `_ops/telegram_center/tg_api.py` | alert throttled هنگام fallback توکن (کاهش ریسک #1) | G |
| `_ops/tests/test_tg_intent.py` | **جدید** | C |
| `_ops/tests/test_tg_metadata_scan.py` | **جدید** | D |
| `_ops/tests/test_tg_approval_store.py` | **جدید** | E |
| `_ops/tests/test_tg_render.py` | تستِ `mn:map` در منو + render_map_page | B |
| `_ops/tests/test_tg_center.py` | تستِ `map:*` و `ap:ok/no` و intent scan | C/D/E |
| `_ops/telegram_center/GLM-FINAL-REPORT.md` | **جدید** | I |

---

## ۹. تصمیم معماری برای ادامه

برای حفظ **همهٔ ناوردی‌های موجود** (render خالص، tg_api بدون business logic، center = orchestration، containment، fail-soft، flag-off، allowlist):

- هر ماژول جدید در `_ops/telegram_center/` با همان idiom: `$0 · stdlib-only · import-time خالص · fail-soft`.
- اکشن‌های خطرناک **همیشه** از صف approval یا دوکلیک می‌گذرند — متن آزاد هرگز مستقیم اجرا نمی‌کند.
- scan فقط metadata می‌خواند (path/size/mtime/ext)؛ محتوای فایل هرگز (مخصوصاً `.env`)؛ hash فقط پشت فلگ و محدود.
- bridge بین دو دنیای approval: هم `_ops/state/telegram/approvals/*.json` (تاریخچه) و هم `_octopus/state/approvals.json` (pending queue) خوانده/نوشته می‌شوند.

---

## ۱۰. نتیجهٔ فاز A

سیستم پایدار است و نباید بازنویسی شود. ۵ کارِ واقعی باقی مانده:

1. **C** — `intent.py` (تمیزتر کردن `_handle_ask`)
2. **D** — `metadata_scan.py` + صفحهٔ `mn:map` واقعی
3. **E** — `approval_store.py` + `mn:ap` واقعی (pending queue)
4. **F** — `actions.py` (skeleton)
5. **G** — یک اصلاحِ کوچک در `tg_api.py` برای کاهش ریسک 409

ادامه با فاز B (افزودن دکمهٔ نقشه به منو) آغاز می‌شود.
