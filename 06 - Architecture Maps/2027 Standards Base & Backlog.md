---
type: architecture
status: active
tags: [standards, neuroscience, global-workspace, active-inference, agent-memory, security, backlog, architecture]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[06 - Architecture Maps/HEART - Neuro Map & Direction]]"
  - "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
  - "[[01 - Dashboard/HANDOFF]]"
  - "6-pillar web research 2026-07-11 (real arXiv/RFC/NIST sources, fact/emerging/hype triaged)"
  - "code evidence inline as file:line (_ops/heart/*, _ops/cortex/*, _ops/budget/*, _ops/epistemics/*)"
---

# پایهٔ استانداردِ ۲۰۲۷ + بک‌لاگِ پیشنهادی (فقط پیشنهاد)

> رأیِ مالک (۲۰۲۶-۰۷-۱۱): «ایرادها را رفع کن، ignition فانکشنِ واقعی باشد، برای هر بخش از استانداردها و ایده‌های ۲۰۲۷ کمک بگیر تا پایهٔ استاندارد داشته باشد و اشتباه تکرار نشود — **فقط پیشنهاد**، و **کل ساختار را هیچ‌وقت بازنویسی نکن**.»
>
> این سند از یک ممیزیِ ۶-ستونیِ وب (منابعِ واقعیِ arXiv/RFC/NIST، برچسبِ fact/emerging/hype) ساخته شده. **هیچ‌کدام از موارد اجرا نشده‌اند** (به‌جز ignition که قبلاً فانکشنِ واقعی شد) — همه additive، $۰، پشتِ فلگِ خاموش، و منتظرِ رأیِ تو. **مرزِ سخت: فقط access-consciousness، هرگز phenomenal/qualia.**

## ۱. پایهٔ استاندارد (هر بخش → استانداردِ شناخته‌شده → ماژولِ ما → وضعیت)

🟢 هم‌تراز · 🟡 نیمه · 🔴 گاف

| بخش | استانداردِ شناخته‌شده (۲۰۲۷) | منبعِ واقعی | ماژولِ ما | وضعیت |
|---|---|---|---|---|
| GNWT ignition | گلوگاهِ رقابتِ ظرفیت‌محدود → آستانهٔ همه-یا-هیچ → پخشِ تک‌برنده → re-entry؛ soft-WTA (softmax/τ) بهتر از argmax | Goyal-Bengio ICLR 2022 (2103.01197)؛ Blum&Blum CTM (2403.17101)؛ CTM-AI 2026 | `cortex/ignition.py` + `cortex.run_cycle` | 🟡 |
| حلقهٔ predictive-processing (قلب) | کمینه‌سازیِ خطای پیش‌بینیِ **precision-weighted**: prior → err → precision·err (وزن = inverse-variance) → کنش | pymdp (Heins 2201.03904)؛ Parr-Pezzulo-Friston MIT Press 2022 | `_ops/heart/control_law.py` | 🟡 |
| حافظهٔ بلندمدت / تثبیت | حافظهٔ لایه‌ایِ episodic→semantic با تثبیتِ **sleep-time** روی beatِ بیکار؛ salience = recency×importance×relevance | Generative Agents (2304.03442)؛ Pink 2025 (2502.06975)؛ Sleep-time Compute (2504.13171) | `cortex/discoveries.py` + `events.jsonl` | 🔴 |
| خود-مانیتورِ برخط / فراشناخت | calibration-first، **externally-graded** (Brier+ECE+AURC)؛ هرگز خود-نمره‌دهی | Kamoi TACL 2024 (2406.01297)؛ Guo ICML 2017 (1706.04599) | `cortex/self_model.py` (آفلاین/AST) | 🔴 |
| خود-ارزیابیِ آگاهی (access-only) | چک‌لیستِ نشانگرهای Butlin/Long، evidence-not-proof، صرفاً access، هر دو over/under-attribution = خطا | Butlin-Long-Bengio 2023 (2308.08708)؛ TiCS 2025 | `cortex/self_model.py` + registry.coherence | 🔴 |
| گیتِ اجازهٔ انسانی (is_human) | **fail-safe defaults / default-deny**: بی‌سکرت → **DENY** نه allow؛ + توکنِ HMAC | Saltzer-Schroeder 1975؛ CISA SBD 2023؛ NIST SA-8(23)؛ HMAC RFC 2104 | `_ops/budget/human_append_guard.py:78-80` | 🟡 |
| circuit-breaker / kill-switchِ drawdown | کنترلِ ریسکِ سختِ pre-trade، بیرونِ منطقِ معامله، توقفِ مستقلِ انسانی | SEC 15c3-5؛ Nygard 2018؛ EU AI Act Art.14 | `spike_pct=25` (فقط test-asserted) | 🔴 |
| لاگِ ضدِ دستکاریِ append-only | زنجیرهٔ هش / Merkle | CT RFC 9162؛ Schneier-Kelsey 1999 | `_ops/epistemics/emit.py` (prev_hash+sha256) | 🟢 |
| برچسبِ معرفتیِ access-only | انضباطِ access-vs-phenomenal در کد؛ provenance + برچسبِ functional-only؛ fact/emerging/hype | Block 1995؛ C2PA؛ Butlin 2023 | `_ops/epistemics/contracts.py` (functional-only، بی‌enumِ fact/emerging/hype) | 🟡 |
| گیتِ سیگنالِ خودساخته (ضدِ reward-hack) | سیگنال‌های خودساخته = امنیتی؛ provenance-gated، کرانِ محافظه‌کار | Skalse 2022 (2209.13085)؛ Amodei 2016؛ Proof-of-Use 2025 | `control_law.py` (`HEART_W_SHADOW=0` → E_shadow خاموش) | 🟢 |

