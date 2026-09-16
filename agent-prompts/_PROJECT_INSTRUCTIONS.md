---
type: instructions
version: 2.0
status: active
tags: [governance]
updated: 2026-07-03
---

# اینستراکشن Vault — قانون اساسی ایجنت‌ها

<!-- برای آری: این فایل «قانون اساسی» vault است. فقط خودت ویرایشش کن؛ ایجنت‌ها پیشنهاد تغییر را در AGENT_QUESTIONS.md می‌نویسند. توضیحاتِ فقط-برای-انسان را مثل همین، در کامنت HTML بگذار تا هزینه کانتکست ایجنت نشود. -->

## ۰. قواعد عملیات ایجنت (به ترتیب اولویت — شماره کوچکتر برنده است)

1. **هرگز حذف نکن؛ فقط منتقل کن.** تکراری → `_Duplicates`؛ بازنشسته/باینری → `_Archive`.
2. **هرگز به `.git`، هیچ پوشه `_code`، و فایل‌های حاوی secret دست نزن.** secret را نه در چت بنویس، نه در نوت، نه در HANDOFF. مسیرهای ممنوع ماشین‌خوان: `.agentignore`.
3. **Inbox-اول:** هر ورودی جدید اول به `00 - Inbox` یا `10 - Telegram processing` می‌رود، بعد طبق درخت تصمیم (بخش ۴) بایگانی می‌شود.
4. نام‌گذاری طبق بخش ۵، فرانت‌متر طبق بخش ۶.

- **اگر قاعده‌ای راهت را بست: توقف کن** و سوال را به [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] اضافه کن. هرگز ممنوعیتی را دور نزن.
- **قبل از هر عملیات دسته‌ای (بیش از ~۵ فایل):** یک commit با پیشوند `agent-checkpoint:` بزن تا کل جلسه یک‌فرمانه برگشت‌پذیر باشد.
- **معیار پایان پردازش Inbox:** در `00 - Inbox` فقط `AGENT_QUESTIONS.md` مانده باشد و هر نوت بایگانی‌شده فرانت‌متر معتبر داشته باشد.
- این فایل برای ایجنت‌ها **فقط‌خواندنی** است.

## ۱. اکوسیستم

vault ابسیدینِ agent-first یک اپراتور تنها (فارسی‌زبان، سیدنی). لایه مادر: architect (کنترل از تلگرام). نقشه کامل: [[06 - Architecture Maps/ECOSYSTEM|ECOSYSTEM]].

| پروژه/حوزه | kind | status | شناسنامه |
|---|---|---|---|
| Lead-نقاشی | area | active | [[03 - Projects/Lead-نقاشی/PROJECT\|PROJECT]] |
| Ziman Galerry | area | active | [[03 - Projects/Ziman Galerry/PROJECT\|PROJECT]] |
| Mining | area | active | [[03 - Projects/Mining/PROJECT\|PROJECT]] |
| Crypto - etoro | area | active | [[03 - Projects/Crypto - etoro/PROJECT\|PROJECT]] |
| Accounting | area | active | [[03 - Projects/Accounting/PROJECT\|PROJECT]] |
| اونلی فنز | project | active | [[03 - Projects/اونلی فنز/PROJECT\|PROJECT]] |
| architect | area | active | [[04 - Architect System/architect/PROJECT\|PROJECT]] |
| هیپنوتیزم و خودآگاهی | area | active | [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT\|PROJECT]] |

## ۲. نقشه پوشه‌ها (جدول مسیریابی)

