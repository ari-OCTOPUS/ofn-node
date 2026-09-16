---
type: report
# title: "Lead-نقاشی Synthesis — Revised"
# subtitle: "Spider/Octopus mapping validated against actual code"
created: 2026-07-12
updated: 2026-07-29
tags: [painting, lead, synthesis]
created_by: "ZCode (GLM-5.2), deep-read of brushline/60_code + کاریابی/bot"
status: draft
# supersedes_note: This document revises the earlier 'Lead-نقاشی Octopus Synthesis'
#   produced in a different agent sandbox. That synthesis contained several
#   claims (E15, E16, E24) that did not survive verification against the
#   actual codebase. This version keeps ONLY claims confirmed by direct
#   file reads with line-number evidence.
# owner_veto: "Ari retains full veto; all names are provisional."
---

# Lead-نقاشی Synthesis — Revised (2026-07-12)

> **اصل مادر:** IMPROVE, DON'T REWRITE. ESTABLISH TRUTH BEFORE AUTOMATION.
> MODEL OUTPUT IS NOT EVIDENCE.

این سند نتیجهٔ **deep-read کد واقعی** است، نه فرض. هر ادعا با `file:line` قابل راستی‌آزمایی است. سنتز قبلی (ساخته‌شده در sandbox ایجنت دیگر) پنج حفرهٔ E15–E25 را ادعا کرد؛ سه‌تا رد شدند، یکی نیمه‌تأیید شد، یکی تأیید شد، و یک حفرهٔ جدید کشف شد.

---

## ۱. نتایج اعتبارسنجی — جدول رأی

| حفره | ادعای سنتز قبلی | واقعیت کد | رأی نهایی |
|------|-----------------|-----------|-----------|
| **E15** | orchestrator + queue + resilience روی یک event loop، دکتر با بیمار می‌میرد | کد کاملاً synchronous است؛ هیچ `asyncio`ای در orchestrator/queue/resilience نیست. `main.py` فقط برای Telegram polling از asyncio استفاده می‌کند. | **🔴 رد شد** |
| **E16** | `is_human=1` ستون قلب/لاجر را جعل‌پذیر می‌کند | چنین ستونی وجود ندارد. schema واقعی: `id, prev_hash, entry_hash, event_type, entity_id, payload, timestamp`. زنجیره SHA-256 hash-chained است. | **🔴 رد شد** |
| **E25** | شش agent هیچ contract رسمی ندارند | تأیید. هیچ BaseAgent / Protocol / ABC / abstractmethod مشترک وجود ندارد. هر کلاس `class XAgent:` است. | **🟢 تأیید شد** |
| **E23** | دادهٔ harvester می‌تواند tainted باشد | نیمه‌تأیید. provenance پایه (`source` + `external_id`) داریم ولی quarantine/schema-validation/integrity-check نداریم. `save_lead()` مستقیم INSERT می‌کند. | **🟡 نیمه‌تأیید** |
| **E24** | bot روی اینترنت بدون auth exposed است | رد شد. `_is_authorized()` روی هر ۸ command handler بدون استثنا اعمال می‌شود. | **🔴 رد شد** |
| **E-new** | — | 🆕 کشف‌شده. `harvesters/keywords.py` وجود ندارد ولی هر سه harvester فعال از آن import می‌کنند → احتمالاً crash on import. | **🟢 یافتهٔ جدید** |

---

## ۲. نگاشت زیست‌شناسی عنکبوت — فقط قسمت‌های واقعی

