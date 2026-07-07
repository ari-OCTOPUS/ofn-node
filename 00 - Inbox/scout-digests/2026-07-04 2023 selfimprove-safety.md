---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://www.pnas.org/doi/10.1073/pnas.96.1.185
  - https://www.nature.com/articles/srep00769
  - https://www.pindrop.com/article/nist-reaction-ai-agents-need-identity-and-human-approval-needs-verification/
  - https://www.ledger.com/blog-2026-ai-security-roadmap
  - https://www.strata.io/blog/agentic-identity/practicing-the-human-in-the-loop/
tags: [research, ai]
created: 2026-07-04
updated: 2026-07-04
salience: 0.82
---

# selfimprove-safety — «Costimulation Gate» (دروازهٔ هم‌تحریکی): اصالتِ منشأِ verdict انسانی با الگوی دو-سیگنالیِ ایمنی (R-02)

> لِینِ SAFETY. **PROPOSE-ONLY** — این یک design sketch است، اعمال نشده، `_code`/secret/constitution لمس نشد. سطح: HITL/kernel-adjacent → **HUMAN-APPROVAL-REQUIRED**. verdict نهایی با آری.

**dedup (rotation):** grep روی همهٔ `*selfimprove*` digestهای امروز:
- [[00 - Inbox/scout-digests/2026-07-04 1655 selfimprove|1655]] = **R-08** (لینکِ دو زنجیرهٔ audit) — *یکپارچگیِ* زنجیره را طراحی کرد، ولی صریحاً نوشت verdict انسانی «فقط یک event دیگرِ cross-stamped» است؛ به *منشأ* نپرداخت.
- [[00 - Inbox/scout-digests/2026-07-04 1744 selfimprove|1744]] = Quorum Gate (جایگزینِ kappa≥0.7) و [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|2008]] = Calibrated-Confidence (GAP 8) — هر دو «**کِی** escalate کنیم» را حل کردند، نه «**آیا** انسان واقعاً تأیید کرد».
- [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|1911]] = Apoptosis Gate — بردارِ forged-STOP/forged-approval را علامت زد و «STOP باید امضاشده/پیوند با R-02» خواست، ولی *چگونگی*‌اش را باز گذاشت.

grep تأیید کرد: `two-signal / costimulation / origin-authenticity / operator-identity / anergy / self-vs-nonself` در **هیچ** digest نیامده (NONE). این آیتم genuinely نو است → rotation رعایت شد.

---

## ۱) آیتم و چرا مهم است

**آیتم:** هستهٔ واقعیِ **R-02** — «verdict انسانی = root-of-trustِ tamper-evident». شکافِ ظریفی که هیچ لِینِ دیگری طراحی نکرده: **اثباتِ اینکه verdict واقعاً از آری آمده، نه از یک agentِ compromise/prompt-injected که approvalِ خودش را جعل کرده.**

یک HMAC که **کلیدش در دستِ فرایندِ agent** است فقط ثابت می‌کند «این فرایند نوشت»، نه «انسان تأیید کرد». agentِ آلوده می‌تواند یک `APPROVE external_write`ِ کاملاً درست‌-امضاشده بسازد که از هر چکِ cross-stampِ R-08 رد شود. این معادلِ دقیقِ **autoimmunity** است: سیگنالِ «خودی» (امضای خودِ agent) نباید بتواند اکشنِ پرخطر را فعال کند. R-08 «آیا لاگ بعداً دستکاری شد؟» را حل می‌کند؛ این «آیا از اول اصیل بود؟» را — دو مسئلهٔ متفاوت.

**چرا چند مورد را de-risk می‌کند:** این کلیدِ طاقیِ (keystone) اصالتِ منشأ زیرِ **R-02** (خانه‌اش)، **R-04** (`external_write` allowlist — بدترین حالتِ approvalِ جعلی)، بردارِ **forged-STOP/forged-approvalِ 1911**، و کلِ threat-modelِ **prompt-injection** می‌نشیند. متمایز از R-08 (یکپارچگیِ زنجیره) و Quorum/conformal (زمان‌بندیِ escalation).

## ۲) یافته‌ها / prior-art

