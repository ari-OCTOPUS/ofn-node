---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, glm, base-map, mapper, handoff]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# GLM-MAPPER PROMPT-SET — نقشه‌کشیِ Base-Map با GLM Max

> **تقسیمِ کار:** Claude = معمار (این ساختار + قیدها را طراحی کرد). **GLM Max = دستِ اجرا** (می‌گردد، مرتب می‌کند، Mermaid/گزارش می‌نویسد). GLM به دایرکتوریِ vault دسترسی دارد → مسیرها را خودش می‌خواند. هیچ فایلِ اصلی را overwrite نمی‌کند؛ فقط **PROPOSAL** می‌دهد.

---

## نحوهٔ اجرا (ترتیب و قواعد — برای آری)

۱. هر بلاکِ زیر یک **پرامپتِ جدا و خوداتکا** است. §۰ را همیشه **بالای** هر پرامپت بچسبان (قانونِ اساسی مشترک).
۲. ترتیب: **§۱ (recon)** اول → بعد §۲..§۵ (می‌توانند موازی) → آخر **§۶ (assemble+verify)**.
۳. خروجیِ هر run را GLM در `00 - Inbox/build-proposals/` می‌نویسد (کنوانسیونِ واقعیِ vault برای propose-only؛ نه روی فایلِ اصلی، نه `.git`، نه `ledger.jsonl`). ratify با توست.
۴. اگر روزِ کم‌انرژی است: فقط §۱ + §۲ را بده؛ همان اسکلتِ حداقلی است.

**گاردریلِ سراسری (در §۰ هم آمده، این‌جا برای تو):** GLM هرگز — به `.git` دست نزند · به `ledger/ledger.jsonl` مستقیم append نکند · `genome/` را تغییر ندهد · فایلِ موجود را overwrite نکند · تصمیمِ قطعی نگیرد (فقط PROPOSAL) · محتوای فایل را کپی نکند (فقط `[[wikilink]]`).

---

## §۰ — MASTER HEADER (بالای هر پرامپت بچسبان)

```
تو Agent-Mapperِ این vault (سیستمِ Octopus) هستی. مدل: GLM Max. نقش: دستِ اجرا برای معماری‌ای که از قبل طراحی شده.

منبعِ حقیقت = فایل‌های واقعیِ vault، نه فرضِ تو. مسیرهای مرجع:
- فازها و gateها: "04 - Architect System/octopus-build-prompts/00-INDEX.md"
- invariantها و فرمت‌ها: "07 - Knowledge/genome-system/STATUS.json" + "07 - Knowledge/genome-system/CHANGELOG.md" (v0.4.6)
- Ledgerِ واحد: "07 - Knowledge/genome-system/ledger/ledger.jsonl" (LANGAR؛ قانون «extend, don't rival»)
- گرهِ زندهٔ Layer 0/5: پوشه‌های ریشه‌ایِ "survival-gateway" و "CHRONOS-FABLE-OS"
- معماریِ کلی: "_ops/ORGANISM-SPEC.md"

قوانینِ قفل‌شده (نقض = خطا):
1. فقط PROPOSAL تولید کن؛ حق APPLY/اجرا/نوشتن روی فایلِ اصلی نداری.
2. خروجی‌ات را فقط در مسیرِ "_proposal/" پیشنهاد بده. به .git، ledger.jsonl و genome/ دست نزن.
3. محتوای فایل‌ها را کپی نکن؛ فقط با [[wikilink]] به آن‌ها ارجاع بده.
4. فرمتِ نقشه = Mermaid داخلِ markdown (فرمتِ باز، local-first). vendor-lock نساز.
5. یک Ledgerِ واحد است؛ ledgerِ دوم تعریف نکن. هر پروژه روی همین ledger می‌نشیند.
6. پولِ زنده هرگز auto نیست (P6، human-gated). auto-executionِ مالی ممنوع.
7. صداقتِ معرفتی: هر ادعای غیربدیهی را با [تثبیت‌شده]/[فرضیه]/[گمانه‌مهندسی] برچسب بزن؛ چیزی که از فایل درنیامد بنویس «مشخص نیست».
8. سبکِ ضدِگنبد: حداقلی بساز، از یک قدم شروع کن، node و توضیح را کوتاه نگه دار.
```

