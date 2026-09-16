---
aliases: [MOC سیستم, System MOC, MOC معماری]
tags: [MOC, سیستم, معماری]
---

# 🤖 MOC — سیستم مولتی‌ایجنت

> [!info] پیاده‌سازیِ عملی
> سیستم 4d_system یک pipeline چهارمرحله‌ای مبتنی بر Orchestrator-Worker که داده‌های خام را تحلیل می‌کند و نشانه‌های بُعد پنهان را کشف می‌کند.

## 🏗️ معماری چهارلایه‌ای

- [[معماری-چهارلایه‌ای]] — UI / Agents / Core+Data / Reference

```
┌───────────────────────────┐
│   Streamlit (ui/app.py)   │  ← لایه‌ی ۴: رابط
├───────────────────────────┤
│  Agents (Orchestrator)    │  ← لایه‌ی ۳: مولتی‌ایجنت
├───────────────────────────┤
│  Core + Data              │  ← لایه‌ی ۲: موتور ریاضی + داده
├───────────────────────────┤
│  4D/ (READ-ONLY)          │  ← لایه‌ی ۱: مرجع تغییرناپذیر
└───────────────────────────┘
```## 🤝 تیمِ ایجنت

| ایجنت | نقش | مدل | یادداشت |
|---|---|---|---|
| Orchestrator | dispatch + gate | GLM | [[Orchestrator]] |
| W0 Verifier | راستی‌آزمایی لنگرها | GLM | [[W0-Verifier]] |
| W1 Detector | تشخیص سایه | GLM | [[W1-Detector]] |
| W2 Analyst | تفسیر هندسی | Fugu | [[W2-Analyst]] |
| W3 Reporter | گزارش نهایی | GLM | [[W3-Reporter]] |

## 🔄 pipeline

- [[gate-و-pipeline]] — W0 (gate) → W1 → W2 → W3

```
W0 (gate: لنگرها PASS شد؟) ──FAIL──► HALT
  │ PASS
  ▼
W1 (تشخیص: [[E-shadow|E_shadow]] > 0؟)
  ▼
W2 (تحلیل هندسی: [[قضیه‌ی-Takens|Takens]]/[[تسراکت-و-سایه|تسراکت]])
  ▼
W3 (گزارش: report card + Rosetta)
```

## 🔌 API و داده

- [[روتر-LLM]] — GLM + Fugu + Mock fallback
- [[mock-mode]] — کار بدون API key
- [[داده-مصنوعی]] / [[داده-فیزیکی]] / [[داده-واقعی-API]] / [[آپلود-CSV]]## ⚖️ قانون طلایی

> [!warning] 4D/ فقط خوانده می‌شود
> دایرکتوری `4D/` منبعِ تغییرناپذیر است. سیستم **هرگز** به آن نمی‌نویسد. `4d_system/knowledge/ledger.py` فقط می‌خواند.

## 📂 محل فیزیکی

```
C:/Users/Armin/Desktop/
├── 4D/              ← مرجع (دست‌نخورده)
├── 4d_system/       ← سیستم قابل اجرا
└── 4D-Vault/        ← این vault (شما اینجا هستید)
```