# Unified Decision Register

> Root IDs canonical هستند. local IDs alias/cross-link می‌شوند؛ تاریخ حذف نمی‌شود.

## Closed / effective
| ID | تصمیم | نتیجه | effective | evidence |
|---|---|---|---|---|
| VQ-ROOT-001 | نقش NBB نسبت به Architect/_ops | **A — Portable sibling / shadow-only** | 2026-07-12 | owner confirmation in current session |
| VQ-ROOT-002 | workspace فعال | **A — همین workspace** | 2026-07-11 | root queue |
| SEC-2026-07-06 | Security Gate rotation | **LIFTED** | 2026-07-06 | owner-provided Brain/HANDOFF context |

## Open — Critical Path
| ID | تصمیم | وضعیت | اثر |
|---|---|---|---|
| VQ-ROOT-003 | تصویب Registry/Risk baseline با اصلاحات | open | شرط activation baseline |
| VQ-MAP-001 | scan workspace پس از repair contract | open | inventory تازه |
| VQ-ACC-001..005 | ورودی‌های مالی پایه | open | Accounting readiness |
| VQ-4D-001 | run 30-day بعد readiness | open | research runtime |
| VQ-PF-001 | Gate 0 | open | هر outward action Project-F |

## Superseded / aliases
| Local ID | canonical | وضعیت |
|---|---|---|
| VQ-NBB-001 / NBB-V1 | VQ-ROOT-001 | superseded; local history retained |
| MAP-V1 | VQ-MAP-001 | alias |
| MAP-V2 | PMO evidence-label task | administrative, not policy verdict |
| ACC-V1..V10 | VQ-ACC family | local detail; root queue should link rather than duplicate semantics |
| LEAD-V* / ZIM-V* / 4D-V* | corresponding root family | local detail |

## Approval record minimum
`decision_id, approver, role, scope, artifact_hash/diff, issued_at, expires_at, action, rollback, evidence`

## Next decision only
`VQ-ROOT-003 = A/B/C` — تا پاسخ مالک open می‌ماند.
