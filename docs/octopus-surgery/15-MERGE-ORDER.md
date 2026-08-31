# 15 — Merge order (owner ruling Q8, 2026-09-01)

Order: **#12 → #14 → #13 → #15 → #16 (after A/B/C) → close #1/#2/#3/#4**.

| PR | Branch | Base | Why it is here |
|---|---|---|---|
| #12 | docs/lineage-map-20260831 | main | Docs-first ruling; the lineage map other docs cite. Merged 2026-09-01. |
| #14 | docs/owner-queue-status-20260831 | main | Owner rulings record; docs-only. Merged 2026-09-01. |
| #13 | docs/accounting-recovery-34-20260831 | main | Docs-only accounting lock; after #14 so queue context exists first. Merged 2026-09-01. |
| #15 | docs/megaprompts-owner-ask-20260831 | main | Docs-only prompt pack; last of the docs wave. Merged 2026-09-01. |
| #16 | feat/s2b-claim-record-20260901 | main | Code. Merges only after lanes A/B/C land on its branch (stacked), then squash to keep linear history. |
| A | feat/s2b-A-claim-adapter | #16 branch | Fixes F1/F2/F3/F4/F9/F10/F11 in claim_record.py + adds claim_adapter. Blocking: B and C build on it. |
| B | feat/s2b-B-store-hardening | #16 branch | Store defects F6/F7/F8; after A (store reads claim_record). |
| C | feat/s2b-C-verifier-reach | #16 branch | Verifier reach F12/F13; after A, parallel to B. |
| #1 | audit/cursor-20260828 | main | CLOSED_SUPERSEDED — predates PR #11 reconciliation. |
| #2 | audit/zcode-20260828 | main | CLOSED_SUPERSEDED — same. |
| #3 | work/truth-record-20260830 | main | CLOSED_SUPERSEDED — content landed via PR #11. |
| #4 | work/r1-portability | main | CLOSED_SUPERSEDED — content landed via PR #11 squash. |
