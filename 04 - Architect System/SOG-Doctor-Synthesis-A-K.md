---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [sog, doctor, information-theory, synthesis]
created: 2026-07-10
updated: 2026-07-10
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# گزارش سنتز نهایی — SOG Theory → Evolutionary Doctor

سند مرجعِ یک‌جا برای Architect Agent. هر آیتم major با اشاره‌گرِ شواهد (`file:locator`) و تگ `canonical | draft | conflicting | obsolete | unknown`. تناقض‌ها پنهان نشده‌اند (بخش F). هرجا داده قطعی نبود، صراحتاً `unknown` نوشته شده.

---

## A. Intent — نیت و هدف (با نمایش variantها، بدون ادغام خاموش)

هدفِ محوری چند بار و از چند منبع بیان شده؛ variantها را جدا نگه می‌داریم چون در register و دامنه فرق دارند.

- **A1 [canonical] — نیتِ حاکم (truth-rule پروژه):** تبدیل استعارهٔ شاعرانهٔ «هرچه می‌بینیم سایهٔ یک بُعد بالاتر است» به یک دستگاهِ *کمّی، ابطال‌پذیر، information-theoretic*؛ هر ادعای متافیزیکی باید به زبان مهندسی/نظریهٔ اطلاعات بازنویسی شود. — `12121212.txt:28,53-55,917-927`
- **A2 [canonical] — variantِ «سه‌کمیتی» (docx/bardasht):** همان نیت، اما با تصریح سه کمیت مرکزی `E_shadow, Delta_self, I_pred` و بازنشستنِ نسخهٔ «۶-خروجیِ شاعرانه» به‌نفعِ backboneِ ۵-اصلیِ ابطال‌پذیر؛ مالک خود می‌گوید «نقدها عمدتاً وارد است». — `sayehha-docx.txt §0:12-17`, `bardasht.md:1,351-361`
- **A3 [canonical] — نیتِ مالک/ارکستریتور (پل به ارگانیسم):** کل corpus «برای **دکترِ تکاملی**» است — تئوری‌ای که قرار است پژوهشگرِ خودمختارِ چندایجنتیِ آیندهٔ داخل ارگانیسم `F:\backup` را تغذیه کند. **توجه:** خودِ فایل txt هرگز نامِ Doctor واقعیِ vault را نمی‌برد؛ این انتساب از briefِ مالک است، نه از متن. — `Orchestrator/owner brief (task context)`
- **A4 [canonical] — نیتِ عملیاتیِ Doctor (مکملِ A3، از سمت کد/بلوپرینت):** یک «انگلِ propose-only» روی سرِ ارگانیسم که همیشه رصد می‌کند و RFC پیشنهاد می‌دهد اما **ساختاراً ناتوان** از تغییرِ production بدون تأییدِ انسانیِ Telegram است؛ «نرخ تکامل = نرخ حضور انسان». — `P2-DOCTOR.md:13-16,27-28`, `_ops/doctor/doctor.py:2-27`

> **آشتیِ variantها:** A1/A2 «چه چیزی را باید ساخت» (دستگاهِ اندازه‌گیریِ SOG) را تعریف می‌کنند؛ A3/A4 «کجا و برای که» (Doctorِ خودمختارِ ارگانیسم). این‌ها هم‌جهت‌اند نه متناقض — اما پلِ بینشان (SOG-math ↔ کدِ Doctor) هنوز ساخته نشده (بخش D/F).

---

## B. Scope و نقشهٔ شواهد

چهار خوشهٔ شواهد، از readerهای موازی:

| خوشه | منبع اصلی | ماهیت | tagِ غالب |
|---|---|---|---|
| SOG corpus + Doctor | `12121212.txt` + `_ops/doctor` | تئوری Phase 1-5 + کدِ پیاده | canonical تئوری / mixed کد |
| Multi-agent handoff | `SOG-multiagent-handoff.md` + `... 2.md` | brief اجراییِ ارکستریتور-worker | canonical + یک §11 حاکم |
| 4d corpus | `bardasht.md` + `sayehha-docx.txt` + `4.py` | ریاضیِ Stage-A/B + مرجعِ اجرایی | canonical math / errata |
| Doctor implementation | `_ops/doctor/*.py`, `_ops/held_out_evaluator.py`, `_ops/debate/*` | کدِ زندهٔ ارگانیسم | canonical + flag-gated stubs |

**قلمروی منفی:** مطابق قانون اساسیِ vault، `_Archive`/`_Duplicates` باز نشده؛ هیچ secret نقل نشده. فایل‌های مرجعِ spec (`DOCTOR-BLUEPRINT-v1.md`، `ORGANISM-SPEC.md`) و **SOG-Research-Ledger** در دامنهٔ readerها نبودند → `unknown` در بخش G.

---

## C. Math Core — فرمول‌های هسته (با خط منبع؛ cross-checked-by-4.py = canonical)

