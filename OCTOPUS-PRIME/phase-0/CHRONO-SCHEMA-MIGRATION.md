# CHRONO-SCHEMA-MIGRATION (C) — v1 → v2, fixture-proven

مرجعِ اجرا: `test-authority/chrono_migration_prototype.py` (۱۳/۱۳ روی fixture). **هرگز chrono.db زنده.**

## روش
SQLite نمی‌تواند CHECK را ALTER کند، پس **table-recreate**:
1. `CREATE TABLE gated_effect_new (...)` با CHECK گسترش‌یافته:
   `status ∈ {pending, releasable, settled, refused, NEEDS_OWNER_REVIEW, LEGACY_UNBOUND}`
   + ستون‌های binding: `content_hash, action_kind, target_ref, idempotency_key,
   proposal_id, mission_id, approval_id, approved_by, approved_at, expires_at`.
2. `INSERT INTO gated_effect_new (v1 cols) SELECT ... FROM gated_effect` (ستون‌های نو = NULL).
3. `DROP TABLE gated_effect; ALTER TABLE gated_effect_new RENAME TO gated_effect`.
4. ردیف‌های legacyِ `pending` بدونِ `content_hash` → `NEEDS_OWNER_REVIEW`.
5. `PRAGMA user_version = 2`.

## خواص اثبات‌شده (fixture)
- **idempotent**: اجرای دوم (user_version≥2) → no-op (`recreated=False`).
- **versioned**: user_version=2.
- **legacy-safe**: unbound pending → NEEDS_OWNER_REVIEW (هرگز خودکار releasable).
- **no data drop**: همهٔ ردیف‌های v1 حفظ.

## release contract (v2)
`release_effect(effect_id, approval)` fail-closed مگر همهٔ:
effect_id==، content_hash==، action_kind==، target_ref==، approval_id غیرتکراری (single-use anti-replay)،
expires_at آینده، status=='pending'. → status='releasable' + ثبتِ approval_id/approved_by/approved_at.
- **money batch release حذف/fail-closed** (`release_gated_effects` دیگر money-kind را blanket آزاد نمی‌کند).
- **idempotent request** با `idempotency_key` (dedup).

## پورت به candidate (قدم بعدی، هنوز نشده)
`_ops/chrono.py`: افزودنِ `_DDL` v2 + تابعِ migration idempotent در `ChronoDB.__init__`،
بازنویسیِ `EffectorGate.request/release_*` به قراردادِ بالا، سپس **اجرای کلِ sandbox suite**.
تا آن زمان، C در سطحِ candidate `[OPEN]`؛ contract روی fixture PASS است.
