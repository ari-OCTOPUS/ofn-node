---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, reuse, ofn, cockpit-v2, no-rebuild]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[04 - Architect System/architect/PROJECT]]"
---

# REUSE-MAP — ممیزی اتصال، نه ساخت

**حکم:** STOP ALL NEW ARCHITECTURE IMPLEMENTATION.  
**ناظر این نشست:** board 180 / vault `F:\backup` · `vantage=this_host` · `scope=this_host_only` · `claim_type=observation` مگر صریح `inference`.  
**مشاهده:** 2026-08-29.  
**RUNTIME_CHANGES=0 · EXTERNAL_EFFECTS=0 · کد جدید=0.**

## ۱. سه درخت که نباید قاطی شوند

| درخت | نوک اندازه‌گیری‌شده | lineage | Cockpit V2 OFN | OwnerDecision / witness_mint / fake_executor |
|---|---|---|---|---|
| Vault زنده `F:\backup` | `c803dee` 2026-08-23 · `docs(evidence): receipt for the malformed-input DoS hardening` | `germline` `E:/germline/octopus.git` | **غایب** (فقط `_ops/tests/test_cockpit_v2.py` = کاکپیت ارگانیسم تلگرام) | **غایب** |
| GitHub `ari322/ofn-node` `main` | `388594e0` 2026-08-04 · پوستهٔ زیمان | خانوادهٔ ofn-node | غایب | غایب |
| شاخهٔ `ofn/cockpit-v2-20260827` | `6070f51` 2026-08-27 | descendant از `388594e0` | حاضر | غایب |
| شاخهٔ `integration/138-business-spine-20260828` | `6881337` 2026-08-28 | شامل 6070f51 + spine | حاضر | حاضر، **فقط تست/آداپتور** |
| runtime ۱۳۸ در ممیزی `f09681a` | `d3fb20c` روی `octopus/reconcile-138-20260827` · ofn.service از 2026-08-27T01:33Z | ofn-node | LIVE طبق audit (شیشه `/cockpit-v2/`) | **بعد از این commit** روی integration؛ در آن لحظه در runtime نبود |

`merge-base(c803dee, 7d8cb2f)` و `merge-base(c803dee, 6881337)` در آینهٔ سرشماری **خالی** است. این دو تاریخچه unrelatedاند. کپی vault را با ofn-node یکی فرض نکنید.

منبع آینه (خوانده شد، fetch تازه از GitHub این نشست انجام نشد):  
`C:\Users\Armin\.zcode\tmp\OCTOPUS-SYNC-CENSUS-v7-20260828\ofn-node-github-mirror.git`  
API عمومی `api.github.com/repos/ari322/ofn-node/commits/...` = **404** (خصوصی). سطح شواهد commitها: **LIVE_REPO** روی آینهٔ ۲۸ اوت، نه LIVE_RUNTIME امروز روی ۱۳۸.

## ۲. وضعیت هر جزء موجود

وضعیت‌ها فقط از فایل/آینه/شواهد قبلی. پروب تازه به ۱۳۸/۱۸۲ از این میزبان انجام نشد (`missing LAN port ≠ API absent`).