**Operating point [canonical]:** `ρ=0.5, λ=0.5, σ_ε=0.1, σ_ζ=0.05, σ_d=0.1` (یعنی `se²=0.01, sz²=0.0025, sd²=0.01`). همهٔ اعداد زیر در همین نقطه‌اند. — `12121212.txt:10`, `4.py:27-28,69-71`

**مدلِ مرجع [canonical]:** `s_{t+1}=ρ·s_t+m_t+ζ_t` (بُعد پنهان)، `Y_t=b_t+λ·s_t+ε_t` (سایهٔ مشاهده‌شده). — `4.py:25-30`, `sayehha-docx.txt §2:25-26`

**سه‌طبقهٔ floor [canonical]:** `σ_z²≈0.014167` (null/iid) ⊃ `S_b≈0.013815` (blind/dynamicist) ⊃ `S≈0.010813` (informed/self-aware, حاصلِ DARE). — `12121212.txt:13-14,75-77`, `sayehha-docx.txt §2:34-44`

| فرمول | مقدار | منبع | tag / cross-check |
|---|---|---|---|
| `Δ_self = ½·log(S_b/S)` | `0.122520` nat/step | `12121212.txt:15-16,85`; `4.py:29-34` (متغیر D) | **canonical** — 4.py محاسبه می‌کند |
| `E_shadow = ½·log(σ_z²/S_b)` | `0.012553` nat/step | `sayehha-docx.txt §3.1:48-49`; `bardasht.md:577,583` | **draft/conflicting** — 4.py آن را **نمی‌سازد**؛ منبعش `shadow-algebra` (دیده‌نشده) |
| chain rule: `½·log(σ_z²/S) = E_shadow+Δ_self` | `0.135073` (=0.012553+0.122520) | `12121212.txt:23-24,91-93`; `sayehha-docx.txt §4:59-61` | **canonical (identity) — اما NOT fully 4.py-backed** — جزءِ `E_shadow` و `σ_z²`ش از shadow-algebraِ دیده‌نشده می‌آید (بالا)؛ تا G0 draft بماند |
| `Var(excess)=1−S/S_b` | `0.217327`؛ effective `v_inf=0.208232` | `12121212.txt:17`; `4.py:42-47` | **canonical** — 4.py می‌سازد |
| سقفِ `Δ_self` وقتی `λ→∞`: `½ln(1+σ_d²/σ_ζ²)` | `0.804719` nat | `4.py:60`; `sayehha-docx.txt §3.2:52` | **canonical** — 4.py چاپ می‌کند |
| نسبت `Δ_self/E_shadow` | `9.76×` (در prose رند به `~10×`) | `12121212.txt:25,100`; `sayehha-docx.txt §7:138` | **canonical عدد / draft رندشده** (بخش F) |
| `I_pred` (excess entropy، Riccati recursion) | value مورد اختلاف: `0.014422` vs `0.0144179` (code) vs `0.01443` (rejected) | `bardasht.md:451,619`; `sayehha-docx.txt:185` | **conflicting** — hard-anchor نکن؛ در G0.5 قفل شود |
| Stage-A anchor (m_rail policy) | `E≈6.29` (=6.2917 در λ=1.25) | `bardasht.md §6a:642-667` | **canonical (ledger-verified) — با caveat status:** منبعِ نهایی SOG-Research-Ledger است (بیرونِ دامنهٔ reader)؛ status §6a در bardasht بین «stub» و «closed» نوسان دارد → G10. 4.py فقط خطِ N-budget را cross-check می‌کند |
| Stage-A N-budget cross-check | `(0.5+2·0.0104)(3/0.0104)² ≈ 43,336` | `4.py:52`; `handoff.md App-B:325` | **canonical** |

**قاعدهٔ اثباتِ 4.py [canonical]:** DARE بسته در برابرِ fixed-point iteration روی ۳۰۰ draw تصادفی (`seed=7`) اعتبارسنجی شده؛ Monte-Carlo دوم (`seed=123, T=1.2e6, burn=4000`) `Var(ν)~S`, `Var(ν_b)~S_b`, `mean(excess)~Δ_self` را تأیید می‌کند. **توجه:** 4.py هیچ‌جا `E_shadow` یا `I_pred` را نمی‌سازد. — `4.py:4-24,62-108`

**قضیهٔ identifiability [canonical]:** `E_shadow>0 ⇔ λ·ρ≠0` (و `σ_ζ'²>0`)؛ دو حالتِ «هست ولی نامرئی»: `ρ=0` یا `λ=0` هر دو `E_shadow=0` دقیق. تجسمِ عددیِ تمایزِ `β_info≠β_det`. — `sayehha-docx.txt §5:63-67`, `bardasht.md:585`

**Bug #16 fix [canonical]:** فرمولِ N از Stage-A به Stage-B با توزیعِ غلط منتقل شده بود (noncentral χ² به‌جای paired variance-ratio)؛ اصلاح: `N=Var_eff·(z/τ)²` با `Var=1−S/S_b`؛ واحد و τ pre-register شوند. — `handoff.md §5:146, §4.2:112-119`

---

## D. Existing Architecture — نگاشتِ مفاهیم SOG به کدِ _ops/doctor (present vs absent)

