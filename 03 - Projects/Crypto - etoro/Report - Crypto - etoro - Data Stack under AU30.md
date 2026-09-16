---
type: report
status: done
tags: [crypto, data, api]
created: 2026-07-04
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
updated: 2026-07-04
---

# Report - Crypto - etoro - Data Stack under AU$30/month (2026)

> Executed by scheduled research agent (Cowork) on 2026-07-04, from [[00 - Inbox/Prompt - Research Pack 7 Projects 2026-07-03|Research Pack]] — Crypto Prompt 1 (Deep). Aligned with decision D-25 (subscription-first, hard cap AU$30/mo). Vendor prices are **USD** as published; AUD conversion assumes ~0.65 USD/AUD → **[Unverified — check live rate; at this rate US$19.50 ≈ AU$30]**.

## 1. Provider comparison table

| Provider | Free tier | Cheapest paid (USD) | ≈AUD/mo | API on that tier? | Key metrics | 2025-26 changes / notes |
|---|---|---|---|---|---|---|
| LunarCrush | Limited app access | Individual ~$24/mo **[Unverified — pricing page JS-gated]** | ~A$37 ❌ over cap | API priced separately | Social volume, sentiment, Galaxy Score | [Pricing](https://lunarcrush.com/pricing/), [API pricing](https://lunarcrush.com/developers/pricing) |
| CryptoQuant | Very limited | Advanced $39/mo ($29 annual) | ~A$45–60 ❌ | No — Data API starts at Professional $109/mo | Exchange flows, miner flows, whale ratio | [Pricing](https://cryptoquant.com/pricing), [CaptainAltcoin review](https://captainaltcoin.com/cryptoquant-review/) |
| Santiment | Free metrics; restricted metrics have **last-30-days cut off**, 3 alerts | Sanbase Pro ~$44/mo | ~A$68 ❌ | Real-time API needs MAX plan | Social + on-chain + dev activity | 30-day lag makes free tier research-only, not tradeable — [Sanbase plans](https://academy.santiment.net/products-and-plans/sanbase-plans/), [SanAPI plans](https://academy.santiment.net/products-and-plans/sanapi-plans/) |
| Glassnode | Limited Studio | Advanced ~$26–39/mo **[sources conflict]** | ~A$40–60 ❌ | **No API on Advanced** (charts only) | HODL waves, SOPR, realized cap | [Studio pricing](https://studio.glassnode.com/pricing), [CaptainAltcoin](https://captainaltcoin.com/glassnode-review/) |
| CoinGlass | Good free web dashboards | API Hobbyist $29/mo (80+ endpoints, 30 req/min, personal use) | ~A$45 ❌ (API) / free web ✅ | Paid only | Funding rates, OI, liquidations, long/short ratio | [Pricing](https://www.coinglass.com/pricing), [Dev review](https://dev.to/great-time-flies/coinglass-api-review-2026-is-it-worth-it-for-crypto-quant-traders-2bcf) |
| Messari | Basic articles | **Lite & Pro RETIRED (2025) — Enterprise only, ~$6k–34k/yr** | ❌❌ | Enterprise | Research, unlocks, fundraising | Big change: no retail tier anymore — [Deprecation FAQ](https://docs.messari.io/user-guides/welcome/plan-deprecation-faq), [Pricing](https://messari.io/pricing) |
| CoinGecko API | **Demo: free, 10,000 calls/mo** | Analyst $129/mo (500/min) | Free tier ✅ | Yes (Demo key) | Prices, market caps, 2M+ tokens, historical | [API pricing](https://www.coingecko.com/en/api/pricing), [Rate limits](https://support.coingecko.com/hc/en-us/articles/4538771776153-What-is-the-rate-limit-for-CoinGecko-API-public-plan) |
| CoinMarketCap API | **Basic: free, 15,000 credits/mo** (1 credit ≈ 100 data points) | Paid tiers above | Free tier ✅ | Yes | Rankings, prices, listings | [API pricing](https://coinmarketcap.com/api/pricing/), [FAQ](https://coinmarketcap.com/api/faq/) |
| TradingView | Free: 3 alerts, no webhooks | Essential $12.95/mo (annual) — 20+20 alerts, **no webhooks**; Plus $24.95 — webhooks ✅ | Essential ~A$20 ✅ / Plus ~A$38 ❌ | Webhooks = Plus+ | Alerts on any chart/indicator | Essential/Plus alerts expire ~2 months — [Pricing](https://www.tradingview.com/pricing/), [Plan comparison](https://supa.is/article/tradingview-essential-vs-plus-vs-premium-which-plan-2026) |

**Blunt conclusion:** at a hard AU$30 cap, **every meaningful paid on-chain tier is over budget**. The viable strategy is a free-API stack plus at most one cheap alert tool.

## 2. ToS risk of scraping instead of paying

- Logged-in scraping (account + "I agree" = clickwrap) is enforceable breach of contract; *Meta v Bright Data* (2024) went Meta's way on logged-in scraping; consequences: account bans, IP blocks, C&D letters, civil claims. Sources: [Quinn Emanuel — legal landscape](https://www.quinnemanuel.com/the-firm/publications/the-legal-landscape-of-web-scraping/), [Apify — is scraping legal](https://blog.apify.com/is-web-scraping-legal/), [GroupBWT 2025 compliance guide](https://groupbwt.com/blog/is-web-scraping-legal/)
- Practical read for this project: scraping LunarCrush/CryptoQuant dashboards behind a login is exactly the clickwrap case — ban risk is real and the data pipeline becomes fragile. Public keyless endpoints are lower-risk but rate-limited and can change silently. **Recommendation: migrate anything scraped to the free official APIs (CoinGecko/CMC/CoinGlass web) — consistent with D-25.**

## 3. Recommended stack ≤ AU$30/month

| Layer | Tool | Cost |
|---|---|---|
| Prices/history API | CoinGecko Demo (10k calls/mo) | $0 |
| Backup prices + listings | CoinMarketCap Basic (15k credits/mo) | $0 |
| Derivatives dashboard (funding, OI, liquidations) | CoinGlass free web | $0 |
| Social/on-chain research (lagged 30d — research only) | Santiment free | $0 |
| Alerts | TradingView Essential (~A$20/mo annual) — accept no webhooks; re-arm alerts ~2-monthly | ~A$20 |
| **Total** | | **~A$20/mo ✅** |

Upgrade path (needs D-25 revision): first paid seat worth buying is CoinGlass Hobbyist API ($29 ≈ A$45) for funding/OI programmatically, or TradingView Plus for webhook automation. Nothing on-chain (CryptoQuant/Glassnode API) is accessible below ~US$100/mo.

## 4. Five weekly metrics with the strongest evidence

1. **Social sentiment at EXTREMES (not average sentiment)** — systematic review of 151 peer-reviewed studies (2018-24) supports short-horizon predictive power; Yale-affiliated work: social sentiment moves short-term returns where news sentiment barely does; newest work shows effects concentrate in extreme regimes. [MDPI systematic review](https://www.mdpi.com/2227-7072/13/2/87), [Blockworks on the study](https://blockworks.co/news/crypto-prices-sentiment-news), [arXiv — Extremity Premium](https://arxiv.org/pdf/2602.07018)
2. **Funding rates (mean-reversion at extremes)** — slight negative correlation with forward returns → contrarian signal; funding-rate levels themselves are forecastable (SSRN, DAR models); BIS documents the crypto carry structure. [Fulgur Ventures analysis](https://medium.com/@fulgur.ventures/bitcoin-funding-rates-and-price-predictability-27ce95535af1), [SSRN 5576424](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5576424), [BIS WP 1087 — Crypto carry](https://www.bis.org/publ/work1087.pdf)
3. **Whale transactions + exchange flows → VOLATILITY (not direction)** — peer-reviewed Transformer study forecasts Bitcoin volatility spikes from whale-alert + CryptoQuant features. Directional "netflow = bullish" claims are mostly vendor/media content, not academic. [arXiv 2211.08281](https://arxiv.org/pdf/2211.08281) vs marketing examples: [OKX Learn](https://www.okx.com/en-eu/learn/bitcoin-negative-netflow-whale-accumulation) **[marketing]**
4. **Twitter/X activity & sentiment for ALTCOIN short-term returns** — peer-reviewed evidence that altcoin returns are predictable from tweet activity/sentiment (effect decays fast; weekly use = screening, not timing). [PMC — Predicting altcoin returns](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6279012/), [Springer — Ethereum sentiment](https://link.springer.com/article/10.1057/s41260-025-00438-8)
5. **Sentiment-regime awareness (COVID-era heterogeneity)** — sentiment's effect on returns vs volatility differs by regime; treat all signals as regime-conditional. [PMC — differential influence during COVID-19](https://pmc.ncbi.nlm.nih.gov/articles/PMC9581699/)

**Marketing vs evidence flag:** vendor blogs (CryptoQuant/Glassnode/OKX "netflow means X") are directionally confident far beyond what peer-reviewed work supports. Academic support is strongest for (a) short-term social-sentiment effects, especially at extremes, and (b) volatility forecasting from whale/flow data. Long-horizon directional prediction from any single metric: weak.

## 5. Open items

- Confirm LunarCrush current Individual price + API quota directly (page is JS-rendered; number here is from a secondary FAQ) — **[Unverified]**.
- Confirm Glassnode Advanced current price (sources conflict $26 vs $39).
- AUD prices move with FX — re-check conversions before committing to any annual plan.
- eToro's own built-in data/ProCharts was out of scope this run; worth checking before paying for anything.
