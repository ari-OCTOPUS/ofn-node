---
tags: [status, report, architect, source-of-truth, handoff]
created: 2026-07-03
based-on: "[[SYSTEM-BLUEPRINT-v2]]"
purpose: گزارش وضعیت واحد (بستن G-12) + پرامپت جامع مرحلهٔ بعد
verified: کد واقعی روی فایل‌ها چک شد (2026-07-03)
---

# گزارش کامل Architect + پرامپت مرحلهٔ بعد

> این سند دو کار می‌کند: (۱) **منبع حقیقت واحد برای وضعیت** — که G-12 (سه سند وضعیت متناقض) را می‌بندد؛ (۲) **پرامپت جامع مرحلهٔ بعد** با تمرکز معماری و طراحی. قانون حل تناقض همان است: **کد واقعی > سند جدیدتر > سند قدیمی‌تر**.

---

## بخش ۱ — این پروژه چیست؟

**Architect** یک «مغز دوم / لایهٔ مادر» است: سیستم AI همیشه‌روشن برای **یک اپراتور تک‌نفره** (آرمین) با دو مأموریت:

1. **محقق/طراح** — تحقیق خودکار و بهبود تدریجی خودِ سیستم، فقط در سطح prompt/skill، **هرگز weight مدل**.
2. **کنترل‌پلین (رئیس کل)** — بازرسی و کنترل بقیهٔ پروژه‌ها (Accounting، Crypto، Mining، Lead-نقاشی، Ziman، هیپنوتیزم) از طریق **یک رابط تلگرام**.

**اصل بنیادی:** «رئیس کل = انسان». نرم‌افزار جمع‌آوری/تحلیل/پیشنهاد می‌کند؛ هر action برگشت‌ناپذیر gate انسانی دارد (D-01).

**واقعیت فعلی در یک جمله:** معماری بسیار بالغ و red-team‌شده داری (~۹۰٪ دانش و طراحی)، ولی سیستم هنوز **مستقر نشده** و چند باگ بحرانی جلوی استقرار را گرفته (~۱۰٪ زنده).

---

## بخش ۲ — چه چیزهایی ساخته شده (نقشهٔ vault)

| مسیر | محتوا | وضعیت |
|---|---|---|
| `00-Home` + `PROJECT.md` | داشبورد و تعریف پروژه | ✅ |
| `01-Project/SYSTEM-BLUEPRINT-v2` | **منبع حقیقت واحد** (نسخهٔ فعال) | ✅ فعال |
| `01-Project/SYSTEM-BLUEPRINT-v1` | آرشیو دست‌نخورده | ✅ |
| `01-Project/DECISIONS` | ۲۴ تصمیم + حل تناقض | ✅ |
| `01-Project/GAPS` | حفره‌ها G-01..G-26 | ✅ |
| `01-Project/BACKLOG / CHANGELOG` | اقدام‌ها و تاریخچهٔ نسخه | ✅ |
| `01-Project/PROMPT-A / PROMPT-B` | پرامپت‌های جذب و تست خصمانه | ✅ |
| `02-Research/` (۱۰ فایل، ۰۵–۱۴) | تحقیق معماری | ✅ |
| `03-Exports/` (۳ فایل، ~۱۲هزار خط) | آرشیو کامل context چت‌ها | ✅ |
| `04-Docs/` | معماری سرور + مرجع فنی | ✅ |
| `_code/ai-farm/AI-sume/langar` | بات + مغز + حافظه + ایمنی (۵۸ فایل py) | ⚠️ کد کامل، مستقر نشده |
| `_code/ai-farm/AI-sume/langar-pro` | موتور تحقیق (FastAPI+Postgres) | ⚠️ باگ بحرانی (G-02) |
| `_code/ai-farm/fusion-mvp` | حلقهٔ خودبهبودی + igk kernel (۳۶ فایل py) | ⚠️ فقط MOCK |

---

## بخش ۳ — مرحله‌به‌مرحله چطور به اینجا رسیدیم

**مرحلهٔ ۰ — ایده‌پردازی:** چند چت طولانی معماری، آرشیو در `03-Exports/` (فقط architect-chat-export = ۷۰۸۸ خط / ۸۱ پیام).

**مرحلهٔ ۱ — تحقیق:** ۱۰ سند تحقیق عمیق روی ۱۰ محور (حافظه، حلقه‌های خودبهبودی، interoperability ابزار، ارزیابی/observability، ایمنی/حاکمیت، هزینه/زیرساخت، failure modeها، landscape فریم‌ورک، مبانی نظری).

**مرحلهٔ ۲ — کدنویسی موازی:** سه لایهٔ کد جدا ساخته شد که بعداً معلوم شد **یک سیستم‌اند** (D-24): `langar` = بدنه، `fusion` = الگوی حلقه و kernel، `architect` = چارچوب حاکم.

