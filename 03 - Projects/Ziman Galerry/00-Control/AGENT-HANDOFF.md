# 🧭 AGENT-HANDOFF — از این‌جا شروع کن (ایجنتِ بعدیِ زیمان)

> **این سند اول خوانده شود.** حالتِ کاملِ پروژه، آنچه ساخته/طراحی/مانده، قواعدِ سخت، و
> «چطور ادامه بده». هیچ حافظهٔ نشستِ قبلی لازم نیست — همه‌چیز این‌جاست.
> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۷.

## ۰) ترتیبِ خواندن
1. همین سند (حالت + قواعد + ادامه). 2. [ROADMAP-NEXT-10-STEPS](ROADMAP-NEXT-10-STEPS.md)
(کجاییم/بعدی چیست). 3. [FOUNDATIONS/00-OVERVIEW](FOUNDATIONS/00-OVERVIEW.md) (طراحیِ کامل).
4. [MARKET-RESEARCH-COMPETITORS](MARKET-RESEARCH-COMPETITORS.md). 5. [VERDICT_QUEUE](../VERDICT_QUEUE.md)
(تصمیم‌های بازِ مالک).

---

## ۱) پروژه چیست
**Ziman Galerry** — کسب‌وکارِ هدایای دست‌سازِ سیدنی (بنیان‌گذارانِ فارسی‌زبان: آری + مادرش).
محصولات: **F1** گل‌آراییِ مصنوعی (۱۸) · **F2** قابِ گلِ شادوباکس (۲) · **F3** سبدِ آب‌نبات (۴)
· **F4** همپرِ ترکیبی (۱۱) = ۳۵ محصولِ عکس‌محور. همهٔ F4 تحویلِ محلی؛ ۷ موردِ الکل‌دار.
مرحله: **اعتبارسنجی، صفر فروشِ ثبت‌شده.** بازارِ گرم اول (جامعهٔ ایرانیِ سیدنی). PayID،
تحویلِ محلیِ سیدنی. سقفِ خرجِ هوش = **AU$15/ماه (fail-closed)**.

## ۲) قواعدِ سخت (نقض = خرابیِ طراحی) 🔒
- **propose-only**: هیچ‌چیز خودکار منتشر/ارسال/DM/خرج نمی‌شود. سیستم *پیش‌نویس و پیشنهاد*
  می‌دهد؛ مالک تأیید می‌کند (**RED = فقط owner/SahebZiman**)؛ و حتی پس از تأیید، `ShadowGate`
  اجرا را قفل نگه می‌دارد تا ۱۰–۳۰ فروشِ واقعی **و** خاموش‌کردنِ صریحِ shadow توسطِ مالک.
