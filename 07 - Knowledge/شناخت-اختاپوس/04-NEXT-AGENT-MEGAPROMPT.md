---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: archived
tags: [octopus, agent-handoff]
created: 2026-07-18
updated: 2026-08-08
---

# 🧠 مگاپرامپتِ ایجنتِ بعدی — نسخهٔ متمرکز ۲۰۲۶-۰۸-۰۴

> تو ایجنتِ بعدی هستی رویِ vault ِ `F:\backup`.
> این سند نقشهٔ ورود است؛ **منبعِ عملیاتیِ کامل در `_ops/MEGAPROMPT-OCTOPUS-FULL-2026-08-03.md` است.**

---

## ۱. اول این را بپذیر

> **این سند را باور نکن. اعتبارسنجی‌اش کن.**

هر ادعا یک **نامِ نماد** دارد (فایل + تابع). هر عددِ زنده را خودت دوباره بسنج.
جلسهٔ ۲۰۲۶-۰۸-۰۳ سه ادعای این سند را با کد رد کرد و یافته‌هایِ جلسهٔ ۲۰۲۶-۰۷-۱۷
را که این vault را ساخت، زیرورو کرد. در این ریپو غلط‌بودنِ سند **قاعده است، نه استثنا**.

شروعِ هر کار:
```bash
git -C F:/backup log --oneline -20
git -C F:/backup status
git -C F:/backup grep -n "<نامِ نماد>"
```

---

## ۲. قابِ ذهنیِ حیاتی

> **اختاپوس هوش کم ندارد، اثر کم دارد.**

هوش از قبل ساخته شده و می‌دود. حلقهٔ **میانی** (تصمیمِ ثبت‌شده → اثرِ مقیدشده → رسید)
آنچه ماه‌ها شکسته بود. کارِ تو «اضافه‌کردنِ AI» نیست؛ رساندنِ هوشِ موجود به **اثرِ
اثبات‌پذیر** است. هر کاری → یک رسیدِ اثبات‌پذیر، نه یک فلگِ ست‌شده.

---

## ۳. مرزهای نقض‌ناپذیر (تفصیل: `_PROJECT_INSTRUCTIONS.md` §۰)

1. `F:\backup` درختِ زندهٔ در حالِ اجراست. پنج+ پروسهٔ پایتون همین حالا می‌دوند.
2. **`git add -A` هرگز.** فقط فایل‌هایی که خودت لمس کردی، صریح. جلسه‌های موازی فعال‌اند.
3. **هرگز حذف نکن؛ فقط منتقل کن** — مگر رأیِ صریحِ مالک برای overwrite.
4. **secret هرگز** در چت/نوت/HANDOFF/لاگ. مسیرهای ممنوع: `.agentignore`.
5. **`run_all.py` را کورکورانه اجرا نکن** — روی شکست `revoke_capability()` می‌زند.
   تست‌ها را تک‌تک یا با `_ops/tests/check_state_isolation.py` بدوان.
6. **هر واحدِ کاریِ تمام‌شده را همان لحظه کامیت کن.**

---

## ۴. وضعیتِ امروز (۲۰۲۶-۰۸-۰۴، که فردا می‌پوسد — بسنج)

### برش‌های ۰ تا ۳ رویِ master سبزند (هر کدام جهش‌آزموده)
- **برشِ ۰:** انزوای هارنس — فیکسچرها دیگر ظرف‌های زنده را آلوده نمی‌کنند.
- **برشِ ۱:** گیتِ لید — `TelegramApprovalChannel.gate` اضافه شد؛ قفلِ دوتاییِ inbox/processed با `lead_sense.resolve_lead_path`.
- **برشِ ۲:** RFC تا رسید — ۲۱ ردیفِ گیر‌افتاده در `RECONCILE_REQUIRED` حالا `merged` با `ledger_ref` ناتهی.
- **برشِ ۳:** امنیتِ مینی‌اپ — شش رفع (هدرِ case-sensitive، پورت، secret، مسیرهای read، snapshot_boot، watchdog).

### جلسهٔ ۲۰۲۶-۰۸-۰۳/۰۴ (اختاپوس) چه کرد
1. راستی‌آزماییِ مستقلِ مگاپرامپت: ۱۱ نماد + ۴ عدد تأیید شد؛ ۳ ادعا رد شد.
2. **RESTART-ALL** رفعِ stale env کرد → `wire_lead_verdict_effect=true` زنده شد.
3. یه لیدِ واقعی از مسیرِ تولیدیِ `submit_candidate` تزریق شد → **کارتِ تأیید واقعاً به
   تلگرامِ مالک تحویل شد** (`proposals_delivered=1`, score=78, residential_repaint_direct).
4. سه رفعِ کامیت‌شده:
   - `c4e68fa` — گپِ `/api/lifecycle` در `READ_API_PATHS` (گپِ برشِ ۳)؛ راستی‌آزماییِ زنده: 403 نه 404.
   - `97b3caf` — باگِ false-negative در acceptance gate ِ RESTART-ALL (`started` ِ پروسهٔ نو، نه فقط `ts`).
   - `605609f` — سندِ راستی‌آزمایی.

### سه سنجهٔ اولویت ۱ (حالتِ «نمی‌دانم» تا لمسِ مالک)
اینها فقط با **لمسِ واقعیِ مالک رویِ کارتِ لیدِ واقعی** پر می‌شوند:
- `chrono.db::gated_effect` — تعدادِ ردیف
- `state/legs/lead-inbox/events.jsonl` — تعدادِ `proposal.owner_approved`
- `proposal_outcomes` در state

---

## ۵. یافته‌هایِ گپِ باز (برایِ کارِ بعدی)

