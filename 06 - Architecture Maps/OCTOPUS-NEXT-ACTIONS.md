---
type: tasks
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, next-actions, backlog, cockpit, governor]
created: 2026-08-02
updated: 2026-08-02
created_by: agent
sources:
  - "[[06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH]]"
  - "[[06 - Architecture Maps/OCTOPUS-INTEGRATION-STATUS]]"
---

# OCTOPUS — Next Actions

<!-- BEGIN GENERATED: vault-docs lane, 2026-08-02. ویرایشِ انسانی زیرِ «Owner notes». -->

> هر ردیف: **چرا** (شاهدِ سنجیده‌شده) · **کجا** (مسیر) · **سنجهٔ پایان** (چطور بفهمیم شد).
> ردیفی که سنجهٔ پایانِ قابلِ مشاهده ندارد، اکشن نیست — آرزوست.
> ترتیب = ریسک × ارزان‌بودنِ رفع. `[ ]` باز · `[x]` بسته · `[owner]` منتظرِ حکمِ مالک.

## P0 — چیزی که ممکن است **گم شود**

- [ ] **N-2 · `governor.py` و تستش را وارد git کن**
  - **چرا:** `git status` → `?? _ops/budget/governor.py` **و**
    `?? _ops/tests/test_governor_routing.py`. ۲۶.۸KB کدِ اجراشونده + یک سوییتِ ۱۷تاییِ سبز،
    هیچ‌کدام کامیت‌نشده. یک `git clean -fd` یا سوییچِ worktree هر دو را می‌بَرد. این سیستم
    این اشتباه را قبلاً کرده (نجاتِ ۲۷ و بعد ۶۳ ماژولِ بی‌گیت).
  - **کجا:** `_ops/budget/governor.py` + `_ops/tests/test_governor_routing.py`
  - **به‌علاوه:** `test_governor_routing.py` در `_ops/tests/run_all.py` **ثبت نشده** —
    یعنی در گیتِ deploy دیده نمی‌شود. ثبت **مرکزی** است (D-14): نامش را گزارش کن.
  - **سنجهٔ پایان:** `git ls-files _ops/budget/governor.py _ops/tests/test_governor_routing.py`
    دو خط برگرداند، و نامِ تست در `run_all.py` باشد.
    (`.gitignore` کافی **نیست** — روی untracked بی‌ربط است و روی tracked بی‌اثر.)

## P1 — سندی که به کد وصل نیست

- [ ] **N-1 · خواننده‌های truth را به vault بِبَر**
  - **چرا:** حکمِ مالک «truth داخلِ vault» است، ولی **دو** خواننده یک فایلِ ریشه با نامِ
    تاریخ‌دار را hardcode کرده‌اند. تا این عوض نشود، `06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH.md`
    برای `/truth` و `/api/current-truth` نامرئی است.
  - **کجا:** دو نقطه —
    1. `_ops/telegram_center/miniapp_state.py` → `_TRUTH = _ROOT / "OCTOPUS-CURRENT-TRUTH-2026-08-02.md"`
    2. `_ops/agi2027_control/runtime.py` (شاخهٔ `if raw == "/truth"`) → همان نامِ فایل
  - **مراقب باش:** نامِ تاریخ‌دار **هر روز** می‌پوسد. مقصدِ جدید بی‌تاریخ باشد:
    `06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH.md`.
  - **سنجهٔ پایان:** `/api/current-truth` رشته‌ای برگرداند که فقط در فایلِ vault هست
    (نه در فایلِ ریشه) — یعنی لنگرِ **یکتا** بگذار، نه یک تیترِ مشترک.
  - **تصمیمِ باز:** فایلِ ریشه بماند یا به `_Archive` برود؟ قاعده «هرگز حذف نکن؛ منتقل کن».
    → [[06 - Architecture Maps/OCTOPUS-DECISION-LOG|DECISION-LOG]] D-4.

