# SYDNEY GIFT BUSINESS BLUEPRINT — Ziman 2027 (طرح پیشنهادی، نه اجرا)

- **نسخه:** 1.0 · **زمان:** 2026-07-17 · **نویسنده:** Project Discovery & Business Automation Agent
- **وضعیت:** **سند طراحی — هیچ اجرا، خرید، لیستینگ، پرداخت یا پیام واقعی مجاز نیست.**
- **قواعد حاکم:** propose-only · تأیید صریح انسانی برای هر اکشن مالی/بیرونی · بدون secret در طراحی · هر بخش حقوقی/مالیاتی نامشخص = **BLOCKED / نیازمند تأیید متخصص**
- **رابطه با پروژهٔ موجود:** این Blueprint روی زیرساخت حاکمیتیِ ساخته‌شدهٔ Ziman Galerry (`control-brain` + `ziman-agent` + `_ops` leg) سوار می‌شود؛ بخش ۱۱.

---

## ۰) قاعدهٔ مرز (الزامی در ابتدای هر پرامپت ایجنت)

```text
PROJECT BOUNDARY — NON-NEGOTIABLE
You are working only on Project ZIMAN (product/gift commerce).
Out of scope: Sydney painting business, tradie marketplaces, job quoting,
construction/strata/property maintenance, and any Painting OS assets.
Before using any file, integration, DB table, Telegram channel or workflow,
verify its project tag is exactly ZIMAN; if unclear → BLOCKED + ask owner.
Never merge ZIMAN and Painting OS data, credentials, budgets, channels or memory.
```

> شواهد اسکن (2026-07-17): درخت `_launchpad/second-brain-live` هم‌اکنون این مرز را نقض می‌کند (painting-bot کنار ziman-agent). این Blueprint برای ساختار جدید، جداسازی کامل را پیش‌فرض می‌گیرد.

## ۱) بازار هدف و فرضیات قابل‌اعتبارسنجی

**بازار:** سیدنی، استرالیا — خریداران هدیه (مصرف‌کنندهٔ نهایی + corporate gifting کوچک). بازار گرم اول: جامعهٔ فارسی‌زبان سیدنی (مناسبت‌های نوروز/یلدا/تولد/نامزدی).

**فرضیات (هر کدام با روش اعتبارسنجی):**

| # | فرض | روش اعتبارسنجی | معیار قبولی |
|---|---|---|---|
| A1 | تقاضای پولی برای دستهٔ انتخابی هست | ۱۰–۳۰ گفت‌وگوی بازار گرم + ۱ پیش‌فروش دستی | ≥۳ سفارش واقعی پرداخت‌شده |
| A2 | margin هدف پس از هزینه‌ها مثبت است | ثبت COGS+fee+delivery هر سفارش در ledger | margin ≥ هدف بخش ۶ در ۸۰٪ سفارش‌ها |
| A3 | کانال اول (تلگرام/اینستا/مارکت‌پلیس محلی) پاسخ می‌دهد | آزمایش ۲ هفته‌ای یک کانال، دستی | ≥۵ لید واجد شرایط |
| A4 | تأمین‌کننده/تولید پایدار است (SLA زمانی) | ثبت زمان آماده‌سازی ۱۰ سفارش | انحراف ≤۲ روز |
| A5 | مشتری حاضر به PayID/پرداخت مجاز است | نرخ تکمیل پرداخت در گفت‌وگوها | ≥۷۰٪ |

**تصمیم دامنه (باز، مالک):** نوع «Gift» — (الف) هدیه فیزیکی دست‌ساز = ادامهٔ زیمان فعلی؛ (ب) Gift Card دیجیتال رسمی؛ (ج) Telegram/NFT Gift = **BLOCKED تا بررسی حقوقی**. پیشنهاد طراحی: شروع با (الف) یا (ب) در یک niche؛ (ج) فقط ماژول تحلیل read-only.

## ۲) مدل کسب‌وکار

