# پرامپت پنج‌گانهٔ مرحله‌ای — ساختِ «genome-system»

> یک سیستمِ دانشِ شخصیِ **خودبهبود، امن، local-first** روی یک لپ‌تاپ، با دو ایجنتِ
> جدیدِ درخواستیِ تو: **Guardian-Architect** (کنترل + آنلاین‌بودن + معماریِ ۲۴ساعته)
> و **Creativity Black-Box** (خلاقیتِ مرزِ دیوانگی/نبوغ، read-only، propose-only).
>
> **نحوهٔ استفاده:** هر فاز یک بلوکِ «پرامپت اجرا» دارد که می‌توانی مستقیم به یک
> agent-builder / Claude بدهی. فازها ترتیبی‌اند؛ تا Definition of Done یک فاز سبز
> نشده، وارد فاز بعد نشو.

---

## قاب‌بندی (یک‌بار بخوان)

- **Problem:** حافظه و ابزارهای دانشِ فعلی یا vendor-lock می‌شوند (درسِ
  Rewind/Limitless→Meta، قطع ضبط ۱۹ دسامبر ۲۰۲۵) یا با اسکن دائمی گران و ناامن‌اند
  (درسِ Recall).
- **Goal:** سیستمی که خودش را بهبود دهد ولی هرگز نتواند معیارِ قضاوتش را دور بزند.
- **Constraints:** یک نفر، یک لپ‌تاپ، بودجهٔ کوچک (~زیر ۵۰ دلار/ماه)، فرمت‌های باز.
- **Assumptions (صریح):** ۵ فاز؛ زبانِ خروجی فارسی + termهای انگلیسی؛ همه‌چیز به
  صورت فایل. اگر این‌ها را نمی‌خواهی، بگو تا عوض کنم.
- **Risks:** خودبهبودِ مهارنشده → reward hacking (درسِ DGM: جعل لاگ تست و غیرفعال‌کردن
  کدِ تشخیص hallucination). مهار: evaluator داخل ژنوم + propose-only + گیت انسانی.

### تصحیح معماریِ کلیدی (عمدی — «be smarter»)
تو خواستی گاردین «داخل ژنوم برای کنترل» باشد. اگر ایجنتی که کنترل می‌کند بتواند
ژنوم را هم بازنویسی کند، دقیقاً همان حفرهٔ DGM باز می‌شود. پس گاردین **تحت حاکمیتِ**
ژنوم است و رویش **read-only**: پایش/گیت/halt می‌کند، ولی تغییرِ ژنوم فقط از مسیرِ
انسانیِ ۷۲ساعتهٔ دو-کلیدی می‌گذرد.

### سه‌گانه‌ای که در هر فاز لحاظ شده
- **Memory:** working (context/CLAUDE.md) · episodic (`ledger.jsonl` append-only+hash-chain)
  · semantic (vault + index محلی) · procedural (genome + role-prompts).
- **Intelligence:** Haiku 4.5 (ارزان) / Sonnet 5 (پیش‌فرض) / Opus 4.8 (پریمیوم) + router؛
  Batch −۵۰٪ · cache-hit −۹۰٪. (قیمت‌ها verify‌شدهٔ ۲۰۲۶-۰۷-۰۶.)
- **Backup:** ۳-۲-۱ · git · restic/rclone رمز‌شده · restore drill ماهانه.

---

## فاز ۰ — بنیان و ژنوم (Foundation & Genome)
**هدف:** هستهٔ تغییرناپذیر و حافظهٔ ممیزی را بساز و **قفل** کن.

**پرامپت اجرا:**
> «پوشهٔ `genome/` را بساز با `values.yaml` (اصولِ invariant + آزمونِ مرز)،
> `gates.yaml` (بودجه، approve-first، routing مدل، run-guards)، `metrics.yaml`
> (تعریفِ سلامت، فریزشده)، `backup.yaml` (۳-۲-۱ + DR)، و
> `genome_change_protocol.md` (۷۲ساعت + دو-کلید). سپس `ledger/ledger.py`
> (JSONL فقط-append با hash-chain) را مستقر کن. کل `genome/` را فایل‌سیستمی
> read-only کن. git repo بساز و اولین commit را بزن.»

