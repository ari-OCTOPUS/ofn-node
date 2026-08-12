# 🐙 HANDOFF: Project-F یکپارچه‌سازی کامل + هماهنگی با تلگرام اختاپوس

> **برای ایجنت بعدی:** این سند خودشكفاست. تمام پیشنهادها با file:line و دستورات دقیق.
> **تاریخ:** 2026-07-26 · **شاخه:** `claude/octopus-event-bridge-aligned`
> **هدف مالک:** «همرو یک‌پارچه کن، فیکس کن، با تلگرام هماهنگ کن.»
> **⚠️ مرز سخت:** GATE 0 قفل می‌مونه تا C واقعاً امضا کنه (بند ۱۲ توافق). **هیچ اکشن بیرونی.** همه‌چیز propose-only.

---

## 🎯 خلاصهٔ اجرا برای ایجنت بعدی

۶ کار propose-only که پروژه رو کاملأ یک‌پارچه و آمادهٔ لانچ می‌کنه (بدون بازکردن GATE 0):

| # | کار | فایل | خطر | زمان |
|---|-----|------|-----|------|
| ۱ | پرکردن blocklist واقعی لنگر | `langar/langar_config.json` (جدید) | کم | ۵د |
| ۲ | انتقال PII به پوشهٔ محافظت‌شده | `test/*.jpg` (۸ عکس) → `08 - Partner (PII)/` | کم | ۱۰د |
| ۳ | Scrub «Sydney»/«سیدنی» از کپی عمومی | ۱۰+ فایل `.md` | کم | ۱۵د |
| ۴ | فعال‌کردن LearningBridge | `pf_admin.py:24-62` (`_default_pipe`) | کم | ۵د |
| ۵ | یکپارچه‌سازی pf_os bridge با تلگرام اختاپوس | `pf_os/bridge.py` + organism ساب | متوسط | ۳۰د |
| ۶ | فعال‌سازی استودیو/اکتساب (propose-only) | flags + studio wiring | متوسط | ۲۰د |

**بعد از همه:** تست‌ها رو اجرا کن (۲۰۹ باید سبز بمونن).

---

## 🩺 وضعیت تأییدشده (از اسکن 2026-07-26)

### کد آماده‌ست:
- ✅ ۵ لایهٔ کامل: `brain/` · `studio/` · `langar/` · `pf_os/` · `acquisition_pipeline`
- ✅ **۲۰۹ تست سبز** (DL-2026-07-20-TESTS)
- ✅ VaultBank با ۲۲ asset seed شده (`langar/vault.json`)
- ✅ `LearningBridge` موجود (`brain/learning.py:263`) ولی اختیاریه
- ✅ `ThompsonBandit` موجود (`brain/learning.py:56`)
- ✅ `AcquisitionBrain.with_bandit()` موجود (`brain/acquisition.py:178`)
- ✅ pf_os bridge موجود (`pf_os/bridge.py`) با ۸ helper: `notify_draft_submitted`, `notify_halt`, `notify_resume`, `notify_boundary`, `notify_brain_tick`, `notify_kpi`, `notify_learning_observed`, `snapshot`

### نقص‌های تأییدشده:
- ❌ `langar/langar_config.json` **وجود نداره** (فقط `langar_config.example.json` هست) → scrubber fail-closed → هر send بلاک می‌شه
- ❌ ۸ عکس `test/photo_2026-07-03_*.jpg` (محتوا باز نشده — احتمالاً PII)
- ❌ کلمهٔ «Sydney»/«سیدنی» در ۱۰+ فایل کپی عمومی
- ❌ `LearningBridge` در `_default_pipe` (`pf_admin.py:24`) فعال نیست — فقط `with_bandit` (که خودش LearningBridge استفاده می‌کنه ولی خروجی به dایجست نمی‌رسه)
- ❌ pf_os bridge می‌نویسه به `saba-bridge.jsonl` ولی اختاپوس فعلاً **consumer‌اش فعال نیست** (در عملکرد تلگرام نمی‌رسه)

---

## 🔧 کار ۱ — پرکردن blocklist واقعی لنگر