---

## §۱ — RECON / INVENTORY (گشتن، مرتب‌کردن، گزارش)

```
[§۰ را این‌جا بچسبان]

وظیفهٔ این run — فقط توصیف، هیچ تصمیمِ نو:
پوشه‌های زیر را بگرد و برای هرکدام یک گزارشِ ساختاریافته بده:
- "04 - Architect System/octopus-build-prompts/"
- "07 - Knowledge/genome-system/"
- "survival-gateway/" و "CHRONOS-FABLE-OS/"
- "_ops/"

برای هر پوشه بنویس:
1) هدفِ پوشه در یک جمله.
2) لیستِ فایل‌ها، هر کدام با شرحِ ≤۸۰ کاراکتر.
3) هرجا مفهومی به P1..P6 / ledger / survival-gateway / handoff مربوط است، با یک [[wikilink]]ِ مناسب علامت بزن.

خروجی: برای هر پوشه یک پاراگرافِ کوتاهِ هدف + یک لیستِ بولتِ فایل‌ها + یک لیستِ بولتِ پیشنهادِ wikilink. سقفِ کل: ۲ صفحه. اگر چیزی از متن معلوم نشد بنویس «مشخص نیست». هیچ معماریِ نو پیشنهاد نده.
پیشنهادِ خروجی را در "_proposal/recon-inventory.md" بگذار.
```

---

## §۲ — SPINE P1..P6 (ستون فقراتِ ورکفلو)

```
[§۰ را این‌جا بچسبان]

وظیفه: از جدولِ فازهای "00-INDEX.md" یک بلاکِ Mermaid واحد بکش که ورکفلوِ end-to-end را نشان دهد:
- شش node: P1 (Heart/Chrono) → P2 (Doctor) → P3 (Telegram) → P4 (Legs) → P5 (Stay-Alive/Coherence) → P6 (Money-Live).
- روی هر edge بینِ فازها، نامِ gateِ همان مرحله را از 00-INDEX به‌صورتِ کوتاه بگذار.
- هر node فقط یک [[wikilink]] به فایلِ فازش داشته باشد؛ توضیح نده.
- P3 (Telegram) را به‌عنوان «کانالِ human-append» علامت بزن (پیش‌نیازِ هر اثرِ برگشت‌ناپذیر).

خروجی: فقط یک بلاک Mermaid + حداکثر ۳ خط توضیح. در "_proposal/base-map-spine.md".
```

---

## §۳ — LEDGER + GATEWAY CORE (زیرساختِ مرکزی)

```
[§۰ را این‌جا بچسبان]

وظیفه: بلاکِ Mermaidِ زیرساخت را بکش:
- گرهِ [[survival-gateway]] = «Layer 0/5 (live)» (gateway + cost cap + kill-switch + audit).
- گرهِ [[07 - Knowledge/genome-system/ledger/ledger.jsonl|Ledger v0.4.6 (LANGAR)]] = منبعِ حقیقتِ واحد، در مرکز.
- اتصالِ gateway↔ledger را با edgeِ dashed و برچسبِ «pending wire» بکش (چون integration هنوز کامل نیست — این را در v1 solid می‌کنیم).
- classِ Mermaidِ "pending" با stroke-dasharray تعریف کن.

نکته: هیچ ledgerِ دومی نساز. اگر شواهدِ اتصالِ کامل در فایل‌ها دیدی، آن را [تثبیت‌شده] علامت بزن و edge را solid کن؛ وگرنه pending بماند.
خروجی: یک بلاک Mermaid + ≤۳ خط. در "_proposal/base-map-core.md".
```

---

## §۴ — LEGS / LANES (سه پا روی ورکفلو)