- **Memory:** episodic memory متولد می‌شود (`ledger.jsonl`).
- **Intelligence:** هنوز مدلی لازم نیست؛ فقط زیرساخت.
- **Backup:** git = کپیِ اول؛ سیاست ۳-۲-۱ نوشته می‌شود.
- **Definition of Done:** `chmod -R a-w genome` اعمال شده · `python tests/smoke_test.py`
  سبز · اولین git commit ثبت شده · ledger.verify()=ok.
- **Gate/ایمنی:** از این‌جا به بعد هیچ ایجنتی حق نوشتن روی `genome/` را ندارد.

---

## فاز ۱ — ادراک و حافظه (Perception & Memory)
**هدف:** ورودیِ رویدادمحور + حافظهٔ قابل‌جستجو، **بدون** polling.

**پرامپت اجرا:**
> «یک file-watcher رویدادمحور (watchdog؛ روی create/modify/delete فقط برای
> allowlistِ پسوندهای متنیِ مصوبِ مالک) بساز که هر تغییر را به یک incremental
> indexer بدهد: SQLite FTS5 (با fallbackِ LIKE) که فقط همان نوتِ تغییرکرده را
> دوباره index کند و یک `INDEX` در ledger بنویسد. digestِ شبانه را با Batch API
> (−۵۰٪) اجرا کن. polling دقیقه‌ای ممنوع.»

- **Memory:** semantic memory (vault→index)؛ index از vault بازساختنی است.
- **Intelligence:** فقط `cheap` (Haiku) برای digest؛ embeddingِ محلیِ اختیاری.
- **Backup:** `backup.yaml` را به index (rebuildable) و vault (critical) بسط بده.
- **Definition of Done:** `index_freshness_s < 5` در ledger دیده شود · جست‌وجو
  نتیجهٔ درست بدهد · هیچ اسکنِ زمان‌بندی‌شدهٔ دقیقه‌ای وجود نداشته باشد.
- **Gate/ایمنی:** allowlistِ perception = privacy boundary؛ default-deny (درسِ Recall).

---

## فاز ۲ — گاردین/معمار ۲۴ساعته (Guardian-Architect)
**هدف:** ایجنتِ همیشه‌روشن برای کنترل، آنلاین‌بودن، و نظارت.
(role-prompt: `agents/guardian-architect.md`)

**پرامپت اجرا:**
> «گاردین را طبق `agents/guardian-architect.md` مستقر کن: heartbeatِ دوره‌ای
> (`HEARTBEAT` + uptime)، اجرای گیت‌های `gates.yaml`، loop/cost-guard (درسِ
> AutoGPT)، پاسبانِ ژنوم (اگر قفل شکست → halt)، و پاسبانِ بک‌اپ (اگر
> `backup_last_success_age_h>24` → هشدار). گاردین روی genome و vault **فقط
> می‌خواند**؛ تنها ledger می‌نویسد؛ هرگز APPLY نمی‌کند.»

- **Memory:** گاردین از episodic memory می‌خواند و `HEARTBEAT/METRIC` می‌نویسد.
- **Intelligence:** `cheap` برای heartbeat/گیت؛ `premium` فقط برای تحلیل معماریِ دوره‌ای.
- **Backup:** گاردین سلامتِ بک‌اپ را متریک می‌کند و افتش را قرمز می‌کند.
- **Definition of Done:** `guardian_uptime_pct ≥ 0.99` · یک نقضِ بودجهٔ آزمایشی →
  pause خودکار · دستکاریِ آزمایشیِ یک فایلِ ژنوم → halt.
- **Gate/ایمنی:** گاردین می‌تواند halt کند ولی نمی‌تواند ژنوم را عوض کند.

---

## فاز ۳ — جعبه‌سیاه خلاقیت + دکتر تکاملی (Creativity + Doctor)
**هدف:** موتورِ ایده‌های جسورانه + داورِ امنِ تکاملی.
(role-prompts: `agents/creativity-blackbox.md`، `agents/evolutionary-doctor.md`)

