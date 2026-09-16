# 🐙 HANDOFF: بازنویسی لایهٔ تلگرام اختاپوس

> **برای ایجنت بعدی:** این سند خودشكفاست. تمام context، file:line، و دستورات لازم اینجاست.
> نیازی به اسکن مجدد نیست — مستقیم از فاز ۰ شروع کن.
> **تاریخ:** 2026-07-26 · **شاخه:** `claude/octopus-event-bridge-aligned`
> **وضعیت:** پلن توسط مالک تأیید شد (بازنویسی کامل لایهٔ تلگرام).

---

## 🎯 هدف نهایی

تلگرام اختاپوس از حالت فعلی:
- ❌ هر ۶ ساعت یک کارت خلاصه + چندتا اسپم تکراری
- ❌ رویدادهای مهم صف می‌شن تا دایجست بعدی
- ❌ پتانسیل‌های خفته (C6/Harvest/lead) کد دارن ولی خروجی نمی‌رسه

تبدیل بشه به:
- ✅ **صفر اسپم** (تک‌نمونه‌ای‌سازی + dedup سراسری)
- ✅ **صفر پیام تکراری** (hash dedup مرکزی)
- ✅ **رویدادهای مهم فوری برسن** (event→telegram bridge)
- ✅ **پتانسیل‌های خفته روشن بشن** (C6/Harvest/lead cards)

---

## 🩺 وضعیت زنده (عکسِ لحظهٔ اسکن)

### پروسه‌های در حال اجرا (۴ پروسه Python):
```
PID 27400 → python -X utf8 organism.py              # حلقه اصلی (منبع اسپم)
PID 20120 → python -X utf8 telegram_center\center.py # digest هر ۸ پا
PID 8132  → python -X utf8 live\server.py            # داشبورد (8770)
PID 27248 → python -X utf8 cortex\cortex.py          # مغز (8772)
```

### شواهد چندنمونه‌ای بودن:
```
_ops/state/cockpit-requests.lock → "8360:2026-07-25T21:48:26"
                                  ↑ این PID قبلی است، ولی الان 27400 اجراست
                                    → ممکنه قبلاً دو نمونه همزمان اجرا شده باشن
```

### ۳ بات تلگرام فعال (از `.env`):
```
TELEGRAM_BOT_TOKEN      → بات Octopus/Langar + approval_channel (owner: 6150431610)
TG_CENTER_BOT_TOKEN     → بات مرکز فرماندهی (گروه forum: -1004475788460)
TG_ZIMAN_STUDIO_BOT_TOKEN → ربات مامان/زیمان
```

---

## 🔥 منابع اسپم (ریشه‌یابی شده با file:line)

### منبع ۱: ۶ تابع beat که هر tick به owner پیام می‌زنن
`organism.py:875-877` این ۶ تا رو صدا می‌زنه:

| تابع | فلگ لازم | فایل throttle state | آخرین ارسال مشاهده‌شده |
|------|----------|---------------------|----------------------|
| `needs_nudge_beat` | `OCTOPUS_WIRE_NEEDS_NUDGE` | `state/needs-nudge.json` | 2026-07-26 09:39:47 |
| `discovery_nudge_beat` | `OCTOPUS_WIRE_NEEDS_NUDGE` | `state/alerts/` (نبود) | فعال |
| `doctor_digest_beat` | `OCTOPUS_WIRE_DOCTOR_DIGEST` | `state/doctor/digest-nudge.json` | 2026-07-26 02:16:55 |
| `brain_digest_beat` | `OCTOPUS_WIRE_BRAIN_DIGEST` | `state/cortex/brain-digest-nudge.json` | 2026-07-26 04:49:44 |
| `heart_card_beat` | `OCTOPUS_WIRE_HEART_CARD` + `OCTOPUS_WIRE_PULSE` | `state/pulse/heart-card-nudge.json` | 2026-07-26 09:39:52 |
| `heartbeat_summary_beat` | (رویداد، بی‌صدا) | — | — |

