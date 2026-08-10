---
tags: [ofn, moc, home]
aliases: [خانه, نقشه, Home]
updated: 2026-08-10
---

# 🐙 OFN — نقشهٔ پروژه

> این یادداشتِ خانه است. کل پروژه یک **والت ابسیدین** است که همان مخزن گیت
> است — پس جابه‌جا کردنش یعنی `git clone`، و هیچ چیز جا نمی‌ماند.

```
کرنل تصمیم می‌گیرد.   مدل مشورت می‌دهد.   انسان حکم می‌کند.
```

---

## ⚡ نگاه کلی برای ایجنت بعدی — این را اول بخوان

دو پروژهٔ زنده روی یک اورنج‌پای ۵ پرو، هر دو برای «آری/سبا»:

| پروژه | مسیر | پورت | سرویس | تست | وضعیت |
|---|---|---|---|---|---|
| **OFN** (مولتی‌تنانت) | `/home/ari/ofn` | ۸۷۹۱-۸۷۹۴ | `ofn.service` | `tools/repo_baseline.py --tests` | 🟢 زنده |
| **hypno-fugu-mini** (تک‌کاربر) | `/home/ari/hypno-fugu-mini` | ۸۸۹۵ | `hypno-fugu-mini.service` | اول جلسه بسنج | اول جلسه بسنج |

عدد تست OFN اینجا نوشته نمی‌شود ([[CLAUDE|§۸-الف]]). ستون hypno هم «بسنج»
است چون `repo_baseline.py` فقط این مخزن را می‌خواند و عدد آن پروژه از اینجا
راستی‌آزمایی نمی‌شود.

**OFN چهار تنانت فنی دارد: `ziman` · `lead` · `studio` · `hypno`.**

```
ziman · lead · studio   نگاشت فعال WebApp/پورت دارند  (۸۷۹۱ · ۸۷۹۲ · ۸۷۹۳)
hypno                   تنانت واقعی در packs/ · بدون WebApp عملیاتی
                        خارج از scope پرتفوی تا charter مالک
```

**GiftMesh Sydney** برند/خط عرضهٔ `ziman` است، نه تنانت پنجم.
مرجع: [[DECISIONS|D-25]] · [[PORTFOLIO-TENANT-MAP]].

**چه کارها تمام شده‌اند (جلسهٔ ۲۰۲۶-۰۸-۰۹):**
- ✅ [[DECISIONS|D-25]] — GiftMesh برند `ziman` است، نه تنانت. سه نام دیگر هم
  تصحیح شد. مرجع: [[PORTFOLIO-TENANT-MAP]].
- ✅ پنل مالک کامل شد: ۱۱ endpoint خواندنی که هیچ‌جا دیده نمی‌شدند حالا
  رسم می‌شوند — outbox، زنجیرهٔ لجر، سطوح، خط مغز. **فقط خواندنی.**
- ✅ نشتی پوشهٔ موقت تست بسته شد (هر اجرا ~۱۷۰۰ پوشه جا می‌گذاشت و tmpfs را
  پر می‌کرد تا بوت به SAFE MODE برود).
- ✅ تست هشدار دیگر crash ساختگی در لاگ زندهٔ اپراتور نمی‌نویسد.
- ✅ خط پایهٔ تست از سند برداشته شد و به `tools/repo_baseline.py` رفت.
- ✅ یک دایرکتوری پشتیبان از `0755` به `0700` رفت · §۷-الف در [[CLAUDE]].
- ⛔ corpus زیمان/GiftMesh **وجود ندارد** → pilot تحقیق مسدود. «۱۵۰۰+ منبع»
  unverified. رجیستری `lead` هم metadata کانال است، نه corpus.

