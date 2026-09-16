---
type: proposal
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: ready
tags: [creator-business, marketing, telegram]
created: 2026-08-03
updated: 2026-08-03
extends: "[[03 - Projects/اونلی فنز/00 - Control/DEEP-SCAN-2026-08-03-FULL]]"
---

# PROP-D5 — مینی‌اپ تلگرامی «اتاق فرمان شبکه‌های اجتماعی Project-F»

> ✅ **فاز ۱ ساخته و راستی‌آزمایی شد (2026-08-03، GO ِ مالک «مینی‌اپ رو بساز»).** وضعیتِ تحویل در §۹ انتهای سند. فازهای ۲ و ۳ هنوز پیشنهادند.
> propose-only. ساخت کد = RED در RISK-LADDER ⇒ شروع فقط با GO ِ صریح مالک. این سند بلوپرینت کامل است.

## ۰. تعریف در یک جمله

یک Telegram Mini App که پشت **همان gateway ِ موجود 8774** می‌نشیند و کل عملیات مارکتینگ Project-F را از موبایل مالک قابل‌دیدن و قابل‌تصمیم می‌کند — **صف تأیید انسانی، نه افکتور**: هیچ متد post/send/publish/pay در هیچ لایه؛ خروجی هر تأیید = payload ِ copy-paste با کد tracking که مالک خودش دستی پست می‌کند (دقیقاً الگوی نیمه‌دستی ToS-safe ِ بازار ۲۰۲۶).

## ۱. چرا الان می‌ارزد

- GATE 0 باز است ولی مینی‌اپ هیچ اکشن بیرونی ندارد ⇒ ساختنش امروز مجاز است؛ روز بازشدن گیت، عملیات از دقیقهٔ اول با انضباط بازار ۲۰۲۶ شروع می‌شود نه با اکسل.
- ۱۰۰٪ backend از قبل هست: صف‌ها (`acquisition_pipeline`/`dm_pipeline`)، KPI ‏(`KPIRollup`+spec ِ آستانه‌ها)، CRM ‏(`FanDB`)، بانک محتوا (`VaultBank` ۲۲ asset)، گاردها، audit، capability registry، فرمان‌های `/pf_*`. گپ = چسب، نه کد جدید.
- گلوگاه واقعی پروژه ۱۴ روز است «تصمیم انسانی» است — کارت گیت‌ها + سینی رأی همین را حل می‌کند.

## ۲. معماری (بازمصرف حداکثری)

```
Telegram (دکمهٔ web_app / لینک t.me)
   │ initData
   ▼
cloudflared tunnel  ──►  miniapp_gateway.py :8774   ← موجود، دست نمی‌خورد جز افزودن مسیر
                          ├─ HMAC initData (≤300s) + allowlist مالک   ← موجود
                          ├─ GET  /api/pf/*  ← جدید: read-only، سیم به miniapp_state.dispatch_api
                          │     منابع: brain/store.py ‏(langar/*.json) · pf_os/capabilities.py
                          │             · PROJECT-F-CONTROL-MANIFEST.json · VERDICT_QUEUE.md
                          ├─ POST /api/actions ← موجود (OpsActionEngine، idempotent)
                          │     اکشن‌های pf از مسیر langar_bridge → LangarBot.handle()
                          └─ STOP-MINIAPP ‏fail-closed + miniapp-hits.jsonl   ← موجود
فرانت: tab/section «PF» در همان شل miniapp/ (vanilla JS، تم --tg-theme-*، RTL + ایزولهٔ bidi)
```

- **هیچ سرور/پورت/توکن جدید.** فرمان‌ها از پل موجود `_ops/legs/langar_bridge.py` می‌گذرند (قانون لا‌مزاحمی: `langar_bot.py` بازنویسی نمی‌شود).
- مرز داده = قرارداد SHADOW_ONLY: بیرون از پوشهٔ پروژه فقط aggregate/count ‏content-free ‏(`{beat, drafts_count, dm_pending, acq_ready, full_stop, karma_met, …}`)؛ متن درفت‌ها فقط داخل صفحهٔ احرازشدهٔ مالک رندر می‌شود و هرگز در لاگ/state ِ مشترک نمی‌نشیند.

## ۳. قابلیت‌ها — فازبندی