**تعریف توابع:** همه در `wiring.py`:
- `needs_nudge_beat` → `wiring.py:2387`
- `cortex_vitals_beat` → `wiring.py:2443` (این بی‌صدا، فقط state)
- `heartbeat_summary_beat` → `wiring.py:2469` (این رویداد emit می‌کنه، نه تلگرام)
- `discovery_nudge_beat` → `wiring.py:2637`
- `doctor_digest_beat` → `wiring.py:2718`
- `brain_digest_beat` → `wiring.py:2747`
- `heart_card_beat` → `wiring.py:2782`

### منبع ۲: `telegram_center/center.py` — digest هر ۹ تاپیک
`center-config.json` نشان می‌ده ۹ تاپیک ساخته شده و `last_digest` همه‌شون تقریباً همزمان:
```json
"topics": {"lead":22, "ziman":23, "mining":24, "crypto":25, "accounting":26,
           "studio_pf":27, "system":28, "knowledge":29, "cartographer":65}
"last_digest": {همه ≈ 1784980943}  ← یعنی به همه ۹ تاپیک همزمان پست می‌کنه
```

### منبع ۳: ریسک 409 Conflict
`tg_api.py:169-178` هشدار داده: اگر `TG_CENTER_BOT_TOKEN` نباشه و fallback به `TELEGRAM_BOT_TOKEN` بشه، با `approval_channel` که داخل `organism.py` poll می‌کنه روی **409 Conflict** می‌خوره.
الان هر دو توکن ست‌شده، ولی بعد از restart باید مطمئن بشی هر پروسه توکن درست رو می‌خونه.

### منبع ۴: watchdog‌ها که نمونهٔ کشته‌شده رو دوباره بالا میارن
```
_ops/cortex-watchdog.ps1
_ops/live-watchdog.ps1
_ops/organism-watchdog.ps1
_ops/tg-center-watchdog.ps1
_ops/register-tg-center-watchdog.ps1
```

---

## 🛠️ الگوهای موجود (هرگز از نو نساز — reuse کن)

### الگوی throttle/hash (قلبِ ضد اسپم)
**`_dialogue_gate`** (`wiring.py:2713-2729`):
```python
def _dialogue_gate(state_name, new_hash, min_interval_s, force=False) -> bool:
    # state/<state_name>.json = {"last_hash", "last_ts"}
    # ارسال وقتی: (hash عوض شده AND age > min_interval_s) یا force (با کف 300s)
    # force=True فقط age > 300 رو چک می‌کنه، hash رو نادیده می‌گیره
```
**`_dialogue_mark`** (`wiring.py:2732-2741`):
```python
def _dialogue_mark(state_name, new_hash):
    # با LockedJson می‌نویسه {"last_hash", "last_ts", "ts"}
```

### الگوی instant force-send
`brain_digest_beat` (`wiring.py:2789-2798`):
```python
red_flip = ("🔴" in cur) and ("🔴" not in prev) and prev != ""
_dialogue_gate(..., force=red_flip)   # فوری، با کف 300s
head = "🚨 تنشِ مغز 🔴 شد!\n" + d["text"]
```

### الگوی send_text با topic routing
`TelegramApprovalChannel.send_text` (`budget/approval_channel.py:1382-1407`):
```python
def send_text(self, text, reply_markup=None, chat_id=None, stream=None) -> bool:
    # chat_id=None → self._owner (DM)
    # stream="lead" → _stream_route → (chat_id, topic_id) از center-config.json
    # اگر stream معتبر → message_thread_id = topic_id
```

### `_STREAM_TOPIC` فعلی (`budget/approval_channel.py:118-121`):
```python
_STREAM_TOPIC = {
    "heart" → "system", "doctor" → "system",
    "needs" → "system", "summary" → "system",
    "brain" → "knowledge", "discovery" → "knowledge",
    "map" → "cartographer"
}
# ❌ نقص: lead, c6, cortisol, alert تعریف نشدن
```

### الگوی exclusive bind (قفل تک‌نمونه)
`organism.py:126-134` و `190-194`:
```python
class _ExclusiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()
```

### الگوی wiring در organism.py
`organism.py:282-400`: ساخت `_chan`, `_bus`, `_live_loop`. اضافه‌کردن subscriber باید بعد از line 327 (`make_live_loop`) باشه.