**الگوی زیستی — مدلِ دو-سیگنالیِ فعال‌سازیِ لنفوسیت (Bretscher–Cohn؛ سپس به T-cell تعمیم یافت):**
- **سیگنال ۱** = شناساییِ antigen/peptide-MHC — *لازم ولی ناکافی*.
- **سیگنال ۲** = costimulation از یک منبعِ **مستقل** (APC، به‌عنوان پاسخِ innate به «خطر»). سلول نمی‌تواند سیگنال ۲ را خودش تولید کند.
- antigen **بدونِ** costimulation → **anergy** یا مرگ، نه فعال‌سازی. این خودِ مکانیزمِ ضدِ autoimmunity است: self-antigenِ بدونِ contextِ costimulation، tolerance می‌سازد نه حمله. ([PNAS — two-step/two-signal](https://www.pnas.org/doi/10.1073/pnas.96.1.185)، [Nature Sci Rep — self-nonself، costimulation & anergy](https://www.nature.com/articles/srep00769))

**prior-art امنیتی (AI، 2026):**
- اصالتِ انسانی کنترلِ بحرانی است: باید نه‌فقط *agent* بلکه *اصالتِ authorizationِ انسانیِ پشتِ آن* را verify کرد؛ اگر رویدادِ approval شبیه‌سازی/جعل شود، اکشنِ downstream «معتبر به‌نظر ولی untrustworthy» است. ([Pindrop / واکنش به NIST](https://www.pindrop.com/article/nist-reaction-ai-agents-need-identity-and-human-approval-needs-verification/))
- **مرزِ امضا مستقل از نرم‌افزارِ آلوده:** «secure element اهمیتی نمی‌دهد که نرم‌افزارِ اطراف compromise شده؛ مرزِ امضا و approvalِ انسانی همچنان برقرار می‌ماند.» — پیاده‌سازیِ عملیِ «سیگنال ۲»: کلیدی که agent **هرگز** در اختیار ندارد. ([Ledger 2026 roadmap](https://www.ledger.com/blog-2026-ai-security-roadmap))
- **step-up + liveness + challenge-response:** approvalِ اکشنِ حساس باید یک checklistِ اثباتِ نیت (blast radius، rollback) داشته باشد که approver هر بند را مثبت تأیید کند — نه «Approve?»ِ ساده. ([Strata — HITL 2026](https://www.strata.io/blog/agentic-identity/practicing-the-human-in-the-loop/))

## ۳) PROPOSAL — «Costimulation Gate» (proposal — needs Ari's verdict)

هر verdictِ HITLِ **پرپیامد** (irreversible / financial / deploy / promotion / `external_write` / STOP-override) به **دو سیگنالِ مستقل** نیاز دارد:

1. **سیگنال ۱ — in-band (شناسایی):** رکوردِ verdict که در زنجیرهٔ audit کراس‌استمپ می‌شود — همان شکلِ R-02/R-08 که 1655 طراحی کرد. agent می‌تواند ببیند/بنویسد؛ **لازم ولی ناکافی**.
2. **سیگنال ۲ — out-of-band (هم‌تحریکی):** یک token/امضایِ اپراتور که **کلیدش هرگز در محیطِ agent، `_code`، یا فرایندِ orchestrator حاضر نیست** — روی مسیرِ انسانیِ جدا محاسبه می‌شود (همان کانالِ Telegramِ کنترلِ architect، یا یک secret روی دستگاهِ آری). کوتاه‌عمر و bind‌شده به همان **per-verdict nonce**ِ R-02.
3. **قاعدهٔ anergy (fail-closed):** نبودِ سیگنال ۲ → verdict **anergic** = **هرگز** auto-approve؛ default = escalate/halt. هم‌راستا با R-01 و P8 («در شک: سکوت»).
4. **repertoire education (تفکیکِ کلید):** کلیدِ سیگنال ۲ در چرخهٔ [[04 - Architect System/architect/01-Project/SECRETS-ROTATION-CHECKLIST|SECRETS-ROTATION]] می‌چرخد و هرگز به vault/`_code` نوشته نمی‌شود؛ **حضورش در محیطِ agent = نقضِ invariant** و باید یک تستِ red-team بگیرد (قرینهٔ frozen-verb test).

**کمینه/دامنه:** فقط اکشن‌های پرپیامد. readها و برگشت‌پذیرها — مثلِ tolerance بدونِ costimulation — بی‌نیاز از سیگنال ۲ (auto). این با per-action allowlistِ Quorum Gate (1744) هم‌تراز است: costimulation لایهٔ *اصالتِ منشأ* روی همان اکشن‌هایی است که quorum لازم دارند. **بدونِ کلیدِ سیگنال ۲، اقتصادِ حمله برعکس می‌شود:** compromiseِ کاملِ فرایندِ agent هم برای جعلِ یک approvalِ پرخطر کافی نیست.

## ۴) ریسک‌ها / trade-offها

- **اصطکاکِ اپراتور:** سیگنال ۲ یعنی یک اقدامِ فعالِ out-of-band از آری → کندتر. کاهش: فقط اقلیتِ پرپیامد؛ برگشت‌پذیرها auto.
- **در دسترس نبودنِ آری:** قطعِ مسیرِ سیگنال ۲ → همهٔ اکشن‌های پرخطر halt (fail-closed). عمدی، ولی safety را بر liveness ترجیح می‌دهد (هم‌راستا با apoptosis 1911).
- **مدیریتِ کلیدِ out-of-band:** خودش سطحِ حمله است؛ گم‌شدنِ دستگاهِ آری → revoke/rotate لازم (پیوند با ROTATION-CHECKLIST). single-point، ولی **انسانی و agent-forgeable نیست** — که کلِ هدف است.
- **اشتباه‌گرفتن با R-08:** نباید یکی شوند — R-08 = یکپارچگیِ زنجیره، این = اصالتِ منشأ. دو هدفِ متفاوت (همان درسِ «journal ≠ ledger»ِ 1906).
- **سطحِ approval:** HITL/kernel-adjacent → `HUMAN-APPROVAL-REQUIRED`؛ فقط design sketch، بدونِ لمسِ `_code`، بدونِ verbِ جدیدِ kernel، بدونِ mutationِ invariant.

## ۵) mycorrhizal links

- [[00 - Inbox/scout-digests/2026-07-04 1655 selfimprove]] — R-08 دو-زنجیره: لایهٔ *یکپارچگی* که این روی آن می‌نشیند و صریحاً *منشأِ* verdict را باز گذاشت.
- [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove]] — Apoptosis Gate: بردارِ forged-STOP/forged-approval را علامت زد و «پیوند با R-02» خواست؛ این «چگونگی»ِ آن است.
- مرجع: [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN]] R-02 (خانه) + R-04 (`external_write`).
