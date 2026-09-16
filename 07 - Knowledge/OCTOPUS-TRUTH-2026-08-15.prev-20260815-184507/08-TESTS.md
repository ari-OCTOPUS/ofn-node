---
title: وضعیت تست‌ها
type: note
tags: [octopus, observatory, tests, mutation-testing]
up: "[[00-INDEX]]"
evidence_level: A
---

# تست‌ها

## اجرای واقعی روی ماشین مالک

```
> python -m pytest _ops\observatory\tests\ -q
93 passed in 1.57s
```

> [!check] سطح شاهد A — این خروجی از ترمینال خودِ مالک آمده، نه از sandbox.

| مجموعه | تعداد | چه چیزی را می‌گیرد |
|---|---|---|
| `test_gateway.py` | ۳۰ | ۱۱ تست منفی اجباری، ۱۰ دروازه، معناشناسی RFC 9309 |
| `test_structural.py` | ۷ | invariant S1 — فقط `gateway.py` شبکه import می‌کند |
| `test_evidence_store.py` | ۲۵ | تعیّن replay، dedup، تشخیص دست‌کاری، بودجهٔ پایدار، rate limit |
| `red_team/test_red_team.py` | ۳۱ | ۲۰ الگوی تزریق پرامپت، boundary، poisoning، فرار از بودجه، kill switch |
| **مجموع** | **۹۳** | |

## تست جهش‌یافتگی روی gateway

هفت جهش عمدی کاشته شد، **هر هفت کشته شد**:

1. حذف گیت متد
2. حذف گیت scheme
3. تبدیل تطبیق دقیق دامنه به تطبیق پسوندی
4. برداشتن سقف حجم
5. خاموش کردن kill-switch
6. برداشتن سقف بودجه
7. رفتار با 5xx مثل 4xx

## تست جهش‌یافتگی روی راستی‌آزما

شش جهش در دیتابیس کاشته شد، **۶ از ۶ کشته شد**:

| جهش | یافتهٔ راستی‌آزما |
|---|---|
| flip یک بایت در `body_bytes` | `[CRIT] body_hash matches bytes` |
| شکستن پیوند `prev_hash` | `[CRIT] prev_hash links` |
| جعل `hash` | `[CRIT] hash formula reproducible — none of 15 candidates matched` |
| تزریق هدر `Set-Cookie` | `[FAIL] no identity headers stored` |
| عبور از سقف بودجه | `[FAIL] domain budget respected` |
| شکاف در `seq` | `[FAIL] seq monotonic no gaps` |

> [!note] چرا جهش‌کاری مهم است
> تست سبز اثبات نمی‌کند تست چیزی را می‌گیرد. جهش‌کاری اثبات می‌کند.
> هر تستی که هیچ جهشی را نکشد، تزئین است.

## تلهٔ اجرا

اولین بار نصب‌کننده از `C:\Users\Armin` اجرا شد و ۱۰ فایل در جای غلط نشستند.
تست‌ها سبز شدند ولی روی فایل‌های بی‌ربط.

> [!warning] نصب‌کننده **همیشه** باید از ریشهٔ مخزن اجرا شود.
> ۹۳ تست سبز در مسیر غلط بی‌ارزش است.