### فاز ۱ (MVP — «ببین و تصمیم بگیر»)
1. **کارت گیت‌ها و بلاکرهای انسانی**: GATE 0 / سه امضا / NO-GO / شمارندهٔ verdictهای معلق — از MANIFEST ‏(صفر-PII، برای همین ساخته شده).
2. **صف تأیید پست**: کارت‌های draft با ok/no/ready ‏(`/pf_queue`→`/pf_ok`→`/pf_ready`)؛ خروجی ready = بلوک copy-paste + کد `L-` ‏(LinkState) با دکمهٔ copy.
3. **صف DM ِ HITL**: ‏draft ِ welcome/winback/ppv-offer → تأیید → payload ِ دستی (`/dm_*`؛ پیش‌نیاز: فیکس باگ `_dm_inbox`).
4. **داشبورد KPI**: جدول هفتگی + چراغ‌های سبز/زرد/قرمز از آستانه‌های hard-coded ِ spec + **فرم ورود سریع جمعه** ‏(`/kpi_record`، `/kpi_import`) — SOP ‏۳۰دقیقه‌ای → چند دقیقه.
5. **وضعیت گاردها + دکمهٔ اضطراری**: WarmupGuard/ChannelLocks/full_stop + دکمهٔ KILL ‏(فایل `langar/KILL` از مسیر `/api/actions` ِ owner-gated)؛ revive عمداً بدون دکمه؛ HALT ِ استودیو فقط نمایش (حق انحصاری C).
6. **دکمه‌های خاموش با دلیل**: از `pf_os/capabilities.py` — هر قابلیت red با «چرا قفل است و چه چیزی بازش می‌کند» (درس UI-Truthfulness: هرگز دکمهٔ مرده).

### فاز ۲ (عمق عملیاتی)
7. **سینی رأی**: رندر VERDICT_QUEUE/OpenQuestions به کارت تصمیم با گزینه‌ها؛ تپ مالک «پیشنهاد رأی» ثبت می‌کند (idempotent)؛ الزام فقط با DecisionLog ‏(DECISION-SOT) — هرگز خودکار.
8. **مرورگر VaultBank**: ۲۲ asset با used_count/rotation ‏(metadata-only، هرگز رسانه).
9. **Fan CRM ِ صفر-PII**: سگمنت‌های vip/regular/lurker/churned + سیگنال at-risk ‏(اولین مصرف‌کنندهٔ `lifecycle.py` ِ يتیم).
10. **زمان‌بند shadow**: تقویم صف با پنجرهٔ طلایی (۹–۱۲ صبح سیدنی = پیک شب US) — فقط یادآور + payload، هرگز auto-post.
11. **چک‌لیست pre-post به‌عنوان گیت ready**: چک‌لیست ۱۲موردی Reddit / ۶موردی X از research-results — تیک کامل → آزادشدن `/pf_ready`.
12. **لاگ ممیزی**: viewer ِ `approvals.jsonl` با فیلتر origin ‏live/test.

### فاز ۳ (پاسخ به شکاف‌های P0 ِ بازار ۲۰۲۶)
13. **صف retention/winback** (طراحی جدید روی قطعات موجود — پاسخ به بزرگ‌ترین گاف): پنجرهٔ ۷۲h، ردیاب rebill٪، trigger ِ winback از churned ِ FanDB → درفت در dm_pipeline با `proposed_by='retention'`.
14. **لاگ A/B قیمت** ‏(`ab_tracker.py` ِ يتیم + آزمایش پیش‌ثبت‌شدهٔ $5-vs-$8) + «چرا این پیشنهاد؟» ‏(`ThompsonBandit.explain()`).
15. **دیتابیس قوانین per-subreddit + مانیتور shadowban** (چک logged-out هفتگی، read-only مجاز) + **هزینه‌سنج** ‏(CostMeter + سقف AUD 100).
16. دایجست یکشنبه برای C ‏(درفت content-free؛ ارسال دستی مالک).

## ۴. تحویل «فقط لینک» در تلگرام

- **فاز dev (همین حالا ممکن):** مرکز دکمهٔ inline ِ web_app را از `miniapp-url.json` می‌سازد — با هر ری‌استارت تونل، دکمهٔ تازه؛ فقط در DM مالک (دکمهٔ web_app در گروه کار نمی‌کند).
- **فاز پایدار:** دامنهٔ شخصی + named tunnel ِ cloudflared به‌صورت سرویس ویندوز + ثبت `/newapp` در BotFather → لینک دائمی `t.me/<bot>/<app>` — ⚠️ BotFather = RED-tier ⇒ **فقط دست مالک**.
- الزام ۲۰۲۶: same-origin ‏(از 2026-07-20 تلگرام cross-origin را می‌بندد) — دامنهٔ ثبت‌شده = دامنهٔ سرو.

