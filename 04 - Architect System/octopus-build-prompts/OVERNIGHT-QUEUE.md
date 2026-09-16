---
type: runbook
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-execution
tags: [octopus, overnight, autonomous, queue, glm]
created: 2026-07-08
updated: 2026-07-08
---

# OVERNIGHT QUEUE — صفِ خودگردانِ شبانه برای GLM

> GLM این فایل را از بالا به پایین اجرا می‌کند. هر آیتم = «پرامپتِ ارجاع‌شده را بخوان، اجرا کن، سبزیِ خام را اثبات کن، checkpoint-commit بزن، برو بعدی». **روی هر قرمز/ابهام هارد-استاپ + گزارشِ ⚑ — هرگز روی خطا جلو نرو.**

## قراردادِ خودگردانی (بالای هر آیتم حاکم است)
```
تو کارگرِ کدنویسِ خودگردانِ Octopus (GLM) هستی، شبانه بدونِ ناظر. قواعدِ ثابت:
- بعد از هر آیتم: python _ops/tests/run_all.py را اجرا کن؛ اگر همه سبز نبود → همان‌جا بایست، یک نوتِ ⚑ STOP در 00 - Inbox/OVERNIGHT-LOG.md بنویس (چه شکست، خروجیِ خام)، و آیتمِ بعدی را شروع نکن.
- روی سبز: checkpoint-commit بزن — git add فقط مسیرهای همان آیتم؛ git reset -- "**/*.db" "_ops/state/chrono.db"؛ commit با پیامِ «overnight <آیتم>: green». (این تنها استثنای مجازِ commitِ خودکار است، فقط path-scoped، Windows-side، هرگز *.db/.env.)
- ناوردی‌ها بی‌استثنا: propose-only · sandbox · human-append برای هر merge · money قفل تا 2026-07-21 · λ_persist منفی · secret فقط env · هیچ import از production گیت/قلب مگر آیتم صریح بگوید · هیچ اثرِ زنده/شبکه/پول.
- هر ابهامِ معماری → «⚑ برای معمار (Claude)» در OVERNIGHT-LOG، و اگر بلاک‌کننده بود هارد-استاپ.
- گزارشِ هر آیتم (فایل‌ها + خروجیِ خامِ تست) را در 00 - Inbox/OVERNIGHT-LOG.md append کن تا صبح مرور شود.
```

## ترتیبِ صف (وابستگی‌محور)

**۰ · (قبل از شروع — مالک، ۱۰ ثانیه):** commitِ چک‌پوینتِ P1–P5 طبقِ `GO-LIVE-PACK §۱`. اگر مالک نزد، GLM به‌عنوان اولین کار یک checkpoint-commitِ path-scoped از وضعِ فعلی بزند تا مبنا امن شود.

**۱ · WIRING (حلقهٔ زنده):** پرامپت = `GO-LIVE-PACK.md §۲`. ۵ لایه را یک حلقه کن. → run_all سبز → commit.

**۲ · DOCTOR EVOLUTION:** پرامپت = `DOCTOR-EVOLUTION-BENCHMARK-10systems.md §۵` (آرشیوِ QD + measured-lift + tournament). → سبز → commit.

**۳ · SPECTRAL-SENSE:** پرامپت = `07 - Knowledge/Time-Architecture/fusion-doctor-spectral-sense.md §۶` (fusion_sim + doctor.spectral_mine، fail-soft). → سبز → commit.

