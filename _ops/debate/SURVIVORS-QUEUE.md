# صف تأیید انسان — بازمانده‌های مناظره (append-only)

> «بازمانده» فقط یعنی وارد این صف شد؛ تأیید = verdict آری.

## 2026-07-17T12:15:28 — seed-3 · status: pending-human

- **topic** (SEED_TOPICS): کوچک‌ترین آزمایش برای سنجش ارزش واقعی governor سایه پیش از verdict زنده‌سازی چیست؟
- **idea:** پروکسی ارزش per-organ از APPROVALهای sent ساخته شود
- **why_genius:** fitness را از حدس به دادهٔ انسانی-تأییدشده می‌برد
- **why_insane:** حجم دادهٔ اولیه کم است؛ نویز نرخ پذیرش
- **kill_condition:** اگر ۱۴ روز بگذرد و هیچ APPROVAL ثبت نشود
- **cheapest_test:** شمارش رویدادهای sent هفتهٔ جاری از logs/outbox.jsonl

