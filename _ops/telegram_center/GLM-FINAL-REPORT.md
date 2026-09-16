# 🐙 GLM-FINAL-REPORT — مقرِ فرماندهیِ تلگرام اختاپوس

- **تاریخ:** 2026-07-18
- **نقش:** مهندس ارشد تکمیل و دیباگ
- **وضعیت:** ✅ **همهٔ فازها انجام شد — ۱۱۷ تست سبز**
- **مبنای ورود:** `GLM-LIVE-BUTTONS-HANDOFF.md` (ایجنت قبلی)

---

## ۰. خلاصهٔ یک‌خطی

اختاپوس از حالت «کارت‌های توضیحی» به «مغز زنده با دکمه‌های عملگرا» رسید: منوی context-aware، پیام آزادِ intent-aware، نقشه‌برداریِ metadata واقعی، و صفِ تأیید bridge‌شده — همه با ۱۱۷ تست سبز، بدونِ هیچ عملیاتِ مخرب، و با حفظِ کاملِ ناوردی‌های امنیتی.

---

## ۱. نتیجهٔ تست‌ها

| Suite | تعداد | وضعیت |
|-------|------:|------:|
| `test_tg_render.py` | 16 | ✅ |
| `test_tg_center.py` | 20 | ✅ |
| `test_tg_power.py` | 12 | ✅ |
| `test_tg_api.py` | 18 | ✅ |
| `test_tg_intent.py` (نو) | 16 | ✅ |
| `test_tg_metadata_scan.py` (نو) | 11 | ✅ |
| `test_tg_approval_store.py` (نو) | 14 | ✅ |
| `test_tg_actions.py` (نو) | 10 | ✅ |
| **جمع** | **117** | ✅ |

دستور اجرا:
```bat
cd /d F:\backup
for %t in (render center power api intent metadata_scan approval_store actions) do python _ops\tests\test_tg_%t.py
```

---

## ۲. چه چیزهایی debug شد

(جزئیات در `GLM-DIAG-REPORT.md` و `TG-LIVE-DEBUG-REPORT.md`)

- ✅ **wiring زنده تأیید شد:** token مستقل، owner/center پیکربندی‌شده، ۹ topic، status pinned، offset restart-safe، همهٔ STOP flags پایین.
- ✅ **ریسکِ 409 Conflict رفع شد:** بررسی زنده نشان داد `TG_CENTER_BOT_TOKEN` ≠ `TELEGRAM_BOT_TOKEN` (دو باتِ مستقل). اما حالتِ fallback نهفته هشداردار شد.

## ۳. چه bugهایی پیدا و رفع شد

| # | باگ | ریشه | رفع |
|---|-----|------|-----|
| 1 | شاخهٔ `ap:detail` به NameError می‌رسید | `_esc` در `center.py` تعریف نشده بود (فقط در render.py) | `html.escape` محلی در `_handle_approval_callback` |
| 2 | ریسک 409 نهفته در fallback توکن | `tg_api` بی‌صدا به `TELEGRAM_BOT_TOKEN` fallback می‌کرد | alert throttled + ردیابیِ `token_source` + متد `diagnostics()` |
| 3 | `_quarantine_text` / صفِ approval فقط نمایشی بودند | `mn:ap` فقط verdictهای قدیمی نشان می‌داد | bridge با `approval_store` → pending queue واقعی |

---

## ۴. دکمه‌های جدید و callbackهایشان

### منوی اصلی (context-aware، از قبل موجود + تکمیل)
- ☣️ قرنطینه (`mn:qr`) — اگر quarantined>0
- 🧭 تصمیم‌ها (`mn:ap`) — اگر guidance.n>0
- 🙋 منتظر پاسخ (`mn:ap`) — اگر awaiting>0
- ▶️ پای متوقف (`mn:lg`) — اگر paused>0
- 📊 وضعیت (`mn:st`) · 🦵 پاها (`mn:lg`) · 🐙 بودجه (`mn:bg`) · 💰 درآمد (`mn:rv`)
- 🗣 **🗺 نقشه‌برداری (`mn:map`)** · **📮 صف تأیید (`mn:ap`)** (نو)
- ⚙️ سیستم (`mn:sy`)

### نقشه‌برداری metadata (نو — فاز D)
- `map:start` → اجرای scan محدود + ساخت manifest + state + job در صف
- `map:status` / `mn:map` → refresh صفحه
- `map:report` → ارسالِ آخرین گزارش markdown