## ۵. قیود ایمنی (غیرقابل‌مذاکره)

1. صف تأیید انسانی، نه افکتور: هیچ متد post/send/publish/pay؛ تضمین ساختاری `test_no_outward_methods` به endpointهای جدید تعمیم و تست می‌شود.
2. هیچ مسیری برای دورزدن GATE 0/NO-GO؛ هیچ ایجنتی stamp را GO نمی‌کند؛ approve به‌جای انسان هرگز.
3. هر درخواست پشت HMAC ِ initData + تطبیق user.id با مالک؛ شکست = 403 بدنهٔ خالی؛ `initDataUnsafe` هرگز مبنای سرور نیست.
4. content-free بیرون از پوشه (قاعدهٔ #۷)؛ صفر PII؛ هیچ‌چیز از `langar_config.json` سرو نمی‌شود؛ fan فقط با هش.
5. kill-switch فایلی در هر درخواست: STOP-MINIAPP ‏(503) / KILL / HALT؛ kill از راه دور مجاز، revive ممنوع.
6. همهٔ فلگ‌های نو default-OFF ‏(فقط رشتهٔ "1")؛ flag-off = بایت‌به‌بایت no-op؛ فعال‌سازی بعد از ۷ روز shadow ِ موفق با معیار «پاسخ routed واقعی».
7. هیچ توکن جدید؛ تونل فقط به 8774؛ snapshot ِ کهنه خاکستری رندر می‌شود نه سبز (`telemetry.is_stale`).
8. مینی‌اپ روی `studio/drafts.json` فقط read-only (قاعدهٔ دو-نویسنده)؛ نوشتن فقط از مسیر فرمان‌های موجود لنگر.
9. هیچ ابزار session-based/scraping روی OF؛ دادهٔ OF فقط CSV ِ export ِ رسمی.
10. کد در worktree + commit با pathspec صریح؛ رسیدن به درخت زنده فقط با merge ِ مالک.

## ۶. پیش‌نیازهای فنی فاز ۱ (کارهای کوچک قبل از UI)

- فیکس باگ `_dm_inbox` ‏(langar_bot.py).
- endpointهای `GET /api/pf/*` در `miniapp_state.dispatch_api` + تست boundary-egress ‏(schema ِ SHADOW_ONLY).
- تصمیم ناسازگاری PLAN-T4 ‏(«هیچ POST» در برابر `POST /api/actions` ِ موجود) — رأی مالک.
- (اختیاری، هم‌سو با G-007) یک خط وصل `saba_bridge_beat` پشت `OCTOPUS_WIRE_SABA_BRIDGE`.

## ۷. سنجهٔ موفقیت

- زمان SOP جمعه: ۳۰ دقیقه → ≤۵ دقیقه.
- هر verdict ِ معلق ≤۲ تپ از موبایل تا «پیشنهاد رأی» ثبت‌شده.
- صفر دکمهٔ مرده (ممیزی UI-Truthfulness)؛ صفر PII/متن در لاگ‌های بیرون از پوشه؛ ۱۰۰٪ endpointها پشت HMAC ‏(پن‌تست دستی: initData ِ دستکاری‌شده/کهنه/غریبه هر سه 403).

## ۸. رأی‌های لازم مالک برای شروع

| # | تصمیم | پیشنهاد |
|---|---|---|
| 1 | GO ِ ساخت فاز ۱ (کد جدید در `_ops/telegram_center` + `miniapp_state`) | ✅ بساز |
| 2 | سوار شدن روی gateway ِ 8774 موجود به‌جای پورت/آداپتور جدا | ✅ همان 8774 (سند SHADOW_ONLY پورت جدا را طرح کرده بود ولی design-only است) |
| 3 | مجاز بودن `POST /api/actions` برای اکشن‌های pf ‏(approve/kill/رأی پیشنهادی) | ✅ با همان OpsActionEngine ِ idempotent |
| 4 | فیکس `_dm_inbox` هم‌زمان با فاز ۱ | ✅ |
| 5 | tunnel: quick ِ فعلی برای dev؛ دامنه + named tunnel + ‏/newapp = بعداً دست مالک | ✅ |

## ۹. وضعیت تحویل — فاز ۱ (2026-08-03)

### ساخته شد
| فایل | نقش |
|---|---|
| `_ops/telegram_center/pf_miniapp.py` (نو) | شش کارتِ read-only: `/api/pf/{status,gates,queue,kpi,guards,capabilities}` — بدونِ هیچ import از کدِ پروژه (فقط خواندنِ JSON)، fail-closed، سه‌حالتی |
| `_ops/telegram_center/miniapp_gateway.py` | ‏+۲۵ خط: مسیرهای `/api/pf/*` پشتِ همان دیوارِ HMAC (‏403 با بدنهٔ خالی) |
| `_ops/telegram_center/miniapp/app.js` + `index.html` | تبِ Project-F با شش کارت؛ **و تعمیرِ mojibake**: همهٔ رشته‌های فارسیِ شل روی دیسک خراب بودند (کاربر بایتِ آشغال می‌دید) |
| `_ops/tests/test_pf_miniapp.py` (نو) + ثبت در `run_all.py` | ۱۹ تست |
| `langar/langar_bot.py` + `langar/test_dm_inbox_wiring.py` (نو) | فیکسِ باگِ `/dm_inbox` (متدِ گم‌شده) + ۶ تستِ رگرسیون |

### سنجه‌ها (خروجیِ واقعی)
- ‏`test_pf_miniapp.py` ‏**۱۹/۱۹** · ‏`test_dm_inbox_wiring.py` ‏**۶/۶** · پروژه `tests/` ‏**۱۵۲** · `langar` ‏**۲۳** · `pf_os` ‏**۱۱۹** · `studio` ‏**۴۳**.
- **جهش‌آزمایی (چهار گارد، همه گرفته شدند):** نشتِ محتوا ⇒ ۱ قرمز · دورزدنِ auth ⇒ ۴ قرمز · نادیده‌گرفتنِ فلگ ⇒ ۳ قرمز · «کهنه همیشه تازه» ⇒ ۱ قرمز.
- **اثباتِ زندهٔ end-to-end** روی سرورِ واقعی (پورتِ ۸۷۹۹، توکنِ ساختگی): بدونِ initData ⇒ ‏403 و یک پیامِ صریح؛ با initData ِ معتبر ⇒ هر شش endpoint ‏200 و کارت‌ها از manifest ِ **واقعی** رندر شدند (GATE 0 ‏OPEN · ۱۱ رأیِ منتظر · مهرِ GO نیست ⇒ همهٔ قابلیت‌ها 🔒 با دلیل). صفر خطای کنسول.

### روشن‌کردن (دستِ مالک)
```
OCTOPUS_PF_MINIAPP=1
```
سپس ری‌استارتِ مرکز/gateway. تا آن لحظه مسیرها **404**اند و ماژول حتی یک فایل هم باز نمی‌کند.

### آنچه عمداً ساخته **نشد** (رأیِ مالک لازم است)
1. **متنِ درفت در مینی‌اپ.** فاز ۱ فقط شمار/شناسه می‌دهد. دیدنِ متنِ hook/کپشن/بدنهٔ DM = پهن‌کردنِ مرزِ قاعدهٔ #۷ (خروجِ محتوا از پوشهٔ پروژه) و رأیِ جدا می‌خواهد.
2. **هیچ دکمهٔ اکشن.** کارت‌ها فقط خواندنی‌اند؛ تأیید/رد همچنان از فرمان‌های تلگرام (`/pf_ok`، `/dm_ok`).
3. فازهای ۲ و ۳ (سینی رأی، VaultBank، CRM، retention، A/B، shadowban) دست‌نخورده ماندند.

### 🔴 یافتهٔ امنیتیِ pre-existing (خارج از این لِین، برای رأیِ مالک)
هشت مسیرِ read-only ِ PHASE 4 (‏`/api/state`، `/api/legs`، `/api/ops`، …) **بدونِ احرازِ initData** سرو می‌شوند — روی تونلِ عمومی یعنی هرکس URL را داشته باشد وضعیتِ ارگانیسم را می‌بیند (اسکراب‌شده، ولی بی‌احراز). مسیرهای PF ِ نو عمداً پشتِ HMAC رفتند. هم‌ترازکردنِ آن هشت‌تا = تصمیمِ تو.