| مفهوم SOG | وضعیت در کد | file:function | tag |
|---|---|---|---|
| Human-Approval-Checkpoint / propose-only | **حاضر و load-bearing** | `doctor.py:517-625 run_cycle`, `430 submit_for_approval` | canonical |
| «no self-preservation» (`λ_persist<0`) | **حاضر**، ثابتِ single-source | `doctor.py:186-187 LAMBDA_PERSIST=-1.0` (import در chamber/evolution/spectral) | canonical |
| Provenance (hash + ledger) | **حاضر** | `doctor.py:150-158 RFC.__post_init__`, `219-227 _note` | canonical/reusable |
| Null-Model baseline | **حاضر در سطح Box** | `box/null_dreamer.py:20-39`, `box/falsif_harness.py:68-122`, `box/sensors.py:66-87 mutual_info` | canonical |
| Informed/blind evaluator (held-out) | **حاضر** (۳ لایهٔ read-only + anti-hacking flag) | `_ops/held_out_evaluator.py:27-33,169-217` | canonical/reusable |
| Blind evaluator (black-box separation) | **جزئی** — در debate هست؛ Criticِ خودِ Doctor **stub قطعی، نه LLM** | `debate/debate_loop.py:11-12` (بله) vs `doctor.py:402-427 _critic_review` (stub) | draft |
| Counterfactual ablation | **جزئی/offline** — on/off روی synthetic seed | `box/b4_fusion.py:103-115 run_ablation`, `box/falsif_harness.py:97-101` | draft |
| Censoring (نه drop) | **حاضر، ۳ لایه** (input sanitize / forbidden-goal / reward-keyword) | `debate/topics.py:22-45`, `box/agent_state.py:12-27,63-68`, `doctor.py:338-341` | canonical |
| stable_read gate (stale↔corrupt) | **حاضر** — verdict∈{stable,stale,corrupt,needs_source_verify,missing} | `doctor.py:55-127` | canonical |
| Warden / 2% cap / STOP kill-switch / `ρ(J)<1` | **حاضر** | `box/warden.py:23-99`, `_stop_file:13-17` | canonical/reusable |
| **Delta-self reflection gate** | **غایب** — نزدیک‌ترین: attention-budget calibration؛ هیچ‌کدام reflection روی state-changeهای قبلیِ خودِ Doctor نیست | `calibration.py:83-126` (تنها آنالوگ) | **codegap / unknown** |
| **Shadow probe روی ترافیک واقعی** | **غایب** — Box یک sandboxِ بسته است نه سایهٔ production؛ «governor سایه» فقط topic است | `box/box.py:30-34`, `debate/topics.py:34` | **codegap / unknown** |
| **v0 Public/Private schema + blind/informed loss harness** | **غایب** — Doctor.mine() از OPS metrics (`errors_24h, effects_pending, frozen, σ_effective`) استخراج می‌کند، نه از blind-vs-informed loss | `doctor.py:230-316` vs `12121212.txt:572-644` | **codegap (بخش F)** |
| **E_shadow/Δ_self estimator با CI بر حسب task-class** | **غایب** — قلبِ کمّیِ SOG در کد ساخته‌نشده | `12121212.txt:202-211,632-644` vs `doctor.py` | **codegap** |
| MAP-Elites archive / Elo tournament (evolution) | **حاضر، flag-gated** | `evolution.py:37-115,160-207` (behind `OCTOPUS_WIRE_EVOLUTION`) | draft |
| Spectral criticality sensor | **حاضر، flag-gated، advisory read-only** | `spectral.py:38-136` (behind `OCTOPUS_WIRE_SPECTRAL`) | draft |

**flag policy [canonical]:** همهٔ مسیرهای پیشرفته (Box, evolution, spectral, chamber-T) پشتِ `OCTOPUS_WIRE_*` و default OFF؛ Chamber خودش default روشن اما temperatureش flag-gated؛ همه fail-soft. — `doctor.py:558-618`

---

## E. مفاهیم / backboneِ نظری (grammarِ قابل‌استفاده)

