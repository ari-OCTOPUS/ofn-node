# AI FARM — MASTER EXPORT (فایل واحد انتقال پروژه)

> تاریخ ساخت: ۲۰۲۶-۰۷-۰۲ · ساخته‌شده برای انتقال کامل context به یک پروژه‌ی جدید.
> نحوه‌ی استفاده: این فایل را در Project knowledge پروژه‌ی جدید آپلود کن. بخش ۱ و ۲ را AI جدید اول بخواند؛ بخش ۳ به بعد محتوای verbatim فایل‌هاست.

---

# بخش ۱ — حافظه‌ی پروژه (Project Memory، verbatim)

**Purpose & context**

Ari is designing a hybrid AI system architecture that integrates three interconnected layers: **LANGAR** (a calibration ledger anchored to external truth), **Fusion** (a phased execution roadmap), and **HRV/biosignal data** as input to an orchestrator. The system is highly engineered around anti-sycophancy, decision rigor, and calibrated uncertainty.

Domain vocabulary in active use: Wilson lower bound, RMSSD, grounding-ratio, agreement spiral, append-only hash-chain, Orchestrator-00, N-of-1, DoD (definition of definition per phase), gate control.

**Current state**

- A master meta-orchestrator prompt (`04-meta-orchestrator-prompt.md`) has been produced with ten structured sections, including six HALT conditions (H1–H6) using Wilson lower bound as a hard decision procedure.
- An interactive visual dashboard summarizing system architecture, gate statuses, and phase progression has been built.
- The one-way information hierarchy is established: LANGAR governs Fusion; HRV feeds in as input only.
- A Task Router is embedded to prevent heavy templating on lightweight queries.
- Identified bottleneck: the real system constraint is **cold-start ledger data**, not prompt quality — no ledger records means prompt improvements have limited impact.

**On the horizon**

- Populating LANGAR with real ledger records to move past the cold-start limitation.
- Sequential phase unlocking in Fusion (Phase 3 gated behind earlier phases per LANGAR's no-self-improvement rule).
- Further calibration and testing of the orchestrator under live conditions.

**Key learnings & principles**

- "Better prompt = better system" is false when the underlying ledger is empty; data availability is the real bottleneck.
- The prompt functions as a **gate**, not an advisor — a meaningful architectural distinction.
- Sycophancy and agreement spirals are treated as first-class failure modes, not edge cases; a seven-step self-check is built into every response cycle.
- LANGAR's no-self-improvement constraint and Fusion's Phase 3 are not contradictory — they resolve through sequential unlocking.

**Approach & patterns — سبک تعامل ترجیحی کاربر (Ari/Armin):**

- Lead with the hardest challenge or broken assumption before offering any solution.
- Use certainty tags throughout: `[Certain]`, `[Probable]`, `[Guess]`.
- Structure complex outputs with named fields: role, challenge, analysis, proposal, steps, success metric, and gate control.
- Outputs are filed as named markdown artifacts (e.g., `04-meta-orchestrator-prompt.md`) — numbered filing convention.
- همیشه فارسی، کوتاه و مستقیم، بدون verbosity.

---

# بخش ۲ — عصاره‌ی چت‌های پروژه (۱۲ session)

## ۲.۱ — تحقیق ۲۰-لِین + Synthesis + Red-team
(sessionهای «Research documentation»، «New live artifact»، «20-Lane Agent Architecture»)

- یک Research Prompt Pack با ۲۰ لِین ساخته و اجرا شد. فایل‌های 05–14 (نیمه‌ی اول: shared-engineering, memory-architecture, self-improvement-loops, tool-interoperability, evaluation-observability, safety-governance, cost-infra-routing, failure-modes-blind-spots, framework-landscape, theoretical-foundations) + لِین‌های ۱۱–۲۰ (Context Engineering, Durable Execution, Multi-tenancy/Isolation, Identity/Auth/Secrets, PromptOps/GitOps, Agentic RAG/GraphRAG, Human-Agent UX, Scheduling/Concurrency, Reproducibility/Replay, Privacy/Compliance) + Synthesis + Red-team + پاسخ پنل (Claude/GPT/Gemini).
- **یافته‌های load-bearing از Synthesis:**
  - خطر شماره‌۱: مجاورت کلید کریپتو با LLM روی VPS اشتراکی → wallet drain via prompt injection. راه‌حل: signer کاملاً جدا/off-box، صفر LLM access، allowlist مقصد، human co-sign.
  - Foundation واقعی = Lane 13 (tenancy) + Lane 14 (secrets)، نه orchestration.
  - Egress proxy اجباری با payload logging + PII scan جلوی هر model call.
  - Durable exec سبک برای تک‌نفره = DBOS روی همان Postgres (نه Temporal).
  - ۹ tension کلیدی (T1–T9)، ۷ claim (C1–C7)، ~۱۵ blind spot مستند. قانون: تناقض‌ها flag شوند، حل نشوند؛ اعداد/آستانه‌ها verbatim.
  - Build order: Phase 0 (سخت‌سازی + isolation + secrets + egress) → 1 (log + policy gate) → 2 (durable + scheduling) → … → کریپتو track جدا → self-improvement آخر. تخمین: ~۳–۵ ماه part-time.
- منابع کلیدی وب: Kaduk et al. 2025 (Psychophysiology)، Microsoft Agent Governance Toolkit، Stanford CodeX (kill switches)، MintMCP AI agent security 2026.

## ۲.۲ — Context کلان کاربر (از self-prompt رسمی session «20-Lane»)

```
کاربر: اپراتور تک‌نفره، سیدنی/استرالیا. یک VPS اشتراکی، ۴ پروژه‌ی ناهمگون هم‌زمان:
(۱) مالی/حسابداری — ATO/GST/BAS، پول واقعی
(۲) ماینینگ کریپتو — کلید و wallet
(۳) مارکتینگ
(۴) دفترچه‌ی شخصی (PII بالا)
هدف کلان: یک سیستم agentی «همیشه‌روشن» long-running و امن (کدنام: langar).
```

## ۲.۳ — معماری LANGAR (sessionهای «Langar blueprint» و «Langar agent architecture»)

- تصمیم معماری: GitHub از طریق git CLI (repo خصوصی، push فایل‌ها + HANDOFF)؛ Telegram bot فقط یک‌طرفه (BotFather token + polling روی VPS، در container جدا از کریپتو).
- بحث تئوریک مرکزی: «آیا container-level isolation کافی است یا کریپتو باید off-box برود؟» موضع نهایی: **کریپتو off-box** — shared kernel یعنی یک CVE کافی است؛ prompt injection روی VPS + signer همان‌جا = فاجعه. ریسک: overhead عملیاتی یک دستگاه اضافه.

## ۲.۴ — Fusion-MVP و حلقه‌ی self-improvement (sessionهای «Fusion-MVP …» و «Memory review»)

- سیستم `fusion-mvp/` (= langar) یک **حلقه‌ی self-improvement کارکننده** دارد: نمره‌ی researcher ۰.۶ → ۰.۸ → ۱.۰، سپس explore → **rollback خودکار**؛ audit chain «سالم». اجرای واقعی تأییدشده.
- ضعیف‌ترین حلقه: `evals.py` یک rubric کلیدواژه‌ای است → خطر specification gaming (FM-10, T-14a). راه‌حل: gate دوم **held-out** از `igk/kernel.py::ground()` اجباری شد.
- پرامپت عملیاتی دو-تکه ساخته شد: بخش A رویه‌ی راه‌اندازی (`python self_update.py <role>`، چک STOP، چک audit chain، سقف ۴ دور، commit اجباری)؛ بخش B متاپرامپت Optimizer در حالت LIVE (bounded edit + دو-گیت + لیست FORBIDDEN).
- **خط قرمز:** self-improvement فقط system-prompt نقش‌های داخلی را عوض می‌کند — هرگز policy gate، killswitch، IGK، secrets، یا مسیر مالی/کریپتو. هر نسخه git commit، هرگز مستقیم به main.
- قدم بعدی اعلام‌شده: ارتقای `held_out.json` از سؤالات ساده به caseهای واقعی + نگهداری unseen set. تصمیم کاربر: «همه چیز اول روی لپ‌تاپ setup شود» (نه VPS).
- فولدرهای مرتبط: `fusion-mvp/`، `fusion-safety/` (THREAT-MODEL, GAP-AUDIT, IGK kernel)، `fusion-creative/`.

## ۲.۵ — Build و راه‌اندازی unified (session «Project handoff file»)

- `SETUP_PROMPT.md` ساخته شد: پرامپت کامل برای هر عامل کدنویس. مراحل: ۰) بررسی ساختار و Docker → ۱) ساخت `.env` از `.env.example` + `.gitignore` → ۲) `docker compose -f docker-compose.unified.yml up -d --build` (۴ کانتینر) → ۳) هفت تست پذیرش (سلامت بک‌اند، `/start` و `/menu`، kill-switch، `/research` متصل به pro، تست fallback با خاموش‌کردن api، AI-Lab، پایداری بعد از restart) → ۴) اجرای ۲۴ ساعته + بکاپ.
- قوانین سخت: هیچ حذفی، کلید واقعی فقط در `.env`، fallback همیشه کار کند، قبل از هر کار مخرب اجازه بگیرد.
- فولدر `langar/` شامل: ARCHITECTURE, PLAN, BRAIN_PROMPT, RESEARCHER_PROMPT, CHECKLIST, USAGE, DEPLOYMENT_GUIDE_FA + `langar-pro/`.

## ۲.۶ — قلب و آگاهی / NEURO (session «Research prompt pack»)

- نقشه‌ی heart-awareness به v2/v3 ارتقا یافت؛ **تصحیح علمی مهم:** ادعای «غذا روی عصب واگ اثر می‌گذارد و HRV را کم می‌کند» غلط بود — در Kaduk 2025 خودِ دستگاه taVNS (مستقل از کالری) HRV را کاهش داد.
- طرح «همراهِ همیشه‌روشن»: سه بخش — **LANGAR** (مغز ناظر، دفترچه append-only، دکمه‌ی `/halt`)، **NEURO** (ثبت روزانه RMSSD و ترند، بدون تشخیص پزشکی)، **FUSION** (نوشتن خلاق با برچسب E/S/P). رابط: بات تلگرام.
- توصیه‌ی ثبت‌شده: همه را یک‌جا نساز؛ اول فقط قلب + دفترچه + دکمه‌ی خاموش.
- جزئیات کامل در HANDOFF.md (بخش ۳ همین فایل).

## ۲.۷ — Brushline: بیزینس نقاشی سیدنی (session «Sydney painting business AI system»)

- سیستم «خط تولید اعتماد»: سیگنال/enquiry → Orchestrator → Workerها (فقط draft) → دروازه‌ی ۱ Gate (قانون استرالیا: no false claim, consent, no PII leak) → دروازه‌ی ۲ تأیید انسانی در تلگرام (Approve/Edit/Reject) → انتشار/sync → دروازه‌ی ۳ Audit (لاگ hash-chained).
- سه قانون تغییرناپذیر: **INV-1** هیچ انتشار/خرج/پیام بدون تأیید کاربر · **INV-2** داده‌ی شخصی/مالی در AU بماند · **INV-3** هر اتوماسیون = kill switch + سقف خرج + audit.
- ۱۲ نقش agent: Orchestrator + Researcher, Audience/Sentiment, Content/Copy, Asset/Image, Channel-Pub, Lead-Capture + لایه‌ی مدیریتی (Estimation, Sales, Marketing, Operations, Compliance, Knowledge-Manager, Automation). اصل: «integrate, don't duplicate» — اتصال به ServiceM8/Tradify.
- ساختار پروژه: ۴۳ فایل markdown در `10_knowledge_base/`, `40_operations/`, `90_reference/`, `99_archive/` (PDFها و zip حذف شدند — ۲.۶MB → ۸۸KB).
- گیت آمادگی (R11/R12) باز است؛ داده‌ی لازم از کاربر: `avg_margin_per_job`، نرخ enquiry→quote، نرخ quote→job، `fx_aud_usd`، نرخ Google Places، `spam_penalty_units`، توکن بات + chat_id، فایل‌های LANGAR، تأیید حقوقی NSW برای `[verify-NSW]`.
- فاز بعدی توصیه‌شده (بدون کد): ساخت قالب quote از OPS-01، ۳ صفحه‌ی suburb، متن GBP + ۵ کپشن before/after، اسکریپت‌های پاسخ اول و پیگیری روز ۲/۵/۱۰.

## ۲.۸ — Export قبلی (session «Project data consolidation» قبلی)

- یک فایل `LANGAR-MASTER-EXPORT.md` (~۳۳۳KB) قبلاً ساخته شده: Memory + ده لِین تحقیق 05–14 verbatim + عصاره‌ی ۱۱ چت + پرامپت پروژه. **آن فایل در فولدر دیگری است و در فولدر فعلی «Ai farm (1)» نیست** — اگر لِین‌های تحقیق را کامل می‌خواهی، آن فایل را هم به پروژه‌ی جدید ببر.

## ۲.۹ — شکاف‌های شناخته‌شده‌ی این export

- فایل‌های `langar/` کامل، `fusion-mvp/` (کد)، `RESEARCH-PROMPT-PACK.md`، `ORCHESTRATOR-hybrid-system.md`، `MASTER-05-14-NORMALIZED.md` و ساختار ۴۳فایلی Brushline در فولدرهای sessionهای دیگر/فولدرهای دیگرند و از این session قابل‌خواندن نبودند. عصاره‌شان بالا آمده؛ برای محتوای کامل باید جداگانه attach شوند.

---

# بخش ۳ — HANDOFF.md (verbatim)

# HANDOFF — قلب و آگاهی + سیستم همیشه‌روشن

