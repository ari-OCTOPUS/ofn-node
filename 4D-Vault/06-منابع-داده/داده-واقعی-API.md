---
id: data-real
aliases: [داده واقعی, real data, API, Yahoo Finance, NOAA]
tags: [داده, #reference]
related: ["[[W1-Detector]]", "[[MOC-سیستم]]"]
---
# 🌐 داده‌ی واقعی (API)

> [!info] سری‌های زمانیِ واقعی از منابعِ رایگان (بدون key)

## منابع

| منبع | داده | نماد |
|---|---|---|
| Yahoo Finance | بازدهِ روزانه | ^GSPC (S&P 500)، BTC-USD، AAPL |
| NOAA / NCEI | دمای روزانه | Chicago O'Hare |

## fallback

اگر شبکه در دسترس نباشد، سیستم به‌صورت خودکار داده‌ی مصنوعیِ AR(1) تولید می‌کند.

## کد
`4d_system/data/real_api.py` → `fetch_yahoo_finance()`, `fetch_noaa_temperature()`