### مشکل:
`langar_bot.py:474` (`send`) → `OpsecGuard.scrub` → اگر `policy_ok()` False باشه = **fail-closed** (هر send بلاک).
`langar_bot.py:129` (`policy_ok`): فقط وقتی True برمی‌گردونه که blocklist غیرخالی بارگذاری شده باشه.
الان `langar_config.json` وجود نداره → هر پیام لنگر بلاک می‌شه (حتی `/status` از بات واقعی).

### پیشنهاد:
فایل `langar/langar_config.json` بساز (untracked، gitignored). **الگوی `langar_config.example.json`** رو کپی کن و placeholderها رو با مقادیر واقعی پر کن:
```json
{
  "blocklist": [
    "نام_خانوادگی_واقعی_صبا",
    "شماره_موبایل_واقعی",
    "آدرس_واقعی"
  ],
  "city_terms": ["Sydney", "سیدنی", "sydney"],
  "name_map": {"نام_واقعی_صبا": "C", "نام_واقعی_آری": "A"},
  "project_code": "Project-F"
}
```

### مهم:
- **این فایل هرگز commit نشه.** چک کن `.gitignore` شامل `langar_config.json` باشه (همونطور که `.example` نشانه داده).
- مقادیر واقعی رو **مالک تأمین کنه** — تو فقط ساختار رو بساز و placeholder بذار، یا اگه مقادیر رو داری (از `.env`/پرسشنامه) جایگزین کن.
- بعد از ساخت: `langar_bot.py` ری‌استارت بشه تا scrubber باز بشه.

### Verify:
```bash
cd "03 - Projects/اونلی فنز"
python -c "from langar.langar_bot import LangarBot; b=LangarBot(); print('policy_ok:', b.guard.policy_ok())"
# باید: policy_ok: True
```

---

## 🔧 کار ۲ — انتقال PII از test/

### مشکل:
```
test/photo_2026-07-03_20-34-55.jpg
test/photo_2026-07-03_20-34-56.jpg
test/photo_2026-07-03_20-34-58.jpg
test/photo_2026-07-03_20-35-00.jpg
test/photo_2026-07-03_20-35-02.jpg
test/photo_2026-07-03_20-35-04.jpg
test/photo_2026-07-03_20-35-06.jpg
test/photo_2026-07-03_20-35-08.jpg
```
این‌ها احتمالاً PII هستن (محتوا تأیید نشده — DL-2026-07-20-PII-INCIDENT). قانونِ پروژه: «هرگز حذف نکن، فقط منتقل کن.»

### پیشنهاد:
```bash
cd "03 - Projects/اونلی فنز"
mkdir -p "08 - Partner (PII)/photos"
git mv "test/photo_2026-07-03_"*.jpg "08 - Partner (PII)/photos/"
# اگه git-tracked نیستن:
# mv "test/photo_2026-07-03_"*.jpg "08 - Partner (PII)/photos/"
```

### مهم:
- ابتدا چک کن آیا این عکس‌ها اصلاً در تست استفاده می‌شن: `grep -rn "photo_2026" --include="*.py" .`
- اگه در تست هستن، fixture جایگزین بساز (placeholder image).
- پوشهٔ `08 - Partner (PII)/` از قبل gitignored احتمالاً هست — `.gitignore` رو چک کن.

### Verify:
```bash
ls "08 - Partner (PII)/photos/"  # باید ۸ عکس باشن
ls "test/"*.jpg 2>/dev/null  # باید خالی باشه
```

---

## 🔧 کار ۳ — Scrub «Sydney»/«سیدنی» از کپی عمومی

### مشکل:
کلمه در ۱۰+ فایل کپی عمومی هست (R9 — پیش‌نیاز bio). قانونِ قفل‌شدهٔ #۶: «سیگنال فرهنگی فقط بصری، نه متنی.»

