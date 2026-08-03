# LANGAR — نقشه‌ی توسعه‌ی ماژولار (Plan only)

> این سند فقط **طرح** است. هیچ کدِ ماژولِ جدیدی بدون تأییدِ تو نوشته نمی‌شود.
> اصلِ کار: گسترشِ ایمن و افزایشی، حفظِ همه‌ی رفتارهای موجود، migrationهای idempotent.

---

## بخش ۱ — بازرسیِ کدِ موجود (وضعیتِ فعلی)

**زبان/فریم‌ورک:** Python 3.10+ · `python-telegram-bot` v21 (async) · `python-dotenv`.
**لایه‌ی داده:** SQLite از طریقِ `db.py` (یک wrapper سبک، بدونِ ORM). حالتِ **WAL** فعال.
**پایداری:** `PicklePersistence` (گفتگوی نیمه‌تمام پس از ری‌استارت می‌ماند). مسیرِ DB/state از env قابلِ تنظیم.

**فایل‌ها (وضعیتِ فعلی):**

| فایل | مسئولیت |
|---|---|
| `main.py` | بارگذاریِ env، init، persistence، post_init، polling |
| `bot.py` | همه‌ی هندلرها و گفتگوها + دکوریتورهای امنیت |
| `db.py` | schema، config، log، insight، reflection، آمار trend |
| `hrv.py` | محاسبه‌ی RMSSD از RR خام + artifact rejection |
| `ai.py` | موتورِ سؤالِ روزانه (آفلاین/Claude) |
| `BRAIN_PROMPT.md` | پرامپتِ سیستمیِ مغزِ دوم |

**دستورهای فعلی:** `/start /log /rmssd /trend /ask /reflect /insight /recheck /export /status /halt /resume` (+ `/cancel /skip` داخلِ گفتگوها).

**Schema فعلی:**
- `log(id, ts, rmssd, sleep, used, loc, note)`
- `insight(id, ts, content, tag[E/S/P], recheck, verdict)`
- `config(key, val)` — seed: `halted=0`
- `reflection(id, ts, domain, question, answer)`

**ناورداهای حیاتی که باید حفظ شوند:**
1. **owner-only** (`owner_only`) — غریبه = سکوتِ کامل.
2. **kill-switch** (`guarded`) — `/halt /resume /status` معاف از gate.
3. **verdict برگشت‌ناپذیر** (`record_verdict` + `AlreadyJudged`) — write-once.
4. **شاخصِ قفل‌شده = RMSSD**؛ همبستگی فقط با ≥۳ جفت؛ «همبستگی ≠ علیت».
5. **local-first / privacy-first** — هیچ ارسالِ ابری مگر `CLAUDE_KEY` صریح.

**شکافِ مهمی که باید اول پر شود:** `db.init_db()` فقط `CREATE TABLE IF NOT EXISTS` دارد و **سیستمِ migration برای افزودنِ ستون به جدولِ موجود ندارد.** ماژول‌های ۱ و ۳ نیاز به `ALTER TABLE` دارند. پس Phase 1 با ساختِ یک migration runnerِ سبک شروع می‌شود.

---

## بخش ۲ — استراتژیِ migration (پایه‌ی همه‌چیز)

- افزودنِ کلیدِ `schema_version` در `config`.
- یک `migrations.py` با لیستِ مرتبِ گام‌ها؛ هر گام idempotent (`ALTER TABLE ... ADD COLUMN` فقط اگر ستون نباشد؛ `CREATE TABLE IF NOT EXISTS`).
- اجرا در `init_db()` پس از ساختِ schema پایه.
- هرگز DROP/حذفِ داده. قبل از هر تغییرِ بزرگ، یک snapshotِ خودکارِ فایلِ DB گرفته شود.
- **هیچ migrationِ مخرب بدونِ تأییدِ صریحِ تو اجرا نمی‌شود.**

---

## بخش ۳ — فازها (نسخه‌ی بازچینی‌شده طبقِ اولویت‌های تو)

> اولویت‌های تأییدشده: **عادت‌ها/مرورها**، **کوچ/ترند/ثبتِ غنی**، **آزمایش‌های N-of-1**، و **تداوم (consistency)**.
> تصمیم‌ها: `/log` کوتاه می‌ماند (جزئیات در `/log_advanced` جدا) · Muse فقط سبک و به آخر منتقل شد.
> **تداوم** یک موضوعِ عرضی است که در همه‌ی فازها تنیده می‌شود: streak، یادآوریِ ملایم، و قواعدِ کوچ.

### Phase 1 — پایه + ثبتِ غنی (بدونِ شکستن) + پایه‌ی تداوم
- migration runner + `schema_version` (هسته‌ی همه‌ی فازها).
- `/log` **دست‌نخورده و کوتاه** می‌ماند؛ `/log_advanced` جدا برای جزئیاتِ بیشتر.
- ستون‌های اختیاریِ `log`: `rmssd_quality`, `rmssd_source`, `measurement_duration_sec`, `measurement_posture` (nullable).
- جدولِ `daily_state(date, mood, energy, stress, soreness, exercise, …)` (migration کم‌حجم).
- `/checkin` (ثبتِ سبکِ mood/energy/stress بدونِ RMSSD) · `/today` · `/edit_today` (ویرایشِ فیلدهای غیرwrite-once).
- **تداوم:** ردیابیِ streakِ ثبتِ روزانه (پینگِ صبحگاهی از قبل هست).
- `/rmssd_help` (راهنمای اندازه‌گیریِ درستِ RMSSD). راهنمای Muse به Phase 5 موکول شد.

