---
type: evidence
status: active
tags: [octopus, signing, ceremony, t28]
created: 2026-08-20
updated: 2026-08-20
---

# مراسم امضای یک‌جا — T28 آماده، STOP

دستور مالک #۵ · فقط آماده‌سازی. **soak روشن نشد. openssl sign اجرا نشد. کلید لمس نشد.**

## Payloadها (immutable — بازنویسی ممنوع)

| Sig | فایل | SHA256 (lowercase hex) |
|---|---|---|
| A | `02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json` | `4c80264d2e3149e41c0600543be98d8cbd339364f360f13aca5318e29ff6a8a8` |
| B | `02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20.json` | `1aaa7d544a24d06c4c332dbcd5051b332c93147fc9f5735d409249af68981fa7` |

Canonical: UTF-8 no BOM · LF · sorted keys · indent=2 · trailing newline. تأیید مستقل: Python `hashlib.sha256` + `certutil -hashfile … SHA256`.

کارت A: [[../02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20]] — `AWAITING_OWNER_SIGNATURE` · حکم قفل: `ACCEPTED_FOR_SHADOW_WITH_CONDITIONS`. پیش‌نویس WAVE0 امضا نیست.

کارت B: [[../02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20]] — همچنان draft / `AWAITING_OWNER_SIGNATURE`. امضا ≠ اجرای K=9. شرط اجرا: `ONLY_AFTER_4H_SOAK_PASS`.

عمومی (فقط مسیر): `_ops/owner-signing/octopus-owner-ed25519-public.pem`  
خصوصی (فقط مالک): `~\.octopus-signing\octopus-owner-ed25519-private.pem`

## فرمان مالک (یک‌بار)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\backup\_ops\owner-runbook\SIGN-ALL-PENDING-2026-08-20.ps1"
```

انتظار اگر هر دو verify سبز: `ALL_SIGNATURES_VERIFIED`  
یک سبز + یک رد: `PARTIAL_SIGNATURE_FAILURE` → soak شروع نشود.

تک‌کارت: `SIGN-SHADOW-VERTICAL-SLICE-2026-08-20.ps1` · `SIGN-PRE-REG-K9-THREE-SEED-2026-08-20.ps1`

## STOP

T28 تمام. T29–T33 و soak چهارساعته را **شروع نکن** تا مالک خروجی wrapper را برگرداند. K=9 اجرا نشود. GAP-001 OPEN · D6 BETWEEN_RUN_VARIANCE · live_spine NOT_VERIFIED_BITEMPORAL · `executable=false`.