### فایل‌های هدف (از اسکن):
```
./00 - Control/SCAN-LOCK-2026-07-20.md
./00 - Control/GATE-STAMP-2026-07-20.md
./00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/*.md (۵ فایل)
./01 - Strategy/MASTER-BUILD-2026-07-04.md
./01 - Strategy/project-master-reference.md
./02 - Research/*.md (چند فایل)
./06 - Ops & Runtime/LAUNCH-RUNBOOK-2026-07-16.md
./ACQUISITION-ENGINE-2026-07-05.md
./DecisionLog.md
```

### پیشنهاد:
- **توجه:** در `DecisionLog.md` و فایل‌های audit/governance کلمه «سیدنی» **عمداً ثبت شده** (مثلاً «Branch A = سیدنی تأیید شد»). این‌ها **تاریخچه‌ان و نباید scrub بشن** — آن‌ها فکت‌اند.
- فقط کپی‌های **عمومی/کاربر-رو** رو scrub کن: bio، link-hub copy، profile copy، caption template.
- الگو: `Sydney` → `⟦geo⟧` یا حذف کامل. `سیدنی` → حذف یا `⟦geo⟧`.
- **روش امن:** اول `grep -rn "Sydney" <file>` ببین context چی هست. اگه audit/governance/fact هست → دست نزن. اگه copy/bio/caption هست → scrub.

### پیشنهاد اسکوپ‌محور:
```bash
# فقط فایل‌های copy-driven (نه audit/history):
FILES=(
  "drafts-awaiting-gate/link-hub-copy.md"
  "drafts-awaiting-gate/bio-template.md"
  "studio/"  # هر caption template
)
# هر فایل رو دستی بازبینی کن؛ جایگزینی کور ممنوع.
```

### Verify:
```bash
grep -rn "Sydney\|سیدنی" drafts-awaiting-gate/ studio/ 2>/dev/null
# باید خالی باشه (در copy کاربر-رو)
```

---

## 🔧 کار ۴ — فعال‌کردن LearningBridge در pf_admin

### مشکل:
`pf_admin.py:24-62` (`_default_pipe`) الان از `AcquisitionBrain.with_bandit()` استفاده می‌کنه (که خودش LearningBridge داره) ولی **خروجی یادگیری به digest/تلگرام نمی‌رسه**. ROADMAP مرحلهٔ ۵: «`LearningBridge` را در `pf_admin._default_pipe()` پیش‌فرض کن.»

### پیشنهاد:
`pf_admin.py:24-62` رو بازنویسی کن تا `LearningBridge` صریح ساخته و به pipeline تزریق بشه، و خروجی یادگیری (memory decay, bandit weights) در `admin_digest` قابل‌مشاهده بشه:

```python
# pf_admin.py، جایگزینِ _default_pipe (line 24):
def _default_pipe():
    from acquisition_pipeline import AcquisitionPipeline
    brain = None
    learner = None  # ← جدید: صریح بساز
    try:
        from acquisition import AcquisitionBrain, AcquisitionMemory
        from learning import LearningBridge, DEFAULT_HALFLIFE_DAYS
        mem = AcquisitionMemory()
        learner = LearningBridge(mem, halflife_days=DEFAULT_HALFLIFE_DAYS)
        # با bandit (exploration-aware) + learner صریح
        if hasattr(AcquisitionBrain, "with_bandit"):
            brain = AcquisitionBrain.with_bandit(memory=mem, learner=learner)
        else:
            brain = AcquisitionBrain(memory=mem, learner=learner)
    except Exception:
        brain = None
    # ... (بقیهٔ warmup/locks/vault/links مثل قبل)
    pipe = AcquisitionPipeline(brain=brain, warmup=warmup, locks=locks, vault=vault, links=links)
    pipe._learner = learner  # ← برای expose در digest
    return pipe
```

### مهم:
- **اولاً چک کن** که `AcquisitionBrain.with_bandit` پارامتر `learner` قبول می‌کنه (`brain/acquisition.py:178`). اگه نه، first اون رو extend کن.
- در `handle_pf` خط `/pf_status`، یه بخش «یادگیری» اضافه کن: `learner` snapshot (n_observations، top tag weights).
- **تست:** `test_pf_admin.py` باید همچنان سبز بمونه. اگه signature عوض شد، تست رو update کن.

