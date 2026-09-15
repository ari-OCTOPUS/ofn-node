# MEGAPROMPT — GROK TEAM BUILD: بیزنس‌های دوم و سوم را به موتور درآمد وصل کنید

**سطح دسترسی شما:** فقط یک repo تازه می‌سازید (خروجی = کد + کانفیگ + تست + ران‌بوک). به هیچ ماشین، سرور، اکانت یا فایلِ ما دسترسی ندارید و ادعایی دربارهٔ «اجرا روی سیستم ما» ننویسید. هر چیزی که بسازید باید با تست خودتان سبز شود و ما بعداً یک‌جا integrate کنیم.
**زبان تحویل:** کد و اسم‌ها انگلیسی؛ گزارش‌ها فارسی ساده.

---

## ۰. زمینه — موتوری که قبلاً ساخته شده و باید مثلش بسازید

یک «موتور درآمد» (revenue engine) برای بیزنس نقاشی همین هفته کامل شد و کار می‌کند. معماری‌اش این است و شما باید برای دو بیزنس دیگر همان الگو را با همان انضباط بسازید (نام‌ها و اسکیماها را عیناً رعایت کنید چون ابزار ادغام ما روی این قراردادها سوار است):

```
revenue-drive/
  leads_master.json        # {"accounts":[{business_name, segment, suburb, website,
                           #   contact_channel, evidence_url, approach, relevance,
                           #   priority, stage, outreach_permission, verified,
                           #   verification_date, source}]}
  lead-emails.jsonl        # {at, business_name, email, source, strategy, suburb}
  lead-enrich-cursor.txt   # عدد — batch cursor، idempotent
  lead_enrich.py           # بازدید سایت هر لید (bounded 8/سیکل، 12s/site)، استخراج ایمیل، رسید
  money_executor.py        # ساخت پکت برای لیدهای نقل‌قول‌نگرفته (رنک، انگشت‌نگاری dedupe)
  quote-packets/QP-*.json  # {"schema":"octopus.quote-packet.v1", packet_id, at,
                           #   lead:{business_name, segment, approach, contact_channel,
                           #   evidence_url, priority}, scope, price, send_status, market}
  channel-authorization.json  # مجوز ماشین‌خوانی کانال: {"envelope":{"daily_send_cap":10}}
  CHANNEL-REVOKED          # فایل وجودش = قطع فوری
  send_queue.py            # گیت‌ها: authorization + not-revoked + kill-switch + سقف روزانه؛
                           #   idempotency از receipts؛ شکست قطعی (بدون ایمیل/≥۳ شکست) → terminal/؛
                           #   لاگ ارسال بعد از نتیجه با فیلد outcome؛ staging خودکار پکت‌های دارای ایمیل؛
                           #   sync ایمیل‌های پیدا‌شده به leads_master
  sent-log.jsonl           # {at, packet, kind:"quote"|"followup_1", outcome:"sent"|"failed",
                           #   payload_sha16, daily_cap, sent_today_before, ab_variant}
  reply_alert.py           # پول IMAP هر ۲ دقیقه؛ پیام جدید از لید/Reply → ردیف
                           #   REPLY_DETECTED + کارت مالک تلگرام؛ cursor بر UID؛ صفر نویز
  owner-decisions.jsonl    # {at, decision, verbatim, meaning, source} — رأی‌های مالک
  offer-experiments.json   # آزمایش A/B موضوع با قاعده تصمیم عددی
  receipts.jsonl           # append-only؛ هر ردیف {schema, at, kind, ...} — هرگز بازنویسی نشود
  season-meter.json        # بازنویسی مقید در هر سیکل: verified_cash, leads_total,
                           #   authorized_with_contact, staged, sent_today, replies_detected
```

قواعد طلایی همین موتور (نقض = رد تحویل):
1. **فقط VERIFIED_CASH درآمد است** — هیچ شمارش دیگری (sent/sub/follower) در فیلد درآمد نمی‌نشیند.
2. **سقف ارسال روزانه** (پیش‌فرض ۱۰) و **idempotency** — هیچ‌چیز دوبار فرستاده نشود.
3. **رسید append-only برای هر اثر خارجی** + مسیر rollback.
4. **شکست قطعی terminal می‌شود** — حلقهٔ retry بی‌پایان ممنوع.
5. **لاگ صادق**: ردیف «sent» فقط بعد از نتیجه واقعی.
6. **مجوز ماشین‌خوان**: بدون فایل authorization هیچ ارسالی؛ فایل REVOKED بالاتر از همه.
7. اثر عمومی (پست/پیام بیرونی) فقط با GO مالک؛ کارت‌های تصمیم حداکثر ۳ گزینه.

