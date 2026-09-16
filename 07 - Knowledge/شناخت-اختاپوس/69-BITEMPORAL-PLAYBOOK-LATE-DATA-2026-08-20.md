---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: spec
tags: [octopus, bitemporal, late-data, correction, supersedes, indexing, shadow, lineage]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
sources:
  - "https://martinfowler.com/articles/bitemporal-history.html"
  - "https://www.ibm.com/docs/en/ias?topic=bt-querying"
  - "https://aiven.io/blog/two-dimensional-time-with-bitemporal-data"
  - "https://www.confluent.io/blog/watermarks-tables-event-time-dataflow-model/"
  - "[[../../03 - Projects/research-spec-compiler/adr/ADR-043-nase-dual-timestamp]]"
  - "[[../../06-EVIDENCE/HC-WM-MC-WAVE0-2026-08-20/CONTRACTS]]"
  - "[[../../06-EVIDENCE/HC-WM-MC-BASELINE-2026-08-20/README]]"
---

# ۶۹ — Playbook مدل‌سازی Bitemporal: correction، دادهٔ دیررس، زمان‌سفر (2026-08-20)

> **وضعیت: SPEC/playbook.** الگوها با SQL استاندارد (PostgreSQL برای بیان الگو،
> SQLite برای واقعیت فعلی پروژه) نوشته شده‌اند و هنوز روی دادهٔ زنده اعمال نشده‌اند.
> پیش‌نیاز واقعی‌سازی همهٔ این ماشین‌آلات در §۰ آمده است.

## ۰. زمینهٔ OCTOPUS — قبل از هر چیز

- [FACT] قرارداد زندهٔ WAVE0 (۲۰۲۶-۰۸-۲۰):
  `occurred_at <= recorded_at <= decision_time` وگرنه `FUTURE_DATA` (غیرمجاز).
- [FACT] ADR-043: روی spine فعلی، دو ستون زمانیِ occurred/recorded عملاً دو فراخوانی
  متوالیِ یک ساعت‌اند (stdev ≈ ۱ms) و «مستقل» شمرده نمی‌شوند.
- [INFERENCE] تا وقتی producer ای `occurred_at` را از زمان واقعی رویداد (نه زمان
  نوشتن) نگیرد، کل ماشین correction/supersession این playbook روی دادهٔ بی‌معنا
  کار می‌کند. **اولیه‌ترین کار عملیاتی: یک تولیدکنندهٔ event-time واقعی، بعد این
  playbook.**
- [FACT] انبارهٔ فعلی: `_ops/state/spine/spine.db` (SQLite) + ledgerهای JSONL
  append-only. یعنی الگوی «event store + projection» عملاً حاضر است؛ §۶.

## ۱. مدل مرجع داده

چهار ستون زمانی، دو محور:

```text
valid_time      (valid_from / valid_to)     ≈ occurred_at — «در جهان چه زمانی درست بود»
transaction_time (transaction_from / transaction_to) ≈ recorded_at — «سیستم چه زمانی فهمید»
```

قواعد نقض‌ناپذیر:

1. هیچ رکوردی فیزیکی UPDATE یا DELETE نمی‌شود؛ اصلاح = بستن یک بازه + append نسخهٔ تازه.
2. `transaction_from` هرگز تغییر نمی‌کند؛ فقط `transaction_to` بسته می‌شود.
3. نسخه‌های superseding همیشه `transaction_from >= transaction_to` نسخهٔ ماقبل دارند.
4. هیچ رکوردی بدون `valid_from` و `transaction_from` و `source_event_id` وارد تصمیم نمی‌شود
   (`INELIGIBLE_TEMPORAL_METADATA` — نه تزریق ساعت فعلی).

### Schema (PostgreSQL — بیان الگو)

