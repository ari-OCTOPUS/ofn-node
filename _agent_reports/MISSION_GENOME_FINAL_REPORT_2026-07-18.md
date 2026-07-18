# گزارش نهایی برای ایجنت اصلی — Mission Genome / Genetic Control Loop

تاریخ: 2026-07-18  
محدوده: `_ops/telegram_center`, `_ops/tests`, `run_all.py`  
هدف: تبدیل Telegram از منوی ساده به قشر حرکتی/زبانی اختاپوس: `Intent → Mission → Action Card → Approval → Execution → Report`

---

## 1. خلاصه اجرایی

طبق متن پیوست، مسیر اصلی پیشنهادی «Genetic Control Loop» اجرا شد: یک لایه‌ی **Mission Genome** و یک **Action Graph** اضافه شد تا درخواست‌های ساده‌ی تلگرام به مأموریت‌های قابل‌ردیابی، قابل‌تست، قابل‌approval و قابل‌rollback تبدیل شوند.

نتیجه‌ی فعلی:

- تلگرام فقط منو نیست؛ درخواست‌های آزاد مثل «منوی تلگرامو بهتر کن»، «تستا رو بگیر»، «اگر سبزه اعمال کن»، «جهش بده»، «یاد بگیر…» به Mission تبدیل می‌شوند.
- هر Mission دارای plan، actions، risk، approval state، rollback flag و fitness اولیه است.
- actionها ژنوم حرکتی دارند: risk، requires_approval، handler، audit، rollback، autonomy_level و tests.
- اعمال واقعی patch هنوز انجام نمی‌شود؛ `code.apply` عمداً high-risk و approval-required باقی مانده است.
- Missionهای حساس وارد unified approval queue می‌شوند.
- دکمه‌های تلگرام برای Mission اضافه شده‌اند: بازکردن، درخواست تست، درخواست review، approve/reject.

حکم نهایی: **پیاده‌سازی مرحله‌ی پایه انجام شد و از نظر static/ساختاری قابل قبول است؛ اجرای runtime تست‌ها هنوز لازم است.**

---

## 2. فایل‌های جدید

### 2.1. `_ops/telegram_center/action_graph.py`

رجیستری ژنوم حرکتی برای actionها.

هر action شامل این مشخصات است:

```text
action_id
label
organ
risk
requires_approval
handler
audit
rollback
autonomy_level
tests
notes
```

نمونه actionهای اضافه‌شده:

```text
status.refresh
approval.view
mission.view
leg.pause
leg.resume
map.scan
mission.next
code.plan
code.patch
code.test
code.diff
code.apply
code.rollback
doctor.review
epistemics.review
evolution.propose
evolution.select
```

نکته ایمنی: action ناشناس fail-closed است و به‌صورت high-risk + approval-required برمی‌گردد.

---

### 2.2. `_ops/telegram_center/mission.py`

Mission Genome اصلی.

قابلیت‌ها:

- تشخیص mission type از متن آزاد:
  - `self_coding`
  - `code_apply_request`
  - `verification`
  - `evolution`
  - `preference`
  - `general`
- ساخت Mission با id یکتا.
- ذخیره state در:

```text
_ops/state/telegram/missions/missions.json
_ops/state/telegram/missions/mission-audit.jsonl
```

- چرخه state:

```text
created
planned
patched
tested
reviewed
awaiting_owner
approved
applied
monitored
done
reverted
rejected
```

- fitness اولیه:

```json
{
  "tests_passed": null,
  "doctor_ok": null,
  "epistemic_ok": null,
  "owner_acceptance": null,
  "rollback_available": true,
  "risk": "high",
  "measured_lift": 0.0,
  "score": 0.0
}
```

- توابع اصلی:

```text
infer_mission_type()
create_mission()
actions_for_type()
build_plan()
record_test()
record_review()
set_owner_verdict()
refresh_fitness()
cockpit_summary()
mission_card()
```

---

## 3. فایل‌های تغییرکرده

### 3.1. `_ops/telegram_center/center.py`

تغییرات مهم:

- import شدن Mission Genome:

```python
import mission as mission_mod
```

- command جدید:

```text
/missions
```

- پیام آزاد مالک قبل از مسیر intent قدیمی، از نظر mission-level بررسی می‌شود.