---

## ۱. بیزنس A — Nova Soles (کریتور؛ قیف: X → FeetFinder → OnlyFans)

واقعیت امروز (از سوابق ما، 2026-08-24):
- برند LOCK: **Nova Soles** · شعار: *Sexy is an energy, not a body type* · بدون چهره (no-face) · لِین: Studio/Saba
- X: **@novasolmate** کامل (بیو+سیدنی+آواتار NS-FF-05+بنر NS-FF-01+لینک سایت→OF)
- FeetFinder: **NovaSolesAU** — KYC بلاک (انسانی؛ فقط مالک) · ۹ پک واترمارک‌شده NS-FF-01..09 آمادهٔ آپلود
- OnlyFans: **@novasolesau** — پروفایل کامل/زنده، بدون پست؛ onboarding درآمد شاید ناتمام
- اینستاگرام/فیس‌بوک: مالک در حال ساخت (هندل دقیق ندارد)
- **سیاست سخت:** OnlyFans فقط مرورگرِ خود مالک؛ cookie/HTTP API مطلقاً ممنوع؛ پسورد/کوکی/شماره در هیچ فایلی نوشته نشود؛ پستِ زنده فقط با GO مالک.

### چه بسازید (`nova-drive/` در repo خودتان)

**A1. قیف مخاطب به‌جای قیف لید** — همان اسکیماها، ترجمه‌شده:
- `fans_master.json`: مخاطبان/سرنخ‌ها (فالوورهای X مرتبط، خریداران محتمل FF،…) با فیلدهای همان leads_master + `platform`
- `content_calendar.json`: تقویم محتوای ۳۰روزه برای X/IG — هر آیتم {date, platform, asset_id (NS-FF-xx), caption_draft(EN), cta, status:"draft"|"owner_approved"|"posted_manual", owner_go_required:true}
- **Caption engine**: مولد کپشن انگلیسی برند-دار (سوژه: feet/پا، بدون چهره، لحن classy نه صریح) — فقط متن؛ خروجی به‌عنوان پیش‌نویس به صف تأیید مالک. صریح/نuder ممنوع؛ برند no-face حفظ شود.
- `channel_gates.json`: وضعیت گیت‌ها (FF_KYC، OF_BECOME_CREATOR، IG_LIVE، FB_LIVE) + قاعدهٔ «هر گیت انسانی = کارت مالک با ۳ گزینه، re-fire هر ۴۸ ساعت»

**A2. هشدار و متر، هم‌الگوی موتور:**
- `reply_alert` معادل: مانیتور (در حد کدی که ما بعداً به API رسمی X وصل کنیم — شما رابط/اینترفیس + فیک-تستر بسازید) → ردیف `FAN_EVENT_DETECTED` (نوع: reply/DM/sub/Tip) + کارت مالک
- `nova-meter.json`: {verified_cash(فقط payout تأییدشده), followers_x, ff_subs, of_subs, content_posted_this_week, dms_replied_median_minutes} — بازنویسی مقید
- `receipts.jsonl` با همان سبک: CONTENT_APPROVED / CONTENT_POSTED_MANUAL / GATE_CARD_SENT / …

**A3. پذیرش A (باید همه سبز شود):**
- pytest سبز: idempotency تقویم (هیچ آیتمی دو بار «posted» نشود)، cursor ها، سقف «حداکثر N کارت مالک در روز»، caption engine هیچ محتوای صریح تولید نکند (لیست کلمات ممنوع + تست منفی)، لاگ صادح
- یک شبیه‌سازی کامل ۷روزه با فیک-دیتا در `tests/sim_week1/` + خروجی متر

---

## ۲. بیزنس B — Ziman Gift (فروشگاه هدیه، سیدنی — Shopify)

واقعیت امروز:
- دامنهٔ ziman-gift.com.au وصل و زنده؛ ۳۵+ محصول (ZM-0013=$67.50)؛ قالب Atelier (درفت)
- `store_watch` هر ۳۰دقیقه روی سرور ما: DNS + صفحهٔ محصول + سفارش‌ها → مارکر «اولین سفارش»
- عکس محصولات: خطِ آپلود API-دار آماده است؛ متن Hero و صفحات = کار ۵دقیقه‌ای مالک
- مجوزهای باز: Google free listing و FB/IG بعد از بررسیِ دامنه (زنجیرهٔ W9-2)، دایرکتوری‌های محلی (GBP/Gumtree) انسانی‌مانده