**۴ · BOX B0:** پرامپت = بلاکِ زیر (هستهٔ عددیِ آفلاین + هندسه). → سبز → commit.
```
B0 از Box-of-Agents دکتر: هستهٔ عددیِ آفلاین با ساختارِ هندسی. بخوان: DOCTOR-BOX-OF-AGENTS-SPEC.md (Part 0..11) + _ops/doctor/doctor.py. بساز زیرِ _ops/doctor/box/: agent_state (Part 10) + دینامیک x/z/M/G (Part 5) + Warden (سقفِ ۲٪ fail-closed + STOP) + توپولوژیِ درخت+small-world (full-mesh ممنوع، O(N log N)) + حافظهٔ مرزیِ زیرخطی (MERA-coarse-grain) + primitiveِ بازگشتیِ Proposer→Skeptic→Integrator + سنسورهای rho_jacobian و mutual_info I(a;x) + null-Dreamer baseline. خطِ قرمز: بدونِ LLM/شبکه، بدونِ نوشتن بیرونِ _ops/doctor/box/، compliance=سیاست‌محور، goal_stack غربال‌شده، λ_persist منفی، هیچ import از *_gate/chrono/money. تست‌ها: ρ(J)<1 · بودجه fail-closed · یال‌ها ~O(N log N) نه O(N²) · حافظه زیرخطی · I(a;x) neural≫null≈0 · contradiction_rate به صفر نرود · STOP فوری · صفر production-touch. خروجیِ خامِ run_all را در OVERNIGHT-LOG بگذار.
```

**۵ · BOX B1 (falsifiability):** طبقِ `DOCTOR-BOX-OF-AGENTS-SPEC.md Part 8·B1` — null-Dreamer control؛ اثباتِ neural Dreamer > chance روی تسکِ seed. تست: neural-ness score و کیفیتِ RFC > baseline. → سبز → commit.

**۶ · BOX B2 (صداهای LLM، کران‌دار):** طبقِ `Part 8·B2` — Dreamer/Skeptic/Integrator به tierِ ارزانِ gateway (glm-coder/deepseek) زیرِ سقفِ per-episodeِ Warden؛ روی رسیدن به بودجه → degrade به numeric-only. تست: هرگز از ۲٪ عبور نکند؛ STOP فوری. → سبز → commit.
> ⚑ اگر gateway/کلید در دسترس نبود → این آیتم را skip کن، ⚑ در LOG بنویس، برو B3 (بقیه offline اجرا می‌شود).

**۷ · BOX B3 (اتصال به دکتر):** طبقِ `Part 8·B3` — خروجیِ جعبه → doctor.submit_for_approval (propose-only). تست: صفر production-touch؛ هیچ merge بدونِ human-append. → سبز → commit.

**۸ · BOX B4 (کوپلینگِ fusion، اختیاری):** طبقِ `Part 8·B4` — φ_t (A=−L(G)) به‌عنوانِ میدانِ مشترک به Dreamer novelty؛ ablationِ on/off. → سبز → commit.

**۹ · DEBUG PASS نهایی:** پرامپت = `GO-LIVE-PACK.md §۷`. کلِ حلقهٔ زنده + جعبه + دکتر را عیب‌یابی کن؛ جدولِ «باگ·ریشه·فیکس·فایل:خط» در OVERNIGHT-LOG. هیچ فیکسی بدونِ verdictِ مالک apply نشود.

## پایانِ صف
وقتی همه سبز شد یا روی اولین قرمز ایستاد → یک خلاصهٔ ۱۰خطی در بالای `00 - Inbox/OVERNIGHT-LOG.md` بنویس: چه سبز شد، کجا ایستاد، ⚑ها برای معمار، کارهای فقط‌مالک.

---

## کارهای صبحِ تو (مالک — GLM این‌ها را نمی‌تواند)
1. مرورِ `OVERNIGHT-LOG.md` + دیف‌ها؛ هر ⚑ را با معمار (Claude) چک کن.
2. باتِ تلگرام: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID` در `.env` (`GO-LIVE-PACK §۴.۱`).
3. Scheduled Task: watchdog ۵دقیقه + germline ساعتی (`§۴.۲`).
4. off-site backup credential (`§۴.۳`).
5. اجرای ۲۴ساعتهٔ smoke (`§۵`) → اولین لیدِ paperِ Lead-نقاشی (`§۶`).
6. P6 (پول) دست نزن — قفل تا ۲۱-۰۷ + پرچمِ تو.
