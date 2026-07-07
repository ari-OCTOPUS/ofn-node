---
type: proposal
status: proposal            # propose-only — طراحیِ حافظه/ارزیابی. چیزی ساخته/اجرا نشد.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «برو» 2026-07-06 → پیش‌بردِ فاز ۴"
depends_on: "[[2026-07-06 PHASE3-MUSE-SPEC-proposal]] · [[2026-07-06 PENTA-PROMPT-Governor-Muse-proposal]] فاز ۴"
grounds: [learning-engine/LEARNING-CONTRACT.yaml L4_memory, ARCHITECT_CHARTER §۴/§۵, RESEARCH-GENOME-RECONCILIATION Q6, LEARNING-STATE.json budget]
tags: [phase4, memory, model-tiering, evolutionary-doctor, evaluation, propose-only]
---

# فاز ۴ — حافظه + هوشمندی + دکترِ تکاملی

> **propose-only.** سه چیز به‌هم سیم‌کشی می‌شود: حافظهٔ مشترک، استراتژیِ مدل، و دکترِ انتخاب. دکتر فقط **forward** می‌کند — هرگز اجرا. حافظه **append-only** — هرگز حذف (منشور: «حذف ممنوع»).

---

## ۱. MEMORY — حافظهٔ مشترک (append-only، بدونِ overkill)

| لایه | چیست | فایل | قاعده |
|---|---|---|---|
| working | وضعیتِ لحظه‌ای | `LEARNING-STATE.json` + `_memory/HEARTBEAT.md` | فیلدهای غیرحاکمیتی mutable |
| episodic | تجربهٔ عملیاتی | `_memory/EXPERIENCE-LEDGER.md` | append-only، هر ردیف با هزینه/نتیجه |
| mutation | جهش‌نامهٔ Engine | `MUTATION-LEDGER.md` | append-only، هر جهش با ردیفِ مبنا |
| quarantine | ایده‌های خامِ MUSE | `MUSE-QUARANTINE-LEDGER` (جدید، فاز ۳) | append-only، fear-wrapper اجباری |
| durable-source | حقیقتِ نهایی | vault (`.md`) + git | منبعِ اوراکل؛ منشور دستِ آری |

- **provenance (اجباری روی هر ردیفِ خروجی):** `origin` + `external_data` (طبق `LEARNING-CONTRACT` L4_memory) — تا همیشه معلوم باشد یک درس از کجا آمده و آیا دادهٔ خارجی داشته.
- **retention:** هرگز حذف؛ فقط انتقال/نسخه‌گذاری (منشور + MUTATION-WHITELIST).
- **صراحتاً overkill (طبق Q6 تطبیق — ساخته نمی‌شود):** vector-DB سروری، Kafka/RabbitMQ، پروتکلِ agent-to-agentِ شبکه‌ای. در مقیاسِ یک‌نفر/یک‌لپ‌تاپ، **JSONL/markdown append-only + git** کافی است.

---

## ۲. INTELLIGENCE / MODEL-STRATEGY (قفل‌شده #۴ + برآوردِ هزینه)

| مصرف‌کننده | مدل | چرا | سقف |
|---|---|---|---|
| دکترِ سلامت (ساختار) | zero-LLM قطعی | تکرارِ زیاد، نتیجهٔ قطعی لازم | رایگان |
| GOVERNOR روتین | Haiku-tier | حجمِ بالا، کارِ ساده | $0.5/call، زیرِ $2/روز |
| GOVERNOR نقطهٔ‌تصمیم | Sonnet-tier | ابهام کم ولی مهم | $0.5/call |
| دکترِ تکاملی (انتخاب) | Sonnet-tier | قضاوتِ متوسط، نه خیلی نادر | زیرِ $2/روز |
| MUSE (تولیدِ ایده) | Sonnet/Opus high-temp | نادر + gated → گران توجیه دارد | شمارش در $2/روز |

**برآوردِ هزینه (برچسب: تخمین، نه قطعی):** دکتر رایگان · GOVERNOR ساعتی با Haiku ~ چند سنت/روز · MUSE + دکترِ تکاملی نادر ~ چند ده سنت در هر اجرا. جمعِ واقع‌بینانه **بسیار زیرِ سقفِ AU$30/ماه** (منشور §۵). خط فاجعهٔ $500 پابرجا.

---

## ۳. EVOLUTIONARY-DOCTOR — لایهٔ انتخاب (جدا از دکترِ سلامت)

> **رابطه (A2):** `dashboard_doctor.py` = سلامتِ **ساختار** (قطعی، zero-LLM، دست‌نخورده). دکترِ تکاملی = انتخابِ **ایده** (ارزیابیِ LLM روی خروجیِ MUSE). دو کارِ متفاوت، دو موجودیت.

**گیتِ ایمنیِ سخت (اول اجرا می‌شود — negative selection):** هر ایده که *هرکدام* را داشته باشد، **بدونِ نمره کشته می‌شود**:
- ناهم‌راستا با charter/لیستِ سیاه، یا
- یک‌طرفه‌ی برگشت‌ناپذیر با blast_radius بالا، یا
- fear-wrapperِ ناقص.

**نمره‌دهیِ بازمانده‌ها (۵ محور، هرکدام ۰–۲):**

| محور | ۰ | ۱ | ۲ |
|---|---|---|---|
| هم‌راستایی با charter | نقض | خنثی | تقویت |
| شواهد/امکان‌پذیری | حدسِ محض | قابلِ‌تست | شاهدِ زنده |
| blast-radius (معکوس) | فاجعه | محدود | بی‌ضرر |
| ROI | ناچیز | متوسط | بالا |
| برگشت‌پذیری | یک‌طرفه | سخت | آسان |

- آستانهٔ forward: **≥ ۸/۱۰**. فقط بازمانده‌ها به‌صورت **propose-only** روی میزِ آری می‌روند.
- دکتر **اجرا نمی‌کند**؛ فقط نمره می‌دهد و forward می‌کند (منشور §۱).
- هر حکم یک ردیف در `MUSE-QUARANTINE-LEDGER` (killed/forwarded + دلیل).

---

## ۴. EVALUATION-FRAMEWORK — متریک‌ها

- نرخِ بقای ایده (forwarded ÷ کلِ MUSE).
- نرخِ پذیرشِ آری (verdict-yes ÷ forwarded) — اگر خیلی پایین، آستانهٔ دکتر بد است.
- هزینه به‌ازای ایدهٔ پذیرفته‌شده.
- تأخیرِ قرنطینه → verdict.
- **متریکِ تنوع** (ضدِ over-pruning — همان kill-criteria نمونهٔ فاز ۳): اگر تنوعِ ایده افت کرد، دکتر زیادی سخت‌گیر است.
- صفر ایدهٔ اجرا‌شده بدونِ عبور از گیتِ آری (اگر > ۰ = نقضِ اصلی).

## ۵. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی.** فقط طراحی؛ هیچ فایلِ ژنوم/کد ویرایش نشد.

## ۶. باز مانده و گامِ بعد
- بازِ verdict نیست.
- **با «برو»:** فاز ۵ (آخر) — بک‌اپِ off-box + DR + قفل‌های ضدِ runaway + همیشه‌روشنِ نهایی.

## ۷. ردیفِ ledger پیشنهادی (kind=propose)

| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | PENTA فاز ۴ + «برو» | schemaی حافظه + model-tiering + دکترِ تکاملی + متریک‌ها | pending-اجرا (فاز ۵) |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد.*
