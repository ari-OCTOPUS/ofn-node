---
id: mock-mode
aliases: [mock mode, حالت موک]
tags: [سیستم, #reference]
related: ["[[روتر-LLM]]"]
---
# 🟡 Mock Mode

> [!info] کار بدون API key
> وقتی `GLM_API_KEY` و `FUGU_API_KEY` تنظیم نشده‌اند، سیستم در mock mode کار می‌کند.

## رفتار

ایجنت‌ها با **قالب‌های آماده** پاسخ می‌دهند:

| trigger | پاسخِ mock |
|---|---|
| verify / anchor | لنگرها به‌صورتِ شبیه‌سازی‌شده PASS می‌شوند |
| shadow / detect | تشخیصِ الگو با اعدادِ پیش‌فرض |
| geometry / tesseract | تمثیلِ [[تسراکت-و-سایه|تسراکت]] و [[قضیه‌ی-Takens|Takens]] |
| report | report card با مقادیرِ کانونی |

## هدف

- تستِ UI بدون هزینه‌ی API
- توسعه‌ و دیباگِ pipeline
- تأییدِ ساختار قبل از فعال‌سازیِ واقعی

## فعال‌سازیِ واقعی

```bash
# .env
GLM_API_KEY=your-key
FUGU_API_KEY=your-key
MOCK_MODE=false
```

## کد
`4d_system/llm/router.py` → `MockClient`