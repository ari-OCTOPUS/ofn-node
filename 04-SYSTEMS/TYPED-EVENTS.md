---
type: system-note
system: typed-events
created: 2026-08-15
updated: 2026-08-15 (خنثی‌سازی کاندیدها طبق رأی مالک NEW-1)
status: phantom-name
---

# TYPED-EVENTS — نامِ phantom

- این نام در گفتگو تولید شد، نه در مخزن. هیچ معادلی تعیین نمی‌شود (رأی مالک NEW-1، 2026-08-15) — جدول کاندیدهای قبلی همین‌جا حذف شد.
- ثبت رسمی: `PHANTOM-DOCUMENTS.md` (موتور octopus_sync، در `--apply`).
- واقعیتِ مستقل و بی‌ارتباط به این نام: سیستم رویداد hash-chain واقعاً در مخزن وجود دارد (`src/nbb_cp/kernel/events.py` — `canonical_json` + `LedgerEvent`) — اما این‌جا به‌عنوان «معادل TYPED-EVENTS» ثبت نمی‌شود چون چنین نگاشتی شواهد‌ساز است.