- **NC-3**: هیچ نقشِ ایجنتی (از جمله OCTOPUS) هرگز approve نمی‌کند.
- **بدونِ عددِ جعلی**: ظرفیتِ «۳۰/هفته» تأییدنشده است (CONFLICT) → هرگز عمومی نشود؛ سقفِ مؤثر
  ≤۶. قیمت‌ها null تا COGS/**ZIM-V5**. موجودی شفاهی (OWNER_INPUT)، نه شمرده.
- **امنیتِ اعتبارنامه**: ایجنت هرگز لاگین/حساب‌سازی/ورودِ رمز نمی‌کند. اتصالِ اجتماعی فقط با
  توکنِ رسمیِ مالک‌تأمین.
- **حریمِ خصوصی**: PII محلی می‌ماند؛ هرگز در git/دایجست/promptِ LLM.
- **اخلاق**: بی‌اسپم، بی‌گواهیِ جعلی، صداقتِ گلِ مصنوعی، بی‌کپیِ طراحی/متنِ رقبا.
- **افزایشی / بهبود نه بازنویسی**؛ **تراز‌تیرِ حقیقت** روی هر ادعا (VERIFIED/OWNER_INPUT/
  MEASURED/ESTIMATE/CONFLICT).
- **کارهایی که بدونِ تأییدِ صریحِ مالک نکن**: تنظیمِ توکن/chat_id، شروعِ pollingِ زنده، خرجِ
  زنده یا بالابردنِ سقف، انتشار/ارسال، قیمتِ عمومی، تبدیلِ proposal به اجرا، دست‌زدن به بخش‌های
  غیر-زیمانِ اُرگانیسمِ `_ops`.

## ۳) حالتِ فعلی — ساخته / طراحی / مانده
### ✅ ساخته و تست‌شده (کد)
- **control-brain/** (مغزِ حاکمیت/فرایند): governance (نردبانِ RED)، دفترِ evt.v1 (hash-chain +
  ULID + ZIM-DEC id)، shadow gate، رجیستریِ فرمان، RBAC (authz)، داشبوردِ فقط‌خواندنی،
  `octopus_bridge`. **تست: 76/76.**
- **ziman-agent/** (لایهٔ محتوا/محصول): `catalog_loader` (۳۵ محصول)، `content.py` (تولیدِ
  draftِ فارسی، مسیرِ hybrid Ollama→API→offline)، `budget.py` (سقفِ AU$15 fail-closed)،
  `product.py` (کارت/ATP/گاردِ D4/anti-misread)، `telegram_adapter`، و **گامِ ۱ (P0)**:
  `steering.py` + `self_model.py` + `ziman-self.yaml`. **تست: 57/57** (شاملِ رگرسیونِ CF-01 در `tests/test_content.py`).
- **اتصالِ اختاپوس**: `_ops/legs/ziman_leg.py` (پا)، دایجستِ غنی از پل پشتِ فلگ. **تستِ
  leg/wiring/biology: 43 سبز** (۱ شکستِ **پیش‌از-ما** `test_ziman_beat_biology_accepts_doctor_
  injection` — با git stash ثابت شد مالِ ما نیست).

### 📐 طراحی‌شده (سند، هنوز کد نه) → `00-Control/FOUNDATIONS/`
مدلِ خود، ماتریسِ شفاف، قراردادِ ضربان، مدلِ داده، هدایتِ مالک، حاکمیت/ایمنی، rollout،
دو-سطح (ادمین/استودیو)، خطِ لولهٔ تولید، اتصالِ اجتماعی، جذبِ مشتری. (اسناد ۰۰–۱۳.)

### ⏳ مانده (کارِ مالک، مسدودکننده)
verdictهای بازِ مالک — بخشِ ۶ پایین.

## ۴) نقشهٔ repo و اجرای تست
```
F:\backup\03 - Projects\Ziman Galerry\
  00-Control\        ← اسنادِ حاکمیت/طراحی (این‌جا) + FOUNDATIONS\ + command-registry.yaml
  03-Offering\       ← CATALOG.md + ziman-catalog.json + Photos\ (۴۱ JPG)
  control-brain\     ← core\{governance,store,shadow,authz,command_registry,manager,...}
                       adapters\{telegram_bot,dashboard,octopus_bridge}  app.py  config\
  ziman-agent\       ← ziman\{catalog_loader,content,budget,product,steering,self_model,
                       llm_router,telegram_adapter,command_registry}  ziman.yaml  ziman-self.yaml
F:\backup\_ops\      ← اُرگانیسمِ اختاپوس (زنده) · legs\ziman_leg.py · wiring.py · GOALS-OCTOPUS.md
```
اجرای تست:
```
cd control-brain && python -m pytest -q            # 76 passed
cd ziman-agent   && python -m pytest -q            # 50 passed
cd _ops && python -m pytest tests/test_ziman_leg.py tests/test_ziman_wiring.py tests/test_ziman_biology.py -q
```
> نکات: PowerShell 5.1 فارسی را با UTF-8 بخوان؛ برای چاپِ فارسی در python از
> `PYTHONIOENCODING=utf-8` استفاده کن. تست‌ها flat import می‌کنند (ziman/ روی sys.path).

## ۵) اتصالِ اختاپوس (coupled-not-merged، ADR-001)
زیمان یک **پا** زیرِ اُرگانیسمِ زندهٔ `_ops` است؛ هر ضربان `wiring.ziman_beat` آن را tick می‌کند.
مغزِ غنیِ من از `control-brain/adapters/octopus_bridge.py` به دایجستِ پا می‌رسد. فلگ‌ها (همه
پیش‌فرض خاموش مگر paper-full):
- `OCTOPUS_WIRE_ZIMAN` — پا فعال (در paper-full روشن).
- `OCTOPUS_WIRE_ZIMAN_RICH` — دایجستِ غنیِ control-brain به تلگرامِ مرکزی.
- `ZIMAN_UNDER_OCTOPUS` — control-brain باتِ *جدای* خودش را بالا نمی‌آورد (ضدِ تصادمِ 409).
- `OCTOPUS_WIRE_ZIMAN_MATRIX` — (گامِ ۲، هنوز ساخته نشده) بلوکِ `ziman.beat.v1` در tick.
- `OCTOPUS_WIRE_ZIMAN_STUDIO/_MARKETING/_CAC/_PUBLISH` — گام‌های بعدی.
**قاعده**: هر تغییرِ `_ops` فقط برای اتصالِ زیمان و flag-gated؛ به بخش‌های دیگرِ اُرگانیسم دست نزن.

## ۶) verdictهای مسدودکنندهٔ مالک (تا این‌ها بسته نشوند، بعضی گام‌ها قفل‌اند)
- **ZIM-V5**: قیمت/COGS (تا آن، همهٔ قیمت‌ها null).
- **CF-01**: ظرفیتِ «۳۰/هفته» تأییدنشده → مؤثر ≤۶، عمومی نشود.
- **ZIM-V8 / ZIM-V9**: سیاستِ الکلِ F4 و تحویل.
- شمارشِ رسمیِ موجودی (فعلاً شفاهیِ ۵۰).
- **وجود/دسترسیِ مسئولِ تولید** (کلِ سطحِ دومِ UI به این وابسته است).
- **P7 (خروج از shadow)**: فقط با ۱۰–۳۰ فروشِ واقعیِ ثبت‌شده + تصمیمِ صریحِ مالک.
صفِ canonical: [VERDICT_QUEUE.md](../VERDICT_QUEUE.md).

## ۷) کجاییم و بعدی چیست (نقشهٔ ۱۰-مرحله‌ای)
- **گامِ ۰** (آشتیِ حقیقت): verdictهای مالک باز + ✅ اصلاحِ نشتِ «۳۰/هفته» در `content.py` انجام شد
  (۲۰۲۶-۰۷-۱۷ — هر ۴ نقطه + تستِ رگرسیون؛ گزارش: `11-Reports/Handoffs/CONTENT-CAPACITY-LEAK-FIX-2026-07-17.md`).
- **گامِ ۱ (P0): ✅ ساخته شد** — `steering.py` + `self_model.py` + `ziman-self.yaml` (فقط‌خواندنی،
  هنوز به tick سیم‌کشی نشده → رفتارِ ضربان بایت‌به‌بایتِ قبل).
- **گامِ ۲ (P1): ⬅️ بعدی** — `ziman_matrix.py`: پیش‌فیلترِ fail-closed + ۶ سیگنالِ ۰..۱ (وزن‌ها
  از `ziman-self.yaml`) + میرایی + `SURFACE_T`؛ افزودنِ بلوکِ `ziman.beat.v1` به `ziman_leg.tick()`
  **پشتِ `OCTOPUS_WIRE_ZIMAN_MATRIX` (خاموش)، با تستِ هم‌ارزیِ فلگ‌خاموش**. طراحیِ کامل:
  [FOUNDATIONS/02-CALCULATION-MATRIX](FOUNDATIONS/02-CALCULATION-MATRIX.md) +
  [03-HEARTBEAT-CONTRACT](FOUNDATIONS/03-HEARTBEAT-CONTRACT.md).
- گام‌های ۳–۱۰: تلگرامِ ادمین → producer/استودیو → پستِ کاتالوگ‌آگاه → کمپینِ مناسبتی/قیف →
  اتصالِ تلگرام → فروشِ واقعی → بازکردنِ کنترل‌شده. جزئیات در ROADMAP.

## ۸) فهرستِ اسنادِ canonical (همه در vault، برای Obsidian)
- `00-Control/AGENT-HANDOFF.md` (این) · `ROADMAP-NEXT-10-STEPS.md` · `MARKET-RESEARCH-COMPETITORS.md`
- `00-Control/FOUNDATIONS/` (۰۰–۱۳ + `GOALS-ZIMAN.md`) · `command-registry.yaml`
- `00-Control/ZIMAN-DESIGN-RECONCILIATION.md` (طراحیِ حاکمیتِ اولیه، معتبر) · `_DESIGN-INDEX-2026-07-12.md`
- `03-Offering/CATALOG.md` + `ziman-catalog.json` · ریشه: `VERDICT_QUEUE.md`

## ۹) دستورالعملِ ادامه برای ایجنتِ بعدی
1. این سند + ROADMAP + FOUNDATIONS را بخوان. 2. قواعدِ سختِ بخشِ ۲ را نقض نکن. 3. تست‌ها را
اجرا کن تا خطِ پایه سبز باشد. 4. اگر مالک نگفت از کجا، **گامِ ۲ (ماتریس)** مسیرِ درست است —
افزایشی، پشتِ فلگِ خاموش، با تست، صفر regression؛ به `_ops` فقط برای سیم‌کشیِ tickِ زیمان دست بزن.
5. هر عددِ جدید را با تراز‌تیر برچسب بزن؛ چیزی جعل نکن. 6. کارِ مهم را همین‌جا (vault) ثبت کن تا
ایجنتِ بعد هم بداند.