**چه کارها تمام شده‌اند (جلسهٔ ۲۰۲۶-۰۸-۰۸ — OPERATOR SAFETY + AUDIT):**
- ✅ کلید خاموشی (Kill Switch): دکمه اضطراری در پنل، engage سریع + release دو مرحله‌ای.
- ✅ داشبورد سلامت برد زنده: دما، RAM، load، دیسک (هر ۳۰s).
- ✅ هشدار خرابی سرویس: `ofn-alert.service` (لاگ محلی همیشه + تلگرام پشت flag).
- ✅ Bluetooth راه افتاد (`ap6256-bt.service`، hci0 UP، BT 5.0).
- ✅ NPU runtime نصب شد (`librknnrt.so v2.3.2` + `NPU-GUIDE.md`).
- ✅ ممیزی کامل پروژه — [[AUDIT-2026-08-08]]: ۲ CRITICAL + ۲ HIGH پیدا شد.

**چه کارها تمام شده‌اند (جلسهٔ ۲۰۲۶-۰۸-۱۰):**
- ✅ [[MEGAPROMPT-OWNER-COMPLETE]] اجرا و commit شد (`4dcb0ce` + infra بعدی).
- ✅ NTP + cloudflared زنده · HTTPS پنج دامنه ۲۰۰.
- ✅ connector infra خواندنی: inbox · correlation · inbound rate · HMAC verify ·
  metrics (`d140756`).
- ✅ اسکن کامل چهار کنترل‌پنل + ارتقا: [[docs/handoffs/panel-scans-2026-08-10/INVENTORY]].
- ✅ [[AGENT-NEXT-PANEL-UPGRADE]] اجرا شد:
  `GET /api/v1/owner/observability` + کارت صندوق ورودی در panel ·
  برچسب اولویت انسانی در lead · `setHeaderColor` در studio ·
  empty-state گرم در ziman. حذف ممنوع رعایت شد.

**کارهای باز برای بعد (طرح آماده در مگاپرامپت‌ها):**
- 🔲 [[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]] — ادامهٔ connector بدون sender.
- 🔲 [[MEGAPROMPT-UNIFY]] — ادغام دو ایجنت (بخش‌هایی انجام شده؛ سند را بسنج).
- ✅ لید نقاشی: `lead_priority()` وصل · CRM شریک روی boot · HIGH-1 بسته.

**🔴 فوری از ممیزی (انتخاب با آری):**
- **CRIT-1** — در ۲۰۲۶-۰۸-۱۰ روی برد listener ۸۰۹۰ دیده نشد؛ قبل از هر کار
  فایروال دوباره با `ss` بسنج. اگر برگشت: فقط گزارش، بدون kill تا تأیید آری.
- drift نام `OFN_WIRE_EMAIL/PUBLISH` — با تست drift پوشش؛ خاموش‌سازی env با آری.

**قوانین سخت:** متن فنی در UI ممنوع ([[DECISIONS|D-22]]). هیچ دیتایی حذف نمی‌شود.
هر سرویس restart + health دارد. زبان UI فارسی ساده/گرم. **در ارتقای پنل:
حذف ممنوع — فقط ادغام یا اضافه.**

برای جزئیات بیشتر به ادامهٔ همین یادداشت و [[HANDOFF]] برو.

---

## شروع از اینجا

| ترتیب | یادداشت | چیست |
|---|---|---|
| ۱ | [[HANDOFF]] | **وضعیت زنده.** اول هر جلسه بخوان، آخرش تازه کن |
| ۲ | [[CLAUDE]] | قانون اساسی دستگاه — قوانین سخت، گیت‌ها، درجه‌بندی ریسک |
| ۳ | [[DECISIONS]] | چه چیزی قفل شده، چه چیزی باز است، چه چیزی برای همیشه رد شد |
| ۴ | [[README]] | معماری کد و فازهای تحویل‌شده |
| ۵ | [[CHECKPOINT]] | آخرین وضعیت دروازه‌ها |

## درس‌ها — چه چیزی شکست و چرا

هر دو فایل یک ساختار دارند: علامت · علت واقعی · چطور درست شد · آیا legهای
دیگر هم دارند. **ستون آخر همان چیزی است که ارزش این فایل‌ها را می‌سازد.**

