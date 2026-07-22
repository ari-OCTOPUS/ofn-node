# EFFECT-AUTHORIZATION-CONTRACT (C) — exact, per-effect, fail-closed

قرارداد authorization→release→settle برای `gated_effect`. **fixture-only migration؛ هرگز chrono.db زنده.**

## اصل
یک approval **دقیقاً یک effect** را با binding کامل آزاد می‌کند. هیچ approvalِ عمومی money/E4 را
batch نمی‌کند. `proposal_id`/`mission_id` فقط provenance‌اند، نه کلیدِ authorization.

## Schema فعلی (baseline v1)
```
gated_effect(effect_id PK, kind, payload_ref, created_beat, created_ts, release_ref,
             status ∈ {pending, releasable, settled, refused})
```

## Migration هدف (v2، additive، idempotent، versioned)
`ALTER TABLE ADD COLUMN` (هر کدام با چکِ وجودِ ستون → idempotent):
| ستون | نقش |
|---|---|
| `content_hash TEXT` | هشِ payload/محتوا — approval باید به همین bind شود |
| `action_kind TEXT` | نوعِ عملِ canonical (send/publish/sync/pay/…) |
| `target_ref TEXT` | مقصدِ عمل |
| `idempotency_key TEXT` | dedupِ درخواست |
| `proposal_id TEXT` (nullable) | provenance/join |
| `mission_id TEXT` (nullable) | provenance/join |
| `approval_id TEXT` (nullable) | approvalی که آزاد کرد |
| `approved_by TEXT` (nullable) | هویتِ تأییدکننده |
| `approved_at INTEGER` (nullable) | زمانِ تأیید |
| `expires_at INTEGER` (nullable) | انقضای approval |
- `status` CHECK گسترش: افزودن `'NEEDS_OWNER_REVIEW'`, `'LEGACY_UNBOUND'`.
- `schema_version` (PRAGMA user_version یا جدولِ meta) = 2.

## قواعدِ migration
1. additive و versioned؛ ۲. idempotent/دوباره‌اجراپذیر (چکِ ستون قبل از ADD)؛
3. backup + rollback plan روی fixture؛ ۴. **ردیف‌های legacyِ pending بدونِ binding دقیق →
`NEEDS_OWNER_REVIEW`** (هرگز خودکار releasable)؛ ۵. هیچ داده silently drop نشود؛
6. schema_version ثبت؛ ۷. fixture قدیمی→جدید migrate و اثبات؛ ۸. rollback روی copy اثبات.

## release contract (v2)
```
release_effect(effect_id, approval):
  fail-closed اگر هرکدام:
    - approval.effect_id != effect_id
    - approval.content_hash != row.content_hash
    - approval.action_kind != row.action_kind
    - approval.target_ref  != row.target_ref
    - approval.approval_id  خالی/تکراری (anti-replay: single-use)
    - approval.expires_at   گذشته
    - row.status != 'pending'
  → در غیر اینصورت: status='releasable'، approval_id/approved_by/approved_at ثبت، single-use.
```
- **حذف/fail-close کردنِ batch release برای E4/money:** `release_gated_effects` دیگر money-kind
  را blanket آزاد نمی‌کند؛ money فقط از مسیرِ `release_effect` (per-effect، id+hash-bound).
- **idempotent request:** effect با همان `idempotency_key` → یک ردیف (نه تکراری).
- **settle** بدون تغییر: فقط `releasable + release_ref` → world؛ force_closed اول.

## تست‌های اجباری (fixture-only)
1 دو pending/یک approval→یک releasable · ۲ بدون effect_id→۰ · ۳ mismatched content_hash→۰ ·
۴ mismatched target→۰ · ۵ mismatched action→۰ · ۶ mismatched proposal/mission (جایی لازم)→۰ ·
۷ expired approval→۰ · ۸ replayed approval→۰ · ۹ duplicate idempotency_key→یک effect ·
۱۰ duplicate settle→بدون اثرِ تکراری · ۱۱ crash after release before settle→recovery بدون تکرار ·
۱۲ crash after external effect before settle→قراردادِ idempotency روشن · ۱۳ legacy unbound→owner review ·
۱۴ migration up دوبار→بدون corruption · ۱۵ rollback روی fixture→بازیابی · + کلِ suite بعد از migration.

## خروجی‌ها
`CHRONO-SCHEMA-MIGRATION.md` · `CHRONO-MIGRATION-TEST-REPORT.json` · `CHRONO-MIGRATION-ROLLBACK.md`.
**هیچ live DB migration.**
