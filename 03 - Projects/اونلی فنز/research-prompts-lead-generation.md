---
type: reference
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: draft
tags: [research-prompts, lead-generation, growth, automation]
created: 2026-07-03
updated: 2026-07-03
---

# ۱۰ پرامپت تحقیقاتی — موتور لیدگیری اتوماتیک (Lead Generation Engine)

> **جایگاه:** تکمیل آیتم ۸.۵ master-reference (`[OPEN]` growth-prompts) با تمرکز روی **جذب لید اتوماتیک**: کشف → جذب → capture → nurture → تبدیل به سابسکرایبر.
> **وضعیت:** draft/proposal طبق Agent interface پروژه — هیچ اکشن خارجی؛ اجرای خروجی‌ها نیازمند verdict انسانی.
> **نحوه استفاده:** هر پرامپت را جدا در یک ابزار deep-research اجرا کن (۲–۴ تا موازی). **بلوک CONTEXT را همیشه اول paste کن.** کل مجموعه time-box شود (پیشنهاد: ≤۷ روز، هم‌راستا با بخش ۶ master-reference).
> **خارج از scope عمدی:** retention/rebill و pricing lab — این‌ها post-lead هستند (conversion/retention)، نه lead-gen؛ مجموعه جداگانه می‌خواهند.

---

## بلوک CONTEXT مشترک (اول هر پرامپت paste شود)

```text
CONTEXT — applies to everything below:
I run a legal, faceless adult creator brand (feet-only content; no face, no body) on OnlyFans-style platforms. Two-person team based in Australia, fully legal under Australian law. Budget cap: AUD 200/month. Current audience: zero. Primary market: global English speakers. Secondary market: Persian-speaking diaspora OUTSIDE Iran, reached via subtle "dog-whistle" cultural cues (brand stays English-first and discreet).

HARD CONSTRAINTS — every recommendation must respect ALL of these:
1. Platform-ToS-compliant tactics only. No spam, no mass cold DMs, no fake engagement, no bot followers, no scraping individuals' personal data. Explicitly flag ban/shadowban risk of anything you suggest.
2. Iran is fully excluded: no targeting Iranian users; content must be geo-blocked for Iran. Never suggest workarounds to this.
3. Creator anonymity is non-negotiable (faceless, zero identity leakage). Buyer privacy/discretion is a core brand principle.
4. Adult-content policies vary by tool — for EVERY tool you recommend, verify and state its adult-content policy and pricing (AUD or USD).
5. Tag every claim [FACT] / [EST] / [OPINION], cite sources with dates, and flag anything likely outdated that needs manual verification.

OUTPUT STYLE: structured markdown, tables where useful, end with a "Blind spots / what I might be missing" section.
```

---

## P1 — کالبدشکافی لیدگیری رقبا (نقشه کانال)

**هدف:** قبل از ساختن هر چیزی، ببینیم برنده‌های همین نیچ لید را از کجا می‌آورند.

```text
Research task: Reverse-engineer the subscriber-acquisition systems of 10–15 successful faceless and/or feet-niche creators (mix of big and mid-size; include at least 3 that grew from zero within the last 18 months).

For each: which channels drive their traffic (X/Twitter, Reddit, TikTok/IG SFW side, feet marketplaces like FeetFinder / FunWithFeet / current equivalents, Discord, YouTube, SEO), their funnel structure (first touch → link-in-bio → paid page), posting cadence per channel, and any public data on follower→subscriber conversion benchmarks in this niche.

Also answer: typical time-to-first-100-subscribers from a zero audience; which channels are rising vs declining in 2025–2026; the role of feet-specific marketplaces vs general platforms (fee structures, buyer intent, effort per sale).

Deliverable: (1) a channel matrix scored 1–10 on cost, effort/week, time-to-signal, ban-risk, and automation potential; (2) top-3 channel recommendation for a zero-audience faceless feet brand with AUD 200/month; (3) 5 concrete patterns the successful accounts share.
```

## P2 — موتور رشد X/Twitter + اتومیشن مجاز