```sql
CREATE TABLE memory_fact (
    fact_id           uuid PRIMARY KEY,
    entity_id         text        NOT NULL,
    payload           jsonb       NOT NULL,
    valid_from        timestamptz NOT NULL,
    valid_to          timestamptz,                          -- NULL = هنوز معتبر
    transaction_from  timestamptz NOT NULL DEFAULT now(),
    transaction_to    timestamptz,                          -- NULL = دانش جاری
    supersedes_id     uuid REFERENCES memory_fact(fact_id),
    source_id         text        NOT NULL,
    source_event_id   text        NOT NULL,
    confidence        real        NOT NULL DEFAULT 0.5,
    arrival_status    text        NOT NULL,                 -- ON_TIME | LATE_NEW_FACT | LATE_CONFLICTING | ...
    provenance_ids    uuid[]      NOT NULL DEFAULT '{}',
    tombstone         boolean     NOT NULL DEFAULT false,
    CHECK (valid_to IS NULL OR valid_to > valid_from),
    CHECK (transaction_to IS NULL OR transaction_to > transaction_from),
    CHECK (transaction_to IS NULL OR transaction_to >= valid_from)  -- دیررسِ آینده مجاز نیست
);

-- رکورد مشتق: summary/embedding/graph-edge/hypothesis...
CREATE TABLE derived_artifact (
    artifact_id     uuid PRIMARY KEY,
    kind            text        NOT NULL,                   -- summary | embedding | hypothesis | ...
    derived_at      timestamptz NOT NULL,
    decision_time   timestamptz NOT NULL,                   -- as-of کدام برش ساخته شده
    evidence_ids    uuid[]      NOT NULL,
    evidence_cutoff timestamptz NOT NULL,
    version         integer     NOT NULL DEFAULT 1,
    status          text        NOT NULL DEFAULT 'ACTIVE'   -- ACTIVE | STALE_BY_LATE_DATA | SUPERSEDED
);

-- رسید اثر هر رویداد دیررس (همان receipt الگوی WAVE0)
CREATE TABLE late_arrival_receipt (
    receipt_id     uuid PRIMARY KEY,
    late_event_id  text        NOT NULL UNIQUE,             -- idempotency
    occurred_at    timestamptz NOT NULL,
    recorded_at    timestamptz NOT NULL,
    delay_seconds  numeric     NOT NULL,
    classification text        NOT NULL,
    affected       jsonb       NOT NULL,                    -- decisions/world_states/summaries/...
    mutated_history boolean    NOT NULL DEFAULT false,      -- باید false بماند
    recomputation_mode text    NOT NULL DEFAULT 'SHADOW'
);
```

جلوگیری از هم‌پوشانی نسخه‌های هم‌زمانِ یک entity (در PostgreSQL):

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE memory_fact ADD CONSTRAINT no_concurrent_overlap
EXCLUDE USING gist (
    entity_id WITH =,
    tstzrange(valid_from, COALESCE(valid_to, 'infinity')) WITH &&
) WHERE (transaction_to IS NULL);   -- فقط میان نسخه‌های «دانش جاری»
```

## ۲. تریگرها — نقش درست و نادرست

**قاعده:** تریگر برای *بازدارندگی* (immutability) به‌کار می‌رود، نه برای
نسخه‌بندی خودکار. versioning با trigger روی UPDATE مستقیم، به‌سادگی بازگشتی
(trigger→insert→trigger) می‌شود و ترتیب بستن بازه‌ها را مبهم می‌کند. الگوی تمیز:

```sql
-- تریگر ۱: نگهبان append-only — هر UPDATE/DELETE فیزیکی را رد کن،
-- جز بستن transaction_to (که فقط از داخل procedure مجاز است با SET LOCAL).
CREATE OR REPLACE FUNCTION guard_immutability() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'memory_fact is append-only: tombstone instead of DELETE';
    END IF;
    IF NEW.fact_id            IS DISTINCT FROM OLD.fact_id
    OR NEW.valid_from         IS DISTINCT FROM OLD.valid_from
    OR NEW.valid_to           IS DISTINCT FROM OLD.valid_to
    OR NEW.transaction_from   IS DISTINCT FROM OLD.transaction_from
    OR NEW.payload           IS DISTINCT FROM OLD.payload
    OR NEW.supersedes_id      IS DISTINCT FROM OLD.supersedes_id
    OR NEW.source_event_id    IS DISTINCT FROM OLD.source_event_id THEN
        RAISE EXCEPTION 'immutable fields changed; use bitemporal_correct()/bitemporal_update()';
    END IF;
    IF app.allow_closing THEN          -- فقط داخل procedureها ست می‌شود
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'direct UPDATE forbidden';
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_guard BEFORE UPDATE OR DELETE ON memory_fact
FOR EACH ROW EXECUTE FUNCTION guard_immutability();
```

پارامتر جلسه‌ای `app.allow_closing` فقط داخل دو procedure زیر با
`SET LOCAL app.allow_closing = on` روشن می‌شود — یعنی تنها مسیر تغییر جدول،
همین procedureهاست.

## ۳. Stored procedureها

### ۳.۱ `bitemporal_correct` — تصحیح گذشته‌نگر

«دانش ما غلط بود؛ واقعیت در جهان همان بود» → بازهٔ system-time نسخهٔ قدیم بسته
می‌شود، نسخهٔ تازه همان `valid_from` را با payload درست تکرار می‌کند.

```sql
CREATE OR REPLACE FUNCTION bitemporal_correct(
    p_entity_id     text,
    p_valid_from    timestamptz,
    p_new_payload   jsonb,
    p_as_of         timestamptz DEFAULT now(),
    p_source_event  text,
    p_confidence    real DEFAULT 0.5
) RETURNS uuid AS $$
DECLARE
    v_old memory_fact;
    v_new_id uuid := gen_random_uuid();