### Phase 2 — عادت‌ها و مرورها (اولویتِ #۱ تو)
- عادت: `/habit /habits /done /habit_report` → جداولِ `habit` و `habit_log`.
  - **تداوم:** streak و نرخِ ثبات؛ بدونِ زبانِ شرم؛ هنگامِ از‌دست‌رفتن «چه چیزی سختش کرد؟» و پیشنهادِ «نسخه‌ی حداقلی».
- مرور: `/review_daily` `/review_weekly` `/review_monthly` → جدولِ `review(type, period, answers_json, summary)`.
- بینش: `/insights` (فهرست) و `/insight_stats` (E/S/P، نرخِ تأیید، overdueها). **write-once دست‌نخورده.**

### Phase 3 — کوچ + ترندِ پیشرفته (بازدهِ داده‌ی غنی)
- ارتقای `/trend`: میانگینِ متحرک، baselineِ ۳۰روزه، فعلی‌vs‌baseline، completeness، هشدارِ کیفیت، همبستگیِ اختیاریِ mood/energy. `/trend 7|14|30|90`.
- `/coach` قاعده‌محورِ deterministic (نه نصیحتِ مبهم): کم‌داده، RMSSDِ پایین + خوابِ کم، مصرفِ اخیر، و **قواعدِ تداوم** (شکستنِ streak، نبودِ export، adherence پایین).

### Phase 4 — آزمایش‌های N-of-1
- `/experiment /experiments /experiment_stop /experiment_report` → جداولِ `experiment` و `experiment_day`.
- طرح‌ها: AB، یک‌روزدرمیان، before-after (با برچسبِ «شواهدِ ضعیف»).
- یادآوری حینِ `/log` اگر آزمایشِ فعال باشد · پیوندِ insightِ تأییدشده → آزمایش.
- گزارش: baseline vs intervention + adherence + هشدارِ «این اثبات نیست، یک سیگنالِ شخصی است».

### Phase 5 — Muse (سبک)، export، privacy، تست
- **Muse فقط سبک، بدونِ numpy/scipy:** `/muse_help` + `/import_muse` با کتابخانه‌ی استانداردِ پایتون.
  - اگر Mind Monitor ستونِ RR/IBI بدهد → مستقیم با `hrv.py` محاسبه (دقیق).
  - اگر فقط PPG خام باشد → peak detectionِ سبکِ pure-python (تقریبی) یا skeletonِ امن با پیامِ صادقانه. جدولِ `measurement_import(...)`.
- ارتقای export: همه‌ی جداولِ جدید + `/export_csv` + metadata (schema_version, created_at).
- privacy/safety: `/privacy` و `/delete_all_data` با تأییدِ دومرحله‌ای (عبارتِ دقیق + archive قبل از حذف).
- تست‌ها: owner-only، halt/resume، write-once، حداقل‌دادهٔ trend، صحتِ RMSSD، گزارشِ آزمایش، idempotent بودنِ migration، streak.

---

## بخش ۴ — معماریِ ماژولار (در همین سبکِ فعلی)

به‌جای تحمیلِ ساختارِ پوشه‌ای، مسئولیت‌ها را در فایل‌های مستقل و loosely-coupled جدا می‌کنیم:
`db.py` (هسته+migration) · `hrv.py` · `muse.py` · `experiments.py` · `habits.py` · `reviews.py` · `coach.py` · `trends.py` · `ai.py` · `safety.py`.
`bot.py` فقط هندلرها را به این ماژول‌ها وصل می‌کند. هر ماژولِ جدید **اختیاری** است و نبودش بات را نمی‌شکند.

---

## بخش ۵ — تصمیم‌های تأییدشده و مواردِ بازمانده

**تأییدشده:**
- وابستگی‌های سنگین (numpy/scipy) **مجاز نیست** → Muse فقط سبک، در Phase 5.
- `/log` کوتاه می‌ماند؛ جزئیات در `/log_advanced`.
- اولویت: عادت‌ها/مرورها → کوچ/ترند/ثبتِ غنی → آزمایش‌ها → (Muse آخر). تداوم: عرضی در همه.

**هنوز نیاز به تأییدِ تو:**
- **`/delete_all_data`** — تنها دستورِ مخرب؛ با تأییدِ دومرحله‌ای (عبارتِ دقیق + archive) پیاده می‌شود. تا تأیید نکنی پیاده نمی‌شود.

هیچ migrationِ مخرب، هیچ حذفِ داده، و هیچ تغییرِ رفتارِ موجود بدونِ اطلاعِ تو انجام نمی‌شود.
