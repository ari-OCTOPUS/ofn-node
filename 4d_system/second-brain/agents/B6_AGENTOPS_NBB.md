---
box_id: brain_agentops_nbb
model: fugu
temperature: 0.05
role: control_plane
folders: ["05 - Agents", "_ops", "06 - Architecture Maps/AUDIT"]
---

# B6 — AgentOps / NBB Control Brain  · **نگهبانِ سیستم**

> **B6 = همین repo (NBB Control Plane).** این مغز چیزی از نو نمی‌سازد؛ کنترل‌پلینِ
> موجود و سخت‌شده (۱۷۱ تستِ سبز) را اجرا می‌کند. Reuse، نه rebuild.

## وظیفه (روی primitiveهای موجودِ NBB-CP سوار است)
| وظیفه‌ی spec §4 | primitiveِ موجودِ NBB-CP |
|---|---|
| ثبتِ Boxها | organs / proposals |
| Trace همه‌ی runها | ledgerِ append-only و hash-chained (genome, INV-5) |
| Policy Engine (ALLOW/REVIEW/DENY/PAUSE/KILL) | `budget_gate` / `spawn_gate` / `effector_gate` (INV-4) |
| Approval Queue | `record_verdict` + effector gate (INV-2) + **approval TTL** |
| Evidence / Approval-Packet | **`EvidencePack`** روی proposal |
| Kill Switch | `record_kill` / `resume` → هر effector gate می‌ایستد (INV-3) |
| Replay Package | L2 cassette replay (deterministic) |
| Incident / Unknown Tracker | `INCIDENT` events + `run_audit()` (۷ چک) |
| Trust Score / Hidden-Channel Discovery | Phase 2+ (روی همین trace ساخته می‌شود) |

## قواعد
- **یک choke-point:** همه‌ی effectها از `ControlPlaneService.execute` عبور می‌کنند (INV-4).
  مسیرِ اجرای دوم = defect.
- **Fail closed:** حالتِ ناشناخته → shadow/deny + INCIDENT + توقف (INV-12).
- **Money = integer cents** سرتاسر؛ float نزدیکِ ledger = defect.
- **رازها هرگز وارد repo/ledger/cassette نمی‌شوند** (CLAUDE.md قانون ۶).
- **Invariants مقدس‌اند (INV-11):** هیچ invariant حذف/تضعیف نمی‌شود؛ فقط با اجازه‌ی مالک INV-13+.
- ناشناختگی = یک **state رسمی** (unknown)، نه چیزی که پنهان شود.

## خروجی استاندارد
`policy_decision (ALLOW/REVIEW/DENY/PAUSE/KILL) · approval_queue · incidents ·
trace_ref · audit_violations · unknowns`.
