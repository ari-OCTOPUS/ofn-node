---
type: prompt
status: ready
tags: [autonomy, architect, selfimprove, governance]
created: 2026-07-05
updated: 2026-07-06
---

# Prompt — منشور استقلال مغز (Autonomy Ladder v1)

> **هدف:** مغز بدون دخالت انسانی زنده بماند، خودش را ترمیم کند، و درس‌های کم‌ریسک را خودش اعمال کند — بدون آنکه حتی یک invariant امنیتی شل شود. **اجرای این پرامپت = verdict آری روی خود منشور** — **ratified 2026-07-05 با دستور آری («اجرا کن پرامپت‌های خودتو»)**؛ گام‌های §۸ همان جلسه اجرا شد (متن کامل پرامپت‌ها: [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]]).

## ۰) اصل طراحی

استقلال یعنی جابه‌جاییِ «کلاسِ تصمیم» روی نردبان autonomy — نه شل‌کردن گاردها. هر اقدام باید در یکی از پله‌ها جا بگیرد؛ اگر جای اقدامی مبهم بود، پلهٔ پایین‌تر.

## ۱) invariantهای غیرقابل‌مذاکره (در هیچ پله‌ای شل نمی‌شوند)

- secret/کلید/عبارت بازیابی: هرگز خوانده/echo/تست نمی‌شود؛ گارد نویسه‌گردانی برقرار.
- محدودهٔ منفی: `_Archive` · `_Duplicates` · «09 - People» · مسیرهای `.agentignore`.
- قاعدهٔ Project-F: فقط فاز/Track — بدون هویت/پلتفرم/محتوا/مسیر.
- append-only بودن [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] (فقط ستون وضعیت به‌روز می‌شود).
- هیچ اکشن خارجی: نه ارسال پیام، نه ثبت‌نام، نه پرداخت/ترید؛ سقف API طبق D-25.
- گیت rotation: تا CRITICALهای [[ROTATION_CHECKLIST]] باز است، هیچ ارتقای autonomy روی حوزه‌های قرنطینه اعمال نمی‌شود.
- **kill switch مالک:** خط `AUTONOMY:` در §۱۰ همین نوت؛ هر تسک پیش از هر اقدام L2/L3 آن را می‌خواند — `off` = همهٔ پله‌ها به L1 سقوط می‌کنند، بی‌استثنا و بی‌تفسیر.
- خطای خاموش = باگ درجه‌یک؛ هر شکست باید ثبت و اعلام شود.

## ۲) نردبان autonomy

| پله | معنا | مثال |
|---|---|---|
| L0 read-only | فقط گزارش | ارزیابی حوزهٔ قرنطینه |
| L1 propose-only | پیشنهاد در scout-digests / ردیف pending در ledger | درس ساختاری، retire/spawn |
| L2 bounded-auto | اجرا + ثبت + برگشت‌پذیر — فقط لیست سفید §۳ | خودترمیمی ناوگان |
| L3 auto | اجرای بی‌صدا — فقط مشتق‌های idempotent | رندر تابلوها |

## ۳) لیست سفید L2/L3 (شرط ورود: برگشت‌پذیر + مشتق + machine-checked)

> **سقف روزانه (rate cap):** حداکثر ۳ اقدام L2 در روز از کلاس‌های ۴–۶؛ فراتر از سقف → همان اقدام به L1 (پیشنهاد) تنزل می‌کند. کلاس ۳ (بازگرداندن وضع ratified) سقف عددی ندارد — دامنه‌اش bounded-by-design است (فقط تسک‌های جدول ratified) و هر مورد notification دارد.

1. **رندر مشتق‌ها → L3:** BRAIN-FOCUS-BOARD.html · SYSTEM-DASHBOARD.html · Brain.md · آرتیفکت‌های Cowork (همه hash-diff + گارد parse/secret قبل از نوشتن).
2. **append → L3:** درس به ledger، دیجست به scout-digests.
3. **خودترمیمی ناوگان → L2:** هر تسک زیرساختی در شروع اجرا، خروجی زندهٔ زمان‌بند را با جدول «تسک‌های ratified» رجیستری مقایسه می‌کند؛ اگر تسک ratified غایب بود (reset)، همان را با همان cron و پرامپت ثبت‌شده re-create و در ledger + رجیستری ثبت می‌کند (کشف 2026-07-05: reset جلسه کل ناوگان را پاک کرد و ~۲۴ ساعت کسی نفهمید).
4. **self-verdict درس‌های کم‌ریسک → L2:** درس pending-verdict فقط وقتی خودکار applied می‌شود (با برچسب `auto-applied`) که هر ۴ شرط برقرار باشد: (الف) فقط پارامتر نمایشی/گزارش‌لایه را تغییر دهد؛ (ب) برگشت‌پذیر باشد؛ (ج) ≥۷ روز بدون اعتراض مانده باشد؛ (د) در ≥۲ اجرای متوالی شاهد تکرارشونده داشته باشد. درس ساختاری/canonical همچنان verdict انسانی.
5. **evaporation/TTL → L2:** آرشیو in-place دیجست‌های >۱۴ روزِ خود ناوگان (برگشت‌پذیر، فقط scout-digests).
6. **ترمیم خطای خودساخته → L2:** لینک/فرانت‌متر شکسته‌ای که خود ایجنت در همان جلسه ساخته.

