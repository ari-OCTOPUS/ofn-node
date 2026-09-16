---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 04 · OBSERVABILITY — گپ‌های KPI و آنچه ‏/kpi_import می‌بندد

## مسئله (قبل از sprint)

معیارهای kill/گیت (G1: ‏≥200 کلیک + ≥10% click→follow؛ G2: ‏free→paid) **قابل‌سنجش نبودند**: هیچ store ای برای کلیک/تبدیل وجود نداشت، KPIRollup فقط revenue/ppv/posts داشت، و هیچ نگاشتی بین «پستی که A دستی گذاشت» و «کلیک‌هایی که برگشت» نبود.

## آنچه ساخته شد (همه دستی/آفلاین — هیچ pull زندهٔ پلتفرم، پیش از G0 مجاز)

1. **LinkState** (‏`store.py`، فایل `langar/link_state.json`): هر ‏`/pf_ready` یک کد `L-xxxxxx` ‏idempotent می‌گیرد؛ A آن را در لینک/UTM دستی می‌گذارد.
2. **KPIWeek + funnel**: فیلدهای جدید `clicks / follows / free_subs / paid_conversions` روی bucket هفتگی.
3. **‏/kpi_import** (لنگر): دو حالت — (الف) سطر CSV هفتگی `revenue,ppv,posts,rate,new_fans,clicks,follows,free_subs,paid` که A از داشبورد پلتفرم paste می‌کند؛ (ب) ‏`L-xxxxxx <clicks>` برای برگرداندنِ کلیکِ یک کد (به bucket هفته هم اضافه می‌شود).
4. **approvals.jsonl**: ‏audit append-only هر ‏pf_approve/pf_ready/dm_approve — مسیر HITL بالاخره قابل‌ممیزی است (content-free).

## حلقهٔ سنجش G1 (پس از GO — امروز NO-GO)

`/pf_ready` → کد L → پست دستی با لینکِ کدخورده → جمعه: A کلیک‌ها را از داشبورد می‌خواند → `/kpi_import L-... N` + سطر CSV → `/kpi` روند ۴هفته‌ای + funnel → ارزیابی G1 با **عدد**، نه حس.

## گپ‌های باقی‌مانده (backlog)

- داشبورد بصری (kpi-dashboard-spec) هنوز ساخته نشده — ‏/kpi متنی است.
- ‏delivery-rate ‏C هنوز ورودی دستی است؛ اتصال به drafts.json خودکار نشده.
- هیچ alerting روی kill-criteria نیست (اگر G1 fail شد، انسان باید خودش ببیند) — پیشنهاد: چک هفتگی در تیک جمعه.