- [[LESSONS-ZIMAN]] — ۱۴ درس از legی که اولین کاربر واقعی را داشت
- [[LESSONS-STUDIO]] — ۸ درس، همه از یک شکل: ادعایی که جدا بررسی نشد
- [[ZIMAN-2026-08-04]] — یادداشت روزی که یک آدم واقعی استفاده کرد

## مگاپرامپت‌ها

- [[AGENT-NEXT-PANEL-UPGRADE]] — ✅ انجام شد — اسکن + ارتقای چهار کنترل‌پنل (۲۰۲۶-۰۸-۱۰)
- [[docs/handoffs/panel-scans-2026-08-10/INVENTORY|اسکن پنل‌ها — قبل و بعد — ۲۰۲۶-۰۸-۱۰]]
- [[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]] — اتصال پلتفرم مارکتینگ با مغز OFN
- [[MEGAPROMPT-OWNER-COMPLETE]] — مالک کامل: ناهنجاری‌ها + دیباگ وب‌اپ‌ها (۲۰۲۶-۰۸-۱۰)
- [[AGENT-NEXT-OWNER-COMPLETE]] — دستورالعمل ادامهٔ owner-complete
- [[MEGAPROMPT]] — دستورکار اصلی پروژه
- [[MEGAPROMPT-UNIFY]] — **ادغام دو ایجنت + حافظهٔ سه‌لایه + مغز مشترک** (مگاپرامپت نهایی)
- [[MEGAPROMPT-EDGE-DEEP]] — **پرورش عمیق مدل لبهٔ سیستم** (مکمل؛ وصل edge.py به مغز + endpoint + حافظهٔ روزانه)
- [[MEGAPROMPT-MINING]] — شاخهٔ ماینینگ ([[DECISIONS|D-8]] از اینجا آمد)
- [[MEGAPROMPT-STUDIO]] — leg چهارم · [[STUDIO-ANSWERS]] · [[STUDIO-BRIEF]]
- [[DESIGN-DIRECTIVE]] — بودجه‌های پوستهٔ استودیو ([[CLAUDE|§۸-الف]]: اعدادش تست‌اند)

## عملیات

- [[APPLY]] — آیین اعمال فایروال (لایهٔ ۲ از [[DECISIONS|D-8]]) · **آری اجرا می‌کند**
- [[POWER-CUT-TEST]] — تست قطع برق

## تنانت‌ها و لِگ‌های عملیاتی

چهار تنانت فنی، سه لِگ با نگاشت WebApp/پورت:

| لِگ | تنانت | پورت | دامنه | UI | وضعیت |
|---|---|---|---|---|---|
| استودیو (سبا) | `studio` | ۸۷۹۳ | `studio.master-painting.com` | `web/studio.html` روی `/sabaapp` | 🟡 زنده — انتشار هنوز قفل |
| لید نقاشی | `lead` | ۸۷۹۲ | `lead.master-painting.com` | `web/lead.html` | ✅ زنده — ثبت + داشبورد + جستجو/فیلتر + جواب/قیمت (تأیید مالک) |
| زیمان | `ziman` | ۸۷۹۱ | `ziman.master-painting.com` | — | 🟢 زنده (اولین کاربر واقعی) · برند: GiftMesh Sydney |
| — | `hypno` | — | — | — | تنانت واقعی در `packs/` · بدون WebApp عملیاتی · خارج از scope پرتفوی ([[DECISIONS|D-25]]) |
| ماینینگ | — | — | — | — | ⬜ متوقف ([[DECISIONS|D-8]]) |