### Verify:
```bash
cd "03 - Projects/اونلی فنز/langar"
python -m pytest test_pf_admin.py -v
python -c "from pf_admin import _default_pipe; p=_default_pipe(); print('learner:', getattr(p, '_learner', None))"
```

---

## 🔧 کار ۵ — یکپارچه‌سازی pf_os bridge با تلگرام اختاپوس (هسته)

### مشکل:
`pf_os/bridge.py` به `_ops/state/saba-bridge.jsonl` می‌نویسه (file-pubsub). ولی اختاپوس فعلاً **هیچ consumer‌ای روش loop نمی‌زنه** — یعنی Project-F به ارگانیسم پیام می‌ده ولی ارگانیسم نادیده می‌گیره. پیوند یک‌طرفه‌ست.

### وضعیت فعلی:
- `pf_os/bridge.py:33` (`bridge_path`): `Path(config.OPS_STATE) / "saba-bridge.jsonl"`
- `pf_os/bridge.py:111` (`publish`): ۸ helper (draft_submitted, halt, resume, boundary, brain_tick_done, notify, kpi, learning_observed)
- `pf_os/bridge_beat.py:47` (`saba_bridge_beat`): تابعی که event‌ها رو از فایل می‌خونه و به handler می‌ده — ولی فعلاً **به wiring اختاپوس وصله نیست**.

### پیشنهاد (دو مرحله):

#### ۵.۱ — `saba_bridge_beat` رو به organism wire کن
در `_ops/wiring.py`، یه beat جدید بساز که `pf_os.bridge_beat.saba_bridge_beat` رو صدا بزنه و به `_chan` (تلگرام) وصل کنه:

```python
# _ops/wiring.py (اضافه کن):
def pf_bridge_beat(channel=None, beat: int = 0) -> dict | None:
    """خواندن رویدادهای Project-F از saba-bridge.jsonl → کارت تلگرام.
    propose-only؛ هیچ اکشن بیرونی. پشتِ OCTOPUS_WIRE_PF_BRIDGE."""
    if not flag("OCTOPUS_WIRE_PF_BRIDGE"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        sys.path.insert(0, str(_HERE.parent / "03 - Projects" / "اونلی فنز" / "pf_os"))
        import bridge_beat as _bb
        def _to_tg(rec: dict):
            if channel is None or not getattr(channel, "wired", False):
                return
            kind = rec.get("kind", "notify")
            text = rec.get("text", "")
            count = rec.get("count", 0)
            # stream = "studio" → تاپیک studio_pf (27) در group
            channel.send_text(f"🎬 Project-F: {kind} — {text} (count={count})",
                              stream="studio")
        r = _bb.saba_bridge_beat(handler=_to_tg)
        return r
    except Exception as e:
        opslib.alert([f"pf_bridge_beat error: {type(e).__name__}: {e}"])
        return None
```

و در `organism.py`، بعد از سایر beatها (حدود line 875):
```python
if not _protective_skip:
    try:
        _w.pf_bridge_beat(_chan, beat=_cstat.get("beat", 0) if _cstat else 0)
    except Exception as _pfe:
        opslib.alert([f"pf_bridge_beat error (non-fatal): {type(_pfe).__name__}"])
```

#### ۵.۲ — stream routing اضافه کن
در `_ops/budget/approval_channel.py:118-121` (`_STREAM_TOPIC`):
```python
"studio" → "studio_pf",  # → تاپیک 27
"pf" → "studio_pf",
```

#### ۵.۳ — flag روشن کن
در `_ops/OCTOPUS-flags.cmd` اضافه کن:
```
set OCTOPUS_WIRE_PF_BRIDGE=1
```

### مهم:
- مسیر فارسی `03 - Projects/اونلی فنز/pf_os` ممکنه روی ویندوز مشکل درست کنه. با `sys.path.insert` و `Path` абсолют تست کن.
- `pf_os` یک **package** هست (`__init__.py` داره) — relative importها داره. اگه import شکست، از `bridge_beat` مستقیم (نه از پکیج) استفاده کن.
- **هر پیام PII می‌گیره** ( scrub `_scrub_summary` در `bridge.py:98`) — ولی در سمت اختاپوس هم یه لایهٔ دوم scrub بذار (`_BANNED_ECHO`).
- throttle: از الگوی `_dialogue_gate` استفاده کن تا از spam جلوگیری بشه.

