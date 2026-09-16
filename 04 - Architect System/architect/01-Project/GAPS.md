---
tags: [gaps, architect, backlog-input]
created: 2026-07-03
---

# GAPS — حفره‌ها، سوال‌های باز، ادعاهای بی‌منبع

> خروجی فاز ۳ [[PROMPT-A-absorb-synthesize]]. ورودی مستقیم برای BACKLOG (PROMPT-B). اولویت: 🔴 فوری / 🟠 مهم / 🟡 بعداً.

## 🔴 فوری (ریسک فعال)

| ID | حفره | شواهد |
|----|------|--------|
| G-01 | **نشت secrets در repo/backup**: سه فایل `.env` با کلید واقعی، `langar.db` و `langar.db-wal` واقعی، `OWNER_ID` واقعی در `.env.example`، IP واقعی VPS (‹redacted 2026-07-04 — اصل در secrets worklist/rotation›) در `one-liner-vps-setup.sh` | `_code/ai-farm/AI-sume/langar/.env`، `langar-pro/.env`، `fusion-mvp/.env`، inv-code-langarpro §تناقض ۹ |
| G-02 | **مسیر LLM در Docker مرده است**: `langar-pro/requirements.txt` کتابخانهٔ anthropic/openai ندارد → با هر کلیدی ImportError و degrade به خروجی آفلاین. + تضاد pg16/pg15 بین دو compose. + `one-liner-vps-setup.sh` سورس را clone نمی‌کند → build fail | `langar-pro/requirements.txt`، `docker-compose.unified.yml` |
| G-12 | **دو ادعای متناقض دربارهٔ وضعیت پروژه**: [[HANDOFF - قلب و آگاهی|HANDOFF]] «کد بات نوشته نشده» vs [[INDEX]] «۲۸ تست سبز» vs کد واقعی (بات کامل با ~۵۰ فرمان موجود است). منبع واحد وضعیت وجود ندارد | inv-01-project؛ حل‌شده در blueprint با اصل کد>سند، ولی HANDOFF باید بازنویسی نشود بلکه سند وضعیت جدید ساخته شود |

## 🟠 مهم (قبل از v1/v2 باید بسته شود)

| ID | حفره | شواهد |
|----|------|--------|
| G-03 | **ACE loop هیچ producer ای برای Outcome ندارد** — حلقه هرگز در runtime صدا زده نمی‌شود؛ HybridRetriever هم call-site ندارد. کد آماده، سیم‌کشی غایب | `langar/core/ace.py`، `langar/core/retrieval.py` |
| G-04 | **eval حلقهٔ خودبهبودی خودارجاع است** (Goodhart by construction): optimizer دقیقاً کیواژه‌های rubric را تزریق می‌کند؛ `held_out.json` واقعی نیست؛ هیچ eval رفتاری در promotion نقش ندارد | `fusion-mvp/src/optimizer.py`، `src/evals.py`، GAP-AUDIT معیار ۲ |
| G-05 | **BrainRouter wire نشده** و tier→model mapping ندارد؛ انتخاب مدل عملاً استاتیک است | `langar/brain/brain_router.py`، inv-code-langar |
| G-06 | **Budget فقط AILab را پوشش می‌دهد** ($1/روز)؛ مصرف سؤال روزانه/researcher/pro خارج از حسابداری است — سقف کل سیستم enforce نمی‌شود | `langar/budget.py` |
| G-07 | **Constitution: «۱۴ قانون» ادعا، ۴ الگوی regex enforce** (پزشکی، علیت بی‌hedge، نشخوار، عادی‌سازی خودتخریبی) — ۱۰ قانون دیگر فقط متن‌اند | `langar/core/constitution.py`، `langar-pro/app/research/constitution.py` |
| G-08 | **Observability خاموش**: دکوریتور `@trace` هیچ call-site ندارد → `/events` خالی؛ `/delete_all_data` جداول research/ailab/event_log را پاک نمی‌کند (نقض GDPR-style کامل بودن حذف) | `langar/observability/tracer.py`، inv-code-langar |
| G-10 | **سه خلأ enforcement در IGK**: (۱) `GROUNDING_REQUIRED=False` — گیت grounding فقط گزارش می‌دهد؛ (۲) ActuationGate فقط `finalize` (یک no-op) را می‌بندد — callهای LLM/tool از مسیر permit نمی‌گذرند؛ (۳) اگر kernel بالا نیاید fallback بی‌صدا به cooperative — خلاف fail-closed. + کلید HMAC توسط همان OS-user خواندنی است و chmod 600 روی Windows بی‌اثر | `fusion-mvp/config.py`، `igk/client.py`، THREAT-MODEL |
| G-15 | **پنل داوران fusion نمایشی است**: کال LLM انجام و هزینه ثبت می‌شود ولی خروجی مدل در رأی بی‌اثر است (تصمیم از هیوریستیک طول/کیواژه)؛ Supervisor dead-path؛ `MAX_STEPS=8` بلااستفاده؛ کل سیستم فقط در MOCK اجرا شده — **هیچ اجرای LIVE ثبت نشده** | `fusion-mvp/src/panel.py`، `src/orchestrator.py`، CHECKLIST |
| G-16 | **langar-pro: schema ۱۴جدولی ولی کد فقط به ۶ جدول می‌نویسد** <sub>(عدد ۱۳→۱۴ در تأیید مستقل 2026-07-03 اصلاح شد)</sub>؛ embedding هیچ‌جا ساخته نمی‌شود (vector-1536 مرده)؛ `confidence` همیشه NULL؛ sources بدون FK (orphan)؛ `synthesizer.py` dead code | `langar-pro/db/schema.sql`، inv-code-langarpro |
| G-18 | **ریسک E2E تلگرام عملیاتی نشده**: راه‌حل «رمز محرمانه» فقط پیشنهاد چت است؛ الان تنها دفاع OWNER_ID است (spoofing بعید ولی session hijack ممکن) | [[architect-chat-export]] ~خط 2808 |

