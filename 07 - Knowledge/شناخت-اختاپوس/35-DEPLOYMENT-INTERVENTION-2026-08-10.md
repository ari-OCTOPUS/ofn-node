---
type: knowledge
status: active
tags: [deployment, model-map, deepseek, fugu, intervention, soak, sre]
created: 2026-08-10
updated: 2026-08-12
created_by: agent
related:
  - "[[34-SEED-AGENT-OWNER-COCKPIT-2026-08-08]]"
---

# ۳۵ — Deployment Intervention: نقشهٔ مدل‌ها + درس‌های SRE (۲۰۲۶-۰۸-۱۰)

## ریشهٔ واقعی (تصحیح زنجیرهٔ تشخیص)

دو ایجنت متوالی دو ریشهٔ متفاوت اعلام کردند:
- گزارش SRE: «کلید placeholder است → 401»
- گزارش Deployment: «کلید معتبر است → 400 max_tokens»

**حقیقت: هر دو تا حدی درست بودند، ولی 401 اسکنر اول artefact پراب خودش بود.**
`env_loader.load_env()` مقدار را برنمی‌گرداند — فقط برچسب امن `"set"` می‌دهد.
اسکنر اول با برچسب (نه مقدار) تست زد → 401 طبیعی. این دومین artefact اسکنر در
یک روز بود (اولی: pid=None).

**ریشهٔ واقعی فنی:** کلید Fugu همیشه معتبر بوده. شکست‌های واقعی از ترکیب
`HTTPError` (شب ۰۸-۰۸/۰۹، احتمالاً network) + fail ceiling پایین (3) → STOP-FUGU →
۹۶ deny. بعد از حذف STOP-FUGU با کلید صحیح: HTTP 200.

## تغییر اعمال‌شده (Deployment)

| فایل | تغییر |
|---|---|
| `_ops/cortex/model_router.py:117` | `_TIER_ROLE.secondary: glm → reason` (deepseek) |
| `.env` | `DEEPSEEK_API_KEY` اضافه شد (len=35) |
| `_ops/state/intervention-ledger.jsonl` | ورودی `model_map_change` ثبت شد |
| `_ops/state/soak-baseline.json` | baseline ۷۲ساعته از 2026-08-10T06:55Z |
| `_ops/agi2027_control/runtime.py` | `/truth` به resolver مشترک miniapp_state وصل شد (drift سندی) |
| `README.md` | Security Gate: «بسته 🔴» → «باز 🟢» (drift سندی) |

## تأیید زنده (پس از ری‌استارت cortex)

```
16:48:47  secondary  model=glm-4.6            (حافظهٔ قدیمی)
16:55:03  secondary  model=deepseek-v4-flash  ✅ (پس از ری‌استارت)
```

## درس‌های ساختاری (backlog — ممنوع الاجرا بدون تأیید)

1. **تست‌های زنده باید از همان مسیر credential-loading پروداکشن استفاده کنند** —
   نه خواندن مستقیم .env. (اسکنر اول از مسیر اشتباه خواند)
2. **env_loader به API جدا نیاز دارد**: `is_set(key)` برای چک امن،
   `get(key)` برای مصرف واقعی — تا برچسب ماسک هرگز به‌جای مقدار مصرف نشود.
3. **هر root cause قبل از نوشتن در ledger با پراب مستقل دوم تأیید شود** —
   دو artefact اسکنر در یک روز (pid=None + 401 جعلی).
4. **hot-reload وجود ندارد** — پایتون ماژول را یک‌بار در startup import می‌کند.
   تغییر ماژول → ری‌استارت لازم است. (در این جلسه اثبات شد: GLM تا ری‌استارت ماند)
5. **D-02 (ثبت policy/model version در هر episode)** از «خوب است» به «لازم»
   ارتقا یافت — بدون آن، attribution هر تغییر مدل از دست می‌رود.

## Soak ۷۲ساعته

- شروع: 2026-08-10T06:55:46Z
- پایان: 2026-08-13T06:55:46Z
- baseline: `_ops/state/soak-baseline.json` (beat=30338, bcm=146, semantic=517)
- هر drift رفتاری در این بازه با تعویض مدل confound دارد.

## به‌روزرسانی‌های بعد از review (۲۰۲۶-۰۸-۱۰ بعدازظهر)

1. **center ری‌استارت شد** (pid 14580→11284) — /truth واقعاً زنده شد
   (proof: integration → runtime → status=OK, preview=335). درسِ hot-reload
   برای center هم صادق بود.
2. **http_code ساختاری** به paid-calls اضافه شد (`_error_http_code` در
   model_router) — دیگر 400/429/5xx از متن حدس زده نمی‌شود.
3. **soak_scorecard.py** ساخته شد — کارت امتیاز با آستانه‌های هشدار/توقف.
   اولین چک: **GREEN** (success 1.0، restart 0، deny رشد 0).
4. **soak-baseline v2** — شروع واقعی 16:24 محلی (اولین موفق بعد از حذف
   STOP-FUGU). v1 (06:55Z) UTC/local قاطی شده بود.
5. **intervention-ledger**: status=interim، مصرف‌کننده=soak_scorecard
   (deny_baseline + planned_restarts). تا وصل به D-02.
6. **BOM در runtime.py**: فایل با U+FEFF شروع می‌شود (از قبل بود، در پنجرهٔ
   soak دست نمی‌زنیم). برای جلسهٔ بعد: strip در اولین ویرایشِ غیر-soak.

## DEFER (لیست)

- گیت‌وی LiteLLM :4000 (فاز ۶ — با تأیید جداگانه)
- causal pilot (DoWhy/EconML — بعد از P0/P1)
- هر provider/governor موازی
- replay خودکار ۵۰۹ پیام archive — ممنوع (ریسک duplicate effect)