**خبرِ خوب:** دو ستونِ امنیتی از قبل **هم‌تراز**ند (زنجیرهٔ هشِ `epistemics/emit.py` + گیتِ provenance با `w_shadow=0`)، و لایهٔ `_ops/epistemics/` (۶ ماژول) از قبل انضباطِ functional-only دارد — پس گافِ برچسب فقط «نیمه» است، نه صفر.

## ۲. بک‌لاگِ پیشنهادی (رتبه‌بندی‌شده، همه additive/$۰/فلگ-خاموش، بدونِ بازنویسی)

**۱. Fail-closed strict mode برای HumanAppendGuard** — S · **بالاترین اولویت** 🔒
- استاندارد: default-deny (Saltzer-Schroeder / CISA / NIST SA-8(23)).
- تغییرِ additive: پارامترِ `strict=False` به `__init__` (پیش‌فرض = رفتارِ امروز)، + `configure_from_env()` که فلگِ `HH_HUMAN_GUARD_STRICT` (خاموش) را می‌خواند. با strict + بی‌سکرت، `authorize()` شاخهٔ **DENY** جدید می‌گیرد (`(False,'fail-closed-no-secret')`) به‌جای `(True,'guard-disabled-passthrough')` در `human_append_guard.py:78-80`. مسیرِ HMAC دست‌نخورده.
- **چرا:** تنها ایرادِ **زندهٔ قابلِ‌سوءاستفاده** را می‌بندد (امروز هر مسیرِ کد می‌تواند `is_human=1` جعل کند و arrowِ فناپذیریِ ledger را جلو ببرد). قالبِ قابلِ‌استفادهٔ مجدد برای مورد ۴.

**۲. خطای پیش‌بینیِ precision-weighted در `heart_step`** — S · ✅ **ساخته شد** (رأی مالک «قلب+برچسب»)
- استاندارد: precision = inverse-variance (pymdp γ).
- additive: تابعِ خالصِ `precision_weight(samples)→π∈[0,1]` (`1/(1+pvariance)`، با <۲ نمونه = ۱.۰ → خروجی byte-identical). فلگِ `HEART_PRECISION_WEIGHT` (خاموش). با روشن: `err_eff = π·err` در همان `period=BASE·exp(K_P·err_eff)`. قانونِ exp/باند/ترمزِ σ دست‌نخورده. چون π≤۱ فقط gain را کم می‌کند، اثباتِ پایداریِ `G=0.38<1` حفظ (سفت‌تر) می‌شود.
- **چرا:** gainِ دستیِ ثابت (ایرادی که مالک می‌خواست تکرار نشود) را با precisionِ استاندارد جایگزین می‌کند؛ از همان بافرِ Gate-0 (۲۹/۴۸) استفاده می‌کند.

