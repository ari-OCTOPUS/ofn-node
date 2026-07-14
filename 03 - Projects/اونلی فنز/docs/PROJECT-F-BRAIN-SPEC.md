---
type: proposal
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: draft-for-build
created_by: agent
relates_to: "[[TELEGRAM-CONTENT-STUDIO-v2]] (صبا) · [[TELEGRAM-BRAIN-COCKPIT-v1]] (آری) · _ops/doctor/box/ (زیرساخت) · CLAUDE.md منشور"
tags: [project-f, brain, orchestration, multi-agent, hitl, propose-only]
created: 2026-07-09
updated: 2026-07-09
aliases: ["Brain Spec", "مغز Project-F"]
---

# PROJECT-F INTELLIGENT BRAIN — مغزِ هوشمندِ بینِ دو UI

> یک لایهٔ هوشِ orchestration که **بینِ استودیوی صبا و کاکپیتِ آری** می‌نشیند. الگوهای AIِ ۲۰۲۷ را کپی می‌کند، ولی داخلِ حصارِ Project-F: propose-only، human-gated، ۲٪-capped، compliance/ethics سخت، صفر رسانه/PII. یک نمونهٔ Box-of-Agents اسکوپ‌شده (بازاستفاده از `_ops/doctor/box/`).

## ۱. جایگاه (بینِ دو UI)
```
🎬 صبا (Content Studio)  →  🧠 مغزِ Project-F  →  🧠 آری (Brain Cockpit)
   درفت/ترند/محدوده          تحلیل+پیشنهاد          تأیید (human-append)
        ↑───────────  verdict برمی‌گردد  ───────────↓
```
مغز ~۸۵٪ کارِ تحلیلی را می‌کند؛ **انتشار/پول/استراتژی فقط با تأییدِ آری** (HITL).

## ۲. الگوهای ۲۰۲۷ که کپی شد
| الگو (شرکت‌های AI ۲۰۲۷) | کاربرد در مغزِ Project-F |
|---|---|
| **multi-agent + control-plane** `[FACT]` | مغز = control-plane؛ ۷ زیرعامل تخصصی |
| **HITL: AI ~۸۵٪، انسان تأییدِ spend/استراتژی؛ tiered review** `[FACT]` | low-risk → پیشنهاد به صبا؛ high-risk/پول/انتشار → آری |
| **contextual bandit، approval-gated learning** `[FACT]` | قیمتِ PPV/زمان‌بندی = bandit سه‌لایه، یادگیری فقط از نتایجِ **تأییدشده** |
| **حاکمیت/cost-cap (۴۰٪ agentic تا ۲۰۲۷ کنسل)** `[FACT]` | ۲٪-cap + kill-switch + audit (ledger) |
| **three-pillar responsible-AI: شفافیت/پاسخگویی/اعتماد** `[FACT]` | Ethics-Guard + ترنسکریپتِ append-only |
| **archive/self-improvement (DGM/MAP-Elites)** | آرشیوِ «چه چیزی کار کرد»، پیشنهادِ variant، λ_persist<0 |

## ۳. معماری — control-plane + ۷ زیرعامل
- **Strategist** — نردبانِ ارزش (wall vs PPV)، برنامهٔ تم.
- **Pricer** — contextual bandit سه‌لایه (نرخِ پایه × ضریبِ محتوا × ضریبِ زمان)، **approval-gated**؛ قیمت را پیشنهاد می‌دهد، آری تأیید.
- **Scheduler** — زمانِ بهینه، تقویم.
- **Copywriter** — کپشن/عنوان/DM (draft، human-gated؛ بدونِ explicit).
- **Analyst** — KPIهای تجمیعی (churn/ARPU/unlock/retention)، سگمنتِ VIP/معمولی/lurker. **صفر PII فن.**
- **Compliance-Guard** — گیتِ سختِ هر پیشنهاد: faceless · فقط‌پا · بدون explicit · ۱۸+/رضایت · ToS · پرداختِ درون‌پلتفرم · geo-block. رد نشد = drop.
- **Ethics-Guard** — بدونِ dark-pattern/دستکاریِ فن؛ ۸۰٪ رابطه/۲۰٪ فروش؛ رفاهِ فن؛ **محدودهٔ صبا مقدمِ مطلق**؛ λ_persist<0 (مغز بقا/engagement-به‌هرقیمت را optimize نمی‌کند).

