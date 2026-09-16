---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
source: "https://en.wikipedia.org/wiki/Autopoiesis"
tags: [cellular, agent, metaphor, autopoiesis]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "https://en.wikipedia.org/wiki/Autopoiesis"
  - "http://arxiv.org/abs/2110.01831v1"
---

# نگاشتِ مفهومی: سلولِ مصنوعی → ایجنتِ نرم‌افزاری

## خلاصه یک‌پاراگرافی

**Autopoiesis** (خود-تولیدی) می‌گوید یک سیستمِ زنده شبکه‌ای از فرایندهاست که
اجزای خودش را بازتولید و مرزِ خودش را حفظ می‌کند. اختاپوس دقیقاً همین است در نرم‌افزار:
حلقه‌هایی که خودشان را ممیزی (`self_audit`)، مدل (`self_model`)، و ارتقا (`improve` +
`synthesis`) می‌کنند، درونِ مرزِ سختِ حریمِ خصوصی/بودجه. این نوت هر مفهومِ سلولی را به
تصمیمِ معماریِ *موجود* می‌بندد تا استعاره جای مکانیزم را نگیرد.

## جزئیات (مفهوم → تصمیمِ معماری)

- **مرزِ خود-نگه‌دار (membrane):** سیستم چه چیزی را بیرون نمی‌دهد؟ → `.agentignore`،
  redaction، human-append؛ تحقیقِ وب فقط موضوعِ عمومی می‌فرستد نه محتوای خصوصی.
- **خود-تولیدی (autopoiesis):** سیستم اجزای خودش را می‌سازد؟ → propose-only؛ فقط
  knobِ $0 خودکار، بقیه پروپوزال به مالک (نه بازنویسیِ آزادِ خود).
- **بستارِ عملیاتی با گشودگیِ ترمودینامیکی:** بسته در کنترل، باز در ماده/انرژی →
  کنترل درونی + ورودیِ باز (وب/تلمتری) با گیت.
- **هویت در برابرِ تغییر:** سلول با هر جهش «همان سلول» می‌ماند → invariantهای هسته
  (kill-switch، σ≤1، سقفِ بودجه، ژنومِ append-only) که خود-تغییری هرگز دور نمی‌زند.

## چرا مهم است (برای مالک)

استعاره وقتی ارزش دارد که به **تصمیم** وصل باشد نه تزئین. هر ردیفِ بالا به یک گیتِ
واقعی می‌رسد؛ اگر روزی ردیفی هیچ تصمیمی نساخت، طبق
[[06 - Architecture Maps/SPEC-OCTOPUS-2027-v0|SPEC ۲۰۲۷ §۲۱-۶]] ساده‌اش می‌کنیم.

> نگاشتِ اجراییِ کامل: [[06 - Architecture Maps/CELLULAR-MODEL-ROSETTA|Cellular Model Rosetta]] ·
> منطقِ سلولی: [[07 - Knowledge/cellular-systems/spudcell-notes|spudcell-notes]].