- **E1 [canonical] — تز استراتژیک:** ارزش SOG ادعای consciousness نیست، «engineering grammar» است: `public trace ≠ private state ≠ self-access ≠ trustworthy introspection`. — `12121212.txt:915-927`
- **E2 [canonical] — decomposition عملیاتی:** سیستمِ hidden-state با `H_t` (hidden)، `D_t` (private dither)، `Y_t` (public trace) و سه رژیمِ پیش‌بینی `L_0/L_b/L_i`؛ `E_shadow≈L_0−L_b`، `Δ_self≈L_b−L_i`. — `12121212.txt:104-138`
- **E3 [canonical] — ۵ اصلِ فلسفی (frozen، در هر دو corpus یکسان):** (1) Identification (بدون null-model هیچ ادعا)، (2) Channel/DPI (کانالِ ثابت اطلاعات اضافه نمی‌کند؛ فقط کانالِ نو)، (3) Levels/Dennett (سطحِ «واقعی» = فشرده/پایدار/پیش‌بین)، (4) Self-reference/Lawvere (فقط نقطه‌کورِ صوری، نه تعالی)، (5) Analogical (AI آزمایشگاهِ قوانینِ شرطیِ `S⇒L`). — `12121212.txt:30-35,59-100`, `bardasht.md:355-361`
- **E4 [canonical] — introspection reliability gate:** scratchpad فقط وقتی «private state» است که (۱) از blind پنهان، (۲) علّی روی output، (۳) ablation قابل‌پیش‌بینی عملکرد را تغییر دهد؛ `Δ_self>0` = دروازهٔ اعتماد. — `12121212.txt:408-412,1018-1027`
- **E5 [draft] — self-hypnosis بازتعریف‌شده:** «prompt-induced mode stabilization» (کاهش واریانسِ seed/tool-entropy)؛ خوانشِ qualia صراحتاً ممنوع. — `12121212.txt:485-517`
- **E6 [draft] — SDE «Leaky Holographic Octopus»:** `dΨ=−L_G·Ψ·dt+B(Ψ)·dW+U·dt`؛ مالک «holographic» را چون lossy است downgrade کرد؛ illustrative، fit-نشده. — `bardasht.md:298-347`
- **E7 [canonical] — واژگانِ طراحی:** ۱۳ engineering primitive، ۱۳ ایدهٔ معماری، ۱۴ الگوی MAS، ۱۴ فرضیهٔ pre-registration-ready با falsifier — همه مستقیماً reusable (بخش H). — `12121212.txt:156-367,524-561`

---

## F. Contradictions — تنش‌های واقعی (هر دو طرف + منبع؛ هیچ‌کدام پنهان نشده)

**F1 [conflicting] — variance-ratio vs log-loss (operational form).**
طرف الف: در Stage-B، فرمِ variance-ratioِ `E_shadow/Δ_self` تحلیلی و MC-تأییدشده است. طرف ب: خودِ سند هشدار می‌دهد این فرم فقط اگر فرضِ Gaussian واقعاً برقرار باشد معتبر است؛ در سیستم‌های LLM نسخهٔ امنِ عملیاتی، اختلافِ cross-entropy/log-loss است. — `12121212.txt:150`. **پیامد:** انتقال به Doctor باید log-loss-based باشد نه variance-based.

**F2 [conflicting] — theory metric vs code metric (v0 measurement-first vs OPS-mining).**
طرف الف (تئوری): v0 «measurement-first» — تخمینِ `L_0/L_b/L_i, E_shadow, Δ_self` با harnessِ blind/informed. طرف ب (کد): `Doctor.mine()` bottleneck را از metrics ارگانیسم (`errors_24h, effects_pending, frozen, σ_effective`) می‌گیرد، هرگز از blind-vs-informed loss. **هستهٔ تخمینِ SOG در Doctorِ زنده غایب است.** — `12121212.txt:568-644` vs `doctor.py:230-316`.

**F3 [conflicting] — دو فایلِ handoff.**
هر دو فایل برای خطوط 1-329 byte-identical‌اند؛ تفاوتِ *واحد* افزودنِ §11 (خطوط 330-352) در فایل ۲ است — نه تعارضِ مقداری. §11 «rulingِ نهاییِ 2026-07-10» صراحتاً **بر §10 حاکم** است و HOLD می‌گذارد: هیچ dispatch (حتی W0) پیش از (۰) merge کاملِ ledger و (۰.۵) بازخوانیِ unit-coherence. **توجه:** خودِ §11 سه «Open PI decision point» را هم unresolved اعلام می‌کند (G11) و ترتیبِ درونیِ Stage-A را با marker «[resource-priority]» می‌گذارد نه hard-serial. — `SOG-multiagent-handoff 2.md §11:333-336`.
**زیرتنش [obsolete]:** §10 «Next steps» (در هر دو فایل یکسان) به Builder می‌گوید W0 را قدم ۳ اجرا کن، بدون HOLD؛ خواننده‌ای که فقط فایل ۱ را ببیند W0 را زودهنگام dispatch می‌کند. §10 توسط §11 override شده. — `handoff.md §10:282-287` superseded by `... 2.md §11:335-336`.

**F4 [conflicting] — owner-interpretation vs rigorous doc.**
طرف الف (مالک): docx را «نسخهٔ شاعرانه/روایتیِ قدیمی که باید جایگزین شود» برچسب می‌زند. طرف ب (خودِ docx): تاریخِ `2026-07-10` (همان روزِ bardasht)، کاملاً code-generated، backboneِ ۵-اصلیِ rigorous را از پیش یکپارچه کرده و «shadows» را صراحتاً روایتی با هستهٔ ابطال‌پذیرِ محدود به Track-G معرفی می‌کند. **docx یک post-critique synthesis است، نه مبدأِ شاعرانه.** فرضِ FOCUS اشتباه است. — `bardasht.md:1` vs `sayehha-docx.txt:5-6,184-189`.

