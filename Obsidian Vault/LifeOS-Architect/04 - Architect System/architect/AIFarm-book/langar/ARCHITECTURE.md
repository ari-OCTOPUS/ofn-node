# LANGAR — سندِ معماریِ کامل

> دفترچه‌ی همیشه‌روشن برای خودشناسی، آزمایشِ شخصیِ N-of-1، و رشدِ آرام — به‌علاوه‌ی یک
> آزمایشگاهِ مستقلِ هوش مصنوعی (AI-Lab). local-first، owner-only، و «AI پیشنهاد می‌دهد، انسان تصمیم می‌گیرد».

---

## ۱. دو محصول

| محصول | پوشه | استک | کِی |
|---|---|---|---|
| **باتِ سبک** | `langar/` | Python + python-telegram-bot + SQLite | امروز کار می‌کند؛ برای استفاده‌ی شخصی کافی است |
| **نسخه‌ی حرفه‌ای** | `langar-pro/` | FastAPI + Postgres(pgvector) + Docker | مهاجرتِ فازی برای آینده/مقیاس |

این سند عمدتاً معماریِ **باتِ سبک** را توصیف می‌کند (که کامل ساخته شده). `langar-pro` فاز ۱–۲ دارد.

---

## ۲. لایه‌ها (نمای کلی)

```
Telegram  ──►  bot.py  (owner-only gate · kill-switch · منوها)
                 │
                 ▼
      ┌──────────────────────────── CORE ────────────────────────────┐
      │  HumanCore  →  MentalModel · Communication · SelfImprover     │
      │  Constitution (۱۴ قانون، گذرگاهِ هر خروجی)                    │
      └───────┬───────────────┬───────────────┬──────────────────────┘
              ▼               ▼               ▼
          Agents          Brain           Researcher / AI-Lab
       (Health/Reflect/   (Claude/OpenAI-   (search + source-scoring
        Relationship/      compat/Offline)   + synthesize + budget)
        Coach + Router)
              │               │               │
              ▼               ▼               ▼
        db.py (SQLite) ── migrations (نسخه‌بندی) ── observability + safety
```

اصلِ کلیدی: **gate و kill-switch قبل از CORE و معاف از آن‌اند؛ CORE آن‌ها را دور نمی‌زند.**

---

## ۳. ماژول‌ها (فایل به فایل)

**هسته و ورودی**
- `main.py` — نقطه‌ی ورود: config → init db → ساختِ CORE/Researcher/AI-Lab/Budget → polling.
- `config.py` — بارگذاری و اعتبارسنجیِ `.env` (با aliasهای OPENAI_*/TELEGRAM_*). تنها نقطه‌ی خواندنِ env.
- `bot.py` — همه‌ی هندلرها، منوها، gate، kill-switch، تزریقِ CORE/Researcher/AI-Lab/Budget.
- `db.py` — لایه‌ی SQLite (WAL)، CRUDِ همه‌ی جدول‌ها، آمار.
- `migrations.py` — نسخه‌بندیِ schema (نسخه‌ی فعلی **۸**)، idempotent و غیرمخرب.

**اندازه‌گیری و آمار (بدونِ AI — قاعده‌محور)**
- `hrv.py` — محاسبه‌ی RMSSD از RR خام + رد کردنِ artifact.
- `muse.py` — ورودِ CSVِ Muse/Mind Monitor (RR یا PPGِ تقریبی).
- آمار trend/همبستگی در `db.py` (Pearson، با حداقل ۳ جفت).

**CORE — شناخت و ارتباط**
- `core/human_core.py` — Orchestrator؛ سؤالِ روزانه را می‌سازد و pipeline را می‌گرداند.
- `core/mental_model.py` — مدلِ ذهنیِ پویا از کاربر (استرس/خواب/درگیری/لحن).
- `core/communication.py` — تنظیمِ لحن و طول بر اساسِ حال‌وروز.
- `core/self_improver.py` — بهبودِ خودِ سیستم (فقط وزن‌دهیِ امن، نه prompt/کد).
- `core/constitution.py` — ۱۴ قانون به‌صورتِ critique (medical/causal/rumination/…).
- `core/world_model.py` — جمعِ World State از داده‌ی داخلی (+ git/فایل اختیاری).
- `core/memory.py` — حافظه‌ی لایه ۱ (session) + ۲ (SQLite)؛ لایه ۳ (vector) غیرفعال.
- `core/contract.py` — قراردادِ انسان‑AI (می‌تواند/نمی‌تواند/می‌پرسد).

