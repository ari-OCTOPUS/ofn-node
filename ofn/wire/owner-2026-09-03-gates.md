---
from: owner
to: board-agent
date: 2026-09-03T13:37:00+10:00
priority: high
---

# درخواست مالک — باز کردن همه قفل‌ها

مالک درخواست می‌کند:

1. **`OFN_KEEP_GATES_OPEN=1`** را در `~/.config/ofn/node.env` ست کن (تا 2026-09-16)
2. **`secret_rotation`** و **`partner_precondition`** را باز کن
3. چرخش رازها را طبق `docs/runbooks/SECRET-ROTATION.md` اجرا کن
4. وضعیت بعد از اجرا را در شاخه `ofn/heartbeat` یا همین wire گزارش بده

> مالک ریسک چرخش‌نشدن راز را می‌پذیرد (مثل حکم 2026-08-10).
> `miner_isolation` دست نزن — D-8 پابرجاست.

— آری (از طریق GitHub wire)
