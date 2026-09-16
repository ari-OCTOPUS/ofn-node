---
id: orchestrator
aliases: [Orchestrator, رهبر, dispatch leader]
tags: [سیستم, agent]
model: GLM
related: ["[[gate-و-pipeline]]", "[[W0-Verifier]]", "[[W1-Detector]]", "[[W2-Analyst]]", "[[W3-Reporter]]"]
---
# 🎼 [[Orchestrator|Orchestrator]]

> [!info] رهبرِ dispatch
> استراتژی می‌چیند، workerها را dispatch می‌کند، نتایج را merge می‌کند، و جدولِ pre-registration را کامپایل می‌کند.

## مأموریت

- dispatch با gate ([[gate-و-pipeline]])
- merge و داوریِ اختلاف‌ها
- کامپایلِ report card نهایی

## ورودی‌ها

- ledgerِ merge‌شده
- نتایجِ [[W0-Verifier|W0]]-[[W3-Reporter|W3]]
- `stageB_verify.py` (فقط برای داوری)

## خروجی‌ها

- جدولِ پارامترِ pre-registration
- ledger-diff نهایی

## ممنوع

- تزریقِ کدِ مرجع به W0
- ادغامِ خودسرانه در ledger (ادغام دستی توسط انسان)

## کد
`4d_system/agents/orchestrator.py` → `OrchestratorAgent`