**پرامپت اجرا:**
> «Creativity Black-Box را مستقر کن: read-only روی کل پروژه (vault + ledger +
> خروجی سایر ایجنت‌ها)، تولیدِ ایده‌های مرزِ دیوانگی/نبوغ، هر ایده با قالبِ
> اجباری {why_genius, why_insane, confidence پایین, kill_criteria, smallest_test,
> reversible}. فقط `PROPOSAL` می‌نویسد، مخاطبش دکتر. سپس دکتر را مستقر کن:
> هفتگی (Opus)، گزارشِ سلامت از `metrics.yaml`، red-teamِ هر PROPOSAL،
> `distance_from_genome` باید صفر باشد، خروجی propose-only به گیتِ مالک.»

- **Memory:** خلاقیت «تجربه» را از ledger می‌خواند و با سایر ایجنت‌ها ترکیب می‌کند.
- **Intelligence:** خلاقیت `default` (Sonnet 5)؛ دکتر `premium` (Opus 4.8) هفته‌ای یک‌بار.
- **Backup:** هر PROPOSAL/گزارش در ledger می‌ماند (audit trail؛ در بک‌اپ critical).
- **Definition of Done:** یک ایدهٔ نمونه از خلاقیت → دکتر → گیتِ مالک به‌درستی جریان
  یابد · هیچ ایجنتی چیزی جز ledger ننویسد · هر PROPOSAL دارای kill_criteria باشد.
- **Gate/ایمنی:** ضدِ reward hacking — evaluator در ژنوم، monitor≠signalِ بهینه‌شونده،
  هرگز آموزش علیه monitor.

---

## فاز ۴ — پایداری، بک‌اپ/DR و حلقهٔ تکامل (Hardening & Evolution Loop)
**هدف:** بستنِ حلقهٔ propose→approve و تضمینِ حافظه/هوش/بک‌اپِ کامل.

**پرامپت اجرا:**
> «حلقهٔ تکامل را ببند: `PROPOSAL → (۷۲h، فقط برای ژنوم) → APPROVAL مالک →
> branch → merge → APPLY`، همه در ledger. مانیتورینگ/لاگینگ را بالای متریک‌ها
> بگذار. بک‌اپِ ۳-۲-۱ را با restic/rclone رمز‌شده راه بینداز و یک restore drill
> ماهانه (بازیابی در پوشهٔ scratch + اجرای smoke_test) زمان‌بندی کن. Future Radar
> فصلی (افق ۲۴ماهه + سناریو ۳–۵ساله) را به دکتر تغذیه کن.»

- **Memory:** هر چهار نوعِ حافظه فعال و در بک‌اپ لحاظ شده.
- **Intelligence:** router نهایی (Haiku↔Sonnet5↔Opus4.8)؛ صرفه‌جوییِ ۴۰–۸۵٪ نسبت به
  «همه‌چیز با مدل بزرگ».
- **Backup:** DR واقعی — RTO ۴ساعت، RPO ۲۴ساعت، drill ماهانه (نه صرفاً روی کاغذ).
- **Definition of Done:** یک تغییرِ آزمایشی کلِ حلقه را طی کند · یک restore drill
  موفق · داشبوردِ متریک‌ها زنده · سقفِ ماهانهٔ هزینه رعایت شود.
- **Gate/ایمنی:** step/cost caps، گیت انسانی، مسیر ۷۲ساعتهٔ ژنوم — همگی فعال.

---

## نقشهٔ وابستگی فازها
```
فاز۰ ژنوم/ledger ──► فاز۱ ادراک/حافظه ──► فاز۲ گاردین ──► فاز۳ خلاقیت+دکتر ──► فاز۴ حلقه/بک‌اپ
        (قفل)              (رویدادمحور)        (۲۴ساعته)        (propose-only)        (DR + تکامل)
```

## سه تصمیمی که فقط مالک می‌گیرد
1. **اعداد نهاییِ بودجه** در `gates.yaml` (`owner_confirmed: true`).
2. **محتوای نسخهٔ ۱ ژنوم** — کدام ارزش‌ها invariant شوند.
3. **مرزِ privacyِ perception** و **مقصدِ off-site backup + custody کلید**.
