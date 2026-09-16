---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, discovery, governance, d1, d6, audit]
created: 2026-08-15
updated: 2026-08-15
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[OCTOPUS/CURRENT-TRUTH]]"
  - "[[00 - Inbox/2026-08-15 SESSION — Desktop Lab D1-D8 Governance]]"
---

# ۴۷ — سیزن آزمایشگاه دسکتاپ (Stage8R → D8) و حقیقتِ حاکمیتی

این نوت **ارگانیسم زندهٔ `_ops`** را عوض نمی‌کند. سیزن ۱۴–۱۵ اوت ۲۰۲۶ روی دسکتاپ ویندوز بود: بستهٔ مهرشدهٔ v4 r2، ممیزی، waiver مالک، و آزمایشگاه FakeEffect تا D8.

مسیرهای دسکتاپ مشاهده‌اند، نه SoT داخل vault. راز/کلید خصوصی اینجا نیست.

## حقیقت رسمی (قفل — جعل نشود)

```text
INDEPENDENT_THIRD_PARTY_PASS             = FALSE
EXTERNAL_AUDIT_VALID                     = FALSE
AUDITOR_ORGANIZATIONAL_INDEPENDENCE      = FALSE
OWNER_WAIVED_EXTERNAL_INDEPENDENT_AUDIT  = TRUE
TECHNICAL_RECOMPUTATION_PASS             = TRUE
D1_RELEASE_VALID                         = FALSE
OFFICIAL_D1_STATUS                       = NOT_STARTED
OFFICIAL_D6_STATUS                       = NOT_STARTED
D7_EXECUTION_AUTHORIZED                  = FALSE
PRODUCTION_ELIGIBILITY                   = SEPARATE_DECISION_REQUIRED
OWNER_KEY_CREATED                        = FALSE
OWNER_SIGNATURE_CREATED                  = FALSE
```

چت مالک ≠ امضای Ed25519. PASS همان‌محیط ≠ گواهی شخص ثالث.

## بستهٔ مهرشده (ورودی کانونی)

مالک CANDIDATE-002 را انتخاب کرد.

- مشاهده: `Desktop\octopus-s8r-run\DELIVERY_v4_r2`
- `FINAL-EVIDENCE-MANIFEST-V4.json` SHA-256: `2489467fef1d53a0d834966956bb5c6aae8e75d22c5ce2d0573dbffe3203b0a7`
- `ARCHIVE_SET_IDENTITY_SHA256`: `df9b403bac69f7530a30c8333f242afa59fed9f9e0a209f9ff879158d2d4d3df`
- `PACKAGE_ROOT_IDENTITY_SHA256`: `dd9caade174e4fbc11e982f74db611153c52b4191f4567d0fb62023538cfcd67`
- ۱۲۰ entry در core manifest · ۹ archive · soak مهرشده ≈ ۳۷۲۱٫۳۷s (≥ ۳۶۰۰)
- Stage8R PASS / Stage9 ۱۷/۱۷ (مهر) / Stage9.5 FROZEN / Stage10 FAILED_STOP
- درخت منبع مهرشدهٔ آزمایشگاه اولیه: `9fb38256c7888f98b81a7e05d4f3dbbd3cdf878064be84bb3feb7424ba4e299e`

## سیزن‌ها (به ترتیب)

### ۱) ابهام‌زدایی و preflight
دو کاندید؛ مالک ۰۰۲. preflight روی intake. D1 رسمی شروع نشد.

### ۲) ممیزی همان‌محیط (اشتباهِ برچسب)
ZIP `OCTOPUS-R1-EXTERNAL-AUDIT-RESULT.zip` (۱۲۶۲۷ بایت، SHA-256 `5ff63e2b3efaca39a6fa72431099a9de1bfb7635931ebb3727eb981a42dc3377`) داخلش `verdict: PASS` نوشت. فایل دسکتاپ با ۲۸ حرف «ن» همان بایت است — بازگشت ممیز نیست.

طبقه‌بندی درست: `SAME_ENVIRONMENT_TECHNICAL_RECOMPUTATION`.  
بازمحاسبهٔ فنی (حفظ): ۱۲۰/۱۲۰ · ۹/۹ · ۱۸/۱۸ امضا · ۱۸/۱۸ authorization · Stage9 ۱۷/۱۷ · soak ۳۷۲۱٫۳۷s · source binding · freeze ۵/۵.

کلید عمومی گزارش فنی (`fe228a95…`) فقط integrity همان گزارش است، نه trust anchor. فایل `.auditor_private_key_hex` وارد registry/بستهٔ خارجی نشد.

