---
type: owner-acceptance-record
status: ACCEPTED_WITH_CONDITIONS — verdict مالک از چت، 2026-08-18 ~22:15 +10:00، عیناً ثبت شد
card: F1-ACCEPTANCE-RECORD
created: 2026-08-18 ~22:1x +10:00
created_by: agent (ZCode GLM-5.3, node .191) — فقط پیش‌نویس؛ verdictها مالک پر می‌کند
program: OCTOPUS FOUNDATION HARDENING v1 · Stage F1
sources:
  - "06-EVIDENCE/F1-191-20260818-2122/00-REPORT.md (verdict: PASS)"
  - "06-EVIDENCE/F1-191-20260818-2122/MANIFEST.sha256 (۲۷ هش)"
  - "agent-prompts/MEGAPROMPT-FOUNDATION-F1-REALITY-INVENTORY-191-2026-08-18.md"
  - "فرمان مالک: OWNER-CHIEF DECISION — EXECUTE FOUNDATION F1 (2026-08-18)"
  - "اصلاح مالک (relay 2026-08-18 ~22:08): canonical vault = F:\\backup به حکم پیشین؛ مسئلهٔ باز نگاشت artifactهاست نه انتخاب ریشه"
tags: [octopus, foundation, f1, acceptance, owner-decision]
---

# F1-ACCEPTANCE-RECORD — رکورد پذیرش مرحلهٔ F1

## Change Contract (کارت مجاز — عیناً از حکم مالک)

```text
CARD-ID: F1-ACCEPTANCE-RECORD
TYPE: Owner-decision document only
TARGET: 02-DECISIONS
ALLOWED: ثبت پذیرش/رد F1 و هفت تصمیم باز
FORBIDDEN: کد، اسکریپت، rename، move، delete، scheduler، شبکه، SSH
ROLLBACK: حذف‌نکردن؛ supersede با تصمیم بعدی
```

وضعیت حاکم تا امضا:

```text
STATE = STOP_FOR_OWNER_ACCEPTANCE
F1 = PASS_REPORTED / OWNER_ACCEPTANCE_PENDING
R01 = NOT_AUTHORIZED
CODE_CHANGES = FORBIDDEN · SCHEDULER_CHANGES = FORBIDDEN
BOARD_180 = UNKNOWN / NO_CONTACT
```

---

## بخش ۱ — Verdict مالک (پر شود)

```yaml
owner_verdict:    ACCEPT_WITH_CONDITIONS
owner_timestamp:  2026-08-18 ~22:15 +10:00 (chat — عین متن در بایگانی چت سشن)
owner_statement:  "F1 را به‌عنوان «PASS_REPORTED» می‌پذیرم، اما نه به‌عنوان اثبات نهایی.
                  R01 مجاز است فقط برای بازرسی، بازتولید، تست، کشف خطا و تهیهٔ patch/proposal
                  قابل بازگشت؛ نه deploy، daemon، scheduler، network discovery جدید، SSH به بردها،
                  تغییر credential، یا فعال‌سازی autonomy."
owner_conditions: پیش از R01: D1 (تأیید MANIFEST) — اجرا و ثبت شد (D1-EXECUTION، پایین)
```

### D1-EXECUTION (شرط، اجرا شد)

```text
command:  sha256sum -c 06-EVIDENCE/F1-191-20260818-2122/MANIFEST.sha256   (از ریشهٔ F:/backup)
result:   27/27 OK · exit=0
record:   06-EVIDENCE/F1-191-20260818-2122/D1-MANIFEST-VERIFY.txt
executed: 2026-08-18 ~22:2x +10:00
downgrade_to_EVIDENCE_UNAVAILABLE: NOT_REQUIRED (manifest fully verified)
```

## بخش ۲ — هفت تصمیم باز (وضعیت هرکدام را مالک تعیین می‌کند)

| # | تصمیم | گزینه‌ها | توصیهٔ ایجنت (غیرالزام‌آور) |
|---|---|---|---|
| D1 | پذیرش بستهٔ شواهدی F1 | ACCEPT / REJECT / ACCEPT_WITH_CONDITIONS | ACCEPT — شش نقشه کامل، هر ادعا برچسب خورده، بازتولیدپذیر با MANIFEST |
| D2 | سرنوشت `/sh` (مسلح، پرچم ACTIVATION موجود) | KEEP_ARMED / DISARM_UNTIL_TWO_STAGE | DISARM تا گیت دومرحله‌ای — تا تأیید enforcement در F4 |
| D3 | `_ops/legs/mail_credentials.py` در git tracked | UNTRACK+ROTATE / KEEP_LOCAL_ONLY | UNTRACK + چرخش اعتبارنامه (یافتهٔ HIGH) |
| D4 | CARD-001 با فرضیهٔ ضعیف‌شدهٔ memory.db | CONTINUE_REPRODUCTION / REPLACE_WITH_FIRST_REPRODUCIBLE_GAP | REPLACE — یتیم ۱۱روزه بدون نویسندهٔ فعال؛ store زنده سالم |
| D5 | داربست `octopus-research-sprint/` (ساخته‌شدهٔ موازی حین F1) | RATIFY / FREEZE_UNTIL_F1_ACCEPTED | RATIFY اگر موج صفر از پیش تصمیم بود؛ در غیر این صورت FREEZE |
| D6 | بازگشت LAN و discovery بردها | SCHEDULE / DEFER | هر زمان دسترسی فیزیکی — پیش‌نیاز مرحلهٔ ۱۴+ |
| D7 | طبقه‌بندی ۵ worktree + ۲ stub-git + ۷ باندل | CONFIRM_AS_F2_INPUT / AMEND | CONFIRM — ورودی مستقیم CANONICAL_REGISTRY در F2 |

