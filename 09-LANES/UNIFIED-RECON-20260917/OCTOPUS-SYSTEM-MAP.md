# OCTOPUS-SYSTEM-MAP — نقشهٔ یکپارچهٔ چهار repo + والت + runtime
# mission: OCTOPUS-UNIFIED-RECON-AND-VAULT-CANONICALIZATION-20260917 · 2026-09-17 AEST

> خواندن این نقشه جایگزین منابع نیست؛ هر ادعا به `OCTOPUS-SYSTEM-GRAPH.json` رجوع می‌دهد که شاهد هر یال را دارد.

## تصویر کلی در یک نگاه

```text
                    owner (GOV-V7 locks + V8 ladder, L2)
                              │  TG + رسید
              ┌───────────────┼───────────────────┐
              ▼               ▼                   ▼
        F:\backup  ←──parallel/divergent──►  ofn-node (main dba9971)
        (canonical vault)   187 مسیر: 180 غایب، 7 متفاوت   │
              │                                        ├──► board138: fleet زنده (timers) + موتور لید نقاشی
              │                                        │      (packs/lead.yaml + web/lead.html — وصل، اثبات‌شده)
              │                                        └──► board180/182: نقش mesh/witness (این نشست بررسی نشد)
              │
      ┌───────┴─────────┬──────────────────┬─────────────────┐
      ▼                 ▼                  ▼                 ▼
   Armin (۵ فایل)   langar (۹۷ مسیر)   vbaa-patches (۳۱)   01-TRUTH + OCTOPUS/ auto-surfaces
   سند مفهومی        dormant-deployable  review substrate   (نقش‌های ثانویهٔ حقیقت)
   idea-only         بدون سرویس زنده     بدون adoption      در والت
```

## پنج حکم معماری (هر کدام با شاهد)

1. **بدنهٔ اصلی = ofn-node.** ۳۴۵۴ مسیر tracked، fleet روی 138 زنده (۱۱+ timer در دقیقه‌های اخیر)، موتور نقاشی در tree و روی host.
2. **Armin سند است، نه محصول.** ۵ فایل: دو ممیزی، نقشهٔ heart-awareness، سند پیدایش LANGAR، evidence json. توضیح repo («Painting lead generation») نقش را بیش‌برآورد می‌کند — متن merge شده خودش می‌گوید «not the live engine».
3. **langar ایزوله و خفته است.** صفر import از ofn (دو طرف)، صفر سرویس روی 138 (زنده بررسی شد)، فایل service در repo هست ولی نصب نیست. money path دست نمی‌زند. `_verify/` کپی سایه دارد و یک آرتیفکت `.fuse_hidden` در git track شده.
4. **vbaa-patches فقط بستر review است.** تست‌ها سبز (۲۳+۱xf+۲xp) ولی هیچ مسیر/import/رسیدی آن را به ofn-node/main وصل نمی‌کند — `GAP` قرارداد انتقال ثبت شد، ساخته نشد.
5. **repo و والت دو بدنهٔ موازی‌اند، نه آینه.** ۱۸۷ مسیر ساختار-والت داخل ofn-node: ۱۸۰ در والتِ همان‌مسیر غایب، ۷ موجود همگی متفاوت. canonical هر artifact باید صریح انتخاب شود (رجیستری نوشته شد).

## حقیقت روی board138 (فقط‌خواندنی، 23:47Z)
- Timers فعال: autonomy-supervisor، coding-worker، budget-monitor، mesh-consume، experience-ingest، go-b3-bind، eti-telemetry، reply-alert، owner-reply، bridge-watchdog، quote.
- WAL زندهٔ PAINT (`outbound-effects.sqlite3`): هنوز **۰ بایت** — تنها شاهد ۵ ارسالِ تاریخی، بکاپ ۰۹-۰۱ است.

## نقطه‌های درد (لینک به کارت‌های تصمیم)
- **PR#71**: blocked؛ ۸ approve تاریخ\Validation‌شده-dismissed؛ تناقض PAINT-L5-001 در متن خود PR. → کارت ۱
- **CRM دوگانگی** #248/#261 (writer در برابر جدول، بدون PR اتصال). → کارت ۲
- **۱۲ نسخهٔ CURRENT-TRUTH** (۱ canonical + ۱ auto-surface + ۱ نقش-نامعلوم + ۹ استاب). → کارت ۳
- **۱۶۳ شاخهٔ بدون حفاظت** (ruleset فقط main). → کارت ۴
- **۲ alert باز secret-scanning** (telegram_bot_token، دیروز جریان push). → کارت ۵
- بدنهٔ موازی repo↔vault (۷ فایل same-path متفاوت). → کارت ۶
- `_verify` در langar + `.fuse_hidden` tracked. → کارت ۷