```
[§۰ را این‌جا بچسبان]

وظیفه: سه پا را به‌صورتِ lane/instanceِ موازی روی همان ستونِ P1..P6 نشان بده:
- [[Lead-نقاشی]] — **اولین پای زنده** (طبق گیتِ P4 در 00-INDEX: «Lead-نقاشی paper-$ CONFIRMED»). پررنگ/solid.
- [[Ziman]] و [[Project-F]] — پاهای بعدی، خاکستریِ placeholder (هنوز زنده نیستند).
- Project-F یک برچسبِ حریم داشته باشد: «فقط کد در خروجیِ cross-domain».
- هر سه از همان spineِ §۲ منشعب شوند (partial-mesh + سلسله‌مراتب، نه full-mesh).

خروجی: یک بلاک Mermaid (ترجیحاً subgraph برای هر پا) + ≤۳ خط. در "_proposal/base-map-legs.md".
```

---

## §۵ — MONEY-PATH + FUTURE HOOKS (قلاب‌های آینده، خاکستری)

```
[§۰ را این‌جا بچسبان]

وظیفه:
- money-path را با یک edgeِ dashed از P4 به P6 بکش و روی P6 «Gate: money-live (human-gated)» بزن.
- شرطِ بازشدنِ گیت را کوتاه علامت بزن: «بعد از هفتهٔ اولِ دیتا» (تصمیمِ انسانی، هنوز قفل نشده — [فرضیه]).
- قلاب‌های آینده (پاهای جدید، اتصالِ cross-project مثلِ nature-architecture) را فقط به‌صورتِ node خاکستریِ placeholder با classِ "future" بکش.
- تأکید: money فعلاً infra-only است؛ هیچ effectorِ پولِ واقعی روی نقشهٔ v0 زنده نباشد.

خروجی: یک بلاک Mermaid + ≤۳ خط. در "_proposal/base-map-money-future.md".
```

---

## §۶ — ASSEMBLE + VERIFY (سرِ هم کردن + خودآزمایی)

```
[§۰ را این‌جا بچسبان]

وظیفه: پنج بلاکِ §۲..§۵ را در یک فایلِ واحد ادغام کن → پیشنهادِ "base-map-v0.md":
- یک Mermaidِ اصلی (source of truth) شاملِ spine + core + legs + money/future.
- بالای فایل frontmatter بگذار (type: proposal, status: draft, created_by: agent).
- زیرِ دیاگرام فقط یک جدولِ کوتاهِ «فاز → wikilink → gate»، بدونِ شرحِ طولانی.

خودآزماییِ اجباری (چک‌لیست را در خروجی بنویس، هر مورد PASS/FAIL):
[ ] فقط wikilink، هیچ محتوای کپی‌شده.
[ ] survival-gateway = Layer 0/5 live، اتصالش به ledger = pending wire.
[ ] Ledger واحد است (یک node)، ledgerِ دوم نیست.
[ ] Lead-نقاشی اولین پای زنده، Ziman/Project-F خاکستری.
[ ] P3 (Telegram) به‌عنوان human-append علامت خورده.
[ ] P6 money-live = human-gated، هیچ auto-money نیست.
[ ] horizon تا P6 + قلاب‌های آیندهٔ خاکستری.

اگر هر مورد FAIL شد، خودت اصلاح کن و دوباره چک بزن. خروجی نهایی در "_proposal/base-map-v0.md". در انتها یک خط بنویس: «PROPOSAL — منتظرِ verdictِ آری».
```

---

## بدهیِ باز / سؤالِ تعلیق‌شده

- **فرضِ v0:** multi-project با ستونِ مشترکِ P1..P6 + سه پا به‌صورتِ lane (طبق روادمپ §۳). اگر تک‌پروژه‌ای می‌خواهی، §۴ را حذف کن و فقط Lead-نقاشی را روی spine بگذار.
- **اتصالِ cross-project (§۲.۱۰ روادمپ):** روی نقشه فقط «pending/خاکستری» است؛ بستنش تصمیمِ انسانیِ توست، نه کارِ GLM.

## منابع
[[04 - Architect System/octopus-build-prompts/00-INDEX|00-INDEX]] · [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG v0.4.6]] · [[07 - Knowledge/genome-system/STATUS.json|STATUS.json]] · [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] · [[04 - Architect System/octopus-build-prompts/NEXT-AGENT-ROADMAP — Octopus Base-Map & Workflow|NEXT-AGENT-ROADMAP]]