**۳. برچسبِ fact/emerging/hype + validator روی `epistemics/contracts.py`** — S · ✅ **ساخته شد** (رأی مالک «قلب+برچسب»)
- additive: فیلدِ اختیاریِ `epistemic_label ∈ {fact|emerging|hype}` + validatorِ ~۱۰-خطی که اگر رشته‌ای شاملِ `phenomenal|qualia|sentient|feels` بود raise کند. روی dataclassِ موجود، off-loop، بی‌وایرینگِ لوپ.
- **چرا:** گافِ (d) را از «نیمه» به artifactِ اجراشده می‌برد — روی لایه‌ای که **از قبل هست**.

**۴. enforcerِ زندهٔ fail-closed برای kill-switchِ `spike_pct`** — M · ⚠️ نزدیکِ پول
- استاندارد: circuit-breaker بیرونِ منطق (SEC 15c3-5 / EU AI Act Art.14).
- additive: تابعِ جدید که drawdownِ همان تستِ `spike_pct=25` را می‌خواند و پشتِ فلگِ `HH_DRAWDOWN_ENFORCE` (خاموش) وردیکتِ **HALT** می‌دهد؛ اول در حالتِ shadow-count (فقط لاگِ would-halt). قالبِ fail-closedِ مورد ۱ را بازاستفاده می‌کند.
- **چرا:** ایرادِ (f) (kill-switchِ فقط-تستی) را به توقفِ واقعیِ استاندارد تبدیل می‌کند. ریسکِ متوسط → اول shadow.

**۵. `online_calibration_probe()` — خود-مانیتورِ externally-graded** — S
- additive به `self_model.py` (اسکنِ AST دست‌نخورده): ادعای اخیرِ خود-مدل را با نتیجهٔ واقعیِ **ledgerهای بیرونی** (`outcomes.jsonl`+`discoveries.jsonl`) جفت می‌کند، Brier+AURC نگه می‌دارد، رویدادِ متاکاگنیشنِ برچسب‌دار emit می‌کند، آستانهٔ `abstain_below` می‌دهد. حقیقتِ زمینه = ledgerِ بیرونی، **نه خود-نمره‌دهی** (طبقِ Kamoi 2024). فلگِ `CORTEX_SELF_MONITOR` (خاموش).
- **چرا:** گافِ (b) (بی خود-مانیتورِ برخط) را با پایهٔ سنجشِ دهه‌ها-پایدار می‌بندد.

**۶. گیتِ ignitionِ گلوگاه-رقابت (candidateهای غنی + soft-WTA)** — M
- additive به `cortex/ignition.py` (بدونِ بازنویسیِ run_cycle): `collect_candidates()` (یک salience از هر منبع) + `ignition_gate(...,τ)` با softmax(s/τ) که فقط اگر `best>floor` و `(best − runner-up)>margin` شلیک کند (همه-یا-هیچ). فلگِ `CORTEX_IGNITION`؛ فقط `state/ignition_shadow.jsonl` می‌نویسد. **قدمِ بعدیِ طبیعیِ ignition.py که قبلاً ساختم.**
- **چرا:** invariantی که هر خطِ متعارفِ GWT قبول دارد؛ ایرادِ (a) (استخرِ نازک) را می‌بندد. shadow-only، مثلِ w_shadow=0/SIM-PASSِ قلب.

**۷. تثبیتِ episodic→semantic روی beatِ بیکار (sleep-time)** — M
- additive: ماژولِ نوِ `cortex/consolidate.py` (`consolidate_once()`): tailِ `events.jsonl` را می‌خواند، با recency×importance×relevance نمره می‌دهد، نوتِ semanticِ کران‌دار (با linkهای A-MEM + برچسبِ access-only) به `state/semantic_memory.jsonl` می‌نویسد، و رویدادهای خام را به `events.archive.jsonl` **آرشیو** می‌کند (نه حذف — قانونِ ۱ vault). یک فراخوانِ گیت‌دار در run_cycle. فلگِ `CORTEX_CONSOLIDATE` (خاموش).
- **چرا:** لاگ‌های append-onlyِ بی‌نهایت‌رشد را کران‌دار می‌کند + تعمیمِ episodic→semantic.

