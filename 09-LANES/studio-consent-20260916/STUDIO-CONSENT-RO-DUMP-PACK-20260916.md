# STUDIO CONSENT RO DUMP PACK — 2026-09-16

| field | value |
|-------|-------|
| at_utc | 2026-09-16T03:43:32Z |
| at_aest | 2026-09-16 13:43 AEST |
| mode | READ-ONLY on 138 · HOLD_EXTERNAL · NO ofn-marketing.timer enable · NO customer_send · NO OF |
| producer | OWNER consent path / Grok Bot executor |
| node | DietPi `ari@192.168.0.138` via laptop `2edb534d-b485-4625-ad43-e92d02aa9a2d` |
| PII | names/emails/phones/handles redacted (restricted labels → `label_hash:…`; subjects → 12-char sha) |
| secrets | none pasted |

## Live DB paths (138)

| role | path | size | sha256 |
|------|------|------|--------|
| consent.sqlite | `/home/ari/.local/share/ofn/consent.sqlite` | 53248 | `abc90c214bea1a5a11b018f0fa411dc3ed71413d4822f78b731ea71462006a35` |
| studio.sqlite | `/home/ari/.local/share/ofn/studio.sqlite` | 118784 | `b6c429968ee1946c7d31e7b91d739051eda391cff7d0934c67cc6279b3071f15` |
| studio symlink | `/home/ari/ofn/data/studio.sqlite` → share studio.sqlite | — | same |
| legs consent.db (outreach) | `/home/ari/ofn/data/state/legs/consent.db` | 32768 | `a6047ff32f74e84b1aed4c06d3af59342ad0975ff60ab97b091602d82f31b443` |
| collections mirror | `/home/ari/octopus-mesh/state/studio/STUDIO-COLLECTIONS-MIRROR-20260906.json` | 2242 | `6e464035ae0cfc61fbb5a9cb61242d2a17b0a488aacd68b0e2c327b74e98b0dd` |

Variants: dated backups under `/home/ari/.local/share/ofn/backups/*/consent-*.sqlite` + `studio-*.sqlite` (RO listed; live used above). No `/home/ari/ofn/data/consent.sqlite` symlink.

## 1) consent.sqlite — schema (tables/columns only) + counts

**Tables:** `subjects`, `releases`, `draft_subjects`, `posts`

| table | columns | row_count |
|-------|---------|-----------|
| subjects | subject_id, tenant_id, display_label, created_at | **1** |
| releases | release_id, subject_id, scope, signed_at, expires_at, document_ref, document_sha256, recorded_by, revoked_at | **1** |
| draft_subjects | draft_id, subject_id, added_by, added_at | **23** |
| posts | post_id, tenant_id, draft_id, platform, external_id, published_at | **0** |

### Consent status aggregates (honest)

There is **no** `VERIFIED` / `pending` / `denied` column on studio `consent.sqlite`. Map-level status is derived:

| metric | count | note |
|--------|------:|------|
| **VERIFIED (collection-map)** | **0** | no owner+Saba+182 artifact cites a collection_id |
| active releases (`revoked_at` NULL) | 1 | scope=`telegram_channel` only |
| revoked releases | 0 | |
| posts published | 0 | |
| subjects | 1 | label redacted |
| release wired to collection_id | **0** | **no `collection_id` column** on `releases` |
| `has_collection_id_in_scope` | false | scope string has no collection |

**Release (non-PII):** `release_id=rel-self-tg-20260822-124450z` · scope=`telegram_channel` · `document_sha256=cfa1f67d53415c8d7ca47844c9714844ab4899a31e1040305617f86c2493ebfe` · doc=`…/consent-docs/owner-release-self-telegram-20260822-124450z.md` · not collection-wired.

**subjects (redacted):** `subject_id_hash=06c604b332b3` · tenant=`studio` · `display_label_hash=fc0eb632a320`

### legs/consent.db (separate outreach store)

| table | row_count | status aggs |
|-------|----------:|-------------|
| consent_current | 0 | empty |
| consent_events | 0 | empty |
| suppression | 0 | empty |

Not used for studio collection map.

## 2) studio.sqlite — collections inventory

**Tables + counts:** collections=3 · media_items=22 · drafts=24 · draft_media=23 · media_sent=0 · media_labels=3 · draft_labels=0 · advisor_findings=0 · id_high_water=3

**sensitivity agg:** general=1 · restricted=2

| collection_id | title (redacted) | slug | sensitivity | created_at | media direct | drafts |
|---------------|------------------|------|-------------|------------:|-------------:|-------:|
| album-0001 | label_hash:c8ff03f42c55 | album-0001 | restricted | 1785939708 | **0** | 0 |
| album-0002 | label_hash:c60d8e634169 | album-0002 | restricted | 1786009176 | **2** (shot-0002, shot-0020) | 0 |
| album-unlock-20260822 | unlock-queue | album-unlock-20260822 | general | 1787402492 | **0** | **23** |

**media_by_collection_id:** `None`/NULL=20 · `album-0002`=2 · unlock direct=0  
**drafts_by_status:** draft=24  
**Unlock bind path:** `draft_media.media_ref` = `studio/shot-NNNN/0-1600.jpg` → resolves to **22 unique** `shot-0001`…`shot-0022` (not via `media_items.collection_id`).

### Wire docs vs live dirs

