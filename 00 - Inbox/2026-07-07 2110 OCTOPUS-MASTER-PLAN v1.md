---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, organism]
created: 2026-07-07
updated: 2026-07-07
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT]]"
  - "[[_ops/ORGANISM-SPEC]]"
---

# OCTOPUS · MASTER-PLAN v1 (plan-only — هیچ چیزی ساخته نشده)

> دستور واحد اپراتور 2026-07-07 (~۲۱:۰۰): فقط پلن. append-only. هر جا تصمیم لازم بود → open-decisions، نه فرض.

## گام ۰ — واقعیت‌سنجی [audit زنده @ 2026-07-07 21:03 — نه از حافظهٔ جلسه]

**تأییدشده روی سیستم:**
- repo: ‏HEAD ‏`5606fb4`؛ germline: دو bundle سبز (`2040`/`2046`، هر دو ۵۷۹ نوت، ledger دوسویه OK) + ‏bare ‏`E:\germline\vault.git` + ‏manifest ‏`drill: PASS`؛ هر دو تسک germline در حالت Ready.
- گیت‌ها: preflight ‏۱۵/۱۵ دوباره PASS (kill مسلح و نپریده · budget_gate v1.1 با deny ‏functional · هر دو live-gate قفل + پرچم‌ها غایب = صفر مسیر پول).
- تولد واقعی بود: سه tick (‏20:42/47/52)، pulse آلوستاتیک 0.047→57.9min، دو NOTE در ledger، زنجیره سالم.

**سه یافتهٔ نو (فقط ثبت — plan-only):**
1. 🔴 **INC-1 — ارگانیسم مرده (از ~20:53):** پورت 8771 ‏refused؛ هیچ python/cmd زنده؛ هیچ alert/ledger-fallback/heartbeat خروج — یعنی kill خارجی پروسه+launcher با هم. محتمل‌ترین علت: teardown ‏job سندباکس ایجنت (فرزند Start-Process با پایان shell کشته می‌شود). **درس ساختاری: تولد پایدار فقط با لانچ مالک (دابل‌کلیک) یا Scheduled Task — نه از shell ایجنت.**
2. 🟠 **INC-2 — اولین اجرای scheduled ‏germline-hourly ‏FAIL** (20:49، ‏exit 1؛ اجرای دستی 20:39 سبز). ‏stderr در log ثبت نمی‌شود → علت نامعلوم. تا فیکس: لایهٔ روزانه + دستی پوشش می‌دهد. [RE-VERIFY: اجرای 21:49]
3. 🟡 کامیت ‏`add -A` قبلی سه فایل state ارگانیسم را ناخواسته tracked کرد → repo با هر tick دائم dirty می‌شود (soma داخل germline). فیکس = gitignore با verdict (C6).

---

## Track A — P1 ایمنی پول

| | |
|---|---|
| هدف | پیش از هر مسیر زنده: enforcement کامل اعداد verdict-خورده + گیتِ توانایی به‌جای تقویم |
| وضعیت | budget_gate v1.1 هاردکد (همه-AUD) سبز؛ ‏human_gate_aud=20 و لوپ=10 فقط در SoT؛ ‏live_gate = تاریخ+پرچم |
| گپ | v2 ‏SoT-read نیست؛ آستانهٔ AU$20 ماژول enforcement ندارد؛ گیت calendar است؛ V2/MAX_LAG ساخته نشده |

