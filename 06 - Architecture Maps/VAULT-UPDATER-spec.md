---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [vault-updater, propose-only, governance, cognition-vs-effect]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[06 - Architecture Maps/SPEC-OCTOPUS-2027-v0]]"
  - "[[06 - Architecture Maps/PART-LOOPS-per-section-autonomy]]"
---

# VAULT-UPDATER — propose-only «تولیدکنندهٔ patch» (cognition ≠ effect)

> رأی مالک (2026-07-11): «پرامپتِ به‌روزرسانی نباید بنویسد — باید patch تولید کند. شناخت را
> از اثر جدا کن؛ EffectorGate تنها نویسنده.» پیاده‌شده: `_ops/vault_updater.py` (proposer،
> هرگز دیسک) + `_ops/vault_updater_gate.py` (validatorِ stdlib، gate پیش از commit).

## اصلِ حاکم: شناخت ≠ اثر

- **proposer** (`vault_updater.propose`) فقط **فکر می‌کند**: raw_input → PATCH PROPOSALِ
  JSONِ سخت‌گیر. هرگز به دیسک نمی‌نویسد (تست `t_j` تضمین می‌کند: صفر `open/write/mkdir`).
- **gate** (`vault_updater_gate.validate`) دومین گاردِ مستقل است: proposalِ ناامن را **پیش از
  هر commit** رد می‌کند (defense-in-depth؛ حتی اگر proposer باگ داشته باشد).
- نوشتنِ واقعی از مسیرِ موجودِ human-append/EffectorGate + auto_approve می‌گذرد (AUTO-tier).

## LAYER_MAP — Ring هر مسیر

| Ring | مسیر | commit |
|---|---|---|
| 0 | ژنوم/قانون اساسی: `CLAUDE.md`, `_PROJECT_INSTRUCTIONS.md`, `.agentignore`, `_code/`, `genome-system/ledger/`, charter/rotation | **HOLD** (فقط flag، هرگز edit) |
| 1 | schema/index/MOC: `Property Schema`, `types.json`, `_Index - *`, `Home/HANDOFF`, `PROJECT.md` | **GATE** (همیشه رأیِ انسان) |
| 2-3 | نوتِ دامنه: `03 Projects`, `07 Knowledge`, `09 People`, `02 Life OS` | **AUTO** اگر LOW و مسیر ∈ envelope، وگرنه GATE |
| 4 | inbox/scratch: `00 Inbox`, `10 Telegram/Raw` | **AUTO** اگر LOW، وگرنه GATE |
| — | **Project-F (اونلی‌فنز)** | **HOLD + escalate** (تخطی‌ناپذیر) |
| — | `_Archive`/`_Duplicates` | فقط مقصدِ انتقال (HOLD) |

## رویه (deterministic؛ به‌ترتیب)

1. **classify** — {fact|decision|task|reference|insight} + Ring + sensitivity.
2. **HOLD-rails (fail-closed):** Project-F / PII-secret / بی‌provenance / retrievalِ خالی+مسیرِ نامشخص → HOLD.
3. **dedup** — شباهتِ token (Jaccard؛ ارتقا: cosineِ hash-embeddingِ `neural/encoders`). ≥τ → **append/merge** به همان نوت، نه create (ضدِ تورمِ تکرار).
4. **risk_flag** — LOW | REVIEW | CRITICAL. CRITICAL هرگز downgrade/suppress.
5. **commit_mode** — از جدولِ Ring×risk×envelope.
6. **ledger_entry** — {before_hash, after_hash, op, provenance, rationale, ts}. op ∈ {create, append, supersede} — **هرگز delete/overwrite**؛ تضاد → supersede-with-pointer (نوتِ قدیم حفظ + لینک).
7. خروجیِ JSONِ سخت‌گیر (`status/classification/target_path/commit_mode/risk/dedup/patch/ledger_entry/rationale/human_prompt`).

## ریل‌های سختِ gate (هر تخطی → رد)

- Ring 0/1 هرگز AUTO · CRITICAL هرگز AUTO · Project-F همیشه HOLD · بی‌provenance رد ·
  op مخرب (delete/overwrite) رد · GATE/HOLD بدونِ human_prompt رد.

## قدم‌های بعد (backlog)

- ارتقای dedup به cosineِ واقعیِ `neural/encoders` (τ = ۹۵th percentile فاصله‌ها).
- لایهٔ cognitionِ LLM (fugu/local) روی `classify`/`draft` — همچنان خروجی از همین gate.
- applierِ AUTO-tier که proposalِ gate-passed را از مسیرِ human-append/EffectorGate commit کند.

تست: `_ops/tests/test_vault_updater.py` (۱۲/۱۲، سبکِ credential-panel، fail-closed).
