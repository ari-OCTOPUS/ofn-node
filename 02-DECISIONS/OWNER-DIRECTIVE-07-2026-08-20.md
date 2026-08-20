---
type: decision
decision_id: OWNER-DIRECTIVE-07
status: ACTIVE — مکمل دستور #۶؛ در تعارض، #۷ برای LIVE-A..C حاکم است
created: 2026-08-20
created_by: OWNER — ثبت توسط ایجنت B (ZCode) از متن پیست‌شدهٔ مالک
prerequisite: گزارش §۹ دستور #۶ (commit 842a19d) پذیرفته شد
audience: ایجنت A و ایجنت B
base_state: WAVE0_OBSERVE_ONLY / L2_ARMED / GAP-001=OPEN / executable=false
---

# OCTOPUS — دستور مالک #۷
## بازکردن LIVE-A، LIVE-B و LIVE-C

## ۰) آرای مالک (نافذ از همین لحظه)

```text
R1_key_identity: ACCEPTED  # KEY_IDENTITY_CONFIRMED_SAME
R2_b1_status:    B1_SIGNED_ED25519
R3_k9_audit:     ACCEPTED_WITH_ATTRIBUTION_GAP
R4_d6:           CLOSED_NEGATIVE  # با اصلاح عدد دقیق p
R5_lease:        APPROVED_FOR_ACTIVATION  # مشروط
R6_event_time:   APPROVED_TWO_PRODUCERS   # فقط دو کاندید مصوب
R7_memory_read:  APPROVED_READONLY_WIRING
R8_ablation:     REMAINS_BLOCKED  # تا فعال‌شدن lease
R9_budget_cap:   NO_INCREASE      # R7 قدیمی پابرجاست
R10_chat_vote:   NOT_A_SIGNATURE  # بدون استثنا
```

## ۱) T40 — اصلاح عدد p در D6

مخرج درست C(18,9) = 48620 است:

```text
p_exact = 2 / 48620 = 4.113533525298231e-05
مقدار ثبت‌شده = 4.115226337448563e-05 = 2 / 48600  ← غلط
```

رسید T36 با ERRATA اصلاح شود؛ مقدار قبلی حذف نشود. علت خطا نوشته شود:
مخرج ۴۸۶۰۰ به‌جای ۴۸۶۲۰. حکم CLOSED_NEGATIVE تغییر نمی‌کند.

## ۲) T41 — تثبیت لنگر اعتماد کلید (اولویت بالا)

ریسک ساختاری: امضا با PEM عمومی داخل مخزن verify می‌شود؛ اگر آن فایل عوض شود
verify همچنان سبز می‌ماند ولی معنایش عوض می‌شود.

- فایل لنگر: `_ops/owner-signing/TRUST-ANCHOR.md` با انگشت‌نگارتی DER:
  `2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2`
- تمام اسکریپت‌های امضا/verify پیش از verify انگشت‌نگارتی PEM را با این مقدار
  تطبیق دهند و در اختلاف fail-closed شوند.
- تست `test_trust_anchor_fingerprint` اضافه شود (تغییر PEM مخزن را تشخیص دهد).
- مالک همین انگشت‌نگارتی را جدا از مخزن نگه می‌دارد.

## ۳) T42 — اعتبارسنجی بکاپ کلید (ریسک بازیابی)

تقسیم کار: **ایجنت فقط runbook می‌نویسد؛ به enc دست نمی‌زند و passphrase نمی‌خواهد.**
مالک خودش: رمزگشایی در مسیر موقت خارج از مخزن → استخراج کلید عمومی → مقایسهٔ
انگشت‌نگارتی DER با مقدار لنگر → پاک‌کردن فایل موقت → گزارش فقط یک کلمه.

```text
MATCH    → backup_recovery: VERIFIED
MISMATCH → backup_recovery: INVALID  → ساخت بکاپ تازه ضروری است
UNTESTED → backup_recovery: UNKNOWN  → ریسک از دست رفتن امضا باقی است
```

هیچ‌گاه passphrase یا محتوای کلید در چت، log، رسید یا commit ظاهر نشود.

## ۴) T43 — فعال‌سازی lease نویسنده

