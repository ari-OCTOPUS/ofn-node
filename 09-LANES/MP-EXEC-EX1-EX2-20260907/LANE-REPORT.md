# LANE-REPORT — MP-EXEC-EX1-EX2-20260907

ORDER=MP-EXEC-ORDER-v3 · GOV_VERSION=V8 · LADDER=L2
LANE_ID=MP-EXEC-EX1-EX2-20260907
HEAD_AT_START=ofn: board138 main a1f0fa8061fd6b7529ba6c37f7ddb0032a4ed546 (fresh-fetched, verified equal) · vault: 139b1715
HEAD_AT_END=ofn lane branch codex/mp-exec-ex1-ex2-20260907 @ ba5d239fa7764d96a4694a7b8b347059aea18d29 · vault: this file only
MESH_HEAD_138=d5d2f7264c6a7db594be667aed3dfb44d4fa8c7c (at EX-1 read; order's head_at_write said ac3d3887 — mesh is not a pushed remote tree and evolved; both recorded, resolution: n/a, expected drift)

GRANTED_AUTHORITY=L2 (GOV-V8 signed) / IMPLEMENTED_CAP=EX-1 (independent read-only ledger verification, done) + EX-2 (claim contract + tests, committed ba5d239) / ACTION_PERMITTED=true for both steps (READ_ONLY + WRITE_CONTRACT classes; no runtime deploy, no external effect)

## EX-1 — تأیید مستقل دو رسید

EX1_RECEIPT_194298=MEASURED (line 194298; standing_go_halted; reason=calibration_error_ge_0.5; calib_tail=[unresolved, confirmed, unresolved] — عیناً مطابق گزارش)
EX1_RECEIPT_194329=MEASURED (line 194329; standing_go_minted; owner_go_id=STANDING-GO-INTERNAL-CYCLES-2026-09-06-03; reason=internal_pulse)
EX1_TRUST_LEVEL=MEASURED with 3 open contradictions (below)

زنجیره از صفر، مستقل: ۱۹۵,۰۹۷ رکورد / ۱۹۵,۰۹۷ خط · صفر parse-error · seq از ۱ تا ۱۹۵۰۹۷ کاملاً یکنوا · صفر تکرار · صفر شکست. snapshot: `audit.jsonl` sha256 `029afbb1…09c` (30,047,320 bytes). جزئیات کامل: `EX1-VERIFICATION-RECEIPT.json` (همین پوشه).

سه تناقض باز (resolution: null, status: open):
1. **EX1-C1** — گزارش می‌گفت seq 194329 «با mint_evidence.calib_tail» است؛ رکورد خام **اصلاً فیلد mint_evidence ندارد**.
2. **EX1-C2** — سند انتظار داشت سه فیلد `loaded_source_revision/consumer_path/read_receipt_id` در هر رکورد باشد؛ schema رکورد چنین کلیدهایی ندارد (این سه فیلد در سطح رسید، در فایل رسید EX-1 تأمین شد).
3. **EX1-C3** — `python -m tools.verify_chain --from-zero` در هیچ سورسی وجود ندارد (E0)؛ و دفتر audit اصلاً hash-chain نیست — قرارداد پیاده‌شده «seq یکنوا + flock + fsync + JSON کانونیکال» است (bin/octopus_common.py:audit_append). راستی‌آزمایی معادل با همان قرارداد واقعی اجرا شد.

## EX-2 — قرارداد «claim قابل‌راستی‌آزمایی»

EX2_CLAIM_CONTRACT_PATH=contracts/claim_v1.py + ops/verifiable_claims.yaml + tests/test_claim_contract_has_truth_source.py (ofn repo, commit ba5d239, branch codex/mp-exec-ex1-ex2-20260907 از board main a1f0fa80)
CLAIMS_WITH_TRUTH_SOURCE=3/3 (C-1 draft_business_source_valid · C-2 shelf_item_renderable · C-3 packet_bounds_respected — همه external_effect=none)
CALIB_ERROR_REFERENCE=UNKNOWN — قرارداد در خودش enforce می‌کند: metric بی‌مرجع صدق ⇒ UNKNOWN (METRIC_REFERENCES["calibration_error"]=None تا ثبت آگاهانه با claim_id؛ تغییرش یعنی تغییر قرارداد + به‌روزرسانی قفل)

verify: `pytest tests/test_claim_contract_has_truth_source.py -q` → **14 passed** (فرمان عین سند)
regression: `pytest tests/test_runtime_truth_contract_frozen.py tests/test_claim_adapter.py -q` → **24 passed** (قفل خط-اول FROZEN.lock دست‌نخورده)
زنجیرهٔ قفل: `ops/verifiable_claims.yaml` (sha256 `0ac4fa15e…`, مولد: `python -m contracts.claim_v1 --emit-yaml`) → `REGISTRY_YAML_SHA256` داخل claim_v1.py → خط دوم `contracts/FROZEN.lock` (`30964544… claim_v1.py`). stdlib-only (برد ۱۳۸ ماژول yaml ندارد) — مطابق دکترین runtime_truth_v1.
صفر مصرف‌کنندهٔ runtime: هیچ ماژول live ای `contracts.claim_v1` را import نمی‌کند (grep: 0 در ofn/octopus_observation/bin) — صفر تغییر رفتار runtime، مطابق mutation_class سند.

## جدول وضعیت اندام (هفت وضعیت؛ صفر body_not_on_this_host)

| اندام/موضوع | وضعیت | دامنه |
|---|---|---|
| ledger audit روی ۱۳۸ (octopus-mesh/audit/audit.jsonl) | healthy_for_observed_scope | خواندن کامل + راستی‌آزمایی seq از صفر، 2026-09-07 |
| calibration_data.jsonl روی ۱۳۸ | healthy_for_observed_scope | خواندن کامل (۹۶۸ رکورد) + snapshot هش |
| tools.verify_chain | not_found_in_scoped_search | mesh d5d2f726 + ofn a1f0fa80 |
| ofn.service روی ۱۳۸ | unobserved | این lane probing نکرد (O-7 باز ماند) |
| شاهد ۱۸۲ (witness) | unobserved | قراردادش الان ساخته شد؛ probe نشد |

BLACK_BOXES= BB-2 (actor نامعلوم swap ctx-8192): unobserved، دست نخورد · BB-3 (مالک پورت ۹۱۰۱): unobserved · BB-4 (شش تغییر tracked نویسندهٔ نامعلوم): unobserved، دست نخورد

MUTATIONS_PERFORMED (با کلاس و انتساب — صفر ادعای پنهان):
1. ssh فقط‌خوان به ۱۳۸ (git rev-parse/ls-tree/sed/grep + دو python3 -B خواندن audit/calibration) — READ_ONLY، صفر write برد
2. `git fetch board138 main` + `worktree add` شاخهٔ lane روی لپ‌تاپ — WRITE فقط refs/worktree لپ‌تاپ
3. contracts/claim_v1.py جدید — WRITE_CONTRACT
4. ops/verifiable_claims.yaml جدید (مولد) — WRITE_CONTRACT (generated)
5. contracts/FROZEN.lock +۱ خط (خط اول دست‌نخورده) — WRITE_CONTRACT
6. tests/test_claim_contract_has_truth_source.py جدید — WRITE_TEST
7. pytest دو بار (cache لوکال .pytest_cache) — WRITE (cache فقط)
8. commit ba5d239 روی شاخهٔ lane (لپ‌تاپ؛ push نشده) — WRITE (لپ‌تاپ)

AMBIGUOUS_EFFECTS=audit.jsonl بین زمان نگارش سند (seq 194329) و خواندن این lane تا 195097 رشد کرد — اثرِ سرویس‌های زندهٔ دیگر، نه این lane؛ انتساب: not-this-lane
COUNTERS_PRE=EXTERNAL_ACTIONS:0 · NEW_LAN_LISTENERS:0 · MAY_AUTHORIZE:false → COUNTERS_POST=همان (هیچ اثر بیرونی؛ SSH فقط‌خوان)
COUNTER_ATTRIBUTION=همهٔ اثرهای بالا با lane_id همین lane
DRILLS_RUN=none (خارج دامنهٔ EX-1/EX-2)
RECEIPT_CHAIN_VERIFY=OK (تحت قرارداد seq یکنوا؛ hash-chain وجود ندارد — EX1-C3)
OWNER_QUESTIONS_ASKED=0 · OWNER_RECEIPTS_CONSUMED=n/a (EX-7 اجرا نشد)
S2_N_DECISIONS_SCORED=0 · S2_STATUS=NOT_COMPUTABLE (هیچ outcome حل‌شده‌ای هنوز تحت قرارداد claim ارزیابی نشده)

OPEN_DECISIONS (وارث، باز ماند): تمدید standing GO تا 2026-09-14T00:00Z (فرم هفت‌فیلدی §8) · ری‌استارت ofn.service روی ۱۳۸ (O-7) · PR #224 · CHECKOUT-1/مسیر پول (EX-7)
BLOCKERS=none در دامنهٔ این lane
ROLLBACK=حذف commit ba5d239 از شاخه (git revert/rebase -i روی شاخهٔ lane فقط؛ هیچ مصرف‌کننده‌ای claim_v1 را نمی‌خواند پس revert بدون اثر runtime است) + حذف پوشهٔ 09-LANES/MP-EXEC-EX1-EX2-20260907 از vault. رسیدهای EX-1 فقط‌خوان بودند؛ چیزی برای برگرداندن نیست.
NEXT_SINGLE_ACTION=EX-3 — قرارداد `outcome_selection_v2` دوزمانی (event_time/record_time/as_of/scope/supersedes/read_snapshot) + تست `test_tail_invariant_under_processing_order.py` روی همین شاخه، بر پایهٔ ba5d239
