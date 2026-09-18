# P1 RECEIPT — رگِ مغز وصل شد (PERFUSION P1)

اجرا: ۲۰۲۶-09-18T01:36Z · GO مالک («GO» روی ASK-REGISTER با پیشنهادهای خودم).

## چه چیزی عوض شد

| قبل | بعد |
|---|---|
| `BRAIN_PROVIDER=fugu` → مستقیم به sakana-fugu (اعتبار تمام، `429 usage_limit_reached`) | pin محترم می‌ماند تا وقتی روتیبل است؛ اگر نبود، رجیستری تصمیم می‌گیرد |

مقدار **زندهٔ** بعد از پچ (اندازه‌گیری‌شده روی ۱۳۸):

```
resolved_provider=deepseek  reason=PIN_BLOCKED(sakana-fugu=EXHAUSTED)_FALLBACK->BRAINPORT_OK
```

ترتیب رجیستری (برای مصرف‌کننده‌های آینده): `local-llamacpp-180 → gemini →
anthropic → openai → deepseek` · حذف‌شده: `sakana-fugu`.

## فایل‌ها و شاهدها

- **جدید:** `/home/ari/ofn/tools/think_pool.py` · `/home/ari/ofn/tools/provider_routing.py`
  (sha دوطرفه: `320e77cf…` · `fc55a83e…` — لوکال == ریموت)
- **پچ‌شده:** `/home/ari/ofn/ofn/helpers/brainport.py`
  - preimage: `brainport.py.pre-perfusion-p1-20260918T013620Z`
  - sha قبل `9b37e3c5e65ece07` → بعد `0b537bb26ba58044`
  - `py_compile`: OK · خط اصلی pin دست‌نخورده به‌عنوان fallback باقی است
- **لجر مسیریابی (جدید):** `state/api-budget/config/brain-routing.jsonl` —
  هر تصمیم با `at_utc/pin/pin_state/chosen/reason` ثبت می‌شود
- **تست:** `tests/test_provider_routing.py` + `tests/test_think_pool.py` — **۲۹/۲۹ سبز**

## طراحی fail-safe (قانون «آسیب نبینه»)

سه شرط، پچ را بی‌خطر می‌کند: اگر ماژول مسیریاب نبود، اگر خطا داد، یا اگر token
برنگرداند → همان `BRAIN_PROVIDER` قبلی استفاده می‌شود. یعنی **بدترین حالت این
پچ = رفتار قبلی**. هیچ flag محیطی جدیدی هم اضافه نشد و TCB دست نخورد.

## rollback

```bash
cp /home/ari/ofn/ofn/helpers/brainport.py.pre-perfusion-p1-20260918T013620Z \
   /home/ari/ofn/ofn/helpers/brainport.py
python3 -m py_compile /home/ari/ofn/ofn/helpers/brainport.py
rm /home/ari/ofn/tools/provider_routing.py /home/ari/ofn/tools/think_pool.py   # اختیاری
```

## هنوز باز (فاز ۲/۳ بقیهٔ ASK-REGISTER)

- **P2 (wiring):** تایمر برای `cognition` (۰ نوشتن/۲۴h، ۶۵h کهنه) و `durability`.
- **P3 (budget):** اجباری‌کردن نام پروایدر در لجر + سقف per-provider.
- **P4 (compute):** مصرف‌کنندهٔ واقعی برای بردهای خالی.
- `remote_brain.py` (مصرف‌کنندهٔ اصلی، ۶ فایل) هنوز به مسیریاب وصل نیست — این
  گام بعدیِ همان رگ است؛ عمداً جدا نگه داشته شد تا هر تغییر یک اندام باشد.
