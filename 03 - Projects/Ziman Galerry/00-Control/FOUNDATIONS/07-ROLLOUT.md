# ۰۷ — راه‌اندازیِ تدریجی (P0 تا P7)

هر فاز افزایشی است، پشتِ یک فلگِ `OCTOPUS_WIRE_ZIMAN_*` (پیش‌فرض خاموش). **حذفِ فلگ = بازگشتِ
کاملِ رفتار به قبل** (rollback در یک خط). ترتیب رعایت شود؛ هر فاز روی فازِ قبلی می‌نشیند.

| فاز | چه می‌سازد | فلگ/دروازه | rollback |
|---|---|---|---|
| **P0** سطحِ مالک + مدلِ خود | `GOALS-ZIMAN.md` + `ziman-self.yaml` (وزن‌ها/آستانه/سقف)؛ `ziman_self_model.py` (فقط‌خواندنی، $0). افزودنِ هر دو به allowlistِ پا. | پشتِ `OCTOPUS_WIRE_ZIMAN` موجود؛ فلگ‌خاموش = tick بایت‌به‌بایت مثلِ امروز؛ صفر عددِ جعلی | حذفِ فایل‌ها/فلگ |
| **P1** ماتریسِ واحد | `ziman_matrix.py`: پیش‌فیلترِ امکان‌سنجی + سیگنال‌های ۰..۱ + میرایی + argmax/SURFACE_T. `tick` بلوکِ `ziman.beat.v1` با candidates+top+reasons. + حذفِ تعریفِ مردهٔ `ziman_beat` | `OCTOPUS_WIRE_ZIMAN_MATRIX` (خاموش)؛ کران ۰..۱؛ HARD_GATED حذف | خاموشیِ فلگ |
| **P2** تپ‌ها + کارتِ آره/نهِ گیت‌شده | تلگرام `/focus /pause /resume /more /mute /status /me /goal /next` از **یک** بات (chat_id مالک) که فقط `steering.json` می‌نویسد؛ پیشنهادِ content-free → یک کارتِ آره/نه در governance | `OCTOPUS_WIRE_ZIMAN_STEER` + `OCTOPUS_WIRE_ZIMAN_EMIT`؛ تپ هرگز decision نمی‌سازد | خاموشیِ فلگ‌ها |
| **P3** جذبِ مشتری (ستونِ فقراتِ CRM) | `leads.py` + `data/leads.jsonl` (PII محلی، gitignored) قیفِ cold→won؛ `/lead_add /leads`؛ `cac_engine` نامزدِ تماس به ماتریس (نزدیکیِ مناسبت/سگمنت/consent/frequency) | `OCTOPUS_WIRE_ZIMAN_CAC`؛ PII هرگز واردِ prompt (گاردِ کد + تست) | خاموشیِ فلگ |
| **P4** بازاریابی + حلقهٔ بازخورد | `calendar.py` + `occasions.yaml`؛ `feedback.py` (`feedback_event.v1`) + وزنِ قالب/کانال؛ پوششِ `content.generate_*` با قواعدِ برند + `anti_misread` | `OCTOPUS_WIRE_ZIMAN_MARKETING`؛ `anti_misread` وتوی ادعای جعلی | خاموشیِ فلگ |
| **P5** هوشِ بازارِ اخلاقی | `ziman_market.py` + `MARKET-SOURCES.md`؛ P5a حالتِ چسباندنِ مالک (صفر egress)، P5b استفادهٔ مجدد از `web_research.py` ($۰، بی‌کلید)؛ انتزاعِ به‌بیانِ‌خود (≥K شاهد) | `OCTOPUS_WIRE_ZIMAN_MARKET` (خاموش = صفر egress)؛ قاعدهٔ به‌بیانِ‌خود/بی‌کپی | خاموشیِ فلگ |
| **P6** سیمکشیِ فروشِ واقعی + مرورِ حلقه‌بسته | فرمانِ owner-onlyِ `/sale` **و** `reconcile.py`ِ CSV هر دو یک `evt.v1 sale:confirmed` می‌نویسند؛ `validation_progress_pct`؛ نمای «هر پیشنهاد چه هدفی را خدمت کرد» | CONFIRMED فقط با `/sale`ِ مالک یا شغلِ reconcile، هرگز ایجنت (تست تضمین) | خاموشیِ فلگ |
| **P7** بازکردنِ پس از اعتبارسنجی | مدلِ خود یک *پیشنهاد* برای باریک‌کردنِ shadow به‌ازای هر طبقهٔ اکشن می‌دهد. **هیچ اجرای خودکاری معرفی نمی‌شود.** | ۱۰–۳۰ فروشِ واقعی ثبت‌شده **و** تصمیمِ صریحِ ثبت‌شدهٔ مالک (SahebZiman) | — |

## اصولِ عرضه
- **همگی پشتِ فلگ، پیش‌فرض خاموش** — مثلِ کلِ اُرگانیسم (مالک روشن می‌کند).
- **هر فاز با تست سبز**؛ فلگ‌خاموش هرگز رفتارِ قبلی را نمی‌شکند (تستِ هم‌ارزی).
- **یک نام‌فضای فلگ**: همه `OCTOPUS_WIRE_ZIMAN_*` (نه نام‌های پراکنده — رجوع `08`).
- **بدونِ خرجِ زنده تا P6**؛ مسیرِ ترجیحی همیشه محلیِ رایگان.

## کجاییم الان
P0 عملاً شروع شده: `GOALS-ZIMAN.md` نوشته شد، و اتصالِ پایه (`octopus_bridge` + گاردِ
`_under_octopus`) از دورِ قبل هست. قدمِ بعدیِ کد = ساختِ `ziman_self_model.py` و `ziman-self.yaml`
(P0)، سپس `ziman_matrix.py` (P1) — هر دو پشتِ فلگِ خاموش، با تستِ هم‌ارزی. **این‌ها هنوز کد
نیستند؛ این سند طراحیِ آن‌هاست** (طبقِ خواستهٔ «طراحی و بنویس»).
