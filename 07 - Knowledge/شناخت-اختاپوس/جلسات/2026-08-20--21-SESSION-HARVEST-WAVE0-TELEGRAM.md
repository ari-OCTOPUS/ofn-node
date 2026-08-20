---
type: session-harvest
status: verified
session_id: SESSION-20260820-21
session_start: 2026-08-20
session_end: 2026-08-21
baseline: 9bc506f
accepted_checkpoint: 0ad6f53
generated_from_head: e8b7415
current_head_at_final_verification: fec3288
canonical_entry: 75-SESSION-HARVEST-WAVE0-TELEGRAM-2026-08-21
superseded_by_note: "این گزارش، هدف تفصیلی نوت ۷۵ است؛ نوت ۷۵ ورودی معتبر هاروست است"
wave0: frozen-pass
wave1: locked
telegram_transport: production-closed
telegram_command_coverage: production-closed
event_bridge: in-progress
paid_calls: 0
memory_mutations: 0
---

# برداشت کامل نشست اختاپوس

## خلاصهٔ مالک

از baseline موج صفر (9bc506f) تا HEAD امروز (e8b7415، ۱۹ commit) مسیر Telegram از
یک حلقهٔ باز و بی‌گارد به سه closure تولیدی رسید: transport ماندگار
(PRODUCTION_CLOSED)، پوشش فرمان (PRODUCTION_CLOSED با پنج event واقعی)، و
running-code drift (بسته با restart کنترل‌شده). گارد canary در runtime وصل شد،
حالت‌های حقیقت تحویل با صف reconciliation کراندار ساخته شد، verifier مستقل برای
پنجرهٔ C سبز شد (5/5 تحویل + readback). صفر paid call، صفر memory write. Wave 1
قفل ماند؛ event_bridge (S-T02) و بدهی پنجرهٔ B همچنان بازند.

## از کجا شروع شدیم؟

Wave 0 recovery (موج صفر پس از WAVE0_PASS)، attribution receiptها، append-only
integrity gate، capability inventory و Loop Registry؛ سپس telegram loop از حالت
shadow به production.

## چه بحران‌هایی پیدا شدند؟

۱. heartbeat spam: `tg_bridge_once` مقدار beat را داخل hash می‌گذاشت → هر beat
پیام قدیمی را «تازه» می‌کرد (root cause ثبت: beat نباید هویت push باشد).
۲. frozen probe replay: probe قدیمی با PROBE_RESPONSE_INVALID هر بار بازپخش می‌شد.
۳. `_sig_fear` بدون identity (بدون event/task/correlation) → outbox-only شد.
۴. direct send bypass: برخی مسیرها send_text مستقیم صدا می‌زدند → مسیر Center به
durable outbox منتقل شد.
۵. crash-after-intent: intent ثبت می‌شد ولی پس از restart به‌عنوان duplicate خفه
می‌شد و task گم می‌شد → resume همان task/run.
۶. multi-message receipt: یک update چند response → receiptهای append-only مستقل.
۷. failed-send green-lie: `state=sent` با ok=false ANSWERED شمرده می‌شد →
ok=false=DELIVERY_FAILED، ok=true=DELIVERY_CONFIRMED، بدون ok=LEGACY_UNCONFIRMED.
۸. verifier regeneration: بازنویسی فایل verdict فیلدهای SUPERSEDED_BY را پاک
می‌کرد → `merge_preserved` + تست تعارض.
۹. canary guard not wired: canary_window تست داشت ولی Center صدا نمی‌زد → پنجرهٔ B
پس از اجرا post-hoc بازسازی شد؛ گارد به مسیر زنده وصل شد.
۱۰. uncertain send: بدون message_id/readback → UNCERTAIN_SEND_OUTCOME + صف
reconciliation کراندار + بدون resend خودکار.
۱۱. full-suite timeout: `self_insight.card()` ~۱۳۰ ثانیه اسکن در هر render →
journal-based.
۱۲. dark_capabilities: ۵–۸ ثانیه اسکن → cache با invalidation مبتنی بر state signature.
۱۳. Wave 0 frozen hash: whole-file hash روی ledger append-only → prefix integrity.
۱۴. conflicting verdicts: CANARY_FAILED در برابر PRODUCTION_CLOSED → یک verdict
معتبر با scope دقیق و SUPERSEDED_BY.
۱۵. running-code drift: کد ویرایش‌شده پس از start مرکز → commit + restart کنترل‌شده
+ hash manifest.
۱۶. Mimosa whole-repo blocking: بدهی OFN-Board (LANE K) جدا ماند؛ hook دور زده نشد.

## چه چیزهایی ساخته شد؟

