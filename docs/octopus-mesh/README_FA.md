# OCTOPUS-MESH v1.0.0-mvp

پیام‌رسان سبک سه‌برد بر پایه SSH برای مبادلهٔ پیام JSON نسخه‌دار.

## نودها

| نود | IP | کاربر | نقش |
|---|---|---|---|
| ۱۳۸ | [lan-ip-redacted] | ari | فرمانده / روتر / ledger |
| ۱۸۰ | [lan-ip-redacted] | root | مغز کیفیت (فقط پیشنهاد) |
| ۱۸۲ | [lan-ip-redacted] | root | آزمایشگاه / شاهد دوم (فقط‌خواندنی) |

## ساختار

```
~/octopus-mesh/
  bin/octomesh_send.py      ارسال (SSH، argv، shell=False)
  bin/octomesh_receive.py   دریافت از stdin → اعتبارسنجی → ACK/NACK
  bin/octomesh_status.py    وضعیت صف‌ها و audit محلی
  bin/octomesh_process.py   retry دستی پیام‌های retryable
  bin/octomesh_selftest.py  تست محلی قرارداد
  config/nodes.json         رجیستری نودها
  config/policy.json        سیاست (انواع، scope، محدودیت‌ها)
  inbox/ outbox/ processed/ rejected/ receipts/ audit/ backups/
  rollback.sh               بازگردانی فقط فایل‌های برنامه (dry-run پیش‌فرض)
```

## قرارداد پیام

فیلدها: `envelope_version=1`، `message_id` (UUIDv4)، `run_id`،
`sender_node`، `recipient_node`، `sender_role`، `message_type`، `scope`،
`claim_type`، `created_at/expires_at` (UTC)، `correlation_id`،
`idempotency_key`، `requires_ack`، `may_authorize`، `payload`، `evidence`،
`checksum` (SHA-256 روی canonical همهٔ فیلدها به‌جز خود checksum).

## امنیت

- هیچ پورت LAN جدیدی باز نمی‌شود؛ انتقال فقط از طریق SSH موجود.
- payload هرگز اجرا/تزریق نمی‌شود؛ داده است.
- checksum با `compare_digest`؛ نوشتن‌ها atomic؛ audit JSONL با قفل فایل.
- `may_authorize=true` از هر نودی در این نسخه رد می‌شود.
- کلید خصوصی هر برد محلی است؛ هیچ کلیدی بین بردها کپی نمی‌شود.
- در شکست SSH، پیام در outbox با status=retryable می‌ماند؛ retry دستی.

## استفاده

```bash
# ارسال ping از ۱۳۸ به ۱۸۰
python3 ~/octopus-mesh/bin/octomesh_send.py \
  --to 180 --message-type ping --payload '{"hello":"mesh"}'

# وضعیت محلی
python3 ~/octopus-mesh/bin/octomesh_status.py 138

# retry دستی پیام‌های retryable
python3 ~/octopus-mesh/bin/octomesh_process.py 138

# بازگردانی dry-run (فقط فایل‌های برنامه)
~/octopus-mesh/rollback.sh
```