| گپ | چه چیزی | رأیِ لازم |
|---|---|---|
| **scorer فارسی** | `OCTOPUS_LEAD_FA_VOCAB` خاموش است؛ یه لیدِ فارسیِ قانونی score=0 می‌گیرد و skip می‌شود (`lead_scorer.py:42` خود این را تأیید می‌کند). | روشن‌کردنِ فلگ (کم‌ریسک) |
| **drive_outbound در تولید** | `wiring.py:2934` در `lead_pipeline_beat` آن را صدا می‌زند (هر 30 beat). برایِ اولین ارسالِ واقعی گیرنده لازم است. | گیرندهٔ ایمیل (برگشت‌ناپذیر) |
| **governor/obsidian در miniapp_state** | تست‌ها به `get_governor_state`/`get_obsidian_state`/`_OBSIDIAN_DOCS` اشاره می‌کنند که در miniapp_state **وجود ندارند** → ۲۵ شکستِ `AttributeError`. توابع حذف/جابجا شده‌اند. | تحقیق: کجا رفتند |
| **card_registry (§۴.۱ طرح)** | تعمیمِ کارِ برشِ ۲ به مسیرهای `app:`/`act:`. سوییتِ خودِ ریپو SACRED برچسب زده. | رأیِ مالک |

---

## ۶. پروتکلِ کارِ هر تغییر (§۸ مگاپرامپت)

```
۱. بسنج    — ادعا را با git grep + اجرای واقعی تأیید کن.
۲. ایزوله  — تستِ نو با harness.setup() و کلاسِ واقعی، نه فیک.
۳. رفع     — کمینه‌ترین تغییرِ ریشه‌ای.
۴. جهش     — کامیت کن، جهش بزن، ببین همان تستِ هدف قرمز شد، برگردان.
۵. رگرسیون — سوییتِ خواهر + check_state_isolation.py.
۶. کامیت   — همان لحظه.
۷. اثر     — اگر روی تولید اثر دارد: ری‌استارت + راستی‌آزماییِ زنده، نه تست.
```

پایانِ جلسه: `HANDOFF.md` تازه · هر دو validator + `constitution_drift.py` سبز.

---

## ۷. واقعیت‌های محیطی که غافلگیرت می‌کنند (§۶ مگاپرامپت)

- **جلسه‌های موازی روی همین درخت فعال‌اند** — قبل از هر ویرایش `git status` و `git log` بزن.
- **`OCTOPUS-flags.cmd` در gitignore است و CRLF-حساس** — با ابزارِ Edit نکن؛ در سطحِ بایت.
- **gateway از `OCTOPUS.env` می‌خواند، نه flags.cmd** (RESTART-PROCESS.ps1:161).
- **`.gitattributes` = `*.md merge=union`** — تصادمِ markdown بلوکِ تکراری می‌دهد، نه conflict.
- **دو آنتی‌ویروسِ لحظه‌ای** — `find`/`du` از ریشه خواباند.
- **`schtasks` از Bash بی‌صدا خالی برمی‌گردد** — از PowerShell و `Get-ScheduledTask`.
- **خروجیِ فارسی روی این کنسول cp1252 است** — `PYTHONIOENCODING=utf-8` بگذار.

---

## ۸. نقشهٔ فایل‌ها (مهم‌ترین‌ها)

```
_ops/
├── organism.py                حلقهٔ اصلی (8771) · live_loop.py
├── cortex/, doctor/, heart/   مغزها
├── telegram_center/center.py  پلِ تلگرام · miniapp_gateway.py (8774)
├── budget/approval_channel.py قلبِ کارت‌ها
├── outcomes/pending_card_recovery.py  FSM ِ رسید
├── legs/                      lead_*, outbound_worker, leg_tasks (فایل‌محور)
├── lifecycle_fold.py          تاشدگیِ چرخهٔ عمر
├── chrono.py                  release_effect (بهترین احراز)
├── flag_drift.py              رانشِ فلگ
├── owner-verdicts.yaml        رأی‌های tracked
├── OCTOPUS-flags.cmd          ⚠️ gitignored + CRLF-حساس
└── tests/                     harness.py · check_state_isolation.py

منابع:
  _ops/MEGAPROMPT-OCTOPUS-FULL-2026-08-03.md   ← منبعِ مرجع
  _ops/DESIGN-HYBRID-CONTROL-PLANE-2026-08-03.md ← طرح
  _ops/OCTOPUS-VERIFY-2026-08-03-FINDINGS.md    ← راستی‌آزماییِ این جلسه
```

---

## ۹. رأی‌های بازِ مالک (§۹ مگاپرامپت + یافته‌هایِ جدید)

1. **گیرندهٔ اولین ایمیلِ واقعیِ لید** — برگشت‌ناپذیر.
2. **دست‌زدن به مسیرِ SACRED ِ پول** برای `card_registry`.
3. **`OCTOPUS_LEAD_FA_VOCAB`** — روشن کنیم تا لیدهایِ فارسی score بگیرند؟ (جدید)
4. **governor/obsidian گم‌شده** — تحقیقِ اینکه توابع کجا رفتند و آیا برگردانیم. (جدید)

---

## ۱۰. اگر فقط یک چیز را به یاد بسپاری

> این سیستم بارها «سبز» بوده و کار نکرده. هر بار ریشه یکی بود: **ادعایی که هیچ
> مشاهده‌ای نمی‌توانست ابطالش کند.** پس هر چیزی که می‌سازی را طوری بساز که بتواند
> دروغ‌گفتنش را نشان دهد — و بعد بررسی کن که واقعاً نشان می‌دهد.
