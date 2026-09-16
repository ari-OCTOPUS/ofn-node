---
type: evidence
task: T47
tags: [octopus, t47, lease, live-a, directive-8]
created: 2026-08-20T14:50+10:00
created_by: agent B (ZCode) — session sess_1d388c34
authority: "[[../../02-DECISIONS/OWNER-DIRECTIVE-08-2026-08-20]] §۱"
lease_id: 8d7b0c413a704534a211db58c107be2d
---

# T47 — فعال‌سازی فیزیکی lease نویسنده

## چرخهٔ واقعی (خروجی خام ابزار، 2026-08-20 ~14:49 +10)

```json
ACQUIRE: {"status": "ACQUIRED", "schema": "octopus-writer-lease/1",
          "lease_id": "8d7b0c413a704534a211db58c107be2d",
          "agent_id": "agent-B-ZCode", "session_id": "sess_1d388c34",
          "acquired_at": 1787199748.897, "ttl_seconds": 1800,
          "scope": ["ledger", "evidence", "budgets", "state", "git"]}
RENEW  : {"status": "RENEWED", "renewed_at": 1787199749.024}
INSPECT: {"held": true, "expired": false, "age_s": 0.3}
```

- قفل فیزیکی: `_ops/state/locks/octopus-writer.lock` — در زمان این رسید **زنده و در
  دست agent-B** است؛ آزادسازی در پایان جلسهٔ کاری با رسید release ثبت می‌شود.
- پذیرش اجباری هر دو ایجنت: طبق §۱ دستور، خط
  `LEASE_ACCEPTED_BY_A — granted by OWNER-DIRECTIVE-08` در
  `00 - Inbox/AGENT_QUESTIONS.md` append شد.
- شرایط T43 برآورده: fail-closed (HOLD = read-only)، دامنهٔ کامل، TTL کوتاه + renew
  صریح، بایگانی stale/released (حذف صفر)، فیلدهای agent_id/session_id در هر رکورد.
- تست‌ها: ۶/۶ سبز (`_ops/tests/test_writer_lease.py`).

## حکم

```text
T47 LEASE ACTIVE : YES
LIVE-A = PASS    (T40 ✓ · T41 ✓ · T43 ✓ · T47 ✓)
```
