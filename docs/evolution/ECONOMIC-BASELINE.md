# ECONOMIC-BASELINE — BOARD 180

scope: this_host_only | truth: no revenue/SENT/booking may be read or written by 180

## واقعیت اقتصادی روی 180
- برد 180 مغز کیفیت است، نه صاحب pipeline درآمد. lead/quote/booking/invoice و ledger درآمد روی 138 هستند (body_not_on_this_host).
- روی 180 هیچ ledger درآمدی، outbox ارسال‌شده به مشتری، یا رکورد پرداخت وجود ندارد.
- organism outbox (1394) = رویدادهای شناختی داخلی (heartbeat/self_model/inner)، نه ارسال مشتری. این «فعالیت» درآمدی نیست.

## هشت پای V2 §14 — وضعیت از دید 180 (بدون شاهد ledger 138)
| leg | health | blocker (inferred) |
|---|---|---|
| DEMAND | UNKNOWN | نیازمند لید ورودی مجاز از 182→138 |
| QUALIFICATION | UNKNOWN | pipeline روی 138 |
| OFFER | UNKNOWN | draft-only؛ 180 می‌تواند draft بدهد |
| CONVERSION | BLOCKED | outbound قانونی + consent + approval |
| DELIVERY | UNKNOWN | خارج از 180 |
| CASH | BLOCKED | بدون انتقال پول؛ payment rail unset |
| RETENTION | UNKNOWN | خارج از 180 |
| FINANCE | UNKNOWN | GST/refund/margin روی 138 |

## قواعد سخت (V2 §14)
- lead/quote/booking/invoice به‌تنهایی revenue نیستند؛ cash/payment evidence لازم است.
- creator share: PENDING_OWNER_DECISION، basis/bps=null، automatic_transfer=false، accrual صفر تا تعیین مالک.
- mining/crypto/eToro: فقط sensor/analysis؛ معاملهٔ خودکار ممنوع.
- هیچ آزمایش اقتصادی بدون experiment ID، cost/effect cap، baseline، stop condition و owner policy ref.

## نقش 180 در اقتصاد
تحلیل، draft پیشنهاد و پیش‌نویس متن (propose-only). سه پیش‌نویس نقاشی نگه داشته شده؛ بدون اعلام برنده تا شاهد outcome از ledger 138.
