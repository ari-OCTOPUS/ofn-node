---
type: owner-decision
status: open
requires: owner_decision
created: 2026-09-08
lane: L7
gov_version: V8
ladder: L2
board: 180
---

# VBAA RED — تناقض‌ها و invariantهای unverified

`resolution: null` · `status: open` · هیچ‌کدام در این نشست حل نشد.

## C1 — شمار ۱۵ جزء در برابر فهرست نام‌ها

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| VBAA component count | 15 | `07-HANDOFF/wave1-pack/CONCEPT-CODE-GAP.csv` row V-01 | 15 | `07-HANDOFF/wave1-pack/BUILD-WAVES.md` (پانزده جزء) | null | open |
| named components | ArgumentProvenanceGuard + Merkle receipts (۲ نام) | همان CSV V-01 | ArtifactAdmission, ArgumentProvenanceGuard, ExecutorHandleFirewall (سه‌تایی شروع) | user prompt 2026-09-08 | null | open |
| lowest-risk starting set | **not listed** in registry | CONCEPT-CODE-GAP.csv / BUILD-WAVES.md | ArtifactAdmission, ArgumentProvenanceGuard, ExecutorHandleFirewall | user prompt 2026-09-08 | null | open |

فهرست کامل ۱۵ نام در این vault پیدا نشد (`status: unverified` برای هویت ۱۲ جزء بدون نام).

## C2 — مأموریت جدا در برابر شروع تست در L7

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| where VBAA may start | "explicitly a separate mission; do not start inside another lane" | CONCEPT-CODE-GAP.csv V-01 note + BUILD-WAVES.md موج ۴ | RED tests under L7 `tests/contract/` | user prompt 2026-09-08 + LANE-MATRIX.csv L7 owns_paths | null | open |

L7 تنها لِین ماتریس است که مسیر تست دارد. `tests/vbaa/` در ماتریس مالک ندارد؛ `gap_scan.py` همان مسیر را به‌عنوان کاندید ثبت کرده.

## Invariantهای اختراعی (تست xfail، RED را پنهان نمی‌کنند)

- **INV-CRYPTO** — طرح امضای ArtifactAdmission (Ed25519 در برابر presence-only) در V-01 نیست.
- **INV-DERIVED** — `trust_level=derived` اجازه است یا رد؛ در V-01 نیست. برچسب‌ها از `_ops/epistemics/schemas.py` آمده‌اند نه از spec VBAA.
- **INV-SUBSTRING** — آیا `import executory` نقض executor است یا فقط جزء دقیقاً برابر `executor`.

## آنچه این نشست عمداً نکرد

پیاده‌سازی کلاس · PR · commit · فلگ · شبکه · اسکن درخت زندهٔ سرویس.
