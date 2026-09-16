# GLM Handoff — Octopus Telegram Live Buttons

تاریخ: 2026-07-18
نقش سند: نقشهٔ مهندسی برای ایجنت بعدی GLM
محدوده: `F:\backup\_ops\telegram_center`

## خلاصهٔ وضعیت

در این دور، مرکز تلگرام از حالت «منوی ثابت/توضیحی» به سمت «منوی زنده/عملگرا» حرکت داده شد.
فایل‌های ویرایش‌شده:

- `render.py`
- `center.py`
- `tests/test_tg_render.py`
- `tests/test_tg_center.py`

هیچ فایل کاربر خارج از `_ops/telegram_center` و تست‌های مرتبط دستکاری نشد.

---

## تغییرات انجام‌شده

### 1. منوی context-aware در `render.py`

تابع زیر از حالت ثابت خارج شد:

```python
render_menu(power=False)
```

و به این شکل توسعه یافت:

```python
render_menu(power=False, feeds=None, paused=None)
```

اکنون منو بر اساس وضعیت زنده اولویت می‌دهد:

1. اگر `quarantined > 0` باشد، دکمهٔ اول:
   - `☣️ {n} قرنطینه — رسیدگی`
   - callback: `mn:qr`
2. اگر `guidance.n > 0` باشد:
   - `🧭 {n} تصمیم منتظر تو`
   - callback: `mn:ap`
3. اگر `awaiting_user > 0` باشد:
   - `🙋 {n} منتظر پاسخ تو`
   - callback: `mn:ap`
4. اگر پایی paused باشد:
   - `▶️ {n} پای متوقف — ادامه؟`
   - callback: `mn:lg`
5. دکمه‌های همیشگی پایین می‌مانند:
   - `mn:st`, `mn:lg`, `mn:bg`, `mn:rv`, `mn:sy`

ناوردی حفظ شد: render خالص است، هیچ I/O ندارد، فقط feeds/paused تزریق‌شده را می‌خواند.

---

### 2. صفحه‌ها در `center.py` زنده‌تر شدند

تابع `_page(name)` اکنون هنگام ساخت صفحه‌ها، `feeds = r.collect_feeds()` را می‌گیرد و به صفحه‌ها تزریق می‌کند.

صفحهٔ `st` اکنون کیبورد عملگرا دارد:

- `🔄 تازه‌سازی` → `mn:st`
- اگر تصمیم معلق باشد: `🧭 {n} تصمیم‌ها` → `mn:ap`
- `🔙 منو`

صفحهٔ جدید اضافه شد:

```python
mn:qr
```

که به `_quarantine_text(feeds)` وصل است. این صفحه فعلاً content-free است:

- فقط شمارش قرنطینه را نشان می‌دهد.
- محتوا/هویت را echo نمی‌کند.
- هنوز per-item action ندارد. این کار برای GLM مانده است.

---

### 3. پرسش‌وپاسخ نرم بدون LLM در `center.py`

در `_handle_message` اگر پیام مالک command نباشد و با `/` شروع نشود، به مسیر جدید می‌رود:

```python
_handle_ask(msg, text)
```

intentهای فعلی:

- وضعیت / چطوری / الان / حالت / status → صفحهٔ وضعیت `st`
- درآمد / پول / مالی / revenue → کارت درآمد
- بودجه / budget → صفحهٔ بودجه `bg`
- کمک / راهنما / منو / help → منوی زنده
- مکث / متوقف / نگه دار / pause / stop → کارت مکث پا
- ادامه / resume / شروع → کارت ادامه پا
- ناشناخته → کارت پیشنهاد با چند دکمهٔ حدسی

نکتهٔ ایمنی:

- متن آزاد هیچ اکشن حساس یا مخربی را مستقیم اجرا نمی‌کند.
- برای مکث/ادامه فقط دکمهٔ `lg:<leg>:p|r` ساخته می‌شود؛ اجرا بعد از کلیک مالک انجام می‌شود.
- اکشن‌های حساس همچنان در `pw/pwc` و `power.py` هستند.

---

### 4. تشخیص سادهٔ پا از متن

تابع جدید:

```python
_leg_from_text(text)
```

فعلاً این پاها را با aliasهای ساده تشخیص می‌دهد:

- `lead`
- `ziman`
- `mining`
- `crypto`
- `accounting`
- `studio_pf`
- `knowledge`
- `cartographer`

اگر چند پا match شوند یا هیچ‌کدام match نشود، `None` برمی‌گرداند و کارت انتخاب پا ساخته می‌شود.

---

### 5. تست‌های اضافه‌شده

در `test_tg_render.py`:

```python
t_m_menu_is_context_aware_and_action_first
```

چک می‌کند:

- منو priority-aware است.
- قرنطینه دکمهٔ اول می‌شود.
- تصمیم‌ها و پای paused در منو دیده می‌شوند.
- دکمه‌های همیشگی هنوز وجود دارند.

در `test_tg_center.py`:

```python
t_m_free_text_status_routes_to_live_page_with_keyboard
t_n_free_text_pause_builds_action_button_not_direct_execute
```

چک می‌کنند:

- پیام آزاد «وضعیت الان چطوره؟» به کارت وضعیت با کیبورد زنده تبدیل می‌شود.
- پیام «لید رو مکث کن» فقط دکمهٔ `lg:lead:p` می‌سازد و مستقیم فایل pause نمی‌نویسد.

---

## کارهای باقی‌مانده برای GLM

### P0 — تست‌ها را اجرا و تثبیت کن

من ابزار اجرای shell نداشتم، پس تست‌ها اجرا نشده‌اند. اول این‌ها را اجرا کن:

```powershell
cd F:\backup
python _ops\tests\test_tg_render.py
python _ops\tests\test_tg_center.py
python _ops\tests\test_tg_power.py
```

اگر harness پروژه با pytest سازگار است:

```powershell
python -m pytest _ops\tests\test_tg_render.py _ops\tests\test_tg_center.py _ops\tests\test_tg_power.py
```

احتمال‌های خطا:

1. fake_render در تست‌ها هنوز signature قدیمی داشته باشد.
2. `render_menu` در جایی با positionalهای قدیمی صدا زده شده باشد.
3. test_tg_center انتظار منوی ثابت داشته باشد.

رفع پیشنهادی:

- backward compatibility را حفظ کن؛ `render_menu(power=False, feeds=None, paused=None)` باید با call قدیمی هم کار کند.
- center `_page` همین را با try/except TypeError پوشش داده است.

---

### P1 — صفحهٔ قرنطینه را واقعی‌تر کن

اکنون `_quarantine_text` فقط شمارش را نشان می‌دهد. GLM باید ببیند execution_board یا state مربوطه itemهای قرنطینه را کجا نگه می‌دارد.

هدف:

- حداکثر ۵ مورد آخر را content-free نشان بده:
  - id
  - نوع
  - سن
  - risk
- دکمه‌ها:
  - `qr:<id>:inspect` فقط گزارش metadata بدهد، نه محتوا
  - `qr:<id>:release` فقط اگر policy اجازه داد و دوکلیک شد
  - `qr:<id>:keep` نگه‌داشتن در قرنطینه

اما تا وقتی منبع itemها روشن نیست، فقط شمارش بماند.

---

### P2 — intent router را تمیزتر کن

الان `_handle_ask` کلیدواژه‌ای است و داخل center.py آمده. پیشنهاد senior-level:

یک فایل جدید بساز:

```text
_ops/telegram_center/intent.py
```

با تابع خالص:

```python
def classify(text: str) -> dict:
    return {"intent": "status|budget|revenue|pause|resume|help|unknown", "leg": "lead|...|None", "confidence": 0.0}
```

مزیت:

- تست‌پذیرتر
- قابل ارتقا به LLM/GLM پشت فلگ
- center.py سبک‌تر می‌شود

ناوردی:

- import-time خالص
- stdlib-only
- هیچ اجرای مستقیم

---

### P3 — قلاب LLM/GLM فقط پشت فلگ

اگر خواستی GLM را برای پرسش‌وپاسخ وصل کنی، مستقیم اجرا نکن. اول:

```text
OCTOPUS_TG_LLM_ASK=0
```

پیش‌فرض خاموش. وقتی روشن شد:

- LLM فقط intent پیشنهاد کند، نه اکشن اجرا کند.
- خروجی LLM باید JSON محدود باشد:

```json
{"intent":"status","leg":null,"confidence":0.82,"reply":"..."}
```

- اگر JSON نامعتبر بود → fallback به کلیدواژه.
- اگر intent حساس بود → فقط کارت تأیید بساز، نه اجرا.

---

### P4 — action graph بساز

برای اینکه دکمه‌ها واقعاً «مغزدار» شوند، یک جدول action تعریف کن:

```python
ACTIONS = {
  "status.refresh": {"callback": "mn:st", "risk": "read", "direct": True},
  "leg.pause": {"callback": "lg:{leg}:p", "risk": "low", "direct": True},
  "budget.apply": {"callback": "pw:ba", "risk": "high", "double_confirm": True},
  "system.panic": {"callback": "pw:pn", "risk": "emergency", "double_confirm": True},
}
```

بعد render_menu و ask router از همین graph استفاده کنند، نه callbackهای hardcoded.

---

### P5 — stale UI را کم کن

اکنون status pinned فقط در beat و `/now` تازه می‌شود. برای حس «زنده»:

- بعد از هر callback موفق، `_edit_page` همان صفحه را رفرش کند.
- برای `lg:*` این کار انجام شده.
- برای `ok/no/later` decision callback هم می‌توان کارت را به «ثبت شد» edit کرد، نه فقط answer_callback.

---

## نواحی حساس که نباید خراب شوند

1. `tg_api.py` نباید token را log کند.
2. `_BANNED_ECHO` در render/tg_api باید حفظ شود.
3. `power.py` گیت‌های safety دارد؛ مستقیم bypass نشود.
4. `center._is_owner` باید fail-closed بماند.
5. `render.py` نباید هیچ write/network داشته باشد.
6. پیام آزاد نباید delete/move/modify فایل کاربر را اجرا کند.

---

## تعریف Done برای GLM

کار GLM وقتی تمام است که:

- سه تست tg_render/tg_center/tg_power سبز باشند.
- `/menu` در تلگرام دکمهٔ اول را بر اساس وضعیت واقعی عوض کند.
- پیام آزاد مثل «وضعیت چیه؟»، «لید رو مکث کن»، «درآمد چقدره؟» جواب دکمه‌دار بدهد.
- هیچ عملیات مخرب از متن آزاد اجرا نشود.
- گزارش نهایی فارسی شامل diff، تست‌ها، و مسیر فایل‌های تغییرکرده باشد.

---

## جملهٔ مأموریت برای GLM

«اختاپوس نباید منو نشان بدهد؛ باید در هر لحظه بهترین دکمهٔ بعدی را بر اساس وضعیت زندهٔ مغزها پیشنهاد کند، و هر دستور مبهمِ ادمین را به کارتِ امنِ قابل‌کلیک تبدیل کند.»