شروط R5:
- کد `_ops/writer_lease.py` توسط **هر دو** ایجنت پذیرفته شود؛ قفل یک‌طرفه توهم است.
- پیش‌فرض fail-closed: lease نگرفته/نامعلوم ⇒ read-only.
- دامنه: ledger، evidence، budgets، state، git write.
- TTL کوتاه با renew صریح؛ lease منقضی بایگانی شود نه پاک.
- هر رسید agent_id و session_id داشته باشد.
- تست‌ها: acquire/renew/expire/steal-prevention/concurrent-write-rejection.
- پس از فعال‌شدن: تست ادغام دو نویسندهٔ هم‌زمان → یکی HOLD.
- با فعال شدن lease و بستن T40 و T41 ⇒ **LIVE-A = PASS**.

## ۵) T44 — دو producer واقعی event-time

فقط این دو مورد مصوب:

```text
producer_1: domain=provider · occurred_at_source=server response timestamp
producer_2: domain=telegram · occurred_at_source=message.date (دقت ثانیه)
```

قواعد: ساعت نوشتن هرگز occurred_at نمی‌شود؛ در نبود منبع واقعی
`INELIGIBLE_TEMPORAL_METADATA`. دقت پایین در رکورد ثبت شود
(`time_precision: 1s`). انحراف ساعت بیرونی ثبت شود؛ `occurred_at > recorded_at`
یعنی `CLOCK_SKEW_SUSPECTED` نه اصلاح خودکار. دامنه‌های داخلی
(system, doctor, neural, lead, ziman) دست نخورند.

گیت LIVE-B:

```text
independent_sources >= 2 · delta stdev > 10ms در هر دو
حداقل یک late-arriving واقعی · suite ۱۵تایی روی داده واقعی = PASS
تمام مسیرهای خواندن از decision_time = PROVEN
```

تا آن زمان live spine = NOT_VERIFIED_BITEMPORAL.

## ۶) T45 — بازسازی مسیر خواندن حافظه

`memory_read_patch.py` (نسخهٔ حلقهٔ زنده) روی دیسک نیست — artifact گم‌شده.

- جست‌وجوی کامل در git history، بکاپ‌ها و vault؛ اگر نبود ⇒ `UNLOCATED` + بازنویسی از صفر.
- wiring فقط-خواندنی پیشنهاد شود: `query_experiments` · `get_pending_hypotheses` · `search_vault`
- شمارندهٔ `memory_reads_per_cycle` پیاده و منتشر شود.
- هر خواندن از query دارای `decision_time` عبور کند.
- تست read-back: نوشتن در چرخهٔ N، خواندن موفق در چرخهٔ N+1.
- گیت LIVE-C: ‏`memory_reads_per_cycle > 0` زنده · read-back PASS · هیچ مسیر خواندنی
  بدون decision_time · executable=false.
- اجرای واقعی wiring روی organism.py = دستور جدا؛ این مرحله فقط patch پیشنهادی + تست + رسید.

## ۷) T46 — تفکیک رسید هزینه

AU$0.011723 کران بالا است نه هزینهٔ دقیق K=9. فیلد `task_id` و `run_id` به
رسیدهای router اضافه شود؛ رسید بدون task_id در آینده `UNATTRIBUTED` علامت بخورد؛
گزارش T35 با برچسب UPPER_BOUND اصلاح شود.

## ۸) ممنوعیت‌های ثابت

ablation چهاربازویی BLOCKED تا LIVE-A=PASS · هیچ فراخوان پولی جدید تا امضای
Ed25519 مخصوص همان آزمایش · رأی چت هیچ‌گاه جانشین امضا نیست · سقف بودجه بالا
نرود · هیچ deploy روی Orange Pi · amend/rebase ممنوع · هیچ اصلاح خودکار روی
life_currency.py، warm-up، rounding یا C-042.

## ۹) گزارش لازم

```text
T40 P-VALUE ERRATA   : DONE | BLOCKED → رسید:
T41 TRUST ANCHOR     : DONE | BLOCKED → fingerprint pinned? test added?
T42 BACKUP RUNBOOK   : DONE (owner action pending) → verdict: MATCH|MISMATCH|UNTESTED
T43 WRITER LEASE     : ACTIVE | AWAITING_AGENT_A | BLOCKED
T44 EVENT-TIME       : sources_live= · stdev= · late_real_case=
T45 MEMORY READ      : PROPOSED | WIRED_READONLY | STILL_WRITE_ONLY
T46 RECEIPT SPLIT    : DONE | BLOCKED

LIVE-A/B/C : PASS | BLOCKED    LIVE-D/E : باید BLOCKED
paid calls / AUD : 0/0 · executable=true: 0 · lease held: · GAP-001: OPEN
```
