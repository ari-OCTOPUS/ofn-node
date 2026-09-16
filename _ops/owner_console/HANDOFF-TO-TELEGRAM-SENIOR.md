# Handoff — اتصال Owner Console به Outer DM

## چرا این بسته لازم شد

قابلیت‌ها ساخته شده‌اند، ولی هرکدام گزارش/manifest/handler جدا دارند و انسان یک سطح واحد ندارد.
Owner Console آن‌ها را در یک خانه جمع می‌کند و فقط حقیقت CODE/WIRED/LIVE را نشان می‌دهد.

## مرز مالکیت

این جلسه فقط `_ops/owner_console/**` را تغییر داد. به فایل‌های تلگرام و کار تو دست نزد.

## قبل از اتصال

1. کار فعلی تلگرام را commit تمیز کن.
2. تست‌های Owner Console را اجرا کن:

```text
python -X utf8 _ops/owner_console/tests/test_catalog.py
python -X utf8 _ops/owner_console/tests/test_conversation.py
python -X utf8 _ops/owner_console/tests/test_acceptance_questions.py
python -X utf8 _ops/owner_console/tests/test_telegram_adapter.py
```

3. مشکلات manifest موجود را ببین: چند manifest قدیمی `action_contract` و `owner_gate` را
   با نوع ناسازگار نوشته‌اند. Console آن‌ها را `MANIFEST_INVALID` نشان می‌دهد. برای اتصال
   اولیه لازم نیست پنهان/حذف شوند؛ بعداً owner package باید manifest خودش را اصلاح کند.

## seam اتصال

در `center.handle_update`، فقط بعد از تصمیم مجاز `input_surface_policy` و قبل از fallback قدیمی:

```python
from owner_console import telegram_adapter as _oc
oc = _oc.handle_message(text, surface_decision=surface_decision)
if oc["handled"]:
    reply = oc["reply"]
    # با send helper موجود outer bot ارسال کن؛ reply['text'] + reply['keyboard']
    # receipt موجود مرکز باید attempted/sent/held را ثبت کند.
    return
```

برای callbackهایی که با `oc:` شروع می‌شوند:

```python
oc = _oc.handle_callback(data, surface_decision=surface_decision)
```

- emitter: outer bot
- handler: center poller همان outer bot
- callback ≤64 bytes
- unknown callback → block

## mutationهای لازم

- حذف شرط `mode == core_conversation` ⇒ تست گروه باید قرمز شود.
- unknown callback → handled ⇒ قرمز.
- `send_attempted=True` داخل Console ⇒ قرمز.
- `NOT_LIVE` → LIVE parser ⇒ قرمز.
- manifest invalid → LIVE ⇒ قرمز.
- registration_is_authorization=True پذیرفته شود ⇒ قرمز.
- capability آینده با manifest دیده نشود ⇒ قرمز.

## runbook انسانی

پس از restart، ۱۲ سؤال `telegram_contract/ACCEPTANCE-RUNBOOK.md` را در Outer DM بپرس.
مالک باید نتیجه قابل لمس ببیند، نه فقط PASS تست.

## وضعیت‌های صحیح

- الآن: `IMPLEMENTED_NOT_WIRED`
- پس از handler ولی قبل restart: `WIRED_NOT_LOADED`
- پس از restart + ۱۲ سؤال + receipt: `OWNER_CONSOLE_LIVE`

هیچ‌کدام مجوز action حساس نیستند.
