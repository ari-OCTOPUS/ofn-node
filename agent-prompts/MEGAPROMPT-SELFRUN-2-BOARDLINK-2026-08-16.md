---
prompt_title: SELFRUN-2 BOARDLINK — اتصال کامل برد اورنج‌پای + بدهی‌ها + چک ری‌استارت
version: "2.0"
written_by: ZCode (GLM-5.3) — به درخواست مالک آرمین، 2026-08-16 ~24:10
audience: خودم (ZCode) — خوداجرا پس از نوشتن
mode: SELF-EXECUTE — اجازه‌ها واقعی و از زبان مالک
source_answers: "مصاحبهٔ ۴سؤالی 2026-08-16 24:0x — پاسخ‌ها زیر verbatim"
---

# 🐙 SELFRUN-2 BOARDLINK — برد، پل، ادغام، بدهی، ری‌استارت

## ۰. اجازه‌های واقعی مالک (پاسخ‌های مصاحبهٔ ۲۰۲۶-۰۸-۱۶)

| موضوع | رأی مالک |
|---|---|
| کانال سینک برد↔ویندوز | **هر دو** — SMB germline مسیرِ اصلیِ سینک و پیام‌رسانی؛ GitHub پشتیبانِ خودِ برد بماند. ویندوز فعلاً به GitHub نیازی ندارد (repo خصوصی + بدون credential). |
| پل زندهٔ کنترل (octopus-bridge) | **کامل روشن** — CONTROL_URL + کلید Bearer + فلگ‌ها. این رأی، قانونِ «هیچ فلگ WIRE تازه‌ای روشن نشود» را **فقط برای همین کانال بردِ داخل LAN** با تأیید مالک نقض/اصر می‌کند. هیچ کانال خروجی دیگری باز نمی‌شود. |
| ادغام کد پاها | **خودم ادغام کن + گزارش** — برد مقدم (NBB-V5)، هر پا جدا، diff کامل، گزارش per-leg، بدون رأیِ فایل‌به‌فایل. |
| دامنهٔ اجرا | **همه‌چیز + چک ری‌استارت** — برد + بدهی‌های معوق + بررسی acceptance ری‌استارت ۲۰۲۶-۰۸-۱۵ (۴ پروسه missing flags) و ترمیم. |

### قوانین ایستاده که سرِ جایشان می‌مانند (نقض = توقف)

1. **راز**: هیچ توکن/کلید/رمز/PAT در چت یا فایلِ گیت‌شده کپی نشود — فقط نام یا وضعیت. کلیدها در مسیر gitignored امن.
2. `.env` فقط نام کلید · کلید خصوصیِ `~/.octopus/signing` هرگز لمس نشود.
3. ماینینگ: تحلیل آزاد، اجرای مالی هرگز (D-10). هیچ اقدام مالی/بیرونی (ایمیل/پست/خرید/ثبت) از طرف ایجنت.
4. حذف صفر — فقط archive · ledger ها append-only.
5. اطلاعات حساس (محل اقامت پارتنر، حسابدار) فقط فایل امن/gitignored.
6. TCB: اگر پچِ TCB لازم شد → تست سبز + امضای manifest طبق روالِ تصویب‌شده (روایت مالک: «قوانینو خودم نوشتم»).
7. شواهد نه ادعا · بهبود نه بازنویسی · fail-closed.

## ۱. زمینهٔ زنده (2026-08-16 نیمه‌شب)

