# LIVE-GATE CARD — VQ-MISSION-CARD-ARM-001

```text
Decision ID     VQ-MISSION-CARD-ARM-001
Exact effect    (۱) merge شاخهٔ claude/octopus-code-integration-175ecb به
                fix/tg-p2-2026-07-30 (ff نیست — درخت زنده dirty است؛ merge
                توسطِ مالک/جلسهٔ مالکِ درخت زنده)
                (۲) افزودنِ `set OCTOPUS_WIRE_MISSION_CARD=1` به OCTOPUS-flags.cmd
                (۳) restart ِ organism (فقط پروسهٔ organism؛ tg-center لازم نیست)
Files/process   OCTOPUS-flags.cmd · پروسهٔ organism (پورت 8771)
Why needed      دو mission ِ واقعی با needs_approval از ۰۷-۳۰/۰۷-۳۱ در
                state/test_cycle/missions.jsonl نشسته‌اند و مالک هیچ کارتی
                ندیده. درز تست‌شده (۷/۷ + ۵ جهشِ قرمز) و content-free است.
Blast radius    حداکثر ۳ کارتِ pending در هر beat (cap)، فقط صفِ ap: ِ موجود؛
                صفر send ِ مستقیم — رندر و رأی همان مسیرِ فعلیِ center.
Max duration    دائمی پس از arm؛ هر لحظه با برداشتنِ فلگ + restart برگشت‌پذیر.
Max messages    برای backlog ِ فعلی: دقیقاً ۲ کارت (دو mission ِ موجود).
Preconditions   merge سبز؛ run_all ِ درخت زنده پس از merge بدونِ قرمزِ نو.
Success         approvals.json دو jobِ mission_approval با id ِ mis-… می‌گیرد و
                کارتِ pending در Inner-flow ِ center دیده می‌شود؛ رسیدِ audit
                در _octopus/logs/audit.log.
Failure         کارتِ تکراری، یا کارتی با متنِ هدف (content leak)، یا هر خطای
                center → فلگ را بردار.
Rollback        set OCTOPUS_WIRE_MISSION_CARD=  (حذفِ خط) + restart organism؛
                jobهای ساخته‌شده با reject در همان UI بسته می‌شوند.
Stop condition  STOP-ORGANISM / HALT-ALL طبقِ معمول مقدم‌اند.
Owner phrase    OWNER_AUTH: ARM FLAG OCTOPUS_WIRE_MISSION_CARD
```

## بندِ جدا (رأی جدا) — VQ-MEMORY-READ-ARM-001

```text
Effect          set OCTOPUS_WIRE_MEMORY_READ=1 + restart organism
Why             ثبتِ مشاهده‌پذیرِ retrieval در دفترِ چرخه (action_memories_used)
                تا دادهٔ A/B ِ §۱۰.۵ جمع شود. بر plan صفر اثر دارد (سنجه + جهش).
Blast           فقط چند خواندنِ FTS ِ محلی در هر چرخه (۲ اسلات/روز) — $0.
Rollback        حذفِ فلگ + restart.
```

رأیِ یک کارت برای کارتِ دیگر معتبر نیست.