مثال:

```text
اختاپوس، منوی تلگرامو بهتر کن و callbackها رو درست کن
```

به Mission از نوع `self_coding` تبدیل می‌شود.

- اگر Mission نیازمند approval باشد، همزمان وارد unified approval queue می‌شود:

```python
aps_mod.add_pending({
  "id": m.get("id"),
  "type": "mission",
  "title": m.get("owner_intent", "mission"),
  "risk": m.get("risk", "medium"),
  "requires_confirmation": True,
  "source": "telegram"
})
```

- route جدید صفحه:

```text
mn:ms
```

- callbackهای جدید:

```text
ms:open:<id>
ms:test:<id>
ms:review:<id>
ms:approve:<id>
ms:reject:<id>
```

نکته مهم: `ms:test` و `ms:review` فقط request/note ثبت می‌کنند؛ تست یا doctor واقعی را اجرا نمی‌کنند. این برای صداقت UI درست است.

---

### 3.2. `_ops/telegram_center/render.py`

در منوی اصلی دکمه جدید اضافه شد:

```text
🧬 مأموریت‌ها → mn:ms
```

---

### 3.3. `_ops/telegram_center/actions.py`

رجیستری callback موجود با Missionها هماهنگ شد:

```text
missions.show      → mn:ms
mission.open       → ms:open:{id}
mission.test       → ms:test:{id}
mission.review     → ms:review:{id}
mission.approve    → ms:approve:{id}
mission.reject     → ms:reject:{id}
```

---

## 4. تست‌های اضافه/به‌روزرسانی‌شده

### 4.1. فایل جدید: `_ops/tests/test_tg_mission.py`

پوشش:

- قرارداد Action Graph
- fail-closed بودن action ناشناس
- ساخت Mission خودکدنویسی
- ساخت Mission تکاملی
- Mission ترجیح/یادگیری
- lifecycle: test/review/owner verdict/fitness
- fitness مثبت/منفی
- cockpit summary
- mission card
- containment redaction
- تشخیص `اگر تستا سبزه اعمال کن` به‌عنوان `code_apply_request`

### 4.2. فایل‌های به‌روزرسانی‌شده

```text
_ops/tests/test_tg_center.py
_ops/tests/test_tg_render.py
_ops/tests/test_tg_actions.py
_ops/tests/run_all.py
```

موارد مهم پوشش‌داده‌شده:

- پیام آزاد کدنویسی Mission بسازد.
- Mission وارد approval queue شود.
- `ms:approve` state مأموریت و approval queue را sync کند.
- غیرمالک روی `ms:*` سکوت کامل بگیرد.
- منوی اصلی `mn:ms` داشته باشد.
- `run_all.py` تست‌های `test_tg_actions.py` و `test_tg_mission.py` را اجرا کند.

---

## 5. تطبیق با توصیه‌های سند

| توصیه سند | وضعیت | توضیح |
|---|---:|---|
| Mission system پایدار | انجام شد | `mission.py` با state/audit/fitness/card |
| Action Graph / ژنوم حرکتی | انجام شد | `action_graph.py` + به‌روزرسانی `actions.py` |
| کنترل self-coding از تلگرام | پایه انجام شد | متن آزاد → Mission + approval queue؛ apply واقعی هنوز gated/propose-only است |
| Cockpit تلگرامی برای قدم بعدی | پایه انجام شد | `mission_card()` و `cockpit_summary()`؛ صفحه `mn:ms` |
| زبان کنترل ساده | پایه انجام شد | تشخیص کلمات کلیدی: درست کن، بساز، تست، اعمال، یاد بگیر، جهش |
| Doctor/Epistemics قبل از apply | در plan لحاظ شد | actionها در plan هستند؛ runner واقعی هنوز لازم است |
| Fitness واقعی | پایه انجام شد | score ساده؛ اتصال به held_out_evaluator هنوز لازم است |
| Debate before apply | انجام نشده | فاز بعد |
| Reflex layer کامل | جزئی | intent/mission keyword layer هست؛ reflex کامل هنوز لازم است |

---

## 6. ایمنی و گیت‌ها

رعایت‌شده:

- `code.apply` همیشه high-risk و approval-required است.
- هیچ patch واقعی در مسیر Mission اعمال نمی‌شود.
- Mission فقط state/plan/approval/fitness را مدیریت می‌کند.
- callbackهای غیرمالک هیچ اثری ندارند.
- action ناشناس fail-closed است.
- داده‌های دارای containment مثل `onlyfans` redact می‌شوند.
- UI برای تست/review ادعای اجرای واقعی نمی‌کند؛ فقط request ثبت می‌کند.

---

## 7. مواردی که هنوز کامل نشده‌اند

### 7.1. Mission Runner

فعلاً Mission ساخته می‌شود، اما consumer/runner واقعی وجود ندارد. باید ماژولی اضافه شود که Missionهای آماده را بردارد و actionهای زیر را واقعاً اجرا کند:

```text
code.plan
code.patch
code.test
doctor.review
epistemics.review
code.diff
```

سپس نتیجه را با `record_test()` و `record_review()` به Mission برگرداند.

### 7.2. اتصال fitness به evaluator واقعی

fitness فعلی boolean/ساده است. باید به این معیارها وصل شود:

- held_out_evaluator
- تست‌های هدفمند اندام مربوطه
- rollback rate
- latency
- error reduction
- owner acceptance over time

### 7.3. یکی‌سازی `actions.py` و `action_graph.py`

فعلاً دو رجیستری داریم:

- `actions.py`: callback registry قدیمی
- `action_graph.py`: ژنوم حرکتی نو

برای کاهش drift، در فاز بعد باید schema واحد شود.

### 7.4. Debate Before Apply

در plan پیش‌بینی نشده و هنوز اجرا نشده است. باید قبل از apply سه امضا گرفته شود:

```text
Builder / Cortex
Doctor
Epistemics
Owner
```

### 7.5. Reflex Layer کامل

فعلاً keyword-based mission classifier داریم. Reflexهای دقیق‌تر باید اضافه شوند، مثلاً:

```text
"وضعیت" → mn:st
"مکث لید" → lg:lead:p card
"تست بگیر" → verification mission
"کد بزن" → self_coding mission
"اعمال کن" → code_apply_request فقط اگر patch آماده و تست سبز باشد
```

---

## 8. وضعیت تست‌ها

Static review انجام شد و مسیرها از نظر ساختاری درست‌اند. اما اجرای واقعی تست‌ها در این محیط انجام نشد، چون ابزار اجرای shell/test runner در دسترس نبود.

تست‌های ضروری برای اجرای بعدی:

```bash
python -X utf8 _ops/tests/test_tg_mission.py
python -X utf8 _ops/tests/test_tg_actions.py
python -X utf8 _ops/tests/test_tg_render.py
python -X utf8 _ops/tests/test_tg_center.py
python -X utf8 _ops/tests/run_all.py
```

---

## 9. پیشنهاد گام بعدی برای ایجنت اصلی

ترتیب پیشنهادی:

1. اجرای تست‌های بالا.
2. اگر سبز بود، ساخت `_ops/telegram_center/mission_runner.py` یا `_ops/cortex/mission_runner.py`.
3. runner فقط روی Missionهای non-applied و safe/propose-only عمل کند.
4. خروجی runner را به Mission برگرداند:
   - patch id
   - diff summary
   - test result
   - doctor review
   - epistemic review
   - fitness score
5. فقط بعد از approval مالک، مسیر `code_autonomy.apply_approved` فعال شود.
6. سپس Debate-before-apply و Reflex layer اضافه شوند.

---

## 10. جمع‌بندی نهایی برای ایجنت اصلی

جهش پایه با موفقیت پیاده شد: اختاپوس اکنون یک **Mission Genome** و **Action Graph** دارد. تلگرام می‌تواند از یک جمله ساده Mission بسازد، risk و action plan تولید کند، Mission را در approval queue بگذارد و کارت تصمیم نشان دهد. اجرای patch همچنان عمداً بسته و gated است، که با توصیه سند درباره خودکدنویسی کنترل‌شده سازگار است.

این مرحله «نخاع حرکتی و ژنوم پایه» را ساخته؛ مرحله بعد «بستن حلقه اجرا با Mission Runner + fitness واقعی + doctor/epistemics + held-out tests» است.
