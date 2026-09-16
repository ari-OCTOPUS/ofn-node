# INTEGRATION GUIDE — وصل کردن رصدخانه به Octopus (`F:\backup`)

**تاریخ:** 2026-08-15 · **منبع:** پروژهٔ «هوشمند سازی» → مقصد: `F:\backup`
**مرحله:** یک از نُه (Egress Gateway). مراحل دو تا هشت هنوز ساخته نشده‌اند.

همه چیز **فقط‌خواندنی** و **fail-closed** است. فلگ `OBSERVATORY` پیش‌فرض `0`
است، پس کپی کردن این فایل‌ها هیچ رفتاری را تغییر نمی‌دهد تا رأی صریح تو.

---

## نگاشت فایل‌ها (کپی مستقیم)

| منبع (این پروژه) | مقصد (`F:\backup`) |
|---|---|
| `internet-observatory/impl/gateway.py` | `_ops/observatory/impl/gateway.py` |
| `internet-observatory/impl/robots.py` | `_ops/observatory/impl/robots.py` |
| `internet-observatory/impl/audit.py` | `_ops/observatory/impl/audit.py` |
| `internet-observatory/tests/test_gateway.py` | `_ops/observatory/tests/test_gateway.py` |
| `internet-observatory/tests/test_structural.py` | `_ops/observatory/tests/test_structural.py` |
| `internet-observatory/scripts/compile_policy.py` | `_ops/scripts/compile_observatory_policy.py` |
| `internet-observatory/architecture/observatory-policy.yaml` | `architecture/observatory-policy.yaml` |
| `internet-observatory/architecture/observatory-allowlist.yaml` | `architecture/observatory-allowlist.yaml` |
| `internet-observatory/handoff/ADR-041-internet-observatory.md` | `03 - Projects/research-spec-compiler/adr/ADR-041-internet-observatory.md` |
| `internet-observatory/handoff/capabilities-record.yaml` | ادغام در `architecture/capabilities-registry.yaml` |
| `internet-observatory/INTERNET-OBSERVATORY-EXECUTION-PLAN-2026-08-15.md` | `03 - Projects/research-spec-compiler/plans/` |

پوشهٔ `compiled/` را کپی **نکن** — خروجی build است و باید روی همان ماشین
ساخته شود تا checksum با YAML همان ماشین بخواند.

**تنها تنظیم لازم در کپی:** مسیر `sys.path` در بالای دو فایل تست، اگر ساختار
پوشه متفاوت شد. منطق عیناً می‌ماند.

---

## ترتیب commitها

1. `impl/` + `tests/` → commit **پس از سبز شدن** `py -m pytest _ops/observatory/tests -q` (۳۰ تست)
2. `architecture/observatory-policy.yaml` + `observatory-allowlist.yaml` → commit پس از `--check` سبز
3. `scripts/compile_observatory_policy.py` → commit
4. ADR-041 + capabilities-record → commit **فقط پس از رأی فاز ۸**

هیچ فایل موجودی حذف نمی‌شود — **improve don't rewrite**.

---

## وابستگی‌ها

```
# مسیر اجرایی: stdlib خالص. هیچ وابستگی جدیدی.
# فقط گام build و تست:
pyyaml      # فقط scripts/compile_policy.py — بیرون مسیر اجرایی
pytest      # فقط tests/
```

تست ساختاری `test_structural.py` این را در کد اجباری می‌کند: اگر روزی کسی
`requests` یا `yaml` را به `impl/` بیاورد، تست قرمز می‌شود.

---

## نحوهٔ اجرا

```powershell
# ۱) اعتبارسنجی سیاست و allowlist (بدون نوشتن)
py _ops\scripts\compile_observatory_policy.py architecture\ _ops\observatory\compiled\ --check

# ۲) کامپایل YAML → JSON برای gateway
py _ops\scripts\compile_observatory_policy.py architecture\ _ops\observatory\compiled\

# ۳) تست‌ها — همه باید سبز باشند
py -m pytest _ops\observatory\tests -q
```

استفاده از gateway در کد:

