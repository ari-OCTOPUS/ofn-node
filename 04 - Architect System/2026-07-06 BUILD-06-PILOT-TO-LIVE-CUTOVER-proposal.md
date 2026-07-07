---
type: runbook-proposal
status: proposal            # propose-only — پروتکلِ نهاییِ go-live. اجرا فقط با verdictِ آری.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «همه‌رو بساز تا آخر» 2026-07-06 → قدمِ ۶ (آخر)"
depends_on: "BUILD-01..05 · PENTA-SYSTEM-REPORT+REVIEW · RESEARCH-GENOME-RECONCILIATION"
grounds: [ARCHITECT_CHARTER §۱ (propose→approve، timeout=DENY), LEARNING-STATE pilot LAPTOP-PILOT-30D]
tags: [build-06, cutover, go-live, pilot, index, propose-only]
---

# BUILD-06 — پایلوت ۳۰روزه → cutover به live (propose-only، آخر)

> **این قدم چیزی را روشن نمی‌کند؛ *ترتیبِ* روشن‌کردن را قفل می‌کند.** هر گذار = یک verdictِ صریحِ آری، یکی‌یکی، از امن‌ترین به کم‌امن‌ترین. timeout = DENY (منشور §۱).

---

## ۱. پیش‌شرط‌های سبز (همه باید ✅ باشند پیش از هر live)
| # | پیش‌شرط | منبع | چک |
|---|---|---|---|
| ۱ | **دریفت‌های ژنوم حل شده** (D1 mode · D2 گیت · D3 تک‌whitelist) | تطبیق | ژنوم باید *سازگار* باشد قبل از live |
| ۲ | بک‌اپ + restore-drillِ موفق | BUILD-01 | `LAST-OK` تازه، یک restore تست‌شده |
| ۳ | گاردِ ژنوم فعال + GENOME-LOCK ست | BUILD-02 | تغییرِ آزمایشی → CRITICAL |
| ۴ | شمارندهٔ بودجه فعال + تست‌شده | BUILD-05 | سقف → deny |
| ۵ | GOVERNOR shadow ۳۰ روز تمیز | BUILD-03 | uptime، دقتِ alert، صفر CRITICALِ رسیدگی‌نشده |
| ۶ | MUSE/دکتر dry-run کالیبره | BUILD-04 | دقتِ would-forward + تنوعِ حفظ‌شده |

## ۲. نگاشت به پایلوتِ موجود
`LAPTOP-PILOT-30D` (day_zero = 2026-07-06، در STATE) = همین پنجرهٔ ۳۰روزه. checkpointِ هفتگی؛ لاین‌های پرفرکانس `*/3,*/5` **dark** تا پایان (scope_dark موجود).

## ۳. ترتیبِ go-live (امن‌ترین → کم‌امن‌ترین؛ هرکدام یک verdict)
1. **حلِ دریفت‌ها (D1/D2/D3)** — ویرایشِ دستیِ مالک؛ سپس `genome_guard --init` دوباره. *(ژنوم اول سازگار شود.)*
2. **budget counter → روشن** (BUILD-05). بی‌ریسک، پیش‌نیازِ هر خرجِ خودکار.
3. **GOVERNOR: shadow → live.** تازه اینجا routingِ LLM + اقداماتِ *از-پیش-تأییدشده* را می‌گیرد؛ ولی تغییرِ قاعده همچنان propose-only.
4. **MUSE/دکتر: dry-run → live-forwarding.** دکتر بازمانده‌ها را به تلگرامِ مالک forward می‌کند (نه اجرا).
5. **(خیلی بعد، verdictِ جدا)** روشن‌کردنِ callهای خارجیِ خودکار یا لاین‌های dark — محافظه‌کارانه‌ترین، آخر.

## ۴. rollback (اگر هر نشانهٔ بد)
- فایلِ `STOP` → همه‌چیز HALTED (D-06).
- هر live → برگرد به shadow/dry-run (فقط زمان‌بند را عوض کن).
- خرابیِ داده → restore از بک‌اپِ رمزشده (BUILD-01).
- خطِ فاجعهٔ $500 → halt کامل، بازبینیِ انسانی.

## ۵. عملیاتِ جاری (بعد از live)
- **هفتگی:** مرورِ خروجیِ دکتر + alertهای GOVERNOR + ردیف‌های forwardشدهٔ MUSE.
- **ماهانه:** restore-drill (BUILD-01) + مرورِ اشتراک Fugu (checklist موجود).
- **فصلی:** رادارِ آیندهٔ ۲۴ماهه (از تطبیق Q3) — Adopt/Trial/Assess/Hold.
- **تغییرِ ژنوم:** همیشه با workflowِ سه‌مرحله‌ایِ قفل (BUILD-02 §۶).

## ۶. فهرستِ کاملِ ساخت (INDEX — ۱۴ سند، همه propose-only)
| فاز | سند |
|---|---|
| مبنا | `RESEARCH-GENOME-RECONCILIATION-proposal` |
| طرح | `PENTA-PROMPT-Governor-Muse-proposal` |
| ۱ | `PHASE1-GOVERNOR-MUSE-CHARTER-proposal` |
| ۲ | `PHASE2-GOVERNOR-SPEC-proposal` |
| ۳ | `PHASE3-MUSE-SPEC-proposal` |
| ۴ | `PHASE4-MEMORY-INTEL-DOCTOR-proposal` |
| ۵ | `PHASE5-BACKUP-DR-INTERLOCKS-proposal` |
| گزارش | `PENTA-SYSTEM-REPORT+REVIEW` |
| build ۱ | `BUILD-01-OFFBOX-BACKUP-runbook-proposal` |
| build ۲ | `BUILD-02-GENOME-READONLY-GUARD-runbook-proposal` |
| build ۳ | `BUILD-03-GOVERNOR-SHADOW-runbook-proposal` |
| build ۴ | `BUILD-04-MUSE-DOCTOR-DRYRUN-runbook-proposal` |
| build ۵ | `BUILD-05-SHARED-BUDGET-runbook-proposal` |
| build ۶ | `BUILD-06-PILOT-TO-LIVE-CUTOVER-proposal` (این سند) |

## ۷. چک‌لیستِ verdictهای مالک (دروازهٔ go-live)
- [ ] دریفت‌ها D1/D2/D3 حل شد؟
- [ ] مقصدِ بک‌اپ (§۲ BUILD-01) انتخاب شد؟
- [ ] فایل‌های `scripts/*` (backup/guard/governor/budget) را propose کنم تا بگذاری؟
- [ ] بلوکِ منشورِ فاز ۱ را در `ARCHITECT_CHARTER` پیست کردی؟
- [ ] ارتقاها را به ترتیبِ §۳ یکی‌یکی verdict می‌دهی؟

## ۸. ردیفِ ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | REPORT §۴ قدم۶ | پروتکلِ cutover + ترتیبِ go-live + index | pending-verdict |

---

*propose-only. کلِ نقشه کامل شد؛ هیچ ژنوم/کد تغییر نکرد و چیزی اجرا/نصب نشد. اجرا = verdictِ آری، به ترتیبِ §۳.*