**مرحلهٔ ۳ — PROMPT-A (جذب و سنتز):** کل vault خوانده شد؛ ۲۴ تناقض حل و در DECISIONS ثبت شد؛ حفره‌ها در GAPS؛ و **BLUEPRINT-v1** به‌عنوان منبع حقیقت واحد ساخته شد.

**مرحلهٔ ۴ — PROMPT-B (تست خصمانه):** v1 نمرهٔ red-team **۵.۷/۱۰** گرفت؛ ~۵۷ ادعا مستقل چک شد (۴ خطای citation، ۲ ادعای بی‌منبع)؛ با اعمال fixها **BLUEPRINT-v2** ساخته شد (نسخهٔ فعال).

**مرحلهٔ ۵ — این سند:** بستن G-12 (منبع حقیقت واحد وضعیت) + آماده‌سازی گام بعد.

---

## بخش ۴ — معماری و طراحی (تمرکز اصلی)

### ۴.۱ معماری ۵-جزئی (بودجهٔ پیچیدگی — P7)

تصمیم کلیدی (D-02): به‌جای ~۱۵ جزء، فقط **۵ جزء core همیشه‌روشن** — چون ظرفیت واقعی یک اپراتور تک‌نفره ~۵ جزء است. بقیه satellite و phase-gated هستند.

```
👤 انسان (رئیس کل)
        │ Telegram
        ▼
┌─────────────────────────────────────────────┐
│ 1. Telegram Bot (langar) — owner_only        │
│    + Intent-Router rule-based (P11)          │
│    + Step-up passphrase برای فرمان مخرب       │
│    + kill-switch /halt (fail-closed)         │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│ 2. Brain + Router (rule-based)               │
│    ساده→Haiku · متوسط→Sonnet · پیچیده→Opus    │
│    Constitution Gate: «در شک: سکوت»           │
└──────┬───────────────────────┬───────────────┘
       ▼                       ▼
┌──────────────┐      ┌────────────────────────┐
│ 3. Research  │      │ 4. Memory              │
│   langar-pro │      │   SQLite v8 (۲۳ جدول)   │
│   :8000      │      │   → هدف Postgres/pgvec  │
│   +۲ checkpoint│    │   برچسب external_data   │
└──────────────┘      └────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│ 5. Safety Kernel                             │
│    constitution + kill-switch + allowlist    │
│    + PatchManager (سطح C = NotImplemented)    │
└─────────────────────────────────────────────┘

Satelliteها (gated، نه همیشه‌روشن):
  6. Self-Improvement Lab   7. Tenant Adapters (read-only)
```

### ۴.۲ اصول طراحی غیرقابل‌مذاکره (P1–P11)

| اصل | چه می‌گوید |
|---|---|
| P1 | Human-gate روی هر action برگشت‌ناپذیر؛ autonomy matrix چهارسطحی |
| P2 | Fail-closed: kill-switch قبل از هر action **و هر round حلقه**؛ timeout = DENY |
| P3 | Constraints **خارج از context مدل** (allowlist table)، نه داخل prompt |
| P4 | هر self-edit = git commit + eval gate + rollback <۵ دقیقه؛ سطح C ممنوع |
| P5 | Isolation per-tenant (schema + credential جدا) + بکاپ off-box |
| P6 | Measure-first: هیچ optimization قبل از instrument |
| P7 | بودجهٔ پیچیدگی = ۵ جزء core؛ satelliteها phase-gated |
| P8 | «در شک: سکوت» |
| P9 | دیوار داده: دادهٔ شخصی بدون اجازه وارد AI-Lab/tenant نمی‌شود |
| P10 | هیچ private key کریپتو روی ماشین agentic؛ signer off-box + human co-sign |
| P11 | هیچ LLM در مسیر فرمان: نگاشت متن→فرمان rule-based است |

### ۴.۳ مهم‌ترین تصمیم‌ها و بده‌بستان‌ها (Trade-offs)

| تصمیم | انتخاب | چرا (بده‌بستان) |
|---|---|---|
| D-01 | رئیس کل = انسان | ایمنی > اتوماسیون کامل؛ کلید اجرا همیشه دست انسان |
| D-02 | ۵ جزء نه ۱۵ | Maintainability یک‌نفره > کمال معماری |
| D-03 | حذف Wilson/rings/hash-chain از MVP | سادگی > «governance تئاتری» |
| D-04 | OpenLLMetry + MLflow نه Langfuse | اجتناب از lock-in (Langfuse خریداری شد ژانویه ۲۰۲۶) |
| D-09 | raw API الان → Agent SDK با احتیاط → LangGraph فقط خروج | اجتناب از lock-in + correlated failure |
| D-10 | Mining: تحلیل=INFORM، execution=HARD_STOP | علاقه به mining بدون ریسک مالی خودکار |
| D-12 | اول لپ‌تاپ، بعد VPS | کاهش ریسک استقرار |
| D-16 | routing هدف 70/25/5 (شروع 50/50) | هزینه پایین بدون افت کیفیت ناگهانی |
| D-22 | $60/ماه hard-stop ($500 = خط فاجعه) | جلوگیری از خزش خاموش هزینه |