```python
import json
from observatory.impl.gateway import Gateway

policy = json.load(open("compiled/observatory-policy.json", encoding="utf-8"))
allow  = json.load(open("compiled/observatory-allowlist.json", encoding="utf-8"))

gw = Gateway(policy, allow, root=".")     # transport واقعی به‌طور پیش‌فرض
res = gw.fetch("https://www.rba.gov.au/statistics/cash-rate/")

if res.ok:
    evidence_id = res.evidence_id()       # OBS-INV-7
else:
    print(res.code, res.detail)           # هرگز استثنا؛ همیشه رد تایپ‌دار
```

`fetch` هیچ‌وقت استثنا پرتاب نمی‌کند. یا `FetchResult` می‌دهد یا `Refusal` با
کد دلیل — و هر دو در زنجیرهٔ audit ثبت می‌شوند.

---

## وضعیت تست‌ها

```
۳۰ تست سبز:
  ۱۰ تست منفی اجباری (N1..N10) + ۱ تست ریدایرکت زیادی
  ۷ تست ساختاری (S1 — هیچ فایلی جز gateway.py شبکه import نمی‌کند)
  ۱۲ تست تکمیلی (RFC 9309، ToS، audit، evidence_id، فلگ خاموش، ...)
```

هیچ تستی به شبکهٔ واقعی دست نمی‌زند — transport تزریق می‌شود.

**آزمون جهش (mutation) روی همین تست‌ها اجرا شد و هر ۷ جهش کشته شد:**

| جهش | نتیجه |
|---|---|
| حذف دروازهٔ متد | KILLED |
| حذف دروازهٔ scheme | KILLED |
| تطبیق exact دامنه → پسوندی | KILLED |
| حذف سقف بایت | KILLED |
| حذف kill-switch | KILLED |
| حذف سقف بودجه | KILLED |
| رفتار ۵xx مثل ۴xx در robots | KILLED |
| افزودن `import socket` به `robots.py` | KILLED (توسط S1) |

این مهم است چون ۳۰ تست سبز به‌تنهایی چیزی ثابت نمی‌کند — یک تست بی‌اثر هم سبز
است. جهش‌های کشته‌شده نشان می‌دهند تست‌ها واقعاً چیزی را می‌پایند.

---

## چهار مورد که عمداً پیاده **نشده**

صداقت در تحویل یعنی گفتن مرزها:

1. **انبار شاهد (L2) نیست.** `FetchResult.evidence_id()` فرمول را می‌دهد، ولی
   ذخیره‌سازی تغییرناپذیر و حالت replay کارِ مرحلهٔ دو است.
2. **rate limit per-domain اعمال نمی‌شود.** `rate_limit_rps` در allowlist ثبت
   شده ولی gateway فعلاً فقط سقف روزانه را می‌پاید. مرحلهٔ دو.
3. **بودجه در حافظه است، نه روی دیسک.** ری‌استارت، شمارنده را صفر می‌کند —
   نشتی بودجه. باید با انبار شاهد پایدار شود.
4. **`/rest/data/` ردیف E مستقیماً آزموده نشد.** فقط `/rest/dataflow/` تأیید شد.

هر چهار مورد در برنامهٔ اجرایی به مرحلهٔ دو موکول شده‌اند و در `capabilities-record`
به‌عنوان هشدار ثبت می‌شوند.

---

## چک‌لیست قبل از `OBSERVATORY=1`

- [x] ۳۰ تست سبز، شامل S1
- [x] جهش‌ها کشته شدند
- [x] `--check` روی سیاست و allowlist سبز
- [x] allowlist با امضای مالک (۲۰۲۶-۰۸-۱۵، پنج ردیف)
- [x] robots ردیف E مستقل بررسی شد (۴۰۳ CloudFront → RFC 9309 §2.3.1.3)
- [ ] انبار شاهد (مرحلهٔ دو)
- [ ] تست تعیّن replay (مرحلهٔ دو)
- [ ] بودجهٔ پایدار روی دیسک (مرحلهٔ دو)
- [ ] ≥ ۲۰ پیش‌بینی فریزشده (مرحلهٔ پنج)
- [ ] تأیید صریح مالک برای شروع اجرای ۳۰ روزه

تا وقتی همهٔ بندهای بالا تیک نخورده‌اند، `OBSERVATORY` روی `0` می‌ماند.