- **Sourcing:** سه مدل جدا — Owned Inventory (فقط پرفروش/کم‌ریسک) · Just-in-time (تهیه پس از سفارش از تأمین‌کنندهٔ ثبت‌شده) · Affiliate/Referral (بدون موجودی، فقط کمیسیون). هر تأمین‌کننده: SLA، نرخ خطا، نرخ refund، region-lock ثبت می‌شود.
- **قیمت‌گذاری:** موتور فرمولی — `Sell = Cost + payment/platform fees + fraud/dispute reserve + delivery/support + target margin − approved discount`. قیمت‌ها **Quote دارای انقضا** برای اقلام نوسانی؛ هیچ قیمت تضمینی طولانی.
- **Inventory:** موجودی لحظه‌ای از `inventory_snapshot.v1` (measured_at اجباری). فروش کالای ناموجود ممنوع (D4 تعمیم‌یافته).
- **فروش:** کانال اول یکی است (verdict). همهٔ سفارش‌ها از صف تأیید انسانی رد می‌شوند تا خروج از shadow.
- **پشتیبانی:** Sales Concierge نیمه‌خودکار (پاسخ پیش‌نویس، موجودی، وضعیت سفارش) + escalation به مالک؛ سیاست refund/dispute مکتوب و لینک در هر سفارش.

## ۳) تفکیک Manual / Assisted / Automated

| فعالیت | Manual | Assisted (پیش‌نویس+تأیید) | Automated (فقط پس از خروج مرحله‌ای از shadow) |
|---|---|---|---|
| مانیتور قیمت/موجودی/ترند | — | — | ✅ read-only، بدون اکشن |
| تولید آگهی/کپشن/DM | — | ✅ (وضعیت فعلی زیمان) | — |
| پاسخ به مشتری | ✅ حساس | ✅ پیش‌نویس | فقط FAQ ساده، با برچسب ربات |
| تأیید قیمت/تخفیف/سفارش بزرگ | ✅ همیشه | — | هرگز بدون RED مالک |
| پرداخت/برداشت/انتقال دارایی | ✅ همیشه | — | **ممنوع در این طراحی** |
| توقف اضطراری (kill switch) | — | — | ✅ خودکارِ fail-closed |
| ثبت ledger/audit | — | — | ✅ خودکار |

## ۴) معماری پیشنهادی (نگاشت روی اجزای موجود)

```text
Telegram Owner Console (خشک: TELEGRAM-CONTRACT.md، dry-run)
        │  RED ladder / آره-نه
        ▼
Human Approval Queue  ←—— control-brain: governance.py + command_registry (موجود ✅)
Risk Engine           ←—— capacity.py + budget.py + product.anti_misread (موجود ✅) + price/volatility guards (جدید)
Audit Log             ←—— evt.v1 hash-chain ledger (موجود ✅)
Alerts                ←—— octopus_bridge digest / telegram_center (نیازمند verdict برای live)
Backend API           ←—— control-brain app.py + ziman-agent worker/phase2_cli (موجود ✅)
Database              ←—— فعلی: JSON/ledger فایل‌محور؛ پیشنهاد: SQLite/Postgres در فاز MVP-3 (طرح، نه اجرا)
Price Monitor         ←—— جدید (فاز MVP-1): read-only scraper/API polling با rate-limit
Sales Inbox + CRM     ←—— جدید (فاز MVP-2/3): lead.v1/order.v1 روی ledger
```

اصل: **هر ماژول جدید پشت فلگ خاموش + تست + ثبت در ledger** — همان الگوی گام ۱/۲ roadmap فعلی.

## ۵) مدل داده پیشنهادی (v1 — طرح)

| Entity | فیلدهای کلیدی |
|---|---|
| `gift.v1` | id، type(physical/digital_card/nft*)، title، supplier_id، region_lock، cost_aud، fees، min_margin_pct، stock_state، expiry_policy، status(draft/verified/paused/blocked) |
| `customer.v1` | id (بدون PII در ledger — PII جدا و محلی)، consent_flags، opt_in_channel، first_seen، tags |
| `order.v1` | id، gift_id، customer_ref، quote_id، amount_aud، cost_aud، fees، payment_method(PayID/…)، delivery_method، state(draft→approved→paid→delivered→closed/refunded)، timestamps |
| `price_quote.v1` | gift_id، sell_aud، components(فرمول بخش ۲)، valid_until، approved_by(human) |
| `profit_ledger.v1` | per order: revenue، cost، fees، reserve، net_margin، dispute_cost |
| `risk_event.v1` | type(margin_breach/capital_cap/daily_loss/volatility/duplicate/fraud_signal)، entity_ref، score، action_taken |
| `approval.v1` | payload_ref، class(RED/…)، requester، decision(owner only)، decided_at، evt_ref (hash-chain) |
| `supplier.v1` | id، type(owned/JIT/affiliate)، sla_days، error_rate، refund_rate، verified_at |