### ۴.۴ مدل بودجهٔ دو-mode (بازنویسی v2)

| پارامتر | Normal (پیش‌فرض) | Growth (فقط با passphrase) |
|---|---|---|
| هر run | $0.50 | $1 |
| روزانه کل | $2 (alert در ۵۰٪/۸۰٪) | $10 |
| ماهانه کل | **$60 hard-stop → halt** | $300 |

نکتهٔ طراحی: در Normal mode، سناریوی سنگین **عمداً fail می‌شود** — این feature است نه bug.

---

## بخش ۵ — وضعیت واقعی کد (راستی‌آزمایی‌شده روی فایل‌ها)

| جزء | وضعیت | جزئیات راستی‌آزمایی‌شده |
|---|---|---|
| بات langar | ✅ کامل | ۵۸ فایل py؛ `bot.py` = ۱۱۶ هندلر async (~۵۰ فرمان) |
| kill-switch `/halt` | ✅ | کد موجود + تست‌شده |
| حافظهٔ SQLite | ✅ زنده | ۲۳ جدول؛ لایهٔ ۳ (HybridRetriever) آماده ولی **بدون call-site** (G-03) |
| BrainRouter | ⚠️ | کد هست ولی **wire نشده** → انتخاب مدل عملاً استاتیک (G-05) |
| موتور تحقیق langar-pro | 🔴 | **مسیر LLM در Docker مرده** (G-02) |
| حلقهٔ خودبهبودی | ⚠️ | سه پیاده‌سازی؛ فقط `self_improver.py` روزانه اجرا می‌شود؛ fusion loop **فقط MOCK** |
| تست‌ها | ⚠️ ۲۸ سبز | ۱۷ fusion + ۸ igk redteam + ۳ integration — **همه MOCK** |
| استقرار VPS | ❌ | هیچ‌چیز مستقر نیست |

### سه ریسک بحرانی (تأییدشده روی کد — باید اول حل شوند)

- 🔴 **G-01 — نشت secrets:** سه فایل `.env` واقعی + `langar.db` واقعی داخل repo. کلیدها باید **فوراً rotate** شوند؛ کلید age باید off-box برود.
- 🔴 **G-02 — مسیر LLM مرده:** `langar-pro/requirements.txt` کتابخانهٔ `anthropic`/`openai` را ندارد (فقط در کامنت «فازهای بعد») → با هر کلیدی ImportError و degrade به آفلاین.
- 🟠 **G-26 — هیچ اجرای LIVE ثبت نشده:** «اثبات ۰.۶→۰.۸→۱.۰» تماماً MOCK با scorer کیواژه‌ای (Goodhart). تا held-out واقعی نیامده، «کارکرد اثبات‌شده» معتبر نیست.

---

## بخش ۶ — نقشهٔ راه

- **MVP (فاز ۰، ۱–۲ هفته):** امن‌سازی secrets → رفع باگ deploy → kill-switch در حلقه → اسموک ۷روزه روی **لپ‌تاپ** + یک restore واقعی از بکاپ.
- **v1-فاز (۳–۶ هفته):** استقرار VPS + سیم‌کشی مغز (BrainRouter، budget، trace، action_policy، step-up passphrase) + اولین adapter (Accounting، read-only).
- **v2-فاز (۲–۳ ماه):** خودبهبودی gated واقعی (با held-out) + چند-tenant + مهاجرت Postgres/pgvector/Mem0.

**معیار «تمام» MVP:** ۷ روز uptime؛ kill-switch <۵s در تست واقعی؛ restore موفق؛ صفر secret در repo (gitleaks پاس).

---

## بخش ۷ — پرامپت جامع مرحلهٔ بعد

> این پرامپت را به یک AI مهندس (Claude/Cowork) بده تا **مرحلهٔ بعد با تمرکز معماری و طراحی** را اجرا کند. طوری نوشته شده که خودبسنده باشد و بلافاصله قابل اجرا.

