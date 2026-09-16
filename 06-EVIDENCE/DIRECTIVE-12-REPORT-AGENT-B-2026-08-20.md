---
type: evidence
task: directive-12
tags: [marker-search, signatures, golden-ui, disc-12, directive-12]
created: 2026-08-20T16:50+10:00
created_by: agent B (ZCode) — lease 308368bc
paid_calls: 0/0 · executable_unexpected: 0 · GAP-001: OPEN
---

# گزارش دستور مالک #۱۲ — ایجنت B

```text
STATIC MARKER SEARCH : writers_found=1 → _ops/RESTART-PROCESS.ps1:88-105
                       (جفت‌مارکر STOP+RESTART می‌نوشت؛ زیر lease به تک‌مارکری
                       اصلاح شد — کامنت + منطق write + finally فقط RESTART؛
                       تست رگرسیون جدید: هیچ فایلی در repo نباید هر دو مارکر
                       را بنویسد ⇒ ۶/۶ سبز)
T48/GUARD            : T48 report هنوز در راه (اتوماسیون 15:49)؛ نگهبان: همهٔ
                       اسکن‌ها OK، organism=9904 زنده، beat جلو، t48 events 5→8
TELEGRAM PRODUCER    : n=0 · late_real=0 (منتظر پیام‌های شما — بدون poll/backfill)
SERVER_CREATED       : n=0 · skew=n/a (پروب تک‌فراخوانی پشت امضا آماده است)
LIVE-B               : BLOCKED (وضعیت نام变了 نیازمند: تلگرام + server_created)
SIGNATURE WRAPPER    : READY (اجرا با شما — پایین)
EVENT-TIME PROBE     : calls=0 · receipt=— (پشت امضای payload-1)
GOLDEN LABEL UI      : READY · labeled=0/20
                       (research/judge_bias/golden_label_ui.py — کور، seed ثابت،
                       A_BETTER/B_BETTER/TIE/UNSURE، ذخیرهٔ تدریجی + resume؛
                       انتخاب ۲۰ جفت high-information اعتبارسنجی: ۱۰+۱۰، ۲۰ تسک یکتا)
FULL-LOOP FLASH      : NOT_RUN (پشت LIVE-B + امضا)
LAB-1 PHASE2         : NOT_RUN (session جدا؛ DeepSeek+GLM طبق رأی شما؛ GLM
                       unavailable ⇒ اجرا نشود)
DISC-12              : NOT_READY_FOR_ACTIVE_INFERENCE (با عدد اکتشافی — پایین)
MERGE                : BLOCKED (طبق رأی؛ 8b7e6e8 دست‌نخورده)
GAP-001 / LIVE-E     : OPEN / BLOCKED
availability_incidents: 0 جدید
executable unexpected: 0
commit / branch      : همین گزارش · equip/g10-cognition-20260816
```

## DISC-12 (§۹) — نتیجهٔ آفلاین با عدد

نگاشت (همان §۶-۷ گزارش #۱۰، این‌بار با داده): observation = جریان رویداد
system-domain (n=6,406)؛ preference/state = رنگ arbiter از تاریخچهٔ shadow
(GREEN=5091 · AMBER=186 · RED=0). surprise اکتشافی (پواسون fit نیمهٔ اول،
ارزیابی نیمهٔ دوم): میانگین surprise در پنجره‌های **GREEN=17.33** در برابر
**AMBER=17.81** ‏nat — تفاوت 0.48 nat، ‏n_AMBER=56 ⇒ ضعیف و کم‌توان؛ هیچ
پیوند کالیبره‌شده‌ای ثابت نمی‌شود. **حکم: ‏NOT_READY_FOR_ACTIVE_INFERENCE** —
مدل انتقال غایب و surprise کالیبره نیست؛ علیت ممنوع (همبستگی اکتشافی صرف).
گام‌های آمادگی: fit transition روی تاریخچهٔ spine + جمع‌آوری نمونهٔ RED +
تعریف C از setpoints.

## توقف یک‌باره (§۱۲) — اجرای شما

سه payload با هش پین‌شده و wrapper آماده‌اند:

```text
PAYLOAD-EVENT-TIME-PROBE-2026-08-20.json   sha256 = E175C9430647DA26096ABDB88B52DBC1F94E3E6CDCD9A0DC4C7F1FE322CB5157
PAYLOAD-JUDGE-BIAS-PHASE2-2026-08-20.json sha256 = D4DF6C0B7D0A9B0DF921A6354A0BD407036807E8092AAF10569E708B8E80CB84
PAYLOAD-FULL-LOOP-FLASH-2026-08-20.json    sha256 = E9DC768BF7761B3950DB9FAE5C0AEFFF0606B93808497D2073D11D994E90DFC9

فرمان (PowerShell، به‌عنوان مالک):
  powershell -ExecutionPolicy Bypass -File _ops\owner-runbook\SIGN-PENDING-CARDS-2026-08-20.ps1
خروجی مورد انتظار: TRUST ANCHOR OK → سه بار SIGN+VERIFY OK → ALL_THREE_SIGNATURES_VERIFIED
(هر اختلاف هش/لنگر = PARTIAL_SIGNATURE_FAILURE و امضا انجام نمی‌شود)
```

پس از `ALL_THREE_SIGNATURES_VERIFIED`، طبق §۱۳ به‌ترتیب: پروب تک‌فراخوانی →
تلگرام‌ها → صدور خودکار LIVE-B → FULL-LOOP (در صورت سبزی) — و فاز ۲ در session جدا.

## سه جملهٔ پایانی

مهم‌ترین فهم امروز: نویسندهٔ جفت‌مارکر یک اسکریپت «درست‌نما» بود که خودش
کامنتش ریشهٔ حادثهٔ ۲۰۲۶-۰۷-۲۸ را توصیف کرده بود و باز همان الگو را می‌نوشت —
بدهی مستندات واقعاً کد است. مهم‌ترین ندانسته: آیا surprise کالیبره‌شده با
رنگ arbiter رابطهٔ پایدار دارد — با صفر نمونهٔ RED و AMBER کم، داده کافی
وجود ندارد. خطرناک‌ترین باور: «سه امضا = سه آزمایش سریع» — هر سه کارت شرط
پیش‌نیاز خودشان را دارند (پروب مستقل، فاز۲ نیازمند GLM، فول‌لوپ پشت LIVE-B)؛
امضا فقط قفل را باز می‌کند، ترتیب را عوض نمی‌کند.