- **برد** (DietPi aarch64, `192.168.0.138`) نشست OFN-BOOT را تمام کرد: snapshot با ۲۱۳۵ فایل روی شاخهٔ `ofn/board-snapshot-20260816` (کامیت `b76a734`) در GitHub خصوصی `ari322/ofn-node` + heartbeat سرویس systemd (هر ~۱۰د push به `ofn/heartbeat`). SMB را بدون credential رد کرد (anonymous → ACCESS_DENIED).
- **ویندوز**: share اختصاصی `germline → E:\germline` ساخته شد (FullAccess: Armin) + رول‌های فایروال SMB-In فعال (Private+Domain) — لاگ: `E:\germline\ofn-smb-setup.log` و `ofn-smb-fix2.log`. پورت 445 از LAN تأیید شده.
- **گلوگاه GitHub**: repo خصوصی است؛ ویندوز credential ندارد (تست: ls-remote → cannot read Username؛ cmdkey خالی). پس فعلاً برد→GitHub یک‌طرفه است؛ SMB مسیرِ main.
- برد ۱۰ سؤال دارد (`QUESTIONS-FOR-OCTOPUS.md` داخل snapshot) — مهم‌ترین‌ها: CONTROL_URL، کانال کلید Bearer، SMB، پروتکل ادغام، مهلت چرخش راز ۱۷ اوت، شاخهٔ `ofn/wire`.
- ری‌استارت ۲۰۲۶-۰۸-۱۵ ۲۰:۵۳: acceptance FAILED — organism/center/cortex/live «missing flags» ولی «flags loaded equally: 338» و beat زنده. باید ریشه‌یابی شود.

## ۲. فازها — خوداجرا

### L0 — پیش‌شرط‌ها
- WORKLOCK چک (`01-Dashboard/HANDOFF.md`)؛ وضعیت git؛ فازِ active علامت‌گذاری.
- هر فاز تمام‌شده → کامیت. پیام کامیت‌ها با پیشوند `boardlink:`.

### L1 — سینک برد از germline
- چک `E:\germline\octopus.git` برای شاخه‌های `ofn/*` (board-snapshot / heartbeat) و فایل `E:\germline\ofn-heartbeat.txt`.
- اگر هنوز چیزی نیست (برد هنوز mount نکرده): فایلِ پیام `E:\germline\FOR-BOARD-CONNECT-NOW.md` بساز (دستور مونت + «از E$ استفاده نکن») و به مالک بگو همان را به برد بدهد. منتظرِ نماندن — بقیهٔ فازها بدون سینک هم پیش می‌روند؛ L2 بعد از رسیدنِ push انجام می‌شود.
- وقتی رسید: `git fetch germline` + لاگ شاخه‌ها.

### L2 — ادغام per-leg (برد مقدم، خودکار + گزارش)
- شاخهٔ snapshot را در worktree جدا checkout کن (نه روی master).
- تطبیق پاها: hypno (اونلی‌فنز) / lead (لیدنقاشی) / studio (زیمان‌گالری؟ تطبیق نام‌ها با کپی‌های ویندوز در `03 - Projects/`) / ziman / mining / project-f.
- برای هر پا: `git diff` درختِ برد ↔ کپیِ ویندوز، فهرست فایل‌های متفاوت/جدید/حذف‌شده، سپس نسخهٔ برد را مقدم کن (کپی به مسیر ویندوز با archive از نسخهٔ قبلی: `_archive/legs/<leg>-pre-merge-20260816/`).
- گزارش per-leg در `06-EVIDENCE/BOARD-MERGE-2026-08-16.md` + کامیت جدا per-leg.
- هیچ چیز از ویندوز روی برد overwrite نشود.