**لید نقاشی** یک CRM کامل برای ورداشت لید نقاشی است: ثبت لید، امتیازدهی،
داشبورد مالک غنی (`web/panel.html`)، و جداول B2B/مناقصه/فروشنده. **جایی که
هنوز وصل نیست** در [[#لید نقاشی — کجا وصل نیست]] پایین‌تر آمده.

---

## وضعیت — اندازه‌گیری ۲۰۲۶-۰۸-۱۰ (پایان جلسه)

```
pytest OFN          عدد را از tools/repo_baseline.py --tests بگیر — اینجا نوشته نمی‌شود
pytest hypno        ۶۲ تست سبز (تاریخی)
سرویس‌ها             ofn · cloudflared · dropbear · hypno-fugu-mini  →  هر چهار active
                    ofn-alert.service نصب شد (OnFailure روی ofn.service)
پورت‌ها              ۸۷۹۱(ziman) ۸۷۹۲(lead) ۸۷۹۳(studio/saba) ۸۷۹۴(owner) ۸۸۹۵(hypno)
                    ⚠️ ۸۰۹۰ = سرور بک‌آپ بی‌احراز هویت (CRIT-1)
git HEAD OFN        (قبل از commit این جلسه)
DB‌های زنده          studio(۲۲ مدیا) · assistant(۳۰ chunk) · painting(۴۴ منبع)
preflight           ۲۸/۲۸ OK
```

> اعداد تستی که در یادداشت‌های قدیمی (۳۷۷ / ۴۱۴ / ۱۲۲۹ / ۱۲۳۹ / ۱۴۹۶ / ۱۵۰۵)
> می‌بینی، همگی قدیمی‌اند. عدد واقعی همین‌جاست و در پایان هر جلسه تازه می‌شود.

## گیت‌های بسته 🔒

| گیت | چرا | باز می‌شود وقتی |
|---|---|---|
| `secret_rotation` | چهار راز CRITICAL نچرخیده | آری بچرخاند |
| `partner_precondition` | پیش‌شرط انتشار استودیو ثبت نشده | ثبت شود |
| `miner_isolation` | [[DECISIONS|D-8]] | قلم ۱ و ۲ و ۳ انجام + تأیید آری |

## بلاکرهای آری

1. سوییچ مدیریتی هست یا نه؟ → لایهٔ ۴ [[DECISIONS|D-8]]
2. فایروال روی ۲۲ → [[APPLY]]
3. توکن‌های بات هنوز خالی‌اند → [[HANDOFF]]

---

## قواعد والت

- **یک منبع حقیقت.** `~/HANDOFF.md`، `~/MEGAPROMPT.md` و
  `~/MEGAPROMPT-MINING.md` حالا symlink به داخل همین مخزن‌اند. مسیر قدیمی
  کار می‌کند، ولی فایل واقعی اینجاست و در گیت است.
- **استثنا: `~/CLAUDE.md`.** عمداً فایل واقعیِ جداست، نه symlink — اگر
  استقرار بعدی `~/ofn` را پاک کند، قانون اساسی نباید با آن برود. الان
  بایت‌به‌بایت برابرِ [[CLAUDE]] است. برای بررسی رانش:
  ```bash
  diff /home/ari/CLAUDE.md /home/ari/ofn/CLAUDE.md && echo یکسان
  ```
- **بعد از پاک شدن مخزن:** `git clone` و بعد symlinkها را دوباره بساز:
  ```bash
  cd ~ && for f in HANDOFF.md MEGAPROMPT.md MEGAPROMPT-MINING.md; do
    ln -sf "ofn/$f" "$f"; done
  ```
- `tests/` و `web/` از دید ابسیدین پنهان‌اند (`.obsidian/app.json`) — کدند،
  نه یادداشت.
- هیچ راز، هیچ PII و هیچ خروجی خام مدل داخل والت نمی‌رود. والت روی گیت‌هاب
  می‌رود ([[CLAUDE|آیین پایان جلسه]]).

## لید نقاشی — وضعیت اتصال

لید نقاشی بیشتر از آن‌که تصور می‌شود ساخته شده، ولی چند جا وصل نیست:

```
✅ ورودی کامل   ثبت لید · امتیازدهی · ۸ جدول (lead_store.py) · داشبورد مالک غنی
✅ امتیاز لید   مدل واقعی lead_priority() وصل است (lead_store.py:500) — heuristic فقط پل است
✅ UI پارتنر    lead.html جستجو/فیلتر/تغییر وضعیت + sheet جواب/قیمت — و از
                ۲۰۲۶-۰۸-۱۰ روی مسیر بوت هم هست. HIGH-1 بسته شد.
                داشبورد نمونهٔ ساختگی و دکمه‌های بی‌اثرش هم حذف شدند.
✅ خروجی        outbox/consent برای leg لید ساخته شد؛ quote/پاسخ از درب fail-closed.
✅ تست‌ها       owner خوب؛ مسیر پارتنر با ۱۲ تست Node واقعی پوشش یافت.
```

جزئیات و ترتیب اولویت در [[HANDOFF]] بخش «لید نقاشی — شکاف‌ها» آمده.

### یادداشت‌های عملیاتی لید نقاشی
- [[docs/prompts/PAINTING-NEXT-AGENT-MEGAPROMPT-v2|مگاپرامپت عامل بعدی (نسخهٔ ۲ — Flight Deck)]]
- [[docs/prompts/PAINTING-NEXT-AGENT-MEGAPROMPT|مگاپرامپت عامل بعدی (نسخهٔ ۱)]]
- [[docs/operations/PAINTING-LEAD-PRICING-RUNBOOK|روان‌نما قیمت‌گذاری لید]]
- [[docs/operations/PAINTING-PHONE-QUOTE-CHECKLIST-v2|چک‌لیست پیشنهاد تلفنی (نسخهٔ ۲)]]
- [[docs/handoffs/2026-08-06-painting-next-agent-v2|تحویل به عامل بعدی (نسخهٔ ۲)]]
- [[docs/handoffs/2026-08-06-painting-lead-pricing-handoff|تحویل به عامل بعدی (نسخهٔ ۱)]]
- [[docs/audit/IMPLEMENTATION-GAP-MATRIX|ماتریس شکاف پیاده‌سازی]]
- [[docs/architecture/DECISION-MODEL|مدل امتیازدهی]]
- [[PORTFOLIO-TENANT-MAP|نقشهٔ پرتفوی ↔ تنانت — مرجع نام‌گذاری]]

## مینی‌اپ سبا — جراحی‌های اخیر

دو جراحی کوچک روی `web/studio.html` انجام شد ([[CHANGELOG]]):

```
جراحی ۱   چیدمان تب اول   چت‌باکس وسط/بالاتر · پنل خالی تیره حذف · دکمه‌ها مرتب
          متن‌ها           گرم/دخترانه/غیرفنی · حذف نشت کلمهٔ RAG
          گالری           «خوش اومدی سبا» · empty-state گرم
جراحی ۲   آپلود چندتایی   رفع هنگ‌کردن · عکس بد batch را متوقف نمی‌کند
          ضربدر روی عکس   × بالای هر عکس · تأیید · فقط همان عکس حذف
```

هیچ‌کدام از کیفیت یا دیتا کم نکردند؛ بک‌اند (`node.py`/`studio_store.py`)
دست نخورد چون حذف آلبوم/عکس از قبل سالم بود.

## مینی‌اپ hypno — مدل لبهٔ سیستم

مدل «لبهٔ سیستم» (تفکیک بدن/خود/ابرموجود با فرمول‌ها) در hypno **کامل پرورش
یافت** — کد، RAG، مغز، endpoint و حافظهٔ روزانه همه وصل شدند:

```
✅ کد مدل         hypno/kernel/edge.py · ۳۲۴ خط · ۱۹ تابع · خالص stdlib
✅ متن در RAG      edge_seed.py · ۸ chunk · در citations پیدا می‌شوند
✅ مغز وصل شد     brain.py: _extract_scores + EDGE_SYSTEM_PROMPT
✅ endpoint       POST /api/edge/decision · POST /api/edge/daily · GET /api/edge/history
✅ حافظه روزانه   store.py: جدول edge_daily (upsert) + قانون سه‌روزه
✅ تست            ۶۲ تست سبز (۴۳ + ۱۹ جدید) — عدد تاریخی
```

جزئیات در [[HANDOFF]] بخش «پرورش عمیق مدل لبهٔ سیستم». طراحی کامل در
[[MEGAPROMPT-EDGE-DEEP]].
