---
type: contract-fields
schema: deep-walk-contract-fields/1
experiment_id: deepwalk-20260829-discovery
captured_at_utc: 2026-08-29T06:45Z
purpose: فیلدهای واقعی قراردادهای proposal/witness/receipt برای نوشتن chaintest.py هم‌خوان با کد زنده
sources: |
  نمونه‌های زنده: 138 inbox (2 پیام)، 180 receipts/control (ack envelope)، 180 receipts/*.claim.json،
  182 state/witness/{verdicts,owner_control_receipts}.jsonl، 180 outbox/180-to-138-*.payload.json
  کد: 180 octopus_cognitive_worker.py، 138 ofn/adapters/{outbox,fake_executor}.py
  همه فقط-خواندنی؛ هیچ سندی از سیستم زنده تغییر نکرد.
---

# D3 — فیلدهای واقعی قراردادها (برای chaintest.py)

## ۰. هشدار مهم برای نویسنده chaintest

پاکت بین‌بردی واقعی **`envelope_version: 1`** است — نه proposal.v1/witness.v1/receipt.v1 پیشنهادی.
`chain_prev_hash` و `signature/signer_key_id` **در سیستم واقعی وجود ندارند**؛
یکپارچگی با `checksum`/`payload_sha256`/`source_checksum` تضمین می‌شود و exactly-once با
کلید اولیه‌ی `idempotency_key`. تستی که فیلد غایب بخواهد، مثل RED test قبلی fail خواهد شد.

## ۱. پاکت سیم بین‌بردی (envelope_version:1) — قرارداد اصلی 180↔138

از پیام زنده‌ی inbox 138 (message_type=proposal) و ack زنده‌ی 180 (receipts/control):

```json
{
  "checksum":          "<sha256-hex پاکت>",
  "claim_type":        "observation | proposal",
  "correlation_id":    "<uuid | ''>",
  "created_at":        "2026-08-26T09:10:37.313705Z",
  "envelope_version":  1,
  "evidence":          [],
  "expires_at":        "2026-08-26T09:11:37.313770Z",
  "idempotency_key":   "<uuid4>",
  "may_authorize":     false,
  "message_id":        "<uuid4>",
  "message_type":      "proposal | ack | task | critique | ping | cognitive_wake.v1",
  "payload":           { },
  "recipient_node":    "138",
  "requires_ack":      true,
  "run_id":            "<uuid4>",
  "scope":             "mesh",
  "sender_node":       "180",
  "sender_role":       "quality-brain | commander-router-ledger-owner"
}
```

- ALLOWED_TYPES در worker ۱۸۰: `task, proposal, critique, ping, cognitive_wake.v1` (خط ۳۸).
- الگوی idempotency_key برای ack: ‏`ack-{task_id}-{reply_id}-v1`.
- انقضای واقعی مشاهده‌شده: observation ≈ ۶۰ث، ack ≈ ۵دق.

### payload پیام ACK (message_type=ack)
```json
{ "block": "REPLY_RETRY_REPAIR_180_RESULT", "classify": "LIVE_DURABLE_REPLY",
  "in_reply_to": "<uuid>", "may_authorize": false,
  "response_sha256": "<sha256-hex>", "status": "ACK", "task_id": "<uuid>" }
```

## ۲. قرارداد جدیدِ تحویل‌فایل 180→138 (outbox/180-to-138-*.payload.json)

```json
{ "proposal_type": "partner_brief_delivery", "created_by": "180", "target_board": "138",
  "requested_path_on_138": "~/ofn/PARTNER-BRIEF-2026-08-29.md",
  "document": "<توضیح>", "sha256": "<sha256 محتوا>", "bytes": 6938,
  "note": "Data only…", "claim_type": "proposal", "may_authorize": false,
  "brief_markdown": "<محتوای فایل>" }
```

## ۳. Claim receipt در 180 (receipts/<message_id>.claim.json)

```json
{ "claimed_at": "…Z", "claimed_by_node": "180", "completed_at": "…Z",
  "lease_expires_at": "…Z", "message_id": "<uuid>",
  "reply_message_id": "<uuid>", "source_checksum": "<sha256-hex>",
  "status": "completed" }
```
→ semantics اجاره: پیام claim شده تا `lease_expires_at` متعلق به یک نود است.

## ۴. Execution receipt در 138 (RECEIPT_SCHEMA="execution_receipt.v1")

- فایل: `state_dir/execution_receipts.jsonl` (append-only؛ فقط FINAL — «receiptی که بتواند عوض شود receipt نیست»).
- DENYها: `witness-unavailable` (بدون receipt، بدون proof)، `duplicate-idempotency-key`، outcome مبهم.
- approval در زمان اجرا دوباره hash می‌شود؛ `payload_sha256 = sha256(exact_payload)`.
- ارائه‌دهنده حداکثر یک‌بار صدا زده می‌شود.

## ۵. Spine snapshot receipt در worker ۱۸۰ (_decode_spine_snapshot)

```json
{ "valid": false, "reason": "<کد>", "canonical_business_source_hash": "<expected|None>",
  "hash_domain": "decoded snapshot_b64 exact bytes (JSONL)", "row_count": 0,
  "actual_sha256": "<وقتی decode شد>" }
```
reasonهای واقعی: `source_hash_invalid, snapshot_b64_missing, snapshot_b64_invalid,
source_hash_mismatch, snapshot_not_utf8, snapshot_row_malformed, snapshot_row_not_object,
snapshot_row_contract_invalid, snapshot_row_count_mismatch`
(payload داخل پیام: `payload_sha256` + `snapshot_b64`).

## ۶. دفتر شاهد 182 (state/witness/)

**verdicts.jsonl** (هر خط):
```json
{ "phase": "final", "message_id": "<uuid>", "outcome": "delivered_acked",
  "verdict": "disputed", "idempotency_key": "auto-verify:<uuid>", "ts": "…Z" }
```
**owner_control_receipts.jsonl**: `{ ts, event, removed, command_message_id }`
**events.jsonl**: `{ event, message_id, ts, type }`

## ۷. Outbox داخل 138 (ofn/adapters/outbox.py)

```python
@dataclass(frozen=True)
class OutboxItem:
    idem_key: str; tenant: str; kind: str; payload: Mapping; tier: RiskTier
    status: str; attempts: int; created_at: str; updated_at: str; note: str
    delivery_mode: str = "manual"          # + approved_at/by, completed_at/by,
                                            #   completion_channel, packet_sha256,
                                            #   external_ref_digest
class Outbox:
    def enqueue(self, scope: TenantScope, idem_key: str, kind: str,
                payload, tier: RiskTier, now_iso: str) -> bool
    # False اگر همین کلید قبلاً صف شده؛ idempotency با PRIMARY KEY (نه read-then-insert)؛
    # BEGIN IMMEDIATE؛ FailClosedError روی idem_key خالی؛ کلید tenant-پیشونددار
```

## ۸. ثبت‌نام schemaها در لپ‌تاپ (_ops) — نام‌های رسمی موجود

`action-receipt.v1` (action_bridge/contracts.py) · `goal_proposal.v1` (cortex/goal_generator.py) ·
`memory-projection.v1→memory-proposal.v1` (memory/session_memory.py) ·
`owner-console.readonly-proposal.v1` · `b6.sog.proposal.v1` (synapse/sense) ·
`full-loop-gateway-receipt.v1` (lab/full_loop_flash/gateway.py)

## ۹. جدول نگاشت: spec پیشنهادی ← واقعیت (برای بازنویسی chaintest.py)

| فیلد پیشنهادی شما | معادل واقعی | یادداشت |
|---|---|---|
| proposal_id (ULID) | `message_id` (uuid4) + `idempotency_key` | دو کلید مستقل: هویت vs بازپخش |
| leg | `scope` + `claim_type` | leg واقعی business در payload/lane |
| intent | `message_type` + `claim_type` | |
| payload_hash | `checksum` (پاکت) + `payload_sha256`/`sha256` (محتوا) | سه لایه hash واقعی |
| expires_at | `expires_at` | ✅ هم‌نام |
| witness_id | ندارد | verdict با `message_id` کلید می‌خورد |
| signature / signer_key_id | ندارد | `checksum`+`source_checksum` جایگزین عملیاتی |
| chain_prev_hash | ندارد | زنجیره = append-only jsonl + hashها، بدون پیوند خطی |
| receipt_id | `reply_message_id` (یا message_id پیام ack) | |
| settled_at | `completed_at` (claim) / `ts` (verdict) | |
| outcome: accepted/expired/void | `verdict` (disputed/…) + `status` (completed/…) + reasonهای DENY | واژگان متفاوت |
| created_at / observed_at | `created_at` / `ts` | ✅ |

## ۱۰. invariantهایی که در کد واقعاً پیاده‌اند (X1 باید همین‌ها را ثابت کند)

1. **exactly-once**: کلید اولیه‌ی `idempotency_key` + `already_processed(message_id, idempotency_key)` + DENY `duplicate-idempotency-key`.
2. **انقضا**: `expires_at` قبل از پردازش چک می‌شود (`expires_at_invalid`).
3. **یکپارچگی سه‌لایه**: `checksum` پاکت ← `payload_sha256`/`sha256` محتوا ← `source_checksum` در claim.
4. **witness-before-receipt**: `witness-unavailable` ⇒ DENY بدون receipt (fake_executor).
5. **اجاره (lease)**: `lease_expires_at` مانع claim هم‌زمان دو نود است.
6. **بدون receipt معلق**: execution_receipts فقط FINAL، append-only.

## ۱۱. راستی‌آزمایی memtest.db پیوست‌شده (خودم اجرا کردم)

`v_memory_health = (episodes=23, current_facts=21, promoted_lessons=1, decisions_changed=1, read_write_ratio=0.045)`
+ usage_log یک ردیف `effect='changed'` (planner@180 → pr-ca29746b7b) + یک lesson `promoted`
+ دو contradiction (`old_wins`, `new_wins`). **با ادعای LEARNING_PROVEN سازگار است.**

⚠️ قید صادقانه: این sandbox با schema پیشنهادی خود شماست (`episodes/facts/lessons/usage_log`)،
نه ذخیره‌گاه‌های زنده (`_ops/state/spine/spine.db`، `state/memory/memory.db`، `organism.db` روی ۱۸۰).
یعنی **حلقه یادگیری روی الگوی پیشنهادی اثبات شد، نه روی ارگانیسم زنده** — تست روی fixtureهای
مسیرهای واقعی همچنان منتظر گیت `SAFE_TESTS` است (نقشه‌ی دقیق در NEXT_AGENT.md).

---

# ضمیمه (۶:۴۵–۶:۵۵Z) — تأیید از کد فعلی + schemaهای رسمی کشف‌شده

## ۱۲. سازنده‌ی envelope در کد (تأیید HEAD جاری)

محل: `octomesh_common.py` + `octomesh_agent_bridge.py` (روی هر دو نود ۱۸۰/۱۳۸؛ **داخل octopus-mesh است، نه ریپوی ofn**
— ریپوی ofn هیچ `envelope_version`‌ی ندارد). ترتیب فیلدها در سازنده دقیقاً همان ۱۸ فیلد بخش ۱ است.

فرمول checksum (بایت‌به‌بایت، برای fixtureسازی chaintest):
```python
canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
compute_checksum = sha256(canonical({k: v for k, v in msg.items() if k != "checksum"}).encode("utf-8")).hexdigest()
verify_checksum = hmac.compare_digest(given, compute_checksum(msg))   # constant-time
source_checksum در claim receipt = compute_checksum(پیام claim شده)
```

## ۱۳. فایل‌های schema رسمی (کشف جدید: `octopus-mesh/config/` روی ۱۸۰)

| فایل | محتوا |
|---|---|
| `business_source.v1.schema.json` | schema رسمی JSON-Schema 2020-12، `$id=octopus://schemas/business_source.v1` |
| `business_cycle_contracts.v1.json` | قرارداد کامل چرخه‌ی business روی ۱۸۰ |

### business_source.v1 — فیلدهای الزامی (۱۰):
`schema("business_source.v1"), source_run_id, producer_node(const "138"), observed_at_utc,
masked(const true), fixture(const false), hold_external(const true), may_authorize(const false),
lane_sources{painting,ziman,studio}, source_receipt_sha256(^[a-f0-9]{64}$)`
- ‏painting.real_leads[]: ‏`internal_id_hash, status, temperature, follow_up_count, job_type, budget_text, suburb, rooms, source_row_hash` (همه hashها sha256-hex)
- ‏ziman.real_products[]: ‏`sku, …` (همان الگو)

### business_cycle_contracts.v1 — قرارداد artifact پیشنهاد روی ۱۸۰:
- **required_artifact_fields (۲۶)**: `run_id, lane, status, node_id, may_authorize, hold_external,
  laptop_required, external_effects, claim_type, scope, confidence, evidence, alternatives, falsifier,
  business_source_receipt, deterministic_facts, memory_context, memory_context_sha256, tool_scope,
  model_receipt, exact_payload, risk, rollback, telegram_decision, witness_packet`
- **telegram_decision_fields (۱۰)**: `decision_id, business, recommended_action, exact_payload,
  price_or_cost, evidence, risk, rollback, expiry, recommendation`
- ‏artifact_status: `PROPOSAL_READY | BLOCKED_HONEST | DEGRADED_LOCAL`
- ‏waiting_states: `PENDING_180_DECISION | PENDING_OWNER_TELEGRAM | PENDING_EXECUTOR`
- ‏owner_responses: `APPROVE | REVISE | REJECT | DETAILS`
- ‏forbidden_output_keys: `revenue, SENT, booking, customer_send`
- ‏witness_submit_semantics_on_180 = `"prepare_packet_for_138_only"`
- **memory_contract** (bounded_typed_memory.v1): وضعیت‌ها `CURRENT/STALE/CONFLICT/SUPERSEDED/UNVERIFIED`
  (legacy بدون status ⇒ UNVERIFIED)؛ سقف‌ها: working_state=10, relevant_episodes=5,
  procedural_rules=5, negative_lessons=3, conflicts=3, source_evidence=10؛
  embedding/reranker backend = PENDING_PC_EXP_01
- ‏lane_tool_scopes: painting/ziman/studio هرکدام `read/score|margin/asset + draft + witness_submit`

## ۱۴. نکته‌ی parity (ثبت برای تناقض‌ها)

‏config نودها هم‌سان نیست: ۱۸۰ `business_source.v1.schema.json` و `business_cycle_contracts.v1.json` را دارد؛
‏۱۳۸ ندارد (به‌جایش `action_tiers.json, autonomy_policy.json, policy.json, calibration_schema.json, …`).
یعنی schemaی که تولیدکننده‌اش ۱۳۸ است، فقط روی ۱۸۸ live شده — توزیع schema بین نودها همگام‌سازی نمی‌شود.