**هدف:** X کانال اصلی فانل ماست؛ قواعد ۲۰۲۶ و مرز دقیق اتومیشنِ بی‌خطر را می‌خواهیم.

```text
Research task: Build a current (2026) playbook for growing an adult-creator X/Twitter account from zero, fully within X's rules.

Cover: X's current adult-content policy and required media/account labeling; how NSFW-labeled accounts are treated by the algorithm (reach limits, search visibility, audience restrictions); proven organic growth tactics for adult creators (content formats, reply strategy, quote posts, X Communities, posting windows); realistic follower-growth benchmarks for the feet niche; causes of shadowbans/suspensions and how to detect them.

Automation layer: which scheduling/automation tools explicitly allow adult content (verify each tool's policy + pricing); X API tiers and 2026 costs, and what a solo operator can cheaply automate (posting, analytics) vs what must stay manual (engagement); which automation behaviors X classifies as platform manipulation.

Deliverable: (1) a 30-day from-zero X playbook with weekly structure; (2) compliant automation stack with pricing; (3) a "never do" list ranked by ban severity.
```

## P3 — موتور Reddit و حضور سالم در کامیونیتی‌ها

**هدف:** Reddit هدفمندترین ترافیک نیچ را دارد ولی سخت‌گیرترین قوانین را؛ نقشه دقیق + SOP ضد-بن.

```text
Research task: Map the Reddit ecosystem for feet-content creators in 2026.

Cover: the 20–30 most relevant subreddits (size, activity, self-promo rules, verification requirements, posting-frequency limits); the verification process per major subreddit for a FACELESS creator (how to verify without showing a face — which subs allow it); account warm-up best practice (karma thresholds, account age, new-account filters); the line between genuine community participation and what mods treat as spam; crossposting strategy; scheduling tools that support Reddit NSFW posting (policy + pricing); common ban causes and recovery options.

Also: how much genuine engagement (comments, non-promo posts) is needed relative to promo posts, and what actually converts to profile clicks in this niche.

Deliverable: (1) ranked target-subreddit table (reach vs strictness vs faceless-verification feasibility); (2) a 4-week account warm-up plan; (3) a weekly posting SOP; (4) an anti-ban checklist.
```

## P4 — پرسونا/لور برند + آزمایشگاه هوک

**هدف:** برند faceless بدون شخصیت مغناطیسی لید نمی‌گیرد؛ پرسونا + هوک‌های scroll-stopper.

```text
Research task: How do top FACELESS adult creators build a magnetic brand persona ("lore") that attracts attention and followers without ever showing a face?

Cover: persona elements (name archetypes, voice/tone, backstory depth, mystery-as-a-feature), visual identity systems for feet-only content (color palettes, props, recurring themes, signature watermarks), and 3–5 case studies of faceless creators whose persona clearly drives growth.

Hook lab: catalog 25–30 proven "scroll-stopper" hooks and content formats in the feet/faceless niche (POV framings, series formats, challenges, unusual props/settings, curiosity gaps) with a note on why each works. Include caption formulas (structure, length, CTA placement) specifically for X and for Reddit.

Extra: subtle, deniable cultural-signaling techniques brands use to attract a specific diaspora audience without publicly labeling themselves (dog-whistle positioning) — examples from any industry, adapted to a discretion-first adult brand.

Deliverable: (1) a fill-in persona-design framework; (2) 30 hook/caption templates adapted to feet-only, faceless constraints; (3) a do/don't list for keeping the persona consistent at scale.
```

## P5 — فانل SFW→NSFW، link-in-bio و گیت‌ها (سن + جغرافیا)

**هدف:** مسیر کلیک لید تا اشتراک؛ به‌علاوه پیاده‌سازی عملی geo-block ایران در همه لایه‌ها.