- [ ] **N-3 · `governor.py` صداکنندهٔ واقعی بگیرد** *(نیمهٔ تست انجام شد)*
  - **[x] تست** — یک lane موازی وسطِ همین جلسه `_ops/tests/test_governor_routing.py` را
    ساخت: ۱۷/۱۷ سبز، اجرا شد. هر دو قفلِ secret را **جداگانه** می‌سنجد (وگرنه جهش روی
    هرکدام را آن‌یکی می‌پوشاند و هر دو «SURVIVED» گزارش می‌شوند). ⚠️ ولی هنوز untracked
    و در `run_all.py` ثبت‌نشده → N-2.
  - **[ ] صداکننده** — همچنان صفر. تنها importکنندهٔ `governor` خودِ تستش است، و **تست
    صداکننده نیست**. فلگِ خاموش + بی‌صداکنندهٔ تولیدی = «قابلیت وجود ندارد».
  - **کجا:** یک مسیرِ تولیدیِ واقعی که به‌جای `model_router.ask` از `governor.ask` با
    `contract=` رد شود — پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_GOVERNOR`.
  - **سنجهٔ پایان:** با فلگِ **روشن** یک خط در `state/governor/decisions.jsonl` از یک
    مسیرِ تولیدی (نه تست) ظاهر شود؛ با فلگِ خاموش، رفتار بایت‌به‌بایتِ امروز بماند.
  - **مراقب باش:** `__pycache__` را بینِ اجراهای جهش پاک کن — بایت‌کدِ کهنه قبلاً در همین
    repo دو جهشِ هم‌اندازه را یکی شمرد.

## P2 — گپِ اصلیِ cockpit

- [x] **N-4 · بخش‌های `brain / governor / obsidian / next_steps` در `/api/ops`** — **انجام شد**
  - **وضعیت (سنجشِ مستقیم ۲۰۲۶-۰۸-۰۳):** کامیتِ `3a8cb2d`. `get_ops_state()` حالا ۱۳ کلید
    دارد و هر چهار بخش هست؛ به‌علاوه سه زیرمسیرِ `/api/ops/{brain,leads,tasks}`.
  - **سنجهٔ پایان — پاس شد:** بخش‌های غایب `available:false` + `reason` می‌دهند، نه صفرِ
    جعلی. `owner_auth.bot_token` هم `<REDACTED>` است، نه مقدارِ خام.
  - **auth:** هر سه زیرمسیر از همان `READ_API_PATHS` ِ تک‌فهرست و همان
    `_read_api_authorized` ِ والد رد می‌شوند. با `OCTOPUS_MINIAPP_READ_OWNER_GATE=1`
    هر پنج مسیر `403`؛ فلگ‌خاموش `200` مثلِ قبل. فلگ بیرونِ `PAPER_FULL_FLAGS`.
  - **⚠️ چرا این بند اول «باز» نوشته شده بود:** سنجشِ نسخهٔ اولِ سند از پیش از `3a8cb2d`
    بود و پیش از commit دوباره سنجیده نشد — یازده دقیقه فاصله. **درس:** روی درختِ
    چند-lane، ادعای «سنجیده شد» را در همان دقیقهٔ commit تازه کن.

- [ ] **N-6 · رفتارِ گروه در برابر DM را بسنج**
  - **چرا:** UNKNOWN است، و سابقهٔ ثبت‌شدهٔ همین سیستم می‌گوید پلِ فرمان و سیاستِ ورودیِ
    گروه دو لایهٔ مستقل‌اند — منویی که در DM مسلح است می‌تواند در گروه کاملاً مرده باشد.
  - **کجا:** `_ops/telegram_center/center.py` (مسیرِ `_handle_message` و گاردهای گروه)
  - **سنجهٔ پایان:** یک جدولِ صریح «کدام فرمان در DM کار می‌کند / در گروه کار می‌کند»،
    از **اجرا** نه از خواندنِ کد.

## P3 — بهداشت

- [ ] **N-5 · mojibake ِ `app.js` را تعمیر کن**
  - **چرا:** رشته‌های فارسیِ سورس دوبار-انکود شده‌اند (`Ã˜Â®Ã˜Â·Ã˜Â§` به‌جای «خطا»).
    یعنی کاربر در UI متنِ آشغال می‌بیند.
  - **کجا:** `_ops/telegram_center/miniapp/app.js` (`index.html` و `style.css` سالم‌اند)
  - **سنجهٔ پایان:** grep روی `Ã` در فایل صفر نتیجه بدهد، و فایل هنوز LF بماند.
  - **مراقب باش:** فایل را با ابزارِ **بایتی/utf-8-صریح** بنویس. `git diff --numstat`
    بعد از ویرایش تأیید کند که فقط خطوطِ مورد نظر عوض شده‌اند.

- [ ] **N-7 · گزارشِ کهنه‌ی MiniApp را اصلاح کن**
  - **چرا:** `MINIAPP-UI-COCKPIT-2026-08-02.md` می‌گوید «۷ تب» و «۹ live/۶ staged»؛
    واقعیتِ امروز ۸ تب و ۱۱ live/۵ staged/۱ unknown است.
  - **کجا:** `_ops/implementation_reports/MINIAPP-UI-COCKPIT-2026-08-02.md`
  - **سنجهٔ پایان:** عددهای گزارش با شمارشِ زندهٔ `index.html` و `ui-registry.json` یکی شود.

- [ ] **N-8 · دو خطای فرانت‌مترِ Inbox**
  - **چرا:** `validate_frontmatter.py` به‌خاطرِ `00 - Inbox/SESSION-NOTES-2026-08-02.md`
    قرمز است: `type: session-note` در `TYPES` نیست و `audience`/`session_author` در
    `KNOWN_KEYS` نیستند.
  - **دو راهِ مشروع** (سومی وجود ندارد): یا `type` را به یک نوعِ معتبر (`report`) عوض کن و
    دو کلیدِ اضافه را بردار؛ یا **اول** `06 - Architecture Maps/Property Schema.md` و
    `.obsidian/types.json` را در همان جلسه با تأییدِ مالک گسترش بده (§۶).
  - **هرگز:** validator را برای سبز شدن ویرایش نکن.
  - **سنجهٔ پایان:** `python "04 - Architect System/scripts/validate_frontmatter.py"` با
    exit code صفر.

## `[owner]` — منتظرِ حکمِ مالک

- [owner] **پیکربندیِ `OCTOPUS_MINIAPP_URL`** — بدونش `/ui` صادقانه `CONFIG_NEEDED` می‌دهد.
  تونل/hosting تصمیمِ مالک است، نه ایجنت. (متغیرِ محیطی — **نامش** این‌جاست، مقدارش هرگز.)
- [owner] **`TG_CENTER_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID`** — تا ست نشوند
  `POST /api/actions` همیشه `403 owner_auth_required` است. این گیت **درست** است؛
  دور زدنش ممنوع.
- [owner] **روشن‌کردنِ `OCTOPUS_WIRE_GOVERNOR`** — بعد از N-2/N-3، نه قبلش.
- [owner] **credentialهای Project-F** — تا آن‌وقت BLOCKED.
- [owner] **Wave-2 CRM** — [[06 - Architecture Maps/WAVE2-CRM-PLAN|WAVE2-CRM-PLAN]] فقط
  طرح است. یک خط کد هم نوشته نشده و تا حکمِ صریح نوشته نمی‌شود.

## هرگز (نه اکشن، نه backlog)

اتوماسیونِ لاگینِ OnlyFans/Fansly · scraping · APIهای مهندسی‌معکوس · auto-DM ·
mass messaging · cookie import. اگر تسکی به این‌ها نیاز داشت: **توقف کن و گزارش بده.**

<!-- END GENERATED -->

## Owner notes

<!-- دستِ مالک. -->
