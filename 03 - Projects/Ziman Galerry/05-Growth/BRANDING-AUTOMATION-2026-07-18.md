---
type: report
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: active
created: 2026-07-18
updated: 2026-07-18
created_by: agent
sources:
  - "[[03 - Projects/Ziman Galerry/PROJECT]]"
  - "[[03 - Projects/Ziman Galerry/10-Interfaces/BIOLOGY-CONTRACT]]"
tags: [ziman, branding, llm, automation]
aliases: ["اتوماتیک‌سازی برندینگ زیمان", "Fugu branding wiring"]
---

# برندینگِ خودکارِ زیمان — وصلِ مغزِ مشترک (Fugu) به پای زنده

## چه شد (2026-07-18)

پیش از این، پای زندهٔ ارگانیسم فقط status گزارش می‌داد و مولدِ واقعیِ برند (`ziman-agent/content.py`) یک CLI جدا و خاموش بود؛ **Fugu از هیچ نقطهٔ زیمان قابل‌دسترس نبود**. حالا پای زنده به مغزِ مشترکِ ارگانیسم (`_ops/cortex/model_router.py`: محلی‌اول → GLM → **Fugu**) وصل شد.

- **کجا:** `_ops/legs/ziman_leg.py` (`_llm_brand_body` + `draft_content(use_llm=…)`) و `_ops/wiring.py` (`ziman_beat`).
- **چطور کار می‌کند:** پشتِ پرچمِ `OCTOPUS_ZIMAN_BRANDING` (پیش‌فرض خاموش)، پای زنده **روزی یک‌بار** (کادنسِ `_ZIMAN_BRANDING_EVERY_N`=۱۴۴۰ بیت ≈ ۲۴h) یک کپشنِ برند از مغز می‌سازد و به‌صورتِ **proposal** emit می‌کند؛ `route_leg_proposals` (که همین حالا در `organism.py` هست) آن را خودکار به کارتِ advisoryِ تلگرام تبدیل می‌کند.
- **مرزها دست‌نخورده:** propose-only، هیچ publish/send/spend؛ `draft_only:True`, `publish:False`. کلِ برندینگ فقط draftِ human-gated است — قیمت عمومی همچنان فقط با verdict آری (ZIM-V5).
- **fail-soft:** خطا/خاموشی/جوابِ پوچِ مغز → همان قالبِ قطعیِ امروز (byte-identical). پرچمِ خاموش → خروجی byte-identical با پیش از این تغییر.
- **اقتصادِ مغز ($0 اول):** tierِ پیش‌فرض `draft` = محلیِ رایگان (qwen)؛ فقط اگر کیفیتِ محلی رد شود و گیتِ پولی باز باشد، router به ردهٔ پولی می‌رود و **Fugu را اول امتحان می‌کند** (key-aware). با `ZIMAN_BRANDING_TIER=deep` می‌توان مستقیم Fugu را برای یک بارِ کیفیتِ بالا خواست. این با سیاستِ مالک (روزمره محلی $0، Fugu برای لحظاتِ مهم) هم‌خط است.
- **اثباتِ زنده:** با برداشتنِ STOP، `draft_content(use_llm=True)` مغزِ محلی را صدا زد و `body_source: llm:local` با متنِ واقعی برگرداند. کیفیتِ qwen 1.5b متوسط است (مدلِ کوچک)؛ کیفیتِ خوب با کلیدِ Fugu می‌آید.

## تست
`_ops/tests/test_ziman_branding.py` — ۱۰ تست سبز (LLM body، fail-soft به قالب، byte-identical flag-off، hard-gate روی publish، نشتِ عدد = پرچمِ بازبینی نه بلاک، beat خاموش=صفر proposal، beat روشن=دقیقاً یک draft). رگرسیون: ۵۷ تستِ موجودِ زیمان + ۴۳ تستِ wiring/leg سبز.

## فعال‌سازی — فقط مالک

1. **حداقلی ($0، بدونِ Fugu):** در `_ops/OCTOPUS-flags.cmd` اضافه کن `set OCTOPUS_ZIMAN_BRANDING=1` → restart ارگانیسم (♻️). از فردا روزی یک کارتِ draftِ برندِ محلیِ رایگان در تلگرام می‌آید.
2. **با Fugu (کیفیتِ بالا):** علاوه بر بالا، گیتِ پولیِ کورتکس را باز کن — `FUGU_API_KEY` در env + فایلِ `ACTIVATION-CORTEX-PAID.flag` (فقط مالک). اختیاری `set ZIMAN_BRANDING_TIER=deep` برای اینکه هر draft مستقیم از Fugu بیاید.
3. **تنظیمِ ریتم (اختیاری):** `CHRONO_ZIMAN_BRANDING_EVERY_N_BEATS` را کم/زیاد کن (کوچک‌تر = مکررتر).

## خاموش‌کردن
`OCTOPUS_ZIMAN_BRANDING=0` (یا حذفِ خط) + restart → دقیقاً رفتارِ قبل. STOP-ORGANISM هم مثلِ همیشه کلِ مغز (حتی محلی) را می‌بندد.

## نکتهٔ صادق
کیفیتِ برندِ خودکار به مدل بستگی دارد: qwenِ محلی برای پیش‌نویسِ خام کافی است ولی صیقلی نیست؛ Fugu کیفیتِ فروش‌محورِ واقعی می‌دهد ولی هزینه/لتنسی دارد. چون همه‌چیز propose-only است، هر کارت پیش از هر استفاده از چشمِ تو می‌گذرد.
