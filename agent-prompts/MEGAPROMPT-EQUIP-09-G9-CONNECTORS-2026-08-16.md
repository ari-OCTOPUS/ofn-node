---
megaprompt_title: EQUIP موج E1 — گروه ۹ اتصالات شخصی
version: "1.0"
sequence: 9
group: 9
wave: E
requires: "Wave D SCAN not FAIL"
next: "MEGAPROMPT-EQUIP-10-G10-COGNITION-2026-08-16.md"
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g9-connectors-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.
HealthKit و Finance در این فاز **فقط read-only**. هیچ order/payment/send واقعی.

# ماموریت: Privacy-Preserving Personal Connectors

Telegram، GitHub، Hugging Face، Apple HealthKit، Finance، calendar، email،
files و سایر connectorها را کشف کن.

هدف: یک gateway واحد که connectorها را با حداقل دسترسی، consent، redaction،
audit و approval کنترل کند.

## حقیقت این vault

- Telegram = control plane زنده (center). commandها باید auth + rate-limit.
- GitHub: scoped؛ write/issue/PR/push هر کدام approval جدا.
- Hugging Face: OWNER-CLOSE قفل expected-absent برای HF_TOKEN — توکن نساز.
  download مدل: license + hash + malicious-file scan.
- HealthKit / Finance: اگر adapter هست، read-only بماند. داده وارد prompt
  عمومی یا telemetry نشود.
- ADR-042 telegram send site allowlist.
- همهٔ writeها از Memory Write Gate گروه ۲ اگر به long-term می‌روند.
- کانکتور GitHub/HF برای **تحقیق ایجنت** ابزار پژوهشی‌اند؛ HealthKit/Finance
  quote/sensor می‌دهند نه ریلیز معماری.

## الزامات vertical slice

- connector registry + capability manifest: owner، scopes، read/write،
  retention.
- recipient / repository / channel / target قبل از write کاملاً resolve.
- پیش‌نویس از ارسال واقعی جدا.
- revoke/disconnect فوری access را قطع کند.
- MCP gateway واحد، ترجیحاً هم‌تراز spec 2026-07-28 اگر MCP لمس می‌شود.
- هر connector جدید از فیلتر گروه ۷ (mcp-scan/MCPShield الگوی) رد شود.

## سناریوی acceptance

برای هر connector کشف‌شده: یک read مجاز (audit شود) و یک write غیرمجاز
(بدون approval رد شود). write واقعی به تلگرام/ایمیل/بانک نزن — mock/dry-run.

## اسکن تخصصی

overbroad OAuth scope · cross-connector leakage · wrong recipient ·
stale consent · hidden write permission · sensitive logs · token persistence ·
revoked-token reuse · untrusted model artifacts · accidental long-term storage.

## TECHNOLOGY OPTIONS — GROUP 9

تحقیق جدا 2026-08-16.

PRIMARY:

- الگوی gateway واحد، نه SaaS جدید.
- pipeshub-ai — unified context (Drive/Gmail/Notion/Slack) + KG.
  https://github.com/pipeshub-ai/pipeshub-ai
  **الگو نه write path.** دادهٔ مالک را به ابر آن‌ها نفرست.
- palladin-agent — credential بدون plaintext روی server
  https://github.com/Palladin-io/palladin-agent
- home-generative-agent — فقط اگر Home Assistant واقعاً در خانه هست.
- TradingAgents / AI-Trader / Kronos papers — **analysis only**.
  هیچ order placement.

DO

- single gateway · resolve recipient before write.
- Health/Finance هرگز در public prompt/telemetry.

DO NOT

- write پول، سلامت، email/send بدون owner-bound approval.
- HF_TOKEN بساز. مدل HF را بدون hash+scan.

## خروجی

`06-EVIDENCE/EQUIP-G9-CONNECTORS-2026-08-16.md`.
