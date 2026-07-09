---
tags: [decisions, architect, log]
created: 2026-07-03
---

# DECISIONS — لاگ تصمیم‌ها و حل تناقض‌ها

> خروجی فاز ۳ [[PROMPT-A-absorb-synthesize]]. قانون: **کد واقعی > سند جدیدتر > سند قدیمی‌تر**. هیچ تناقضی بی‌صدا حل نشده. Append-only — تصمیم جدید اضافه کن، قدیمی را حذف نکن.

| ID | تصمیم | تناقض/گزینه‌ها | قانون حل | منبع |
|----|--------|----------------|-----------|-------|
| D-01 | «رئیس کل» = **انسان**؛ نرم‌افزار فقط پیشنهاد می‌دهد | [[PROJECT]] رئیس کل را ماژول نرم‌افزاری می‌خواند؛ چت مادر در نهایت انسان را gatekeeper کرد («کلید اجرا همیشه دست انسان») | سند جدیدتر (2026-06+) > قدیمی‌تر | [[architect-chat-export]] ~خط 6751 |
| D-02 | معماری **۵ جزء core**، نه ~۱۵ | معماری کامل ۱۵جزئی vs red-team: «ظرفیت یک نفر ~۵ جزء» (تنها حملهٔ باطل‌کننده، #۸) | سند جدیدتر (red-team 2026-07-01) | [[AI-FARM-MASTER-EXPORT]] بخش ۵ |
| D-03 | Wilson score، execution rings، hash-chain عمومی، FUSION module → **حذف از MVP** (hash-chain فقط در v2 برای مسیر مالی) | اسناد اولیه تجویز می‌کردند؛ نسخهٔ ۲.۰ MVP-first همه را رد کرد | سند جدیدتر + red-team («governance تئاتری») | [[سیستم-همیشه-روشن-پرامپت-و-دستورالعمل]] v2.0، [[AI-FARM-MASTER-EXPORT]] |
| D-04 | Observability = **OpenLLMetry + MLflow**، نه Langfuse self-host | [[05-research-shared-engineering-lane]] → Langfuse؛ [[09-research-evaluation-observability]] → MLflow (acquisition Langfuse توسط ClickHouse ژانویه ۲۰۲۶، ۵+ سرویس) | سند آگاه‌تر/جدیدتر (۰۹ رویداد ژانویه را می‌شناسد) | [[09-research-evaluation-observability]] |
| D-05 | MCP gateway = معماری هدف ولی **ساختش deferred** تا trigger «≥N action/روز روی ≥۲ tenant» | تناقض داخلی لِین ۰۵: «بالاترین ROI» vs «فعلاً هیچ لایهٔ مشترکی نساز» | جمع هر دو: طراحی الان، ساخت با trigger | [[05-research-shared-engineering-lane]]، [[08-research-tool-interoperability]] |
| D-06 | Kill-switch واحد: **flag `halted` در DB = منبع حقیقت** + mirror فایل `STOP` برای processهای غیر-bot؛ fail-closed | دو مکانیزم موازی در کد: SQLite flag (langar) vs فایل STOP (fusion/igk) | کد واقعی (هر دو تست‌شده) + یکسان‌سازی | `langar/bot.py`، `fusion-mvp/src/killswitch.py` |
| D-07 | لایهٔ ۳ حافظه: HybridRetriever محلی BM25+TF-IDF **موجود است** (dormant)؛ v1 فقط call-site اضافه می‌کند | `ARCHITECTURE.md` کد: «لایه ۳ غیرفعال/vector-based» vs کد واقعی: پیاده‌سازی کامل بدون embedding | **کد > سند** | `langar/core/retrieval.py` |
| D-08 | مدل پیش‌فرض = `claude-haiku-4-5-20251001` (نه Haiku 3.5 جدول قیمت‌ها) | Haiku 3.5 در جدول قیمت لِین ۱۱ vs haiku-4-5 در کد routing | **کد > سند** | `langar/brain/providers.py`، [[11-research-cost-infra-routing]] |
| D-09 | Framework: **raw API الان → Claude Agent SDK با احتیاط → LangGraph فقط مسیر خروج/branching**؛ cross-model validation (Gemini) اجباری برای تصمیم مالی | SDK توصیه‌شده (۱۳) vs لایسنس proprietary با lock-in=8 ناقض ارزش export-first (۱۰/۱۳) و correlated failure (۱۲) | جمع: SDK=runtime، خروج=LangGraph، داور=بین‌خانواده | [[13-research-framework-landscape]]، [[12-research-failure-modes-blind-spots]] |
| D-10 | پارادوکس HARD_STOP ماینینگ: **تحلیل/گزارش آزاد (INFORM)، execution مالی هرگز (HARD_STOP)**؛ HITL real-time رد شد (غیرعملی) | «ماینینگ tenant می‌خواهیم» vs «FINANCIAL=HARD_STOP» — تناقض باز در هر دو export | سنتز جدید (این سند) | [[10-research-safety-governance]]، [[LANGAR-MASTER-EXPORT]] |
| D-11 | کلید کریپتو: **off-box کامل**، صفر LLM access، human co-sign | پیشنهاد اکثریت: off-box vs پیشنهاد Gemini: bare-metal جدا | اجماع اکثریت + P10؛ bare-metal = زیرمجموعهٔ off-box | [[AI-FARM-MASTER-EXPORT]]، [[LANGAR-MASTER-EXPORT]] |
| D-12 | ترتیب استقرار: **اول لپ‌تاپ (اسموک ۷روزه)، بعد VPS** | کل تحقیق حول VPS vs تصمیم صریح کاربر: اول لپ‌تاپ | تصمیم کاربر = نهایی | [[LANGAR-MASTER-EXPORT]] |
| D-13 | Approval timeout = **DENY-on-timeout** (نه suspend-and-die) | «هر دو معتبر» در export | سازگاری با P2 (fail-closed) و سادگی MVP | [[LANGAR-MASTER-EXPORT]]، [[10-research-safety-governance]] |
| D-14 | Policy engine = **allowlist table در DB**، نه OPA (تا ≥۵ tenant) | لِین ۰۵/۱۲: OPA؛ لِین ۱۰ و Instructions نهایی: table ساده | سند جدیدتر + P7 (سادگی) | [[10-research-safety-governance]] |
| D-15 | Durable execution: الگوی **DBOS-style journaling روی همان Postgres** در v2؛ Temporal هرگز | Temporal (استاندارد صنعت) vs DBOS (سبک، همان DB) | توصیهٔ صریح تحقیق + P7 | [[05-research-shared-engineering-lane]] |
| D-16 | نسبت routing هدف = **70/25/5** (شروع عملی 50/50 تا داده بیاید) | 70/25/5 vs 70/20/10 vs شروع 50/50 در اسناد مختلف | عدد لِین ۱۱ (سند تخصصی هزینه) | [[11-research-cost-infra-routing]] |
| D-17 | آستانهٔ شروع حلقهٔ خودبهبودی: **≥۵۰ trajectory per project**؛ Level B فقط با ≥۲۰۰ | ≥20 per skill vs ≥50 vs ≥200 در لِین‌های مختلف | سند تخصصی (۱۴) + محافظه‌کاری | [[14-research-theoretical-foundations]] |
| D-18 | Eval set: **anchor ثابت + رشد ماهانه (+۱۰ production failure)**، نه rotation | rotation (۱۲ اولیه) vs anchor+grow (۱۲ اصلاحی و ۱۴) | نسخهٔ اصلاحی جدیدتر | [[09-research-evaluation-observability]]، [[12-research-failure-modes-blind-spots]] |
| D-19 | Reverse proxy = **Traefik** ([[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER-ARCHITECTURE]])؛ Caddy فقط اگر استک local-ai-packaged جداگانه adopt شود | Traefik vs Caddy (استک مرجع) | سند معماری رسمی > سند مرجع | [[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER-ARCHITECTURE]]، [[local-ai-packaged-reference]] |
| D-20 | دسترسی AI به زیرساخت: **فقط از مسیر repo + deploy gate؛ SSH مستقیم ممنوع** | سند معماری: gated؛ transcript: «Claude Code زنده روی VPS» | سند معماری رسمی + P1/P3 | [[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER-ARCHITECTURE]]، [[transcript-claude-md-agents]] |
| D-21 | حلقهٔ fusion = **الگوی مرجع** self-improvement (تنها حلقهٔ اثبات‌شده در اجرا) ولی eval آن باید از rubric کیواژه‌ای به گیت سه‌شرطی + held-out ارتقا یابد | ACE loop (langar، هرگز اجرا نشده) vs fusion loop (اجراشده ولی Goodhart) | کد اجراشده > کد dormant؛ ضعف ثبت شد | `fusion-mvp/self_update.py`، `langar/core/ace.py`، [[GAPS]] G-04 |
| D-22 | بودجهٔ $500/ماه: **نه سقف عادی، بلکه خط فاجعه**؛ سقف عملیاتی v1 = $60/ماه hard-stop | لِین ۱۱: «$500 معقول» vs لِین ۱۰: «خط فاجعهٔ recursive loop» | جمع: cap پایین + circuit breaker | [[11-research-cost-infra-routing]]، [[10-research-safety-governance]] |
| D-23 | Sandbox: cgroups برای contention همیشه؛ gVisor **فقط برای کد untrusted/generated** (شامل backtest ماینینگ اگر کد تولیدشده اجرا کند) | ۰۵: «اگر untrusted نیست حذف کن» vs ۰۸/۱۰: sandbox برای side-effect و کد generated | جمع شرطی؛ backtest = کد generated → gVisor | [[05-research-shared-engineering-lane]]، [[10-research-safety-governance]] |
| D-24 | سه لایهٔ ناهمگام vault (langar سادهٔ HRV / fusion پیچیده / architect متا) **یک سیستم‌اند**: langar=بدنه، fusion=الگوی حلقه و kernel، architect=چارچوب حاکم | سه نام‌گذاری و سه سطح پیچیدگی بدون اتصال صریح | سنتز این blueprint (بخش ۲) | [[SYSTEM-BLUEPRINT-v1]]، inv-01-project |
| D-25 | **معماری بودجه v1 (جایگزین فرض $60 در D-22):** کل هزینه AI ماهانه ≈ ۲۰۰–۳۰۰ AUD که ستونش اشتراک کلود (~AU$300/ماه فلت، شامل Cowork) است → کار سنگین (تحقیق/سنتز/blueprint/فیوژن) در جلسات Cowork زیر اشتراک؛ API متری بات langar = **hard-stop AU$30/ماه** با alert ۵۰٪/۸۰٪ و halt خودکار. خط فاجعهٔ $500 (D-22) پابرجا | فرض $60 hard-stop در blueprint vs بودجهٔ واقعی اپراتور (این چت 2026-07-03) | تصمیم کاربر = نهایی | پاسخ اپراتور؛ [[11-research-cost-infra-routing]] |
| D-26 | **ترتیب tenantها: Accounting → Lead-نقاشی → Mining.** Lead به‌خاطر درآمد دوم شد (مطابق پیش‌فرض blueprint)؛ Mining فقط تحلیل/INFORM طبق D-10 | سوال باز ۱ [[GAPS]]: Lead (درآمد) vs Mining (علاقه) | تصمیم کاربر = نهایی | پاسخ اپراتور 2026-07-03 |
| D-27 | **ریپوهای GitHub هنوز ساخته نشده‌اند** → نشت G-01 محدود به فایل‌سیستم/بکاپ محلی است. قاعده: هر repo از روز اول **private + history پاک** (history فعلیِ حاوی secret هرگز push نشود؛ init تازه بعد از پاکسازی). چرخش کلیدها همچنان الزامی است چون فایل‌ها در بکاپ گشته‌اند | سوال باز ۴ [[GAPS]] (فرض export: repo ساخته نشده) | واقعیت تأییدشده > فرض | پاسخ اپراتور 2026-07-03 |
| D-28 | **مغز upgradable است — با گیت انسانی:** تعویض model ID = تغییر config (`model_registry`، نه prompt — P3) با چرخهٔ کشف (`/v1/models` rule-based + تحقیق وب `<external_data>`) → eval گیت سه‌شرطی → پیشنهاد تلگرام → **APPROVE_FIRST + passphrase** → canary 48h + rollback خودکار. بهبود پرامپت/skill از تحقیق وب = فقط candidate diff وارد حلقهٔ §۴. weight/fine-tune همچنان Non-goal | «خودش عوض کند» vs D-01 (نرم‌افزار فقط پیشنهاد) | جمع: خودکارِ پیشنهاد، انسانیِ اعمال | درخواست اپراتور 2026-07-03؛ [[BRAIN-UPGRADE-LOOP]] |
| D-29 | **سینک vault:** گوشی↔لپ‌تاپ = Obsidian Sync (پلن واحد $4/ماه سالانه، E2E؛ جایگزین رایگان اندروید: Syncthing-Fork)؛ VPS = **هرگز کل vault** (منشور §۶/O-04) — فقط repo خصوصی `agent-outbox` با pull یک‌طرفه به لپ‌تاپ؛ `_code/` و DBهای زنده exclude؛ **هیچ سینکی قبل از بستن BACKLOG-01** | Obsidian Sync vs Syncthing vs obsidian-git (موبایل unstable) vs cloud drive | P7 (کمترین پیچیدگی) + منشور §۶ + تأیید وب 2026-07 | درخواست اپراتور 2026-07-03؛ [[OBSIDIAN-SYNC]] |
| D-30 | **Chrono زمانِ ذهنی = HLC فقط علّی + نرخ در `experience_meter`** (نه merge به max) — گیت D-A | broadcast max(HLC) بماند vs HLC علّی+نرخ جدا (E19) | recon گراندینگ 2026-07-09 + موافقت Ari | [[2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates]] §۵ (پرامپت P-A2) |
| D-31 | **صفِ world-deadline کنارِ beat-deadline اضافه شود** — گیت D-B | فقط beat-deadline (slip پذیرفته) vs دو صف (E20) | همان + موافقت Ari (followupِ مشتری تابعِ کما نباشد) | همان §۵ (P-A3) |
| D-32 | **قلبِ احرازشده: امضای entry + wire کانالِ تلگرام = تنها نویسندهٔ `is_human`** — گیت D-C (E16 شدیدترین حفره) | is_human بولیِ آزاد بماند vs امضا/کانالِ احرازشده | همان + موافقت Ari؛ **بحرانی، pre-merge نیازِ germline-backup+review** | همان §۵ (P-H1) |
| D-33 | **فلشِ سنیِ heart-driven (genome v0.4.6) تثبیت + متنِ spec آپدیت** — گیت D-D | بازگشت به human-only vs تثبیت | کد واقعی (v0.4.6) + موافقت Ari؛ تکمیلِ تصمیمِ 07-08 | همان §۵ (P-D2؛ ORGANISM-SPEC خط ۵۵ از قبل reconciled) |
| D-34 | **Doctor Evolution + Box B3 پشتِ flagِ خاموش wire شوند** — گیت D-E | on-shelf بماند vs wire خاموش | همان + موافقت Ari (قابلِ آزمایش، بی‌ریسک) | همان §۵ (P-N1/N2) |
| D-35 | **فعلاً تک‌پا (LeadLeg) + اتصالِ HLC؛ ناوگانِ ۶-پا ساخته نشود** — گیت D-F | ناوگانِ ۶-پا vs تک‌پا+سطوحِ کسب‌وکار | همان + موافقت Ari | همان §۵ (P-L1) |
| D-36 | **فقط effect-lease (idempotency E18) پذیرفته؛ sleep-leg/quarantine-reader/lineage-archive بعداً** — گیت D-G | همهٔ ۵ مفهومِ V2 vs فقط effect-lease | همان + موافقت Ari | همان §۵ (P-L2) |
| D-37 | **genome-system فایلِ ساده بماند (نه submodule)؛ لایهٔ نامیِ V2/alias در repo authored شود** — گیت D-H + حلِ open-item 07-07/07-08 | submoduleِ مستقل vs فایلِ ساده | همان + موافقت Ari؛ کمترین پیچیدگی تا نیازِ نسخه‌بندیِ جدا | همان §۵ + [[00 - Inbox/AGENT_QUESTIONS]] 07-07 |

## تصمیم‌های باز (تصمیم نگرفته‌ایم — عمداً)

| ID | موضوع | وضعیت |
|----|--------|--------|
| O-01 | Hetzner CX22 vs Oracle Free ARM برای VPS | هر دو در اسناد؛ انتخاب هنگام v1 با تست latency/price |
| O-02 | زمان فعال‌سازی `GROUNDING_REQUIRED=True` | نیازمند held-out واقعی؛ v2 — [[GAPS]] G-10 |
| O-03 | userbot Telethon اصلاً ساخته شود یا نه | فقط اگر use-case مشخص پیدا شد؛ default: نه |
| O-04 | محل دادهٔ HRV/شخصی (فقط لپ‌تاپ vs VPS رمزنگاری‌شده) | اپراتور عمداً باز گذاشت (2026-07-03)؛ **default محافظه‌کارانه تا تصمیم: دادهٔ شخصی به VPS نمی‌رود** و P9 دیوار منطقی می‌ماند |

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