- durable intent/outbox (durable_loop.py) با state machine و crash-resume.
- outbox-first delivery با message_key قطعی و restart-no-resend.
- canary_window guard با توالی strict و idempotency update_id.
- delivery_reconciliation: هفت حالت حقیقت تحویل + صف کراندار + OWNER_OBSERVED.
- verify_production_canary با scope پنجره (CANARY_MIN_UPDATE_ID) و merge_preserved.
- loop registry (۹ incident)، capability inventory، test registry در run_all.
- cockpit commands، STOP-TG-HEARTBEAT، kill-switch ماندگار.
- orphan watchdog (unit)، event_bridge outbox-first، receipt truth labels.
- شواهد پنجره‌های A/B/C + authoritative verdict + running-code manifest.

## چه چیزهایی واقعاً بسته شدند؟

| Loop | وضعیت | Evidence |
|---|---|---|
| S-T01 durable transport | PRODUCTION_CLOSED | 5/5 زنجیرهٔ پنجرهٔ A؛ message_ids 554/557/560/561/562 |
| LOOP-TELEGRAM-COMMAND-COVERAGE | PRODUCTION_CLOSED | پنجرهٔ C: 5/5 ترتیب strict، 5/5 تحویل (572/574/576/578/580)، 5/5 readback، verifier سبز |
| LOOP-RUNNING-CODE-DRIFT | PRODUCTION_CLOSED | commit + restart 23568→29492 + RUNNING-CODE-MANIFEST |
| LOOP-LEGACY-RECEIPT-UNCONFIRMED (پنجرهٔ B) | CONTAINED_VERIFIED | 344/346 → OWNER_OBSERVED_UNCONFIRMED_API |
| LOOP-RUN_ALL-TIMEOUT | ROOT_CAUSE_FIXED | self_insight journal |
| Unowned instant alert | CONTAINED_VERIFIED | outbox-only |

## چه چیزهایی هنوز بازند؟

| Loop | وضعیت | Closure path |
|---|---|---|
| S-T02 event_bridge | IN_PROGRESS | alert واقعی از شاخهٔ critical یا تصمیم مالک یا retirement اثبات‌شده |
| Window-B 344/346 | OWNER_OBSERVED (نه confirmed) | نیاز به message_id واقعی ندارد؛ بسته با همین برچسب |
| PROBE-INVALID | OPEN | root cause نهایی spam |
| LIVE orphan supervision | OPEN | wiring مشاهده‌ای watchdog |
| Wave 1 | LOCKED | preflight: memory gate suite بدهی pre-existing دارد |
| Calibration→improve | OPEN | verify زنجیرهٔ علی |
| Self-knowledge EMA | OPEN | جایگزینی مقدار ثابت با EMA مبتنی بر receipt |
| Cockpit tiers | OPEN | مصرف واقعی self-knowledge/calibration |
| Self-insight shadow cycle | OPEN | اجرای cycle واقعی |
| Doctor mission deadlock | OPEN | timeout/quarantine/replacement |
| brain parity | NO_BASELINE | baseline معتبر لازم است |
| OFN-Board LANE K | OPEN (جدا) | بدهی SQL/security؛ نیازمند مالک |

## خط زمانی Commitها (19 مورد، از Git)

| Commit | مأموریت | تغییر اصلی | حکم |
|---|---|---|---|
| 7836627 | probe-invalid | stop heartbeat spam؛ beat از هویت push حذف شد | OPEN |
| 99eea71 | unowned fear | contain `_sig_fear` (outbox-only)؛ shadow roundtrip | CONTAINED_VERIFIED |
| 913cbcf | shadow closure | telegram-e2e-shadow-closed | SHADOW_CLOSED |
| af12d5e | fear verified | رانِ تأیید مالک؛ canary permit | CONTAINED_VERIFIED |
| 73c495d | canary baseline | reconcile به af12d5e | READY_TO_ARM=false |
| e3040f3 | lanes B/C/D/E | wave1 authority؛ event_bridge outbox-first؛ truth labels؛ runner isolation | در جریان |
| 65d9697 | verifier | بازتولید علیه hashهای نهایی | — |
| 6dcbfe2 | lane H | capability inventory (10 قابلیت) | — |
| ca4465c | open-loops | وضعیت laneها | — |
| 84a8a96 | run_all timeout | self_insight.card journal-based (130s→fast) | ROOT_CAUSE_FIXED |
| ef2ff2f | cockpit | فرمان‌های cockpit + DEGRADED_LOCAL_ONLY + kill-switch | — |
| 0603fff | lanes status | مرکز با event_bridge روشن | — |
| 8fd7c72 | dark_capabilities | sig-keyed cache (5.5s→0s)؛ بودجهٔ slow suite؛ manifest 801 ردیف | — |
| f37eb98 | guard wiring | گارد canary به center وصل؛ delivery truth states؛ reconciliation queue | TESTED |
| 710cb45 | staging fix | canary_window extensions + merge_preserved | TESTED |
| 2acff7b | post-restart closure | RUNNING-CODE-DRIFT بسته؛ restart plan EXECUTED | PRODUCTION_CLOSED |
| b30fd04 | window C armed | پنجرهٔ C با nonce | — |
| 0ad6f53 | command coverage | پنجرهٔ C PRODUCTION_CLOSED؛ verifier سبز | PRODUCTION_CLOSED |
| e8b7415 | post-closure | owner acceptance؛ S-T02 canary؛ window-B resolution؛ wave1 preflight | در جریان |