BEGIN
    SET LOCAL app.allow_closing = on;

    SELECT * INTO v_old FROM memory_fact
    WHERE entity_id = p_entity_id
      AND valid_from <= p_valid_from
      AND (valid_to IS NULL OR p_valid_from < valid_to)
      AND transaction_to IS NULL
    ORDER BY transaction_from DESC
    LIMIT 1
    FOR UPDATE;                                   -- serialize هم‌زمانی

    IF v_old.fact_id IS NULL THEN
        RAISE EXCEPTION 'no current version covering valid_from %', p_valid_from;
    END IF;

    UPDATE memory_fact
       SET transaction_to = p_as_of                -- تنها تغییر مجاز
     WHERE fact_id = v_old.fact_id;

    INSERT INTO memory_fact (fact_id, entity_id, payload,
        valid_from, valid_to, transaction_from, supersedes_id,
        source_id, source_event_id, confidence, arrival_status, provenance_ids)
    VALUES (v_new_id, p_entity_id, p_new_payload,
        v_old.valid_from, v_old.valid_to, p_as_of, v_old.fact_id,
        v_old.source_id, p_source_event, p_confidence,
        'LATE_CORRECTION', v_old.provenance_ids || v_old.fact_id);

    RETURN v_new_id;
END $$ LANGUAGE plpgsql;
```

### ۳.۲ `bitemporal_update` — تغییر واقعیِ جهان

«واقعیت در جهان عوض شد» → `valid_to` نسخهٔ جاری بسته می‌شود و نسخهٔ تازه از
لحظهٔ تغییر `valid_from` می‌گیرد. تاریخِ دانش دست‌نخورده می‌ماند.

```sql
CREATE OR REPLACE FUNCTION bitemporal_update(
    p_entity_id   text,
    p_change_at   timestamptz,                -- لحظهٔ تغییر در جهان
    p_new_payload jsonb,
    p_as_of       timestamptz DEFAULT now(),
    p_source_event text
) RETURNS uuid AS $$
DECLARE
    v_old memory_fact;  v_new_id uuid := gen_random_uuid();
BEGIN
    SET LOCAL app.allow_closing = on;

    SELECT * INTO v_old FROM memory_fact
    WHERE entity_id = p_entity_id AND transaction_to IS NULL
      AND valid_from <= p_change_at AND (valid_to IS NULL OR p_change_at < valid_to)
    FOR UPDATE;
    IF v_old.fact_id IS NULL THEN
        RAISE EXCEPTION 'no current fact at %', p_change_at;
    END IF;

    UPDATE memory_fact SET valid_to = p_change_at, transaction_to = p_as_of
     WHERE fact_id = v_old.fact_id;

    INSERT INTO memory_fact (fact_id, entity_id, payload,
        valid_from, transaction_from, source_id, source_event_id, provenance_ids)
    VALUES (v_new_id, p_entity_id, p_new_payload,
        p_change_at, p_as_of, v_old.source_id, p_source_event, v_old.provenance_ids || v_old.fact_id);

    RETURN v_new_id;
END $$ LANGUAGE plpgsql;
```

### ۳.۳ تفاوت correction و update در عمل (خلاصهٔ تصمیم)

| | **bitemporal correction** | **bitemporal update** |
|---|---|---|
| چه چیز اشتباه بود | دانشِ سیستم | خودِ واقعیت جهان |
| ستون بسته‌شده در نسخهٔ قدیم | `transaction_to` | `valid_to` (+ `transaction_to` باز هم append) |
| `valid_from` نسخهٔ جدید | همان قدیم | لحظهٔ تغییر واقعیت |
| query «آن‌روز چه می‌دانستیم؟» | نسخهٔ غلطِ قدیم را برمی‌گرداند (درست است!) | همان قدیم (هنوز آن‌روز معتبر بود) |
| query «امروز؟» | نسخهٔ تصحیح‌شده | نسخهٔ جدید |
| مثال | «دما ۷۰ خوانده شد؛ درستش ۷۵ بود» | «تا ۱۰:۰۰ ضربان ۶۰ بود؛ از ۱۰:۰۰ شد ۷۵» |

### ۳.۴ `record_late_event` — درجه‌بندی دیررسی

```sql
CREATE OR REPLACE FUNCTION classify_lateness(p_occurred timestamptz, p_watermark timestamptz)
RETURNS text LANGUAGE sql AS $$
    SELECT CASE
        WHEN p_occurred >= p_watermark                    THEN 'ON_TIME'
        WHEN p_occurred >= p_watermark - interval '24 hours' THEN 'LATE_WITHIN_WINDOW'
        ELSE 'LATE_BEYOND_WATERMARK'
    END $$;
