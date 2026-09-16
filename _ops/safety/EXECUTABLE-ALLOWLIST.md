# EXECUTABLE-ALLOWLIST — استثنای مجاز executable=true (دستور مالک #۱۱ §۱)

> تصحیح قاعده، نه تخفیف ایمنی. تنها مسیرهای مجاز برای `executable=true`:
> رفلکس‌های محافظ ADR-035 با جهتِ **محدودکننده فقط** (halt/throttle).
> `forbidden_direction: expansive` — هیچ گسترش/خرج/ارسال/نوشتن بیرونی.
> شمارش گزارش‌ها از این پس: `executable_true_allowlisted` + `executable_true_unexpected` (باید ۰).

| # | فایل:خط | شرط فعال‌شدن | اثر (محدودکننده) | اجازه |
|---|---|---|---|---|
| AL-1 | `_ops/wiring.py:1981-1987` | `assessment.pain > threshold` (ADR-035 APPLY) | `action=protective_halt` → توقف کار غیرضروری organism | restrictive_only |
| AL-2 | `_ops/wiring.py:1988-1994` | `critical` reflex فعال | `action=throttle` → کندسازی/محدودسازی | restrictive_only |
| AL-3 | `_ops/organism.py:696-703` | دریافت protective_halt از لایه رفلکس | `_protective_skip=True` + prot_state (توقف کار تیک) | restrictive_only |
| AL-4 | `_ops/organism.py:704-711` | دریافت throttle از لایه رفلکس | `next_epoch_at=now+600` (تعویق) | restrictive_only |
| AL-5 | `_ops/brain_worker.py:204-212,212-220` | همان دو رفلکس در مسیر brain worker | protective_executable=True روی همان دو اثر محدودکننده | restrictive_only |

## قواعد تست (اجباری)

1. هر مسیر `executable=True` در `_ops` که در این جدول نیست ⇒ تست FAIL.
2. هیچ مدخل allowlist نباید اثر گسترش‌دهنده داشته باشد ⇒ تست ساختاری:
   اثر مجاز فقط از مجموعهٔ {halting, skipping, throttling, deferring} است.

## سابقه

- 2026-08-20: تدوین پس از DISC-04 (ممیزی استاتیک) و حکم ۱ دستور #۱۱.