```yaml
D1: ACCEPT_WITH_CONDITIONS  # شرط MANIFEST — اجرا و ثبت شد، 27/27 OK
D2: DISARM_UNTIL_TWO_STAGE  # /sh و هر activation flag تا اثبات enforcement در تست مستقل و
                            # تأیید دومرحله‌ای غیرفعال بماند
D3: UNTRACK_AND_ROTATE      # فاز فعلی: فقط locate + metadata + git-history inspection +
                            # evidence report؛ چرخهٔ واقعی credential فقط با OwnerDecision
                            # جداگانه و اجرای انسانی؛ هیچ چاپ/کپی/commit/push/ارسال
D4: REPLACE_WITH_FIRST_REPRODUCIBLE_GAP  # CARD-001 از فرض memory.db شروع نشود مگر با اثبات
                            # writer/reader/schema/freshness + failure قابل بازتولید با trace مستقل
D5: FREEZE_UNTIL_R01_BASELINE_COMPLETE   # octopus-research-sprint/ فقط inventory؛ اجرا ممنوع
D6: DEFER                   # LAN discovery، SSH، هر تماس با .138/.180/.182 ممنوع؛
                            # BOARD_180 = UNKNOWN / NO_CONTACT حفظ شود
D7: CONFIRM_AS_R01_INPUT   # worktreeها/stub-gitها/bundleها فقط طبقه‌بندی و hash؛
                            # rename/move/delete/archive/merge ممنوع
```

## بخش ۳ — مرجع دقیق artifactهای F1

```text
run_id:        F1-191-20260818-2122
capture_dir:   F:\backup\06-EVIDENCE\F1-191-20260818-2122\
window:        2026-08-18T21:22:00+10:00 → 2026-08-18T21:55:35+10:00
executor:      ZCode GLM-5.3 (node .191, DESKTOP-KA9RFN5)
self_verdict:  PASS (با caveat نویسندهٔ موازی، گزارش §C-7)

هش‌های کلیدی (کامل در MANIFEST.sha256):
  00-REPORT.md        sha256=ba978d9378ed54ea7689c0da37e4d512672f994665238a7da84c787ed08a839e
  command-log.md      sha256=5c1d85aa3755499c55d5746c565f2605618ead1b860a99e0da24295c4f3264c7
  03-storage-30d.tsv  sha256=445712ae46a688f512bd00ed4cd6315eecb7fddae246d248440f9afc9ee50bb
بازتولید صحت:  sha256sum -c 06-EVIDENCE/F1-191-20260818-2122/MANIFEST.sha256   (از ریشهٔ F:/backup)
```

## بخش ۴ — مجوز فعال‌سازی R01 (پر شود)

```yaml
r01_authorized:      true
r01_input_bundle:    "06-EVIDENCE/F1-191-20260818-2122/ (verified 27/27)"
r01_models:          "طبق طرح: دو مدل مستقل؛ این سشن (.191 / ZCode GLM-5.3) اجراکنندهٔ بازرسی است"
r01_scope:           "بازرسی، بازتولید، تست محلی فقط-خواندنی/بدون-شبکه، نگاشت API/حافظه/یادگیری/
                      evidence/حاکمیت، کشف کد مرده و fake-metric و silent-failure، گزارش باگ و
                      پچ پیشنهادی قابل بازگشت — هیچ deploy/daemon/scheduler/شبکه/SSH/راز"
r01_forbidden:       "عیناً طبق verdict مالک (deploy · daemon/timer/cron/scheduler/service ·
                      network discovery · board contact · SSH · API با اثر جانبی · نمایش/کپی/
                      commit/push/چرخش راز · delete/move/rename/rewrite/تعمیر خودکار ·
                      نوشتن مستقیم LLM در حافظهٔ canonical · فعال‌سازی /sh یا WIDE flags یا autonomy)"
r01_required_outputs:
  - R01-REALITY-MANIFEST.md    # هر مسیر ادعایی: PRESENT / ABSENT / UNVERIFIED
  - R01-TEST-MATRIX.md         # دستور، محیط، exit code، مدت، وضعیت شبکه، نتیجه
  - R01-API-BOUNDARY.md        # هر entrypoint: auth، side effect، timeout، retry، budget، receipt
  - R01-MEMORY-LEARNING-AUDIT.md  # raw→episode→retrieval→validation→canonical؛ یادگیری واقعی یا ذخیره؟
  - R01-BUG-REGISTER.md        # شدت، بازتولید، شاهد، حداقل فیکس امن، rollback، تست
  - R01-GOVERNANCE-GAPS.md     # مسیرهای activation/scheduler/راز/شبکه + نقض fail-closed
  - R01-OWNER-DECISION.md      # بدون کد؛ فقط کارت‌های بعدی رتبه‌بندی‌شده
notes: "شرط‌های توقف (توقف فوری + حفظ شاهد + بلاکر + درخواست تصمیم مالک):
        mismatch در manifest · ریسک افشای راز · ترافیک شبکه یا تغییر state پایدار ·
        وابستگی/فقدان API خارجی · ابهام در مالکیت canonical."
```

---

**امضای مالک:** ثبت‌شده از verdict چت (2026-08-18 ~22:15 +10:00) — متن کامل عیناً بالای همین سند و در بایگانی چت سشن. تاریخ ثبت: 2026-08-18 ~22:2x +10:00.

*این سند توسط ایجنت پیش‌نویس و پس از verdict مالک تکمیل شد. هیچ verdict یا مجوزی از سوی ایجنت ساخته نشده است. اصلاح یا ابطال فقط با supersede، نه حذف. وضعیت جدید: F1 = ACCEPTED_WITH_CONDITIONS · R01 = AUTHORIZED (با دامنه و ممنوعیت‌های بالا).*