### Verify:
```bash
# دستی یه رویداد به bridge بنویس:
cd "03 - Projects/اونلی فنز/pf_os"
python -c "import bridge; bridge.notify_draft_submitted('test-001', 3)"
# بعد چک کن:
tail -1 "F:/backup/_ops/state/saba-bridge.jsonl"
# باید یه ردیف جدید با kind=draft_submitted باشه.
# بعد از restart organism، در تاپیک studio_pf گروه باید کارت بیاد.
```

---

## 🔧 کار ۶ — فعال‌سازی استودیو/اکتساب (propose-only)

### مشکل:
استودیوی Creator و قیف اکتساب کاملأ ساخته شدن ولی فعلاً «خاموش» هستن — یعنی pipeline در حال تولید draft نیست. این کار propose-only هست و **بدون GATE 0 مجازه** (draft داخلی، صفر پست).

### پیشنهاد:

#### ۶.۱ — استودیو رو به‌صورت advisory فعال کن
استودیوی Creator (`studio/creator_studio.py`) رو بررسی کن. فعلاً HALT یا idle هست. می‌تونی:
- در `studio/drafts.json` چک کن چند draft هست.
- `/pf_plan 5` رو از لنگر اجرا کن تا ۵ draft از VaultBank ساخته بشه (۲۲ asset موجوده).
- این draftها به‌صورت propose-only در صف می‌شینن، منتظر `/pf_ok`.

#### ۶.۲ — قیف اکتساب رو «گرم» کن
```bash
cd "03 - Projects/اونلی فنز/langar"
# شبیه‌سازی (بدون تلگرام واقعی):
python -c "
from pf_admin import handle_pf
print(handle_pf('/pf_status'))
print(handle_pf('/pf_plan', '5'))
print(handle_pf('/pf_queue'))
"
```

#### ۶.۳ — Learning loop رو پر کن
- `VaultBank` با ۲۲ asset هست (`langar/vault.json`).
- `/pf_plan` از VaultBank draft می‌سازه.
- اگه LearningBridge (کار ۴) فعاله، هر approve/reject یاد می‌گیره و weightها به‌روز می‌شن.

### مهم:
- **هیچ‌کدام از این draftها نباید به بیرون برن.** فقط در `drafts.json` (gitignored) ذخیره می‌شن.
- warm-up guard فعاله: اگه karma آستانه نداشته باشه، `/pf_ready` بلاک می‌شه (درست).
- `OCTOPUS_WIRE_PF_BRIDGE` (کار ۵) هر فعالیت استودیو رو به تلگرام اختاپوس می‌فرسته.

### Verify:
```bash
cat "03 - Projects/اونلی فنز/studio/drafts.json" | python -c "import json,sys; d=json.load(sys.stdin); print(f'drafts: {len(d)}')"
```

---

## 🧪 کار ۷ — تست و verify نهایی

### پیشنهاد:
```bash
cd "03 - Projects/اونلی فنز"

# ۱. تست‌های Project-F (۲۰۹ باید سبز):
python -m pytest tests/ -q
cd studio && python -m pytest test_saba_studio.py -q && cd ..
cd brain && python -m pytest test_acquisition_pipeline.py test_learning.py -q && cd ..
cd langar && python -m pytest test_langar.py test_pf_admin.py -q && cd ..

# ۲. تلفیق pf_os (اگه کار ۵ انجام شد):
cd _ops && python -m pytest tests/ -q
```