```text
Research task: Design the optimal click-path from first touch to paid subscription for an adult creator, plus the gating infrastructure around it.

Cover: adult-friendly link-in-bio tools in 2026 (AllMyLinks-class tools and current alternatives — verify policies, pricing, and which get link-blocked by mainstream platforms); landing-page conversion best practices for adult (layout, social proof, free-vs-paid page ladder, trials as a lead hook); age-gate requirements and implementations; and CRITICALLY: geo-blocking at every layer — does OnlyFans (and 2–3 alternative platforms) support native country-level geo-blocking, how reliable is it, and how to also geo-block the link-in-bio/landing layer (tool-native options, Cloudflare-level blocking). Target country to block completely: Iran.

Tracking: UTM/link-tracking options that work in an adult context and survive platform link policies.

Deliverable: (1) recommended funnel architecture (text diagram); (2) tool stack with pricing; (3) step-by-step geo-block implementation checklist per layer; (4) [EST] conversion benchmarks per funnel step, with sources.
```

## P6 — مخاطبِ مالکیتی: ایمیل/تلگرام (بیمه ضد-بن)

**هدف:** اگر اکانت X یا Reddit بن شود، لیدها نباید بسوزند؛ لیست باید مال خودمان باشد.

```text
Research task: Platform-independent lead capture and nurture for an adult creator (de-risking platform bans).

Cover: email service providers that explicitly ALLOW adult content in 2026 (most mainstream ESPs prohibit it — verify each policy; pricing at <1k and <10k subscribers); lead magnets that actually convert a follower into an email/Telegram contact in this niche; Telegram channel + bot strategy for teaser distribution (what Telegram ToS permits for adult content, channel vs group, auto-posting bot tools); automated welcome/nurture sequence design (structure, frequency, tease-to-paid ratio); legal essentials: Australian Spam Act 2003 + CAN-SPAM basics for a small adult business (consent, unsubscribe, sender identity).

Deliverable: (1) capture→nurture blueprint (text flow); (2) ESP + Telegram tooling comparison table; (3) outline of a 5-message welcome sequence (structure only); (4) compliance checklist.
```

## P7 — اتومیشن DM و گفتگو با فن‌ها (ToS-safe)

**هدف:** DM جایی است که لید به پول تبدیل می‌شود؛ مرز دقیق «اتومیشن مجاز» و «بن‌خور» لازم است.

```text
Research task: What can be safely automated in fan DMs/conversations for an OnlyFans-style creator in 2026, and with which tools?

Cover: OnlyFans ToS position on automated messaging, AI chat tools, and third-party "chatter" services — what is explicitly allowed, gray, or banned; disclosure obligations (must fans be told they're talking to an AI/assistant? platform rules + any legal angle in AU/US); the 2026 landscape of AI DM/CRM tools for creators (SuperCreator-class tools and current equivalents — verify features, pricing, and their ToS-compliance claims independently); best-practice welcome messages, PPV DM sequencing, and segmentation (new subscriber vs lurker vs spender); documented cases of accounts penalized for DM automation and what triggered enforcement.

Design constraint: propose a HUMAN-IN-THE-LOOP split — what to automate (timing, segmentation, drafting) vs what stays human (the actual relationship), given the brand depends on trust and discretion.

Deliverable: (1) automate-vs-human decision table; (2) tool shortlist with pricing and risk rating; (3) new-subscriber DM flow (structure only); (4) risk register for DM automation.
```

## P8 — شبکه S4S / شات‌اوت / کولب

**هدف:** سریع‌ترین راه قرض‌گرفتن مخاطبِ دیگران — بدون قربانی‌شدن در بازارِ پر از اسکم.

```text
Research task: How does the shoutout/S4S (share-for-share) economy work for adult creators in 2026, and how can a zero-audience faceless account use it safely?

Cover: where deals actually happen (X, Reddit, Discord servers, Telegram groups, marketplaces, agencies); typical paid-shoutout pricing by account size, and reciprocity norms for free S4S; realistic conversion benchmarks from a shoutout (followers gained, subscriber conversion) [EST] with sources; scam patterns (bot audiences, faked engagement screenshots, payment scams) and a concrete vetting method to audit an account's audience quality BEFORE paying; whether S4S benefits small accounts at all, or only works above a follower threshold; agency red flags in this niche.

Deliverable: (1) S4S playbook for months 1–3 from zero; (2) pre-deal vetting checklist; (3) budget recommendation within AUD 200/month (or the argument for AUD 0 until the X account passes follower threshold N — state N).
```

