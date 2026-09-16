# OCTOPUS — تقویم عملیاتی ۳۰ روزه (GLM-5.3)
## برگهٔ روزانه برای ایجنت اجرایی
## تاریخ شروع: 2026-08-21 · منبع: Kimi K3 + اصلاحات Claude Sonnet 5.0

---

## هفتهٔ ۱ — بازیابی حقیقت (Wave 0)

| روز | کار | گیت |
|---|---|---|
| ۱ | REALITY_SNAPSHOT: PID/port/beat/flags/lease/state همه برداشت | writes=0 |
| ۲ | TEST_REGISTRY: همهٔ تست‌ها discovery، وضعیت run_all | writes=0 |
| ۳ | RECEIPT_ATTRIBUTION_AUDIT: نسبت task_id، فهرست بی‌انتساب | writes=0 |
| ۴ | CAPABILITY_INVENTORY: قابلیت‌ها + duplicate map | writes=0 |
| ۵ | MEMORY_READ_GATE: memory_reads_per_cycle در ۱۰ سیکل | گیت اصلی |
| ۶ | تجزیهٔ duplicate + تعیین canonical | propose-only |
| ۷ | صدور WAVE0 verdict | یکی از ۴ حکم |

**توقف:** اگر WAVE0_PASS صادر نشد → توقف. گزارش CONTRADICTED با شاهد.

---

## هفتهٔ ۲ — حافظهٔ خواندنی (فاز ۱)

| روز | کار | متریک |
|---|---|---|
| ۸-۹ | memory_read_patch به organism (اگر نیست) | reads>0 |
| ۱۰ | as-of query روی دادهٔ واقعی | future_use=0 |
| ۱۱ | read-back test (N→N+1) | readback=PASS |
| ۱۲ | memory_utility baseline | utility ≥ 0.1 |
| ۱۳ | ۲۰ beat پایداری ratio | margin > 0 |
| ۱۴ | گیت فاز ۱ | PASS/FAIL |

---

## هفتهٔ ۳ — حس‌گیری (فاز ۲)

| روز | کار | متریک |
|---|---|---|
| ۱۵-۱۶ | knowledge canary (تک‌event) | دقیقاً ۱ event |
| ۱۷ | mapper baseline epoch | hash reproducible |
| ۱۸ | ۲۰ beat پایداری ratio با knowledge | margin > epsilon |
| ۱۹ | اندام بعدی (mapper→accounting) | یک اندام/session |
| ۲۰ | catch-up batch ≤25 | halt در اولین anomaly |
| ۲۱ | گیت فاز ۲ | ≥۲ منبع مستقل |

---

## هفتهٔ ۴ — bounded self-modification (فاز ۳)

| روز | کار | متریک |
|---|---|---|
| ۲۲-۲۳ | clade_ledger فعال + اولین self-patch | falsifier دارد |
| ۲۴ | P0 vs P1 causal test | HC/WM غیرتزئینی |
| ۲۵ | sealed_holdout ساخته (hash خارج از builder) | builder نمی‌بیند |
| ۲۶ | fitness_ledger فعال | attribution ≥95% |
| ۲۷ | اولین tournament | داور متفاوت |
| ۲۸ | تحلیل نتیجه + clade CMP | چهار حکم |
| ۲۹ | گزارش جامع + پیشنهاد فاز بعد | مالک تصمیم |
| ۳۰ | جمع‌بندی ماه | سند تکامل |

---

## چک‌لیست روزانه (هر صبح)

```text
□ beat advancing?
□ memory_reads_per_cycle > 0?
□ memory_utility >= 0.1?
□ attribution today >= 95%?
□ executable_unexpected == 0?
□ future_use == 0?
□ hash chain intact?
□ lease discipline maintained?
□ no new availability incident?
□ paid calls == 0 (unless signed card)?
```

اگر هر یک ❌ → آن روز degrade_to_conserve یا halt. ساخت ممنوع.

---

## یادآوری Safety

```text
L2_ARMED = propose-only
scheduler/cron حتی read ممنوع
restart فقط با supervisor احراز + baseline
هیچ hot path بدون handoff
هیچ delete؛ فقط انتقال
هیچ secret در چت/لاگ/evidence
رأی چت ≠ امضا
```
