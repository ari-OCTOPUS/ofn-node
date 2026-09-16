# 01-RUNTIME-BASELINE — Cognitive Runtime (2026-08-12)

## روش

۲۰ درخواست in-process (بدون شبکه/مدل) روی مسیر conversation.handle → deterministic.

## نتایج

| # | دسته | سؤال | kind | latency |
|---|------|------|------|---------|
| 1 | short | سلام | intro | 13.9ms |
| 2 | short | چطوری | intro | 0.7ms |
| 3 | short | هدف چیست؟ | goal | 220.1ms |
| 4 | short | وضعیت چیست؟ | runtime | 0.0ms |
| 5 | short | موانع چیست؟ | blockers | 0.0ms |
| 6 | self | از چی تشکیل شدی؟ | intro | 0.8ms |
| 7 | self | تو کی هستی؟ | intro | 0.7ms |
| 8 | self | راجب خودت چی میدونی | intro | 0.6ms |
| 9 | self | نقشه خودت رو بگو | selfmap | **16279.0ms** ⚠️ |
| 10 | arch | Pulse Arbiter به چی وصله؟ | architecture | 12.6ms |
| 11 | arch | PolicyGate کجای معماریه؟ | architecture | 0.4ms |
| 12 | eq | معادله BCM چیه؟ | equation | 33.0ms |
| 13 | eq | سیگما چه اثری دارد؟ | equation | 0.4ms |
| 14 | mem | درباره من چی میدونی؟ | memory | 0.0ms |
| 15 | mem | آخرین improve چی بود؟ | memory | 0.0ms |
| 16 | ev | شاهدت چیه؟ | evidence | 0.0ms |
| 17 | biz | مغز تجاری چه پیشنهادی دارد؟ | business | 0.2ms |
| 18 | eff | سرعت رو کم کن | effect | 97.9ms |
| 19 | gen | فوتبال چیه؟ | chat | 0.0ms |
| 20 | gen | پایتون چیه؟ | chat | 0.0ms |

## آمار

| معیار | مقدار |
|-------|-------|
| p50 | **0.6ms** |
| p95 | **16279.0ms** (selfmap outlier) |
| min | 0.0ms |
| max | 16279.0ms |
| timeout rate (deterministic) | **0%** |
| error rate | **0%** |

## تحلیل

1. **deterministic path عالی است** — p50=0.6ms، زیر ۱ms برای ۱۸ از ۲۰ سؤال.
2. **selfmap = 16.3s outlier** ⚠️ — `_selfmap_summary()` از `miniapp_state.get_selfmap_state()` می‌خواند که کند است. **بهینه‌سازی لازم**.
3. **goal = 220ms** — `status.current_goal()` از state می‌خواند؛ قابل قبول.
4. **effect = 98ms** — `limited_effect.evaluate()` از owner_verdicts می‌خواند؛ قابل قبول.
5. **model path (DeepSeek) در این baseline نیست** — در runtime واقعی ۲۰-۴۰s (طبق گزارش‌های قبلی).

## TTFT (Time To First Token)

- deterministic: **فوری** (< 1ms) — SSE لازم نیست.
- model-backed (chat/clarify → DeepSeek): **20-40s** تا اولین token.
- **SSE برای model path ارزش دارد**؛ برای deterministic نه.

## تصمیم TDR اولیه

| فناوری | مشکل واقعی | تصمیم |
|--------|-----------|-------|
| SSE | model path 20-40s blocking | **TRIAL** (فقط model path) |
| WebSocket | نیازی به دوطرفه نیست (هنوز) | **DEFER** |
| FastAPI | ThreadingHTTPServer کار می‌کند | **DEFER** |
| NATS | single process کافی | **DEFER** |
| tiktoken | context management | **TRIAL** (budget) |
| ChromaDB | semantic retrieval (vault_bridge موجود) | **DEFER** (arm نشده) |
