---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [governance, control-plane, architecture]
created: 2026-07-16
updated: 2026-07-16
created_by: agent
sources:
  - "[[06 - Architecture Maps/TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane]] (§۷ ضمیمهٔ ۰۷-۱۶)"
  - "4d_system/docs/B6-SOG-INTEGRATION-STEP1.md (سند گام ۱ + schema منجمد)"
  - "4d_system/second-brain/agents/B6_AGENTOPS_NBB.md (منشور B6: یک choke-point، fail-closed)"
  - "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]] (دکترین coupled-not-merged)"
---

# دکترین «درختِ authority، نه درختِ فایل‌ها»

## خلاصه یک‌پاراگرافی

وقتی دو نسخه از یک سیستم (کپی پژوهشی و کپی تولیدی) آشتی داده می‌شوند، چیزی که باید هرس/کنترل شود **شاخه‌های authority** است، نه شاخه‌های فایل‌سیستم: کپی‌شدن فایل‌های یک تحلیل‌گر به داخل درخت تولیدی، به آن write authority نمی‌دهد؛ و جدا ماندن فایل‌ها هم به‌تنهایی ایمنی نمی‌آورد. مرز واقعی جایی است که policy/gate/flag تعیین می‌کند چه کسی حق mutation، kill، self-heal، خرج بودجه، دسترسی secret یا نوشتن مستقیم در ledger را دارد. (تعمیم رأی فوگو در ادغام 4D، ۲۰۲۶-۰۷-۱۶.)

## جزئیات

- **مصداق عینی:** هم‌سطح‌سازی C→F در `4d_system` (کامیت `5a69f2c`) فایل‌های مغز پژوهشی را داخل درخت تولیدی آورد، ولی هیچ authority جدیدی نداد — همهٔ flagهای اجرایی default-OFF ماندند و نقش B6 «فقط‌خواندنی، propose-only» تعریف شد (schema منجمد `b6.sog.proposal.v1` با `authority: propose-only` سخت‌کد).
- **قاعدهٔ عملی برای هر ادغام آینده:** قبل از پرسیدن «کدام فایل‌ها کپی شوند؟» بپرس «کدام مسیرهای عمل (action paths) باز می‌شوند؟». اگر پاسخ «هیچ» است، ادغام additive و کم‌ریسک است حتی با صدها فایل؛ اگر حتی یک مسیر عمل باز می‌شود، همان یک مورد رأی مالک می‌خواهد.
- **هم‌نشینی با [[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged|ADR-001]]:** هم‌مکانیِ فایل ≠ merge شدنِ پلین‌ها. دو پلین می‌توانند در یک پوشه زندگی کنند و همچنان coupled-not-merged بمانند، مادامی که سنجش بیرونِ عمل بماند و interface فقط envelope بدهد.
- **زنجیرهٔ مهار استاندارد (از تحلیل فوگو):** snapshot فقط‌خواندنی → proposal امضادار/نسخه‌دار (`model-version`/`anchor-hash`/`idempotency-key`) → Bus → ‏Gates deny-by-default → verdict انسانی (تلگرام) → ledger فقط‌افزودنی. نشتِ authority از «تحلیل» به «عمل» = ریسک شمارهٔ یک هر ادغام.
