---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: done
tags: [cortex, brains, ollama, router]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HH-P9-ALWAYS-ON-AUTONOMY]]"
  - "[[01 - Dashboard/HANDOFF]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P10 — مغزِ مرکزیِ جدا + سه‌مغزی (fugu/glm/ollama) — ساخته شد

> vision مالک (2026-07-10): «چند عضو، هرکدام آگاهیِ خودشان؛ همه وصل به مغزِ مرکزیِ
> جدا که مسئولِ مرتبیِ همه است؛ قلب ریتم را به کلِ ساختار منطبق می‌کند؛ مغزِ اصلی
> fugu، فرعی glm، و ollama برای کارهای سادهٔ روزمره؛ به همه جا API؛ آخرش اتوماتیک.»
> چهار رأیِ قفل‌شده در مشورت: qwen2.5:1.5b · پروسهٔ جدا 8772 · مرتب‌سازیِ $0 با کران ·
> اشتراک‌ها (fugu Pro + GLM MAX ~AU$200) خریده شده و **نصفِ سهمیه سهمِ سیستم** است.

## چه ساخته شد (تست: `test_cortex.py` ۸/۸)

- **`_ops/cortex/`** — پکیجِ مغزِ مرکزی، پروسهٔ جدا (`RUN-CORTEX.bat`، bind انحصاری 127.0.0.1:8772، STOP-CORTEX):
  - `registry.py`: ۱۰ عضو، هرکدام آگاهی از state-fileِ خودش (فقط‌خواندنی) → نمرهٔ تازگی/SLA + coherence وزنی.
  - `local_llm.py`: ollama (qwen2.5:1.5b — **دانلود و زنده شد**؛ پاسخ فارسی ~۱.۸s، $0، فقط localhost؛ rate-limit + timeout 90s cold-load).
  - `model_router.py`: درِ واحدِ سه‌مغزی — task→tier (روزمره→local، تحقیق→glm، orchestration→fugu)؛ **paid دوقفله** (تاریخ ≥ 2026-07-21 + `ACTIVATION-CORTEX-PAID.flag`) + lazy `organ_gate` (I2)؛ بسته/شکست → fallbackِ صادق به local. `keys_present()` فقط bool (هرگز مقدارِ کلید).
  - `cortex.py`: چرخه = sweep اعضا → **مرتب‌سازیِ کران‌دارِ نقشهٔ کارِ $0** (فقط ترتیب + every_s در [۰.۵×..۲×]؛ paid/kind هرگز؛ بدنِ STOP → فقط تماشا) → فکرِ ژورنال‌شده (append-only، ماندگار) → state + HTTP (`/api/cortex`، `/api/journal`، `POST /ask`). **ریتم از قلب**: period مغز = ۲×periodِ قلبِ سایه (کران ۶۰..۶۰۰s).
- **budgets.yaml** (SoT، طبقِ رأی): `routing.local` (ollama) + `system_share: 0.5` روی glm/orchestr + `subscription: pro` روی fugu.
- **کابین**: تبِ نهمِ «🧠 مغز مرکزی» (coherence، ریتم، مرتب‌سازی، وضعِ سه مغز و کلیدها، آخرین فکر).

## متر بعد از بازشدنِ گیت (طراحی — سهمیه‌ای نه فقط دلاری)

اشتراک‌ها flatاند → هزینهٔ مارجینال ≈ ۰ ولی **سهمیهٔ نصف** باید رعایت شود: هر call از
`organ_gate.reserve/settle` می‌گذرد (شمارشِ استفاده)؛ گزارشِ ماهانهٔ سهمِ سیستم از
سهمیه = کارِ فازِ بعد (وقتی providerها dashboard usage بدهند). تا آن روز estimate.

## میزِ مالک (برای کامل‌شدنِ سه‌مغزی)

1. **کلیدها در `F:\backup\.env`** (ایجنت هرگز نمی‌خواند/نمی‌نویسد): `FUGU_API_KEY=` · `GLM_API_KEY=` · `GLM_BASE_URL=` (از dashboardِ MAX). تا نباشند، router صادقانه «بی‌کلید» نشان می‌دهد و local کار می‌کند.
2. **schtask سوم**: `schtasks /Create /TN "OCTOPUS-Cortex" /SC ONLOGON /TR "F:\backup\_ops\RUN-CORTEX.bat"` (+ یک‌بار دستی الان: دابل‌کلیک RUN-CORTEX.bat).
3. 2026-07-21+: ساختنِ `ACTIVATION-CORTEX-PAID.flag` → glm/fugu در router زنده می‌شوند.
4. ارتقایِ مدلِ محلی (اختیاری، 1660Ti جا دارد): `ollama pull qwen2.5:7b-instruct-q4_K_M` + ‏`OLLAMA_MODEL` در OCTOPUS-flags.cmd.

## خطوطِ قرمز (بی‌تغییر)

مغز جداست (coupled-not-merged — کرashِ هرکدام دیگری را نمی‌کشد) · فقط کارِ $0 را مرتب می‌کند؛ پول/merge/حذف هرگز · σ/قلب/HLC دست‌نخورده · کلیدها فقط env؛ حتی presence فقط bool · STOP همیشه برنده.