## 🟡 بعداً / آگاهی

| ID | حفره | شواهد |
|----|------|--------|
| G-09 | تحقیق‌های ۰۱–۰۴ وجود ندارند (سری از ۰۵ شروع می‌شود) — محتوای احتمالی: تعریف مسئله، بازار، الگوهای orchestration پایه | [[00-Home]] |
| G-11 | **مشخصات tenantها تعریف‌نشده**: Accounting/Ziman/هیپنوتیزم در هیچ export ای spec ندارند؛ فولدرهایشان خارج از این vault است (`backup/03 - Projects/`). Adapter contract (چه چیزی expose می‌شود، چه credential ای) نانوشته | [[SYSTEM-BLUEPRINT-v1]] پیوست |
| G-13 | فایل‌های ارجاعی PROMPT-B (CHANGELOG، BACKLOG) هنوز ساخته نشده‌اند — در اولین اجرای B ساخته می‌شوند | [[PROMPT-B-test-improve]] |
| G-14 | هیچ port map صریحی در [[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER-ARCHITECTURE]] نیست (همه‌چیز label-based Traefik)؛ تنها پورت host مستند :8000 در compose | inv-docs |
| G-17 | redis در compose هست ولی هیچ کدی از آن استفاده نمی‌کند — حذف یا استفاده | `docker-compose.unified.yml` |
| G-19 | الزامات EU AI Act (binding از 2026-08-02، retention ≥۶ ماه) به کنترل عملیاتی تبدیل نشده | [[10-research-safety-governance]] |
| G-20 | **Cold-start ledger data** — گلوگاه بنیادی: بدون ≥۵۰ trajectory واقعی، حلقهٔ خودبهبودی و بخشی از eval بی‌معناست. برنامهٔ جمع‌آوری داده از کار روزمره تعریف نشده | [[05-research-shared-engineering-lane]]، [[14-research-theoretical-foundations]] |
| G-21 | ادعاهای علمی HRV نسخه‌های قدیمی در برخی اسناد مانده (HRVB برای اضطراب g≈0.83 → null در متاآنالیز ۲۰۲۵؛ تصحیح Kaduk 2025) — هر استفادهٔ آینده باید نسخهٔ تصحیح‌شده را مبنا بگیرد | [[AI-FARM-MASTER-EXPORT]] |
| G-22 | مسیر بکاپ SQLite ناسازگار بین اسناد: `langar/langar.db` vs `langar/data/langar.db` | CHECKLIST vs SETUP_PROMPT |

## افزوده‌های اجرای PROMPT-B (2026-07-03)

| ID | حفره | شواهد |
|----|------|--------|
| G-23 | 🟡 **قیمت Haiku 4.5 در هیچ سند vault نیست** — جدول قیمت [[11-research-cost-infra-routing]] مال Haiku 3.5 است ($0.80/$4) ولی کد `claude-haiku-4-5` را صدا می‌زند؛ قبل از تخمین نهایی هزینه از منبع رسمی verify شود | تأیید مستقل، D-08 |
| G-24 | 🟡 **ابهام واژگانی «وزن»**: قانون ۱۲ constitution کد («تغییر خودکار فقط وزن») منظورش `agent_weights` داخلی است نه weight مدل — با Non-goal سطح C تعارض واقعی ندارد ولی نام‌گذاری کد باید اصلاح شود | `langar/core/constitution.py`، `core/self_improver.py` |
| G-25 | 🟠 **ادعای «read-only بازرسی tenantها» در v1 فقط قرارداد بود نه enforced** — bot برای deploy/kill قدرت write دارد؛ v2 با creds جداگانهٔ read-only حل طراحی کرد، پیاده‌سازی = BACKLOG-13 | red-team محور ۲ |
| G-26 | 🟠 **هیچ اجرای LIVE از حلقهٔ fusion ثبت نشده** — «اثبات 0.6→0.8→1.0» تماماً MOCK با scorer کیواژه‌ای بود؛ تا held-out واقعی نیامده، هیچ ادعای «کارکرد اثبات‌شده» معتبر نیست | G-04، G-15، red-team محور ۵ |

## سوال‌های باز برای اپراتور (آرمین) — پاسخ‌داده‌شده 2026-07-03

1. ✅ **Lead-نقاشی** بعد از Accounting (مطابق blueprint) → [[DECISIONS]] D-26
2. ✅ کل بودجه ≈ ۲۰۰–۳۰۰ AUD/ماه؛ ستون = اشتراک کلود ~AU$300 (شامل Cowork)؛ **API متری بات: hard-stop AU$30/ماه** → D-25 (جایگزین فرض $60)
3. ⏳ عمداً باز ماند → O-04؛ default تا تصمیم: دادهٔ شخصی فقط لپ‌تاپ، به VPS نمی‌رود
4. ✅ **ریپوها هنوز ساخته نشده‌اند** → نشت G-01 فقط لوکال/بکاپ است؛ قاعدهٔ private-from-birth + history پاک → D-27

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