### ۳) R0–R4 و handoff اشاره‌ای
`Desktop\octopus-completion-r0-r4-v1` — توقف روی ممیز مستقل + امضای مالک. ZIP export اشاره‌ای بود (بدون soak ۲۴۰MB).

### ۴) مأموریت شبانه ۱۰ساعته
`Desktop\octopus-overnight-completion-20260815T010353`  
بستهٔ self-contained: `OCTOPUS-SELF-CONTAINED-EXTERNAL-AUDIT-BUNDLE-20260815.zip`  
SHA-256: `c2814e4c13d5a6df0f5f6397dc94347be4f7644d8a9855bcb096625b63a58ebe` (۲۵۰٬۴۷۳٬۴۶۲ بایت).  
Reproduction kit QA = PASS. D1 unsigned schema آماده؛ hash ممیز UNRESOLVED ماند.

### ۵) حکم مالک: بدون ممیز
عین عبارت: «بدون ممیزس بریم».  
`Desktop\octopus-owner-waived-audit-20260815T011906` — waiver ثبت شد. payload D1 با `external_audit_status=OWNER_WAIVED` و hash هنوز UNRESOLVED. امضا ساخته نشد.

### ۶) «تا آخر» — آزمایشگاه FakeEffect
`Desktop\octopus-owner-to-end-20260815T084249` (v2 این سیزن، نه v2 کشف قدیمی): D1–D5 آزمایشگاه OK؛ D6 اول `FAILED_STOP` (constraint ۱۱۷/۱۲۰، novelty قالب‌بسته). D7 بدون دادهٔ زنده `FAILED_STOP`. D8 `MIXED_REQUIRES_REVISION`.

Rubric منجمد novelty = Jaccard متن `strategy_proposal` ≥ ۰٫۸۵ نزدیک‌تکرار. آستانه پایین نیامد. holdout رسمی `97001–97003` مصرف نشد.

### ۷) آلودگی jsonl و v3 تمیز
`append_jsonl` با mode `a` در rerun همان پوشه ledgerها را دوبل کرد (مثلاً D6 = ۲۴۰ ردیف). v2 سیزن (`…T084249`) append-only ماند؛ ledger آلوده‌اش ۲۴۰ ردیف است.

**بستهٔ تمیز معتبر:** `Desktop\octopus-owner-to-end-20260815T110641`  
ledger D6 = ۱۲۰ ردیف / ۱۲۰ id یکتا / constraint `120/120` / usefulness `115/120` / novelty `1/120` / creativity `1/120`.  
تصمیم D6: `LAB_CONTINUED` · `official_status=NOT_STARTED`.  
خلاصهٔ بالای بسته ممکن است D6 را `RELEASED` بنویسد — آن برچسب pipeline است نه promotion رسمی.

`120/120` constraint از تغییر سیاست candidate آمد (`evidence_uncertainty` + stakes از `value_cents`/`harm_cents`)، بعد از دیدن شکست‌های v2. درخت منبع این اجرا: `921e953bdbf770e6136f02c8241e1fc78c790b0f58169676b70e75960878c2d7` — این کدِ مهرشدهٔ CANDIDATE-002 نیست.

`append_jsonl` در runner v3 با `"w"` بازنویسیِ همان اجراست.

## آزمایشگاه در برابر رسمی

| مرحله | آزمایشگاه (v3) | رسمی |
|---|---|---|
| D1–D5 | LAB_OK (تست سبز، mutation ۱۷/۱۷، invariants صفر) | NOT_STARTED |
| D6 | LAB_CONTINUED — creativity ۱/۱۲۰ | NOT_STARTED |
| D7 | FAILED_STOP — live=false | NOT_STARTED |
| D8 | FINALIZED = MIXED_REQUIRES_REVISION | غیررسمی |

v1 کشف قدیمی (`octopus-discovery-d1-d8-full-v1`) و v2 کشف (`…-full-v2`) هم append-only ماندند؛ promotion ندارند.

## کارِ بازِ مالک (OD)

1. OD-001 — ممیز سازمانی مستقل، یا پذیرش صریح که waiver کافی است (الان waiver چت است، نه PASS).
2. OD-002 — امضای Ed25519 مالک برای `D1_RELEASE_VALID`.
3. OD-003 — D7 جدا (دادهٔ زنده) و production جدا.

`TERMINAL_ACTION` آزمایشگاه = STOP. D7/production از این نوت باز نمی‌شود.

## رابطه با ارگانیسم زنده

`_ops` / مینی‌اپ / ADR-033..040 / برد Orange Pi = خط جدا. این سیزن آن‌ها را مسلح یا دیس‌آرم نکرد. SoT زنده همان [[OCTOPUS/CURRENT-TRUTH]] و registry/ADR است.
