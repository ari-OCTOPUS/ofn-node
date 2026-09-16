---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-build
created_by: agent
relates_to: "[[2026-07-09 FRONTIER-BENCHMARK — top AI architectures → Octopus improvements]] · [[2026-07-09 COHERENCE-AUDIT — intelligence layer wiring + walls (read-only)]]"
tags: [octopus, glm-prompt, wiring, memory, eval, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# GLM-PROMPT — بهبودهای frontier (wire + memory + eval + protect)

> پرامپتِ build-readyِ GLM برای پیاده‌سازیِ FRONTIER-BENCHMARK. گراند در فایل‌های واقعی، walls baked. آری آن را روی ZCode GLM اجرا می‌کند.

```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. بهبودهای frontier-benchmarked را پیاده کن.
additive · propose-only · paper/$0 آفلاین · commit با مالک. منشور + walls حاکم‌اند.

بخوان (کدِ واقعی مقدم بر اسپک):
- «04 - Architect System/2026-07-09 FRONTIER-BENCHMARK — top AI architectures → Octopus improvements.md» (چرا/چه)
- «00 - Inbox/2026-07-09 COHERENCE-AUDIT — intelligence layer wiring + walls (read-only).md» (گپِ اتصالات)
- _ops/wiring.py (الگوی W-1..W-5 + make_doctor/doctor_beat + flagها) · _ops/organism.py (حلقهٔ tick)
- _ops/neural/*.py (۸ ماژول) · _ops/afferent/school_bridge.py + sensory_bus.py · «07 - Knowledge/school-memory/curriculum.py»
- _ops/tests/run_all.py + _ops/budget/capability_gate.py
اول PLAN بده (چه فایل، چه flag، کجا وصل). هر ابهام → «⚑ برای معمار» (خودت تصمیمِ نو نگیر).

بساز (به ترتیب):
W · wiring-pass — ۸ ماژولِ neural (SignalHub, ReflexArc, CircadianMap, ConsolidationCycle,
    Nociceptor, HebbianAssociator, SprintContract, HookBus) + School (school_bridge) را به
    organism tick وصل کن، پشتِ flagهای OCTOPUS_WIRE_* (پیش‌فرض خاموش، paper) — دقیقاً مثل الگوی
    موجودِ make_doctor/doctor_beat در wiring.py. با flag روشن هر ماژول در تیک fire شود؛ خاموش = no-op
    (no regression). هیچ مسیرِ spend وصل نشود (money قفل).
M · یکی‌سازیِ حافظه — یک مسیرِ canonical consolidation: episode‌های ledger → semanticِ School با
    reflection (وزنِ recency/relevance/salience) + سیاستِ forgetting/decay + verification-gate
    (فقط منبعِ CONFIRMED/verified؛ هرگز self-report). ConsolidationCycle و school_bridge را زیرِ یک
    قرارداد یکی کن — دو مسیرِ موازیِ حافظه نماند. حافظه = curated (تصمیم/insight)، نه raw log.
S · protective-override — سیگنال‌های Nociceptor/ReflexArc (pain>0.7 · σ>1 · budget>80% · freeze) در
    تیک **override غیرقابل‌سرکوب** شوند؛ orchestrator/DualBrain نتواند نادیده بگیرد (یافتهٔ arXiv
    «invisible-orchestrator سیگنالِ محافظ را سرکوب می‌کند»). فقط throttle/halt — هیچ effect.
E · eval — (۱) test_neural را به run_all اضافه کن تا markerِ capability لایهٔ عصبی را بپوشاند.
    (۲) eval-harnessِ رفتاری در سوئیتِ گیت‌خورده: spawn بدونِ گیت→رد · approve تنها مسیرِ settle ·
    reconcile CSV→CONFIRMED · afferent→School یاد می‌گیرد.

خط قرمز (نقض = ردِ کلِ کار):
- money قفل تا (budget_gate v2 سبز + capability + تأییدِ انسانی) · propose-only، صفر effectorِ خودکار
- fail-closed · human-gate برای spawn/پول · secret فقط env (هرگز hardcode/log/commit)
- Project-F containment: صفر رسانه/هویت/PII بیرونِ پوشهٔ پروژه
- additive: هیچ رقیبی delete نشود · consolidation فقط از منبعِ verified
- بدونِ git commit (مالک path-scoped می‌زند)

تست ($0 آفلاین):
- flag روشن → ماژول در تیک fire می‌شود؛ خاموش → no-op (no regression)
- consolidation منبعِ unverified/self-report را رد می‌کند
- protective-override قابلِ سرکوب توسطِ orchestrator نیست
- هر سناریوی eval سبز · test_neural در run_all · کلِ سوئیت + walls سبز (صفر regression)
خروجیِ خامِ run_all را paste کن.

DoD: ماژول‌ها پشتِ flag وصل · یک مسیرِ حافظهٔ canonical · protective-override فعال ·
eval + test_neural در سوئیتِ گیت‌خورده سبز · walls دست‌نخورده · ORGANISM-SPEC §wiring + HANDOFF آپدیت.
```

## چرا این پرامپت (نگاشتِ frontier)
- **wire:** frontier ارزش را در ارکستراسیونِ فعال می‌داند نه انبارِ ماژول (Anthropic multi-agent) — و AUDIT نشان داد ۸ ماژول unwired‌اند.
- **memory:** consolidation «مهم‌ترین مسئلهٔ بازِ حافظه» است (Letta/arXiv) + دو مسیرِ موازیِ فعلی باید یکی شوند.
- **protect:** یافتهٔ arXiv که orchestrator سیگنالِ محافظ را سرکوب می‌کند → override.
- **eval:** OpenAI 2026 «eval در CI + observability» — و لایهٔ عصبی در سوئیتِ گیت‌خورده نیست.