---

## 📊 پتانسیل‌های خفته (کد دارن ولی خروجی نمی‌رسه)

### الف) روشن ولی به تلگرام نمی‌رسن:

| قابلیت | flag | منبع داده | چی تو تلگرام دیده می‌شه |
|--------|------|-----------|--------------------------|
| کورتکس (مغز) | `CORTEX_THINK_EVERY_N=1` | `state/cortex/stress-latest.json` | فقط کارت ۶ساعته |
| دکتر خودشناسی | `OCTOPUS_WIRE_DOCTOR_SELFKNOW_PAID=1` | iterative | فقط RFC پیشنهاد |
| لید مستقیم مسکونی | `OCTOPUS_LEAD_DIRECT_RESIDENTIAL=1` | `state/ORGANISM-STATE.lead_discovery` | فقط در state |
| C6 Producer | `OCTOPUS_WIRE_C6_PRODUCER=1` | `state/c6/hypothesis-queue.jsonl` | **هیچ** (تا flag فاز ۴) |
| Debate | `OCTOPUS_WIRE_DEBATE=1` | `debate/SURVIVORS-QUEUE.md` | فقط شمارش |
| Epistemics | `OCTOPUS_WIRE_EPISTEMICS=1` | advisory | هیچ |
| Selfheal | `OCTOPUS_WIRE_SELFHEAL=1` | پای خراب | فقط alert خطا |

### ب) کاملأ خاموش (کد هست، flag `=0`):

| قابلیت | flag | ارزش |
|--------|------|------|
| C6 self-repair | `OCTOPUS_WIRE_C6_RESEARCH=1` ✓ ولی `ACTIVATION-C6-RESEARCH.flag` ✓ موجود | خودبهبودی کد |
| Harvest (AusTender) | `OCTOPUS_WIRE_HARVEST=0` | لید رایگان دولتی |
| Mission Runner | `OCTOPUS_WIRE_MISSION_RUNNER=0` | ماموریت مستقل |
| Romajan Probes | `OCTOPUS_WIRE_ROMAJAN_PROBES=0` | پل آزمایشگاه فیزیکی |
| PocketSmith | `OCTOPUS_WIRE_POCKETSMITH=0` | سینک بانک |
| Email inbound | (wire نیست) | پردازش ایمیل |
| Lead Draft | `OCTOPUS_WIRE_LEAD_DRAFT=0` | درفت قیمت |

---

## 📋 خلاصهٔ flagهای روشن (از `OCTOPUS-flags.cmd`)

### flagهای مرتبط با تلگرام (همگی روشن، علت اسپم):
```
set OCTOPUS_WIRE_HEART=1
set OCTOPUS_WIRE_HEART_WORK=1
set OCTOPUS_WIRE_NEEDS_NUDGE=1
set OCTOPUS_WIRE_PULSE=1
set OCTOPUS_WIRE_DOCTOR_DIGEST=1
set OCTOPUS_WIRE_BRAIN_DIGEST=1
set OCTOPUS_WIRE_HEART_CARD=1
set OCTOPUS_WIRE_PROPOSAL_BUTTONS=1
set OCTOPUS_WIRE_DOCTOR_KNOB_RFC=1
set OCTOPUS_WIRE_MENU_V2=1
set OCTOPUS_TG_LLM_ASK=1
set OCTOPUS_TG_POWER=1
set OCTOPUS_TG_EXEC=1
set OCTOPUS_TG_TOPIC_REPLY=1
set OCTOPUS_TG_QUIET=1
set OCTOPUS_WIRE_VERDICT_OUTCOME=1
set OCTOPUS_WIRE_SPINE=1
```

### flagهای خوابیدهٔ مهم (پتانسیل):
```
set OCTOPUS_WIRE_HARVEST=0          ← لید رایگان AusTender
set OCTOPUS_WIRE_C6_RESEARCH=1      ← C6 (flag file هم هست)
set OCTOPUS_WIRE_POCKETSMITH=0      ← بانک
set OCTOPUS_WIRE_MISSION_RUNNER=0   ← ماموریت
```