## P9 — پایپ‌لاین تولید→توزیع اتوماتیک (Repurposing)

**هدف:** یک شوت در هفته باید بدون کار دستی به ده‌ها پست تبدیل شود — گلوگاه واقعی اتومیشن ما به‌احتمال زیاد همین‌جاست (اتصال به ریسک #۵).

```text
Research task: Design a content repurposing + scheduling pipeline for a two-person adult creator team: one batch shoot per week → dozens of derivative assets (X posts, Reddit posts, teasers, PPV sets) with minimal manual work.

Cover: workflow-automation platforms (n8n self-hosted vs Make vs Zapier) — verify each platform's adult-content policy, realistic monthly cost, and which is safest for this vertical; adult-friendly social schedulers (and which mainstream schedulers prohibit adult); watermarking automation; anonymity hygiene inside the pipeline: EXIF/metadata stripping, reverse-image-search resistance, file-naming discipline; asset/vault organization patterns; realistic build effort (hours) for a technical solo operator and monthly run cost.

Also: looking across the whole acquisition workflow, which steps are truly automatable end-to-end vs need human judgment — connect automation to the REAL bottleneck, not a hypothetical one.

Deliverable: (1) pipeline architecture (text diagram: shoot → process → distribute → track); (2) tool-stack decision with pricing; (3) build-vs-buy recommendation; (4) a week-1 minimal version vs a month-3 full version.
```

## P10 — آنالیتیکس، Attribution و حلقه آزمایش هفتگی

**هدف:** بدون اندازه‌گیری، «لیدگیری اتوماتیک» فقط «پست‌گذاشتن اتوماتیک» است؛ باید بدانیم کدام کانال مشترکِ پول‌ده می‌آورد.

```text
Research task: Build the measurement layer for a new adult creator brand's lead generation, suited to a validation phase with tiny numbers.

Cover: OnlyFans (and 2 alternative platforms) native tracking-link capabilities and their limits; link shorteners/trackers that permit adult content (verify + pricing); a minimal KPI set across the funnel (impression → profile visit → link click → free follow / email capture → paid sub) with realistic niche benchmarks per step [EST]; how to attribute subscribers to channels when platform analytics are weak; lightweight dashboard options (spreadsheet template vs cheap tools); and a weekly experiment-loop framework for a 2-person team: hypothesis → single-variable test → decision rule — including how to decide with statistically tiny samples (what signal size justifies killing or scaling a channel inside a 3-month runway).

Deliverable: (1) KPI definitions + target thresholds for the validation phase; (2) step-by-step tracking setup guide; (3) weekly experiment-loop template (fill-in table); (4) explicit "kill criteria" per channel.
```

---

## نقشه پوشش نسبت به آیتم ۸.۵ master-reference

| موضوع آیتم ۸.۵ | پرامپت |
|---|---|
| community-infiltration | P3 (بازتعریف‌شده به participation سالم و ToS-safe) |
| persona/lore | P4 |
| SFW→NSFW funnel | P5 |
| Reddit engine | P3 |
| S4S network | P8 |
| weird hooks | P4 |
| caption/DM | P4 + P7 |
| weekly experiment loop | P10 |
| retention/rebill · pricing lab | خارج از این مجموعه (post-lead) — نیازمند مجموعه بعدی |

## ترتیب اجرای پیشنهادی (time-box: ۷ روز)

1. **روز ۱–۲:** P1 + P2 + P3 — کانال‌ها؛ بیشترین اثر روی طراحی Track A
2. **روز ۳–۴:** P5 + P10 — زیرساخت فانل و اندازه‌گیری؛ پیش‌نیاز اسپرینت
3. **روز ۵–۶:** P4 + P9 — محتوا و پایپ‌لاین
4. **روز ۷:** P6 + P7 + P8 — لایه nurture؛ اگر وقت نماند، هفته بعد

> `[OPINION]` برای استارت Track A همان P1، P2، P3، P10 کافی است؛ بقیه را می‌شود بعد از اولین سیگنال واقعی اجرا کرد — تله analysis paralysis (بخش ۶ master-reference) را تکرار نکنیم.