## ۴. جریانِ HITL (tiered)
1. صبا درفت/ایده ثبت → مغز تحلیل + پیشنهاد (استراتژی/قیمت/زمان/کپی).
2. Compliance+Ethics Guard هر پیشنهاد را گیت می‌کنند (drop یا pass).
3. **low-risk** (ایدهٔ محتوا/زمان) → مستقیم به استودیوی صبا (پیشنهاد).
4. **high-risk** (قیمت/انتشار/DMِ فروش) → کاکپیتِ آری برای **human-append**.
5. verdictِ آری → اجرا **درون‌پلتفرم** + برگشت به صبا + ثبت در آرشیو (یادگیری).

## ۵. خطوطِ قرمز (baked)
propose-only، هرگز انتشارِ خودکار · دوکلیده (صبا→آری) · صفر رسانه/هویت/PII در مغز (فقط متادیتا/تجمیعی) · پرداخت فقط درون‌پلتفرم، صفر مذاکره · محدودهٔ صبا مقدم · ۲٪ cost-cap + kill-switch · λ_persist<0 + Ethics-Guard (ضدِ دستکاری) · containment در پوشهٔ Project-F · بازاستفاده از `_ops/doctor/box` (نه کانِنِ دوم).

## ۶. پرامپتِ GLM
```
تو کارگرِ کدنویسِ Project-F (GLM) هستی. مغزِ هوشمندِ Project-F را بساز: control-plane + ۷ زیرعامل، بینِ استودیوی صبا و کاکپیتِ آری. propose-only، sandbox، ۲٪-capped، commit با مالک. یک نمونهٔ Box-of-Agents (بازاستفاده از _ops/doctor/box/)، نه کانِن دوم.
بخوان: 03 - Projects/اونلی فنز/{PROJECT-F-BRAIN-SPEC, TELEGRAM-CONTENT-STUDIO-v2, TELEGRAM-BRAIN-COCKPIT-v1(مسیرِ 04), CLAUDE.md} + _ops/doctor/box/ (Warden/agent_state/topology) + doctor/evolution.py (archive). PLAN بده. فایل زیرِ پوشهٔ Project-F.
بساز: control-plane + Strategist · Pricer(contextual bandit سه‌لایه، approval-gated) · Scheduler · Copywriter(draft) · Analyst(تجمیعی) · Compliance-Guard(گیتِ سخت) · Ethics-Guard(ضدِ دستکاری، محدوده مقدم). جریانِ HITLِ tiered §۴. آرشیوِ «چه کار کرد» با λ_persist<0.
خطِ قرمز (نقض=رد): propose-only، صفر انتشارِ خودکار · دوکلیده با آری · صفر رسانه/هویت/PII (فقط متادیتا/تجمیعی) · پرداخت فقط درون‌پلتفرم · محدودهٔ صبا مقدم · ۲٪-cap + kill-switch · λ_persist<0 + Ethics-Guard · بازاستفاده از box، نه کانِن دوم · بدونِ git commit.
تست‌ها ($0): هر پیشنهاد از Compliance+Ethics Guard رد می‌شود اگر قاعده بشکند · high-risk بدونِ تأییدِ آری اجرا نمی‌شود · Pricer فقط از نتایجِ تأییدشده یاد می‌گیرد · صفر PII/رسانه در خروجی · ۲٪-cap fail-closed · λ_persist منفی. خروجیِ خامِ تست را paste کن.
DoD: مغز تست‌سبز، HITLِ tiered، دو Guard فعال، ایزوله، صفر رسانه/PII. commit دستِ مالک. هر ابهام → «⚑ برای معمار».
```

## Sources
- [Multi-agent orchestration 2026 (reinventing.ai)](https://insights.reinventing.ai/articles/ai-agents-multi-agent-orchestration-2026-02-26) · [2026 year of multi-agent (aiagentsdirectory)](https://aiagentsdirectory.com/blog/2026-will-be-the-year-of-multi-agent-systems)
- [Human-in-the-loop AI marketing (Improvado)](https://improvado.io/blog/human-in-the-loop-ai) · [HITL contextual bandits pricing (arXiv 2606.02595)](https://arxiv.org/pdf/2606.02595)
- [Responsible AI three-pillar (arXiv 2601.06223)](https://arxiv.org/pdf/2601.06223)
- OF ops: [PPV value-ladder](https://www.pseudoface.com/guides/start-here/profile-setup/onlyfans-wall-vs-ppv-value-ladder) · [Analytics KPIs](https://www.sirency.com/blog/onlyfans-analytics-metrics-tracking-guide)