**F5 [conflicting] — poetic vs falsifiable framing (هم‌زیستِ عمدی).**
corpus هم‌زمان قاب‌های شاعرانه/متافیزیکی («سایهٔ بُعد بالاتر»، «حسِ تعالی») را نگه می‌دارد و مکرراً به‌عنوانِ ادعای فنی *ممنوع* می‌کند. این دو register باید bracket شوند نه silently merge. — `12121212.txt:34,86,100,515-517`.

**F6 [conflicting] — SOG theory vs Doctorِ کم‌عمقِ rule-based کنونی.**
تئوری یک دستگاهِ اطلاعاتیِ blind/informed می‌خواهد؛ Doctorِ زنده Criticِ deterministic (keyword/length)، judgeِ stub و lift مبتنی‌بر severity دارد. علاوه‌براین **verifier-independence نقض‌پذیر است:** `_default_eval` در evolution، lift را از `rfc['evidence']['severity']` می‌گیرد که خودِ `mine()`ِ Doctor تولید کرده؛ استقلال فقط وقتی برقرار است که `eval_fn` بیرونی inject شود. — `evolution.py:143-153` vs claim در `doctor.py:750-756`.

**F7 [conflicting] — دو تعریفِ متفاوتِ σ (spectral).**
`spectral.py` از Laplacian `L=D−A` استفاده می‌کند؛ `b4_fusion.py` از `A=−L(G)`. عددی هم‌خوان نیستند و هیچ فایلی canonical را مشخص نمی‌کند. **این σ (criticalityِ event-graph) با σ_z²/σ_d در SOG یکی نیست — conflate نشود.** — `spectral.py:58-71` vs `b4_fusion.py:47,61-72`.

**F8 [obsolete] — spec «no code» vs کدِ موجود.**
`DOCTOR-BOX-OF-AGENTS-SPEC.md` خود را «spec + roadmap only; no code yet / draft-for-verdict» اعلام می‌کند، اما Box کاملاً در `_ops/doctor/box/` (۱۲ ماژول) پیاده شده. framingِ «no code» stale است. مشابهاً `P2-DOCTOR.md §2` هنوز به `genome-system/agents/doctor.py (restart-only today)` اشاره می‌کند حال‌آنکه Doctorِ production به `_ops/doctor/doctor.py` منتقل شده. — `SPEC:14` vs dir listing؛ `P2-DOCTOR.md:22-24`.

**F9 [conflicting/errata، resolved] — driftهای ~10⁻⁵ در symbolic checks.**
`union 0.135041` (غلطِ حسابی؛ درستش `0.135073`)؛ `constraint-12 gap 0.13882 vs 0.138837`؛ swapِ حدود `λ=0/ρ=0`. همه resolved اما «سومین بار که symbolic check خطای حسابی داشت» — ریسکِ calibration برای هر Doctorِ خودمختارِ symbolic. — `bardasht.md:442-443,549,615,618`.

**F10 [draft] — 9.76× vs ~10×.** عددِ دقیق `9.76` است ولی نتیجه‌گیریِ prose «حدود ۱۰ برابر» را حمل می‌کند. جزئی اما وارد conclusions شده. — `12121212.txt:25,100`.

---

## G. Open Questions / Unknowns / Pre-registration (ترجیحِ «unknown» صریح)

