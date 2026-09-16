---
type: prompt
status: active
tags: [research, prompts, all-projects]
created: 2026-07-03
updated: 2026-07-03
---

# Prompt Pack — دو پرامپت تحقیقاتی برای هر پروژه

> **نحوه استفاده:** پرامپت ۱ هر پروژه برای Deep Research (ChatGPT/Gemini)، پرامپت ۲ برای چت معمولی با وب‌سرچ. خروجی هر اجرا را به‌صورت md با اسم `Report - <پروژه> - <موضوع>.md` در `00 - Inbox` بگذار تا جلسه بعد پردازش شود.
> **⚠️ امنیت:** این پرامپت‌ها عمداً بدون secret، مسیر vault و هویت (Project-F فقط با توصیف generic) نوشته شده‌اند — چیزی به آنها اضافه نکن.

---

## ۱) Lead-نقاشی

### پرامپت ۱ — نقشه کانال‌های لیدگیری سیدنی (Deep)

```text
Act as a growth strategist for a small owner-operated residential painting business in Sydney, Australia. Produce a comprehensive 2026 comparison of every viable lead-generation channel for painters in Sydney: hipages, Airtasker, ServiceSeeking, Oneflare, Google Local Services Ads (current AU availability), Google Ads, Meta lead ads, Google Business Profile / local SEO, strata & property-manager referrals, builder partnerships, and letterbox/local tactics. For EACH channel report: how it works, typical cost per lead in AUD, lead quality and win-rate reported by tradies, effort to run, and any 2025–2026 changes (pricing, policy, algorithm). Include 2–3 short case studies of AU painting/trade businesses that scaled leads successfully. Output: (1) a markdown comparison table, (2) a ranked channel mix for a solo painter with a small budget, (3) a 90-day action plan. Cite sources with URLs for every claim; mark anything unverified.
```

### پرامپت ۲ — Speed-to-lead و اتومیشن تبدیل (سبک)

```text
For trade businesses (painting, AU market): what measurably increases quote-win rates in 2026? Answer with evidence and sources: (1) speed-to-lead statistics — how much does responding in <5 min vs 1 hour change conversion; (2) missed-call text-back and AI receptionist tools suitable for a solo tradie — names, AUD pricing, AU phone support; (3) Google review velocity impact on local ranking; (4) quote follow-up sequences that work. Output: 5 ranked tactics with the evidence behind each, plus a tool shortlist with monthly cost in AUD.
```

---

## ۲) Mining

### پرامپت ۱ — کوین‌های قابل ماین روی RK3588 + پلی‌بوک شکار کوین جدید (Deep)

```text
I run a small mining experiment on an Orange Pi 5 Pro (Rockchip RK3588, 8-core ARM, ~10–15W). Research the 2026 landscape of CPU/ARM-mineable coins viable on this board: RandomX coins (Monero, Zephyr, others), VerusHash 2.2 (Verus — known ARM-efficient), Yespower/Ghostrider family, and any 2025–2026 newcomers. For each coin: algorithm, REAL benchmarked hashrate on RK3588 or comparable ARM SoCs (cite the benchmark source — do not estimate), power draw, method to compute daily revenue, mining software that compiles on ARM64, and pools with low minimum payouts. Then build an "early coin hunting" playbook: where new mineable coin launches are announced (Bitcointalk ANN, miningpoolstats.stream, GitHub, Discords), how to qualify a launch in under 30 minutes, and red flags for scams/instamines. Output: two markdown tables (established coins; launch-monitoring playbook) + source URLs. Mark every number that lacks a real ARM benchmark as [Unverified].
```

### پرامپت ۲ — نقش ESP32 در ریگ (سبک)

```text
What useful roles can ESP32 boards realistically play in a small crypto-mining setup in 2026? Cover with sources: (1) NerdMiner-style Bitcoin solo "lottery" mining — realistic odds math; (2) Duino-Coin — current state and payout reality; (3) rig monitoring/watchdog — temperature, hashrate, auto-restart via relay + MQTT; (4) remote power control of SBC boards. For each: is it worth doing, hardware needed, realistic expectation, and a link to the best guide/firmware. Output: short verdict table.
```

---

## ۳) Crypto - etoro

### پرامپت ۱ — استک دیتای کریپتو زیر AU$30/ماه (Deep)

