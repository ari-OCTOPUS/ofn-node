---
id: w3-reporter
aliases: [W3, Reporter, گزارش‌نویس]
tags: [سیستم, agent]
model: GLM
related: ["[[W0-Verifier]]", "[[W1-Detector]]", "[[W2-Analyst]]", "[[نقشه‌ی-Rosetta]]"]
---
# 📝 W3 — [[W3-Reporter|Reporter]]

> [!info] گزارش‌نویسِ نهایی
> نتایجِ همه‌ی workerها را در یک report card کامل کامپایل می‌کند + جدولِ Rosetta.

## مأموریت

- ترکیبِ نتایجِ [[W0-Verifier|W0]] (verify)، [[W1-Detector|W1]] (detect)، [[W2-Analyst|W2]] (analyze)
- ساختِ report card: فرضیه / داده / کمیت‌ها / تأیید-رد / محدودیت‌ها / گامِ بعد
- کامپایلِ [[نقشه‌ی-Rosetta]]
- اعلامِ verdict و درجه‌ی اطمینان

## خروجی

| فیلد | محتوا |
|---|---|
| verdict | SUPPORTED / NULL / PROVISIONAL |
| confidence | high / medium / low |
| rosetta_table | پروژه ↔ ریاضی ↔ تجربه |
| report_card | متنِ کامل |## قاعده

> [!important] صادق باش
> اگر نتیجه منفی است، آن را ثبت کن — نتایجِ منفی هم ارزشمندند.
> → [[قواعد-شش‌گانه]] قاعده‌ی ۵

## کد
`4d_system/agents/reporter.py` → `ReporterAgent`