- **G1 [unknown] — `SOG(κ,d)`:** متریکِ تعیین‌کنندهٔ ابطالِ self-reference/transcendence؛ conceptually تعریف شده (`err_inf^self − err_inf^other`) اما **هرگز عددی تعریف/محاسبه/تست نشده** در هیچ‌یک از سه فایل. — `12121212.txt:34,86`, `bardasht.md:205-229`.
- **G2 [unknown] — Stage-A MC convention:** جداسازیِ «Mean-Table Gate» (نمونه فقط روی b) از «Variance Diagnostic» (شاملِ floor noise) قفل‌نشده؛ سه convention (mean-table/analytic-floor/paired-oracle) واریانس‌های متفاوت می‌دهند. red-line پیش از هر run. — `12121212.txt:42`, `bardasht.md:686-729`.
- **G3 [unknown] — پارامترهای معلق:** `τ`-convention (absolute vs relative؛ `τ_A≈0.01` هنوز pin نشده)، objectiveِ dither `J(σ_d;λ)` برای W1، burn-in budget. `J` مالکِ انسانی است، بهینه‌سازیِ عددی W1. — `12121212.txt:43`, `handoff.md §5:147`, `bardasht.md:781-800`.
- **G4 [unknown] — `I_pred` value:** بین `0.014422/0.0144179/0.01443` مورد اختلاف؛ در G0.5 با کدِ canonical قفل شود، hard-anchor نکن. — `bardasht.md:451,619`.
- **G5 [unknown] — «۳ بازتولیدِ مستقل»:** وضعیت فعلی 2/3؛ W0 بازتولیدِ سوم است و استقلالش با ندادنِ کدِ مرجع (`4.py`/`stageB_verify.py`) و seedِ خودانتخاب تضمین می‌شود. E_shadow G0 reproduction هنوز pending (§6d در 2/3). — `handoff.md §1:29,§7.6:223-226`, `bardasht.md:511`.
- **G6 [unknown] — subjective self-state:** آیا mode-stabilization به هر self-stateِ سابجکتیو نظیر دارد → صراحتاً «بیرونِ ادعای مهندسی/unknown». — `12121212.txt:503-505`.
- **G7 [unknown] — doc↔code sync:** آیا `DOCTOR-BLUEPRINT-v1.md` و `ORGANISM-SPEC §2.7` به «implemented» به‌روز شده‌اند تأییدنشده (فایل‌ها در دامنهٔ reader نبودند). — `P2-DOCTOR.md §7:55-56`.
- **G8 [unknown] — constants tuning:** `N_max, ρ_min/ρ_max, L_max, c_min, memory-K`, نگاشتِ `E_total→tokens/CPU` در spec `[OPEN]`؛ warden.py defaults (`0.02/0.98/0.5`) شاید با مقادیرِ tuned نخواند. — `SPEC Part 9:184-188` vs `warden.py:24-30`.
- **G9 [unknown] — Pacemaker attach:** آیا `run_cycle` واقعاً هر N beat در production فراخوانده می‌شود تأییدنشده (`chrono.py/organism.py` خوانده‌نشدند). — `doctor.py:18-19`.
- **G10 [unknown] — §6a documentation-status oscillation + source-of-truth:** status §6a در `bardasht.md` بین «stub — awaiting paste» (خط 508) و «closed, stub removed» (خط 630) نوسان می‌کند؛ منبعِ authoritative صراحتاً **SOG-Research-Ledger** اعلام شده، نه این فایل‌ها (بیرونِ دامنهٔ reader). پس consolidation در-فایلیِ anchorِ `6.29` نباید به‌عنوان «کاملاً settled» بیش‌ادعا شود تا ledger دیده شود. — `bardasht.md:508,630`.
- **G11 [unknown] — سه تصمیمِ PI بازِ §11 (handoff-2):** طبق «Open PI decision points remain unresolved at handoff» هنوز حل‌نشده‌اند: (الف) تأییدِ اتمامِ full-merge ledger؛ (ب) مسیرِ splice §6د؛ (ج) تفسیرِ «Stage-A coding ≻ sweep» به‌عنوان resource-priority (توصیه‌شده) در برابر hard-serial. خودِ claimِ ترتیب marker «[resource-priority]» دارد نه hard gate → ترتیبِ J تا حلِ (ج) الزام‌آور نیست. — `SOG-multiagent-handoff 2.md §11:333-336`.

---

## H. Reusable Assets — دارایی‌های آمادهٔ استفادهٔ مجدد

**H-تئوری (formula/primitive):**
- **H1 [canonical]** `4.py` — پیاده‌سازیِ خودبسندهٔ numpy: DARE closed-form، فیلترهای informed/blind Kalman، paired-excess variance، MC ‏`T=1.2e6`. بدون network، دو seed (7,123). **بلوکِ `E_shadow/I_pred` («shadow-algebra») غایب است — 4.py آن‌ها را نمی‌سازد.** — `4.py (کل فایل)`.
- **H2 [canonical]** Rosetta table (term↔math↔literature)، backboneِ ۵-اصلی، testbedِ `β_info/β_det`، bibliographyِ lit-pass (Radon/Helgason, Diaconis-Freedman 1984, Takens, Bialek-Nemenman-Tishby 2001, Crutchfield). — `bardasht.md:355-361,419-420`.
- **H3 [canonical]** جدولِ ۱۳ primitive + ۱۳ ایده + ۱۴ الگوی MAS + ۱۴ فرضیهٔ falsifier-دار + نقشهٔ v0→v1→v2 با schemaِ ~۱۸-fieldِ logging. — `12121212.txt:156-367,524-561,565-732`.
- **H4 [canonical]** production decision-rule: MAS فقط اگر `Δquality > coordination+verification+latency cost`؛ single-agent وقتی task در یک context جا شود یا `Δ̂_self≈0`. — `12121212.txt:736-753`.

**H-کد (ماژول‌های زندهٔ آماده wiring):**
- **H5 [canonical/reusable]** `held_out_evaluator` — ۳ لایهٔ مستقلِ read-only + `anti_hacking_flag`؛ growth-system نمی‌تواند در آن بنویسد. آنالوگِ مستقیمِ informed/blind evaluator. — `_ops/held_out_evaluator.py:27-217`.
- **H6 [canonical/reusable]** `box/` numeric core — Warden (2% fail-closed + STOP)، `sensors.mutual_info/rho_jacobian`، `null_dreamer` + `falsif_harness`، `topology` tree+shortcut، `primitive` بازگشتی. — `_ops/doctor/box/*`.
- **H7 [canonical/reusable]** `debate/` — black-box muse×architect (≤3 round)، `client.py` gated LLM transport (leak-guards: allow-list host, price-lock, telemetry-error). وقتی Critic/Chamber از stub به LLM بروند، این transport استفاده شود. — `debate/debate_loop.py`, `debate/client.py:30-315`.
- **H8 [canonical/reusable]** `RFC` dataclass (schemaِ کاملِ propose-event + `to_markdown` برای P3 card) و `review_bus` (قراردادِ human-gated phase-gate: `verify_handoff/handoff_ready`). — `doctor.py:133-180`, `review_bus.py:21-197`.
- **H9 [canonical]** primitiveهای censoring (۳ لایه)، `stable_read` gate، `calibration` attention-budget، `evolution` MAP-Elites+Elo، `temperature` controller — همه stdlib-only، $0، additive، fail-soft. — `_ops/doctor/*`.