```text
I am a solo crypto/stock investor on eToro with a hard budget cap of AU$30/month for data APIs and subscriptions. Compare the 2026 offerings of: LunarCrush, CryptoQuant, Santiment, Glassnode, CoinGlass, Messari, CoinGecko API, CoinMarketCap API, and TradingView alerts/webhooks. For each: free tier limits, cheapest paid tier in AUD, API rate limits, key metrics offered, and terms-of-service risk if scraped instead of paid. Then review the evidence: which metric families have DOCUMENTED predictive value for crypto prices (peer-reviewed or rigorous backtests — social sentiment, exchange flows, funding rates, whale activity)? Output: (1) comparison table, (2) a recommended stack that stays under AU$30/month, (3) the 5 weekly metrics with the strongest evidence, each with the study/source cited. Flag marketing claims vs independent evidence.
```

### پرامپت ۲ — واقعیت‌های eToro برای سرمایه‌گذار استرالیایی (سبک)

```text
Fact-check eToro for an Australian retail investor in 2026, with sources: (1) current fee structure — crypto spreads, stock commissions, FX conversion, withdrawal fees in AUD; (2) which assets are real vs CFD for AU accounts; (3) what tax reports eToro provides and how the ATO treats eToro crypto and stock gains (CGT events, records needed); (4) custody/counterparty risks and AU regulatory status; (5) evidence on copy-trading performance. Output: one-page fact sheet, each claim with a URL.
```

---

## ۴) Accounting

### پرامپت ۱ — نقشه کامل تعهدات مالیاتی FY2025-26 (Deep)

```text
Build a complete Australian tax and compliance map for a NSW-based sole trader whose main income is a residential painting business, with side income from: a small online gift shop, crypto investing (eToro) and small-scale crypto mining, and digital content subscription platforms. For FY2025-26 and FY2026-27, cover with ATO source links: ABN vs company structure trade-offs at this scale; GST registration ($75k threshold) and BAS cycles; PAYG instalments; painter/tradie deductions (vehicle, tools, home office, licence); how the ATO treats crypto mining (hobby vs business) and crypto CGT record-keeping; how income from foreign platforms (eToro, content subscriptions) must be declared; super contributions for sole traders; NSW painter licensing thresholds. Output: (1) obligation checklist grouped by business line, (2) a deadline calendar table for FY2026-27, (3) record-keeping requirements list. Cite ato.gov.au pages for every rule.
```

### پرامپت ۲ — نرم‌افزار حسابداری برای میکروبیزنس استرالیایی (سبک)

```text
Compare 2026 accounting software for an Australian micro-business (sole trader, multiple small income streams, budget-sensitive): Xero, MYOB, QuickBooks AU, Hnry, Rounded, and any solid free option. For each: cheapest AUD plan, bank feed quality with AU banks, receipt OCR, BAS/GST lodgment support, invoice features, and API access for automation agents. Output: comparison table + one recommendation under AU$30/month with reasoning.
```

---

## ۵) Ziman Galerry

### پرامپت ۱ — پلی‌بوک لانچ بیزنس آنلاین محلی سیدنی (Deep)

```text
Act as a go-to-market strategist for a small Sydney-based online gift/gallery brand in 2026 with a launch budget under AU$500. Research and compare: (1) marketplaces — Etsy, eBay AU, Amazon AU, Facebook Marketplace vs own Shopify store: fee tables, AU buyer traffic, discovery dynamics; (2) organic social — realistic Instagram Reels and TikTok reach rates for small AU product brands in 2025–2026, posting cadence evidence; (3) local channels — Sydney weekend markets and pop-ups (names, stall costs, application process), Google Business Profile for online-local hybrid; (4) AU consumer trends in gifts/art/handmade for 2025–2026. Output: channel comparison table with costs in AUD, a recommended launch mix, and a 90-day plan with weekly actions. Cite sources; separate data from opinion.
```

### پرامپت ۲ — کیس‌استادی‌های برند کوچک با ویدیوی کوتاه (سبک)

```text
Find 8–10 documented case studies (2024–2026) of small gift, art, or handmade brands that grew primarily through short-form video (TikTok/Reels). For each: niche, what content format actually drove sales (process videos, unboxing, storytelling, UGC), time to traction, and any numbers they disclosed. Then distill: the 5 content formats with the best evidence for product brands, and a realistic weekly content plan for a one-person brand. Include links to every case.
```

