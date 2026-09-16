# تحویل به ایجنت ارشد — تکمیل دسترسی تلگرام پس از کارهای موازی

## وضعیت

`DESIGNED_NOT_INTEGRATED`

این دور فقط‌خواندنی معماری موجود را بررسی کرد و فقط namespace مستقل
`_ops/telegram_contract/**` را ساخت. هیچ فایل runtime، state، flag، token، poller،
process، test runner یا فایل ایجنت موازی تغییر نکرد.

## هدف مالک

- دو بات خصوصی به کل اختاپوس دسترسی بدهند.
- گروه Forum فقط پاها و پروژه‌های بیرونی باشد؛ هیچ چیز دیگر.
- مکالمه طبیعی باشد و فرمان‌ها لازم نباشد حفظ شوند.
- قابلیت‌های فعلی و آپدیت‌های بعدی خودکار در دسترس تلگرام قرار گیرند.

## معماری مطلوب

1. Outer DM: رابط اصلی گفت‌وگو، هدف، کشف، مأموریت، گزارش و کارت رأی.
2. Inner DM: سلامت، هشدار، approval و receipt.
3. Outer Forum Group: فقط پاها؛ context از topic.

مرجع ماشین‌خوان:

`TELEGRAM-ACCESS-CONTRACT.v1.json`

## یافته‌های قطعی معماری موجود

### ۱. مقصد target عمدتاً مطابق رأی مالک است

`telegram_center/surface-routing.json` جریان‌های هسته را به دو DM و `legs-all` را به
گروه هدف می‌دهد. اما سند خودش می‌گوید در مقطعی مصرف‌کننده زنده نداشت؛ باید پس از
کار موازی وضعیت فعلی `OCTOPUS_TG_SPLIT_V1` و caller واقعی سنجیده شود.

### ۲. دو لایه routing موازی وجود دارد

- `surface_router`: inner/outer + DM/group
- `surface_policy`: GROUP/DM/HOLD

این‌ها در دو دنیای process کار می‌کنند. باید یک قرارداد precedence و parity test داشته
باشند؛ در غیر این صورت یک stream از center درست route می‌شود و همان stream از organism
مسیر دیگری می‌رود.

### ۳. fallback فعلی برای خواسته مالک بیش از حد permissive است

`surface_router.resolve()` روی stream ناشناخته به outer/current fallback می‌کند و
`_chat_for()` روی surface مبهم center group را امن‌ترین فرض می‌داند. برای قرارداد جدید،
unknown نباید به گروه برسد؛ باید `HOLD_AND_ALERT` باشد.

### ۴. ورودی گروه هنوز واقعاً legs-only نیست

`TelegramApprovalChannel` گروه allowlisted را برای read-only core commands می‌پذیرد و
`telegram_center.Center` نیز commander-grade است. خواسته مالک سخت‌تر است:

- General و topic ناشناخته: deny+redirect به DM
- topic پا: فقط همان پا
- core commands در گروه: redirect/deny
- cross-leg action: clarify/deny

این تغییر باید input policy مستقل داشته باشد، نه فقط output routing.

### ۵. دسترسی کامل آینده هنوز structural نشده

`capability_registry.py` فقط چند پوشه ثابت و `card()` بی‌آرگومان را اسکن می‌کند.
Namespaceهای جدید مانند `world_discovery` و `action_bridge` در `SCAN_DIRS` نیستند و
قابلیت بدون `card()` دیده نمی‌شود. بنابراین آپدیت آینده ممکن است دوباره نامرئی شود.

راه درست: capability manifest نسخه‌دار، بدون import، با status probe و action contract.

### ۶. هر دو بات commander-grade شده‌اند

گزارش قدیمی `GLM-TELBOT-ROLE-AUDIT.md` نیز همین را ثبت کرده. اکنون باید roleها باریک
شوند، نه یک بات سوم ساخته شود:

- Outer = conversation commander + propose/gate
- Inner = organism status/approval
- Group = leg operations only

### ۷. callback parity حیاتی است

تاریخچه پروژه چند کارت مرده به‌علت handler بودن روی بات دیگر داشته (`iv`, `tr`). گیت
نهایی باید برای تمام callbackهای emitted، emitter bot و handler همان poller را ثابت کند.

## ترتیب اجرای بعد از پایان GLM/Action Bridge/Integration

### P0 — تثبیت مرزها

1. کارهای موازی commit/clean شوند.
2. ownership map جدید بگیر.
3. قرارداد این بسته را با رأی مالک canonical کن.
4. هیچ merge/restart/arm بدون رأی تازه.

### P1 — یک Input Surface Policy بساز