| # | پوشه | اینجا می‌آید | اینجا نمی‌آید |
|---|---|---|---|
| 00 | Inbox | ورودی تازه دسته‌بندی‌نشده؛ AGENT_QUESTIONS.md | چیزی که بیش از ۷ روز مانده |
| 01 | Dashboard | Home.md، HANDOFF.md، فایل‌های `.base` | نوت محتوایی |
| 02 | Life OS | برنامه زندگی، Weekly Review | نوت پروژه بیزنسی |
| 03 | Projects | پوشه هر پروژه: PROJECT.md + لاگ تلگرام + اسنادش | دانش عمومی (→07)، عکس (→08) |
| 04 | Architect System | سیستم مادر + `_code` و `scripts` خودش | نوت پروژه‌های دیگر |
| 05 | Agents | شناسنامه هر ایجنت/ربات | کد ایجنت (→ `_code`) |
| 06 | Architecture Maps | نقشه‌های کلان، ECOSYSTEM، Property Schema | سند معماری تک‌پروژه (→ همان پروژه) |
| 07 | Knowledge | دانش ماندگار موضوعی | باینری، نوت پروژه‌ای |
| 08 | Assets | عکس/پیوست (`Photos/<منبع-سال>`) | markdown |
| 09 | People | نوت اشخاص | لاگ چت (→ لاگ پروژه) |
| 10 | Telegram processing | پیام خام (`Raw/`)، SOP، ROUTING | عکس (→08)، باینری (→ `_Archive`) |
| — | _Archive | فقط مقصد انتقال (باینری، venv، بازنشسته) | **بازش نکن مگر صریحاً خواسته شود** |
| — | _Duplicates | فقط مقصد انتقال (قرنطینه تکراری) | **بازش نکن مگر صریحاً خواسته شود** |

قواعد شماره‌گذاری: 00 و 01 پوشه‌های سیستمی رزروند؛ شماره‌ها هرگز بازیافت یا جابه‌جا نمی‌شوند؛ بخش جدید فقط به انتهای لیست اضافه می‌شود (11، 12، …).

## ۳. چرخه عمر پروژه

- هر PROJECT.md اعلام می‌کند: `kind: project` (پایان‌دار) یا `kind: area` (عملیات جاری — بیزنس‌ها و architect؛ هرگز done نمی‌شود؛ مرور ماهانه).
- وقتی `kind: project` به `status: done` رسید — چک‌لیست تکمیل:
  1. نوت‌های بازمصرف → `07 - Knowledge` (با فرانت‌متر کامل).
  2. کل پوشه پروژه → `_Archive/Projects/<سال> - <نام>` و `status: archived`.
  3. ردیفش در [[03 - Projects/_Index - Projects|ایندکس پروژه‌ها]] → لیست «آرشیوشده».
  4. `updated:` امروز شود. (انتقال، نه حذف.)

## ۴. درخت تصمیم پردازش ورودی (Inbox / تلگرام)

برای هر آیتم، اولین شاخه منطبق را اجرا کن:

- (a) **کارِ پروژه شناخته‌شده** → `- [ ]` به «Next actions» همان PROJECT.md + ثبت تاریخ‌دار در لاگ تلگرامش.
- (b) **ونچر/پروژه جدید** → اسکلت از `_Templates/project.md`.
- (c) **دانش بازمصرف** → نوت در `07 - Knowledge` از template + لینک از MOC. نوت ایجنت‌ساخته: `created_by: agent` + حداقل ۲ منبع؛ وگرنه به‌عنوان کاندید در Inbox بماند.
- (d) **شخص** → `09 - People` از template.
- (e) **مبهم** → در Inbox با `status: idea` + یک سوال فارسی در AGENT_QUESTIONS.md.

ریتم: جاروی روزانه ایجنت؛ مرور هفتگی مالک ([[02 - Life OS/Weekly Review|Weekly Review]]). SOP کامل پیام تلگرام: [[10 - Telegram processing/SOP|SOP]] + [[10 - Telegram processing/ROUTING|ROUTING]].

## ۵. نام‌گذاری

- capture ماشینی (پیام خام تلگرام، dump، لاگ): `YYYY-MM-DD HHmm <slug>.md` — تصادم نام ساختاراً غیرممکن.
- نوت دست‌چین (03/07/09): عنوان کوتاه توصیفی، بدون پیشوند ID.
- ممنوع: « - Copy» و «(1)». نسخه جدید = suffix تاریخ یا `v2`.
- قبل از ساختن نوت/لینک، وجودش را grep کن؛ **اگر مطمئن نیستی نوتی وجود دارد، متن ساده بنویس نه wikilink.**
- عکس جدید → `08 - Assets/Photos/<منبع-سال>` + embed در نوت.

## ۶. فرانت‌متر (خلاصه — مرجع کامل: [[06 - Architecture Maps/Property Schema|Property Schema]])

