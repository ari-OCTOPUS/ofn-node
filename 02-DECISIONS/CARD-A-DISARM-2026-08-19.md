---
type: owner-decision-record
decision_id: CARD-A-DISARM
status: EXECUTED
owner_answer: "همین حالا disarm کن" (chat 2026-08-19 ~10:4x +10:00)
tags: [octopus, security, card-a, sh]
---
# CARD-A بسته شد — /sh غیرمسلح شد
اقدام: پرچم ACTIVATION-RAW-SHELL.flag به ACTIVUS-RAW-SHELL.flag.disarmed-<ts> آرشیو شد (حذف نشد).
گیت زنجیره‌ای موجود: _is_owner allowlist (fail-closed) + shell_capability fail-closed + deny-list §۰.
بازمسلح‌سازی: فقط خود مالک فایل پرچم را بازسازی کند (طبق D2 تا گیت دومرحله‌ای).
وضعیت جدید: /sh از این پس «🔴 ACTIVATION وجود ندارد» می‌گوید (fail-closed پیش‌فرض).