---

## I. Risks — ریسک‌ها

- **I1 [canonical] — ۵ اشتباهِ خطرناک:** (۱) scratchpad = introspection معتبر؛ (۲) rationale عمومی = محاسبهٔ درونی؛ (۳) promptِ تزئینی = کانالِ کنترلِ واقعی؛ (۴) شفافیت همیشه خوب (شادو-leak رازها را لو می‌دهد)؛ (۵) MAS همیشه بهتر از single-agent. — `12121212.txt:870-885`.
- **I2 [canonical] — informed می‌تواند بیشتر biased از blind باشد (H9)** وقتی rationale متقاعدکننده‌اما‌غلط است؛ probe-target می‌تواند «compliance theater» کند و tomography را خنثی کند. — `12121212.txt:301-302,553`.
- **I3 [canonical] — driftِ manual-recompute در رژیمِ ~10⁻⁵** قانونِ خودِ corpus («همهٔ nat-values کدساخته») را نقض می‌کند — ریسکِ سیستمیِ calibration برای هر Doctorِ symbolic-checker. — `bardasht.md:611-618`.
- **I4 [draft] — تکرارِ چهارگانهٔ چکِ reward-integrity** (`doctor.propose_rfc`, `_critic_review`, `chamber._red_critic/_synthesizer`, `evolution._default_eval`) با keyword-setهای کمی متفاوت → drift (مثلاً `doctor.py:339` «keep alive» را چک می‌کند، `_critic_review:409` نه). — `doctor.py:339,409; chamber.py:77,116; evolution.py:151`.
- **I5 [draft] — fragilityهای کد:** `calibration.record_verdict` جدولِ `duration_marker` را overload و `rfc_id[:16]` را truncate می‌کند → برخورد/overwrite؛ `b3_bridge` با `sys.path` دستکاری import می‌کند (brittle). — `calibration.py:39-48`, `doctor.py:627-662`.
- **I6 [draft] — UNPROVEN بودنِ سبزها:** greennessِ Chamber/Box فقط «مکانیزم کار می‌کند» را ثابت می‌کند نه کیفیت؛ همه deterministic stub، $0، بدون LLM. `calibration` بدون wiringِ واقعیِ verdict گرسنه است. — `chamber.py:18-20`, `calibration.py:14`.
- **I7 [canonical] — over-claimِ ontology:** انتقالِ متافیزیکی فقط شرطی است (`S⇒L`)؛ ادعای «موجودِ بُعد-بالاتر» به premiseهایی نیاز دارد که معمولاً checkable نیستند. — `sayehha-docx.txt §10:186`.
- **I8 [canonical] — novelty guard:** `Δ_self=½log(S_b/S)` باید در خانوادهٔ Gel'fand–Yaglom / directed-information (Massey) معرفی شود، **نه** کمیتِ نو؛ تنشِ بالقوه با ICML-2025 performative-multicalibration در related-work آدرس شود. — `handoff.md §6:158-164`.
- **I9 [canonical] — merge-blocker جزئی:** PNGِ اسکچِ `739F...png` کاملاً سفید/خالی؛ پیش از merge re-export یا حذف. — `sayehha-docx.txt §10:187`.

---

## J. Roadmap و پیشنهادهای طراحی (حداقلی)

**ترتیبِ اجراییِ پیشنهادی [resource-priority — توصیه‌شده، نه hard gate]** (§11، فایل ۲): (۰) merge کاملِ ledger ≻ (۰.۵) بازخوانیِ unit-coherence ≻ **Stage-A coding** ≻ Stage-B sweep (W0) ≻ lit-pass ≻ Track-G (W4، conditional). **توجه:** خودِ §11 این ترتیبِ درونی را با marker «[resource-priority]» (توصیه) ثبت کرده نه hard-serial؛ تفسیرِ «Stage-A coding ≻ sweep» به‌عنوان resource-priority در برابر serialِ سخت هنوز از «Open PI decision points» باز است (G11). پس Stage-A را «دروازهٔ سختِ همه‌چیز» فرض نکن تا این تصمیم حل شود؛ Track-G همچنان آخرین و کم‌اولویت‌ترین. — `... 2.md §11:335`, `bardasht.md:591-597`.

**دو گیتِ مجزا [canonical]:** (الف) W0-PASS دروازهٔ W1/W3؛ (ب) Stage-A-run دروازهٔ هر آزمایشِ learner-in-loop. (این دو گیتِ اجرا از handoff §7.3 مستقل از ترتیبِ resource-priorityِ بالا هستند.) — `handoff.md §7.3:209-210`.