**Brain — لایه‌ی LLM**
- `brain/providers.py` — Anthropic + OpenAI-compatible (DeepSeek/Chatbox) + Offline + factory با fallback.
- `brain/prompt.py` — بارگذاریِ `BRAIN_PROMPT.md`.
- `brain/question_bank.py` — بانکِ سؤالِ آفلاین.

**Agents — مولتی‌ایجنت**
- `agents/health_agent.py` (بدن/HRV) · `reflection_agent.py` (ذهن/معنا/کار) · `relationship_agent.py` (رابطه) · `coach_agent.py` (پیش‌فعال) · `router.py` (انتخابِ حوزه با وزن).

**Researcher — پژوهش**
- `researcher/researcher.py` — هماهنگ‌کننده (هدف armin/self).
- `researcher/search_providers.py` — Brave/SerpAPI/Offline.
- `researcher/source_quality.py` — امتیازِ منبع + تخمینِ عدم‌قطعیت.
- `researcher/synthesizer.py` — بریفِ سورس‌دار و تگ‌خورده.

**AI-Lab و کنترل**
- `ailab.py` — آزمایشگاهِ مستقلِ AI (دادهٔ جدا، فقط پیشنهاد).
- `budget.py` — تخمینِ هزینه + سقفِ روزانه/ماهانه.
- `safety/patch_manager.py` — پیشنهادِ diff (سطح ۱ و ۲؛ سطح ۳ عمداً نیست).
- `safety/rollback.py` — بکاپ/بازگردانی.
- `observability/tracer.py` + `event_log.py` — شفافیت و ردگیری.

**رابطِ کاربری و راهنما**
- `menus.py` — ۹ دسته‌ی منو + زیرمنو + پیشنهادِ دستورِ ناشناخته.
- `BRAIN_PROMPT.md` · `RESEARCHER_PROMPT.md` — پرسوناها.
- `USAGE.md` · `CHECKLIST.md` · `DEPLOYMENT_GUIDE_FA.md` · `README.md` — مستندات.
- `Dockerfile` + `docker-compose.yml` — اجرای ۲۴ ساعته.
- `tests/test_langar.py` — تستِ داده‌لایه.

---

## ۴. مدلِ داده (۲۳ جدول، نسخه‌ی schema = ۸)

- **شخصی:** `log`, `daily_state`, `insight`, `reflection`, `habit`, `habit_log`, `review`, `experiment`, `experiment_day`, `measurement_import`, `config`.
- **CORE:** `mental_model_snapshot`, `question_quality`, `improvement_report`, `agent_weights`.
- **پژوهش/شفافیت:** `research`, `verdict_log` (append-only), `event_log`, `patch_suggestion`.
- **AI-Lab (جدا):** `ailab_entry`, `ailab_idea`, `ailab_proposal`.
- **بودجه:** `ai_usage`.

مهاجرت idempotent و غیرمخرب است: روی دیتابیسِ موجود فقط ستون/جدول اضافه می‌شود، داده پاک نمی‌شود.

---

## ۵. کاتالوگِ دستورها (۹ دسته)

۱) **ثبت/بدن:** `/log` `/checkin` `/rmssd` `/rmssd_help` `/today` `/streak`
۲) **الگوها:** `/trend` `/review_weekly` `/review_monthly` `/habit_report`
۳) **بینش:** `/insight` `/recheck` `/insights` `/insight_stats`
۴) **عادت/هدف:** `/habit` `/done` `/habits` `/habit_report` `/goal` `/coach`
۵) **آزمایش:** `/experiment` `/experiments` `/experiment_report` `/experiment_stop`
۶) **پژوهش:** `/research` `/architect` `/contract` `/research_verdict`
۷) **مغز دوم:** `/ask` `/reflect` `/mind` `/improve` `/pending`
۸) **داده/کنترل:** `/export` `/export_csv` `/import_muse` `/events` `/status` `/halt` `/resume` `/privacy`
۹) **AI-Lab:** `/ailab` `/ai_research` `/ai_digest` `/ai_architect` `/ai_memory` `/ai_benchmark` `/ai_safety` `/ai_ideas` `/ai_roadmap` `/ai_budget` `/ai_propose_update`
ناوبری: `/start` `/menu` (دکمه‌ای) · `/help_all` (فهرستِ متنیِ کامل).

