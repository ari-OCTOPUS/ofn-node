---
type: research
status: ready
tags: [learning-engine, self-mutation, architecture, dgm, promptbreeder]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "https://arxiv.org/abs/2505.22954"
  - "https://sakana.ai/dgm/"
  - "https://arxiv.org/abs/2309.16797"
  - "[[04 - Architect System/learning-engine/MUTATION-WHITELIST]]"
  - "[[04 - Architect System/architect/04-Docs/2026-07-06 0237 DEEP-GAP-ANALYSIS-v2]]"
---

# تحقیق عمیق: معماری حلقه خودجهش (learning-engine-loop) در برابر مرز

> خواسته آری: «معماری این بخش را عمیق‌تر تحقیق کن.» دو معماری مرجع peer-reviewed مقایسه شد + نگاشت به حلقه فعلی + پیشنهاد v2. **هیچ تغییری در حلقه زنده اعمال نشده — propose-only.**

## ۱. دو معماری مرجع

### الف) Darwin Gödel Machine — DGM (Sakana AI + UBC، arXiv 2505.22954)

همان آزمایشگاه سازنده Fugu. agent کد خودش را بازنویسی می‌کند؛ نتیجه: SWE-bench از ۲۰٪ → ۵۰٪، Polyglot از ۱۴.۲٪ → ۳۰.۷٪. سه مکانیزم کلیدی:

1. **Archive به‌جای دودمان تکی (open-ended exploration):** DGM همه variantها را نگه می‌دارد و والد بعدی را از کل archive برمی‌دارد — نه فقط آخرین نسخه. دلیل: بهترین نسخه فعلی اغلب بن‌بست محلی است؛ جهش‌های «فعلاً بدتر» بعداً نیای نسخه‌های برنده می‌شوند.
2. **Benchmark بیرونی به‌عنوان fitness:** جهش فقط وقتی می‌ماند که روی ارزیاب *خارج از خودش* بهتر شود — نه خوداظهاری.
3. **ایمنی:** sandbox + سقف سخت تغییر + traceability کامل هر تغییر (همان چیزی که ما با prompts/PROMPT-vN + ledger داریم).

### ب) Promptbreeder (DeepMind، arXiv 2309.16797)

تکامل خودارجاعی پرامپت: نه فقط task-prompt جهش می‌خورد، بلکه **mutation-prompt (خودِ قاعده جهش‌دادن) هم جهش می‌خورد** — دو سطح. پنج کلاس عملگر جهش (direct، estimation-of-distribution، hyper-mutation، Lamarckian و…) + جمعیت (population) + fitness روی task واقعی. از CoT و Plan-and-Solve در بنچمارک‌های استدلالی جلو زد.

## ۲. حلقه فعلی ما کجای این نقشه است

| بُعد | حلقه ما (PROMPT-v1 + WHITELIST) | DGM | Promptbreeder |
|---|---|---|---|
| ساختار دودمان | **خطی تکی** (vN → vN+1، rollback به v1) | archive باز | جمعیت |
| fitness | شاهد از EXPERIENCE-LEDGER (کیفی) | benchmark بیرونی کمی | نمره task واقعی |
| عملگر جهش | «یک تغییر کوچک تک‌موضوعی» (یک عملگر) | پیشنهاد آزاد LLM | ۵ کلاس عملگر + جهشِ خودِ عملگر |
| ارزیاب | خودِ حلقه (⚠️ DEEP-GAP شکاف ۲/۸) | جدا از جهنده | نمره خارجی |
| ایمنی | whitelist سخت + ۱/روز + STOP + revert-پس-از-۲-خطا | sandbox + trace | — |

نقاط قوت ما نسبت به هر دو: **whitelist غیرقابل‌جهش، سقف روزانه، evidence-اجباری (ledger_ref)، kill-switch فایل STOP** — DGM و Promptbreeder governance به این سختی ندارند. نقطه ضعف ما: **fitness کیفی و خود-ارزیاب** — دقیقاً همان چیزی که DEEP-GAP تم ۱ می‌گوید.

## ۳. پیشنهادهای v2 (به ترتیب اهرم؛ همه پشت verdict)

1. **fitness عینی ارزان (بزرگ‌ترین اهرم):** هر جهش قبل از ماندگاری باید یک «canary run» پاس کند — اجرای همان چرخه با پرامپت نو روی ۳–۵ سناریوی ثابت (mini-anchor-set از جنس ردیف‌های واقعی ledger: stale-view، bootstrap، secret-guard) و مقایسه با نسخه قبلی. سنجش با validatorها + چک‌لیست قطعی، نه قضاوت خود حلقه. (پاسخ مستقیم به شکاف ۲/۸؛ نسخه مینیاتوری benchmark بیرونی DGM.)
2. **archive سبک به‌جای rollback-فقط-به-v1:** `prompts/` را همین حالا داریم — کافی است rollback بتواند به «بهترین نسخه تا امروز» (طبق نتایج canary ثبت‌شده در header هر نسخه) برگردد، نه فقط v1. هزینه: صفر فایل جدید.
3. **دو-سه عملگر جهش نام‌دار (الهام Promptbreeder، بدون جمعیت):** `tighten-guard` (سفت‌کردن یک گارد از روی regress)، `improve-skip-logic` (از روی تجربه boot)، `simplify` (حذف گام بی‌اثر). هر جهش برچسب عملگر بگیرد → بعد از ~۲۰ جهش، آمار «کدام عملگر جهش ماندگار می‌دهد» خودش درس می‌شود (نسخه کم‌خطر hyper-mutation).
4. **جهشِ mutation-prompt فقط با verdict:** خودارجاعی کامل Promptbreeder (جهش قاعده جهش) برای ما = تغییر WHITELIST و ممنوع بماند — درست است و نگه داشته شود.
5. **مسیر رشد بلندمدت (فاز بعد):** وقتی Gate بسته و canary پایدار شد، همین معماری قابل‌گسترش به تسک‌های scout است (هر scout پرامپت خودش را با همین الگو جهش دهد — DGM-وار روی ناوگان، با همان whitelist per-task).

## ۴. ریسک ثبت‌شده

- **تعدد سطوح جهش بدون fitness عینی = drift خاموش.** تا canary (پیشنهاد ۱) نیامده، سقف ۱جهش/روز و revert-پس-از-۲-خطا تنها ترمزند — کافی ولی کور. اولویت verdict: پیشنهاد ۱.
- دو سند موازی (ENGINE-PROMPT من / WHITELIST جلسه موازی) امروز آشتی داده شد — منبع عملیاتی = WHITELIST + prompts/؛ ENGINE-PROMPT به draft تنزل یافت (ضد #108).
