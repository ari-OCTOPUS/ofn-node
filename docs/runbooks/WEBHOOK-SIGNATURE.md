# Runbook — شکست امضای وب‌هوک

**وقتی:** `POST /api/v1/webhooks/...` با ۴۰۳/۴۲۲ برمی‌گردد یا لاگ نشان می‌دهد
امضا پذیرفته نشده.

## وضعیت فعلی (صادقانه)
- هنوز هیچ vendor واقعی وصل نیست.
- مسیر وب‌هوک: tenant از path + cross-check با Host (mismatch → 403).
- **HMAC در مسیر زنده فعال نیست** — `webhook_verify: noop_until_vendor`.
  پنل مالک این را در observability نشان می‌دهد (vendors_connected خالی).

## وقتی vendor رسمی آمد
1. مستندات رسمی vendor: الگوریتم (sha256؟)، هدر امضا، ساختار timestamp.
2. secret را در `~/.config/ofn/*.env` بگذار — **هرگز در کد/گیت/لاگ**.
3. `webhook_verify.verify_with_header` را با پارامترهای vendor وصل کن.
4. freshness window (±۵ دقیقه) enforce کن (یافته ۱۰).
5. تست golden با payload واقعی vendor — هرگز با payload ساختگی.

## هشدار
- راز واقعی خوانده/چاپ نشود (NEVER_1).
- هیچ vendor ای بدون تأیید آری وصل نشود (NEVER_7، یافته H).
