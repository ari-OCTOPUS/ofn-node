---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, legs, orange-pi, read-only, telemetry, chat]
created: 2026-08-13
updated: 2026-08-13
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[07 - Knowledge/شناخت-اختاپوس/43-PARALLEL-AGENT-INTEGRATION-CHAT-BRAIN-2026-08-13]]"
---

# ۴۵ — رصدِ فقط‌خواندنیِ بیزنس‌های برد (Orange Pi)

چشمِ ارشد روی لگ‌های عمومیِ برد — بدون فرمان، بدون loopback، بدون دور زدنِ auth.

- خواننده: `_ops/owner_console/legs_status.py` (GET همزمان، بدنه خوانده نمی‌شود، HTTPS-only + ردِ host خصوصی)
- intent چت: `kind=legs` در `conversation.py` — **قبل از** `_BUSINESS` تا «وضعیت بیزنس‌های برد» به مغز تجاریِ داخلی نرود
- مدل: `legs` به DeepSeek نمی‌رود (پینِ قطعی در `collaborator.py`) — HTTP 401 نباید «سالم» بازنویسی شود
- تستِ ثبت‌نشده در `run_all.py`: `_ops/tests/test_legs_status_reader.py`
- قرارداد قفل: `_LEGS` قبل از `_BUSINESS` · لوپ‌بک/LAN رد · redirect غیرعمومی همان لگ را می‌خواباند · `legs` به مدل نمی‌رود

## شاهدِ برد (2026-08-13)

- Bridge زنده نیست: unit `not-found`، چیزی روی `:8796` listen نمی‌کند، `OUTBOUND_ENABLED` فقط با `"1"` روشن می‌شود.
- چهار لگ همان چهارتاست (`panel` 8794 · `ziman` 8791 · `lead` 8792 · `studio` 8793). `app` و `hypno` به لیست اضافه نمی‌شوند.
- `/api/health` تله است (۴۰۱ → `_principal`). پینِ زنده: `/healthz` روی همان چهار هاست.
- **معنی ۲۰۰:** فقط پروسهٔ HTTP جواب می‌دهد — نه DB، نه بوت، نه کانکتور، نه سلامتِ کسب‌وکار. غیر۲۰۰ = همان لگ نرسید/غیرسالم. بدون fallback به `/` یا `/api/health`.
- چهار listener از یک سرویس `ofn`اند؛ افتادنِ هر چهار `/healthz` معمولاً مرگِ پروسه است. افتادنِ یکی از بیرون = مسیر عمومی آن هاست (تونل/DNS).
- GET عمومی به `/` و `/healthz` از نظر برد فرمان/تداخل نیست. POST / loopback / `:8796` / `/api/*` احرازنشده = فرمان.

عمداً ساخته نشد: Bridge ویندوزی موازی، مسیر فرمان، تماس با loopback برد.

**نیمهٔ فرمان شروع نمی‌شود مگر حکم صریح مالک.**

قفل سبز (۲۰۲۶-۰۸-۱۳، تأییدِ ارشد): برد تست/سندِ lock می‌نویسد — نه systemd، نه listener، نه outbound، نه `:8796` در تونل. GET بدون auth به `/api/v1/command` و `/api/v1/brain/ask` اگر ۴۰۱ شد یعنی تلهٔ `_principal` است، نه سطحِ فرمان. متنِ کاملِ cloudflared را در HANDOFF نگذار.

هر دو طرف روی رصد هم‌ترازند. مالک طرحِ قفل سبز را برای اجرا روی برد تأیید کرد.
