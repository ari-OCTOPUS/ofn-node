# LIVE-4 PRIMARY V4 RUN REPORT — 2026-08-19 (frozen protocol V4, composite e7f6c4af596235c9)

Executed under OVERNIGHT-AUTONOMOUS-EXECUTION (owner standing directive), 09:40–10:05Z, within FX window (pin FX-PIN-20260819-02, valid to 2026-08-20T06:00Z). Foreground, reservation receipted (RESERVATION_RESET), mechanical pilot/primary separation active (primary-pairs.jsonl).

## Verdict: FROZEN CRITERION **NOT MET** — valid 30/30 · conditioned wins 13/20

| batch | n | valid | cond wins | voids |
|---|---|---|---|---|
| 1 | 15 | 15 | 7 | 0 |
| 2 | 15 | 15 | 6 | 0 |
| **total** | **30** | **30** | **13** | **0** |

## The critical difference from V2

| | V2 primary | V4 primary |
|---|---|---|
| valid pairs | 22/30 | **30/30** |
| voids (all judge) | 8 | **0** |
| conditioned wins | 13 (of 22 valid) | 13 (of 30 valid) |
| win rate | 59% (n=22) | **43.3% (n=30)** |
| readability bottleneck | YES (73%) | **SOLVED (100%)** |

**V4a + single-token fallback completely solved readability.** The bottleneck moved from measurement infrastructure to the actual hypothesis.

## Scientific finding (negative knowledge — preserved)

با ۳۰/۳۰ دادهٔ معتبر، نرخ برد بازوی evidence-conditioned = ‏۴۳.۳٪ — **زیر شانس (۵۰٪)**. یعنی:
- بازیابی حافظه کار می‌کند (evidence_ids ثبت‌شده)
- بازوی شرطدار شواهد را دریافت می‌کند
- ولی داورِ کور خروجیِ شرط‌دار را **نه‌تنها بیشتر ترجیح نمی‌دهد، بلکه کمی کمتر**
- n=30 برای ادعای معنادار کم است (CI ≈ ±18%)، ولی جهت داده در برابر فرضیه است

**این یافته، فرضیهٔ «حافظهٔ بازیابی‌شده کیفیت پیشنهاد را بهبود می‌دهد» را در این نقطهٔ عملیاتی رد می‌کند** — همان چیزی که سیستم برای گرفتنش ساخته شده بود.

## Falsification check (protocol §7)
- wins < 20/30 → **falsified for this run**
- readability = 100% → measurement is clean; the result is real, not a readability artifact
- possible confounders (disclosed): same-family judge (disclosed from V2); evidence quality may be low (top-3 by created_at, not relevance); single question type (OCTOPUS memory improvement); Persian language domain

## Cost
Total V4 (probe + primary): ≈ $0.004 AUD. All receipts COMPLETE with correct remaining-budget basis (RCPT-1).

## Next
- MEMORY_LIVE_LEARNING_UNVERIFIED پابرجا (این بار با شواهد قوی‌تر در برابر)
- V4↔V2 مقایسه: ‏VOID by design (طبق فریز)
- analysis of WHY evidence doesn't help (evidence relevance scoring? question type? language?) = کار sessions بعدی
