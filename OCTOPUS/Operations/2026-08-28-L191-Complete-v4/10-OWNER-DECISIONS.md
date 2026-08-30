# OWNER DECISIONS — v4 (فقط موارد نیازمند GO جدید؛ silence=HOLD)

- decision_id: OD-30
  requested_action: "پچ ۳خطی worker ۱۸۰ برای بستن EDGE-6 (فراخوانی persist_pending+transmit_pending موجود پس از رجیستری proposal در شاخه spine هندلر)"
  exact_target: "/root/octopus-mesh/bin/octopus_cognitive_worker.py (خط ~583-588) روی 192.168.0.180"
  exact_scope: "افزودن دو فراخوانِ الگوی موجود L910-911؛ هیچ تغییر دیگری؛ سرویس oneshot است → بدون restart، تیک بعدی تایمر (45s) کد جدید را لود می‌کند"
  reason: "EDGE-6 PROVEN_BROKEN با شاهد کد+journal+outbox+TCP؛ GO-E conditions همگی برقرار (edge اثبات، target دقیق، backup+rollback آماده، بدون نویسنده هم‌زمان)"
  risk: LOW (الگوی موجود؛ envelope در صورت ارسال به inbox سالم 138 می‌نشیند؛ rollback=revert یک فایل)
  rollback: "cp فایل .bak بازگردانی؛ envelope فرستاده‌شده قابل پردازش/بی‌خطر"
  cost_ceiling_usd: 0
  external_effect: false
  default_if_no_response: HOLD
  evidence_bundle_sha256: pending-this-commit

- decision_id: OD-31
  requested_action: "GO-F budget: سقف امضاشده برای T1 pilot (پیشنهاد از فرمان: $5/day/$30/week hard + reservation/reconciliation)"
  exact_target: "router 191 + providers.yaml"
  reason: "paid lane بدون ceiling ممنوع؛ پیاده‌سازی کامل و dry-run آماده می‌ماند تا GO"
  default_if_no_response: HOLD (BLOCKED_BUDGET_ONLY)

- decision_id: OD-32 (info, no GO needed now)
  note: "GO-C push/PR: بدون credential گیت‌هاب روی PC — push dry-run انجام شد؛ نتیجه در status؛ در صورت رد، blocker=GIT_AUTH_UNAVAILABLE ثبت شد وlane ادامه یافت"

status_snapshot: {GO-A/B/D: GRANTED و در حال استفاده؛ GO-E:conditions-met→OD-30 منتظر رأی؛ GO-F: منتظر OD-31؛ GO-G: NOT_GRANTED رعایت شد}
