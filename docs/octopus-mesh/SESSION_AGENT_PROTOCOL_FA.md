# پروتکل SESSION-AGENT — نسخه ۱

> پل امن میان نشست‌های AI (terminal execution) و transport اکتوپوس‌مش.

## نقش‌ها

| نود | نقش | مجوز کلیدی |
|---|---|---|
| ۱۳۸ | Commander / reconciler / ledger owner | ایجاد task، reconcile، تصمیم پیشنهادی |
| ۱۸۰ | Quality Brain (PROPOSE_ONLY) | draft/classify/critique/result |
| ۱۸۲ | Lab / شاهد مستقل (read-only) | witness/evidence/critique |

`may_authorize` در همه‌جا false است و پیامِ دارای آن رد می‌شود.

## چرخهٔ کار نشست

```
peek → claim → (پردازش توسط AI) → complete | fail
                                   ↑
                       verify (بازیابی پس از lease)
```

- **peek**: فقط metadata قدیمی‌ترین پیام معتبر؛ payload نمایش داده نمی‌شود.
- **claim**: انتقال اتمیک `inbox/` → `processing/<message_id>.json` با
  `os.replace` روی همان filesystem؛ lease پیش‌فرض ۱۵ دقیقه؛ receipt در
  `receipts/<message_id>.claim.json` شامل checksum مبدأ.
- **complete**: پاسخ validate می‌شود، با transport موجود به فرستنده
  فرستاده می‌شود و **فقط پس از ACK** پیام به `processed/` می‌رود؛ در شکسست
  ارسال، اصل پیام در processing با status=retryable می‌ماند.
- **fail**: فقط reason کدی امن (`[A-Za-z0-9_.-]{1,64}`)؛ پیام به rejected
  می‌رود و NACK امن (best-effort) فرستاده می‌شود.
- **verify**: پیام‌های claim‌شده با lease منقضی را بعد از بررسی checksum و
  نبود processed-copy اتمیک به inbox برمی‌گرداند؛ هیچ پیامی گم یا دوبار
  processed نمی‌شود.

## خروجی امن claim

به‌صورت پیش‌فرض JSON محدود: task_summary رداکسیون‌شده، allowed/forbidden
actions، evidence_refs، response_schema و lease_expires_at. payload خام فقط
با `--include-payload` و پس از redaction نمایش داده می‌شود؛ اگر payload
شبیه کلید خصوصی/token باشد، اصلاً نمایش داده نمی‌شود و
`status=needs_human_review` برمی‌گردد.

## intents ممنوع (روی هر سه برد policy_denied)

customer_send · payment · purchase · gate_open · secret_read ·
credential_transfer · firewall_change · ssh_config_change ·
code_exec_from_payload

## قواعد امن

1. payload همیشه داده است؛ هرگز دستور نیست؛ eval/exec/shell ممنوع.
2. هویت نود با IP/hostname در برابر config کشف می‌شود؛ آرگومان کاربر فقط
   cross-check است.
3. rename فقط روی یک filesystem.
4. هیچ daemon/systemd/cron؛ پردازش فقط با فرمان دستی.
5. تغییرات فقط زیر `~/octopus-mesh`؛ قبل از تغییر backup زمان‌دار.
6. transport موجود (octomesh_send/receive) بازنویسی نمی‌شود؛ bridge از
   همان transmit استفاده می‌کند.