\* type=nft در MVP غیرفعال (BLOCKED) — فقط فیلد رزرو.

## ۶) موتور تصمیم‌گیری با سقف ریسک (همه fail-closed)

| قاعده | پیش‌فرض پیشنهادی (قابل‌تنظیم توسط مالک) | رفتار |
|---|---|---|
| حداقل margin | ≥ ۲۰٪ خالص پس از همهٔ هزینه‌ها | زیر آن: پیشنهاد رد + دلیل |
| حداکثر سرمایه در هر معامله | ≤ AU$50 (MVP) | بالاتر: RED مالک |
| سقف ضرر روزانه | AU$30 | عبور: توقف خودکار فروش روز + alert |
| تشخیص نوسان غیرعادی | تغییر قیمت تأمین > ۱۵٪/۲۴ساعت یا موجودی مبهم | listing → `PAUSED` / `VERIFY_REQUIRED` |
| Kill switch | `control-brain halt` + `STOP-ORGANISM` (موجود ✅) | همهٔ صف‌ها refuse؛ فقط مالک resume |
| جلوگیری از معاملهٔ تکراری | dedupe روی (gift_id, customer_ref, 24h) + idempotency-key | تکراری: رد + log |
| ظرفیت (میراث D4) | capacity_fail_closed ≤۶/هفته تا revalidation | موجود ✅ در leg؛ گیت worker نیازمند verdict |
| بودجهٔ AI/credits | AU$15/ماه Anthropic (موجود ✅) + سقف Higgsfield TBD | عبور: fail-closed |

## ۷) چک‌لیست تطابق — **همه «نیازمند تأیید متخصص»**

| حوزه | نکتهٔ طراحی (ادعای حقوقی نیست) | وضعیت |
|---|---|---|
| Australian Consumer Law | consumer guarantees؛ ممنوعیت «no refunds under any circumstances»؛ شفافیت قیمت نهایی | نیازمند تأیید متخصص |
| Gift Card (در صورت مسیر ب) | حداقل اعتبار ۳ ساله برای کارت‌های مشمول پس از 2019-11-01 + استثناها (تخفیف واقعی/دست‌دوم)؛ شفافیت شرایط/انقضا/activation | نیازمند تأیید متخصص |
| الکل (F4) | فروش/تحویل الکل در NSW احتمالاً مجوز می‌خواهد | **BLOCKED** تا سیاست مالک + مشورت |
| Telegram/NFT/TON | دارایی دیجیتال: راهنمای رگولاتوری، AFCA برای پلتفرم‌های کریپتو، KYC/AML (AUSTRAC)، مالیات (CGT)، ToS تلگرام | **BLOCKED** — مشورت حقوقی/مالیاتی پیش از هر طراحی اجرایی |
| Spam Act 2003 | پیام بازاریابی فقط با رضایت (opt-in) + unsubscribe | نیازمند تأیید متخصص |
| Privacy | Privacy Act/APPs؛ حتی زیر آستانه: سیاست حریم مکتوب؛ PII محلی و جدا از ledger | نیازمند تأیید متخصص |
| مالیات/GST | آستانهٔ ثبت GST $75k؛ تفکیک درآمد Ziman از نقاشی؛ مشورت accountant | نیازمند تأیید متخصص |
| KYC/AML | برای مسیر دیجیتال/NFT یا نگهداری وجه/دارایی مشتری | **BLOCKED** در MVP — بدون custody |
| پلتفرم‌ها | ToS تلگرام/اینستا/مارکت‌پلیس برای فروش و اتوماسیون | بررسی پیش از هر کانال |

## ۸) KPIها

سود خالص (ledger) · margin خالص٪ · زمان فروش (list→paid) · نرخ dispute/refund · موجودی راکد (>۳۰ روز) · هزینهٔ API/AI به‌ازای سفارش · نرخ خطای اتوماسیون (پیش‌نویس ردشده/کل) · نرخ تبدیل لید→پرداخت · repeat purchase · زمان پاسخ به مشتری. همه از `evt.v1` + `profit_ledger.v1` مشتق می‌شوند، نه عدد دستی.