---

## ۶. هوش مصنوعی‌ها

- **LLM (مغز):** Anthropic Claude **یا** OpenAI-compatible (OpenAI / DeepSeek / Chatbox) **یا** Offline. انتخاب با `BRAIN_PROVIDER=auto`، با fallbackِ بدونِ‌کرش.
- **جست‌وجو:** Brave Search **یا** SerpAPI **یا** Offline.
- **بدونِ کلید = کاملاً آفلاین** (هیچ داده‌ای بیرون نمی‌رود).
- بخشِ بزرگِ سیستم **هیچ AIای ندارد** (RMSSD، آمار، constitution، coach، منبع‌سنجی) — قاعده‌محور و رایگان.

---

## ۷. AI-Lab

آزمایشگاهِ مستقل با تمرکز روی **خودِ AI** (معماری/حافظه/ارزیابی/امنیت). دادهٔ آن در جدول‌های `ailab_*` و **جدا از دادهٔ شخصی** است. می‌گردد، با منبع‌سنجی و LLM خلاصه می‌سازد، از constitution رد می‌شود، و در صورتِ `propose_update` یک **diffِ سطح ۲** برای هدفِ `ailab|human|system` می‌سازد — **بدونِ اجرای خودکار**. مصرفش با `budget.py` سقف‌دار است.

---

## ۸. گاردریل‌های ایمنی (۸ ضلع)

1. **owner-only** — فقط مالک؛ غریبه = سکوت.
2. **kill-switch** — `/halt` همه را ساکت می‌کند؛ `/resume`/`/status` معاف.
3. **Constitution** — جلوی ادعای پزشکی/علیتِ بی‌احتیاط/نشخوار/خودتخریبی.
4. **verdictِ بینش write-once** — داوریِ بینش برگشت‌ناپذیر؛ (verdictِ پژوهش نسخه‌بندی‌شده).
5. **بدونِ خودویرایش** — patch فقط diff؛ سطح ۳ ساخته نشده.
6. **جداسازیِ داده** — AI-Lab ⟂ دادهٔ شخصی.
7. **بودجه** — سقفِ هزینه‌ی AI؛ تمام شد → آفلاین.
8. **حریم خصوصی** — local-first؛ بدونِ کلید هیچ ارسالی نیست.

قانونِ طلایی: *No source→no fact · No consent→no action · No feedback→no learning · No audit→no trust · No uncertainty→no verdict.*

---

## ۹. استقرار

- **محلی:** `python main.py` (نیازِ `.env` با `BOT_TOKEN`+`OWNER_ID`).
- **۲۴ ساعته:** `docker compose up -d` (با `restart: unless-stopped`، داده در `data/`).
- جزئیاتِ کامل در `DEPLOYMENT_GUIDE_FA.md`.

---

## ۱۰. وضعیتِ تست

منطقِ همه‌ی ماژول‌ها واحد‌به‌واحد تست شده (HRV، constitution، budget، source-quality، coach، muse، menus، agents/router، researcher engine، CORE با fake-db، و SQLِ هر ۲۳ جدول). محدودیت: فایل‌های بزرگِ ویرایش‌شده (`bot.py`/`main.py`) به‌خاطرِ یک گلیچِ همگام‌سازیِ محیطِ ساخت، runtimeِ کامل اینجا اجرا نشدند؛ آزمونِ نهایی، اولین `python main.py`/`docker compose up` روی دستگاهِ توست.

---

## ۱۱. نقشه‌ی آینده (به‌ترتیبِ ارزش)

1. **BrainRouter** — مدلِ ارزان برای کارِ ساده، قوی فقط برای AI-Lab (کاهشِ هزینه).
2. اجرای واقعیِ Docker و چند روز **استفاده‌ی واقعی** قبل از افزودنِ لایه‌ی جدید.
3. `langar-pro` فاز ۳ — Graph Memory (claims/edges) + جست‌وجوی معناییِ pgvector.
4. Webhook + Cloudflare Tunnel (فقط اگر لازم شد).

*ساخته‌شده گام‌به‌گام، با اصلِ «ساده بمان مگر دردِ واقعی، توجیهش کند».*