| artifact | status |
|----------|--------|
| Season/HQ map placeholders `RESTRICTED-UNKNOWN-1/2` | **REPLACED** by live `album-0001`, `album-0002` |
| Mirror on 138 | PRESENT · inventory matches live counts |
| photos tree | `/home/ari/.local/share/ofn/photos/studio/shot-*/` · 66 files |
| consent-docs | 8 files (1 release cited by sqlite + drafts/health json) |
| gates.json | owner_release / kill_switch / secret_rotation closed; `agent_may_open=false` |
| ofn-marketing.timer | **disabled / inactive / dead** (RO `systemctl`; **not enabled this run**) |

### Missing for consent→collection map

1. Partner (Saba) written attestation naming collection_id + media ids  
2. Owner written attestation per collection (owned marketing proposals only)  
3. `releases` → `collection_id` link (schema gap: no column; current scope telegram-only)  
4. 182 scoped witness receipt naming collection_ids  
5. Map row flip to VERIFIED (docs-only; agents do not flip)  
6. Separate owner GO + 182 OK before any timer enable (still HOLD)

## 3) Checklist score vs STUDIO-CONSENT-CHECKLIST.md

Scoring boxes: Preconditions (3) + per-collection A(4)×3 + B(4)×3 + C(3)×3 + D(3)×3 = **3 + 42 = 45** checklist atoms.  
Also batch-unlock gate kept FAIL_CLOSED (not scored as green for enable).

| area | green | red | unknown | notes |
|------|------:|----:|--------:|-------|
| Preconditions | 3 | 0 | 0 | map read; live ids exported; timer disabled |
| A Identity (×3) | 11 | 1 | 0 | album-0001 media list empty (0 rows) → 1 red |
| B Consent evidence (×3) | 1 | 11 | 0 | release doc path exists but not collection-wired; Saba/owner collection attest missing |
| C Attestors (×3) | 0 | 9 | 0 | no owner/Saba/182 collection-scoped signs |
| D Status update (×3) | 3 | 6 | 0 | eligible correctly **no**; VERIFIED not flipped; receipt updated by this pack |
| **TOTAL** | **18** | **27** | **0** | **score 18/45 = 40%** |

**VERIFIED count (map rows): 0 / 3**  
**ofn-marketing_eligible: no / no / no**

### Per-row consent_status (updated live ids)

| collection_id | consent_status | ofn-marketing_eligible |
|---------------|----------------|------------------------|
| album-unlock-20260822 | UNVERIFIED | no |
| album-0001 | UNVERIFIED | no |
| album-0002 | UNVERIFIED | no |

## 4) Saba attest media CSVs (priority pivot)

Dir: `/workspace/octopus-hq/wiring/studio-consent-20260916/`  
Vault mirrors: `F:\backup\00-SEASON\studio-consent-20260916\` · `F:\backup\09-LANES\studio-consent-20260916\`

| file | sha256 |
|------|--------|
| collections-138.csv | `05b4af4e6e92821cc1adca3c062425216bccb9b81f57972620b66bf51e10fc47` |
| media-album-unlock-20260822-138.csv | `ee6f2924f3c4a5420a4625cd7fc243e7739e13051da61750a28bc925f0d59260` |
| media-restricted-albums-138.csv | `ebda6338c252df4f8a21b0a4538386bff52ebb3d581a55b59a47d0fbfed48ac9` |
| media-items-attest-bind-138.csv | `ee6f2924f3c4a5420a4625cd7fc243e7739e13051da61750a28bc925f0d59260` |
| media-items-direct-collection-138.csv | `46795fed948aa8a6aaf1eb098025d3e4651e5ad7877530a094624690fb65c6c5` |
| draft-media-unlock-138.csv | `c0b35914a8c83c09074fe2ea68540d151262eac2d2f8a31cb3d1b746c16dd7bb` |
| SUMMARY.json | `33501da05d1a4c04871b8fe9b508aae2e35555a93329f68b09af244c6a99571d` |

**Media ids (max 30) for unlock attest bind via drafts:**  
shot-0001, shot-0002, shot-0003, shot-0004, shot-0005, shot-0006, shot-0007, shot-0008, shot-0009, shot-0010, shot-0011, shot-0012, shot-0013, shot-0014, shot-0015, shot-0016, shot-0017, shot-0018, shot-0019, shot-0020, shot-0021, shot-0022  

**Restricted direct:** shot-0002, shot-0020 on `album-0002` only · `album-0001` = 0 media.

Paths are `studio/shot-NNNN/{0-1600,0-320,0-original}.jpg` under photos — no token/cookie segments.

## 5) Timer / external holds (unchanged)

```
UnitFileState=disabled
ActiveState=inactive
SubState=dead
```

**NO enable performed. NO OF. NO customer_send. HOLD_EXTERNAL.**

## 6) Blockers for U3 (no timer enable)

1. **VERIFIED=0** — no collection row may unlock marketing  
2. **Saba attest missing** — need written media/collection authorization (CSVs above are the bind list)  
3. **Owner collection attest missing** — self-TG release ≠ collection wire  
4. **releases↔collection_id schema/link gap**  
5. **182 scoped OK missing** for named collection_ids  
6. **Policy:** ofn-marketing.timer stays KEEP_DISABLED until map VERIFIED + owner GO + 182 scoped OK (separate enable prompt)  
7. album-0001 empty of media — attest/bind unclear until media assigned or collection retired

## Companion JSON

See `STUDIO-CONSENT-RO-DUMP-PACK-20260916.json` (counts only).

— RO only · FAIL_CLOSED publish · no invent VERIFIED