فایل مستقل پیشنهادی:

`_ops/telegram_center/input_surface_policy.py`

API پیشنهادی:

```python
def classify(update, *, bot_role, owner_id, group_id, topics) -> dict:
    # {allow, mode, leg, redirect, reason}
```

قواعد:

- outer+DM+owner → core conversation
- inner+DM+owner → status/approval
- outer+group+known leg topic+owner → leg-scoped
- group General/unknown → deny+redirect
- group core command → deny+redirect
- cross-leg → clarify/deny
- non-owner mutation → deny

### P2 — unknown output را fail-closed کن

- unknown stream → HOLD+ALERT
- surface مبهم → گروه fallback نشود
- leg بدون topic → HOLD+ALERT، نه General
- inner unavailable برای core safety → alert + explicit degraded receipt؛ fallback به outer DM فقط
  اگر قرارداد مالک اجازه دهد، هرگز group

### P3 — capability manifest registry

یک schema مستقل بساز و از packageها بخواه manifest منتشر کنند. برای شروع:

- core/self-goal
- world_discovery
- action_bridge
- integration boundary
- doctor
- memory/recall
- telegram diagnostics
- پاها

Registry فقط metadata را بخواند؛ import نکند. Outer DM یک catalog واحد نشان دهد.

### P4 — مکالمه طبیعی

- Outer DM پیام آزاد را ابتدا به read-only answer یا mission proposal تبدیل کند.
- برای action، Action Bridge classifier مستقل تصمیم بگیرد؛ LLM اجازه را تعیین نکند.
- unknown clarify شود.
- Inner DM free chat را redirect کند.
- گروه فقط از topic context استفاده کند.

### P5 — اتصال World Discovery و Action Bridge

پس از handoff integration جاری:

- `NO_VALID_DISCOVERY` را حفظ کن.
- World Discovery E0/E1/E2/E3/E4 را به A0/A1/A3/A4/A5 ترجمه کن.
- Telegram فقط draft/owner card بگیرد.
- ارسال واقعی هر بار رأی تازه بخواهد.
- World Discovery chat/report فقط Outer DM؛ نه گروه.

### P6 — تست نهایی

`ACCEPTANCE-RUNBOOK.md` را کامل اجرا کن:

- fake clients
- adversarial/mutation
- callback emitter parity
- one-poller-per-token
- input/output matrix
- capability update discovery
- سپس live canary با تپ مالک

## تست‌های جدید لازم

پیشنهاد نام‌ها:

```text
_ops/tests/test_tg_input_surface_policy.py
_ops/tests/test_tg_two_bot_contract.py
_ops/tests/test_tg_group_legs_only.py
_ops/tests/test_tg_callback_emitter_parity.py
_ops/tests/test_tg_capability_manifest_registry.py
_ops/tests/test_tg_future_capability_discovery.py
_ops/tests/test_tg_owner_conversation_e2e.py
```

به `run_all.py` تا پایان کار موازی دست نزن؛ سپس با ownership تمیز ثبت کن.

Mutationهای اجباری:

- unknown stream → group
- General → core
- core command in group → allow
- cross-leg → execute
- inner free chat → mission
- missing callback handler → emit
- unregistered capability → LIVE
- capability manifest → execution authorization

هر جهش باید قرمز شود؛ `__pycache__` پاک و restore از git معتبر باشد.

## رأی‌های مالک که فقط برای LIVE لازم‌اند

1. قرارداد سه سطح بالا canonical شود؟ پیشنهاد: بله.
2. safety alert در خرابی inner به Outer DM fallback کند یا فقط held+local alert؟
   پیشنهاد: fallback فقط Outer DM، هرگز group.
3. گروه برای اعضای غیرمالک هیچ read-only هم داشته باشد؟ پیشنهاد: خیر؛ owner-only کامل.
4. capability catalog جدید در Outer DM با فرمان `/capabilities` و متن طبیعی فعال شود؟
   پیشنهاد: بله.
5. World Discovery card در Outer DM ارسال شود؟ طبق رأی فعلی، فقط با رأی تازه در هر بار.

## Done

فقط پس از اجرای runbook:

- `TELEGRAM_ACCESS_LIVE`
- Outer DM همه قابلیت‌ها را می‌بیند.
- Inner DM سلامت/approval را دارد.
- گروه فقط پاهاست.
- قابلیت تازه با manifest بدون ویرایش منوی مرکزی دیده می‌شود.
- هیچ callback یتیم و هیچ poller اضافه وجود ندارد.

## rollback

این بسته مستقل است و هیچ caller ندارد. حذف `_ops/telegram_contract/` صفر اثر runtime دارد.
