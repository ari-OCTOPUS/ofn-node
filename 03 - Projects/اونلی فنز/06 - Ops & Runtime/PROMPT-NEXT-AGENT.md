# پرامپت ایجنت بعدی: بازطراحی truthful cockpit + هم‌راستاسازی معماری «اختاپوس»

> تو agent بعدی برای بازطراحی truthful cockpit و هم‌راستاسازی معماری «اختاپوس» با کد واقعی هستی.  
> workspace: `F:/backup/03 - Projects/اونلی فنز/`  
> زبان: فارسی برای گزارش به آری؛ کد/کامنت انگلیسی.

---

## هدف

اختاپوس فعلی از نظر استعاره، observability و truth-cards زنده به نظر می‌رسد اما از نظر actuation و operator UX هنوز فلج است. می‌خواهیم استعاره را به قابلیت واقعی در دنیای واقعی تبدیل کنی.

---

## خواسته‌های قطعی

### الف) UI Audit — صداقت کامل

1. **همه دکمه‌ها/کنترل‌های UI را audit کن.**  
   - `langar_bot.py` (⚓ لنگر): `/kpi`, `/report` قبلاً اصلاح شدند (🔒 disabled-with-reason). بقیه را بررسی کن.
   - `saba_studio.py` (🎬 استودیو): `s:trend`, `s:ppv`, `s:stats`, `s:brief_ai` در ADVANCED_MENU با 🔒 coming-soon هستند. صحت این را تأیید کن.

2. **هر دکمه‌ای که واقعاً executable نیست، از UI حذف کن؛** اگر باید بماند، فقط به‌صورت **disabled with explicit reason**.

3. **هر عنصر مبهم/غیرواقعی** (placeholder, dummy data, fake metric) را اگر به capability واقعی وصل نیست از UI حذف کن.

4. **برای هر action قابل اجرا، مسیر کامل intent → approval → execution → result را مشخص کن.**  
   - مثال: `s:new` → `_start_new` → `_finish_draft` → `studio.submit_draft` → `drafts.json` → لنگر می‌خواند → آری تأیید → انتشار درون‌پلتفرم (خارج از سیستم).

### ب) هم‌راستاسازی استعاره اختاپوس

5. **metaphor اختاپوس را به معماری اجرایی map کن:**

| استعاره | نقش واقعی | مسئولیت |
|---|---|---|
| Brain A (عقل ۱) | Goal arbiter, policy engine, approval logic, priority queue | `langar_bot.py` + `shadow.py` + `governance.py` |
| Brain B (عقل ۲) | Learning/memory/evaluation/calibration/router selection | `learning.py` + `acquisition.py` + archive |
| Heart 1 (قلب حقیقت) | Telemetry, truth-cards, stale detection, provenance | `store.py` + ledger + verify |
| Heart 2 (قلب انرژی) | Budget, credits, tokens, rate limits, API quotas | `budget.py` + `CostMeter` |
| Heart 3 (قلب اجرا) | Execution retries, delivery confirmation, circuit breakers, actuation health | **فاقد — باید بسازی** |
| Arms (بازوها) | Bounded domain workers with local autonomy + sensing | `ziman-agent/worker.py` + `acquisition_pipeline.py` + `pf_admin.py` |
| Nervous System | Event bus + correlation + health + capability propagation | **فاقد — باید بسازی** |
| Suckers (بادکش‌ها) | Tool adapters / API connectors / file-system & channel handlers | `telegram.py` + raw `urllib` |

6. **بررسی کن کجاها فقط read-only truth داریم ولی motor output نداریم.**  
   - لیست کن: فایل، تابع، وضعیت فعلی، چه motor output باید باشد.

### ج) gap analysis

7. **برای هر بخش بالا، gap analysis بده:**
   - **current:** الان چه هست
   - **intended:** باید چه باشد
   - **missing wiring:** چه سیمی نبریده شده
   - **risks:** اگر وصل نشود چه می‌شود

### د) ساخت در worktree

8. **هر تغییر را در worktree بساز (نه روی live)، تست بنویس، patch تمیز تحویل بده.**

9. **فایل‌های جدیدی که باید بسازی:**
   - `event_bus.py` — lightweight pub/sub با `asyncio.Queue` یا polling روی `F:/backup/.bus/`
   - `actuator.py` — motor cortex: shadow → dry-run → live + approval gate
   - `capability_registry.py` — dynamic advertisement + revocation + UI sync
   - `telemetry.py` — sensory loop structured: `{job_id, duration, cost, error, outcome}`

10. **UI نهایی باید truthful باشد:**
    - no fake controls
    - no ambiguous state
    - no green-live rendering for stale snapshots

---

## خروجی‌های لازم

| خروجی | نام فایل | توضیح |
|---|---|---|
| A) گزارش معماری کوتاه | `OCTOPUS-ACTUATION-ALIGNMENT.md` (بروزرسانی) | gap analysis + نگاشت استعاره→کد |
| B) patch حذف/اصلاح UI controls | `patches/001-ui-truth.patch` | حذف دکمه‌های مرده + disabled-with-reason |
| C) patch capability-driven rendering | `patches/002-capability-sync.patch` | `capability_registry.py` + render logic |
| D) patch execution wiring | `patches/003-actuator-wiring.patch` | `actuator.py` + `event_bus.py` + `telemetry.py` |
| E) تست‌های regression | `tests/test_truthful_cockpit.py` | hidden controls, disabled reason, capability revoked, stale snapshot, action lifecycle |

---

## معیار موفقیت (قبول/رد — binary)

- [ ] هیچ دکمه مرده‌ای در UI نمانده.
- [ ] هر کنترل یا executable واقعی است، یا صریحاً non-executable با دلیل.
- [ ] operator بتواند بفهمد هر اندام اختاپوس چه می‌کند، با چه مجوزی، و در چه وضعیتی است.
- [ ] استعاره فقط تزئینی نیست؛ به کد، state machine و outcomes واقعی متصل است.

---

## محدودیت‌های سفت (hard constraints)

- **روی live چیزی ننویس** — فقط در worktree.
- **به `F:/backup` بدون approval آری ننویس** — این HIGH است.
- **swarm هرگز daemon را استارت نمی‌زند، اقدام مالی/بیرونی نمی‌کند** — HIGH = برگردان به آری.
- **verdict منفی = موفقیت** — اگر چیزی non-executable است، صریحاً بگو؛ نتایج را متورم نکن.
- **هر patch تمیز باشد** — یک concern per patch، diff قابل review.

---

## چک‌لیست قبل از تحویل

- [ ] همهٔ دکمه‌ها audit شدند؟
- [ ] capability registry ساخته و با UI sync شد؟
- [ ] actuator.py دارای shadow/dry-run/live است؟
- [ ] event_bus.py بدون dependency خارجی است؟
- [ ] تست‌ها pass می‌شوند؟
- [ ] گزارش به فارسی، با هر عدد تگ‌دار؟

> شروع کن از §0 Orient — فایل‌های جهت‌یابی (`PROJECT.md`, `CLAUDE.md`, `BRAIN-SPEC.md`) را بخوان، ساختار را پیدا کن، سپس wave 1 (UI audit) → wave 2 (capability registry) → wave 3 (actuator wiring).