> این فایل یک handoff کامل برای انتقال context به یک AI جدید است.
> هیچ فایل خارجی‌ای نیاز نیست — همه چیز اینجاست.

---

## زمینه‌ی پروژه

**صاحب پروژه:** Armin  
**هدف کلی:** یک سیستم شخصی N-of-1 برای بررسی رابطه‌ی ماریجوانا، ضربان قلب، و آگاهیِ درونی (interoception) — با یک بات تلگرام به‌عنوان رابط همیشه‌روشن.

دو بخش جداگانه:
1. **نقشه‌ی پژوهش (HTML)** — مرجع علمی + پروتکل‌های عملی
2. **سیستم همیشه‌روشن (Markdown)** — معماری بات تلگرام + دستورالعمل ساخت

---

## بخش ۱ — نقشه‌ی پژوهش (heart-awareness-map-v3.html)

### خلاصه‌ی آنچه ساخته شده

یک صفحه‌ی HTML با طراحی dark-mode و متن فارسی RTL که:
- شواهد علمی را با تگ E (مستحکم) / S (حدس) / P (استعاره) دسته‌بندی می‌کند
- پروتکل‌های مشخص برای ۵ آزمایش N-of-1 دارد
- یک قالب لاگ روزانه دارد
- یک بخش «امروز چه کار کنم» در ابتدا دارد

### پنج آزمایش (E1–E5)

**E1 — منحنی autonomic:** اندازه‌گیری RMSSD در سه نقطه (قبل / onset / peak نشئگی) برای پیدا کردن عددِ tip-over شخصی.

**E2 — accuracy × confidence:** شمارش ضربان قلب بدون ابزار + ثبت میزان اطمینان → مقایسه‌ی هوشیار vs نشئه. از دو سنجه استفاده شود (شمارش + تشخیص هم‌زمانی).

**E3 — تست زمان:** تخمین ۳۰ ثانیه بدون ساعت → تأیید یا رد tolerance.

**E4 — retest بینش:** هر بینشِ نشئه را تگ [E/S/P] بزن → فردای هوشیار داوری کن.

**E5 — baseline خالص واگ:** یک روز بدون مصرف، RMSSD صبح + بعد از تنفس رزونانس + عصر → جدا کردن اثر THC از نوسانِ روزانه.

### یافته‌های علمی کلیدی (تأییدشده)

- **THC:** dose-dependent HR↑, HF-HRV↓. مدل PBPK-PD 2025 منحنی را کمّی کرد. [E]
- **taVNS 2025:** SDNN بالا رفت ولی RMSSD نه → مکانیسم: کاهش سمپاتیک، نه افزایش واگ. [E]
- **Interoception:** شمارش ضربان به‌تنهایی شکننده (Ferentzi 2025) — دو سنجه لازم است. [E]
- **HRVB:** برای افسردگی g=−0.41 معنادار، برای HRV g=+0.44. برای اضطراب/استرس: null. [S]
- **Kaduk 2025 تصحیح:** «غذا روی واگ» ادعای پشتیبانی‌نشده است. taVNS مستقل از کالری HRV را کاهش داد.

### قالب لاگ روزانه

| فیلد | مقدار | یادداشت |
|---|---|---|
| تاریخ | YYYY-MM-DD | همیشه |
| RMSSD | عدد ms | صبح · قبل از کافئین · ۲ دقیقه |
| خواب | ۱–۵ | ۱=خیلی بد، ۵=عالی |
| مصرف | بله/خیر | اگر بله: دوز و زمان |
| مکان | خانه/کار | |
| یادداشت | اختیاری | بینش با تگ E/S/P |

### حلقه‌ی روزمره

- **صبح (۱۲–۱۵ دقیقه):** baseline RMSSD → تنفس رزونانس ۶ نفس/دقیقه
- **حین روز (on-demand):** sigh دوگانه هر وقت موجِ عاطفی بالا زد
- **هفتگی (۱۰ دقیقه):** ترند ۷ روزه + cross-reference با خواب/مصرف

---

## بخش ۲ — سیستم همیشه‌روشن (Markdown)

### خلاصه‌ی آنچه ساخته شده

یک دستورالعمل MVP-first برای ساختن یک بات تلگرام شخصی با:
- معماری ۵ فایل ساده (بدون hash-chain، بدون Wilson score، بدون execution rings)
- Gate ساده (flag در SQLite)
- Kill-switch واقعی (`/halt`)
- Schema کامل
- کد Python واقعی برای gate و kill-switch
- ConversationHandler برای `/log`
- پرامپت ساده‌شده برای ایجنت کدنویس

### معماری MVP

```
VPS Linux
├── langar/
│   ├── main.py
│   ├── bot.py
│   ├── db.py
│   ├── .env          (BOT_TOKEN, OWNER_ID, CLAUDE_KEY)
│   └── requirements.txt
└── langar_bot.service
```

### Schema SQLite

```sql
CREATE TABLE IF NOT EXISTS log (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts    TEXT    NOT NULL DEFAULT (datetime('now')),
    rmssd REAL,
    sleep INTEGER,   -- 1–5
    used  INTEGER,   -- 0/1
    loc   TEXT,      -- home/work/other
    note  TEXT
);

CREATE TABLE IF NOT EXISTS insight (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT    NOT NULL DEFAULT (datetime('now')),
    content TEXT,
    tag     TEXT,   -- E / S / P
    recheck TEXT,   -- YYYY-MM-DD
    verdict TEXT    DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    val TEXT
);
INSERT OR IGNORE INTO config VALUES ('halted', '0');
```

### Gate و Kill-switch

```python
# db.py
def is_halted() -> bool:
    return get_config("halted") == "1"

# bot.py
async def any_handler(update, ctx):
    if is_halted():
        return  # سکوت کامل

async def cmd_halt(update, ctx):
    if str(update.effective_user.id) != OWNER_ID:
        return
    db.set_config("halted", "1")
    await update.message.reply_text("⏸ سیستم متوقف.")

async def cmd_resume(update, ctx):
    if str(update.effective_user.id) != OWNER_ID:
        return
    db.set_config("halted", "0")
    await update.message.reply_text("▶ ادامه.")
```

### دستورها

| دستور | کار |
|---|---|
| `/start` | معرفی |
| `/log` | ConversationHandler پنج‌مرحله‌ای |
| `/trend [N=7]` | میانگین RMSSD + correlation با خواب/مصرف |
| `/insight [متن]` | ثبت بینش با E/S/P و recheck |
| `/recheck` | بینش‌های امروز |
| `/status` | آخرین log + halted/active |
| `/halt` | توقف |
| `/resume` | ادامه |

### ConversationHandler /log — پنج مرحله

1. RMSSD (عدد یا /skip)
2. خواب (۱–۵)
3. مصرف (بله/خیر)
4. مکان (خانه/کار/جای دیگر)
5. یادداشت (اختیاری)

### پرامپت برای کدنویس

```
یک بات تلگرامِ شخصیِ single-user بساز.

Stack: Python 3.11 / python-telegram-bot v21 (async) / SQLite / python-dotenv
Security: BOT_TOKEN و OWNER_ID از .env؛ فقط OWNER_ID پاسخ می‌گیرد.
اول هر handler: if is_halted(): return

Schema: [جدول بالا]

Commands: [جدول بالا]

/log با ConversationHandler پنج‌مرحله‌ای
/trend با میانگین RMSSD و Pearson correlation با sleep/used
/insight با ذخیره و recheck date
/recheck بینش‌های recheck=today
/halt و /resume برای kill-switch

Output: main.py + bot.py + db.py + requirements.txt + systemd service + README deploy
```

### راه‌اندازی — پنج گام

1. `@BotFather` → `/newbot` → توکن
2. `@userinfobot` → chat_id
3. VPS بگیر (Hetzner/DigitalOcean، ~۵ دلار/ماه)
4. کد deploy کن + `.env` پر کن + تست
5. `systemctl enable langar_bot && systemctl start langar_bot`

### اصول LANGAR که باید حفظ شود

- gate قبل از هر پیام خروجی
- Human-write-only برای verdict (بات پیشنهاد، تو تأیید)
- kill-switch تست‌شده
- همیشه RMSSD — هرگز شاخص‌ها را مخلوط نکن
- در شک: سکوت

### فازهای بعدی

- **فاز ۱ (بعد از ۲ هفته):** پینگ صبحگاهی خودکار، مرور هفتگی، Apple Shortcut
- **فاز ۲ (بعد از ۱ ماه):** FUSION، Microsoft Agent Governance Toolkit، Wilson score

---

## وضعیت فعلی

- ✅ نقشه‌ی پژوهش v3 ساخته شد (HTML)
- ✅ دستورالعمل سیستم ساده‌شد (Markdown)
- ✅ هر دو فایل commit شدند
- ⏳ کد بات هنوز نوشته نشده — پرامپت آماده است
- ⏳ VPS راه‌اندازی نشده

## گام بعدی پیشنهادی

پرامپت بخش «پرامپت برای کدنویس» را به یک AI کدنویس (Claude/GPT) بده تا کد کامل بات را تولید کند. بعد طبق پنج گام راه‌اندازی روی VPS deploy کن.

---

*ساخته‌شده با Claude Sonnet 4.6 · ژوئن ۲۰۲۶*

---

# بخش ۴ — سیستم همیشه‌روشن: پرامپت و دستورالعمل (verbatim)

# سیستمِ همیشه‌روشن — نسخه‌ی ساده‌شده

> نسخه ۲.۰ · ژوئن ۲۰۲۶ · اصل: MVP‑first · ویرایش: بهینه‌سازی معماری

---

## مشکلِ اصلیِ نسخه‌ی ۱

نسخه‌ی قبل سه لایه‌ی enterprise را روی یک ابزار single-user کشید:

| ویژگی | طراحی‌شده برای | وضعیت در MVP |
|---|---|---|
| Wilson score lower-bound | ارزیابی ادعاهای علمیِ چندکاربره با n≥20 | ❌ HRV شخصی نیازی ندارد |
| Hash-chained SQLite | جلوگیری از tamper توسط چند کاربر | ❌ تو تنها کاربری — چه کسی tamper می‌کند؟ |
| Execution rings (Ring 0/2/3) | AI agent deployment در سازمان | ❌ برای single-user bot اضافه است |
| FUSION module | نوشتن خلاق | ❌ نباید در v1 باشد |

اصلِ ساده: feature را وقتی اضافه کن که **نبودش درد واقعی ایجاد کرده باشد.**

---

## معماریِ MVP — پنج فایل

```
VPS Linux
├── langar/
│   ├── main.py           # entry point
│   ├── bot.py            # handlers + conversations
│   ├── db.py             # SQLite wrapper
│   ├── .env              # BOT_TOKEN, OWNER_ID, CLAUDE_KEY
│   └── requirements.txt
└── langar_bot.service    # systemd — همیشه‌روشن
```

---

## Schema — بدون hash-chain

```sql
CREATE TABLE IF NOT EXISTS log (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts    TEXT    NOT NULL DEFAULT (datetime('now')),
    rmssd REAL,
    sleep INTEGER,   -- 1–5
    used  INTEGER,   -- 0 = نه / 1 = بله
    loc   TEXT,      -- home / work / other
    note  TEXT
);

CREATE TABLE IF NOT EXISTS insight (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT    NOT NULL DEFAULT (datetime('now')),
    content TEXT,
    tag     TEXT,   -- E / S / P
    recheck TEXT,   -- YYYY-MM-DD
    verdict TEXT    DEFAULT 'pending'  -- pending / confirmed / refuted
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    val TEXT
);
INSERT OR IGNORE INTO config VALUES ('halted', '0');
```

---

## Gate و Kill-switch (ساده)

```python
# db.py
def is_halted() -> bool:
    return get_config("halted") == "1"

# bot.py — اول هر handler
async def any_handler(update, ctx):
    if is_halted():
        return  # سکوت کامل

# /halt و /resume — فقط OWNER_ID
async def cmd_halt(update, ctx):
    if str(update.effective_user.id) != OWNER_ID:
        return
    db.set_config("halted", "1")
    await update.message.reply_text("⏸ سیستم متوقف.")

async def cmd_resume(update, ctx):
    if str(update.effective_user.id) != OWNER_ID:
        return
    db.set_config("halted", "0")
    await update.message.reply_text("▶ ادامه.")
```

**تست kill-switch را قبل از اعتماد انجام بده: `/halt` بزن، مطمئن شو بات جواب نمی‌دهد، بعد `/resume`.**

---

## دستورها

| دستور | کار |
|---|---|
| `/start` | معرفی + راهنمای سریع |
| `/log` | ثبت RMSSD + تگ‌ها (conversation) |
| `/trend [N=7]` | میانگین RMSSD و همبستگی با خواب/مصرف |
| `/insight [متن]` | ثبت یک بینش با تگ E/S/P و recheck date |
| `/recheck` | بینش‌هایی که امروز باید داوری شوند |
| `/status` | آخرین log + وضعیت halted/active |
| `/halt` | توقف فوری — همه‌ی ماژول‌ها ساکت |
| `/resume` | ادامه |

### ConversationHandler برای `/log` — پنج مرحله

1. «RMSSD امروز صبح چند بود؟» (عدد یا `/skip`)
2. «خوابِ دیشب؟» (۱–۵)
3. «دیشب مصرف؟» (بله / خیر)
4. «کجا بودی؟» (خانه / کار / جای دیگر)
5. «یادداشت؟» (اختیاری — `/skip`)
→ ثبت در DB + تأیید

### `/trend` — خروجی ساده

```
📊 ترند ۷ روز اخیر
RMSSD میانگین: ۴۲.۳ ms
بهترین روز: ۲۶ ژوئن (۵۸ ms) — خواب ۵، بدون مصرف
ضعیف‌ترین: ۲۳ ژوئن (۳۱ ms) — خواب ۲، مصرف
همبستگی خواب‌RMSSD: +۰.۶۸ (۷ نقطه)
```

