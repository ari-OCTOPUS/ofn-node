# NEXT-TO-ALIVE — RUNBOOK اجرایی روی بدن ۱۳۸
scope: تبدیل «کاغذ» به «اثر خارجی ثبت‌شده» با یک کانال، یک شلیک، یک ردیف لجر
status: READY_FOR_EXECUTING_AGENT (این سند خودش هیچ اثر خارجی ندارد)

---

## 0) واقعیت مرزها (قبل از هر کلید)

- این سند از یک نشست بدون دسترسی SSH/F: نوشته شده. اجرای آن فقط بر عهدهٔ ایجنت میزبان روی ۱۳۸ است.
- یافتهٔ کلیدی نشست قبل: در `season5-gates-final.json` روی ۱۳۸ کلیدی به نام `HOLD_EXTERNAL` وجود ندارد؛ کلید واقعی `m5_owner_release = ACTIVE_REAL_SEND_AUTHORIZED` است.
- نتیجهٔ منطقی: قدم ۱ پلن («فایل فصل ۵ را عوض کن تا HOLD برداشته شود») روی بدن اصلی **موضوعیت ندارد**. مانع، فایل فصل ۵ نیست.
- مانع واقعی دو چیز است:
  1. سیاست ایجنت: `AGENTS.md` هرگونه wire / auto_email / پیام خروجی را ممنوع کرده است.
  2. تعارض provenance: نوت `01-TRUTH/SEASON-5-2026-09-04.md` هنوز HOLD_EXTERNAL را «بسته» می‌نویسد؛ این اختلاف `status: open` است.

---

## PHASE A — پیش‌پرواز فقط‌خواندنی روی ۱۳۸ (بدون هیچ نوشتنی)

A1. hash و متن کامل `season5-gates-final.json` را pin کن؛ همهٔ کلیدهای release/gate را فهرست کن.
A2. فهرست تایمرها و unitهای فعال را بگیر (سیستمی + داخلی اپ). هدف: پاسخ به یک سؤال بله/خیر —
    «آیا هیچ تایمر/کرون/queue-consumer وجود دارد که با تغییر یک flag به‌طور خودکار پیام بفرستد؟»
A3. مسیر ارسال تلگرام را در کد ردیابی کن: نقطهٔ ورودی → policy gate → HTTP client. مشخص کن ارسال فقط با فراخوان دستی رخ می‌دهد یا با loop.
A4. schema دقیق لجر ۱۳۸ را بخوان (فیلدهای اجباری یک ردیف اثر خارجی) و آخرین ردیف موجود را pin کن.
A5. مرجع rollback: کپی pre-image هر فایلی که قرار است لمس شود + دستور برگشت یک‌خطی.

خروجی PHASE A: `PREFLIGHT-138.json` با پنج بند بالا و یک verdict:
`AUTOSENDER_ARMED = true | false | UNKNOWN`

توقف سخت: اگر `AUTOSENDER_ARMED != false` هیچ flagای تغییر نمی‌کند. علت را بنویس و به PHASE D برو.

---

## PHASE B — رفع تعارض کاغذی (بی‌خطر، همیشه مجاز)

B1. در vault یک نوت lane تازه بساز که واقعیت ۱۳۸ (`m5_owner_release=ACTIVE_REAL_SEND_AUTHORIZED`) را در برابر نوشتهٔ فصل ۵ بگذارد.
B2. فایل `01-TRUTH/SEASON-5-2026-09-04.md` را overwrite نکن؛ فقط ردیف تعارض را با اشاره به hash هر دو منبع ثبت کن.
B3. validatorها را تا exit code کامل اجرا کن و دو ادعا را جدا گزارش کن: «۵ فایل lane تازه» در برابر «کل vault».

---

## PHASE C — تک‌شلیک (فقط با GO دامنه‌دار مالک)

این فاز بدون توکن GO زیر اجرا نمی‌شود. یک کلید، یک کانال، یک پیام.

```
GO-TOKEN (باید مالک پر کند)
channel:        telegram
recipient:      <chat_id دقیق>
surface:        <یکی از /heart /brain /doctor /budget یا card:<id>>
payload_sha256: <هش متن نهایی، قبل از ارسال محاسبه و pin شود>
expiry:         <UTC، حداکثر ۳۰ دقیقه>
abort_rule:     هر خطای HTTP یا هر ارسال دوم = abort فوری + rollback
scope:          فقط همین یک کلید — نه کل OCTOPUS-flags.cmd
```

C1. متن کارت را بساز، hash کن، در `SEND-INTENT.json` ثبت کن.
C2. ارسال را از خودِ ۱۳۸ انجام بده (تنها گرهٔ مجاز برای گفت‌وگو با مالک، یک تصمیم در هر پیام).
C3. بلافاصله یک ردیف در لجر ۱۳۸ بنویس: زمان، کانال، recipient، payload_sha256، پاسخ API، exit.
C4. ردیف را بازخوانی کن و hash نهایی لجر را pin کن. `/healthz` مدرک زنده‌بودن نیست؛ همان ردیف مدرک است.

---

## PHASE D — بستن (هر مسیری که طی شد)

D1. `CLOSEOUT-RECEIPT.json`: چه چیزی واقعاً رخ داد، چه چیزی نشد و دقیقاً چرا.
D2. manifest + hash-chain دوباره روی همهٔ فایل‌های بسته.
D3. وضعیت پایانی را یکی از این سه بنویس، بدون واژهٔ زیباتر:
    `ALIVE_ONE_CHANNEL_PROVEN` · `BLOCKED_AUTOSENDER_RISK` · `BLOCKED_NO_OWNER_GO`

---

## آنچه برای زنده‌شدن لازم **نیست**

SSH دوبارهٔ ۱۸۰ · تونل ۱۳۸→۱۸۰ · B-full روی لپ‌تاپ · SIG-IV · چسباندن ریاضیات N3V2 · promotion هشت مورد INCONCLUSIVE.
