---
id: llm-router
aliases: [روتر, LLM router, GLM, Fugu]
tags: [سیستم, #reference]
related: ["[[mock-mode]]", "[[Orchestrator]]"]
---
# 🔌 روترِ LLM

> [!info] مسیریابیِ درخواست‌ها به مدلِ مناسب
> - تحلیل / راستی‌آزمایی / ریاضی → **GLM**
> - خلاقیت / هندسه / تمثیل → **Fugu**
> - fallback اگر آفلاین → **Mock**

## جدولِ مسیریابی

| task | مدل |
|---|---|
| analysis | GLM |
| verify | GLM |
| math | GLM |
| report | GLM |
| orchestrate | GLM |
| geometry | Fugu |
| creative | Fugu |
| analogy | Fugu |

## fallback chain

```
preferred → other real → Mock
```

## وضعیت

```python
router.status  # {"glm": "online/offline", "fugu": "online/offline", "mode": "live/mock"}
```

## کلیدها

- `GLM_API_KEY` و `FUGU_API_KEY` در `.env`
- بدون کلید → [[mock-mode]]

## کد
`4d_system/llm/router.py` → `LLMRouter`