### چه بسازید (`ziman-drive/` در repo خودتان)

**B1. قیف مناسبتی به‌جای قیف لید:**
- `occasions_master.json`: مناسبت‌های فروش سیدنی (Valentine's, Mother's Day, Christmas, Sympathy, Birthday, Corporate) با {name, date, lead_window_days, top_skus[], landing_slug}
- `campaign_packets/ZC-*.json`: اسکیما مثل quote-packet + فیلدهای {occasion, products[sku], channel:"email_existing"|"google_post"|"fb_ig", creative_copy(EN), budget_usd:0, owner_go_required:true}
- `copy_engine.py`: تولید متن کمپین انگلیسیِ لوکس (پلتون: wealthy Sydney، بدون فارسی، بدون تخفیف‌خواهی) — همان سبک A/B (دو قالب موضوع، قاعده تصمیم عددی، مهر variant)
- `ziman_queue.py` = همان send_queue ما با یک تفاوت: خروجی‌اش «بستهٔ آمادهٔ انتشار» است نه ارسال مستقیم؛ انتشار عمومی فقط پس از ردیف owner-decision
- `ziman-meter.json`: {verified_cash(=مجموع سفارش تأییدشده از store_watch), orders_total, first_order_at, campaigns_approved, campaigns_published}

**B2. پذیرش B:**
- pytest: idempotency کمپین، سقف، لاگ صادق، بدون متن فارسی در خروجی‌ها (تست یونیکد)، copy_engine هرگز discount/«cheap» تولید نکند (تست منفی)
- `tests/sim_valentine/`: شبیه‌سازی کمپین Valentine's از draft تا کارت مالک تا انتشار

---

## ۳. تیم و تقسیم کار (شما تیم گروک هستید — ۳ نقش)

- **ROLE-FUNNEL** (مهندس هسته): فایل‌های master/queue/receipts/meter + گیت‌ها + تست‌های idempotency — هر دو بیزنس
- **ROLE-CHANNEL** (مهندس کانال): caption/copy engineها + اینترفیس‌های هشدار + شبیه‌سازی‌ها
- **ROLE-QA** (بازرس): اجرای همهٔ تست‌ها + مرور خطوط قرمز + گزارش فارسی تحویل (`DELIVERY-FA.md`) با جدول «چه ساختیم/کجاست/چطور تست شد/چی ماند»

هر PR/فایل باید هدر استاندارد داشته باشد: `# OWNER-CONTRACT v1 — no secrets, no external effect without owner GO, VERIFIED_CASH only`.

## ۴. قرارداد تحویل (repo شما)

```
<repo>/
  nova-drive/  ziman-drive/  tests/  DELIVERY-FA.md  INTEGRATION-RUNBOOK.md
```
`INTEGRATION-RUNBOOK.md` باید خط‌به‌خط بگوید تیم ما (که به سرورها دست دارد) چه فایلی را کجا بگذارد و چه تایمری بگذارد — بدون هیچ گام «شما دسترسی بگیرید».

## ۵. خطوط قرمز (نقض = باطل)

1. هیچ API/cookie/scraper علیه OnlyFans یا FeetFinder — حتی «برای تست».
2. هیچ ارسال/پست/DM واقعی — شما فقط صف + کارت مالک + شبیه‌سازی می‌سازید.
3. هیچ secret/پسورد/توکنی در کد یا دیتا؛ فقط نام متغیر.
4. محتوای صریح جنسی در captionها ممنوع (brند no-face و classy).
5. هیچ ادعای درآمد غیر VERIFIED_CASH؛ هیچ شمارش فالوور به‌عنوان پول.
6. idempotency + سقف روزانه + رسیدهای append-only — مثل موتور مرجع.
7. فقط چیزهایی که با تست سبز قابل نشان‌دادن‌اند ادعا شود؛ خوش‌بینی ≠ انجام‌شده.

**تعریف تمام‌وکامل:** هر دو پوشه + همهٔ تست‌ها سبز + دو شبیه‌سازی + DELIVERY-FA و INTEGRATION-RUNBOOK کامل. کمتر از این = ناقص.