| جزء | مسیر / ref | وضعیت | شاهد |
|---|---|---|---|
| `CockpitV2ReadModel` | `ofn/adapters/cockpit_v2_read_model.py` @ `7d8cb2f` / `6881337` | **BRANCH_ONLY** نسبت به `main` و نسبت به vault `c803dee`؛ **LIVE_AND_USED** فقط اگر ۱۳۸ هنوز همان درخت M1 را serve کند (آخرین LIVE_RUNTIME: L191 2026-08-28، pid `1351408` از 2026-08-27 11:33 AEST) | `RESOURCES = ("status","nodes","legs","queue","audit","version")` · `SCHEMA_VERSION = "2.0"` · **۲۹۶۶ خط** در `6881337` (P1 log؛ ادعای ۲۹۶۶ تأیید شد) · صف V2 = mesh `message_id` نه `tenant:idem` |
| تست read-model | `tests/test_cockpit_v2_read_model.py` @ `7d8cb2f` | BRANCH_ONLY | ۲۳۴ خط محتوا |
| `GET /api/v2/owner/*` | `ofn/adapters/http_api.py` @ `af5c358` | BRANCH_ONLY روی main/vault؛ wired در `ofn/run.py` همان خانواده | `_OWNER_V2_PREFIX = "/api/v2/owner/"` · ETag/304 |
| `ofn/run.py` reader | @ `6881337` | **LIVE_NOT_USED** روی vault؛ روی ۱۳۸: load `CockpitV2ReadModel` **هست**، import `owner_decision`/`witness_mint`/`fake_executor` **نیست** | `git show 6881337:ofn/run.py` فقط `CockpitV2ReadModel` |
| پوسته RTL Cockpit V2 | `web/cockpit-v2/**` @ `2cebc55`+`9738e29`+`6070f51` | BRANCH_ONLY vs main/vault؛ read-only | `api.js`: فقط `GET` روی پنج path؛ `TypeError` اگر path خارج از allowlist |
| harness polling | `web/cockpit-v2/tests/polling.test.mjs` @ `6070f51` | BRANCH_ONLY | timeout / backoff / رد پاسخ دیررس |
| پنل legacy | `web/panel.html` + `POST /api/v1/decide` | **LIVE_AND_USED** در کد vault `c803dee` و در قرارداد ممیزی ۱۳۸ | `http_api.py:1284` · `node.owner_decide` → `outbox.approve_manual` |
| `OwnerReads` facade | `ofn/adapters/owner_reads.py` @ vault | LIVE_AND_USED (واگذار به Node) | `decide()` → `owner_decide` |
| `OwnerDecision` | `ofn/adapters/owner_decision.py` @ `6881337` only | **BRANCH_ONLY** · به HTTP/outbox/182 وصل نیست | ۱۲ فیلد؛ فقط روی `integration/138-business-spine-20260828` |
| `witness_mint.py` | @ `6881337` | BRANCH_ONLY | JSONL append-only در تست |
| `fake_executor.py` | @ `6881337` | BRANCH_ONLY | fail-closed gates؛ executor تولیدی نیست |
| `business_source_export.py` | @ `6881337` | BRANCH_ONLY | export بدون PII |
| Fake E2E ۳۷ تست | `tests/test_*` @ `6881337` | BRANCH_ONLY · GAP-2 ممیزی را به‌صورت **fake** بست | `docs/spine-138/E2E-FAKE-REPORT.md` |
| outbox / ledger OFN | `ofn/adapters/outbox.py` + `ledger.py` | LIVE_AND_USED در هر دو خانواده | sole egress اعلام‌شده |
| `*.bak-*` در `ofn/adapters` | پنج فایل روی درخت ۱۳۸ | **TRACKED_BACKUP_NOT_RUNTIME** | حذف نشد؛ scanner نباید آن‌ها را implementation فعال بگیرد |
| `alert.py` | vault + ofn | **LIVE_NOT_USED** به‌عنوان کارت تصمیم؛ shadow برای crash | docstring: فقط سرویس مرده؛ `OFN_ALERT_TELEGRAM` default off |
| telegram-bridge | unit روی ۱۳۸ | **DEAD** | `WHAT-IS-DEAD.md` @ `56e9369` |
| Owner Control API / `/api/control/v2` | — | **MISSING** به‌عنوان مسیر جدا؛ و **نباید ساخته شود** | هدف discovery: همان command surface موجود، نه API سوم |
| witness worker 182 | برد ۱۸۲ | LIVE به‌عنوان timer/oneshot (شواهد L191)؛ اتصال به این run = MISSING_CONNECTION | inbox/outbox اعداد ≠ mint ۱۳۸ |
| `octopus_verify_dispatcher.py` | `/home/ari/octopus-mesh/bin/` | **DISK_ONLY** (خارج از git ofn-node) | F-2 باز؛ این میزبان فایل را نخواند |
| کاکپیت ارگانیسم `_ops` | `_ops/budget/cockpit_readmodel.py` + `_ops/tests/test_cockpit_v2.py` | LIVE_AND_USED در vault · **DUPLICATE نام** با OFN Cockpit V2 | ۲۱ تست MiniApp؛ نه `CockpitV2ReadModel` |
| event ledger / receipts ارگانیسم | `_ops` + epistemics | LIVE در vault | موازی با ledger OFN؛ domain جدا |
| Temporal / LangGraph / DBOS | — | **نباید وارد شود** | هیچ شکاف proven برای framework موازی |

## ۳. مسیر approve موجود (کد واقعی، نه طرح)

```
legacy panel / OwnerReads
  → POST /api/v1/decide {id, approve, confirmed_twice}
  → Node.owner_decide
      kill-switch fail-closed
      outbox.approve_manual  (تأیید ≠ claim ≠ send)
      ledger.append VERDICT
  → return approved_manual
  → انسان: GET packet + POST complete (manual dispatch)
```

این مسیر **OwnerDecision / witness_mint / 182 / fake_executor را صدا نمی‌زند.**  
Cockpit V2 این مسیر را **نمی‌نویسد** (`api.js` فقط GET).

مسیر fake @ `6881337`:

```
business_source_export → transport fake → witness_mint
  → OwnerDecision → fake_executor → receipt JSONL
```

PASS در تست. **LIVE chain هنوز:** snapshot masked painting → 180 ACK؛ proposal 180 pending؛ EDGE-6 drain 180→138 = PROVEN_BROKEN (شواهد 2026-08-28).

## ۴. تصحیح اعداد (ضد hype داخلی)

| ادعا | حکم این ممیزی |
|---|---|
| read-model ۲۹۶۶ خط | **CONFIRMED** در P1: `len(splitlines())=2966` روی `6881337`. ۲۷۷۵ فقط خطوط غیرخالی بود. |
| ۵۱۰ خط تست اختصاصی | `test_cockpit_v2_read_model.py` = ۲۳۴ خط محتوا؛ بقیه در `test_cockpit_v2_*.py` پخش است. جمع ۵۱۰ را اینجا **UNVERIFIED** بگذار. |
| تست ۲۰۲۸ / ۲۰۶۵ / ۲۱۲۰ | فقط **۲۰۲۸ collected · ۲۰۱۷ pass · ۱ error · ۱۰ skip** در `f09681a` `138-TEST-REPORT.md` سند شده. بقیه واریانس discoveryاند — canonical نیست. |
| `/api/v2/owner` روی vault `c803dee` | **نیست.** `rg` روی `http_api.py` vault صفر.match |

## ۵. خروجی ماشین‌خوان

```
AUDIT_ID=OCTOPUS-REUSE-AUDIT-2026-08-29
VAULT_HEAD=c803dee
OFN_MAIN=388594e0
COCKPIT_V2_TIP=6070f51
SPINE_TIP=6881337
AUDIT_REF=f09681a
DISCOVERY_REF=56e9369
LAST_138_DEPLOY_DOCUMENTED=d3fb20c
NEW_SUBSYSTEMS=0
NEW_APIS=0
VERDICT=REUSE_ONLY
```
