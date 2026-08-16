# کارت صبحگاهی — 2026-08-17 (ایجنت شب‌کار: معمار ارشد)

> هر کارت: بله/نه. پچ‌ها و دستورات آماده‌اند؛ هیچ‌کدام بدون رأی شما اعمال نشده.

## کارت ۱ — گیت enabled() در approve/reject (C-026، مصوب، ولی فایل TCB است)

**چرا:** پیشنهادِ ساخته‌شده حین ON، بعد از OFF هم قابل تصمیم است؛ گیت دو خط آن را می‌بندد.
**چرا کارت ماند:** `brain/self_code.py` جزو ۱۴ فایل مرز اعتماد است — ویرایش بدون امضای مجدد = halt.
**سه قدم صبح (۲ دقیقه):**
```powershell
cd F:\backup
# ۱) اعمال پچ (daemon شاید موقتاً halt کند — عادی است)
git apply "00 - Inbox/PATCH-C026-self_code-enabled-gate.patch"
# ۲) بازتولید manifest
cd 4d_system; py scripts/generate_trust_boundary.py; cd ..
# ۳) امضا + وریفای
openssl pkeyutl -sign -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" -rawin -in "4d_system\config\trust-boundary.json" -out "4d_system\config\trust-boundary.json.sig"
openssl pkeyutl -verify -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" -rawin -in "4d_system\config\trust-boundary.json" -sigfile "4d_system\config\trust-boundary.json.sig"
```
**بعد:** دو تست xfail سخت‌گیر `test_seam_selfcode_gate_20260816.py` را به positive ارتقا ده (حذف نشانگر). rollback: `git checkout -- 4d_system/brain/self_code.py` + regen + sign.