## تصمیم‌های مالک

- **Gate scope owner-side (BLK-0005)**: Mimosa را Agent تغییر/دور نزند؛ OFN-Board جدا.
- **Authoritative verdict تک**: duplicate_effect=0 PASS؛ duplicate_content=۱ جفت observation؛
  protocol_coverage پنجرهٔ B INCOMPLETE؛ transport PRODUCTION_CLOSED؛ command coverage OPEN تا پنجرهٔ C.
- **پنجرهٔ C strict**: CANARY-01..05 دقیقاً به ترتیب، بدون تکرار؛ duplicate بدون پیشروی ثبت شود.
- **Ownership Acceptance (0ad6f53)**: transport + command coverage + drift پذیرفته‌شده؛
  S-T02، window-B، unowned alert، Wave 1 صریحاً باز.
- **Post-closure continue order**: S-T02 → window-B → wave1 preflight → شناختی → recovery.
- **Session Harvest**: ثبت مستند در Obsidian مجاز؛ memory write تولیدی ممنوع.

## درس‌های امروز (خلاصه)

heartbeat closure نیست؛ event ثابت یعنی ورودی تازه نیست؛ intent قبل از dispatch
durable شود؛ uncertain send هرگز auto-resend نشود؛ owner-visible با API-confirmed
فرق دارد؛ shadow با production فرق دارد؛ duplicate effect با duplicate content
فرق دارد؛ verifier نباید authoritative verdict را بازنویسی کند؛ append-only با
prefix integrity سنجیده شود نه whole-file hash؛ ثبت تست با اجرای تست فرق دارد؛
نمونهٔ صفر PASS نیست؛ render نباید اسکن سراسری کند؛ کد زنده باید با committed hash
تطبیق کند؛ هر loop باید closure path داشته باشد؛ blocker یک lane همهٔ laneها را
متوقف نکند. (جزئیات کامل: LEARNING-LEDGER.jsonl)

## وضعیت Waveها

- Wave 0: PASS و frozen؛ baseline 9bc506f؛ append-only gate 4/4 از کد committed.
- Wave 1: LOCKED (wave1_unlocked=false)؛ preflight 2026-08-21: ۱۶ shadow read
  (۱۱ غیرخالی، read-only)، zero mutation اثبات‌شده، اما memory gate suite بدهی
  pre-existing دارد (تست‌ها کهنه‌تر از قرارداد F3 هستند) → activation مجاز نیست.

## وضعیت Telegram

- Transport + command coverage PRODUCTION_CLOSED (پنجرهٔ C).
- گارد runtime وصل (center 29492)؛ offset 223883347؛ poll سالم.
- S-T02 IN_PROGRESS؛ event_bridge رسید اما شاخهٔ low-urgency به notif inbox
  می‌رود (طراحی)؛ شاخهٔ critical نیاز به incident واقعی دارد.
- پنجرهٔ B: 344/346 → OWNER_OBSERVED_UNCONFIRMED_API (بدون message_id جعلی).

## وضعیت Memory

- ۱۶ shadow read فقط-خواندنی؛ hash دیتابیس قبل/بعد یکسان (صفر mutation).
- write gate: بدهی تست‌های کهنه (F3) — واحد تعمیر بعدی.

## وضعیت مغزها و اندام‌ها

- doctor/self-knowledge: بدهی شناختی (EMA، tiers) باز.
- 4d/parity: NO_BASELINE تا baseline معتبر.
- Cortex: degraded-local fallback ثبت‌شده.
- Test/verification: ۵۶ تست سبز این نشست؛ ۵۱ فایل baseline failure triaged.

## اقدام بعدی

۱. تعمیر memory gate (F3 + t_h crash + timeout isolation) — blocker موج ۱.
۲. laneهای شناختی (calibration→improve، EMA، cockpit tiers، self_insight shadow).
۳. recovery (orphan watchdog observe-only، LIVE-ORPHAN، PROBE-INVALID).
۴. S-T02: منتظر alert واقعی یا تصمیم مالک.

## Evidence

- `06-EVIDENCE/SESSION-HARVEST-2026-08-21/` (inventory، timeline، ledgers، capsule، verifier)
- `_ops/state/loops/canary-coverage-2026-08-21-C/AUDIT.json`
- `_ops/state/loops/TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json`
- `_ops/state/loops/EVENT-BRIDGE-CANARY-2026-08-21.json`
- `_ops/state/waves/WAVE1-PREFLIGHT-2026-08-21.json`
