---
id: diaconis-freedman
aliases: [Diaconis-Freedman, DF theorem, projection Gaussian]
tags: [هندسه, #theorem, ابعاد]
related: ["[[قضیه‌ی-شناسایی]]", "[[β-info-نه-β-det]]", "[[E-shadow]]"]
---
# Diaconis-Freedman

> [!info] سایه‌ی استاتیک کور است
> Persi Diaconis & David Freedman (1984) — اکثرِ projectionهای یک‌بعدیِ داده‌ی high-dim **تقریباً گاوسی** می‌شوند.

## قضیه

وقتی بعدِ p و تعدادِ نمونه‌ها n هر دو به بی‌نهایت برسند، توزیعِ تجربیِ اکثرِ projectionهای خطیِ یک‌بعدی از داده‌ی high-dim **به گاوسی همگرا** می‌شود (یا scale mixture از گاوسی).

## نتیجه‌ی معماری

> [!important] تک‌سایه generically کور است
> اگر یک موجود ۴D را به‌صورتِ **استاتیک** به ۳D projekt کنی، هیچ ردی از ساختارش باقی نمی‌ماند.
> β_det = 0 دقیقاً.## دو راهِ نجات

| راه | مکانیزم | در [[مدل-خطی-گاوسی|مدل SOG]] |
|---|---|---|
| **دینامیک** | محورِ زمان → [[قضیه‌ی-Takens|Takens]] embedding | [[E-shadow|E_shadow]] > 0 چون ρ≠0 |
| **چند‌پروجکشنِ ساختاردار** | Radon / tomography | [[ردون-و-توموگرافی]] |

## پل به شناسایی

> [!quote]
> قضیه‌ی [[قضیه‌ی-شناسایی]] (E_shadow > 0 ⟺ λρ≠0) دقیقاً بازآفرینیِ همین اصل است:
> **سایه‌ی استاتیک کور است؛ سایه‌ی پویا لو می‌دهد.**

## منابع
- Diaconis & Freedman (1984) — «Asymptotics of Graphical Projection Pursuit»
- [JSTOR](https://www.jstor.org/stable/2240961)
- [PMC review](https://pmc.ncbi.nlm.nih.gov/articles/PMC6140545/)