### Verify نهایی یکپارچه‌سازی:
```bash
# ۱. langar scrubber فعال:
cd "03 - Projects/اونلی فنز"
python -c "from langar.langar_bot import LangarBot; b=LangarBot(); print('scrub:', b.guard.policy_ok())"

# ۲. PII منتقل شده:
ls "08 - Partner (PII)/photos/" 2>/dev/null | wc -l  # باید ۸ باشه

# ۳. LearningBridge فعال:
python -c "from langar.pf_admin import _default_pipe; p=_default_pipe(); print('learner:', bool(getattr(p,'_learner',None)))"

# ۴. pf_os bridge write:
python -c "import sys; sys.path.insert(0,'pf_os'); import bridge; print('publish test:', bridge.notify_brain_tick(1))"

# ۵. Sydney scrubbed (در copy):
grep -rn "Sydney" drafts-awaiting-gate/ studio/ 2>/dev/null | head  # باید خالی
```

---

## ⚠️ مرزهای سخت (هیچ‌وقت نشکن)

1. **GATE 0 قفل می‌مونه.** هیچ اکشن بیرونی (پست/DM/ساخت اکانت) تا امضای واقعی C.
2. **`langar_config.json` هرگز commit نشه.** در `.gitignore` هست.
3. **عکس‌ها حذف نشن.** فقط منتقل بشن به `08 - Partner (PII)/`.
4. **«Sydney» در DecisionLog/audit دست نمی‌خوره.** فقط در copy کاربر-رو scrub بشه.
5. **هیچ auto-send.** AI draft می‌زنه، انسان می‌فرسته.
6. **توکن/`.env` هرگز لو نره.**
7. **هر تغییر، additive + fail-soft.** خرابی → flag `=0` یا STOP.

---

## 📁 فایل‌هایی که دست می‌خورن

**جدید:**
- `langar/langar_config.json` (با placeholder، بعد مالک پر می‌کنه)
- `_ops/wiring.py::pf_bridge_beat` (تابع جدید)
- `_ops/tests/test_pf_bridge.py` (تست جدید)

**ویرایش:**
- `pf_admin.py:24-62` (`_default_pipe` + LearningBridge)
- `_ops/organism.py` (فراخوانی `pf_bridge_beat`، ~line 875)
- `_ops/budget/approval_channel.py:118-121` (`_STREAM_TOPIC` + studio/pf)
- `_ops/OCTOPUS-flags.cmd` (`OCTOPUS_WIRE_PF_BRIDGE=1`)
- ۱۰+ فایل `.md` (Sydney scrub، در copy فقط)

**انتقال:**
- `test/photo_2026-07-03_*.jpg` → `08 - Partner (PII)/photos/`

---

## 🎯 ترتیب اجرای پیشنهادی برای ایجنت بعدی

1. **کار ۱** (blocklist) — سریع‌ترین، بالاترین ارزش (scrubber باز می‌شه).
2. **کار ۴** (LearningBridge) — کد، آزموده‌شده.
3. **کار ۲** (PII انتقال) — امن، قابل rollback.
4. **کار ۳** (Sydney scrub) — دقت‌محور، فایل‌به‌فایل.
5. **کار ۵** (pf_os bridge) — پیچیده‌ترین، بعد از بقیه.
6. **کار ۶** (استودیو فعال) — بعد از bridge تا خروجی دیده بشه.
7. **کار ۷** (تست) — آخر، همه‌چیز رو verify.

**بعد از همه:** پروژه کاملأ یکپارچه‌ست، آمادهٔ لانچ. وقتی C توافق رو امضا کرد، فقط `GATE-STAMP` رو به GO تغییر بده و DAY-ZERO شروع می‌شه.

---

## 🔗 اسناد مرتبط

- پلن بازنویسی تلگرام: `_ops/HANDOFF-TELEGRAM-REWRITE.md`
- ROADMAP ۱۰-مرحله‌ای: `00 - Control/ROADMAP-10-STAGES-2026-07-12.md`
- DecisionLog: `DecisionLog.md` (به‌خصوص DL-2026-07-20-AGREEMENT، DL-2026-07-20-PII-INCIDENT)
- GATE-STAMP: `00 - Control/GATE-STAMP-2026-07-20.md`
- manifest: `PROJECT-F-CONTROL-MANIFEST.json`

**موفق باشی. از کار ۱ شروع کن — blocklist لنگر، سریع‌ترین برد.**