---

## راه‌اندازی — پنج گام

**گام ۱ — بات بساز** (۳ دقیقه)
در تلگرام: `@BotFather` → `/newbot` → نام و یوزرنیم → **توکن** بگیر.

**گام ۲ — chat_id بگیر** (۱ دقیقه)
`/start` به بات بزن → `@userinfobot` → عددِ `chat_id` را کپی کن.

**گام ۳ — VPS بگیر** (ماهی ۴–۶ دلار)
Hetzner CX11 یا DigitalOcean Droplet. Ubuntu 22.04. Python 3.11 نصب کن.

**گام ۴ — deploy کن**
```bash
pip install python-telegram-bot python-dotenv
# .env را بساز:
#   BOT_TOKEN=...
#   OWNER_ID=...
#   CLAUDE_KEY=...   (اختیاری برای فاز ۱)
python main.py      # تست کن — /start بزن
```

**گام ۵ — همیشه‌روشن کن**
```ini
# /etc/systemd/system/langar_bot.service
[Unit]
Description=LANGAR Personal Bot
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/langar
ExecStart=/usr/bin/python3 main.py
Restart=always
EnvironmentFile=/home/ubuntu/langar/.env

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable langar_bot && systemctl start langar_bot
```
حالا حتی با ریستارت سرور، بات بالا می‌آید.

---

## HITL — نظارتِ متناسب با ریسک

| اقدام | نیاز به تأیید |
|---|---|
| خواندن RMSSD، نمایش ترند | ❌ خیر |
| پینگ صبحگاهی، یادآوری | ❌ خیر |
| ثبت بینش جدید (insight) | ❌ خیر — ولی با تگ E/S/P |
| ثبت verdict برای بینش | ✅ بله — دکمه‌ی Confirm |
| پاک‌کردن داده | ✅ بله — متن تأیید تایپ کن |
| تغییر قوانین gate | ✅ ممنوع برای بات — فقط تو از `.env` |

---

## اصولِ LANGAR که باید بماند

✅ **gate قبل از هر پیام خروجی** — `if is_halted(): return`
✅ **Human-write-only برای verdict** — بات پیشنهاد می‌دهد، تو تأیید می‌کنی
✅ **kill-switch واقعی** — تست شده، نه فقط در کد
✅ **شاخص قفل‌شده** — همیشه RMSSD؛ هرگز شاخص‌ها را مخلوط نکن
✅ **در شک: سکوت** — بات ساکت است، نه پرحرف

---

## پرامپتِ ساده‌شده برای ایجنتِ کدنویس

```
یک بات تلگرامِ شخصیِ single-user بساز.

Stack: Python 3.11 / python-telegram-bot v21 (async) / SQLite / python-dotenv
Security: BOT_TOKEN و OWNER_ID از .env؛ فقط OWNER_ID پاسخ می‌گیرد.
اول هر handler: if is_halted(): return

Schema:
  log (id, ts, rmssd, sleep[1-5], used[0/1], loc, note)
  insight (id, ts, content, tag[E/S/P], recheck, verdict)
  config (key, val) — seed: ('halted','0')

Commands:
  /start — خوش‌آمد
  /log — ConversationHandler پنج‌مرحله‌ای (RMSSD → خواب → مصرف → مکان → یادداشت)
  /trend [N=7] — میانگین RMSSD + correlation با sleep/used (Pearson ساده)
  /insight [text] — بپرس E/S/P و recheck date، ثبت کن
  /recheck — بینش‌هایی که recheck=today هستند
  /status — آخرین log + halted/active
  /halt — halted=1
  /resume — halted=0

Output: main.py + bot.py + db.py + requirements.txt + systemd service + README deploy روی VPS
```

---

## شاخصِ موفقیت

۱. بات بدون لپ‌تاپ ۲۴ ساعته بالاست
۲. هر صبح RMSSD ثبت می‌شود
۳. `/halt` در تست واقعاً همه را ساکت می‌کند
۴. هیچ verdict بدون تأیید تو ثبت نشده
۵. بعد از ۱۴ روز ترند واقعی داری

---

## فازهای بعدی (فقط وقتی واقعاً لازم شد)

**فاز ۱ — بعد از ۲ هفته‌ی استفاده‌ی واقعی:**
→ پینگ صبحگاهی خودکار (JobQueue تلگرام)
→ مرور هفتگیِ خودکار
→ Apple Shortcut → HTTP POST → بات (RMSSD از Health)

**فاز ۲ — بعد از ۱ ماه استفاده‌ی واقعی:**
→ اگر FUSION واقعاً می‌خواهی: یک handler جداگانه اضافه کن
→ اگر multi-agent شد: آن وقت [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) را وارد کن
→ اگر به مقایسه‌ی ادعاهای علمی نیاز داشتی: آن وقت Wilson score + hash-chain

---

## منابع

