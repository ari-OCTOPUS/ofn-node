---
id: pipeline
aliases: [pipeline, gate, pipeline and gate]
tags: [سیستم, #core]
related: ["[[Orchestrator]]", "[[W0-Verifier]]", "[[W1-Detector]]", "[[W2-Analyst]]", "[[W3-Reporter]]"]
---
# 🔄 Gate و Pipeline

> [!info] الگوی [[Orchestrator|Orchestrator]]-Worker با gate
> [[W0-Verifier|W0]] اول و به‌عنوان gate؛ بعد [[W1-Detector|W1]]-[[W3-Reporter|W3]] موازی یا ترتیبی.

## pipeline

```
W0 (gate) ──FAIL──► HALT + گزارش discrepancy به انسان
  │ PASS
  ▼
W1 (detect) ──► [[E-shadow|E_shadow]] > 0؟
  ▼
[[W2-Analyst|W2]] (analyze) ──► تفسیر هندسی ([[قضیه‌ی-Takens|Takens]]/[[تسراکت-و-سایه|تسراکت]])
  ▼
W3 (report) ──► report card + جدول Rosetta
```

## قاعده‌ی gate

> [!warning] W0 اگر FAIL کند، کل سیستم متوقف می‌شود
> هیچ آزمایشی نباید روی مدلِ تأیید‌نشده اجرا شود.## قراردادِ پیام

هر worker به orchestrator برمی‌گرداند:
۱. **اختلاف‌ها اول** — اعدادِ متفاوت با مرجع
۲. جدولِ نتایج با اشتقاق
۳. فرض‌های صریح
۴. مسیرهای ردشده
۵. ledger-diff پیشنهادی
۶. «چیزهایی که verify نکردم»

## منبع
- کد: `4d_system/agents/orchestrator.py`
- [[📄 متن-کامل-handoff]] §۷