| بخش پروژه | مسیر فایل | معادل زیستی | معادل Octopus | شواهد کد |
|-----------|-----------|------------|--------------|----------|
| **قلب / لاجرم غیرقابل‌تحریف** | `60_code/src/audit.py` | ابریشم با pheromone signature | LANGAR ledger | hash-chained SHA-256، `_append_lock` (خط ۲۵)، `verify_chain` (خط ۱۰۷–۱۴۷). PII → hash ref در `_sanitise_payload` (خط ۲۸–۳۸). |
| **مغز / هماهنگ‌کننده** | `60_code/src/orchestrator.py` + `queue.py` | سین‌گانگلیون | GWT broadcast hub | **synchronous** call-stack، نه event loop. `intake_enquiry`, `handle_enquiry`, `kickoff_suburb_page` و غیره. |
| **شش پا / ورکرها** | `60_code/src/agents/{asset,audience,channel,content,lead_capture,researcher}.py` | گانگلیون پا (Leg Neuromeres) | شش Worker | بدون BaseAgent. `ContentAgent` (`content.py:136`)، `LeadCaptureAgent` (`lead_capture.py:62`)، و غیره. فقط `AGENT_ID` رشته‌ای قراردادی. |
| **تار کششی / I/O** | `60_code/src/resilience.py` | تار کششی + damping | Chrono Bus + damping | synchronous retry با exponential backoff + jitter (خط ۸۲–۸۳)، `before_attempt` governance hook (خط ۷۲–۷۳)، idempotency keys (خط ۲۷–۲۹). |
| **عصب‌کشی / مرز I/O** | `کاریابی/bot/telegram_bot.py` + harvesters | Anchor threads + Slit sensilla | I/O boundary + quarantine | `_is_authorized()` روی هر ۸ handler (خط ۴۸–۵۸). `ACTION_RE` regex whitelist (خط ۳۱). |
| **حافظه** | `10_knowledge_base/` + `data/portfolio/` | Web geometry + vibration history | Semantic + Episodic memory | ۱۵ فایل KB-00 تا KB-14. |
| **سیاست / cuticle** | `00_governance/` + `20_specs/THREAT_MODEL.md` | Exoskeleton | Policy kernel | BLUEPRINT, MANIFEST, ROADMAP, MASTER_INSTRUCTIONS. |
| **دکتر / recovery** | `60_code/src/resilience.py` + `evals/run_eval.py` | Molting | Recovery + eval | retry/backoff inline، نه watchdog مستقل. ارزیابی در `run_eval.py`. |

---

## ۳. حفره‌های واقعی تأییدشده (۳ مورد)

### 🟢 E25 — agents بدون contract رسمی

**وضعیت:** تأیید شد.

**شواهد:**
- `src/agents/__init__.py` (۲ خط، کامنت فقط): هیچ export، هیچ base class.
- شش کلاس، همگی inherit از `object`:
  - `Researcher` (`researcher.py:96`)
  - `AudienceAgent` (`audience.py:86`)
  - `ContentAgent` (`content.py:136`)
  - `AssetAgent` (`asset.py:24`)
  - `ChannelAgent` (`channel.py:46`)
  - `LeadCaptureAgent` (`lead_capture.py:62`)
- grep برای `BaseAgent|Protocol|ABC|abstractmethod|interface|contract` در کل `src/agents/` = **صفر تطابق**.
- الگوی مشترک فقط `AGENT_ID` رشته‌ای است که هر agent مستقلاً تعریف می‌کند — بدون enforcement.
- orchestrator (`orchestrator.py:40–57`) هر کلاس را مستقیم import و instantiate می‌کند، بدون typing مبتنی بر interface.

**خطر واقعی:** اگر signature متد یک agent عوض شود، orchestrator در runtime می‌شکند نه در import-time. وقتی agent جدید اضافه شود، هیچ ساختار اجباری برای تعریف authority/inputs/outputs وجود ندارد. در معماری چندایجنتی OLP-1، این یعنی **Role Cardها در کد نهفته‌اند نه در `09-Agents/Role-Cards/`**.

### 🟡 E23 — دادهٔ harvester بدون quarantine

**وضعیت:** نیمه‌تأیید.

**آنچه داریم (مثبت):**
- provenance پایه: `source` و `external_id` روی هر Lead (`austender.py:94`, `nsw_etendering.py:79`, `planning_alerts.py:110`).
- dedup constraint در `save_lead()` از طریق unique `(source, external_id)` (`db.py:100–114`).
- keyword filter: `is_paint_relevant()` قبل از ساخت Lead.
- truncation: `title[:200]`, `description[:3000]`, `raw_json[:5000]`.
- defensive parsing در scorer: `scorer.py:38–44` با try/except و `isinstance(raw, dict)`.