```

سیاست هر درجه (مطابق قرارداد سپهر دیررس): ingest همیشه؛ بازمحاسبه فقط Shadow؛
ترویج fact برای `LATE_CONFLICTING` ممنوع (`eligible_for_hypothesis=true`).

## ۴. کوئری‌های زمان‌سفر (Time-travel)

```sql
-- «در لحظهٔ T1، دربارهٔ لحظهٔ T2 چه می‌دانستیم؟» (حسابرسی تصمیم تاریخی)
SELECT * FROM memory_fact
WHERE entity_id = :entity
  AND valid_from       <= :t2 AND (:t2 < COALESCE(valid_to,       'infinity'))
  AND transaction_from <= :t1 AND (:t1 < COALESCE(transaction_to, 'infinity'));

-- «امروز دربارهٔ T2 چه می‌دانیم؟» (بهترین برداشت فعلی از گذشته)
-- همان کوئری با :t1 = now()

-- «برای تصمیمِ decision_time چه چیزی مجاز است؟» (قانون سخت WAVE0)
SELECT * FROM memory_fact
WHERE entity_id = :entity
  AND valid_from       <= :decision_time
  AND transaction_from <= :decision_time
  AND transaction_to IS NULL;
```

[FACT] این همان قرارداد `context_for_decision` است که WAVE0 امتحان کرد؛
`FUTURE_DATA` یعنی نقض شرط سوم. context builder هرگز نباید با
`known_at = NOW` برای تصمیم تاریخی query بزند.

## ۵. مقایسهٔ استراتژی‌های indexing (پس از درج دادهٔ دیررس)

[UNKNOWN] اعداد نسبی زیر استدلال ساختاری است، نه benchmark اجراشده روی
دادهٔ ما؛ قبل از انتخاب نهایی، با fixtureهای WAVE0 بسنجید.

| استراتژی | بهترین کاربرد | ضعف تحت بار دیررس |
|---|---|---|
| A: btree `(entity_id, valid_from, valid_to)` | point-in-time بر valid-time | دیررس = insert در میانهٔ timeline → page-split و fragmentation بیشتر از append انتهایی |
| B: btree `(entity_id, transaction_from)` | حسابرسی/زمان‌سفر بر system-time | روی فیلتر valid-only کمکی نمی‌کند |
| C: ترکیب A+B | هر دو محور؛ پوشش کامل | هزینهٔ write و فضا ×۲؛ برای spine کوچک فعلی مشکلی نیست |
| D: partial index `WHERE transaction_to IS NULL` | «دانش جاری» — کوچک و داغ | با هر correction باید invalidate شود؛ فقط query فعلی را سریع می‌کند |
| E: GiST `tstzrange` + EXCLUDE | جلوگیری از overlap، بازه‌های باز | point-lookup کندتر از btree؛ در SQLite موجود نیست |
| F: BRIN روی `transaction_from` | جدول‌های append-only بزرگ (اسکن بازه‌ای) | برای point-lookup بی‌فایده؛ فقط در حجم بالا |

**توصیه برای OCTOPUS (SQLite):** compound `(entity_id, transaction_from)` برای
زمان‌سفر + partial index دانش جاری `(entity_id) WHERE transaction_to IS NULL` +
`(entity_id, valid_from)` برای برش valid-time. در SQLite بعد از موج correction،
`ANALYZE` دوباره لازم است چون آمار توزیع کهنه می‌شود.
نکتهٔ کلیدی دیررس‌ها: برخلاف تراکنش عادی (که همیشه در *انتهای* ایندکس
transaction-time می‌نویسد)، correction روی ایندکس valid-time *وسطِ* درخت می‌نویسد؛
اگر موج اصلاحات قدیمی بیاید، نسبت page-split بالا می‌رود — پایش `sqlite stat` یا
`pgstattuple` بعد از هر موج دیررس جزو playbook است.

## ۶. موتورهای غیررابطه‌ای و نقشهٔ OCTOPUS

- **SQLite (واقعیت فعلی):** بدون range-type و EXCLUDE؛ همان چهار ستون +
  قیدهای CHECK + تریگر بازدارنده + procedure به‌شکل تابع پایتونی داخل همان
  تراکنش (`BEGIN IMMEDIATE` برای serialize).
- **Ledger JSONL append-only (الگوی فعلی ledger.jsonl):** event خام = حقیقت؛
  «نسخه» = fold رخدادها تا یک برش زمانی. query as-of = فیلتر دوگانهٔ
  `occurred_at <= T && recorded_at <= T` هنگام بازپخش. مزیت: replay deterministic؛
  ضعف: query ad-hoc کند → همان چیزی که spine.db برایش projection است.
- **MongoDB (فقط اگر stack عوض شود):** همان چهار فیلد در سند؛
  partial index `{entity_id: 1, transaction_from: 1}` با
  `partialFilterExpression: {transaction_to: null}`؛ schema validation سخت‌گیر.
- الگوی جمع‌بندی: **event store canonical + projectionهای versioned.** spine همین
  است؛ این playbook فقط projectionها را صریحاً bitemporal می‌کند.

## ۷. مکانیزم Invalidate و بازمحاسبه در Shadow

جریان الزامی برای هر fact دیررس/تصحیح:

```text
late fact (append) 
   → find dependents در derived_artifact (evidence_ids ∩ new_fact)
   → علامت‌گذاری STALE_BY_LATE_DATA (بدون حذف)
   → ساخت recomputation proposal (executable=false)
   → بازمحاسبه در Shadow با decision_time تازه
   → append نسخهٔ جدید artifact (version+1)
   → نوشتن late_arrival_receipt
