# C-PORT-PLAN — porting Exact Effect Authorization into candidate chrono.py

منبع: audit ۵-عاملیِ read-only (C-AUDIT-C-A..C-E). این recipe دقیق است تا پورتِ **money-code**
درست انجام شود، نه عجولانه. C فقط با C-G1..C-G10 سبز، PASS است — **هنوز نیست**.

## کشفِ کلیدی: C از prototype بزرگ‌تر است
prototype (۱۳/۱۳) فقط **binding + migration** را اثبات کرد. audit نشان داد کدِ فعلیِ candidate
مشکلاتِ عمیق‌ترِ **اثبات‌نشده** دارد که پورت باید حلشان کند:

## بخش ۱ — ۲ BLOCKER بحرانیِ schema (C-A) — پیش‌نیازِ هر پورت
1. **`chrono.py:227` `PRAGMA user_version=1` داخلِ `_DDL`** روی هر `__init__` اجرا می‌شود →
   version را به ۱ برمی‌گرداند → guardِ `if ver>=2:return` را می‌شکند. **باید از `_DDL` حذف شود.**
2. **`__init__` هیچ migration صدا نمی‌زند** (فقط `IF NOT EXISTS`). **باید `migrate_up(self._con)`
   بعد از `executescript(_DDL)` اضافه شود** (`chrono.py:238`).
3. **فقط ۱۰ ستونِ اثبات‌شده** (content_hash, action_kind, target_ref, idempotency_key,
   proposal_id, mission_id, approval_id, approved_by, approved_at, expires_at). **۵ ستونِ دیگر
   (effect_class, settled_at, external_receipt_ref, failure_reason, schema_version) طرحِ اثبات‌شده
   ندارند → پورت نشوند** (schema_version با PRAGMA user_version تضاد دارد).

## بخش ۲ — authorization (C-E) — قلبِ money-safety
- `release_gated_effects` (chrono.py:402-404) همهٔ money/E4 pending را با یک append آزاد می‌کند،
  bind به هیچ per-effect. → **برای E4 fail-closed/حذف**؛ همه از `release_one`ِ binding-verified.
- `release_one` (chrono.py:418-419) فقط به effect_id bind است. → **بند به
  content_hash+action_kind+target_ref+expiry + single-use anti-replay** (طبق prototype release_effect).
- `settle` (chrono.py:443-452) فقط `status=='releasable' + release_ref` را چک می‌کند، binding/expiry
  را re-verify نمی‌کند.
- `on_human_judgment` بدونِ effect_id به batch fallback می‌کند (money-batch باز).

## بخش ۳ — crash/idempotency (C-C) — فراتر از prototype، نیازمندِ طرحِ اثبات‌شده
- **settle یک TOCTOU است** (SELECT سپس blind UPDATE، نه CAS). → **CAS تک‌statement:**
  `UPDATE gated_effect SET status='settled' WHERE effect_id=? AND status='releasable' [AND external_status='confirmed']`.
- **request idempotent نیست** (uuid تازه). → `idempotency_key` اجباری + dedup (SELECT-first).
- **crash window (a):** on_human_judgment به دو store غیراتمیک می‌نویسد، بدونِ restart re-drive →
  **reconciliation lane** (اسکنِ ledger برای APPROVALهای pendingِ مانده، re-drive).
- **crash window (b):** `sweep_stale_effects` فقط `pending` را جارو می‌کند نه `releasable` →
  intent گیرافتاده. → reconciliation pass روی `releasable`.
- **crash window (c):** settle هیچ external receipt ثبت نمی‌کند → **exactly-once ممکن نیست**؛
  فقط **effectively-once under idempotency/reconciliation**. (external_receipt نیازمندِ طرحِ جدا.)

## بخش ۴ — caller migration (C-B) + reader safety (C-A)
- chrono.py مالکِ انحصاریِ DML است (test_effector_gate_bridge:148).
- readerهای بیرونی فقط `status` را می‌خوانند (COUNT/GROUP BY: export_status.py:105،
  cockpit_readmodel.py:337) → table-recreateِ additive caller-safe است، **اما** statusهای نوِ
  NEEDS_OWNER_REVIEW/LEGACY_UNBOUND در GROUP BY ظاهر می‌شوند → dashboardها باید tolerate کنند.
- callerهای `release_gated_effects`/`release_one`/`settle`/`on_human_judgment` → به API دقیق migrate.

## گیت‌های C (C-G1..C-G10) — هیچ‌کدام هنوز سبز نیست
port logic · همهٔ callers migrate · صفر E4 batch · unauthorized→۰ release در اجزای واقعی ·
migration ۱۶ سناریو · idempotency test از phantom خارج · full suite سبز · ruff/static سبز ·
live-write/network/effect صفر · rollback+forward اثبات.

## توصیهٔ صادقانه (money-code)
این یک جراحیِ چندمرحله‌ایِ کدِ پول است که audit نشان داد از prototype بزرگ‌تر است (TOCTOU/CAS،
crash reconciliation، external receipt). **باید در یک نشستِ متمرکز و بادقت انجام شود، نه عجولانه**،
با regression بعد از هر مرحله. prototype (۱۳/۱۳) طرحِ binding+migration را اثبات کرد؛ crash/CAS/receipt
نیازمندِ طرحِ اثبات‌شدهٔ بیشتر است. تا آن زمان C در سطحِ candidate `[OPEN]` است — **نه fake-port.**