**آنچه نداریم (حفره):**
- ❌ quarantine table یا status پیش از `status="new"`.
- ❌ schema validation روی Lead قبل از INSERT.
- ❌ integrity check (hash/signature) روی raw_json.
- ❌ جدول جداگانه برای pending-review قبل از ورود به لاجرم اصلی.

**خطر واقعی:** اگر API upstream (Austender، NSW eTendering، Planning Alerts) دیتای مخرب یا malformed برگرداند، می‌تواند مستقیم به جدول leads برسد. truncation به‌حدی محافظت می‌کند ولی content sanitization (XSS، injection) وجود ندارد.

### 🟢 E-new — `keywords.py` مفقود

**وضعیت:** کشف‌شده، تأیید شد.

**شواهد:**
- هر سه harvester فعال از `harvesters.keywords` import می‌کنند:
  - `austender.py:24`: `from harvesters.keywords import is_paint_relevant`
  - `nsw_etendering.py:23`: `from harvesters.keywords import is_paint_relevant`
  - `planning_alerts.py:18`: `from harvesters.keywords import is_paint_relevant`
- `keywords.py` در repo **وجود ندارد** (تأیید با `find` و `ls`).
- `estimate_one.py` disabled است (خروجی `[]`).

**دو احتمال:**
1. فایل هرگز commit نشده → harvesters روی import کرش می‌کنند → کل لیدگیری از این سه منبع نمی‌تواند run شود.
2. فایل روی deployment machine هست ولی در این repo نیست → keyword filter opaque و غیرقابل‌audit است.

**این مهم‌ترین مشکل عملی فوری است.** قبل از هر معماری، باید مشخص شود آیا `keywords.py` هرگز وجود داشته یا گم شده.

---

## ۴. ادعاهای ساختگی که حذف می‌شوند

صادقانه، چون اعتماد به واقعیت مهم‌تر از زیبایی مدل است:

### 🔴 E15 — "shared event loop"

**چرا غلط بود:** grep برای `asyncio|async def|await|get_event_loop|create_task|gather` در `orchestrator.py`، `queue.py`، `resilience.py`، `audit.py` = **صفر تطابق**. `resilience.py:96` از `time.sleep(delay)` استفاده می‌کند، نه `asyncio.sleep`. `queue.py` هر متد synchronous SQLite است.

**حقیقت ظریف‌تر:** کد synchronous call-stack دارد. اگر process کرش کند، هیچ watchdog مستقلی برای recovery وجود ندارد — ولی مکانیزم "shared event loop" که ادعا شده بود، واقعیت ندارد. `main.py:40` از `asyncio.run(main())` فقط برای Telegram polling استفاده می‌کند، نه برای orchestration.

### 🔴 E16 — "`is_human=1` column"

**چرا غلط بود:** grep برای `is_human` در کل `src/` = **صفر تطابق**. schema واقعی (`audit.py:93–98`):
```sql
INSERT INTO audit_entries
(id, prev_hash, entry_hash, event_type, entity_id, payload, timestamp)
VALUES (?, ?, ?, ?, ?, ?, ?)
```
هیچ ستون origin/provenance flag نیست. `verify_chain` (خط ۱۰۷–۱۴۷) کل زنجیره را walk می‌کند و هر hash link را راستی‌آزمایی می‌کند.

**نقطه‌ضعف واقعی (متفاوت از ادعا):** زنجیره خودارجاعی است — هر entry فقط `prev_hash` را hash می‌کند. کلید HMAC خارجی وجود ندارد. یعنی کسی با write access به SQLite می‌تواند از نقطهٔ tamper تا tip کل زنجیره را با hashهای معتبر بازنویسی کند و `verify_chain` آن را قبول کند. دفاع فعلی database-level access control است، نه cryptographic non-repudiation. **این مشکل واقعی است ولی مکانیزمش با ادعای `is_human=1` فرق دارد.**

### 🔴 E24 — "bot بدون auth"

**چرا غلط بود:** `_is_authorized()` (`telegram_bot.py:48–58`) روی **هر ۸ command handler** به‌عنوان اولین خط فراخوانی می‌شود:
- `cmd_start:122`, `cmd_new:145`, `cmd_digest:166`, `cmd_channels:191`, `cmd_stats:206`, `cmd_hunt:238`, `cmd_action:264`, `cmd_report:400`.
- فقط یک chat ID مجاز است (از `.env`).
- کاربران غیرمجاز silent rejection می‌شوند (بدون leak اطلاعات).
- `/draft` صریحاً از ارسال email امتناع می‌کند (پیام: "send only manually").
- command injection protection: `ACTION_RE` regex whitelist (خط ۳۱) + parameterized queries.