### کادنس‌ها (مقادیر پیش‌فرض در wiring.py):
```
CHRONO_NUDGE_EVERY_N_BEATS = 360        (~۶ ساعت با beat 60s)  → needs_nudge
CHRONO_DISCOVERY_NUDGE_EVERY_N_BEATS = 480  (~۸ ساعت)            → discovery
CHRONO_DOCTOR_DIGEST_MIN_S = 21600      (۶ ساعت)                → doctor
CHRONO_BRAIN_DIGEST_MIN_S = 21600       (۶ ساعت)                → brain
CHRONO_HEART_CARD_MIN_S = 21600         (۶ ساعت)                → heart
```

---

## 🗺️ داده‌های state برای instant alerts (آماده)

| رویداد | فایل state | فیلد کلیدی | آستانه |
|--------|-----------|------------|--------|
| C6 hypothesis جدید | `state/c6/hypothesis-queue.jsonl` | `card_delivered: false` | هر ردیف جدید |
| Lead مستقیم | `state/ORGANISM-STATE.lead_discovery` | `n_new` | > 0 |
| Cortisol 🔴 | `state/cortex/cortisol-state.json` | `level` | "🔴" |
| Discovery | `state/discoveries.jsonl` vs `state/discoveries-seen.json` | `n_unseen` | > 0 |
| Doctor RFC بحرانی | `state/doctor/rfcs.json` | `severity` | ≥ 4 |
| Stress 🔴 | `state/cortex/stress-latest.json` | `level` | "🔴 ترس" |

### ساختار `state/c6/hypothesis-queue.jsonl`:
```json
{"id":"...", "status":"DONE", "kind":"micro_benchmark", "question":"...",
 "hypothesis":"...", "verdict":"accepted", "card_delivered": false, ...}
```
**نکته:** `card_delivered: false` هوک طبیعی برای push به تلگرام است. هیچ consumer‌ای روش loop نمی‌زنه.

---

## ✅ فازهای اجرا (به ترتیب)

### فاز ۰ — توقف فوری (۵ دقیقه)
```bash
# ۱. پروسه‌های تکراری رو پیدا کن:
powershell -Command "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Select ProcessId,CommandLine | Format-List"
# اگر چند نمونه organism.py یا center.py هست → یکی رو نگه‌دار، بقیه رو:
# taskkill /PID <id> /F

# ۲. (اگه لازم) kill-switch بساز:
touch _ops/STOP-ORGANISM
touch _ops/STOP-TG-CENTER
```

### فاز ۱ — تک‌نمونه‌ای‌سازی + رفع 409
- `organism.py:290` و `telegram_center/center.py` رو چک کن که توکن درست استفاده می‌شه.
- به `center.py` و `cortex.py` قفل exclusive bind اضافه کن (الگوی `organism.py:126-134`).
- watchdog‌ها (`*.ps1`) رو چک کن — اگه بعد از kill دوباره spawn می‌کنن، موقتاً غیرفعال.

### فاز ۲ — ماژول `tg_dedup.py` (جدید)
```python
# _ops/tg_dedup.py
# hash(text + chat_id + topic_id) → state/tg-sent-hashes.jsonl (append-only)
# با flock ویندوزی. send_text قبل از POST چک می‌کنه.
# اگر در ۱ ساعت گذشته با همین hash فرستاده شده → skip.
# rotation روزانه (خط‌های > 24 ساعت حذف).
```
هوک در `budget/approval_channel.py:1382` (`send_text`): قبل از POST، `tg_dedup.should_send(...)` صدا بزن.

### فاز ۳ — ماژول `instant_alert_bridge.py` (هسته)
```python
# _ops/instant_alert_bridge.py
# subscribe به bus + watch state files برای:
#   - C6 hypothesis (card_delivered: false)
#   - lead جدید
#   - cortisol 🔴
#   - discovery جدید
#   - doctor severity ≥ 4
# هر کدوم با _dialogue_gate(force=...) throttle می‌شه.
```
wiring در `organism.py` بعد از line 327:
```python
if _chan is not None and _bus is not None:
    try:
        import instant_alert_bridge as _iab
        _iab.wire(_chan, _bus, state_dir=str(opslib.STATE_DIR))
    except Exception as _iae:
        opslib.alert([f"instant_alert_bridge wire failed: {_iae}"])
```
گسترش `_STREAM_TOPIC` در `approval_channel.py:118-121`:
```python
"lead" → "lead", "c6" → "knowledge", "cortisol" → "system", "alert" → "system"
```

