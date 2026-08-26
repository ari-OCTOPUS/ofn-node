# REPOSITORY-LINEAGE — BOARD 180

scope: this_host_only | vantage: local-disk | method: git read-only

## repos روی این میزبان
| path | branch | HEAD | remote | dirty | note |
|---|---|---|---|---|---|
| /opt/octopus/lab | feat/phase3-completion | 747c373 | NONE | 84 untracked | organism + phase3 tree |
| /opt/octopus/ofn-l4 | master | 08f9155 | NONE | (unknown) | L4 kernel/store/arbiter |
| /opt/octopus/research-intake | — | — | not a git repo | — | proto-organism artifacts |
| /root/octopus-mesh | — | — | not a git repo | — | session bridge transport |

## branches موجود در lab
- `feat/phase3-completion` (current, HEAD 747c373)
- `archive/board-life-001-50f31db`
- `experiment/board-life-001`

## آخرین ۱۲ کامیت lab
```
747c373 Record the blocked Wave 1 learning canary.
c6ecac0 Record the passing controlled growth canary.
9dc8ad8 Record the one-use capability canary transition.
2594e32 Add a gated local capability canary.
6525877 Accept a valid LAN token even immediately after an unauthenticated probe.
e2ced65 Harden GET purity and LAN token, and stop checkpoint watchers dying on receipt shape drift.
013ec54 Limit OCTOPUS_ALLOW_LIVE_SCHEMA to additive live migration, not every connect.
3dbd9b1 Add Memory Gate proof, new-skin manifest, and unexecuted live replacement gate.
320ac62 Wire Mandatory Memory Read through named decision paths with bitemporal filters.
5a10253 Record Phase 3 live baseline, Cellframe disk analysis, and SQLite backup receipt.
539d296 Record local commit hashes for the Phase 3 lab and OFN-L4 trees.
71d018a Record Phase 3 recoverability, memory gate, and local source freeze.
```

## verdict حقیقتِ lineage
- مخزن هدف سند V2 = `ari322/ofn-node`، اما هیچ remote روی 180 تنظیم نشده؛ push از 180 ناممکن است. مالک repo برای push، برد 138 است (صاحب pipeline/ledger).
- branchهای تاریخیِ ذکرشده در V2 §15 روی 180 وجود ندارند → DOCUMENTED، نه canonical محلی.
- کل ۸۴ فایل dirty از نوع untracked (`??`) هستند؛ هیچ فایل modified/deleted نیست → خطر بازنویسی تاریخ صفر. تغییرات این فاز additive و روی branch جدا خواهد بود.
