---
type: report
status: draft
created_by: agent
tags: [octopus, audit, wiring, coherence, intelligence, read-only]
created: 2026-07-09
updated: 2026-07-09
---

# COHERENCE-AUDIT — لایهٔ هوش: اتصالات + walls (read-only، صفر تغییر)

> پاسِ verificationِ read-only روی سیلِ ماژول‌هایی که GLM real-time می‌سازد (هر ۳-۶ دقیقه commit). هیچ فایلی تغییر نکرد. هدف: آیا این‌ها منسجم/وصل/امن‌اند یا additive-unwired؟

## یافتهٔ کلیدی: سیستم **ماژول‌پُر، اتصال‌کم** است

GLM یک کتابخانهٔ غنیِ هوش ساخته (doctor/box/evolution/chamber/spectral · DualBrain · AcquisitionBrain · **Neural Integration v2: ۸ ماژول** SignalHub/ReflexArc/CircadianMap/ConsolidationCycle/Nociceptor/HebbianAssociator/SprintContract/HookBus · School/curriculum · sensory). ولی:

| چک | نتیجه |
|---|---|
| ۸ ماژولِ neural وصل به `organism.py`/`wiring.py`؟ | 🟡 **صفر** — هر ۸ تا additive-but-**unwired** (در حلقهٔ زنده fire نمی‌شوند) |
| testِ neural (`_ops/neural/test_neural.py`) در `run_all` (سوئیتِ گیت‌خورده)؟ | 🟡 **نه** — پس markerِ capability این ۸ ماژول را پوشش نمی‌دهد |
| School به sensory/afferent وصل؟ | ✅ **این نوبت بسته شد** (`school_bridge`) — بیرونِ لِینِ GLM |
| walls (money قفل / live / secret / PII) در ماژول‌های نو؟ | ✅ تمیز — صفر نقض (همه advisory/isolated طبق ادعا) |
| سوئیتِ کامل بعد از سیلِ ماژول‌ها | ✅ **۳۲/۳۲ سبز** (چیزی نشکست) |

## معنا (پاسخ به «ارتباطاتش تکمیل بشه»)
«تکمیلِ اتصالات» = ساختِ ماژولِ بیشتر **نیست** (آن هست + GLM سریع می‌سازد) — بلکه **wire کردنِ همین ماژول‌ها به تیکِ organism** است (پشتِ flag، paper-safe). الان تقریباً همه unwired‌اند. این کار `organism.py`/`wiring.py` را می‌زند = **فایل‌های زندهٔ GLM** → باید **هماهنگ/توسطِ GLM** انجام شود، نه موازی (تصادم).

## توصیه (ترتیب)
1. **یک wiring-passِ واحد** (GLM یا هماهنگ): ۸ ماژولِ neural + School را پشتِ flagهای `OCTOPUS_WIRE_*` به `organism` tick وصل کن (مثل الگوی موجودِ `wire_doctor`/`doctor_beat`). DoD: با flag روشن، هر ماژول در تیک fire می‌شود، paper/$0، walls دست‌نخورده.
2. **`test_neural` را به `run_all` اضافه کن** تا markerِ capability لایهٔ عصبی را هم گیت کند (الان پوشش نمی‌دهد).
3. **AwarenessField/School را به SignalHub/ConsolidationCycle متصل کن** (اجتناب از دو مسیرِ موازیِ حافظه: `school_bridge` منِ vs `ConsolidationCycle` GLM — یکی‌شان canonical شود).

## چه چیزِ غیرتکراری این نوبت اضافه شد (بیرونِ لِینِ GLM)
- `_ops/afferent/school_bridge.py` (+test ۵/۵) — afferent→School (یادگیری از کلاس) + persistِ awareness (حافظه). تنها حلقهٔ باز که در لِینِ GLM نبود.
- `_ops/afferent/ingest_raw.py` + ۲۱ نوتِ summary/structure — afferent 0.0→0.5 (سیستم دیگر «رؤیا» نمی‌بیند).
- همه uncommitted (GLM زنده commit می‌کند؛ interleave خطرناک) — برای مالک.

> ⚠️ همپوشانی: `ConsolidationCycle` (GLM، ۵ ثانیه پیش) و مسیرِ حافظهٔ منِ (`school_bridge` persist) هم‌پوشان‌اند — مالک تصمیم بگیرد کدام canonical است تا دو مسیرِ حافظه واگرا نشوند.
