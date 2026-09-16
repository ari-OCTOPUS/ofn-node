---
type: runbook
status: active
tags: [learning-engine, startup, bootstrap, governance]
created: 2026-07-06
updated: 2026-07-06
---

# STARTUP-PROTOCOL — مصاحبه شروع هر جلسه (boot interview)

> **هدف:** هر بار سیستم روشن می‌شود (شروع هر جلسه تعاملی)، ایجنت قبل از هر کاری اطلاعات حیاتی را از آری می‌گیرد، در `LEARNING-STATE.json` می‌نویسد و بر اساسش سطح عملیات همان جلسه را تعیین می‌کند.
> verdict آری 2026-07-06: «تموم اطلاعات حیاتی که من باید بدم در استارت خوردن ازم بگیرد — هر سری روشن میشود.»

## ۱. trigger

در شروع هر جلسه تعاملی، بلافاصله بعد از خواندن HANDOFF و قبل از هر کار دیگر:

1. `LEARNING-STATE.json` را بخوان.
2. `STARTUP-CHECKLIST.yaml` را بخوان و برای هر سوال، شرط `ask_if` را چک کن.
3. فقط سوال‌هایی را بپرس که **باز یا کهنه‌اند** (skip-logic §۳) — حداکثر ۴ سوال در هر نوبت، به ترتیب priority.
4. جواب‌ها را در targetهای مشخص بنویس + یک ردیف در [[_memory/EXPERIENCE-LEDGER|ledger]] append کن + سطر `learning-engine` در [[_memory/HEARTBEAT|HEARTBEAT]] به‌روز شود.
5. سطح عملیات جلسه را اعلام کن: چه چیزی این جلسه باز شد، چه چیزی قفل ماند.

## ۲. قواعد سخت (غیرقابل مذاکره)

- **هرگز مقدار secret نپرس و نپذیر.** اگر آری در چت secret بنویسد: استفاده نکن، echo نکن، فقط بگو در password manager/سر سرویس بگذارد و در چت revoke/rotate کند. سوال‌ها فقط **وضعیت/عدد/تصمیم** می‌گیرند (مثلاً «کلید ثبت شد؟ بله/نه» نه خود کلید).
- جواب آری = verdict ثبت‌شدنی؛ هر جواب با تاریخ در ledger append می‌شود (audit trail).
- بی‌جوابی = وضعیت قبلی می‌ماند (fail-closed)؛ هیچ قفلی با سکوت باز نمی‌شود.
- «همه‌چیز باز» فقط با جواب صریح به تک‌تک سوال‌های همان قفل — نه با یک «بله» کلی.
- اگر جواب جدید با verdict قبلی تناقض داشت: تناقض را نشان بده و تأیید دوباره بگیر (مثل سابقه git init: نه ← بله).

## ۳. skip-logic (که هر سری همه‌چیز پرسیده نشود)

| کلاس سوال | کی می‌پرسد |
|---|---|
| قفل‌های باز (`unlock`) | تا وقتی باز است، **هر جلسه** — این‌ها همان «اطلاعات حیاتی»اند |
| مقادیر تنظیمی (`config`) | فقط اگر `null`/نامعتبر باشد یا آری بگوید «تنظیمات» |
| وضعیت‌های کهنه (`stale`) | اگر از آخرین تأیید > `ttl_days` گذشته باشد (مثلاً مرور اشتراک Fugu ماهانه) |
| رویدادی (`event`) | فقط وقتی رویدادش رخ داده (مثلاً بعد از reset زمان‌بند: «Run now زدی؟») |

## ۴. بانک سوال = `STARTUP-CHECKLIST.yaml`

تک‌منبع سوال‌ها، شرط‌ها و مقصد نوشتن هر جواب. سوال جدید = ویرایش همان فایل (با verdict). خلاصه فعلی:

| id | سوال (خلاصه) | کلاس | می‌نویسد در |
|---|---|---|---|
| rotation_status | وضعیت ۴ ردیف CRITICAL در [[ROTATION_CHECKLIST]] | unlock | STATE.security_gate_status (+ اقدام دستی مالک برای lift رسمی) |
| fugu_key_registered | ردیف کلید Fugu در ROTATION ثبت شد؟ (وضعیت، نه مقدار) | unlock | STATE.external_calls_unlock |
| budget_daily | سقف بودجه روزانه خارجی (عدد) | unlock/config | STATE.budget_ceiling_daily |
| fugu_tier | کدام tier اشتراک Fugu | config | STATE.fugu_tier |
| git_init | git init — خودت/من با verdict/فعلاً نه | unlock | STATE.git_ready (+ اجرا فقط با verdict صریح) |
| gate0_projectF | GATE 0 پروژه F (فقط اگر کار آن پروژه در دستور باشد) | event | PROJECT.md همان پروژه |
| subscription_review | مرور ماهانه اشتراک Fugu (auto-renew) | stale (ttl=30) | ledger |
| run_now_preapprove | «Run now» روی تسک‌های ratified بعد از هر reset | event | HEARTBEAT |

## ۵. خروجی هر boot

بعد از جواب‌ها، ایجنت این را اعلام می‌کند (قالب ثابت):

```
🔑 BOOT 2026-MM-DD — سطح این جلسه
باز شد: <چیزهایی که با جواب امروز باز شد>
قفل ماند: <قفل‌های هنوز باز + دلیل>
mode Engine: shadow | full
اقدام دستی معوق آری: <لیست>
```

## ۶. اتصال به بقیه ساختار

- **HANDOFF §«جلسه بعد باید»** خط اول: «اول boot interview طبق [[04 - Architect System/learning-engine/STARTUP-PROTOCOL|STARTUP-PROTOCOL]]».
- جواب‌ها فقط در `LEARNING-STATE.json` + ledger + HEARTBEAT نوشته می‌شوند؛ ROTATION_CHECKLIST و charter همچنان فقط دست مالک.
- این پروتکل خودش contract L2 (control) است — Engine گزارش می‌دهد، آری verdict می‌دهد.