---

## ۶) اونلی فنز (Project-F)

### پرامپت ۱ — Track B: بانکداری، پرداخت و ساختار قانونی در استرالیا (Deep)

```text
Research the 2026 payments, banking, and legal landscape for an Australia-based faceless adult-content creator business on subscription platforms (OnlyFans, Fansly and alternatives). Cover with sources: (1) payout mechanics per platform — methods available to AU creators, fees, minimums, payout delays; (2) AU bank "de-risking" — which banks are reported friendly/hostile to adult-industry income, documented account-closure cases, mitigation strategies; (3) business structure — sole trader ABN vs company for this income, and the ATO's published guidance on OnlyFans/content income, GST applicability; (4) platform fee and rule comparison OnlyFans vs Fansly vs 2–3 alternatives, including how reliable per-country geo-blocking is on each platform and its limits (VPNs, leaks); (5) privacy practices — stage identity, address privacy, payment-name appearing on statements. Output: risk register table (risk / likelihood / mitigation), recommended banking + entity setup, and a list of open questions needing professional advice. Cite everything; no speculation without flagging it.
```

### پرامپت ۲ — Track C: ابزارهای اتومیشن و خطوط قرمز ToS (سبک)

```text
Map the 2026 tool landscape for managing a subscription-creator business (OnlyFans/Fansly): scheduling, CRM, mass-messaging, analytics, and AI-chat assistants (e.g., Supercreator and competitors). For each tool: pricing, what it automates, and — critically — what the platforms' current Terms of Service allow: AI chat disclosure rules, automation limits, and documented account-ban cases from tool misuse. Also summarize proven marketing funnels for faceless niche creators (Reddit/X strategies) at a high level. Output: tool comparison table + a "ToS red lines" checklist. Sources required.
```

---

## ۷) هیپنوتیزم و خودآگاهی

### پرامپت ۱ — تحقیق تاریخی: Cardew و حلقه New Thought سیدنی (Deep)

```text
Conduct a historical investigation into Henry Cardew and the Sydney "New Thought" circle, ~1898–1910s. Cardew was reportedly a former surveyor turned journalist in Sydney who published a sequence of metaphysical periodicals: The Metaphysician → Progressive Thought → Science of Life → Progressive Thinker, and printed affirmations (confirmed example: "I am fearless"). Using Trove (trove.nla.gov.au), State Library of NSW catalogue, NSW Births Deaths & Marriages index, WorldCat, National Archives of Australia RecordSearch, and academic literature (Jill Roe "Beyond Belief"; work by Alexandra Roginski): (1) establish Cardew's full name, birth/death dates, and fate after his periodicals stopped; (2) identify E. A. Pennock — nationality and other works; (3) find any Sydney New Thought societies, venues, or "mental science" classes and who ran them; (4) find legal/medical-board/quackery cases touching this circle; (5) assess whether his affirmations were original or reprinted from US New Thought sources (e.g., Larson). Output: a findings table (question / finding / source / confidence), a source log with URLs and library call numbers, and explicit "not found" entries where searches came up empty — absence of evidence is itself a finding.
```

### پرامپت ۲ — بریف شواهد: HRV × خودهیپنوتیزم (سبک)

```text
Summarize the 2020–2026 evidence on combining HRV biofeedback with self-hypnosis for stress, sleep, and self-regulation. Cover: (1) resonance-frequency breathing (~0.1 Hz) protocols and reported effect sizes; (2) any studies combining hypnosis/suggestion with HRV training; (3) accuracy of consumer sensors (Polar H10 chest strap vs wrist PPG) for HRV; (4) open-source tools for HRV analysis (e.g., Kubios alternatives, Python libraries). Then design a 4-week n-of-1 self-experiment: daily protocol, metrics, and how to judge success. Output: short evidence brief with citations + the experiment protocol.
```

---

## بعد از اجرا

- خروجی‌ها → `00 - Inbox` با پیشوند `Report -` → جلسه بعد دسته‌بندی و تزریق به PROJECT.md هر پروژه.
- اعداد ماینینگ فقط بعد از بنچ واقعی روی Orange Pi 5 از [Unverified] خارج می‌شوند (پیگیری باز HANDOFF).
