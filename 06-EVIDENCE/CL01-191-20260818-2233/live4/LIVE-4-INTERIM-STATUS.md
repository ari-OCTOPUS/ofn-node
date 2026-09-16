# LIVE-4 INTERIM — 2026-08-19 ~11:1x +10:00 (نشست جاری)
## شکسته‌شده‌ها
• ریشهٔ پنج شکست اجرا: پروسه‌های background این ابزار مسیرِ paid را بی‌صدا local می‌کنند (foreground همیشه سبز —
  اثبات با بازتولید دقیق) → runner تکه‌ایِ foreground ساخته شد (live4_fg_runner.py، هر batch، ذخیرهٔ incremental)
• ID تکراری دفتر (از اجراهای مرده) → پسوند یکتا r6
• اولین جفت‌های واقعیِ امتیازخوردهٔ تاریخ پروژه روی deepseek پرداختی: 3 جفت معتبر (1 برد evidence، 2 باخت) · spent $0.0023
## نقص‌های باز (صف نشست بعدی، زیر CORE-AUTO-DEBUG)
D-A: بازوی baseline 7/15 شکست (cond همزمان موفق — الگوی rate-limit/policy مسیر base؛ علت دقیق از paid-calls)
D-B: داور 5/15 ناخوانا (پرامپت قاطع‌تر: «فقط یک حرف»، انگلیسی، fallback عدد)
## وضعیت اجرا
رزرو فعال با override مالک (LEARNING-FIRST) · سقف‌ها 30/24/1.00 · مقیاس 4×15 (1-2 primary منجمد)
· FX معتبر تا 16:00 · دیمون 18020 زنده · /sh disarm شد · D3 untrack شد · daily_loop آماده
## قدم بعدی (نشست بعدی، ~15 دقیق)
رفع D-A/D-B → 4 اجرای foreground → گزارش نهایی + cost-per-pair + verdict طبق آستانهٔ منجمد