### صف تأیید واقعی (نو — فاز E)
- `ap:ok:<id>` → approve + legacy verdict + refresh
- `ap:no:<id>` → reject + legacy verdict + refresh
- `ap:detail:<id>` → کارتِ جزئیاتِ content-free

---

## ۵. پیام آزاد چه intentهایی را می‌فهمد

ماژولِ `intent.py` (فاز C) این نیت‌ها را تشخیص می‌دهد:

| intent | کلیدواژه‌ها (نمونه) | خطر | عمل |
|--------|---------------------|:----:|-----|
| `status` | وضعیت، الان، status, now | read | صفحهٔ st |
| `revenue` | درآمد، پول، revenue, aud | read | کارت درآمد |
| `budget` | بودجه، تخصیص، budget | read | صفحهٔ bg |
| `help` | کمک، راهنما، منو, help | read | منو |
| `pause_leg` | مکث، متوقف، pause + نام پا | low | کارت `lg:{leg}:p` (نه اجرا) |
| `resume_leg` | ادامه، resume + نام پا | low | کارت `lg:{leg}:r` (نه اجرا) |
| `scan_metadata` | نقشه، اسکن، manifest، metadata | read | صفحهٔ map (نه اجرا) |
| `approvals` | تأیید، تصمیم، صف، approval | read | صفحهٔ ap |
| `unknown` | (هر چیز دیگر) | read | کارت پیشنهاد با ۵ دکمه |

تشخیصِ پا: `lead/ziman/mining/crypto/accounting/studio_pf/knowledge/cartographer/system` (ابهام → None → کارتِ انتخاب).

---

## ۶. فاز ۲ metadata scan — تا کجا پیاده شد

**کامل.** ماژولِ `metadata_scan.py`:

- ✅ فقط metadata می‌خواند (path/type/size/mtime/ext) — **هرگز محتوای فایل**.
- ✅ excludeها: `.git`, `__pycache__`, `node_modules`, `venv`, `.venv`, `dist`, `build`, ...
- ✅ hash سنگین فقط پشتِ `OCTOPUS_METADATA_HASH=1` و با سقفِ ۵۰۰۰ فایل (sampler 64KB).
- ✅ `.env` هرگز hash نمی‌شود (gating).
- ✅ خروجی: `latest_manifest.json` + `history/manifest_<ts>.json` + `reports/daily/metadata_scan_<ts>.md` + `state/metadata_scan.json` + append به `audit.log`.
- ✅ قابل‌قطع: `max_files` (پیش‌فرض ۲۰۰٬۰۰۰) + `max_seconds` (پیش‌فرض ۳۰۰).
- ✅ fail-soft: خطای هر فایل → skip + شمارش؛ کلِ scan هرگز crash نمی‌کند.
- ✅ به تلگرام وصل: `map:start` callback از مالک → scan واقعی + job در صف.

---

## ۷. صف approval — تا کجا واقعی شد

**کامل (bridge دو دنیا).** ماژولِ `approval_store.py`:

- ✅ pending queue در `_octopus/state/approvals.json` (ساختارِ فاز ۱).
- ✅ bridge با `_ops/state/telegram/approvals/*.json` (تاریخچهٔ verdict قدیمی).
- ✅ `add_pending/approve/reject/mark_done/load_pending/get/summary`.
- ✅ idها sanitize می‌شوند (ضدِ path-traversal).
- ✅ محتوای کاربر هرگز در job ذخیره نمی‌شود (فقط title/type/risk/content-free).
- ✅ به تلگرام وصل: `ap:ok/no/detail:<id>` callbacks + نمایشِ pending + history در `mn:ap`.

---

## ۸. چه چیزهایی هنوز deliberately not-wired مانده و چرا

| مورد | چرا not-wired |
|------|---------------|
| **`mn:qr` per-item actions** (`qr:<id>:inspect/release/keep`) | منبعِ itemهای قرنطینه در `execution_board` روشن نیست؛ فعلاً فقط شمارش. (طبق دستور: «تا وقتی منبع itemها روشن نیست، فقط شمارش بماند».) |
| **اجرای واقعیِ jobهای risk=high از صف** | `approval_store` فقط state را عوض می‌کند (pending→approved). اجرای واقعیِ move/delete/budget-apply به power-gate (`pw`/`pwc`) یا handlerهای جداگانه واگذار می‌شود — این لایه‌جدایی، یک ویژگیِ امنیتی است نه نقص. |
| **LLM در intent router** | طبق دستور، فقط پشتِ `OCTOPUS_TG_LLM_ASK=1` (پیش‌فرض خاموش). `intent.classify` آمادهٔ ارتقاء است بدونِ لمسِ center. |
| **TelBot (assistant) جداگانه** | هنوز در repo موجود نیست. قراردادِ امنیتی‌اش در `GLM-TELBOT-ROLE-AUDIT.md` مستند شد. |
| **`actions.py`統合 با `action_graph.py`/`mission.py`** | هم‌پوشانی شناسایی شد ولی ادغام یک refactor بزرگ است؛ فعلاً هر سه مستقل و سبز کار می‌کنند. |

