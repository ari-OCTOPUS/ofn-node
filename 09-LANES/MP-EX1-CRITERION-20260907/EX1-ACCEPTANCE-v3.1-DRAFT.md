---
type: draft
status: not_adopted
kind: advisor_proposal
supersedes_nothing: v3.0 result remains NOT_PASSED
updated: 2026-09-07
---

# پیش‌نویس معیار EX1 v3.1 — adopt نشده

این پیش‌نویس قرارداد v3.0 را عوض نمی‌کند. نتیجهٔ قبلی تحت v3.0: **NOT_PASSED**.  
Adopt فقط با جواب صریح مالک + (طبق v3) حکم امضاشده، نه با این فایل.

پیشنهاد لایه‌بندی مطابق دستور مالک:

```text
EX1-L1 existence_and_content
  scope: keys actually present on the raw receipt lines
  194298/194329: retained in baseline forever as historical events
  verdict now: MEASURED_WITHIN_RECEIPT_KEYS_ONLY

EX1-L2 mode_observation
  scope: halt branch and mint branch each fired once
  not in scope: rate, stability, decision quality, scientific calibration
  verdict now: TWO_MODES_OBSERVED

EX1-L3 original_contract (frozen v3.0)
  expect text unchanged
  verifier unchanged
  verdict now and later under v3.0: NOT_PASSED
```

اگر v3.1 روزی adopt شود، فقط برای **تصمیم‌های پس از تاریخ قطع** می‌توان trio / `reason_code` / `mint_evidence` / verifier نام‌دار را اجباری کرد. ردیف‌های ۱۹۴۲۹۸/۱۹۴۳۲۹ backfill نمی‌شوند.

تا adopt: هر گزارش باید `EX1_V3_0=NOT_PASSED` بنویسد.