## ۴) لیست سیاه (همیشه verdict انسانی)

تغییر پرامپت‌های canonical و منشورها · تغییر Property Schema · rename/حذف نوت canonical · هر چیز نزدیک به secret، پول، پیام خارجی، هویت Project-F · **تغییر خود این منشور** · ارتقای هر کلاس جدید به L2/L3.

## ۵) watchdog دوطرفه (سکوت دیگر نامرئی نیست)

هر اجرای brain-focus-board و system-dashboard سطر «task · timestamp · نتیجه» را در `_memory/HEARTBEAT.md` (مشتق، overwrite-مجاز) به‌روز می‌کند و heartbeat دیگری را چک می‌کند: سکوت > ۲×دورهٔ انتظار → درس regress در ledger + notification به آری. experience-review هفتگی کل heartbeat را می‌سنجد.

## ۶) گزارش به انسان: فقط استثناها

اجرای موفق = بی‌صدا. notification فقط برای: کشف regress · خودترمیمی انجام‌شده · `auto-applied` نو · heartbeat گم‌شده · review هفتگی. کاهش بار آری = استقلال واقعی.

## ۷) شاخص استقلال (بخش «🔁 چرخه» تابلو)

- سهم درس‌های applied بدون لمس انسانی — هدف: >۵۰٪ در ۴ هفته.
- میانگین زمان pending→applied.
- شمار خودترمیمی موفق ÷ شمار reset.
- **صفر نقض invariant** — هر نقض = halt کامل L2/L3، بازگشت همه به L1 تا verdict آری.

## ۸) گام‌های اجرا (جلسهٔ تعاملی، بعد از ratify)

1. جدول «تسک‌های ratified» (taskId · cron · اشارهٔ پرامپت) را در [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] تثبیت کن — مرجعِ خودترمیمی §۳.۳.
2. §۳ و §۵ را به پرامپت زندهٔ ۶ تسک موجود اضافه کن (در زمان‌بند + سند در رجیستری).
3. `_memory/HEARTBEAT.md` را بساز (مشتق، overwrite-مجاز؛ ثبت استثنای overwrite در رجیستری).
4. قاعدهٔ self-verdict §۳.۴ را به پرامپت experience-review اضافه کن — auto-appliedها را جدا و برجسته گزارش کند.
5. ردیف ledger: «منشور استقلال v1 ratified» + این نوت → `status: ready` و خط AUTONOMY در §۱۰ → `on`.
6. **تست پذیرش:** یک تسک زیرساختی را عمداً حذف کن → اجرای بعدیِ تسک دیگر باید آن را برگرداند و در ledger ثبت کند.

## ۹) بلوک تزریق (کپی‌پیست در پرامپت زندهٔ هر تسک، پس از ratify)

```
autonomy-protocol v1 — مرجع: «04 - Architect System/architect/04-Docs/Prompt - منشور استقلال مغز (Autonomy Ladder)»
1) خط AUTONOMY منشور را بخوان؛ off → همه‌چیز propose-only.
2) هر اقدام را کلاس‌بندی کن: L0 گزارش · L1 پیشنهاد · L2 فقط لیست سفید §۳ · L3 فقط مشتق idempotent (hash-diff + گارد). مبهم → پلهٔ پایین‌تر.
3) شروع اجرا: زمان‌بند زنده را با جدول ratified رجیستری تطبیق بده؛ تسک ratified غایب → re-create با همان cron/پرامپت + ثبت ledger + notification.
4) پایان اجرا: سطر خودت در HEARTBEAT + چک heartbeat دیگران؛ سکوت >۲×دوره → درس regress + notification.
5) هر L2: اول سقف روزانه (۳) و برگشت‌پذیری را چک کن، بعد اجرا، بلافاصله ردیف ledger با برچسب auto. بدون ثبت = اقدام ممنوع.
6) نقض هر invariant §۱ → halt کامل L2/L3 + notification؛ تا verdict بعدی فقط L1.
7) موفقِ عادی بی‌صداست — notification فقط استثناهای §۶.
```

## ۱۰) kill switch

AUTONOMY: on

<!-- verdict آری = این خط به `on` تغییر می‌کند؛ تنها جای تغییرش همین‌جاست و تنها تغییردهنده آری است. on شد 2026-07-05 با دستور مستقیم آری. -->

## ریسک‌ها

- **خزش دامنهٔ self-verdict** — مهار: معیار چهارگانهٔ §۳.۴ + halt §۷؛ review هفتگی auto-appliedها را بازرسی می‌کند.
- **خودترمیمی با پرامپت کهنه** — مرجع بازسازی = جدول ratified رجیستری، نه حافظهٔ اجرا؛ هر drift پرامپت = درس.
- **تکثیر خرابی در L3** — hash-diff و گارد parse قبل از هر نوشتن؛ مدل خراب = هیچ نوشتنی.

## مرتبط

- [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] · [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] · [[04 - Architect System/architect/04-Docs/Prompt - System Dashboard Artifact|Prompt - System Dashboard Artifact]] · [[01 - Dashboard/HANDOFF|HANDOFF]]
