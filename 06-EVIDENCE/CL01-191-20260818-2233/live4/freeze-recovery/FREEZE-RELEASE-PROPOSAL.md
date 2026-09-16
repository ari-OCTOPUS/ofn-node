# FREEZE-RELEASE-PROPOSAL — منتظر OWNER_APPROVES_FREEZE_RELEASE_AND_PAID_SMOKE
دستور پیشنهادی (بعد از تأیید تو، من اجرا می‌کنم):
  python -X utf8 -c "import sys; sys.path.insert(0,'_ops/budget'); import opslib; print(opslib.release_freeze('OWNER_APPROVES_FREEZE_RELEASE_AND_PAID_SMOKE'))"
اثر: FREEZE-RELEASE-RECEIPT.json نوشته می‌شود + flag به FREEZE.flag.released-<ts> آرشیو (حذف نمی‌شود)
سپس paid-smoke محدود: یک فراخوانی secondary/deepseek با سقف 0.001 دلار → انتظار: رسید کامل COST-OBS-1 (REPORTED، AUD با FX پین 1.4082523588) در cost-receipts.jsonl + paid-calls.jsonl
اگر smoke سبز شد: بازاجرای Live-4 (دو batch × ۱۵، آستانهٔ ۲۰ برد از ۳۰)
rollback: بازگرداندن flag آرشیو‌شده به نام اصلی (freeze همچنان برقرار) — بدون از دست رفتن هیچ state ای
