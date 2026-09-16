---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, board-cp, orange-pi, command, gate0]
created: 2026-08-13
updated: 2026-08-13
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[07 - Knowledge/شناخت-اختاپوس/45-BOARD-LEGS-READONLY-READER-2026-08-13]]"
---

# ۴۶ — Control Plane ویندوز (board-pull) + بریف فاز ۲ برد

فاز ۱ روی ویندوز ساخته شد. فلگ `OCTOPUS_BOARD_CP` پیش‌فرض **۰**. Gate 0 باز است تا مالک `OCTOPUS_BOARD_CONTROL_URL` (HTTPS ویندوز-facing، نه ziman/lead/studio/panel/app) و Bearer را بگذارد. راز در این نوت نیست.

- صف: `_ops/board_cp/` — schema همان `octopus-bridge/octopus_bridge/models.py`
- چت: `kind=board-command` («به برد بگو») → enqueue، ارسال خام نیست
- مینی‌اپ: POST `/api/board/commands` (initData مالک) · GET `/api/board-cp/pull` + POST `/api/board-cp/ack` (Bearer برد)
- تاسک همیشه `owner_required`
- تستِ ثبت‌نشده: `_ops/tests/test_board_cp.py`
- رصد `/healthz` دست‌نخورده است

## بریف فاز ۲ — برای ایجنت تک‌نویسندۀ برد

این را ایجنت ویندوز پیاده نمی‌کند. قرارداد pull با فاز ۱ یکی است:

- `GET /api/board-cp/pull` + `POST /api/board-cp/ack` — Bearer جدا از initData مالک
- `CONTROL_URL` اگر host آن panel/ziman/lead/studio/app باشد رد
- kind → عملیات: ask=`ofn.ask` · status=`ofn.status.owner` · panel=`ofn.panel.act` · task=`ofn.task.start`
- مسیرهای واقعی OFN روی لوپ‌بک `:8794` (نه از ویندوز): `POST /api/v1/owner/ask` · `GET /api/v1/owner/brain` — نه `/api/v1/brain/ask`
- تونل به `127.0.0.1` می‌رسد؛ لوپ‌بک به‌تنهایی امن نیست — Bearer مالک‌ساخته اجباری
- listener `:8796` فقط loopback؛ تونل هرگز به ۸۷۹۶ نرود (قفل سبز بماند)
- `OUTBOUND_ENABLED=1` فقط وقتی CONTROL_URL ویندوز آماده است
- poll جدا از dispatch: اگر poll شکست خورد، صف خالی است؛ `ofn` زنده می‌ماند
- `admit()` bypass نشود
- GET بدون auth به هاست عمومی همچنان ۴۰۱ تله است نه ۲۰۰ِ فرمان
- تا حکم فاز ۳: outbound خاموش، CONTROL_URL خالی، systemd enable نه

## فاز ۳ — مسلح‌سازی (حکم جدا)

1. فلگ ویندوز `OCTOPUS_BOARD_CP=1` + pull پشت HTTPS مالک
2. برد outbound روشن + اولین فرمان زنده = `ask` یا `status` (نه تاسک)
3. receipt؛ بعد پنل؛ در آخر `task` با رأی تازه

قطعِ ویندوز = صف نمی‌رسد، نه مرگِ ofn.