```

- [FACT] `effect-shadow` همین الگو را هر beat روی خط زنده اجرا می‌کند و
  WAVE0 با fixtureهای `future.json`، `period_conflict.json`، `restart_hrv.json`
  همین مسیر را آزمود.
- [INFERENCE] هر artifact مشتق باید `evidence_cutoff` داشته باشد تا قانون
  derived-leakage قابل آزمودن بماند: summary ساخته‌شده در ۱۴:۰۰ دربارهٔ صبح،
  در replay ساعت ۱۱:۰۰ مجاز نیست — حتی اگر همهٔ شواهدش قدیمی باشند.

## ۸. Data lineage — بهترین‌ها

1. زنجیرهٔ supersession با recursive CTE قابل بازسازی باشد:

```sql
WITH RECURSIVE lineage AS (
    SELECT f.* , 0 AS depth FROM memory_fact f WHERE f.fact_id = :fact_id
    UNION ALL
    SELECT n.*, l.depth + 1 FROM memory_fact n
    JOIN lineage l ON n.supersedes_id = l.fact_id
)
SELECT fact_id, transaction_from, transaction_to, payload FROM lineage ORDER BY depth;
```

2. `provenance_ids` الزامی؛ رکورد بدون provenance = رد شدن گیت
   (`records without provenance = 0` — همان گیت WAVE0).
3. رسید برای هر رویداد دیررس با `historical_decisions_mutated=false`؛
   «affected» یعنی «با دانش امروز شاید نتیجه فرق کند»، نه بازنویسی تصمیم.
4. idempotency: `UNIQUE (source_event_id, transaction_from)` تا replay دوبارهٔ
   همان رویداد نسخهٔ تکراری نسازد.

## ۹. گیت‌های قبولی playbook

```text
late raw event retained                 = true
historical decision mutated             = false
query before recorded_at sees event     = false
query after  recorded_at sees event     = true
old correction version retained         = true
conflict silently overwritten           = false
derived artifacts invalidated           = true
recomputation executed outside Shadow   = false
direct UPDATE/DELETE on fact table      = blocked by trigger
idempotent replay of same source_event  = no duplicate version
future-use in historical replay         = 0
records without provenance              = 0
```

Invariant اصلی (وارث از طراحی دیررس سپهر):

```text
Late data may change what OCTOPUS believes now about the past,
but it must never change what OCTOPUS is recorded as having known then.
```

مسیر ارتقای وضعیت همان `NOT_VERIFIED_BITEMPORAL → VERIFIED_BITEMPORAL` است؛
بزرگ‌ترین گلوگاه فعلی نه schema، که §۰ است: دو ساعتِ واقعاً مستقل.