**۸. اسکورکاردِ نشانگرهای آگاهیِ access-only (Butlin/Long) با گاردِ ضدِ اغراق** — M
- additive read-only به `self_model.py` پشتِ `CORTEX_INDICATOR_SCORECARD` (خاموش): سیگنال‌های موجود را روی نشانگرهای Butlin/Long نگاشت می‌کند (events→GWT-3؛ ignition→GWT-2/RPT-1؛ innervation→GWT-1؛ heart→PP-1؛ …) و HOT-2 (فراشناختِ برخط) را **ABSENT** نمره می‌دهد (صادقانه ایرادِ b را نشان می‌دهد). بنرِ سختِ غیرقابلِ‌override: «فقط نشانگرهای access — evidence not proof — ادعای phenomenal/qualia/sentience نیست» + گاردی که با رشتهٔ phenomenal|qualia|sentient raise می‌کند.
- **چرا:** خود-ارزیابیِ استاندارد به‌جای proxyِ خامِ registry.coherence؛ اغراق را **ساختاراً** ناممکن می‌کند.

## ۳. تریاژِ معرفتی — چه بسازیم، چه نسازیم

- **FACT (امنِ ساخت):** precision-weighting (pymdp)، Shared Global Workspace (Goyal-Bengio)، salience retrieval (Generative Agents)، Kamoi 2024 (خود-نمره‌دهی معمولاً کمکی نیست)، Brier/ECE/AURC، default-deny (Saltzer-Schroeder)، HMAC RFC 2104، زنجیرهٔ هش RFC 9162، SEC 15c3-5، reward-hacking (Skalse).
- **EMERGING (پشتِ فلگ، نه اثبات):** Blum&Blum CTM + soft-WTA، فرمال‌سازیِ ignitionِ همه-یا-هیچ، Predictive-GNW، sleep-time compute، roadmapِ حافظهٔ اپیزودیک، introspectionِ Anthropic (خودشان می‌گویند محدود/غیرقابل‌اتکا).
- **HYPE (فقط به‌عنوان بازاریابی/نظر):** «۲۶٪ دقتِ بیشتر / ۹۰٪ توکنِ کمترِ» Mem0 (vendor)، کردنسِ «~۲۰٪ آگاه» (تخمینِ شخصیِ یک پژوهشگر)، اظهاراتِ kill-switchِ بانکِ مرکزی (مرحلهٔ پیشنهاد).
- **چه نسازیم (خطِ قرمز):** (۱) هیچ ادعای IIT-Φ / «یکپارچگی=آگاهی» — `registry.coherence` یک proxyِ خامِ برچسب‌دار می‌ماند؛ (۲) **هرگز `HEART_W_SHADOW>0` را روی قوتِ یک سیگنالِ خودساخته live نکن** (تلهٔ reward-hacking؛ provenance-gated روی صفر تا اعتبارِ بیرونی)؛ (۳) نشانگرهای GWT/HOTِ ارضاشده = اثباتِ آگاهی نیست (Cogitate 2025 هیچ ignitionِ frontal در onset ندید) — ماژولِ ignition = مسیریابیِ access، نه آگاهی.

## ۴. توصیهٔ برتر + قدمِ بعد

**توصیهٔ برتر: مورد ۱ (Fail-closed HumanAppendGuard).** تنها ایرادی که یک نقصِ **زندهٔ قابلِ‌سوءاستفاده** را می‌بندد (`is_human` جعل‌شدنی)، S-effort، $۰، backward-compatible (فلگ خاموش)، و قالبِ مورد ۴. چون به فایلِ امنیتیِ `_ops/budget/` دست می‌زند و تو گفتی «فقط پیشنهاد» — **منتظرِ «برو»ی توام**؛ خودم نزدم.

**نکتهٔ درختی (صادقانه):** ماژول‌های `cortex/*` روی شاخهٔ master هستند (نه این worktreeِ heart-branch)، پس موارد ۵–۸ روی درختِ یکپارچهٔ master اعمال می‌شوند — که `ignition.py` را همین جلسه آنجا ساختم.

---
*ساخت: جلسهٔ ۴۶ ادامه (۲۰۲۶-۰۷-۱۱) — ممیزیِ ۶-ستونیِ وب (۷ ایجنت، web_used=true، ۶/۶ ستون با منبعِ واقعی) + سنتز. همراهِ [[06 - Architecture Maps/HEART - Neuro Map & Direction]].*