**قدم‌ها:**
- **A1 · budget_gate v2** — خواندن سقف‌ها از `_ops/budget/budgets.yaml` با fallback ‏fail-closed = سخت‌گیرترینِ (yaml، هاردکد فعلی) اگر yaml ناخوانا؛ ‏bucket per-organ واقعی (پارامتر agent دیگر بی‌اثر نباشد). فایل‌ها: `scripts/budget_gate.py` + تست نو `_ops/tests/test_budget_gate_v2.py` + به‌روزرسانی زنجیر organ_gate. تخمین: ~۱ جلسه.
- **A2 · money_gate (enforcement ‏AU$20)** — ماژول نو `_ops/budget/money_gate.py`: قرارداد «هر effector پول واقعی پیش از عمل `check(amount_aud, approval_token)`»؛ > ‏human_gate_aud بدون token معتبر (فقط از صف انسانی control-brain) = deny + log. تستِ جعل token. الان مصرف‌کننده ندارد (paper) ولی دیوار باید پیش از اولین مصرف موجود باشد. تخمین: ~نیم جلسه.
- **A3 · capability-gate** — ‏`opslib.live_gate_open` سه‌شرطی شود: (تاریخ ≥ 07-21 به‌عنوان کف) **AND** پرچم مالک **AND** ‏marker ‏CAPABILITY-OK که فقط اجرای سبزِ سوئیت (شامل تست‌های A1/A2) می‌نویسد. رسیدن تاریخ به‌تنهایی دیگر هیچ‌چیز باز نمی‌کند. فایل‌ها: ‏opslib + تست‌های live-gate موجود. ⚠ تغییر تعریف قفل = verdict (open-decision #2).
- **A4 · V2 ledger** — ‏type جدید در `genome-system/ledger/ledger.py` ‏EVENT_TYPES ‏(`MONEY_ATTRIBUTION`؛ کاندید دوم `TRUST_EVENT`) + تست سازگاری زنجیره + CHANGELOG ‏v0.4.4. ⚠ ویرایش هستهٔ ژنوم = تأیید مالک (open-decision #3).
- **A5 · MAX_LAG vital** — ‏`germline_lag = now − max(manifest.stamp، آخرین push موفق hourly.log)` در ORGANISM-STATE + آلارم. پیشنهاد عددی: >2h ‏warn، >26h ‏ERROR (open-decision #4).

وابستگی: A1،A2 → A3؛ ‏A4 → B2. ریسک: پیچیدگی parser داخل gate (کوچک نگه داشته شود)؛ جعل marker (امضای محتوایی ساده + تست). **DoD:** سوئیت + preflight توسعه‌یافته سبز؛ اثبات اینکه پس از 07-21 بدون capability+انسان هیچ گیتی باز نمی‌شود.

## Track B — اولین tentacle درآمد در paper mode: ‏Lead-نقاشی (Rule Zero)

| | |
|---|---|
| چه دلاری؟ | فاکتورهای شغل نقاشی که همین حالا در بیزنس واقعی آری جاری‌اند — paper یعنی سیستم فقط draft/ردیابی می‌دهد، ارسال/دریافت فقط انسان |
| ورودی سنجش‌پذیر | ‏lead (نام/کار/کانال) از فرم پنل یا نوت |
| خروجی سنجش‌پذیر | ‏draft کوت + فالوآپ + ‏attribution_id چاپ‌شده روی کوت |
| متریک حقیقت | ‏AUD ‏CONFIRMED پس از reconcile با feed مستقل، در پنجرهٔ ۷روزه (verdict قبلی) + ‏attribution_coverage |

**قدم‌ها:** ‏B1 قرارداد carrier (فرمت id مثلاً `LEAD-YYYYMMDD-nnn`، جای چاپ روی کوت/فاکتور — open-decision #9) · ‏B2 ‏`_ops/budget/attribution.py` (mint/lifecycle ‏PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED) + ‏`reconcile.py` (تطبیق CSV، ترفیع فقط توسط job، ‏mismatch=CONFLICT-freeze) — وابسته به A4 · ‏B3 فرم lead در پنل 8790 (`_ops/panel/server.py`) · ‏B4 اتصال fitness (فقط CONFIRMED؛ پنجره+grace) · ‏B5 حلقهٔ هفتگی reconcile با CSV اپراتور (فرمت/مسیر = open-decision #5).
تخمین: ۲–۳ جلسه پس از A4. ریسک: coverage پایین → اول carrier اصلاح شود (طبق MONEY-ATTRIBUTION v1). human-gate: هر تماس با مشتری = انسان؛ دادهٔ مشتری فقط لوکال، هرگز به Fugu (قاعدهٔ privacy موجود). **DoD:** اولین دلار paper-CONFIRMED با attribution صحیح + گزارش coverage.

## Track C — سخت‌سازی و رصد

- **C1 · فیکس INC-2:** ‏hourly script باید stderr گیت‌ها را در log بنویسد + retry/backoff؛ ریشه‌یابی FAIL ‏20:49. (اولین آیتم ساخت پس از تأیید پلن.)
- **C2 · فیکس INC-1:** تسک `organism-autostart` (at-logon) + ‏watchdog ۱۵دقیقه‌ای «اگر 8771 مرده و هیچ STOP نیست → استارت» — تسلیمِ بی‌قیدوشرط به STOP (persistence نه resistance).
- **C3 · smoke ‏۲۴ساعته:** چک‌لیست: state تازه‌تر از ۱۰min · ‏heartbeat ساعتی · صفر alert/ledger-fallback · ‏ledger verify · خرج $0 · یک epoch-log منطقی.
- **C4 · داشبورد 8771:** صفحهٔ «/» غنی‌تر (فقط‌خواندنی): pulse/organs/σ/‏germline_lag/‏attribution_coverage + لینک manifest. فایل: `_ops/organism.py`. نکتهٔ audit: کلیدهای daily (σ و fitness) فقط در tick روزانه در state می‌مانند — در C4 باید persist شوند.
- **C5 · tier ابری germline:** طبق [[04 - Architect System/architect/01-Project/M0.5-RESTORE-RUNBOOK-proposal|M0.5-runbook]] §۱–۳ — ‏rclone crypt، ‏credential فقط دست مالک، بدون ‏.env، کاندید B2 (open-decision #7)؛ سپس تسک روزانهٔ push آخرین bundle + یک restore-drill ابری.
- **C6 · تکلیف soma-state در git:** فایل‌های runtime ‏(`ORGANISM-STATE.json`، ‏`telemetry-latest…`) از germline جدا شوند (gitignore) تا repo دائم dirty نباشد — چون ‏.gitignore حساس است، فقط با verdict (open-decision #8).

**DoD:** ‏۲۴h سبز + آلارم germline_lag فعال + اولین restore-drill ابری سبز.

## Track D — tentacle فروش 07-20 (human-gated؛ عمداً مستقل از A)

هدف: تا 2026-07-20 سه pitch شخصی‌سازی‌شدهٔ Coherence-Audit «ارسال‌شده توسط انسان». چون هیچ حرکت پولی/ارسالی توسط سیستم نیست، به budget_gate v2 وابسته نیست و می‌تواند اول برود.
**قدم‌ها:** ‏D1 آری ۳ مخاطب بدهد (**بدون این، کل track خوابیده — open-decision #6**) · ‏D2 تحقیق عمومی هر مخاطب (بدون هیچ تماسی) + ‏draft شخصی از [[00 - Inbox/2026-07-06 1410 COHERENCE-AUDIT-PITCH-draft|COHERENCE-AUDIT-PITCH]] · ‏D3 چک‌لیست ارسال/فالوآپ human-gated + ثبت دستی attribution_id (پل به Track B) · ‏D4 پس از پاسخ مثبت: draft توافق کوچک ($3–5k طبق pitch).
تخمین: ~۱ جلسه پس از D1. **DoD:** ۳ پیام آمادهٔ ارسال پیش از 07-18 و ارسال توسط آری پیش از 07-20.

## هم‌گرایی — گراف وابستگی و critical path

```
INC-1 (استارت مالک/C2) ─► C3 smoke24h ─► اعتماد پایه
D1 (۳ مخاطب) ─► D2→D3→D4      [ددلاین سخت 07-20 — مستقل، اول برود]
A4 (V2 ledger) ─► B2 (attribution) ─► B3/B4/B5 ─► 💵 اولین paper-$
A1 (bg v2) ─┬─► A3 (capability-gate) ─► (آینده) هر مسیر live
A2 (money_gate) ┘
C1، C5، C6 مستقل و موازی
```
**ترتیب پیشنهادی:** ‏(۱) INC-1 استارت مالک + C1/C2 → ‏(۲) D1→D (ددلاین) → ‏(۳) A4 → A1+A2 → A3 → ‏(۴) B2..B5 → ‏(۵) C4/C5، مرور. ‏**Milestones:** ‏M-safe (Track A سبز) · ‏M-pitch (D پیش از 07-20) · ‏M-hard (C: ‏۲۴h+ابر) · ‏M-paper$ (B: اولین دلار CONFIRMED). **DoD کلی:** هر چهار milestone + صفر نقض ناوردی + گزارش test-backed.

## ناوردی‌های سختِ encode شده

هیچ مسیر پول واقعی تا سبزیِ budget_gate v2 + money_gate (A3 ‏marker) · ‏07-21 = کفِ تقویمی داخل گیتِ توانایی+انسان، نه کلید · ‏paper→live فقط proven+trust+human · ‏germline-first (بک‌آپ دولایه + MAX_LAG ‏vital) · ‏kill-switch مقدم (watchdog تسلیم STOP) · ‏persistence نه resistance · ‏anti-injection (فنس موجود + تست) · ‏SECRET-GUARD (هرگز ‏.env؛ whitelist نام فایل).

## open-decisions (منتظر verdict اپراتور — فرض نساخته‌ام)

1. **INC-1:** ری‌استارت ارگانیسم — الان دابل‌کلیک خودت، یا صبر تا C2 ‏autostart؟ (پیشنهاد: هر دو — الان دستی، C2 بعداً.)
2. تأیید تبدیل live_gate به capability+human (A3) — تغییر تعریف قفل.
3. تأیید ویرایش EVENT_TYPES ژنوم برای V2 (A4) — حاکمیت هستهٔ ledger.
4. اعداد MAX_LAG (پیشنهاد: warn>2h، ‏ERROR>26h).
5. ‏feed ‏reconcile: فرمت/مسیر CSV بانک/حسابداری + کادنس (هفتگی?).
6. **۳ مخاطب pitch ‏(D1) — بازکنندهٔ کل Track D.**
7. مقصد tier ابری (Backblaze B2?) + زمان ساخت credential (فقط خودت).
8. ‏gitignore کردن soma-state ‏(C6).
9. فرمت/جای چاپ carrier-id کوت Lead ‏(B1).
10. بودجهٔ زمانی هفتگی خودت برای reconcile دستی فاز A.

## [RE-VERIFY]های ثبت‌شده برای جلسات بعد

نتیجهٔ اجرای hourly @21:49 (INC-2) · پایداری organism پس از استارتِ مالک (چند tick + heartbeat) · قیمت DeepSeek از کنسول platform هنگام اولین call زنده · دسترسی AU ‏Sakana + ‏base_url ‏[OPEN] · رفتار σ/fitness پس از ۲۴ ساعت داده.