### L3 — پل کامل روشن (owner: «کامل روشن»)
1. **تحقیق**: در کد ویندوز دنبال `board-cp` / `board_cp` / مسیرهای `/api/board-cp/pull` و `/ack` بگرد (cortex/gateway/center). اگر endpoint هست → فقط فعال‌سازی؛ اگر نیست → پیاده‌سازی مسیرِ pull/ack در سرویسِ مناسب (اگر فایل TCB → روال امضا).
2. **CONTROL_URL**: `https://192.168.0.191:<پورت>` — پورت ≠ 8796 و خارج از بازهٔ 8771-8777 (پیشنهاد: 8801). binding غیر-loopback. TLS self-signed + fingerprint pin در سندِ راهنمای برد (نه در کد).
3. **کلید Bearer**: ≥32 بایت random. ذخیرهٔ ویندوز: مسیر امن gitignored (مثل بقیهٔ رازها، فقط نام فایل در مستندات). تحویل به برد: فایل `E:\germline\ofn-bearer.key` (share فقط Armin) → مالک به برد می‌گوید برد بگیرد → بعد از تأیید مالک («برد گرفت») فایلِ share حذف شود.
4. **فلگ‌ها**: فقط فلگ‌های همین پل (نام‌گذاری صریح، پیش‌فرض off، fail-closed). روشن‌کردن با کامیت + مستند در `03-GATES/GATES.md` (گیتِ board_cp از closed → open با رأی مالک ۲۰۲۶-۰۸-۱۶).
5. **تست رفت‌وبرگشت**: از خود ویندوز یک GET pull با Bearer (بدون چاپ کلید) → کد وضعیت + لاگ. تستِ واقعی برد بعد از اتصالش.

### L4 — پاسخ ۱۰ سؤال برد
- فایل `ANSWERS-FROM-OCTOPUS.md` در ریشهٔ `E:\germline\` (share) — پاسخ کاملِ هر ۱۰ سؤال بر اساس نتایج L1-L3 (CONTROL_URL، کانال کلید، SMB آماده است، پروتکل ادغام، polling، چرخش راز ۱۷ اوت [تحقیق کن معلوم نیست از کجا آمده]، کامیت کد کنسول، 404 app/hypno، ofn/wire).

### L5 — دو gauge ناشناختهٔ شب
- gauge #1 root + cortex-2nd-try (از گزارش نشست شب) — ریشه‌یابی با شواهد در `06-EVIDENCE/`.

### L6 — پنجره‌های پوشش B/D/E/G
- طبق گزارش continuous-improve؛ هر پنجره یک بخش شواهد.

### L7 — کامیت working tree کثیف + ledger
- فایل‌های modified فعلی (OCTOPUS-DOCTOR state ها، CURRENT-TRUTH، HEARTBEAT، …) با پیامِ واضح کامیت.
- CONTRADICTIONS (آزادِ بعدی C-031 اگر تناقضِ نو پیدا شد) · OPEN-VERDICTS · MEASUREMENT در صورت سنجهٔ جدید.

### L8 — چک ری‌استارت (acceptance دیروز)
- علتِ «missing flags» با «flags loaded equally: 338» — آیا acceptance script مقایسهٔ stale می‌کند یا پروسه‌ها واقعاً فلگ ندارند؟ ریشه‌یابی + ترمیم + اگر ری‌استارت لازم شد: طبق روال RESTART-ALL + acceptance سبز.

### L9 — گزارش نهایی مالک
```
فازهای کامل: L1..L8 — وضعیت هرکدام
برد: snapshot رسید؟ (sha) · ادغام per-leg: چه شد · پل: CONTROL_URL + فلگ + کلید (نام فقط)
بدهی‌ها: gauge ها · پنجره‌ها · کامیت‌ها (شمار + sha)
ری‌استارت: ریشهٔ missing flags + وضعیت الان
اقدام لازم مالک: (مثلاً «به برد بگو mount کند» / «برد گرفت کلید را»)
```

## ۳. مرز — چه نکنی

- هیچ push به GitHub از ویندوز (credential نیست) · هیچ رازی در چت/گیت · هیچ overwrite از سمت ویندوز روی کد برد · هیچ کانال خروجی غیر از پلِ تأییدشدهٔ برد · حذف صفر (به‌جز فایل bearer در share بعد از تأییدِ تحویل — که خودش «پاک‌سازیِ راز» است، مجاز).
- اگر برد هنوز وصل نشده: متوقف نکن — L5-L8 مستقل پیش می‌روند.

[END]
