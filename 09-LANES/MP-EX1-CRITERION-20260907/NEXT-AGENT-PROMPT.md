---
type: prompt
status: parked_no_code
tags: [octopus, handoff]
updated: 2026-09-07
---

# ادامه — EX1 ثبت شد؛ کد نزن مگر go تازه

مالک در همین جلسه گفت candidate EX2 دست نخورد. جهت مولد را خودسرانه پیاده نکن.

## بخوان

`OWNER-ANSWER.md` · `THREE-RESULTS.json` · `CONTRADICTION-TABLE.md` · `EX3-PRECONDITIONS.md`

قفل‌ها: `EX1_V3_0=NOT_PASSED` · دو seq و رسیدها را نگه دار · verifier/آستانه را عوض نکن · EX3 را با نام تازه یا حذف رکورد شروع نکن.

## کار موازی مجاز (فقط با go جدا برای کد)

اگر مالک صریحاً گفت جهت مولد EX2 را مطابق v3 پیاده کن: کار در `F:/wt-debug-mp-ex1-ex2-20260907`، YAML→Python، حفظ parity/قفل. baseline `F:/wt-mp-exec-ex1-ex2-20260907` را تغییر نده. این کار EX1 را PASS نمی‌کند.

## ممنوع

EX3–EX7 · backfill تاریخ · adopt خودسرانهٔ v3.1 · `owner_ruling` ساختگی · restart/deploy · self-buy
