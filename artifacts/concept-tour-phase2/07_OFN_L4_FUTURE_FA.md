# OFN-L4: اسکلت آینده، نه runtime امروز

## inventory کامل

درخت `/opt/octopus/ofn-l4` دقیقاً ۱۰ فایل داشت:

1. `ofnl4/__init__.py` — identity ثابت، نسخه preflight و claimهای false. `[LOCAL-SCAFFOLD] :1-13`.
2. `ofnl4/config.py` — pathهای هدف، envelopeها، periodها، port 8091 و `PROPOSE_ONLY`. `[LOCAL-SCAFFOLD] :7-46`.
3. `ofnl4/contracts.py` — event schema v2، UUID7-like، monotonic ns، UTC، causal parents، severity/confidence و identity before/after. `[LOCAL-CODE] :13-31,34-125`.
4. `ofnl4/store.py` — schema events/identity/episodes/theta/proposals/meta و commit پایه. `[LOCAL-CODE] :13-79,96-147`.
5. `ofnl4/identity.py` — ledger v2 با event_id و internal verification. `[LOCAL-CODE] :12-43,54-138`.
6. `ofnl4/body.py` — memory/load/temp/disk measurement و material delta. `[LOCAL-CODE] :33-104`.
7. `ofnl4/homeostat.py` — component error، max error و state deterministic. `[LOCAL-CODE] :14-63`.
8. `ofnl4/arbiter.py` — allow/deny actها و owner-required response. `[LOCAL-CODE] :5-54`.
9. `ofnl4/theta.py` — Δθ pure engineering score و threshold. `[LOCAL-CODE] :7-48`.
10. `docs/SCALE-AND-ACTIVE-INFERENCE.md` — WBE، Active Inference و vLLM/Hybrid design. `[DOCUMENTED] :1-18,148-234,238-340`.

هیچ فایل دیگری، subdirectory runtime، test یا artifact اجرایی در این ریشه نبود. `[RUNTIME-VERIFIED] recursive inventory`.

### استعارهٔ «کشتی روی خشک‌کن»

A) **Vibe Coding:** قطعات کشتی آینده روی خشک‌کن چیده شده‌اند، اما موتور/خدمه/آب ندارد.  
B) **ترجمهٔ مهندسی:** pure modules و schema حاضرند، orchestration و deployment غایب‌اند.  
C) **محدودیت:** وجود scaffold به معنی process، policy loop، سلامت یا حیات نیست.

## آنچه implementation دارد

- contract v2 با زمان monotonic و causal parents
- event validation و canonical hash
- SQLite schema پیشنهادی
- body signal و material delta
- homeostatic error/state
- deterministic safety arbiter
- identity chain v2
- engineering Δθ

این‌ها `IMPLEMENTED_DISCONNECTED` یا `SCAFFOLD` هستند، نه `LIVE`.

## آنچه صریحاً غایب است

- daemon/main loop
- HTTP server و listener `8091`
- systemd unit
- runtime DB و `var/`
- test file
- package/runtime `pymdp`
- A/B/C/D/E model واقعی
- belief update و `infer_policies`
- scheduler/policy loop
- event→identity atomic orchestration
- outbox، dispatch و replay
- writer برای `episodes`
- writer برای `theta_ticks`
- writer برای `proposals`
- public status/letter writer loop
- owner gate file validation و state machine rollout
- v1↔v2 bridge

`[BLOCKED] listener 8091 absent؛ /opt/octopus/ofn-l4/var absent؛ no systemd match؛ no tests؛ pymdp module absent؛ INSERT search فقط events را یافت`.

## نکات طراحی

- v2 event نسبت به v1 غنی‌تر است: node/boot، monotonic time، causal parents، severity/source/value/unit/confidence، identity hashes و owner flag. `[LOCAL-CODE] contracts.py:13-31`.
- store فقط event را transactionally commit می‌کند؛ outbox ندارد و identity append transaction جدا دارد. در نتیجه هنوز semantics «commit-before-dispatch + identity coupling» نسخهٔ زنده را بازتولید نمی‌کند. `[LOCAL-CODE] store.py:96-133؛ identity.py:106-138`.
- `theta_ticks.event_id` و `proposals.event_id` FK صریح ندارند؛ writer هم وجود ندارد. `[LOCAL-SCAFFOLD] store.py:43-60`.
- homeostat L4 thermal critical را مستقیم `SAFE_HALT` می‌کند؛ نسخهٔ زنده از margin ده درجه استفاده می‌کند. این دو semantics باید ADR مشترک داشته باشند. `[CONFLICT] ofnl4/body.py:91-104؛ ofnl4/homeostat.py:54-63؛ live homeostasis/core.py:76-93`.
- `ALIVE_CLAIM=False` و `CONSCIOUS_CLAIM=False` مانع overclaim صحیح است. `[LOCAL-SCAFFOLD] ofnl4/__init__.py:1-13`.

## bridge لازم از v1 به v2

bridge آینده باید حداقل این قراردادها را داشته باشد:

1. **Mapping schema:** `v1_event_id → v2_event_id` با uniqueness و idempotency؛ هیچ event قدیمی rewrite نشود.
2. **Hash preservation:** hash و body v1 به‌عنوان opaque provenance داخل `extra` یا migration table نگه‌داری شود؛ با hash v2 جایگزین نشود.
3. **Time mapping:** `created_at` wall-clock v1 هرگز به‌عنوان monotonic v2 جعل نشود؛ migration event زمان ثبت و original timestamp جدا داشته باشد.
4. **Causality:** causal parents فقط وقتی evidence دارد ساخته شود؛ ترتیب node_seq به‌تنهایی causal graph کامل نیست.
5. **Identity anchor:** terminal hash v1 در اولین migration/genesis-extension v2 ثبت شود، ولی دو chain یکی اعلام نشوند.
6. **Outbox parity:** event+outbox و dispatch/replay semantics قبل از هر daemon برقرار شود.
7. **Episode provenance:** source/type matching و uniqueness v1 حفظ شود.
8. **Owner gate:** هر proposal/action در arbiter و explicit owner reference عبور کند؛ `PROPOSE_ONLY` default بماند.
9. **Shadow validation:** ابتدا read-only dual projection، سپس comparison receipts؛ هیچ writer دوگانه بدون rollback plan.
10. **Tests:** corruption، replay، crash-between-commit/dispatch، boot continuity، source mismatch و downgrade/rollback.

## معیار خروج از scaffold

تا زمانی که daemon، tests، outbox/replay، writers، public state، owner gate و bridge وجود ندارد، status باید `SCAFFOLD` بماند. port/config declaration یا file presence activation نیست.

WBE و Active Inference این scaffold در [08_WBE_CONCEPT_FA.md](08_WBE_CONCEPT_FA.md) و [09_ACTIVE_INFERENCE_CONCEPT_FA.md](09_ACTIVE_INFERENCE_CONCEPT_FA.md) باز شده‌اند.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
