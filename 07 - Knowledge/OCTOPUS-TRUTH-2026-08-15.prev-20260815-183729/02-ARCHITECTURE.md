---
title: معماری رصدخانه
type: note
tags: [octopus, observatory, architecture, invariants]
up: "[[00-INDEX]]"
---

# معماری

## اصل بنیادی: تک‌درگاه خروج

**فقط یک فایل در کل مخزن اجازه دارد شبکه import کند:** `_ops/observatory/impl/gateway.py`

این یک آرزو نیست — یک تست ساختاری آن را اعمال می‌کند. `test_structural.py`
درخت AST همهٔ فایل‌های رصدخانه را می‌خواند و اگر جایی `socket`، `http`،
`urllib`، `requests` یا مانند آن import شده باشد، تست می‌شکند.

## فایل‌ها

| فایل | حجم | نقش |
|---|---|---|
| `impl/gateway.py` | ۱۹٬۴۴۹ B | تنها فایل شبکه‌ای. ۱۰ دروازه. transport تزریق‌پذیر برای تست |
| `impl/robots.py` | ۸٬۶۳۶ B | ارزیاب RFC 9309. **بدون** import شبکه |
| `impl/audit.py` | ۲٬۲۲۹ B | زنجیرهٔ hash |
| `impl/evidence_store.py` | ۱۴٬۴۴۴ B | انبار شاهد + بودجهٔ پایدار + rate limiter |
| `scripts/compile_policy.py` | — | YAML → JSON. **بیرون** از runtime، اجازه دارد PyYAML بخواهد |
| `scripts/verify_live_store.py` | ۱۹٬۱۴۵ B | راستی‌آزمای فقط‌خواندنی انبار زنده |

> [!note] runtime فقط stdlib است.
> هیچ وابستگی بیرونی در مسیر اجرا نیست. PyYAML فقط در ابزار کمکی مجاز است،
> چون خارج از runtime اجرا می‌شود.

## ۱۰ دروازهٔ gateway

هر درخواست باید از هر ده گیت رد شود. رد شدن در هر یک = مسدود، **نه** retry.

1. **گیت متد** — فقط `GET` و `HEAD`
2. **گیت scheme** — فقط `https`
3. **گیت allowlist** — تطبیق **دقیق** دامنه، نه پسوندی
4. **گیت مسیر** — مسیر باید در فهرست مجاز دامنه باشد
5. **گیت robots** — ارزیابی RFC 9309
6. **گیت kill-switch** — وجود فایل `kill.switch` همه چیز را می‌بندد
7. **گیت بودجهٔ دامنه** — سقف تعداد درخواست per-domain، پایدار روی دیسک
8. **گیت rate limit** — پنجرهٔ لغزان per-domain
9. **گیت سقف حجم** — بدنهٔ بزرگ‌تر از سقف رد می‌شود
10. **گیت مرز راز** — هیچ هدر هویتی (`Cookie`، `Authorization`) ارسال یا ذخیره نمی‌شود

## invariant ها

| کد | متن | اعمال‌کننده |
|---|---|---|
| S1 | فقط `gateway.py` شبکه import می‌کند | `test_structural.py` |
| S2 | runtime فقط stdlib | `test_structural.py` |
| E1 | زنجیرهٔ شاهد genesis-anchored است | `verify_live_store.py` |
| E2 | `body_hash == sha256(body_bytes)` | `verify_live_store.py` |
| E3 | `prev_hash[n] == hash[n-1]` | `verify_live_store.py` |
| E4 | replay تعیّنی است | `test_evidence_store.py` |
| B1 | `spent_requests <= max_requests` | gateway + راستی‌آزما |
| P1 | پیش‌بینی پیش از رویداد قفل می‌شود | `predictions.db` زنجیره |
| P2 | سه baseline همیشه همراه پیش‌بینی ثبت می‌شوند | راستی‌آزما |
| K1 | kill-switch بی‌قید‌و‌شرط مسدود می‌کند | `test_gateway.py` |

> [!danger] نقض invariant یعنی **halt**.
> هیچ کجای این سیستم retry نمی‌کند. retry یعنی پنهان‌کردن نقض.

## معناشناسی RFC 9309 — نکتهٔ ظریفی که اول غلط بود

طبق [RFC 9309 §2.3.1](https://www.rfc-editor.org/rfc/rfc9309.html):

| پاسخ `robots.txt` | معنا | اجازه |
|---|---|---|
| ۲۰۰ | قواعد معتبر | طبق قواعد |
| **4xx** | «unavailable» | crawler **MAY** access all |
| **5xx** | «unreachable» | crawler **MUST** assume complete disallow |

نسخهٔ اول ما همهٔ غیر ۲۰۰/۴۰۴ را «نامعلوم» می‌گرفت. غلط بود. تصحیحش دو اثر
واقعی داشت — به [[03-ALLOWLIST]] برو.