---

## ۹. فایل‌های جدید/ویرایش‌شده

### ویرایش‌شده (۳)
- `_ops/telegram_center/center.py` — `_handle_ask` به `intent.classify`، `_page` برای `mn:map`/`mn:ap` واقعی، `_handle_map_callback`، `_handle_approval_callback`، `_approvals_queue_page`.
- `_ops/telegram_center/render.py` — افزودن `mn:map`/`mn:ap` به منو + `render_map_page` + `render_approvals_queue`.
- `_ops/telegram_center/tg_api.py` — alert هنگام fallback توکن + `token_source` + متد `diagnostics()`.

### نو (۴ ماژول + ۴ تست + ۳ گزارش)
- `_ops/telegram_center/intent.py` — طبقه‌بندِ نیت (۱۶ تست).
- `_ops/telegram_center/metadata_scan.py` — نقشه‌برداریِ metadata (۱۱ تست).
- `_ops/telegram_center/approval_store.py` — پلِ صفِ تأیید (۱۴ تست).
- `_ops/telegram_center/actions.py` — رجیستریِ callbackها (۱۰ تست).
- `_ops/tests/test_tg_intent.py`, `test_tg_metadata_scan.py`, `test_tg_approval_store.py`, `test_tg_actions.py`.
- `_ops/tests/test_tg_render.py` (+۲), `test_tg_center.py` (+۶ e2e), `test_tg_api.py` (+۲).
- `_ops/telegram_center/GLM-DIAG-REPORT.md` — فاز A.
- `_ops/telegram_center/TG-LIVE-DEBUG-REPORT.md` — فاز G.
- `_ops/telegram_center/GLM-TELBOT-ROLE-AUDIT.md` — فاز H.

---

## ۱۰. دستور اجرای bot

```bat
cd /d F:\backup\_ops
RUN-TG-CENTER.bat
```

یا مستقیم (با env):
```bat
cd /d F:\backup
python -X utf8 _ops\telegram_center\center.py
```

پس از اجرا، در تلگرام `/menu` بزنید. باید کارتِ زنده با دکمه‌های context-aware (شامل 🗺 نقشه‌برداری و 📮 صف تأیید جدید) ببینید.

دستور تست‌ها:
```bat
cd /d F:\backup
python _ops\tests\test_tg_render.py
python _ops\tests\test_tg_center.py
python _ops\tests\test_tg_power.py
python _ops\tests\test_tg_api.py
python _ops\tests\test_tg_intent.py
python _ops\tests\test_tg_metadata_scan.py
python _ops\tests\test_tg_approval_store.py
python _ops\tests\test_tg_actions.py
```

---

## ۱۱. پیام کوتاه برای تلگرام (پس از deployment)

```text
🐙 اختاپوس — کنترل زنده

✅ منوی پویا فعال شد (context-aware).
✅ دکمه‌ها action واقعی دارند (map/ap/legs/power).
✅ پرسش آزاد ادمین به کارت امن تبدیل می‌شود (intent router).
✅ نقشه‌برداری metadata آماده/فعال شد (فقط خواندنی).
✅ صف تأیید به persist وصل شد (pending واقعی).
🔒 عملیات مخرب همچنان قفل و نیازمند تأیید است.

دکمه‌های جدید: 🗺 نقشه‌برداری · 📮 صف تأیید

برای شروع:
/menu
```

---

## ۱۲. تعریفِ موفقیت — تحقق یافته

> «ادمین در تلگرام `/menu` می‌زند و به‌جای یک منوی مرده، یک کارت زنده می‌بیند که مهم‌ترین کار الان را بالا آورده. دکمه را می‌زند، callback واقعاً handle می‌شود، state/audit تغییر می‌کند، پیام edit می‌شود، و هیچ عملیات خطرناک بدون تأیید انجام نمی‌شود.»

✅ همهٔ شروط برآورده شد. اختاپوس حس یک مغز زنده می‌دهد، نه یک بروشور.