**نقطه‌ضعف واقعی (متفاوت از ادعا):** rate limiting وجود ندارد. اگر chat مجاز compromise شود، `/hunt` می‌تواند API token خرج کند بدون secondary confirmation. ولی در مدل single-operator این اولویت پایینی دارد.

---

## ۵. ایده‌های spider-inspired — بررسی مجدد

از ۷ ایدهٔ سنتز قبلی، فقط ۳ مورد روی حفرهٔ واقعی سوارند:

### ✅ نگه داشته می‌شوند

**۱. Neuromere Contract (برای E25)**
- برای شش agent یک `BaseAgent` protocol یا ABC تعریف کنیم که `AGENT_ID`, `authority` (allowed/forbidden)، `inputs`، `outputs`، `run()` signature را اجباری کند.
- مطابق OLP-1 Role Card schema (قسمت ۵ استاندارد).
- این قرارداد می‌تواند نقش `09-Agents/Role-Cards/` را در کد ایفا کند.
- خطر: کم. افزودنی، نه تخریبی. هر agent فعلی به‌مرور migrate شود.

**۲. Slit Sensilla Quarantine (برای E23)**
- قبل از `save_lead()` یک جدول `leads_quarantine` اضافه شود؛ Leadها ابتدا آنجا بنشینند با `status="pending_validation"`.
- schema validation + integrity hash روی raw_json.
- فقط پس از validation به جدول اصلی `leads` منتقل شوند.
- خطر: متوسط. به schema migration نیاز دارد ولی روی data-flow موجود additive است.

**۳. External HMAC on Audit Chain (نسخهٔ اصلاح‌شدهٔ "Pheromone Audit")**
- ایدهٔ اصلی Pheromone Audit درست بود ولی روی ادعای غلطِ `is_human=1` سوار بود.
- نسخهٔ واقعی: یک کلید HMAC خارجی (از `.env`، نه در DB) اضافه شود؛ هر entry علاوه بر `entry_hash` یک `hmac_tag` داشته باشد که با کلید خارجی محاسبه شده.
- این rewrite کامل زنجیره را غیرممکن می‌کند (مگر اینکه کلید هم leak شود).
- خطر: متوسط. به schema migration و کلیدmanagement نیاز دارد.

### ❌ حذف یا mark می‌شوند

**۴. Web Rebuilding Portfolio** (`shadow/portfolio/` به‌جای duplicate) — این ایده برای مشکل duplicate عکس‌ها (`photos/` = `data/portfolio/`) بود. مشکل واقعی است ولی ربطی به زیست‌شناسی عنکبوت ندارد. نگه می‌داریم ولی به‌عنوان **data-hygiene task**، نه spider-inspired idea.

**۵. Test Pluck Gateway** (`model_gateway.py` + shadow run قبل از model swap) — ایدهٔ خوب ولی روی هیچ‌کدام از حفره‌های تأییدشده سوار نیست. به backlog منتقل می‌شود.

**۶. Supercontraction Recovery** (compact → rehydrate پس از crash) — این روی E15 سوار بود که رد شد. حذف.

**۷. Molting Upgrade Protocol** — ایدهٔ خوب ولی عمومی؛ روی حفرهٔ خاصی سوار نیست. به backlog.

---

## ۶. ۹ سرویس نقد — بررسی مجدد