- هستهٔ هر نوت، دقیقاً این کلیدها: `type` / `project` / `status` / `tags` / `created` / `updated`.
- `status` فقط: `idea | active | paused | done | archived` (حروف کوچک، دقیق — Bases به حروف حساس است).
- `project` همیشه wikilink داخل کوتیشن: `project: "[[03 - Projects/X/PROJECT]]"`.
- `tags` فقط موضوعی (painting، crypto، …)؛ هرگز status/type در تگ.
- نوت جدید همیشه از `_Templates` ساخته می‌شود؛ هر ویرایش `updated:` را امروز کند.
- **ایجنت هرگز کلید جدید اختراع نمی‌کند.** کلید جدید = ویرایش Property Schema + `.obsidian/types.json` در همان جلسه، با تأیید مالک.

## ۷. محتوای ایجنت‌ساخته

- نوت سنتز ایجنت: `created_by: agent` + `sources:` با ≥۲ لینک.
- به نوت انسانی فقط append یا انتقال؛ **هرگز بازنویسی مخرب**.
- نوشتنِ خودکار (تلگرامی/cron) همیشه appendِ تاریخ‌دار است.
- فایل کمکی حدسی نساز؛ نوت فقط وقتی درخت تصمیم بگوید یا مفهومی در ۳+ جا تکرار شود.

## ۸. حافظه و handoff

- هر PROJECT.md دو بخش فرار دارد: `## Active Context` (تمرکز فعلی / تغییرات اخیر / ۳ قدم بعدی / تصمیم‌های باز) و `## Progress` (چه کار می‌کند / چه مانده / مشکلات شناخته).
- هر ایجنت قبل از کار داخل پوشه یک پروژه، **اول PROJECT.md همان پروژه را بخواند.**
- پایان هر جلسه: (۱) Active Context/Progress پروژه‌های لمس‌شده آپدیت؛ (۲) [[01 - Dashboard/HANDOFF|HANDOFF]] بازنویسی شود (فقط wikilink به نوت‌ها، نه کپی محتوا، نه secret)؛ (۳) یک ورودی تاریخ‌دار در لاگ پروژه.
- نوت‌های ایندکس (Home، MOCها، PROJECT.md) زیر ۲۰۰ خط بمانند — لینک بدهند، کپی نکنند؛ سرریز به نوت خواهر منتقل شود.
- عبارت جادویی «**حافظه را به‌روز کن**» یعنی: Active Context و Progress همهٔ پروژه‌های active بازبینی و تازه شوند.

## ۹. تکراری‌ها

- فقط فایل **byte-identical** تکراری است → انتقال به `_Duplicates` (با حفظ مسیر) + ثبت در `_گزارش تکراری‌ها.txt`. هم‌نامِ متفاوت، تکراری نیست.
- پیشگیری: قبل از نوشتن نوت تلگرامی، `message_id` را (در محدوده همان `chat_id`) grep کن؛ اگر بود، skip — پایپ‌لاین idempotent است.
- داخل `.git` و `_code` هرگز dedup نکن.

## ۱۰. امنیت

- IMPORTANT: secret (کلید API، سید، پسورد، آدرس کیف پول) **هرگز** در چت، نوت، HANDOFF یا لاگ نوشته نمی‌شود.
- مسیرهای ممنوع: `.agentignore` (ماشین‌خوان). اجرای فنی: `.claude/settings.json` (deny + hooks) — متن این بخش لایه پشتیبان است.
- ربات تلگرام فقط از user ID مالک (whitelist) فرمان نوشتن می‌پذیرد.
- چک‌لیست چرخش secretها: `04 - Architect System/architect/01-Project/SECRETS-ROTATION-CHECKLIST.md`.

## ۱۱. اعتبارسنجی

بعد از هر ویرایش دسته‌ای و در شروع مرور هفتگی، هر دو را اجرا کن (dry-run):
`python "04 - Architect System/scripts/validate_frontmatter.py"` و `python "04 - Architect System/scripts/find_broken_links.py"`.
جلسه وقتی «تمام» است که هر دو پاس شوند. دامنه چک: لایه دست‌چین (پوشه‌های سیستمی، PROJECT.mdها، نوت‌های سطح‌بالای 03/07) — بسته‌های سند داخلی پروژه‌ها قرارداد خودشان را دارند.

## ۱۲. تاریخچه و نگهداری این فایل

- لاگ کامل پاکسازی/ارتقاها: `_Archive/Logs/Cleanup 2026.md`.
- نگهداری (فقط مالک): وقتی ایجنتی اشتباهی را **تکرار** کرد، دقیقاً یک خط قاعده اضافه کن؛ خط‌هایی که همیشه رعایت می‌شوند را حذف کن. سقف فایل: ~۲۰۰ خط.
