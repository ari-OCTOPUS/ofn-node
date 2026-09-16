# PROPOSED_DIFFS

این diffها **اعمال نشده‌اند**. فقط پیشنهاد برای مرور مالک. Live files دست نخورده‌اند مگر موارد صریح مجاز این جلسه (تست‌ها، Doctor read-only، unsigned checkpoint export، اشارهٔ handoff به owner-review).

| File/service | Exact change (proposed) | Risk | Validation | Rollback |
|---|---|---|---|---|
| `/opt/octopus/scripts/skill_tracker_loop.py` | قبل از `ledger.append(outcome)` اگر `resolved_at_ns < issued_at_ns` باشد outcome را رد کن (`exclusion_reason=stale_timestamp`) و append نکن | کم؛ فقط رد رکورد بد | pytest INV-05 + ledger_verify | git/restore script copy |
| `/opt/octopus/cognition/src/octopus_cognition/metacontrol/gate.py` | برای Wave0 هرگز `PLAN_ALLOWED` با `executable=True` برنگردان؛ نام `PLAN_ALLOWED_ADVISORY` را به‌عنوان alias برای `PLAN_RECOMMENDED` با `executable=False` اضافه کن؛ planner import ممنوع بماند | متوسط اگر profile اشتباه پاس شود | pytest INV-12/13 | restore gate.py |
| `/opt/octopus/shadow_validation/src/octopus_shadow/ledger.py` | در `outcome()` اگر `resolved_at_ns < prediction.issued_at_ns` → `LedgerError("outcome_timestamp_before_prediction")` | فقط staging | pytest shadow INV-05 | restore ledger.py |
| live `octopus-world-model.service` | **هیچ**. candidate WM جدا، خارج از مسیر زنده | جایگزینی زنده ممنوع | T4 off-path only | n/a |
| `octopus-shadow-validation.service` | enable نکن؛ :9464 bind نکن | اگر enable شود ممکن است فایل status بنویسد | unit-file remains disabled | n/a |
| GAP-002 apply | فقط پس از bundle امضاشدهٔ لپ‌تاپ با head مطابق live | بستن دروغین GAP | apply_signed_inbound verify | remaining unsigned |
| Reflex ARMED.json | **هیچ تغییری** تا OA-T7 | بالا | Doctor + criteria | n/a |
| FastAPI / docker / :8080 | **deploy نشود** | سطح حمله LAN | ss must stay empty | n/a |
| `/etc/octopus/config/registry.yaml` | فقط از SIGNED-REGISTRY-BUNDLE با root-v2 | تغییر unsigned ممنوع | G2 digest | config-history backup |

هیچ unified diff روی فایل زنده اعمال نشده است.