| سرویس | فایل‌های موجود | وضعیت واقعی | توضیح |
|-------|---------------|-------------|-------|
| Trust Kernel | ❌ هیچ‌کدام | **نیاز واقعی: کم** | `audit.py` hash chain دارد. HMAC خارجی فقط اگر threat model آن را طلب کند. |
| Identity & Charter | `00_governance/` | ✅ وجود دارد | BLUEPRINT، MANIFEST، ROADMAP. |
| Event Ledger | `src/audit.py` | ✅ قوی است | hash-chained، append-only، PII-sanitised. نقطه‌ضعف: HMAC خارجی ندارد. |
| Memory Compiler | `10_knowledge_base/` | ⚠️ نیمه‌کامل | KB فایل‌های دستی هستند، نه fact_store اجرایی. |
| Evidence/Provenance | ❌ هیچ‌کدام | **نیاز واقعی: متوسط** | برای E23 (harvester quarantine). |
| Context Composer | `src/models.py` | ⚠️ بررسی نشده | نیاز به deep-read جداگانه. |
| Model Gateway | ❌ هیچ‌کدام | **نیاز واقعی: کم (الان)** | routing در `config.py` و `orchestrator.py` نهفته است. |
| Execution Fabric | `src/gate.py` + `src/queue.py` | ✅ وجود دارد | gate = approval boundary، queue = decision tracking. |
| Eval & Release | `evals/run_eval.py` | ✅ وجود دارد | ولی qualification suite رسمی (OLP-1 §14) پیاده‌سازی نشده. |

---

## ۷. متا-پرامپت برای ایجنت بعدی

```
CONTEXT: Lead-نقاشی یک سیستم لیدگیری service-mode برای نقاشی ساختمان سیدنی است.
دو لایهٔ کد دارد:
  1. brushline/60_code/ — سیستم محتوا/تایید اصلی (sync، SQLite، Telegram)
  2. کاریابی/bot/ — ربات harvesting/scoring فعال (async، Telegram)

CONFIRMED HOLES (validated against code, 2026-07-12):
  E25: src/agents/*.py — شش کلاس بدون BaseAgent/Protocol/ABC.
       پیامد: orchestrator در runtime می‌شکند نه import-time.
  E23: کاریابی/bot/db.py:110 — save_lead() مستقیم INSERT، بدون quarantine.
       پیامد: دادهٔ upstream malformed می‌تواند به leads برسد.
  E-new: کاریابی/bot/harvesters/keywords.py مفقود ولی هر سه harvester import می‌کنند.
       پیامد: احتمالاً harvesters نمی‌توانند run شوند.

REFUTED CLAIMS (do NOT act on these):
  E15: "shared event loop" — کد synchronous است.
  E16: "is_human=1 column" — چنین ستونی نیست؛ schema واقعی را ببین.
  E24: "bot بدون auth" — _is_authorized() روی هر ۸ handler هست.

REAL (but different) WEAKNESSES:
  - audit chain خودارجاعی است؛ HMAC خارجی ندارد (نه is_human).
  - rate limiting در bot نیست (نه "بدون auth").
  - watchdog مستقل برای crash recovery نیست (نه "shared event loop").

FIRST PRIORITIES (owner decides order):
  1. keywords.py: آیا هرجا در سیستم هست؟ آیا باید بازسازی شود؟
  2. E25: BaseAgent protocol (additive، کم‌خطر).
  3. E23: quarantine table (medium، schema migration).

CONSTRAINTS:
  - هیچ فایل موجودی تغییر نکن تا owner approve کند.
  - نام‌ها provisional، حق veto با Ari.
  - OLP-1 §"additive evolution over destructive rewrite".
```

---

## ۸. یک تصمیم لازم از owner

طبق OLP-1، هر پاسخ با یک تصمیم owner تمام می‌شود.

**اولویت اول کدام است؟**

| گزینه | چه چیزی | خطر | زمان تخمینی |
|-------|---------|------|------------|
| **A** | جستجوی کل سیستم برای `keywords.py` (آیاAnywhere هست؟) | کم (read-only) | سریع |
| **B** | بازسازی `keywords.py` اگر واقعاً گم شده | متوسط (کد جدید) | متوسط |
| **C** | BaseAgent protocol برای E25 | کم (additive) | متوسط |
| **D** | quarantine table برای E23 | متوسط (migration) | کند |

**توصیه:** A اول (تشخیص قبل از درمان) — بدون دانستن اینکه آیا `keywords.py` واقعاً مفقود است یا فقط در جای دیگری هست، نمی‌توان B را درست انجام داد.

---

*پایان سند. این سند هیچ فایل یا کد موجودی را تغییر نداد. همهٔ ادعاها با `file:line` قابل راستی‌آزمایی‌اند.*
