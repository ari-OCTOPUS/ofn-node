---
id: sog-synthesis
aliases: [سنتز جامع SOG, SOG generalization, engineering grammar, MAS patterns]
tags: [پژوهش, #core-concept, سیستم, معماری]
source: "C:/Users/Armin/Downloads/سایه‌های‌ابعاد‌بالاتر-در-دنیای-انسان_2.docx"
related: ["[[MOC-سیستم]]", "[[E-shadow]]", "[[Delta-self]]", "[[قضیه‌ی-شناسایی]]"]
---

# 🧬 سنتز جامع SOG — گرامر مهندسی برای سیستم‌های هوشمند

> [!important] تعمیم پروژه از مدلِ خطی-گاوسی به گرامر مهندسیِ عمومی
> این سند SOG را از یک مدل Stage-B خاص به یک **دستگاهِ مهندسی** برای هر سیستمِ چندعاملی ارتقا می‌دهد. ~۷۰٪ محتوای آن نسبت به [[📄 متن-کامل-نظریه]] و [[📄 متن-کامل-handoff]] جدد است.## ۱. تجزیه‌ی عملیاتی SOG

[[مدل-خطی-گاوسی|مدل خطی-گاوسی]] به هر سیستم با حالت پنهان تعمیم می‌یابد:

$$H_t = \text{hidden state}, \quad D_t = \text{private dither}, \quad Y_t = \text{public trace}$$

سه رژیمِ پیش‌بینی:
- $L_0$ = null/baseline loss
- $L_b$ = blind observer (فقط $Y_t$)
- $L_i$ = informed observer ($Y_t + D_t + M^{private}$)

تجزیه‌ی قابلِ استفاده:
$$E_{\text{shadow}} \approx L_0 - L_b, \quad \Delta_{\text{self}} \approx L_b - L_i$$

> [!warning] در LLM، نسخه‌ی ایمن cross-entropy/log-loss است، نه variance-ratio (مگر اینکه فرض گاوسی برقرار باشد).## ۲. پانزده اصلِ مهندسی| اصل | معنای SOG | بازتفسیر مهندسی |
|---|---|---|
| [[shadow-observability]] | نشت حالت پنهان به مشاهدات | توانایی [[Orchestrator|orchestrator]] در استنتاجِ وضعیت worker از خروجی عمومی |
| [[self-model-gain]] | [[Delta-self|Δ_self]] | سودِ دسترسی به scratchpad/memory/plan خصوصی |
| [[private-control-channel]] | دیتر خصوصی | branch IDs، seeds، retrieval traces، internal critique |
| [[epistemic-asymmetry]] | تفاوت اطلاعات self و other | agent های مختلف context های متفاوت می‌بینند |
| [[temporal-identifiability]] | λρ≠0 | یک خروجی کافی نیست؛ نیاز به trajectories/probes |
| [[censoring-not-dropping]] | گزارش نه حذف | timeout/censored در run logs، نه silent exclusion |
| [[null-model-pressure]] | مقایسه با iid | هر خروجی باید baseline ارزان را شکست دهد |
| [[leakage-budget]] | حد نشت | چقدر private state از public trace قابل‌استنتاج است |
| [[mode-stability]] | self-conditioning loop | anchors/prompts واریانس رفتار را کاهش می‌دهد |→ ۶ اصل دیگر در فایلِ پیوست.## ۳. سیزده الگوی معماری

> [!abstract] هر الگوی دارای: core-insight / problem / pattern / observability / failure / criteria۱. **[[dual-track-evaluator]]** — ارزیابِ blind + informed
۲. **[[reflection-gate]]** — بازتابشِ مشروط به Δ_self
۳. **[[shadow-orchestrator]]** — routing از compressed shadows
۴. **[[first-person-router]]** — بازگشت به agent اصلی وقتی memory مهم است
۵. **[[epistemic-censor]]** — gate برای tool actionsِ غیرقابل‌بازگشت
۶. **[[reflective-dither-regulator]]** — exploration کنترل‌شده
۷. **[[provenance-dither]]** — metadata امضاشده برای delegation
۸. **[[temporal-shadow-tomography]]** — بازسازی policy از sequential probes
۹. **[[counterfactual-self-surgery]]** — ablation harness برای private state
۱۰. **[[adversarial-shadow-firewall]]** — ضدِ نشتِ private state
۱۱. **[[mode-locked-stabilizer]]** — anchor برای کاهش drift
۱۲. **[[censored-consensus]]** — رأی‌گیری با وزنِ استقلال
۱۳. **[[null-model-rejection]]** — reject خروجی که baseline را نشکسته## ۴. چهار امتیاز عملیاتی

| امتیاز | فرمول | معنی |
|---|---|---|
| **SMS** (Self-Model Score) | $L_b - L_i$ | چقدر private state پیش‌بینی را بهتر می‌کند |
| **SLS** (Shadow Leakage) | $L_0 - L_b$ | چقدر از public trace قابل‌استنتاج است |
| **PCAI** (Private-Channel Advantage) | $\frac{L_b - L_i}{L_0 - L_i + \epsilon}$ | کسرِ سود از private state |
| **MSC** (Mode-Stability) | $1 - V_a/V_0$ | چقدر anchors واریانس را کم می‌کند |

## ۵. چهارده فرضیه‌ی falsifiable

هر کدام با independent/dependent variables، metric، و falsifier.

نمونه: «scratchpad فقط در task های با hidden intermediate state بهتر است»
- falsifier: «هیچ gain معناداری در task های سخت دیده نمی‌شود»

→ لیست کامل در [[ hypotheses-sog ]].## ۶. نقشه‌راه v0/v1/v2

- **v0**: public/private schema، blind/informed harness، null baseline، counterfactual ablation، cost ledger
- **v1**: reflection gate، shadow orchestrator، first-person router، epistemic censor
- **v2**: temporal tomography، leakage firewall، censored consensus، mode-stability

## ۷. قاعده‌ی طلاییِ مهندسی

$$\text{public trace} \neq \text{private state} \neq \text{self-access} \neq \text{trustworthy introspection}$$

> [!warning] پنج خطرِ مرگبار
> ۱. confonding scratchpad با introspection قابل‌اعتماد
> ۲. confonding public rationale با computation
> ۳. confonding decorative prompts با control channels
> ۴. فرض کردنِ اینکه transparency همیشه خوب است
> ۵. فرض کردنِ اینکه multi-agent همیشه بهتر است## ۸. مدل فضازمان-رویداد (تعمیم به تجربه‌ی انسانی)

$$e_{i,t} = (\tau_t, x_{i,t}, r_{i,t}, y_{i,t}, c_t)$$

- $\tau_t$ = زمان تقویمی
- $x_{i,t}$ = موقعیت فضایی
- $r_{i,t}$ = گره در گراف اجتماعی
- $y_{i,t}$ = کنش قابل‌مشاهده (shadow)
- $c_t$ = زمینه‌ی معنایی

> [!tip] نتیجه‌ی استراتژیک
> اگر هدف foundation model است، نه از زمان، نه از فضا شروع کن — از **رویداد** شروع کن.