# Architecture — Mining Pre-Execution MVP

## 1. هدف

ساختن هسته پایه‌ای که قبل از هر mining execution بتواند پروژه را از نظر governance، hardware، electricity، wallet policy و coin scouting بررسی کند.

## 2. لایه‌ها

```text
User / Agent
   |
   v
CLI / Reports
   |
   +--> Governance Gates
   |       - VERDICT_QUEUE gate
   |       - electricity gate
   |       - wallet zero-access gate
   |       - hard-gated action guard
   |
   +--> Hardware Registry Validator
   |       - node_id
   |       - status
   |       - power_source
   |       - electricity cost
   |
   +--> Coin Scout Draft
   |       - algorithm classifier
   |       - launch age
   |       - dev/community evidence
   |       - mining data completeness
   |
   +--> Death Watch
           - dev_dead_weeks
           - chain_stalled
           - community_dead
```

## 3. ماژول‌ها

| فایل | نقش |
|---|---|
| `models.py` | dataclassها و enumها |
| `constants.py` | قوانین ثابت پروژه |
| `governance.py` | گیت‌های حاکمیتی و hard stopها |
| `registry.py` | loader/validator رجیستری سخت‌افزار |
| `verdicts.py` | loader برای VERDICT_QUEUE YAML |
| `algo_classifier.py` | تشخیص محافظه‌کارانه الگوریتم CPU/ARM |
| `scout.py` | امتیازدهی draft کوین‌ها |
| `death_watch.py` | ارزیابی D2 death-watch |
| `report.py` | تولید گزارش Markdown |
| `cli.py` | رابط command line |

## 4. الگوی امنیتی

- هیچ secret خوانده نمی‌شود.
- هیچ network call وجود ندارد.
- هیچ subprocess اجرا نمی‌شود.
- هیچ miner binary کنترل نمی‌شود.
- هیچ wallet field اجباری نیست.

## 5. مسیر توسعه بعدی

بعد از بستن VERDICT_QUEUE:

1. افزودن `benchmark_report` برای ثبت دستی H/s/W/temp.
2. افزودن `death_watch_log` برای کوین فعال.
3. اتصال report-only به Obsidian noteهای پروژه.
4. ساخت scout source adapters فقط به صورت read-only و با cache.
5. ساخت fleet report adapter که فقط فایل‌های status را بخواند، نه nodeها را.