پیشنهادهای طراحیِ حداقلی (فقط جایی که شواهد صراحتاً «بساز»):
1. **v0 measurement-first را اول بساز، بعد به `Doctor.mine()` سیم بکش** — جایگزین/مکملِ OPS-metric mining با تخمینِ blind/informed SOG (F2/F6). — `handoff.md:565-644` + `doctor.py`.
2. **دو codegapِ روشن:** delta-self reflection gate و shadow-probe (بخش D).
3. **ارتقای روشن:** جایگزینیِ Critic/judge/eval stub با gated LLM client (H7) — با حفظِ verifier-independence از راهِ inject کردنِ `eval_fn` بیرونی (رفعِ F6).
4. **operational form برای LLM = log-loss diff، نه variance-ratio** (F1).

---

## K. Handoff Brief — برای Architect Agent (settled vs must-decide-first)

**settled (canonical، دست‌نخوردنی — ریل‌های غیرقابل‌مذاکره):**
- propose-only + sandbox-only + human-append merge (Telegram) — `doctor.py:21-27`.
- `λ_persist<0` (بدون پاداشِ بقا)؛ Warden hard 2% cap؛ اطاعتِ بی‌قیدِ STOP؛ verifier-independence (Doctor هرگز scoring خودش را ویرایش نمی‌کند)؛ `ρ(J)<1`. — `warden.py`, `evolution.py:750-756`.
- **هستهٔ ریاضیِ Stage-B که مستقیماً 4.py-backed است:** `Δ_self=0.122520`, `Var(ex)=0.217327`, operating-point، سقفِ `λ→∞`=`0.804719` (بخش C). **⚠ chain-rule identity `0.135073` را جزوِ «4.py-backed» نشمار:** identity الجبری درست است، اما جزءِ `E_shadow=0.012553` و `σ_z²`ش از اسکریپتِ دیده‌نشدهٔ shadow-algebra می‌آید نه 4.py — پس تا بازتولیدِ مستقلِ G0 در وضعیتِ draft می‌ماند (هماهنگ با بخش C؛ رفعِ تناقضِ قبلیِ K↔C).
- backboneِ ۵-اصلی (E3) و grammarِ public/private/self/introspection (E1/E2) پایدارند.
- دارایی‌های کدِ آماده: `4.py`، `held_out_evaluator`، `box/` core، `debate/` + gated client، `RFC`+`review_bus` (بخش H).

**must-decide-first (باید پیش از هر اجرا حل شود):**
- **HOLD §11:** هیچ dispatch (حتی W0) پیش از merge کاملِ ledger + بازخوانیِ unit-coherence (F3).
- **G11 — سه تصمیمِ PI بازِ §11:** (الف) تأییدِ اتمامِ full-merge ledger (پیش‌شرطِ خودِ HOLD)؛ (ب) مسیرِ splice §6د؛ (ج) resource-priority در برابر hard-serial برای «Stage-A coding ≻ sweep». تا حلِ (ج)، ترتیبِ J الزام‌آور نیست.
- **G10 — §6a source-of-truth:** anchorِ `6.29` در bardasht بین «stub» و «closed» نوسان دارد و منبعِ نهاییش SOG-Research-Ledger (بیرونِ دامنه) است؛ consolidation در-فایلی را قطعی فرض نکن تا ledger دیده شود.
- **G2** Stage-A MC convention قفل شود؛ **G3** `τ_A=0.01` pin و `J(σ_d;λ)` توسط مالک تعریف شود؛ **G4** `I_pred` در G0.5 قفل (hard-anchor نکن)؛ **G5** W0 بازتولیدِ مستقلِ سوم با seedِ خودانتخاب.
- **تصمیمِ معماری:** آیا metricِ Doctor از OPS-mining به SOG blind/informed loss مهاجرت می‌کند؟ (F2/F6) — این تکِ actionable-ترین قدم است.
- **رفعِ F6:** eval_fn بیرونیِ مستقل به `evolution` inject شود تا verifier-independence از ادعا به واقعیت برسد.
- **رفعِ F7:** کدام σ (Laplacian `L=D−A` در spectral.py یا `A=−L` در b4_fusion) canonical است.
- **G7/G8/G9:** sync سند↔کد، tuningِ constantها، و تأییدِ Pacemaker attach.
- **E_shadow provenance (C):** بلوکِ «shadow-algebra» که `E_shadow=0.012553` و `σ_z²` را می‌سازد بیرونِ دامنه است → مستقلاً بازتولیدنشدنی تا آن اسکریپت دیده شود (همین چرا chain-rule بالا draft ماند).

**تک‌جملهٔ actionable [canonical]:** «measurement-first v0 (blind/informed loss harness + E_shadow/Δ_self estimator + ablation lab) را بساز، سپس آن را به‌جای/در کنارِ OPS-metric miningِ `Doctor.mine()` سیم بکش — با حفظِ همهٔ ریل‌های settled.» — `handoff.md:565-644,915-936` + `_ops/doctor/doctor.py`.