```markdown
# مأموریت: تثبیت معماری Architect و آماده‌سازی برای اولین استقرار امن

تو یک Senior AI Engineer / Solution Architect / Security Expert هستی که روی
پروژهٔ «Architect» کار می‌کنی — یک سیستم AI همیشه‌روشن تک‌اپراتوره با دو نقش:
محقق/طراح خودبهبود + کنترل‌پلین تلگرامی برای بازرسی بقیهٔ پروژه‌ها.
منبع حقیقت واحد = SYSTEM-BLUEPRINT-v2. قانون حل تناقض: کد واقعی > سند جدیدتر > قدیمی‌تر.

## زمینهٔ الزامی (اول این‌ها را بخوان)
- 01-Project/SYSTEM-BLUEPRINT-v2.md  (معماری فعال، ۵ جزء، اصول P1–P11)
- 01-Project/DECISIONS.md            (۲۴ تصمیم + بده‌بستان‌ها)
- 01-Project/GAPS.md                 (حفره‌ها G-01..G-26)
- 01-Project/BACKLOG.md              (اقدام‌ها به اولویت)
- این سند (GOZARESH-KAMEL-VA-PROMPT-BAADI) برای وضعیت راستی‌آزمایی‌شده

## Problem / Goal / Constraints / Assumptions / Risks (اول این‌ها را صریح کن)
- Problem: معماری بالغ است ولی سیستم مستقر نیست و ۳ ریسک بحرانی باز است.
- Goal: تثبیت معماری در سطح طراحی + بستن ۳ ریسک بحرانی تا سیستم آمادهٔ
  اسموک ۷روزهٔ امن روی لپ‌تاپ شود.
- Constraints: تک‌اپراتور، بودجهٔ پیچیدگی ۵ جزء (P7)، بودجهٔ مالی $60/ماه
  hard-stop، fail-closed (P2)، هیچ LLM در مسیر فرمان (P11).
- Assumptions: هر فرض بحرانی را صریح بنویس، هرگز بی‌صدا فرض نکن.
- Risks: G-01 (secrets)، G-02 (LLM مرده)، G-26 (بدون LIVE).

## کارهای این مرحله (به ترتیب، معماری‌محور)

### الف) بستن ۳ ریسک بحرانی (پیش‌نیاز هر چیز)
1. G-01: طرح rotation کامل کلیدها + حذف .env/langar.db از repo + .gitignore
   کامل + انتقال کلید age به off-box. (BACKLOG-01)
2. G-02: افزودن anthropic/openai به langar-pro/requirements.txt + یکسان‌سازی
   نسخهٔ Postgres (pg15) بین دو compose + رفع clone در one-liner-vps-setup.sh.
3. G-26: طراحی held_out.json واقعی (۲۰+ فکت) + جایگزینی scorer کیواژه‌ای با
   eval غیرخودارجاع + ارتقای گیت از denylist به allowlist ساختار.

### ب) تثبیت معماری در سطح طراحی (خروجی = سند + کد اسکلتی)
4. جدول action_policy(tenant_id, domain, max_amount, requires_approval,
   hard_stop) را طراحی و به schema اضافه کن + نقطهٔ enforcement در مسیر فرمان.
5. قرارداد Tenant Adapter را به‌صورت interface خواندنی نهایی کن:
   status()/logs(n)/report(period)/audit() با credential جداگانهٔ read-only
   که enforced است نه قراردادی (G-25).
6. Intent-Router rule-based + Step-up passphrase را طراحی کن (الگوی
   brain_router.py). نگاشت‌نشدنی → «فرمان صریح بده».
7. kill-switch را در هر round حلقهٔ self_update و قبل از هر git commit
   interpose کن + mirror فایل STOP در langar (منبع حقیقت = flag DB).

### ج) verification (اجباری)
8. هر ادعای وضعیت را روی کد واقعی چک کن (grep/read)، نه از روی سند.
9. یک خروجی diff/گزارش از تغییرات بده + به‌روزرسانی BACKLOG (✅ زدن انجام‌شده‌ها).

## استانداردهای خروجی
- هر تصمیم معماری: بده‌بستان روی Cost/Complexity/Scalability/Security (۱–۱۰)
  + ثبت در DECISIONS با قانون حل تناقض.
- کد: Clean Code + error handling + fail-closed default.
- هر چیز طراحی‌شده-ولی-بدون-کد را صریح برچسب بزن (صداقت وضعیت).
- در پایان: خلاصهٔ «چه ساخته شد / چه ریسکی باز ماند / گام بعد».

## Non-goals (دست نزن)
- weight update/fine-tune خودکار · trade خودکار (FINANCIAL=HARD_STOP)
- CrewAI/AutoGen/k8s · اجرای LIVE حلقه قبل از held-out واقعی
- استقرار VPS قبل از اسموک موفق لپ‌تاپ (D-12)
```

---

*ساخته‌شده ۲۰۲۶-۰۷-۰۳ · مبتنی بر SYSTEM-BLUEPRINT-v2 · وضعیت کد روی فایل‌ها راستی‌آزمایی شد · می‌بندد: G-12*
