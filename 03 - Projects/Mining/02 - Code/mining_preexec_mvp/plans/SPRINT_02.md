# SPRINT 02 — One-Node Benchmark Planning

Duration: 7 days  
Mode: benchmark planning + manual evidence capture only

## Objective
برنامه‌ریزی و قالب‌سازی برای benchmark یک OPi5، بعد از human verdict.

## Preconditions

- MIN-V1/MIN-V2/MIN-V3/MIN-V5/MIN-V6 بسته شده باشند.
- برق node benchmark امن باشد.
- wallet zero-access تأیید شده باشد.
- مالک انسانی اجرای benchmark را approve کند.

## Tasks

### Day 1 — Benchmark Protocol
- [ ] انتخاب یک node: OPI-X.
- [ ] تکمیل مشخصات hardware.
- [ ] انتخاب الگوریتم‌های benchmark.

### Day 2 — Safety Checklist
- [ ] threshold دما: warning=70°C, hard=75°C.
- [ ] duration اولیه: 30min smoke, سپس 24h.
- [ ] rejected shares threshold: <2%.

### Day 3 — Benchmark Result Template
- [ ] کپی `schemas/benchmark_result.schema.yaml` برای هر الگوریتم.
- [ ] آماده‌سازی گزارش دستی.

### Day 4 — Result Review
- [ ] پر کردن H/s/W/temp.
- [ ] invalid reason اگر داده ناقص است.

### Day 5 — Compare Algorithms
- [ ] H/s/W محاسبه شود.
- [ ] stability notes.
- [ ] candidate preferred algorithm.

### Day 6 — Update Constants
- [ ] فقط بعد از evidence، مقادیر الگوریتم در code/config به‌روزرسانی شوند.
- [ ] هیچ عدد unverified وارد source-of-truth نشود.

### Day 7 — Sprint Review
- [ ] Benchmark Report.md
- [ ] update OpenQuestions
- [ ] آماده‌سازی Sprint 03 read-only scouting

## Definition of Done

- حداقل یک benchmark معتبر 24h.
- H/s/W/temp ثبت شده.
- هیچ wallet secret در فایل‌ها نیست.
- هیچ buy/sell/withdraw نیست.
