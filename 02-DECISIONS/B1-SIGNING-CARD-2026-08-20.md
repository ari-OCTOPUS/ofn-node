---
type: proposal
status: SIGNED
owner_vote: APPROVED
signed_at: 2026-08-20T11:12+10:00
payload_sha256: e11f45e9a0913c066de99f0a25ee1b7aa1621c2a7929b817f48be4d5d9c72290
verify_result: Signature Verified Successfully
verify_method: openssl pkeyutl -verify -rawin (Ed25519 pure)
key_scope: owner_local_only
tags: [octopus, b1, signing]
created: 2026-08-20
updated: 2026-08-20
---

# کارت امضای B1 — SIGNED

decision_id: B1-SIGNING-CARD-2026-08-20
status: SIGNED
owner_vote: APPROVED
signed_at: 2026-08-20T11:12+10:00
covers:
  - B1_APPLIED_UNSIGNED (ledger `a4dc56931ca84044b754c7f1fecd0d77`)
  - B1_SAFETY_ROLLBACK_TO_30 (ledger `1219e24773944474b45c88badfc933b5`)
payload: `02-DECISIONS/B1-SIGNING-PAYLOAD-2026-08-20.json`
payload_sha256: `e11f45e9a0913c066de99f0a25ee1b7aa1621c2a7929b817f48be4d5d9c72290`
tip_at_record: n=12750 · `e101f7ce313f8cd9…`

> ایجنت کلید خصوصی را نمی‌خواند و `openssl pkeyutl -sign` را اجرا نمی‌کند.
> این کارت متن دقیق مراسم است. امضا = عمل مالک.

## آنچه امضا می‌شود

یک فایل JSON کانونی، نه بازنویسی تاریخ. هر دو رخداد بی‌امضای tip در یک payload می‌آیند تا پس از verify دیگر «دو رخداد بی‌امضا» نباشند — وضعیت‌شان `SIGNED_AFTER_THE_FACT` می‌شود، نه حذف از زنجیره.

`owner-key.enc` (بکاپ بقا، ۱۴۴ بایت) **همان PEM امضا نیست.** PEM امضا:

- private: `~\.octopus-signing\octopus-owner-ed25519-private.pem` (وجود، ۱۲۲ بایت، بایت خوانده نشد)
- public: `_ops\owner-signing\octopus-owner-ed25519-public.pem` (وجود، ۱۱۶ بایت)

فایلی با نام `generate-and-sign` روی دیسک **نیست.** مسیر تثبیت‌شدهٔ TCB: `4d_system/scripts/generate_trust_boundary.py` + `openssl pkeyutl`. B1 این مراسم **TCB manifest را تازه نمی‌کند** (`budgets.yaml` / ارز داخلی ≠ `trust-boundary.json`).

## فرمان مالک (عیناً، یک‌به‌یک)

در PowerShell، از `F:\backup`:

```powershell
if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
  $env:Path += ";C:\Program Files\Git\usr\bin"
}
cd F:\backup
$pay = "02-DECISIONS\B1-SIGNING-PAYLOAD-2026-08-20.json"
Get-FileHash $pay -Algorithm SHA256
# انتظار: E11F45E9A0913C066DE99F0A25EE1B7AA1621C2A7929B817F48BE4D5D9C72290

openssl pkeyutl -sign `
  -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" `
  -rawin -in $pay `
  -out "02-DECISIONS\B1-SIGNING-PAYLOAD-2026-08-20.json.sig"
if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED - stop"; exit 1 }

openssl pkeyutl -verify `
  -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" `
  -rawin -in $pay `
  -sigfile "02-DECISIONS\B1-SIGNING-PAYLOAD-2026-08-20.json.sig"
```

انتظار verify: `Signature Verified Successfully`

اسکریپت هم‌ارز: `_ops/owner-runbook/B1-SIGN-2026-08-20.ps1` — مالک اجرا کرد؛ ایجنت دوباره اجرا نکرد. verify عمومی 2026-08-20T11:15+10: `Signature Verified Successfully` · sig 64B mtime 11:12:12.

## پس از verify سبز (هنوز ریاستارت نه)

1. این کارت: `status: SIGNED` + تاریخ + «verify OK».
2. یک خط append به `phase-gates.jsonl` با `signature: VERIFIED` (بازنویسی خط 00:06:53 ممنوع).
3. بعد — و فقط بعد — freeze baseline ریاستارت (رسید DAILY-CAP §dry-run) و ریاستارت کنترل‌شده.

اگر hash فایل با `e11f45e9…` نخواند: **امضا نکن**؛ payload عوض شده.

## رأی

- [x] **امضا می‌کنم** — هر دو رخداد، پس از verify
- [ ] **رد** — B1 unsigned می‌ماند؛ rollback ۳۰ روی دیسک می‌ماند؛ ریاستارت همچنان قفل
- [ ] **فقط یکی:** ______ (نقص مراسم؛ توصیه نمی‌شود)

امضا: owner · تاریخ: 2026-08-20T11:12+10:00 · verify: Signature Verified Successfully
