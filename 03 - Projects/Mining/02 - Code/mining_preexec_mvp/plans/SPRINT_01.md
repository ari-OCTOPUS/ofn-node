# SPRINT 01 — Registry + Gate Closure Preparation

Duration: 7 days  
Mode: report-only

## Objective
آماده‌سازی اطلاعات واقعی لازم برای خروج از ابهام pre-execution، بدون اجرای هیچ miner یا SSH.

## Tasks

### Day 1 — Inventory Template
- [ ] کپی `schemas/hardware_registry.schema.yaml` به یک فایل working.
- [ ] ثبت همه دستگاه‌ها با ID ثابت: OPI-1.., ESP-1.., FPGA-1...
- [ ] بدون IP/password/seed.

### Day 2 — Physical Status
- [ ] برای هر دستگاه status بزن: unknown/offline/available/running/broken.
- [ ] مشخص کن کدام‌ها واقعاً Orange Pi 5 Pro هستند.
- [ ] مشخص کن کدام‌ها SD/eMMC/NVMe دارند.

### Day 3 — Electricity
- [ ] منبع برق هر location را تعیین کن.
- [ ] اگر grid است، نرخ $/kWh را ثبت کن.
- [ ] اگر solar/free است، evidence note اضافه کن.

### Day 4 — Verdict Draft
- [ ] برای MIN-V1..MIN-V6 پاسخ پیشنهادی بنویس.
- [ ] مالک انسانی باید approve/reject کند.

### Day 5 — Readiness Run
- [ ] اجرای CLI readiness روی YAMLها.
- [ ] تولید `output/readiness.md`.
- [ ] ثبت failed gates.

### Day 6 — Fix Missing Fields
- [ ] unknownها را کم کن.
- [ ] اگر چیزی هنوز unknown است، در OpenQuestions ثبت کن.

### Day 7 — Sprint Review
- [ ] DecisionLog update.
- [ ] TODO update.
- [ ] آماده‌سازی Sprint 02 benchmark.

## Definition of Done

- Hardware registry حداقل ۸۰٪ دستگاه‌های واقعی را پوشش دهد.
- هزینه/منبع برق برای nodeهای benchmark مشخص باشد.
- readiness report ساخته شود.
- هیچ execution انجام نشده باشد.