### فاز ۴ — فعال‌سازی پتانسیل
- `OCTOPUS_WIRE_HARVEST=1` (خط 25 flags.cmd)
- کادنس دایجست‌ها طولانی‌تر:
```
set CHRONO_DOCTOR_DIGEST_MIN_S=43200
set CHRONO_BRAIN_DIGEST_MIN_S=43200
set CHRONO_HEART_CARD_MIN_S=43200
set CHRONO_NUDGE_EVERY_N_BEATS=720
```

### فاز ۵ — تست + verify
```bash
cd _ops
python -m pytest tests/test_tg_center.py tests/test_tg_api.py tests/test_telegram_channel.py -v
```
تست‌های جدید برای `instant_alert_bridge` و `tg_dedup` بنویس (الگوی `tests/test_tg_api.py`: client تزریقی، صفر شبکه).

### آخر — restart
```bash
rm _ops/STOP-ORGANISM _ops/STOP-TG-CENTER
# بعد RUN-ORGANISM.bat و RUN-LIVE.bat رو دوباره اجرا کن
```

---

## ⚠️ ریسک‌ها و rollback

- هر مرحله **additive + fail-soft** (الگوی codebase). خرابی → flag رو `=0` کن یا STOP بساز.
- قبل از تغییر: `git stash` یا branch بزن. الان روی `claude/octopus-event-bridge-aligned`.
- **هرگز** توکن/`.env` رو لو نده یا commit نکن.
- فایل‌های state که دست می‌زنی (`hypothesis-queue.jsonl`, `tg-sent-hashes.jsonl`) append-only هستن — **overwrite نکن**.
- اگر `cortisol 🔴` alarm واقعاً فوری شد، مطمئن شو با `force=True` ارسال می‌شه نه با cadence عادی.

## 📁 فایل‌هایی که دست می‌خورن

**جدید:**
- `_ops/instant_alert_bridge.py`
- `_ops/tg_dedup.py`
- `_ops/tests/test_instant_alert_bridge.py`
- `_ops/tests/test_tg_dedup.py`

**ویرایش:**
- `_ops/organism.py` (subscriber wiring، بعد از line 327)
- `_ops/budget/approval_channel.py` (`_STREAM_TOPIC` در 118-121 + dedup hook در send_text)
- `_ops/OCTOPUS-flags.cmd` (Harvest + کادنس)

**حذف/پاک‌کردن (آخر):**
- پروسه‌های تکراری
- `_ops/STOP-ORGANISM`, `_ops/STOP-TG-CENTER`

---

## 🔍 نکات کلیدی برای ایجنت بعدی

1. **langar_bot.py و orchestrator.py سالم‌ان** — پراپوز-فقط، خودشون اسپم نمی‌کنن. دست نزن.
2. **منبع اصلی اسپم:** `organism.py` (۶ تابع beat) + `telegram_center/center.py` (۹ تاپیک همزمان).
3. **`event_bus.py` و `unified_bus.py` وجود دارن** ولی هیچ subscriber‌ای به تلگرام وصل نیست. این بزرگ‌ترین فرصته.
4. **`ACTIVATION-C6-RESEARCH.flag` هست** (93 bytes, 2026-07-25). فقط خروجی به تلگرام وصله نیست.
5. **`.env` حاوی توکن/کلید واقعیه** — هرگز در output یا commit قرارش نده.
6. **ساختار group forum:** `chat_id: -1004475788460`, تاپیک‌ها در `center-config.json`.
7. **اولویت کاربر:** (۱) توقف اسپم (۲) صفر تکرار (۳) پتانسیل‌های خفته روشن.

**موفق باشی. از فاز ۰ شروع کن — توقف اسپم، بعد بقیه.**
