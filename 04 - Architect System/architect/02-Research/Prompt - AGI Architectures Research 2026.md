---
type: prompt
created: 2026-07-03
target: Claude / ChatGPT Deep Research
output-language: فارسی
status: done
updated: 2026-07-04
---

# پرامپت تحقیق — ۲۰ معماری نوآورانه AGI (وضعیت ۲۰۲۶)

**نحوه استفاده:** کل بلاک کد زیر را در حالت Deep Research (کلود یا ChatGPT) پیست کن. خروجی یک گزارش فارسی با اصطلاحات انگلیسی است — مناسب انتقال به `07 - Knowledge`.

لیست seed داخل پرامپت از اسنپ‌شات وب ژوئیه ۲۰۲۶ استخراج و راستی‌آزمایی شده (سورس‌ها در انتهای همین نوت).

```text
# ROLE
You are a senior AI research analyst specializing in AGI architectures, cognitive
science, and agent systems. You verify every claim against primary sources and
never present unverified names or numbers.

# MISSION
Using deep web research (current as of 2026), identify, verify, and profile the
20 most influential and innovative architectures, methods, and structural
paradigms aimed at AGI. Cover the full landscape — not just LLM agents.

# COVERAGE REQUIREMENTS
Select the 20 across these paradigm families. Include at least 1 from each
family; no family may exceed 4 entries:

1. World models & latent prediction — e.g., JEPA/V-JEPA (Meta), Genie 3
   (Google DeepMind), Dreamer
2. Active inference & free-energy principle — e.g., AXIOM (VERSES)
3. Neurosymbolic & hybrid — e.g., OpenCog Hyperon + PRIMUS/MeTTa
   (SingularityNET), AlphaProof/AlphaGeometry (DeepMind)
4. Classic cognitive architectures still active — e.g., SOAR, ACT-R, LIDA,
   NARS, BDI
5. LLM-agent reasoning patterns — e.g., ReAct, Reflexion, Tree-of-Thoughts,
   Plan-and-Execute, CoALA
6. Memory-centric architectures — e.g., MemGPT/Letta, Mem0, Zep,
   Generative Agents (Stanford)
7. Multi-agent societies — e.g., supervisor-worker / maker-checker patterns,
   AutoGen → Microsoft Agent Framework, MetaGPT
8. Self-improving & open-ended systems — e.g., Darwin Gödel Machine
   (ICLR 2026), AlphaEvolve, Voyager, AI Scientist-v2, quality-diversity
   (MAP-Elites, POET)
9. Frontier scaling & test-time reasoning — e.g., reasoning models,
   Mixture-of-Experts, test-time compute
10. Embodied / robotics — e.g., vision-language-action (VLA) foundation models

The examples above are seeds from a July 2026 snapshot: verify each one, and
replace any seed with a stronger candidate if your research supports it.

# SEARCH PROTOCOL
- Prioritize primary sources: arXiv, lab blogs (DeepMind, OpenAI, Anthropic,
  Meta AI, VERSES, SingularityNET), ICLR/NeurIPS/ICML 2025–2026 proceedings;
  then credible surveys and engineering blogs.
- Recency: prefer 2024–2026 work and always report 2026 status. Include
  pre-2024 classics ONLY if still actively developed or foundationally
  influential today.
- Cross-verify every architecture with at least 2 independent sources.
  If a name cannot be verified, exclude it — never invent or guess.
- Seed queries: "AGI architecture survey 2026" · "world models AGI 2026" ·
  "self-improving agents ICLR 2026" · "neurosymbolic AGI 2026" ·
  "cognitive architecture comparison 2026" · "agentic AI design patterns 2026"

# SELECTION CRITERIA (score candidates, keep top 20)
- Influence: citations, adoption, derivative work
- Architectural novelty: a genuinely distinct mechanism, not a wrapper
- 2026 vitality: active development or deployment this year
- Credibility: a real lab, company, or research community behind it

# OUTPUT FORMAT — write the report in PERSIAN (فارسی), keep technical terms in English
1. خلاصه اجرایی — چشم‌انداز معماری AGI در ۲۰۲۶ در حداکثر ۵ جمله
2. جدول اصلی هر ۲۰ مورد:
   | # | نام | آزمایشگاه/سازنده | سال | خانواده پارادایم | مکانیزم هسته (یک جمله) | وضعیت ۲۰۲۶ |
3. پروفایل تک‌به‌تک ۲۰ معماری، برای هر کدام:
   - نام و سازنده
   - مکانیزم اصلی (۳–۴ جمله)
   - نوآوری کلیدی (چرا «معماری متمایز» است)
   - نقاط قوت و محدودیت‌ها
   - وضعیت و کاربرد واقعی در ۲۰۲۶ + برچسب [research / prototype / production]
   - ۲–۳ منبع با لینک
4. نقشه پارادایم‌ها — کدام خانواده‌ها در حال همگرایی یا رقابت‌اند
   (مثلاً مناظره world models در برابر LLM scaling خالص)
5. مسیر مطالعه — ۵ معماری اول برای یک مهندس AI با توجیه
6. فهرست کامل منابع شماره‌دار با تاریخ

# QUALITY RULES
- Every factual claim must trace to a cited source.
- Separate hype from reality: label each entry [research / prototype / production].
- Report disagreements between researchers (e.g., LeCun's critique of
  generative/pixel-reconstruction world models) instead of picking a side.
- No duplicate entries: closely related variants (e.g., JEPA and V-JEPA)
  count as one entry.
- If two architectures share the same core mechanism, keep the more
  influential one and mention the other inside its profile.
```

## سورس‌های راستی‌آزمایی seedها (وب — ژوئیه ۲۰۲۶)

- [Darwin Gödel Machine — arXiv 2505.22954 (ICLR 2026)](https://arxiv.org/abs/2505.22954)
- [Genie 3 — Google DeepMind](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)
- [World Models Race 2026 — Introl](https://introl.com/blog/world-models-race-agi-2026)
- [OpenCog Hyperon + PRIMUS — Springer 2026](https://link.springer.com/chapter/10.1007/978-3-032-00686-8_18)
- [LLM Agent Architectures in 2026 — FutureAGI](https://futureagi.com/blog/llm-agent-architectures-core-components/)
- [35 Agentic Architectures (Reflexion, MemGPT, Voyager…) — GitHub](https://github.com/FareedKhan-dev/all-agentic-architectures)
- [Agentic AI: Comprehensive Survey — arXiv 2510.25445](https://arxiv.org/html/2510.25445v1)
- [Letta agent loop: ReAct، MemGPT — Letta Blog](https://www.letta.com/blog/letta-v1-agent)
- [World Models: Five Competing Approaches — Themesis 2026](https://themesis.com/2026/01/07/world-models-five-competing-approaches/)
