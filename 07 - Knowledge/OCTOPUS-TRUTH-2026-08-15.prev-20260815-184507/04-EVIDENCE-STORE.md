---
title: انبار شاهد — دو پیاده‌سازی و تصمیم یکسان‌سازی
type: note
tags: [octopus, observatory, evidence-store, adr]
up: "[[00-INDEX]]"
---

# انبار شاهد

## کشف: دو انبار موازی وجود داشت

در نشست ۱۵ اوت فهمیدیم انبار شاهد **دو بار** ساخته شده. این دقیقاً همان الگویی
است که قبلاً سه نسخهٔ موازی NBB-CP را ساخت.

| | انبار runner | انبار جدید |
|---|---|---|
| نوع | SQLite — `evidence.db` | فایل‌محور — `.dat` + `.meta` + `audit_chain.jsonl` |
| وضعیت | **زنده، دادهٔ واقعی USGS** | تست‌شده، صفر دادهٔ واقعی |
| تست | نامعلوم بود | ۲۵ تست |

## ساختار واقعی دیتابیس زنده

بازرسی مستقیم روی لپ‌تاپ مالک انجام شد. **این ارقام از اجرای واقعی آمده‌اند.**

### `evidence.db` — ۲۳۷٬۵۶۸ بایت

```
evidence_chain(seq, evidence_id, url, method, occurred_at, recorded_at,
               status_code, response_headers, body_hash, body_size,
               body_bytes BLOB, prev_hash, hash)          -> ۱ ردیف
domain_budget(domain, max_requests, spent_requests, epoch) -> ۲ ردیف
store_meta(key, value)                                     -> ۰ ردیف  <- خالی
```

### `predictions.db` — ۲۴٬۵۷۶ بایت

```
prediction_events(seq, event_type, prediction_id, payload, prev_hash, hash) -> ۱ ردیف
```

## حکم: improve, don't rewrite

انبار SQLite **بهتر از حد انتظار** بود:

- خودش hash-chain دارد (`prev_hash` + `hash`)
- بایت خام پاسخ را به‌صورت BLOB نگه می‌دارد، نه فقط hash
- genesis-anchored است — `prev_hash` ردیف صفر = ۶۴ صفر

پس:

1. **SQLite انبار عملیاتی می‌ماند.** یک لحظه هم متوقف نمی‌شود.
2. انبار فایل‌محور می‌شود **پیادهٔ مرجع** + مجموعهٔ تستی که SQLite باید از آن عبور کند.
3. پل بین دو: `scripts/verify_live_store.py`

## راستی‌آزمای مستقل

`verify_live_store.py` — stdlib خالص، هر دیتابیس را با `mode=ro` باز می‌کند.
**نوشتن ساختاراً ناممکن است.**

۱۳ ضمانت را می‌سنجد: وجود فایل، باز شدن read-only، اسکیما،
`body_hash == sha256(body_bytes)`، `body_size`، لنگر genesis، یکنوایی `seq`،
پیوند `prev_hash`، بازتولیدپذیری فرمول hash، یکتایی `evidence_id`، تعیّن خواندن،
تشخیص دست‌کاری، نبود هدر هویت، سقف بودجه، تطبیق میزبان با allowlist، و
پرشدگی `store_meta`.

### نکتهٔ طراحی مهم — چرا این تست معنی دارد

**فرمول hash انبار زنده را نمی‌دانیم.** پس حدس نزدیم. راستی‌آزما ۱۵ فرمول
کاندید را روی **همهٔ** ردیف‌ها امتحان می‌کند و می‌گوید کدام یکی hash ذخیره‌شده
را بازتولید می‌کند.

اگر هیچ‌کدام نکرد، خود این یک یافتهٔ **CRITICAL** است:
«زنجیره مستقل قابل تأیید نیست.»

> [!important] این تفاوت بین «تستی که پاس می‌شود» و «تستی که چیزی ثابت می‌کند» است.
> یک راستی‌آزما که فرمول را از خودِ کد تولیدکننده وام بگیرد، هیچ چیز اثبات
> نمی‌کند — فقط با خودش موافق است.

## اجرا

```powershell
python verify_live_store.py
python verify_live_store.py --data-dir _ops/observatory/data
```

خروجی: جدول `PASS` / `FAIL` / `CRITICAL` / `SKIP` و یک حکم نهایی.
کد خروج ۰ فقط وقتی همه چیز PASS باشد.