## ۹) برنامه MVP چهارمرحله‌ای

1. **مانیتورینگ و ثبت قیمت (read-only):** Price/Supplier Monitor + کاتالوگ v1 + ledger. خروجی: گزارش روزانه. هیچ پیشنهاد فروش.
2. **هشدار و پیشنهاد معامله:** Risk Engine در حالت پیشنهاد؛ کارت‌های «فرصت/ریسک» در Telegram Owner Console (dry-run تا verdict توکن).
3. **تأیید انسانی و ثبت عملیات:** صف RED فعال؛ هر سفارش با تأیید مالک؛ ثبت کامل در audit ledger؛ اجرای پرداخت/تحویل **دستی توسط مالک**.
4. **اتوماسیون محدود با kill switch:** فقط طبقه‌های کم‌ریسک (مثل پاسخ FAQ یا به‌روزرسانی موجودی) پس از ۱۰–۳۰ معاملهٔ واقعی موفق + تصمیم صریح مالک؛ kill switch و سقف‌های بخش ۶ همیشه فعال.

## ۱۰) نقشهٔ ساختار فایل (پیشنهاد، جدا از Painting)

```text
ZIMAN\
  agents\ (scout, demand, concierge, crm, risk — همه propose-only)
  data\ (ledger، catalog، inventory snapshots)
  crm\  inventory\  marketing\  risk\  docs\
  .env.ziman  ← فقط مالک؛ هرگز در git/گزارش
SYDNEY_PAINTING_OS\  ← کاملاً جدا (repo/env/db/log/بودجه/کانال جدا)
```

## ۱۱) طرح ادغام Higgsfield (فاز ۴ — پیش از هر اتصال)

- **هدف:** تولید ویدیو/ریل ۳۰–۶۰ثانیه‌ای محصول از کیت موجود `content/higgsfield-video-kit-2026-07-07.md` برای مارکتینگ زیمان — فقط پس از verdict محتوا.
- **وضعیت دانش:** نام «Higgsfield» در MANIFEST.yaml پروژه ثبت است؛ اعتبار تخمینی ~AU$70 ≈ 835 credits [To measure]. **نام دقیق سرویس و دامنهٔ رسمی هنوز با مالک تأیید نشده.**
- **پیش‌نیاز ۱ (از مالک):** تأیید نام/دامنهٔ رسمی → سپس بررسی مستندات رسمی برای API/OAuth/روش اتصال مستند.
- **حداقل دسترسی (least privilege):** فقط scope لازم برای تولید ویدیو؛ بدون دسترسی به پرداخت/حساب‌های دیگر؛ اکانت جدا برای بیزنس در صورت امکان.
- **ذخیرهٔ Secret:** environment variable محلی یا Secret Manager؛ **هرگز** در git/گزارش/پرامپت؛ الگوی موجود: `.env.ziman` + `.gitignore`.
- **چرخش/لغو:** ثبت تاریخ صدور کلید، چرخش دوره‌ای (پیشنهاد ۹۰ روز)، لغو فوری از پنل رسمی هنگام تغییر نقش/ریسک.
- **سقف هزینه:** ثبت سقف اعتبار در `MANIFEST §budget_caps`؛ هشدار مصرف در ۵۰/۸۰/۱۰۰٪؛ fail-closed مانند budget.py.
- **Fallback:** اتمام credit/قطع سرویس → مسیر offline (کپشن/تصویر ثابت)؛ صف ویدیو `PAUSED` نه fail-open.
- **اجرای اتصال:** فقط پس از تأیید مالک، **صفحهٔ ورود رسمی باز می‌شود و خودِ مالک لاگین می‌کند**؛ سپس **یک تست کم‌هزینهٔ غیرمالی** (مثل خواندن وضعیت حساب/یک رندر تستی) با ثبت نتیجه در ledger.

## ۱۲) آنچه این سند نیست

اجرای واقعی نیست · مشاورهٔ حقوقی/مالیاتی نیست · تضمین سود نیست · مجوز خروج از shadow نیست. هر بخش BLOCKED فقط با بررسی انسانی/متخصص باز می‌شود.

**No secrets were copied or exposed.**