- [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) — execution rings + kill-switch برای فاز ۲+
- [python-telegram-bot v21](https://python-telegram-bot.org/) — کتابخانه‌ی اصلی
- [OWASP Agentic AI Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — مبنای گاردریل‌ها
- مبنای طراحی: **LANGAR Blueprint v0.1** (فایل اصلی خودت)

---

# بخش ۵ — Red-team معماری یکپارچه (از دانش پروژه، verbatim)

# RED-TEAM — حمله به معماریِ یکپارچه
# شکستنِ `15-synthesis-unified-architecture.md` — نه تأیید، حمله

> **ورودی:** معماریِ یکپارچه (فایل ۱۵) + ۱۰ گزارشِ lane.
> **مأموریت:** این معماری را بشکن. حفره‌های هزینه، governance تئاتری، failure modeهای نادیده، فرض‌های شکسته، و وابستگی‌های پنهان را پیدا کن.
> **قاعده:** هیچ تعریفی. فقط حمله. اگر یک بخش درست است، سکوت؛ اگر شکننده است، بشکنش.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱.

---

## حکمِ کلی (اول، نه آخر)

معماری از نظرِ مهندسی منسجم است ولی سه فرضِ بنیادی دارد که هیچ‌کدام برای یک اپراتورِ تک‌نفره روی VPS مشترک برقرار نیستند:

۱. **فرض:** «داده تولید کن، بعد بساز.» — **شکسته:** داده‌ی خام بدونِ scoring برای SkillOpt بی‌فایده است، و scoring خودش زیرساختی است که هنوز نساخته‌ای. یک وابستگیِ حلقوی پنهان.

۲. **فرض:** «governance = audit + hash-chain + autonomy matrix.» — **شکسته:** این governance برای سازمان طراحی شده، نه برای یک نفر. تهدیدِ واقعیِ تو دستکاریِ log توسطِ دشمن نیست؛ نخواندنِ log توسطِ خودت است.

۳. **فرض:** «Anthropic زیرساختِ قابلِ‌اعتماد است.» — **شکسته:** گزارشِ هزینه‌ی خودت (Lane 7) مستند کرد که Anthropic دسترسی به Fable 5 را در ۱۲ ژوئن ۲۰۲۶ قطع کرد. معماری‌ای که export-first ادعا می‌کند ولی روی یک vendor که دسترسی را پس می‌گیرد بنا شده، با خودش در تناقض است.

اینها را در ادامه، مرتب‌شده بر اساسِ شدت، می‌شکنم.

---

## حمله #۱ (کشنده) — وابستگیِ حلقویِ cold-start

`[Certain]`

**ادعای معماری:** فاز ۰ = «داده تولید کن.» فاز ۴ (SkillOpt) بعداً از این داده استفاده می‌کند.

**شکستن:** SkillOpt به **scored trajectories با held-out split** نیاز دارد (خودِ Lane 10 این را گفت). ولی:
- scoring به eval layer نیاز دارد → فاز ۲
- eval layer به anchor set نیاز دارد → که از production traces دستی استخراج می‌شود
- استخراجِ anchor set نیاز به داده‌ای دارد که **قبلاً scored شده باشد** تا بدانی کدام «خوب» است

پس در فاز ۰ داری **trajectoryهای بدونِ score** تولید می‌کنی. یک انبار log بدونِ برچسب. برای SkillOpt تقریباً بی‌مصرف است.

**سناریوی شکست:** سه ماه task اجرا می‌کنی، ۵٬۰۰۰ row در LANGAR داری، بعد می‌خواهی SkillOpt راه بیندازی. کشف می‌کنی که هیچ‌کدام scored نیستند. حالا باید دستی ۵۰+ trajectory per project را بخوانی و score بدهی — کاری که در هیچ فازی بودجه‌بندی نشده. برای سه tenant = ۱۵۰+ trajectory دستی. این هفته‌ها کارِ کسل‌کننده است که معماری پنهانش کرده.

**چه کسی score می‌دهد؟** معماری هرگز جواب نمی‌دهد. «LANGAR = calibrated evidence store» فرض می‌کند calibration از جایی می‌آید. در cold-start از هیچ‌جا نمی‌آید.

**ارزان‌ترین رفع:** از **روزِ اول** یک scoring signal سبک را در gateway embed کن — حتی یک binary «آیا این task به نتیجه‌ی مطلوب رسید؟» که خودت با یک کلیک ثبت می‌کنی. بدونِ این، فاز ۰ log تولید می‌کند نه data. Score-at-write، نه score-later.

---

## حمله #۲ (کشنده) — ماینینگ بدترین اولین کاندیدای SkillOpt است، نه بهترین

`[Certain]`

**ادعای معماری:** فاز ۴، «SkillOpt روی یک tenant با objective metric (مثلاً ماینینگ backtest score).»

**شکستن:** backtest P&L بدنام‌ترین overfittable metric در کلِ کوانت است. یک skill که علیهِ داده‌ی تاریخی بهینه شود، **curve-fitting** می‌کند — الگوهای خاصِ همان بازه‌ی تاریخی را حفظ می‌کند که در آینده تکرار نمی‌شوند. این قدیمی‌ترین شکستِ معاملاتِ الگوریتمی است.

**چرا held-out gate اینجا کار نمی‌کند:** SkillOpt held-out split را از همان توزیع می‌گیرد. ولی بازارها **non-stationary** هستند — held-out تاریخی از همان دوره، همان market regime را دارد. validation gate pass می‌شود در حالی که real-world fail می‌شود. این دقیقاً «silent degradation» است که Lane 8 و Lane 10 هشدار دادند — و معماری آن را به‌عنوانِ **اولین** کاندیدای SkillOpt گذاشت.

**تضادِ درونی:** خودِ Lane 10 نوشت: «SkillOpt is most directly applicable when the target task has automatic verifiers, exact-match metrics, executable checks.» P&L یک verifier قطعی **نیست** — یک متغیرِ تصادفیِ noisy است. معماری این هشدار را نادیده گرفت.

**ارزان‌ترین رفع:** اولین کاندیدای SkillOpt باید یک task با verifier واقعاً قطعی باشد — مثلاً یک استخراجِ ساختاریافته که output آن دقیقاً درست یا غلط است (code execution، schema match، data extraction). ماینینگ باید **آخرین** دامنه باشد که SkillOpt را رویش امتحان می‌کنی، نه اول. اگر اصلاً.

---

## حمله #۳ (شدید) — پارادوکسِ HARD_STOP مالی

`[Certain]`

**ادعای معماری:** «FINANCIAL=HARD_STOP برای ماینینگ.» هر action مالی نیاز به تأییدِ انسان دارد.

**شکستن:** کلِ ارزشِ یک ماینینگ agent خودکار این است که سریع‌تر از انسان روی فرصت‌ها عمل کند. اگر هر action مالی HARD_STOP می‌شود:
- agent مستقل نیست، یک سیستمِ اعلانِ گران‌قیمت است
- مزیتِ latency (دلیلِ اصلیِ automation) از بین می‌رود
- پس چرا اصلاً automate کنی؟

**تضادِ حل‌نشده:** یا autonomous financial action با cap را می‌پذیری، یا ماینینگ را automate نمی‌کنی. معماری هر دو را می‌خواهد: هم ماینینگ tenant داشته باشد، هم همه‌ی financial actions را HARD_STOP کند. این دو با هم نمی‌سازند.

**سناریوی شکست:** یا (الف) کاربر خسته می‌شود از تأییدِ دستیِ هر trade و HARD_STOP را به AUTONOMOUS تنزل می‌دهد — که تمامِ safety layer را دور می‌زند بدونِ طراحیِ درست؛ یا (ب) ماینینگ tenant عملاً هرگز مستقل عمل نمی‌کند و یک داشبوردِ نیمه‌کاره می‌شود.

**ارزان‌ترین رفع:** به‌جای دوگانه‌ی HARD_STOP/AUTONOMOUS، یک **bounded autonomy** تعریف کن: agent می‌تواند مستقل trade کند تا سقفِ $X per action و $Y per day، هر چیزِ بالای آن HARD_STOP. این هم latency را حفظ می‌کند هم ریسک را cap می‌کند. ولی این یعنی باید بپذیری که پولِ واقعی بدونِ انسان حرکت می‌کند — تصمیمی که معماری از آن طفره رفت.

---

## حمله #۴ (شدید) — همه‌ی جاده‌ها به یک Postgresِ روی ضعیف‌ترین زیرساخت می‌رسند

`[Probable]`

**ادعای معماری:** «یک Postgres برای همه‌چیز» به‌عنوانِ برترین تصمیمِ معماری معرفی شد (بخش ۷، بینشِ #۱).

**شکستن:** روی یک Postgres، هم‌زمان اجرا می‌شوند:
- LANGAR ledger (نوشتنِ append-only در هر action)
- memory (خواندن/نوشتنِ pgvector — vector search سنگین)
- MLflow (نوشتنِ eval results)
- policy table (خواندن در هر action)
- DBOS state (نوشتن در هر consequential step)

روی VPS مشترک که Lane 0 و Lane 7 هر دو resource contention را خطرِ اصلی خواندند، این **write amplification** روی ضعیف‌ترین ممکن infra متمرکز است. pgvector search حافظه و CPU می‌خورد؛ در همان لحظه policy check منتظرِ همان connection pool است.

**نقطه‌ی شکستِ بحرانی — fail-open یا fail-closed؟** معماری می‌گوید kill switch (روی Redis) fail-closed است. ولی **policy check روی Postgres است.** اگر Postgres تحتِ فشار کند یا down شود و gateway نتواند allowlist را بخواند، چه می‌شود؟ معماری **هرگز نمی‌گوید.** اگر fail-open است (اجازه بده)، یک Postgres slowdown = دور زدنِ کلِ policy layer. اگر fail-closed است (block کن)، یک Postgres hiccup = توقفِ کلِ سیستم. این ابهام یک حفره‌ی امنیتیِ جدی است.

**سناریوی شکست:** tenant ماینینگ یک vector search سنگین روی memory می‌زند، Postgres کند می‌شود، policy check برای یک financial action timeout می‌کند، و اگر طراحی fail-open باشد، آن action بدونِ policy check اجرا می‌شود — دقیقاً روی پرخطرترین tenant.

**ارزان‌ترین رفع:** دو چیز. (۱) صریحاً policy check را **fail-closed** کن — اگر Postgres جواب نداد، action block می‌شود. (۲) policy table و kill switch را از مسیرِ داغِ pgvector جدا کن — یا policy را در Redis cache کن (خواندنِ سریع، fail-closed)، یا یک Postgres جدا برای governance از Postgresِ data. «یک Postgres برای همه» را برای governition نقض کن.

---

## حمله #۵ (شدید) — governance تئاتری برای یک نفر

`[Probable]`

**ادعای معماری:** append-only hash-chain، WORM audit، autonomy matrix چهارسطحی، تستِ ماهانه‌ی kill switch.

**شکستن — مدلِ تهدید را بپرس:** hash-chain در برابرِ **دستکاریِ log توسطِ دشمن** محافظت می‌کند. برای یک اپراتورِ تک‌نفره، دشمنی که log را دستکاری کند کیست؟ audit log برای این است که **خودت** مرورش کنی. ولی یک نفرِ مشغول که سه کسب‌وکار را می‌گرداند، هرگز audit log را نمی‌خواند.

پس:
- هزینه‌ی مهندسیِ hash-chain + WORM storage + تستِ ماهانه = واقعی و مکرر
- منفعت (محافظت در برابرِ tamperingِ دشمن) = برای مدلِ تهدیدِ یک‌نفره تقریباً صفر
- محافظتی که واقعاً نیاز داری (سقفِ خرج، dead-man's switch) = ساده‌تر و ارزان‌تر است

این ceremony در سطحِ سازمانی است روی یک سیستمِ یک‌نفره. هزینه از منفعت بیشتر است.

**تضادِ ثانویه:** تستِ ماهانه‌ی kill switch یک تعهدِ عملیاتیِ مکرر است. یک اپراتورِ تک‌نفره که فراموش می‌کند، یک kill switchِ untested دارد — که بدتر از نداشتن است چون توهمِ امنیت می‌دهد. Lane 6 خودش گفت untested kill switch = false confidence.

**ارزان‌ترین رفع:** governance را به آنچه یک نفر واقعاً استفاده می‌کند تقلیل بده:
- **سقفِ خرجِ سخت** (روزانه/هفتگی) — این واقعاً محافظت می‌کند
- **dead-man's switch** — اگر ۲۴ ساعت check-in نکردی، همه‌ی autonomous action متوقف می‌شود
- **audit log ساده** (append-only کافی است، hash-chain لازم نیست مگر یک روز چند نفره شوی)
- kill switch را **خودکار تست کن** (یک cron که ماهانه kill switch را می‌زند روی یک canary action و alert می‌دهد اگر کار نکرد) — نه یک یادآوریِ دستی که فراموش می‌شود

hash-chain را نگه دار **فقط اگر** یک روز این سیستم را به کسِ دیگری می‌فروشی یا چند-کاربره می‌کنی. تا آن روز، over-engineering است.

---

## حمله #۶ (متوسط) — وابستگیِ Anthropic که با شواهدِ خودت رد می‌شود

`[Certain]`

**ادعای معماری:** export-first، no vendor lock-in. منطقِ حیاتی از Claude Agent SDK دور نگه داشته شد.

**شکستن:** با این حال کلِ سیستم به Anthropic چسبیده:
- model routing کاملاً Anthropic است (Haiku/Sonnet/Opus)
- prompt caching (لِوِرِ اصلیِ ۹۰٪ صرفه‌جویی) Anthropic-specific است
- orchestration از Claude Cowork
- تنها non-Anthropic جزء، Gemini judge است — که خودش وابستگیِ دوم اضافه می‌کند

**شاهدِ خودت علیهِ خودت:** Lane 7 مستند کرد که Anthropic **دسترسی به Fable 5 و Mythos 5 را در ۱۲ ژوئن ۲۰۲۶ قطع کرد** (export-control). این اثباتِ زنده است که دسترسی پس گرفته می‌شود. معماری‌ای که Anthropic را زیرساختِ قابلِ‌اعتماد فرض می‌کند، در حالی که تحقیقِ خودش Anthropic را در حالِ پس‌گرفتنِ دسترسی ثبت کرده، با خودش در تناقض است.

**سناریوی شکست:** Anthropic terms را عوض می‌کند، یا یک outage دارد، یا مدلی که استفاده می‌کنی suspend می‌شود (همان‌طور که Fable 5 شد). کلِ سیستم متوقف می‌شود. «export-first» بودنِ داده کمکی نمی‌کند وقتی موتورِ اجرا در دسترس نیست.

**ارزان‌ترین رفع:** یک fallback path واقعی به یک مدلِ غیرِ Anthropic (Gemini یا یک local model روی لپ‌تاپ) برای critical operations. نه برای صرفه‌جویی — برای بقا. و prompt caching را به‌عنوانِ یک بهینه‌سازی تلقی کن که می‌تواند ناپدید شود، نه یک ستونِ بودجه. اگر ۸۰٪ صرفه‌جوییِ تو به یک لِوِرِ vendor-specific بسته است، آن صرفه‌جویی موقتی است.

---

## حمله #۷ (متوسط) — cross-model judge یک سقفِ جدید می‌سازد

`[Probable]`

**ادعای معماری:** cross-model judge (Gemini برای Claude outputs) برای رفعِ family bias.

**شکستن:** family bias را با **judge-competence risk** عوض کردی. اگر Gemini تحلیلِ ماینینگِ Claude را judge کند، محدودیت‌های خودِ Gemini در استدلالِ مالی به سقفِ کیفیت تبدیل می‌شوند. Gemini و Claude می‌توانند به‌شکلِ سیستماتیک اختلاف داشته باشند به‌گونه‌ای که «تصحیحِ bias» نیست — صرفاً دو تعریفِ متفاوت از کیفیت است.

**هزینه‌ی پنهان:** حالا روی هر eval دو مدلِ frontier می‌پردازی. برای یک اپراتورِ budget-محدود که Lane 7 برایش routing به Haiku را توصیه کرد، judge کردن با Gemini Pro روی هر eval یک هزینه‌ی مکرر است که در cost model نیامده.

**ارزان‌ترین رفع:** cross-model judge را فقط برای یک anchor set کوچک (۵۰ case) به‌صورتِ دوره‌ای استفاده کن، نه روی هر output. برای اکثرِ evalها، یک rule-based یا exact-match verifier ارزان‌تر و قطعی‌تر است. judge model را برای جایی نگه دار که واقعاً subjective است، و آنجا بپذیر که judge خودش خطا دارد.

---

## حمله #۸ (سیستمی، مهم‌ترین) — ۱۵ جزء در برابرِ یک انسان

`[Certain]`

**ادعای معماری:** معماریِ نهایی شامل: Postgres، pgvector، Mem0، DBOS، MCP gateway، OPA، Redis، OpenLLMetry، MLflow، cgroups، iptables، gVisor، LangGraph، Claude Agent SDK، SkillOpt.

**شکستن:** این ~۱۵ جزءِ متحرک است که **یک نفر** باید بسازد، نگه دارد، debug کند، و operate کند — **در حالی که هم‌زمان سه کسب‌وکارِ واقعی را می‌گرداند** (تحقیق، ماینینگ، حسابداری).

failure modeِ واقعی هیچ‌کدام از حفره‌های تکنیکیِ بالا نیست. این است: **یک اپراتورِ تک‌نفره نمی‌تواند ۱۵ سیستم را نگه دارد** و به یک استکِ نیمه‌ساخته‌ی نیمه‌نگه‌داری‌شده می‌رسد که در آن:
- governance layer کهنه شده
- kill switch هرگز تست نشده
- نصفِ observability wired نشده
- SkillOpt loop یک بار اجرا شده و رها شده

**این تنها حمله‌ای است که کلِ معماری را باطل می‌کند** — نه به‌خاطرِ اشتباهِ فنی، بلکه چون بودجه‌ی پیچیدگی از ظرفیتِ یک انسان فراتر است. معماری هرگز یک reality check از پیچیدگی در برابرِ زمانِ یک نفر انجام نداد.

**سناریوی شکست (محتمل‌ترین از همه):** سه ماهِ اول را صرفِ ساختِ foundation و gateway می‌کنی. ماهِ چهارم مشغولِ کسب‌وکارِ واقعی می‌شوی. gateway کار می‌کند ولی eval هرگز کامل wire نشد. kill switch را یک بار تست کردی. شش ماه بعد یک agent در یک loop گیر می‌کند، kill switch به‌خاطرِ یک تغییرِ کوچک کار نمی‌کند، و چون هرگز دوباره تست نشد، نمی‌دانستی. این سناریوی پیش‌فرض است، نه بدترین حالت.

**ارزان‌ترین رفع — تنها رفعِ واقعی:** معماری را به **حداقلِ قابلِ‌بقا** تقلیل بده که یک نفر بتواند نگه دارد:
- Postgres + یک gateway ساده با logging + kill switch + سقفِ خرج
- routing دستی (نه SkillOpt) تا وقتی یک tenant واقعاً سود می‌دهد
- observability = یک داشبوردِ ساده که per-task cost و success را نشان می‌دهد
- **هیچ‌کدام** از OPA/gVisor/DBOS/Mem0/LangGraph/SkillOpt تا وقتی یک درد مشخص آن‌ها را ضروری کند

هر جزء را فقط وقتی اضافه کن که **نبودش** یک مشکلِ واقعیِ اندازه‌گیری‌شده ایجاد کرده. معماریِ فعلی همه‌چیز را از قبل تجویز می‌کند؛ یک نفر باید برعکس عمل کند — از هیچ شروع کند و فقط زیرِ فشارِ واقعی اضافه کند.

---

## حمله #۹ (متوسط) — LANGAR ناظرِ خودش را ندارد

`[Probable]`

**ادعای معماری:** LANGAR سه نقشِ هم‌زمان دارد — audit log، calibrated evidence store، empirical validation. «مرکزِ همه‌چیز.»

**شکستن:** اگر calibration خودِ LANGAR غلط باشد (confidence scoreهای miscalibrated)، هر تصمیمِ downstream این miscalibration را ارث می‌برد، **و** self-improvement loop علیهِ یک سیگنالِ miscalibrated بهینه می‌شود — خطا را مضاعف می‌کند. هیچ meta-check روی calibration خودِ LANGAR نیست.

**نقطه‌ی کور مشخص:** Wilson lower bound (از سیستمِ خودت) روی **چه داده‌ای؟** در cold-start، هیچ داده = هیچ calibration = confidence scoreها در فازهای اولیه اساساً ساختگی‌اند. LANGAR در روزهای اول اعداد تولید می‌کند که هیچ پایه‌ی آماری ندارند، ولی معماری به آن‌ها به‌عنوانِ «calibrated evidence» اعتماد می‌کند.

**ارزان‌ترین رفع:** یک آستانه‌ی حداقلِ داده قبل از اینکه LANGAR score را «معتبر» اعلام کند. زیرِ N observation، LANGAR باید صریحاً بگوید «insufficient data» به‌جای یک confidence عددیِ ساختگی. و calibration خودِ LANGAR را دوره‌ای در برابرِ نتایجِ واقعی check کن (calibration plot: آیا چیزهایی که ۷۰٪ اعتماد داشتند واقعاً ۷۰٪ مواقع درست بودند؟).

---

## جمع‌بندیِ حملات — ماتریسِ شدت

| # | حمله | شدت | ریشه | آیا معماری را باطل می‌کند؟ |
|---|---|---|---|---|
| ۱ | وابستگیِ حلقویِ cold-start | کشنده | scoring پیش‌نیازِ خودش است | تأخیرِ چندماهه |
| ۲ | ماینینگ بدترین کاندیدای SkillOpt | کشنده | backtest overfitting | ضررِ مالیِ واقعی |
| ۳ | پارادوکسِ HARD_STOP مالی | شدید | autonomy vs safety | ماینینگ بی‌فایده می‌شود |
| ۴ | همه‌چیز روی یک Postgresِ ضعیف | شدید | write contention + fail-open ابهام | حفره‌ی امنیتی |
| ۵ | governance تئاتری برای یک نفر | شدید | مدلِ تهدیدِ اشتباه | هزینه > منفعت |
| ۶ | وابستگیِ Anthropic (با شواهدِ خودت) | متوسط | single vendor | توقفِ کامل ممکن |
| ۷ | cross-model judge سقفِ جدید | متوسط | judge-competence risk | هزینه‌ی پنهان |
| ۸ | **۱۵ جزء در برابرِ یک انسان** | **سیستمی** | **بودجه‌ی پیچیدگی** | **بله — تنها حمله‌ی باطل‌کننده** |
| ۹ | LANGAR ناظرِ خودش را ندارد | متوسط | miscalibration مضاعف | خطای خاموش |

---

## تنها چیزی که واقعاً باید تغییر کند

اگر از این کلِ red-team فقط یک چیز را بپذیری: **حمله‌ی #۸.**

بقیه‌ی حملات حفره‌های قابلِ‌رفع در یک معماریِ درست‌اند. حمله‌ی #۸ می‌گوید معماری برای مخاطبِ اشتباه طراحی شده. یک اپراتورِ تک‌نفره به معماریِ «درست» نیاز ندارد — به معماری‌ای نیاز دارد که **یک نفر بتواند نگه دارد**. این دو یکی نیستند.

معماریِ فعلی جوابِ «بهترین سیستمِ ممکن چیست؟» است. سؤالِ واقعی این است: «ساده‌ترین سیستمی که یک نفرِ مشغول می‌تواند بسازد، تست‌شده نگه دارد، و به آن اعتماد کند چیست؟» جوابِ آن سؤال ~۵ جزء است، نه ۱۵.

**بازطراحیِ پیشنهادیِ red-team — «حداقلِ قابلِ‌بقا»:**

```
۱. Postgres (LANGAR ledger + score-at-write)
۲. Gateway ساده: log + kill switch (Redis، fail-closed) + سقفِ خرجِ سخت + dead-man's switch
۳. routing دستی (Haiku default، Sonnet/Opus فقط دستی برای task سخت)
۴. داشبوردِ ساده: per-task cost + success/fail
۵. یک fallback model غیرِ Anthropic برای critical ops
```

هر چیزِ دیگر — OPA، gVisor، DBOS، Mem0، LangGraph، SkillOpt، hash-chain، autonomy matrix، cross-model judge — **حذف تا وقتی یک دردِ اندازه‌گیری‌شده آن را ضروری کند.** نه قبلش.

**سؤالِ فیلترِ نهایی برای هر جزء:** «آیا نبودِ این، همین الان یک مشکلِ واقعیِ اندازه‌گیری‌شده ایجاد کرده؟ اگر نه، نساز.»

---

*فایل: `16-redteam-unified-architecture.md` — حمله به synthesis. آخرین قدمِ Research Prompt Pack.*

---

# بخش ۶ — heart-awareness-map-v3.html (کد کامل)

```html
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>قلب و آگاهی — نسخه‌ی ۳ · عملی‌شده</title>
<style>
  :root{
    --bg:#0d1117; --panel:#161b22; --panel2:#1c2430; --ink:#e6edf3; --muted:#9aa7b4;
    --line:#2a3340; --accent:#ff5b6e; --accentdim:#4a1f28;
    --E:#3fb950; --Ebg:#10371b; --S:#d29922; --Sbg:#3a2d0a; --P:#a371f7; --Pbg:#2a1f44;
    --new:#58a6ff; --newbg:#0d2a4d;
    --ok:#2ea043; --okbg:#0d2a1a;
  }
  *{box-sizing:border-box}
  body{margin:0;background:radial-gradient(1200px 600px at 70% -10%,#16202e 0,var(--bg) 60%);
       color:var(--ink);font-family:"Vazirmatn","Segoe UI",Tahoma,sans-serif;line-height:1.85;padding:28px 18px 60px}
  .wrap{max-width:1080px;margin:0 auto}
  .crumb{letter-spacing:.18em;font-size:12px;color:var(--muted);text-align:center;margin-bottom:6px}
  h1{font-size:30px;text-align:center;margin:4px 0 2px;font-weight:800}
  .sub{text-align:center;color:var(--muted);font-size:15px;max-width:760px;margin:0 auto 10px}
  .v3flag{display:block;width:fit-content;margin:14px auto 26px;background:var(--okbg);color:var(--ok);
          border:1px solid #1e5e2e;border-radius:999px;padding:6px 16px;font-size:13px;font-weight:700}
  .sec{margin:34px 0 12px;display:flex;align-items:center;gap:12px}
  .sec .tag{background:var(--accentdim);color:var(--accent);border:1px solid #6b2530;border-radius:8px;
            width:34px;height:34px;display:grid;place-items:center;font-weight:800;flex:none}
  .sec h2{font-size:20px;margin:0}
  .grid{display:grid;gap:14px}
  .g2{grid-template-columns:1fr 1fr}
  .g3{grid-template-columns:1fr 1fr 1fr}
  @media(max-width:760px){.g2,.g3{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
  .card h3{margin:0 0 10px;font-size:16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .num{background:var(--panel2);border:1px solid var(--line);border-radius:7px;font-size:13px;color:var(--muted);
       padding:1px 8px;font-weight:700}
  .claim{margin:9px 0;padding-right:6px;font-size:14.5px}
  .pill{display:inline-block;font-size:11px;font-weight:800;border-radius:6px;padding:1px 7px;margin-left:5px;
        vertical-align:1px;border:1px solid}
  .E{color:var(--E);background:var(--Ebg);border-color:#1e5e2e}
  .S{color:var(--S);background:var(--Sbg);border-color:#6b531a}
  .P{color:var(--P);background:var(--Pbg);border-color:#4b357f}
  .NEW{color:var(--new);background:var(--newbg);border-color:#1f4d80}
  .FIX{color:#ff7b72;background:#3a1418;border-color:#7a2630}
  .OK{color:var(--ok);background:var(--okbg);border-color:#1e5e2e}
  .src{font-size:11.5px;color:var(--muted)}
  .src a{color:var(--new);text-decoration:none;border-bottom:1px dotted #2a4a73}
  .src a:hover{color:#8cc4ff}
  .flow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:center;
        background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:14px;margin:8px 0}
  .flow .b{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:8px 12px;font-size:13.5px}
  .arrow{color:var(--accent);font-weight:800}
  .loop{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
  .loop .when{color:var(--accent);font-weight:800;font-size:13px;margin-bottom:4px}
  .rail{background:linear-gradient(180deg,var(--panel),#13181f);border:1px solid var(--line);
        border-right:3px solid var(--accent);border-radius:12px;padding:8px 16px;margin:9px 0;font-size:14px}
  .rail-ok{background:linear-gradient(180deg,var(--panel),#13181f);border:1px solid var(--line);
        border-right:3px solid var(--ok);border-radius:12px;padding:8px 16px;margin:9px 0;font-size:14px}
  .legend{display:flex;gap:18px;flex-wrap:wrap;justify-content:center;margin:6px 0 0;color:var(--muted);font-size:13px}
  .foot{text-align:center;color:var(--muted);font-size:12px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
  .note{font-size:13px;color:var(--muted);font-style:normal;background:var(--panel2);border:1px dashed var(--line);
        border-radius:10px;padding:10px 14px;margin:10px 0}
  .srcsec{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 20px}
  .srcsec li{margin:6px 0;font-size:13px}

  /* --- practical additions --- */
  .today{background:linear-gradient(135deg,#0d2a1a,#13181f);border:2px solid var(--ok);border-radius:16px;
         padding:20px 22px;margin-bottom:24px}
  .today h2{margin:0 0 14px;font-size:19px;color:var(--ok)}
  .checklist{list-style:none;padding:0;margin:0}
  .checklist li{display:flex;align-items:flex-start;gap:10px;font-size:14.5px;margin:8px 0;padding:6px 0;
                border-bottom:1px solid #1a2a1a}
  .checklist li:last-child{border-bottom:none}
  .step-num{background:var(--ok);color:#000;border-radius:50%;width:22px;height:22px;min-width:22px;
            display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;margin-top:2px}
  .step-time{color:var(--muted);font-size:12px;white-space:nowrap;margin-top:3px}

  .proto{background:var(--panel2);border:1px solid var(--line);border-radius:10px;
         padding:10px 14px;margin:10px 0;font-size:13.5px}
  .proto .step{display:flex;gap:8px;margin:5px 0;align-items:flex-start}
  .proto .step .n{color:var(--accent);font-weight:800;min-width:18px}

  .logtable{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}
  .logtable th{background:var(--panel2);padding:7px 10px;text-align:right;color:var(--muted);
               font-weight:700;border-bottom:1px solid var(--line)}
  .logtable td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  .logtable tr:last-child td{border-bottom:none}
  .tag-e{color:var(--E)}
  .tag-s{color:var(--S)}
  .tag-m{color:var(--muted)}
</style>
</head>
<body>
<div class="wrap">
  <div class="crumb">N-OF-1 · SELF-EXPERIMENT · V3 · PRACTICAL</div>
  <h1>قلب و آگاهی — نقشه‌ی عملی</h1>
  <p class="sub">نسخه‌ی ۳: شواهد همان، پروتکل‌ها مشخص‌تر — اکنون می‌دانی هر روز دقیقاً چه کار کنی.</p>
  <span class="v3flag">✓ نسخه‌ی ۳ · بهینه‌سازی ساختار و عملی‌سازی · ژوئن ۲۰۲۶</span>

  <!-- ===================== TODAY PROTOCOL ===================== -->
  <div class="today">
    <h2>▸ امروز، همین الان — چه کار کنم؟</h2>
    <ul class="checklist">
      <li>
        <span class="step-num">۱</span>
        <div><b>قبل از کافئین و مصرف:</b> دو دقیقه ساکت بنشین، Muse را روشن کن، RMSSD را بخوان.
          <br><span class="step-time">⏱ ۲ دقیقه · صبح · پیش از هر چیز</span></div>
      </li>
      <li>
        <span class="step-num">۲</span>
        <div><b>تنفس رزونانس:</b> ۶ نفس در دقیقه (بازدم ۵ ثانیه + دم ۵ ثانیه). هر نفس را بشمار.
          <br><span class="step-time">⏱ ۱۰–۱۵ دقیقه · همان صبح</span></div>
      </li>
      <li>
        <span class="step-num">۳</span>
        <div><b>لاگ روزانه را پر کن</b> (ببین جدول پایین — فقط ۵ فیلد):
          RMSSD · خواب ۱–۵ · مصرف بله/خیر · مکان · یادداشت
          <br><span class="step-time">⏱ ۱ دقیقه · هر روز</span></div>
      </li>
      <li>
        <span class="step-num">۴</span>
        <div><b>هر هفته — ۱۰ دقیقه:</b> ۷ روز RMSSD را نگاه کن. با خواب و مصرف cross-reference کن.
          <br><span class="step-time">⏱ هفتگی · شنبه صبح</span></div>
      </li>
    </ul>
  </div>

  <!-- ===================== B : EXPERIMENTS ===================== -->
  <div class="sec"><span class="tag">B</span><h2>آزمایش‌های N-of-1 — پروتکلِ مشخص</h2></div>
  <div class="grid g2">

    <div class="card">
      <h3><span class="num">E1</span> منحنیِ autonomic</h3>
      <div class="claim"><b>سؤال:</b> نشئگی دقیقاً چطور سیستم خودکار را جابه‌جا می‌کند؟</div>
      <div class="proto">
        <div class="step"><span class="n">۱.</span> قبل از مصرف: Muse را ۲ دقیقه بخوان. <b>RMSSD و HR</b> را یادداشت کن.</div>
        <div class="step"><span class="n">۲.</span> در اوج onset (۲۰–۴۰ دقیقه بعد): دوباره ۲ دقیقه بخوان. همان فیلدها.</div>
        <div class="step"><span class="n">۳.</span> لحظه‌ای که احساس کردی اضطراب شروع شد: RMSSD آن لحظه = <b>عددِ tip-over شخصی‌ات</b>. علامت بزن.</div>
        <div class="step"><span class="n">ثبت:</span> هر سه عدد + تخمین دوز + مسیر مصرف (استنشاق / خوراکی)</div>
      </div>
      <div class="claim src">↪ همیشه RMSSD بخوان نه SDNN — چون SDNN می‌تواند بالا برود در حالی که RMSSD (واگ‌محور) تغییر نمی‌کند. <span class="pill NEW">NEW</span></div>
    </div>

    <div class="card">
      <h3><span class="num">E2</span> accuracy × confidence</h3>
      <div class="claim"><b>سؤال:</b> THC با خواندن بدن چه می‌کند؟</div>
      <div class="proto">
        <div class="step"><span class="n">۱.</span> ۱ دقیقه چشم‌ها را ببند. ضربان قلبت را بدون ساعت/نبض بشمار.</div>
        <div class="step"><span class="n">۲.</span> بعد از ۳۰ ثانیه، شمارش را بنویس. Muse را ببین — خطا را محاسبه کن.</div>
        <div class="step"><span class="n">۳.</span> روی کاغذ از ۱–۱۰ بگو: «چقدر مطمئنی که درست شمردی؟»</div>
        <div class="step"><span class="n">۴.</span> این را در دو حالت انجام بده: هوشیار و نشئه. <b>فاصله‌ی خطا − اطمینان = داده.</b></div>
        <div class="step"><span class="n">+</span> سنجه‌ی دوم: در ۱۰ ضربه‌ی متوالی، بگو کدام‌ها را «حس کردی». دقت را مقایسه کن. <span class="pill NEW">NEW</span></div>
      </div>
      <div class="claim src">↪ شمارشِ ضربان به‌تنهایی شکننده است (Ferentzi 2025) — حتماً یک سنجه‌ی دوم.</div>
    </div>

    <div class="card">
      <h3><span class="num">E3</span> تستِ زمان (tolerance)</h3>
      <div class="claim"><b>سؤال:</b> tolerance تجربه‌ات چقدر واقعی است؟</div>
      <div class="proto">
        <div class="step"><span class="n">۱.</span> یک تایمرِ ۳۰ ثانیه را راه بینداز ولی صفحه را نگاه نکن.</div>
        <div class="step"><span class="n">۲.</span> وقتی فکر کردی ۳۰ ثانیه گذشت، بزن. خطا را ثبت کن.</div>
        <div class="step"><span class="n">۳.</span> هوشیار + نشئه هر دو را انجام بده.</div>
        <div class="step"><span class="n">تفسیر:</span> خطای کم در نشئگی = tolerance واقعی → تست interoception E2 دقیق‌تر است. خطای زیاد = نتایج E2 آلوده.</div>
      </div>
    </div>

    <div class="card">
      <h3><span class="num">E4</span> retest بینش</h3>
      <div class="claim"><b>سؤال:</b> کدام بینش جان به در می‌برد؟</div>
      <div class="proto">
        <div class="step"><span class="n">۱.</span> هر «بینش» در حال نشئگی را همان لحظه با 【E】/【S】/【P】 تگ بزن و بنویس.</div>
        <div class="step"><span class="n">۲.</span> فردا صبح هوشیار دوباره بخوان. داوری کن: تأیید / رد / نامشخص.</div>
        <div class="step"><span class="n">۳.</span> فقط تأییدشده‌ها را «بینش» بنام. بقیه = «حالِ خوشایند».</div>
        <div class="step"><span class="n">لاگ:</span> تاریخ · متن بینش · تگ · داوری فردا</div>
      </div>
    </div>

    <div class="card">
      <h3><span class="num">E5</span> baselineِ خالصِ واگ <span class="pill NEW">NEW</span></h3>
      <div class="claim"><b>سؤال:</b> چه مقدار از نوسانِ HRV من THC است و چه مقدار نوسانِ روزانه‌ی طبیعی؟</div>
      <div class="proto">
        <div class="step"><span class="n">۱.</span> یک روز کاملاً بدون مصرف انتخاب کن.</div>
        <div class="step"><span class="n">۲.</span> صبح: baseline RMSSD بخوان.</div>
        <div class="step"><span class="n">۳.</span> ۱۵ دقیقه تنفس رزونانس ۶/۶ انجام بده. RMSSD بعدش را بخوان.</div>
        <div class="step"><span class="n">۴.</span> عصر: دوباره RMSSD بخوان (بدون تنفس).</div>
        <div class="step"><span class="n">تفسیر:</span> بازه‌ی روزانه‌ی RMSSD بدون THC = نویزِ طبیعی. هر چیزی بیرون از این بازه در روزهای مصرف = اثرِ THC.</div>
      </div>
      <div class="claim src">↪ بدون این baseline نمی‌توانی اثر THC را از نوسانِ روزانه جدا کنی. <span class="pill S">S</span></div>
    </div>

  </div>

  <!-- ===================== LOG TEMPLATE ===================== -->
  <div class="sec"><span class="tag">L</span><h2>قالبِ لاگِ روزانه — همین را پر کن</h2></div>
  <div class="card">
    <table class="logtable">
      <thead>
        <tr>
          <th>فیلد</th>
          <th>مقدار</th>
          <th>یادداشت</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b>تاریخ</b></td>
          <td class="tag-m">YYYY-MM-DD</td>
          <td>همیشه ثبت شود</td>
        </tr>
        <tr>
          <td><b>RMSSD</b></td>
          <td class="tag-e">عدد به ms</td>
          <td>صبح · قبل از کافئین · ۲ دقیقه</td>
        </tr>
        <tr>
          <td><b>خواب</b></td>
          <td class="tag-m">۱–۵</td>
          <td>۱=خیلی بد، ۵=عالی</td>
        </tr>
        <tr>
          <td><b>مصرف</b></td>
          <td class="tag-m">بله / خیر</td>
          <td>اگر بله: دوز و زمان تقریبی</td>
        </tr>
        <tr>
          <td><b>مکان</b></td>
          <td class="tag-m">خانه / کار</td>
          <td>بار روانیِ زمینه</td>
        </tr>
        <tr>
          <td><b>یادداشت</b></td>
          <td class="tag-s">اختیاری</td>
          <td>رویداد مهم، بینش، تگ E/S/P</td>
        </tr>
      </tbody>
    </table>
    <div class="note" style="margin-top:10px">همیشه <b>RMSSD</b> را ثبت کن، نه شاخص دیگری. اگر امروز اندازه نگرفتی، خالی بگذار — داده‌ی ناقص بهتر از داده‌ی اشتباه است.</div>
  </div>

  <!-- ===================== C : DAILY LOOP ===================== -->
  <div class="sec"><span class="tag">C</span><h2>حلقه‌ی روزمره — ریتوال · سه نقطه</h2></div>
  <div class="grid g3">
    <div class="loop">
      <div class="when">صبح · ۱۲–۱۵ دقیقه</div>
      <b>۱. baseline</b><br>Muse · ساکت · قبل از کافئین و مصرف. RMSSD + سه تگ (خواب / مصرف دیشب / مکان).<br><br>
      <b>۲. تنفس رزونانس</b><br>۶ نفس در دقیقه — دم ۵ ثانیه، بازدم ۵ ثانیه. سازنده‌ی ظرفیت، نه پُرکنِ وقت.
    </div>
    <div class="loop">
      <div class="when">حین روز · on-demand</div>
      <b>sigh دوگانه</b> هر وقت موجِ عاطفی بالا زد:<br>دو دم سریع + یک بازدم خیلی کند (۸–۱۰ ثانیه).<br><br>
      مخصوصاً: تنشِ رابطه · جمع شلوغ · قبل از یک گفتگوی مهم.
    </div>
    <div class="loop">
      <div class="when">هفتگی · ۱۰ دقیقه</div>
      <b>مرورِ ترند</b><br>خطِ ۷ روزه. انحراف‌ها را با رویدادها cross-reference کن.<br><br>
      سیگنال در <b>ترندِ چندهفته‌ای</b> است، نه در تپشِ یک روز.
    </div>
  </div>
  <div class="note">یادآوری: HRVB برای <b>افسردگی</b> اثر معنادار دارد (g=−۰.۴۱) و برای <b>HRV</b> خودش (g=+۰.۴۴). برای اضطراب/استرس در متاآنالیز راه‌دور ۲۰۲۵ نتیجه‌ی قطعی نبود. ترندِ چندهفته‌ای را معیار بگیر، نه «حالِ بهتر» یک جلسه. <span class="pill NEW">NEW</span></div>

  <!-- ===================== A : FIVE LAYERS ===================== -->
  <div class="sec"><span class="tag">A</span><h2>پنج لایه‌ی شواهد — مرجع سریع</h2></div>
  <div class="grid g2">

    <div class="card">
      <h3><span class="num">۱</span> امضای autonomic</h3>
      <div class="claim">THC dose-dependent: HR↑، HF-HRV↓، اضطراب↑. مصرف‌کننده‌ی سنگین: پاسخ blunted (tolerance) — نوسانِ کوچک = بی‌اثری نیست. <span class="pill E">E</span></div>
      <div class="claim">اثر biphasic: دوز پایین آرام، بالاتر → سمپاتیک/اضطراب. RMSSD نقطه‌ی tip-over شخصی‌ات را علامت می‌زند. <span class="pill S">S</span></div>
      <div class="claim"><b>مدل ۲۰۲۵:</b> PBPK-PD تاکی‌کاردیِ THC را کمّی کرد — جهشِ ضربان قابل‌مدل است، نه تصادفی. <span class="pill E">E</span> <span class="pill NEW">NEW</span><br><span class="src">← <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11858910/">PBPK-PD model of THC & heart rate, 2025</a></span></div>
      <div class="claim"><b>نکته‌ی ظریفِ taVNS ۲۰۲۵:</b> پارامترهای خاص SDNN (HRV کلی) را بالا بردند ولی RMSSD (واگ‌محور) تغییر نکرد. دلیل: کاهشِ سمپاتیک، نه افزایشِ پاراسمپاتیک. یعنی «HRV بالا» لزوماً «واگ قوی‌تر» نیست. <span class="pill E">E</span> <span class="pill NEW">NEW</span><br><span class="src">← <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11940630/">taVNS frequency × pulse-width RCT, 2025</a></span></div>
    </div>

    <div class="card">
      <h3><span class="num">۲</span> interoception</h3>
      <div class="claim">دقتِ interoceptive هدفِ توست؛ همانی که با مصرف مزمن کاهش می‌یابد (insula). <span class="pill E">E</span></div>
      <div class="claim">تستِ شمارش ضربان معیوب است: با دانستنِ HR و تخمینِ زمان «تقلب» می‌شود، r≈.16. <span class="pill E">E</span></div>
      <div class="claim">THC زمان را کش می‌دهد → شمارش را آلوده می‌کند؛ ولی در تو blunted است → قابل سنجش. <span class="pill E">E</span></div>
      <div class="claim"><b>Ferentzi 2025:</b> سه سنجه‌ی دقتِ قلبی هم‌پوشانی محدودی دارند — شمارشِ ضربان به‌تنهایی شکننده است. یک سنجه‌ی دوم لازم است. <span class="pill E">E</span> <span class="pill NEW">NEW</span><br><span class="src">← <a href="https://onlinelibrary.wiley.com/doi/10.1111/psyp.70078">Ferentzi et al., 2025, Psychophysiology</a></span></div>
      <div class="claim">فاصله‌ی accuracy (خطا) و confidence (حس) = توهمِ بینش در سطحِ بدن. <span class="pill P">P</span></div>
    </div>

    <div class="card">
      <h3><span class="num">۳</span> خودتنظیمی (HRVB)</h3>
      <div class="claim">برای <b>افسردگی</b>: اثرِ معنادار در متاآنالیز راه‌دور ۲۰۲۵ (g=−۰.۴۱). برای <b>HRV</b> خودش: g=+۰.۴۴. برای اضطراب/استرس: نتیجه قطعی نبود. <span class="pill S">S</span> <span class="pill NEW">NEW</span><br><span class="src">← <a href="https://link.springer.com/article/10.1007/s10484-025-09750-w">Remote HRVB meta-analysis, 2025</a></span></div>
      <div class="claim">مکانیسم: تنفس آهسته → افرنتِ واگ → PFC، amygdala، insula. <span class="pill E">E</span></div>
      <div class="claim">درمان نیست؛ یک training است. اثر متوسط، ناهمگن. <span class="pill S">S</span></div>
    </div>

    <div class="card">
      <h3><span class="num">۴</span> پیوندِ BPD</h3>
      <div class="claim">vagal tone پایین‌تر با BPD همبسته است؛ HRV g=−۰.۵۹، بایومارکرِ فرا-تشخیصی. <span class="pill E">E</span></div>
      <div class="claim">مکانیسم: ضعفِ کنترل مهاریِ PFC روی amygdala (neurovisceral integration). <span class="pill E">E</span></div>
      <div class="claim">DBT ضربانِ بالای BPD را نرمال می‌کند → اهرم‌های فیزیولوژیک آشنا. <span class="pill E">E</span></div>
      <div class="claim"><b>N-of-1 پشتوانه:</b> HRVِ پایه می‌تواند پیش‌بینی‌کننده‌ی پاسخِ فردی به تحریک واگ باشد. <span class="pill S">S</span> <span class="pill NEW">NEW</span><br><span class="src">← <a href="https://www.nature.com/articles/s41398-025-03780-y">«The heart knows best», Translational Psychiatry, 2025</a></span></div>
    </div>

  </div>

  <div class="grid" style="margin-top:14px">
    <div class="card">
      <h3><span class="num">۵</span> epistemologyِ بینش</h3>
      <div class="claim">حسِ بینش نویزِ محض نیست: برای مسائلِ قابل‌بررسی، با درستی همبسته است. <span class="pill E">E</span></div>
      <div class="claim">اما قابل هک است — «Dark side of Eureka»: حسِ aha می‌تواند گزاره‌ی دلخواه را «درست» جلوه دهد. <span class="pill E">E</span></div>
      <div class="claim">برای مسائلِ باز/خلاق، حسِ پیشرفت اعتبار را پیش‌بینی نمی‌کند. <span class="pill E">E</span></div>
      <div class="claim">بینشِ نشئه = بدترین حالت (باز + آزمونِ تغییریافته). حال ≠ مقام — retest، تبدیل است. <span class="pill P">P</span></div>
    </div>
  </div>

  <div class="note"><b>تصحیح مهم — Kaduk 2025 <span class="pill FIX">FIX</span></b><br>
  taVNS، HRV را <b>مستقل از بار کالری</b> کاهش می‌دهد. Milkshake اثر معناداری نداشت. «غذا روی واگ» ادعای پشتیبانی‌نشده است. به‌علاوه: یافته‌ی ۲۰۲۵ نشان داد کاهشِ HRV از مسیرِ سمپاتیک است، نه واگ — پس «تحریکِ واگ = HRV بالا» فرمولِ ساده‌شده‌ای است که همیشه صادق نیست.</div>

  <div class="flow" style="margin-top:18px">
    <div class="b">کش زمان · افتِ accuracy · THC</div>
    <span class="arrow">← کندکردن</span>
    <div class="b" style="border-color:var(--accent)">قلب: نقطه‌ای که هر دو نیرو دیده می‌شوند</div>
    <span class="arrow">ساختن →</span>
    <div class="b">تنفس رزونانس · توجهِ بدنی · biofeedback</div>
  </div>

  <!-- ===================== D : GUARDRAILS ===================== -->
  <div class="sec"><span class="tag">D</span><h2>دیسیپلینِ معرفتی — گاردریل</h2></div>
  <div class="legend">
    <span><span class="pill E">E</span> Established — علمِ مستحکم</span>
    <span><span class="pill S">S</span> Speculation — حدس/موردِ مناقشه</span>
    <span><span class="pill P">P</span> Metaphor — نگاشتِ مفهومی</span>
    <span><span class="pill NEW">NEW</span> افزوده‌ی v3</span>
  </div>
  <div style="margin-top:12px">
    <div class="rail">▸ سیگنال در ترندِ چندهفته‌ای است، نه در تپشِ امروز. PPGِ Muse نویزی است؛ تک‌روزها را جدی نگیر.</div>
    <div class="rail">▸ هدف mastery و کالیبراسیون است، نه surveillance. دستگاه یک calibrator است، نه عصا.</div>
    <div class="rail">▸ اگر ردیابی اضطراب تولید کرد، عقب بکش. علامتِ تنظیم است، نه شکست.</div>
    <div class="rail">▸ HRV ابزارِ تشخیص پزشکی نیست. علامتِ واقعیِ قلبی → cardiology، نه اپ.</div>
    <div class="rail-ok">▸ <b>گاردریلِ کلیدی:</b> همیشه RMSSD را گزارش کن. SDNN و RMSSD می‌توانند خلافِ هم حرکت کنند — مقایسه‌ی آن‌ها خودش منبعِ توهم است. <span class="pill NEW">NEW</span></div>
    <div class="rail-ok">▸ <b>گاردریلِ تازه:</b> قبل از اینکه نوسانی را به THC نسبت دهی، baseline خالصِ E5 را داشته باش. بدون baseline، نمی‌دانی چه چیزی از کجا است. <span class="pill NEW">NEW</span></div>
  </div>

  <!-- ===================== SOURCES ===================== -->
  <div class="sec"><span class="tag">★</span><h2>منابع</h2></div>
  <div class="srcsec">
    <ul>
      <li>Kaduk et al., 2025 — <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11862327/">Non-Invasive Auricular Vagus Nerve Stimulation Decreases HRV Independent of Caloric Load</a> · <i>Psychophysiology</i> — پایه‌ی تصحیح</li>
      <li>THC heart-rate PBPK-PD model, 2025 — <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11858910/">Quantifying Heart Rate Changes After Δ9-THC Administration</a> · <i>Pharmaceutics</i></li>
      <li>taVNS frequency × pulse-width RCT, 2025 — <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11940630/">Acute Effects of Varying Frequency and Pulse Width of taVNS on HRV</a></li>
      <li>Ferentzi et al., 2025 — <a href="https://onlinelibrary.wiley.com/doi/10.1111/psyp.70078">Cardiac Interoceptive Accuracy: Comparison of Three Ability Measures</a> · <i>Psychophysiology</i></li>
      <li>Remote HRV-biofeedback meta-analysis, 2025 — <a href="https://link.springer.com/article/10.1007/s10484-025-09750-w">Efficacy of Remote HRV Biofeedback for Mental Health</a> · <i>Appl. Psychophysiol. Biofeedback</i></li>
      <li>«The heart knows best», 2025 — <a href="https://www.nature.com/articles/s41398-025-03780-y">Baseline HRV as guide to taVNS in depression</a> · <i>Translational Psychiatry</i></li>
      <li>روش‌شناسی — <a href="https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.00213/full">HRV & Cardiac Vagal Tone — Recommendations for Experiment Planning</a> · Frontiers in Psychology</li>
    </ul>
  </div>

  <div class="foot">قلب و آگاهی · v3 · بهینه‌سازی ساختار و عملی‌سازی · ژوئن ۲۰۲۶<br>
  تغییرات v3: پروتکل‌های مشخص برای E1–E5 · قالبِ لاگ · تصحیح HRVB (افسردگی معنادار) · مکانیسمِ taVNS (سمپاتیک نه واگ)</div>
</div>
</body>
</html>
```

---

# بخش ۷ — heart-awareness-map-v2.html (کد کامل، نسخه‌ی قبلی)

```html
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>قلب و آگاهی — نقشه‌ی پژوهش · v2</title>
<style>
  :root{
    --bg:#0d1117; --panel:#161b22; --panel2:#1c2430; --ink:#e6edf3; --muted:#9aa7b4;
    --line:#2a3340; --accent:#ff5b6e; --accentdim:#4a1f28;
    --E:#3fb950; --Ebg:#10371b; --S:#d29922; --Sbg:#3a2d0a; --P:#a371f7; --Pbg:#2a1f44;
    --new:#58a6ff; --newbg:#0d2a4d;
  }
  *{box-sizing:border-box}
  body{margin:0;background:radial-gradient(1200px 600px at 70% -10%,#16202e 0,var(--bg) 60%);
       color:var(--ink);font-family:"Vazirmatn","Segoe UI",Tahoma,sans-serif;line-height:1.85;padding:28px 18px 60px}
  .wrap{max-width:1080px;margin:0 auto}
  .crumb{letter-spacing:.18em;font-size:12px;color:var(--muted);text-align:center;margin-bottom:6px}
  h1{font-size:30px;text-align:center;margin:4px 0 2px;font-weight:800}
  .sub{text-align:center;color:var(--muted);font-size:15px;max-width:760px;margin:0 auto 10px}
  .v2flag{display:block;width:fit-content;margin:14px auto 26px;background:var(--newbg);color:var(--new);
          border:1px solid #1f4d80;border-radius:999px;padding:6px 16px;font-size:13px;font-weight:700}
  .sec{margin:34px 0 12px;display:flex;align-items:center;gap:12px}
  .sec .tag{background:var(--accentdim);color:var(--accent);border:1px solid #6b2530;border-radius:8px;
            width:34px;height:34px;display:grid;place-items:center;font-weight:800;flex:none}
  .sec h2{font-size:20px;margin:0}
  .grid{display:grid;gap:14px}
  .g2{grid-template-columns:1fr 1fr}
  .g3{grid-template-columns:1fr 1fr 1fr}
  @media(max-width:760px){.g2,.g3{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
  .card h3{margin:0 0 10px;font-size:16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .num{background:var(--panel2);border:1px solid var(--line);border-radius:7px;font-size:13px;color:var(--muted);
       padding:1px 8px;font-weight:700}
  .claim{margin:9px 0;padding-right:6px;font-size:14.5px}
  .pill{display:inline-block;font-size:11px;font-weight:800;border-radius:6px;padding:1px 7px;margin-left:5px;
        vertical-align:1px;border:1px solid}
  .E{color:var(--E);background:var(--Ebg);border-color:#1e5e2e}
  .S{color:var(--S);background:var(--Sbg);border-color:#6b531a}
  .P{color:var(--P);background:var(--Pbg);border-color:#4b357f}
  .NEW{color:var(--new);background:var(--newbg);border-color:#1f4d80}
  .FIX{color:#ff7b72;background:#3a1418;border-color:#7a2630}
  .src{font-size:11.5px;color:var(--muted)}
  .src a{color:var(--new);text-decoration:none;border-bottom:1px dotted #2a4a73}
  .src a:hover{color:#8cc4ff}
  .flow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:center;
        background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:14px;margin:8px 0}
  .flow .b{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:8px 12px;font-size:13.5px}
  .arrow{color:var(--accent);font-weight:800}
  .loop{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
  .loop .when{color:var(--accent);font-weight:800;font-size:13px;margin-bottom:4px}
  .rail{background:linear-gradient(180deg,var(--panel),#13181f);border:1px solid var(--line);
        border-right:3px solid var(--accent);border-radius:12px;padding:8px 16px;margin:9px 0;font-size:14px}
  .legend{display:flex;gap:18px;flex-wrap:wrap;justify-content:center;margin:6px 0 0;color:var(--muted);font-size:13px}
  .foot{text-align:center;color:var(--muted);font-size:12px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
  .note{font-size:13px;color:var(--muted);font-style:normal;background:var(--panel2);border:1px dashed var(--line);
        border-radius:10px;padding:10px 14px;margin:10px 0}
  .srcsec{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 20px}
  .srcsec li{margin:6px 0;font-size:13px}
</style>
</head>
<body>
<div class="wrap">
  <div class="crumb">N-OF-1 · SELF-EXPERIMENT · V2</div>
  <h1>قلب و آگاهی — نقشه‌ی پژوهش</h1>
  <p class="sub">سنجشِ همزمانِ ذهن، بدن، و اعتبارِ بینش — و خواندنِ ضربان قلب به‌عنوان آینه‌ی اینکه ماریجوانا با همان قوه‌ای که می‌خواهم تمرینش کنم (interoception) چه می‌کند.</p>
  <span class="v2flag">↻ نسخه‌ی ۲ — به‌روزرسانی شواهد ۲۰۲۵–۲۰۲۶ · با تگ E/S/P و منبع · بدون ادعای پزشکی/تشخیصی جدید</span>

  <div class="note"><b>تصحیح مهم نسبت به نسخه‌ی قبل و به پرامپت‌پک <span class="pill FIX">FIX</span></b><br>
  در نسخه‌ی قبلی فرض شده بود «مطالعه‌ی Kaduk 2025 نشان داد بار کالری، HF-HRV و RMSSD را کاهش می‌دهد — یعنی غذا روی واگ اثر می‌گذارد». این برعکسِ یافته‌ی واقعی مقاله است. عنوان و نتیجه‌ی مقاله: «تحریک واگ گوشی (taVNS)، HRV را <b>مستقل از بار کالری</b> کاهش می‌دهد». یعنی milkshake اثر معناداری نداشت؛ آنچه RMSSD و HF-HRV را پایین آورد، خودِ تحریک واگ بود — که خودش هم خلافِ انتظارِ ساده‌ی «واگ بالا = HRV بالا» است. ادعای «غذا روی واگ» پشتیبانی نمی‌شود.</div>

  <!-- ===================== A : FIVE LAYERS ===================== -->
  <div class="sec"><span class="tag">A</span><h2>پنج لایه‌ی یافته — شواهد + تگِ معرفتی</h2></div>
  <div class="grid g2">

    <div class="card">
      <h3><span class="num">۱</span> امضای autonomic</h3>
      <div class="claim">THC به‌صورت dose-dependent: HR↑، HF-HRV↓، اضطراب↑ — مسیرِ CB1. برای مصرف‌کننده‌ی سنگین پاسخ blunted است (tolerance) — پس نوسانِ تو کوچک خواهد بود. نبودِ جهش ≠ بی‌اثری. <span class="pill E">E</span></div>
      <div class="claim">اثر biphasic: دوزِ پایین آرام، بالاتر → سمپاتیک/اضطراب. HRV نقطه‌ی tip-overِ شخصی‌ات را علامت می‌زند. <span class="pill S">S</span></div>
      <div class="claim"><b>تازه:</b> مدلِ PBPK-PD سال ۲۰۲۵ تاکی‌کاردیِ ناشی از Δ9-THC را کمّی کرد و منحنیِ HR↑ را به غلظتِ پلاسما گره زد — یعنی «جهشِ ضربان» قابل‌مدل و قابل‌انتظار است، نه تصادفی. <span class="pill E">E</span> <span class="pill NEW">NEW</span><br><span class="src">منبع: <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11858910/">PBPK-PD model of THC & heart rate, 2025 (PMC)</a></span></div>
      <div class="claim"><b>تازه — نکته‌ی ظریف:</b> در یک RCTِ crossover، فرکانس/پالس‌ویدثِ خاصِ taVNS «HRV کلی» را بالا برد ولی «HRVِ واگ‌محور» را نه. یعنی همه‌ی شاخص‌های HRV یک‌چیز را نمی‌گویند — باید مشخص کنی RMSSD/HF (واگ‌محور) را می‌خوانی یا شاخص کلی. <span class="pill E">E</span> <span class="pill NEW">NEW</span><br><span class="src">منبع: <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11940630/">taVNS frequency × pulse-width RCT, 2025 (PMC)</a></span></div>
    </div>

    <div class="card">
      <h3><span class="num">۲</span> interoception</h3>
      <div class="claim">دقتِ interoceptive هدفِ تو است؛ همان قوه‌ای که با مصرف مزمن کاهش می‌یابد (insula). <span class="pill E">E</span></div>
      <div class="claim">تستِ شمارش ضربان (Schandry) معیوب است: با دانستنِ HR و تخمینِ زمان «تقلب» می‌شود، r≈.16. <span class="pill E">E</span></div>
      <div class="claim">THC زمان را کش می‌دهد → شمارش را آلوده می‌کند. ولی در تو blunted است → قابل سنجش. <span class="pill E">E</span></div>
      <div class="claim"><b>تازه:</b> مقاله‌ی Ferentzi 2025 (Psychophysiology) سه سنجه‌ی دقتِ قلبی را تجربی مقایسه کرد و نشان داد این سنجه‌ها هم‌پوشانیِ محدودی دارند و شمارش ضربان به‌تنهایی شکننده است — مستقیماً به اعتبارِ E2/E3 تو مربوط است: حتماً یک سنجه‌ی دوم (مثلاً تشخیص هم‌زمانی ضربان) کنارش بگذار. <span class="pill E">E</span> <span class="pill NEW">NEW</span><br><span class="src">منبع: <a href="https://onlinelibrary.wiley.com/doi/10.1111/psyp.70078">Ferentzi et al., 2025, Psychophysiology</a></span></div>
      <div class="claim">فاصله‌ی accuracy (خطا) و confidence (حس) = توهمِ بینش، اما در سطحِ بدن. <span class="pill P">P</span></div>
    </div>

    <div class="card">
      <h3><span class="num">۳</span> خودتنظیمی (HRVB)</h3>
      <div class="claim">biofeedback روی اضطراب/استرس: در متاآنالیزهای قدیمی‌تر اثرِ بزرگ گزارش شده بود (g≈0.83)؛ افسردگی متوسط (g≈0.38). <span class="pill S">S</span></div>
      <div class="claim">مکانیسم: تنفس آهسته → afferentهای واگ → PFC، amygdala، insula (شبیه vagal nerve stimulation). <span class="pill E">E</span></div>
      <div class="claim"><b>تازه — تنزلِ احتیاطی:</b> متاآنالیزِ ۲۰۲۵ روی HRVBِ راه‌دور (۱۸ مطالعه، ۱۳۵۲ نفر) برای اضطراب و استرس <b>بی‌نتیجه</b> بود؛ شواهدِ قوی فقط برای بهبودِ خودِ HRV و تا حدی افسردگی ماند. پس عددِ «g≈0.83» را به یک ادعای محتاطِ [S] تنزل بده — اثر هست ولی بزرگیِ آن در شرایطِ خودسنجیِ راه‌دور (دقیقاً سناریوی تو) نامطمئن است. <span class="pill S">S</span> <span class="pill NEW">NEW</span><br><span class="src">منبع: <a href="https://link.springer.com/article/10.1007/s10484-025-09750-w">Remote HRV-biofeedback meta-analysis, 2025 (Appl. Psychophysiol. Biofeedback)</a></span></div>
      <div class="claim">درمان نیست؛ اثر متوسط، ناهمگن. یک training است، نه جادو. <span class="pill S">S</span></div>
    </div>

    <div class="card">
      <h3><span class="num">۴</span> پیوندِ BPD</h3>
      <div class="claim">آنچه «BPD خفیف» نامیدی با vagal tone پایین‌تر همبسته است؛ HRV = g≈-0.59، بایومارکرِ فرا-تشخیصی. <span class="pill E">E</span></div>
      <div class="claim">مکانیسم: ضعفِ کنترلِ مهاریِ prefrontal روی amygdala (neurovisceral integration). <span class="pill E">E</span></div>
      <div class="claim">DBT ضربانِ بالای BPD را نرمال می‌کند → اهرم‌های فیزیولوژیکِ آشنا. <span class="pill E">E</span></div>
      <div class="claim">یافته‌ها ناهمگن‌اند؛ قطعی و جبری نیست. این یک لنز است، نه برچسب. <span class="pill S">S</span></div>
      <div class="claim"><b>تازه — پشتوانه‌ی N-of-1:</b> مقاله‌ی Nature 2025 («قلب بهتر می‌داند») نشان داد HRVِ پایه می‌تواند پیش‌بینی‌کننده‌ی پاسخِ فرد به تحریک واگ باشد — یعنی شخصی‌سازی بر اساس baselineِ خودت (هسته‌ی روشِ N-of-1) شواهدِ نوظهور دارد. <span class="pill S">S</span> <span class="pill NEW">NEW</span><br><span class="src">منبع: <a href="https://www.nature.com/articles/s41398-025-03780-y">«The heart knows best», Translational Psychiatry, 2025</a></span></div>
    </div>

  </div>

  <div class="grid" style="margin-top:14px">
    <div class="card">
      <h3><span class="num">۵</span> epistemologyِ بینش</h3>
      <div class="claim">حسِ بینش نویزِ محض نیست: برای مسائلِ قابل‌بررسی (معما)، با درستی همبسته است. <span class="pill E">E</span></div>
      <div class="claim">اما قابلِ هک است — «Dark side of Eureka»: حسِ aha می‌تواند گزاره‌ی دلخواه را «درست» جلوه دهد. <span class="pill E">E</span></div>
      <div class="claim">برای مسائلِ باز/خلاق، حسِ پیشرفت اعتبار را پیش‌بینی نمی‌کند — فرایند پنهان است. <span class="pill E">E</span></div>
      <div class="claim">بینشِ نشئه = بدترین حالت (باز + آزمونِ تغییریافته). حال ≠ مقام — retest، تبدیل است. <span class="pill P">P</span></div>
    </div>
  </div>

  <div class="flow" style="margin-top:18px">
    <div class="b">کش زمان · افتِ accuracy · THC</div>
    <span class="arrow">← کندکردن</span>
    <div class="b" style="border-color:var(--accent)">قلب: نقطه‌ای که هر دو نیرو دیده می‌شوند</div>
    <span class="arrow">ساختن →</span>
    <div class="b">تنفس رزونانس · توجهِ بدنی · biofeedback</div>
  </div>
  <div class="note">هسته‌ی پارادوکس: می‌خواهم توانِ خواندنِ سیگنالِ درونی‌ام را بسازم، در حالتی که THC دقیقاً همان توان را موقتاً کند می‌کند. این یک باگ نیست — این خودِ آزمایش است.</div>

  <!-- ===================== B : EXPERIMENTS ===================== -->
  <div class="sec"><span class="tag">B</span><h2>آزمایش‌های N-of-1 — قابلِ تکرار · قابلِ لاگ</h2></div>
  <div class="grid g2">
    <div class="card">
      <h3>E1 — منحنیِ autonomic</h3>
      <div class="claim">نشئگی چطور سیستمِ خودکار را جابه‌جا می‌کند؟ HRV را در سه نقطه بخوان: هوشیار → onset → peak. لحظه‌ی tip-over و عددِ HRVِ آن لحظه را علامت بزن — این early-warningِ ایمنیِ توست.</div>
      <div class="claim src">↪ تطبیق با شواهدِ تازه: مشخص کن RMSSD/HF (واگ‌محور) را ثبت می‌کنی، نه شاخص کلی — چون این دو در taVNS متفاوت رفتار کردند. <span class="pill NEW">NEW</span></div>
    </div>
    <div class="card">
      <h3>E2 — accuracy × confidence</h3>
      <div class="claim">ماریجوانا با خواندنِ بدن چه می‌کند؟ هم خطای شمارش ضربان (accuracy) و هم میزان اطمینانت (confidence) را ثبت کن — هوشیار vs نشئه. فاصله‌ی این دو، خودِ دیتاست.</div>
      <div class="claim src">↪ تطبیق: شمارش ضربان به‌تنهایی شکننده است (Ferentzi 2025) — یک سنجه‌ی دومِ interoceptive کنارش بگذار. <span class="pill NEW">NEW</span></div>
    </div>
    <div class="card">
      <h3>E3 — تستِ زمان</h3>
      <div class="claim">آیا tolerance واقعاً برقرار است؟ یک بازه‌ی ۳۰ ثانیه‌ای را بدون ساعت تخمین بزن — هوشیار vs نشئه. اگر خطایت کم بماند، tolerance تأیید می‌شود؛ یعنی تستِ ضربانت کمتر از یک مبتدیِ آلوده است.</div>
    </div>
    <div class="card">
      <h3>E4 — retest بینش</h3>
      <div class="claim">کدام بینش جان به در می‌برد؟ هر «بینش»ِ نشئه را همان‌جا با 【E】/【S】/【P】 تگ بزن و فردای هوشیار دوباره داوری کن. بازمانده‌ها = مقام؛ بقیه = حالِ خوشایند.</div>
    </div>
  </div>
  <div class="note"><b>پیشنهادِ E5 (شکافِ تازه):</b> با توجه به اینکه taVNS در Kaduk 2025 خودش HRV را پایین آورد و در RCTِ فرکانس، اثرش به نوعِ شاخص وابسته بود — یک آزمایشِ کنترلیِ ساده اضافه کن: یک روزِ کاملاً هوشیار + تنفس رزونانس بدون مصرف، تا «منحنیِ پایه‌ی واگِ خودت» را جدا از THC ثبت کنی. بدونِ این baseline، نمی‌توانی اثرِ THC را از نوسانِ روزانه‌ی HRV جدا کنی. <span class="pill S">S</span> <span class="pill NEW">NEW</span></div>

  <!-- ===================== C : DAILY LOOP ===================== -->
  <div class="sec"><span class="tag">C</span><h2>حلقه‌ی روزمره — یک ریتوال · پنجره‌ی پاکِ صبح</h2></div>
  <div class="grid g3">
    <div class="loop"><div class="when">صبح · ۲ دقیقه</div>اندازه‌گیریِ baseline. Muse، ساکن، قبل از مصرف و کافئین. RMSSD + ۳ تگ (مصرف دیشب / خانه‌یاکار / خواب).</div>
    <div class="loop"><div class="when">بلافاصله · ۱۰–۱۵ د</div>تنفس رزونانس ۵/۵، ۶ نفس در دقیقه. سازنده‌ی ظرفیت. فرکانسِ شخصی را بعداً کالیبره می‌کنیم.</div>
    <div class="loop"><div class="when">حین روز · on-demand</div>sigh / بازدمِ کشیده هر وقت موجِ عاطفی بالا زد (مخصوصاً در رابطه). circuit-breakerِ فیزیولوژیک.</div>
  </div>
  <div class="loop" style="margin-top:14px"><div class="when">هفتگی · مرورِ ترند</div>خطِ ۷ روزه. انحراف‌ها را با رویدادها (خواب/مصرف/بار/رابطه) cross-reference کن. <span class="src">↪ یادآوریِ تازه: HRVBِ راه‌دور برای اضطراب در متاآنالیز ۲۰۲۵ بی‌نتیجه بود — پس ترندِ چندهفته‌ای را معیار بگیر، نه «حالِ بهترِ» یک جلسه. <span class="pill NEW">NEW</span></span></div>

  <!-- ===================== D : GUARDRAILS ===================== -->
  <div class="sec"><span class="tag">D</span><h2>دیسیپلینِ معرفتی و مرزها — گاردریل</h2></div>
  <div class="legend">
    <span><span class="pill E">E</span> Established — علمِ مستحکم</span>
    <span><span class="pill S">S</span> Speculation — حدس/موردِ مناقشه</span>
    <span><span class="pill P">P</span> Metaphor — نگاشتِ مفهومی، نه فیزیک</span>
    <span><span class="pill NEW">NEW</span> افزوده‌ی v2 ۲۰۲۵–۲۰۲۶</span>
  </div>
  <div style="margin-top:12px">
    <div class="rail">▸ سیگنال در ترندِ چندهفته‌ای است، نه در تپشِ امروز. PPGِ Muse نویزی است؛ تک‌روزها را جدی نگیر.</div>
    <div class="rail">▸ هدف mastery و کالیبراسیون است، نه surveillanceِ مضطربانه. دستگاه یک calibratorِ interoception است، نه عصای دائمی.</div>
    <div class="rail">▸ اگر ردگیری به‌جای بینش، اضطراب تولید کرد — همین خودش دیتاست: عقب بکش. این علامتِ شکست نیست، علامتِ تنظیم است.</div>
    <div class="rail">▸ HRV ابزارِ تشخیص پزشکی نیست. علامتِ واقعیِ قلبی → cardiology، نه اپ.</div>
    <div class="rail">▸ اتصال به Orchestrator: RMSSD-00ِ صبح = ورودیِ عینی کنارِ لایه‌ی intuition. عدد سخت‌تر از حس گول می‌خورد.</div>
    <div class="rail">▸ <b>گاردریلِ تازه:</b> یک شاخصِ HRV را قفل کن و همان را همیشه گزارش کن (پیشنهاد: RMSSD). نتایج ۲۰۲۵ نشان داد شاخص‌های مختلف HRV می‌توانند خلافِ هم حرکت کنند — مقایسه‌ی سیب‌وپرتقال، خودش منبعِ توهم است. <span class="pill NEW">NEW</span></div>
  </div>

  <!-- ===================== SOURCES ===================== -->
  <div class="sec"><span class="tag">★</span><h2>منابع — شواهدِ تازه‌ی v2</h2></div>
  <div class="srcsec">
    <ul>
      <li>Kaduk et al., 2025 — <a href="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11862327/">Non-Invasive Auricular Vagus Nerve Stimulation Decreases Heart Rate Variability Independent of Caloric Load</a> · <i>Psychophysiology</i> — <b>پایه‌ی تصحیح بالا</b></li>
      <li>THC heart-rate PBPK-PD model, 2025 — <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11858910/">Quantifying Heart Rate Changes After Δ9-THC Administration</a> (لایه ۱)</li>
      <li>taVNS frequency × pulse-width RCT, 2025 — <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11940630/">Acute Effects of Varying Frequency and Pulse Width of taVNS on HRV</a> (لایه ۱)</li>
      <li>Ferentzi et al., 2025 — <a href="https://onlinelibrary.wiley.com/doi/10.1111/psyp.70078">Cardiac Interoceptive Accuracy: Comparison of Three Ability Measures</a> · <i>Psychophysiology</i> (لایه ۲ / E2-E3)</li>
      <li>Remote HRV-biofeedback meta-analysis, 2025 — <a href="https://link.springer.com/article/10.1007/s10484-025-09750-w">Efficacy of Remote HRV Biofeedback for Mental Health</a> · <i>Appl. Psychophysiol. Biofeedback</i> (لایه ۳)</li>
      <li>«The heart knows best», 2025 — <a href="https://www.nature.com/articles/s41398-025-03780-y">Baseline HRV as guide to taVNS in depression</a> · <i>Translational Psychiatry</i> (لایه ۴ / N-of-1)</li>
      <li>روش‌شناسی (مرجعِ پایدار) — <a href="https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.00213/full">HRV & Cardiac Vagal Tone — Recommendations for Experiment Planning</a> · Frontiers in Psychology</li>
    </ul>
  </div>

  <div class="foot">قلب و آگاهی · v2 · به‌روزرسانیِ شواهد ۲۰۲۵–۲۰۲۶ · ساختهٔ مشترک — آماده برای رونویسی روی وایت‌برد<br>
  هیچ ادعای پزشکی یا تشخیصیِ جدیدی اضافه نشده؛ فقط لایه‌های شواهد تازه و یک تصحیح علامت‌گذاری شده‌اند.</div>
</div>
</body>
</html>
```

---

*پایان export — AI FARM · ۲۰۲۶-۰۷-۰۲*
