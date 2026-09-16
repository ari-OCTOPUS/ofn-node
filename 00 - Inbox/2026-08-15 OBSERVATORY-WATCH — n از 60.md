---
type: observatory-watch
date: 2026-08-15 (19:00)
mode: read-only (هر دو دیتابیس mode=ro)
source_cmd: sqlite3 file:...predictions.db?mode=ro — SELECT event_type,payload; فیلتر «strategy:bayes-v1» در payload.event_description
---

# OBSERVATORY-WATCH — 2026-08-15 · n بیزی = ۱ از ۶۰

- **registered_total = 7 · resolved = 0 · bayes_registered = 1** (نفس اول bayes-v1 در 18:57: OCTOPUS 0.99 در برابر persistence 0.80)
- budget روزانه (epoch 739843): `earthquake.usgs.gov 5/100` · `hacker-news.firebaseio.com 0/50` — سالم
- evidence_chain = ۷ ردیف؛ زنجیره تأییدشده (27/27 در 2026-08-15 عصر)
- قضاوت آماده نیست — با کادنس ساعتی، n≥60 تقریباً ۲.۵ روز دیگر (اولین resolution از فردا، پس از ۲۴ ساعتِ پیش‌بینی اول)
- نکتهٔ فنی این رصد: ستونی به نام event_description وجود ندارد — description داخل payload است؛ پرس‌وجوی اول خطا داد و اصلاح شد (سطح A با بازتولید)
