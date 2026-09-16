---
type: megaprompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, tests, green-lie, wl-collapse, structural-check, run_all]
created: 2026-08-02
updated: 2026-08-02
inspiration: OMEGA-PARITY 1-WL collapse — distinct inputs collapse to the same observable signal (exit 0)
evidence_source: [[DEEP-SCAN-REPORT-2026-08-02]] § creative mapping
---

# مگاپرامپت — رده‌بندِ green-lie (تست‌های دروغ‌سبز)

> الهامِ ریاضی: در 1-WL، دو گرافِ متفاوت به یک رنگ همگرا می‌شوند و الگوریتم
> نمی‌تواند جدا کند. در run_all.py، یک تستِ واقعیِ سبز و یک اسکریپتِ no-op
> (بدونِ `__main__`، صفر assert) **هر دو** `exit 0` می‌دهند. repo خودش این را
> مستند کرده (`run_all.py:726-745`) و با دو مکانیسم مبارزه کرده: چکِ ساختاریِ
> «has __main__» (که ۵۰ false-positive داد) و اجرای تجربی (که کار کرد ولی
> کند است). این مگاپرامپت یک رده‌بندِ **دولایه** می‌سازد که هر فایلِ تست را
> قبل از اجرا طبقه‌بندی می‌کند: واقعی/pytest-style/no-op، و مواردِ مشکوک را
> پرچم می‌زند.

---

## ۰ · قواعدِ §₀ (تکرار نشود)

از `_ops/tests` شروع کن. `Grep`/`Glob`. ≤۶۰s. ≤۴ ایجنت.
هرگز فلگ/پروسه/commit بدونِ `OWNER_AUTH`.

---

## ۱ · نقش

تو یک ایجنتِ سازنده‌ای. خروجی: یک رده‌بند که هر فایلِ تست را بررسی می‌کند و
طبقه‌بندی می‌کند: `real_unittest` / `real_pytest` / `no_op_or_bare` / `ambiguous`.
هدف: قبل از اجرا، بفهمیم کدام فایل می‌تواند green-lie باشد، بدونِ اجرای کامل.

**اعترافِ صادقانه:** repo خودش تا حدِ زیادی این را حل کرده (`PYTEST_TESTS`،
کامنت‌های مفصل، اجرای تجربی). این مگاپرامپت ارزشِ **محدودی** دارد — بیشتر
یک ابزارِ ممیزیِ دوره‌ای است تا یک نیازِ فوری. آن را با همین انتظار بساز.

---

## ۲ · واقعیتِ روی دیسک (قبل از شروع، این را بخوان)

- `tests/run_all.py:13` — لیستِ `TESTS`.
- `tests/run_all.py:281,728,734,737` — `PYTEST_TESTS` (set از فایل‌های pytest-style).
- `tests/run_all.py:726-745` — کامنتِ مفصل درباره‌ی green-lie: «structural check
  (existence of __main__) did NOT catch this and gave 50 false positives. The
  only thing that caught it was empirical execution.»
- `tests/harness.py` — الگوی استاندارد: `import harness; ENV = harness.setup(...)`.

---

## ۳ · فازها

### فاز ۱ — رده‌بندِ استاتیکی (pure)
یک تابع: `classify_test_file(path) -> {kind, confidence, signals}`. سیگنال‌ها:
- دارد `if __name__ == "__main__"`؟
- دارای توابعِ `t_*` یا `test_*`؟
- دارای `pytest.fixture`؟
- دارای `import harness`؟
- خروجیِ اجرا صفر-assert است؟ (این نیاز به اجرا دارد — فازِ ۲).
خروجی: `real_unittest` / `real_pytest` / `no_op_or_bare` / `ambiguous`.

### فاز ۲ — اعتبارسنجیِ تجربی (اختیاری، کند)
اجرای هر فایل با `timeout` و شمارشِ خطوطِ خروجی. اگر `exit 0` + صفر خروجی →
`no_op_or_bare` تأیید می‌شود. فقط روی فایل‌های `ambiguous`.

### فاز ۳ — اثرِ observable
- یک گزارش: `_ops/tests/test-classification-report.json` — هر فایل، kind،
  confidence. این observable است (CLI/گزارش).
- پرچم‌گذاریِ فایل‌های مشکوک به green-lie برای بازبینی.

### فاز ۴ — تست
- واحد: classify روی فایل‌های نمونه‌ی شناخته‌شده.
- mutation: یک فایلِ no-op را به‌عنوان `no_op_or_bare` شناسایی کن.

---

## ۴ · مرزهای سخت
- **read-only** روی فایل‌های تست: هرگز فایلِ تستی را تغییر نده.
- پشتِ فلگ (`OCTOPUS_WIRE_TEST_AUDIT`)، پیش‌فرض خاموش.
- هرگز green lie نساز: اگر classify مطمئن نیست، `ambiguous` بزن، نه `real`.
- additive: `run_all.py` بازنویسی نشود — فقط یک گزارش جانبی.
- halt مقدم بر فلگ.

---

## ۵ · خروجیِ مورد انتظار
«فازِ N تمام/نیمه/باز» + اثباتِ observable (گزارش + تعدادِ فایل‌های مشکوک).
صادقانه بنویس: «repo خودش تا حدِ زیادی این را حل کرده؛ این ابزارِ ممیزی است.»
