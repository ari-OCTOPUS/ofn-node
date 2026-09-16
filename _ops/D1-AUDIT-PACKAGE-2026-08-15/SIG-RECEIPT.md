# رسید امضا — MANIFEST بستهٔ D1

- **امضاکننده:** مالک (آرمین) — جفت‌کلید Ed25519 مورخ 2026-08-15
- **کلید عمومی:** `_ops/owner-signing/octopus-owner-ed25519-public.pem` · fingerprint: `2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2`
- **فایل امضاشده:** `MANIFEST.txt` (این بسته) · امضا: `MANIFEST.sig` (۶۴ بایت · sha256: `68fea6a4a62fbb8b…`)
- **زمان:** 2026-08-15 ~18:22 (local)
- **مجوز امضا (provenance):** ۷ رأی تایید در `OCTOPUS-DOCTOR/90-_meta/state/tg-inbox.jsonl` (مأموریت `owner-gate-sign-d1-manifest` ×۳ تایید از همان رأی‌دهنده) — رأی‌دهنده با `TELEGRAM_OWNER_CHAT_ID` تطبیق داده شد (boolean-verified) + دستور چتی مالک در نشست تفویضی. اجرای امضا: ایجنت تفویض‌شده با کلید خصوصیِ مقیمِ ماشین مالک (`~/.octopus-signing/`، بیرون از repo).

## راستی‌آزمایی عمومی (هر کسی، هر جا)

```
openssl pkeyutl -verify -pubin \
  -inkey octopus-owner-ed25519-public.pem \
  -rawin -in MANIFEST.txt -sigfile MANIFEST.sig
```

خروجی مورد انتظار: `Signature Verified Successfully`

## مرز

این امضا اصالتِ بسته را تضمین می‌کند؛ D1 همچنان تا اجرای ممیزِ مستقل «NOT_STARTED» است.
