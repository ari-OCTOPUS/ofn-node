---
type: proposal
status: draft
tags: [octopus, live-d, full-loop, pre-registration, flash]
created: 2026-08-20
updated: 2026-08-20
created_by: agent B (ZCode) — directive #۸ §۶ (T51)
---

# کارت پیش‌ثبت LIVE-D — اولین حلقهٔ کامل با مدل واقعی — UNSIGNED · اجرا = ۰

decision_id: PRE-REG-FULL-LOOP-FLASH-2026-08-20
status: SIGNED_ED25519 (2026-08-20 · payload E9DC768B...DFC9 · .sig verified vs anchor)
execution_condition: LIVE-A + LIVE-B + LIVE-C همگی PASS **و** امضای Ed25519 جداگانهٔ
مخصوص همین کارت (لنگر: `_ops/owner-signing/TRUST-ANCHOR.md`؛ رأی چت هرگز
جانشین امضا نیست — R10).

```yaml
card: PRE-REG-FULL-LOOP-FLASH-2026-08-20
tasks: 12                    # یک task واقعی هر ۵ دقیقه
interval_minutes: 5
max_calls: 12                # حداکثر یک فراخوان به‌ازای task
concurrency: 1
hard_stop_aud: 0.50          # سقف سخت جلسه — از سطل علم موجود؛ هیچ سقفی بالا نمی‌رود
timeout_seconds: 60
max_retries: 1
judge: advisory_only         # D6 = CLOSED_NEGATIVE: قضاوت داور تابع جفت است
output: proposal_only        # هر خروجی فقط پیشنهاد؛ executable هرگز true نمی‌شود
judgment_acceptance:         # حکم ۳ دستور مالک #۱۱ — داور advisory هم فقط قضاوتِ پایدار
  method: هر مقایسه در دو ترتیب اجرا شود
  accept_if: هر دو ترتیب یک برنده بدهند
  otherwise: VOID_UNSTABLE
  flip_rate_on: only_pairs_with_advantage
executable: false
memory: هر task از memory_read_loop با decision_time می‌خواند (LIVE-C)
receipts: هر فراخوان رسید کامل با task_id/run_id (T50) + گیت FX تازه ≤24h
rollback: قطع با HARD_STOP خودکار؛ گزارش انحراف طبق الگوی T35
```

## سؤال ازپیش‌ثبت‌شده

آیا حلقهٔ کامل «خواندن حافظه (as-of) → context با provenance → DeepSeek واقعی →
پیشنهاد → ثبت receipt» روی ۱۲ task واقعی بدون خطای حاکمیتی اجرا می‌شود، با
صفر executable و صفر نشت آینده در context؟

## حکم‌های ازپیش‌ثبت‌شده

| مشاهده | حکم |
|---|---|
| ۱۲/۱۲ task با receipt کامل، صفر executable، صفر future-evidence در context | LIVE-D کاندید PASS |
| هر گیت حاکمیتی شکست (HARD_STOP/FX/بودجه) | STOP + گزارش انحراف |
| context حاوی رکورد future | حکم FAIL + ریشه‌یابی قبل از هر تلاش بعدی |
| کمتر از ۱۲ task کامل (timeout/retry exhausted) | INCOMPLETE — بدون top-up |

حداقل یک حالت شکست باید بتواند کارت را بکُشد (محدودیت hard_stop واقعی).

## وضعیت اجزاء (2026-08-20 ~15:00 +10)

- LIVE-A: **PASS** (T47)
- LIVE-B: در حال سنجش (T48؛ producerها مستقر، جمع‌آوری ۶۵+ دقیقه در جریان —
  گزارش: `06-EVIDENCE/T48-EVENT-TIME-MEASUREMENT-2026-08-20.md` پس از ساعت ۱۵:۴۹)
- LIVE-C: شواهد زندهٔ اولیه سبز (memory_reads_per_cycle=3، readback=read_ok،
  executable=false) — بستهٔ کامل در `06-EVIDENCE/DIRECTIVE-8-REPORT-AGENT-B-2026-08-20.md`

**تا امضا: اجرا = ۰. هیچ فراخوان پولی از این کارت انجام نشده است.**
