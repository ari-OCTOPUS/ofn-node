---
type: truth-note
section: contradictions
created: 2026-08-15
status: open — هیچ تناقضی بدون رأی مالک «حل» نشده
rule: "هر دو مقدار ثبت می‌شوند؛ در صورت شواهد قوی فقط `likely` می‌نویسیم و status را open نگه می‌داریم"
---

# CONTRADICTIONS — ثبت تناقضات (STEP 7 مگاپرامپت)

```yaml
contradiction:
  id: C-001
  claim: "تعداد تست NBB-CP"
  value_a: 207
  source_a: "03 - Projects/NBB-Control-Plane/MANIFEST.yaml (2026-07-11) — «83 l0 + 102 l1 + 5 l2 + 17 import-lint»؛ README ریشه هم ۲۰۷ می‌گوید"
  value_b: 171
  source_b: "03 - Projects/NBB-Control-Plane/BACKUP-README.txt (2026-07-11) — «Head: 02561ea (171 tests green)»"
  live_check: "2026-08-15: py -m pytest -o addopts= -q → 171 passed in 2.50s"
  likely: value_b
  resolution: null
  status: open
```

```yaml
contradiction:
  id: C-002
  claim: "اعداد وضعیت ارگانیسم (coherence/beat)"
  value_a: "coherence=0.958, beat=36436"
  source_a: "مگاپرامپت مالک (2026-08-15)"
  value_b: "coherence=0.95, beat=36563"
  source_b: "OCTOPUS/CURRENT-TRUTH.md — بلوک auto 2026-08-15T04:10:09Z (runtime)"
  live_check: "خواندن مستقیم فایل در همین جلسه — مطابق value_b"
  likely: value_b
  resolution: null
  status: open
  note: "اختلاف likely ناشی از فاصلهٔ زمانی خواندن است (beat جلو می‌رود)؛ ولی طبق قاعده هر دو ثبت شد."
```

```yaml
contradiction:
  id: C-003
  claim: "سلامت سوئیت تست hypothesis_engine"
  value_a: "«۵ سوییت سبز» (فریم‌ورک deceptive-grid، ۹ سناریو + ablation + red-team)"
  source_a: "OCTOPUS/CURRENT-TRUTH.md — بخش 2026-08-13"
  value_b: "ImportError در collection: cannot import name 'falsified_assists_at' from 'deceptive_grid' (_ops/hypothesis_engine/experiments/deceptive_grid.py)"
  source_b: "اجرای زنده 2026-08-15: py -m pytest -q در _ops/hypothesis_engine"
  live_check: "بازتولیدپذیر در همین محیط (Python 3.13، بدون venv اختصاصی)"
  likely: "علت = ویرایشِ uncommitted درخت کاری، نه کد کامیت‌شده — git show HEAD شامل falsified_assists_at است (۲ بار) ولی درخت کاری (−۳۶۴ خط/+۶۷، uncommitted و pre-existing) صفر بار داشت"
  resolution: "owner_verdict NEW-4 (2026-08-15): بازگردانی با git stash قبلش — اجرا شد: git stash push مسیر-مشخص → stash@{0} (ویرایش آرشیو شد، حذف نشد) → اجرای مجدد تست‌ها: 23 passed in 1.53s ✅"
  status: resolved (رأی مالک + اجرای زندهٔ مجدد، 2026-08-15)
```

```yaml
contradiction:
  id: C-004
  claim: "محل NBB-CP حاکم"
  value_a: "app/NBB-CP — «۲۰۷ تست سبز»"
  source_a: "README.md ریشه (2026-08-10)"
  value_b: "app/ حذف شده در کامیت ea69126 (پاکسازی 2026-08-03)؛ نسخه‌های زنده در 03 - Projects/NBB-Control-Plane و 4d_system/*"
  source_b: "git log --diff-filter=D + بررسی درخت فایل‌سیستم 2026-08-15"
  live_check: "ls /f/backup/app → وجود ندارد"
  likely: value_b
  resolution: "R22 جاروی بدهی (2026-08-16): README ریشه اصلاح شد — ارجاع stale به app/NBB-CP حذف شد (سطح A: grep منفی)"
  status: resolved (README corrected — grep verify)
  note: "رأی مالک 2026-08-15 دربارهٔ نسخه‌ها: «همش منم» — چهار نسخه یک پروژه‌اند."
```

```yaml
contradiction:
  id: C-005
  claim: "وجود ADR-041 (رصدخانهٔ اینترنت)"
  value_a: "ADR-041 به‌عنوان سند رصدخانهٔ اینترنت (allowlist، gateway)"
  source_a: "مگاپرامپت مالک (2026-08-15)"
  value_b: "ADR-041 در هیچ‌جا نیست؛ دنبالهٔ پوشهٔ adr از ADR-040 به ADR-042 می‌پرد (024–032 هم غایب)"
  source_b: "جستجوی نام+محتوا+git history --all در F:\backup و ۱۰ Vault دیگر (2026-08-15)"
  live_check: "ls 03 - Projects/research-spec-compiler/adr/"
  likely: null
  resolution: "owner_verdict NEW-2 + اجرای --apply (2026-08-15 17:09): موتور octopus_sync سند را نوشت → 03 - Projects/research-spec-compiler/adr/ADR-041-internet-observatory.md — پرش ۰۴۰→۰۴۲ بسته شد ✅"
  status: resolved (applied)
  note: "گزارش نشست رصدخانه §10 نیز همین کار را به‌عنوان آیتم باز ۷ فهرست کرده بود."
```

```yaml
contradiction:
  id: C-006
  claim: "تعداد تست سبز کل (۴۱۴ یا ۴۰۸)"
  value_a: 414
  source_a: "CHECKPOINT (به ادعای مگاپرامپت؛ خود CHECKPOINT.md پیدا نشد)"
  value_b: 408
  source_b: "پیام کامیت (به ادعای مگاپرامپت؛ git log --all --grep ۴۰۸/۴۱۴ → خالی — تاریخچه در ea69126 اسکواش شده)"
  live_check: "اجرای کاملِ رسمی 2026-08-15 شب (جاروی تست T2): python -X utf8 run_all.py — نخستین اجرای کاملِ ثبت‌شده در تاریخ (لاگ: _ops/tests/_baselines/run-all-output-20260815-sweep.log)"
  likely: "هر دو عدد کهنه/رتوریکی بودند — سوئیت واقعی بسیار بزرگ‌تر است"
  resolution: "فکت زنده: ۲۵۶ فایل تست در رانر رسمی → ۲۴۰ فایل سبز (خودگزارشیِ ۲۹۳۱/۲۹۳۱ چک) + ۱۶ فایلِ شکست‌خورده که ۱۵ تايش pre-existing (دریفِ تست↔کدِ زنده ×۹ · API drift ×4 · محیط/سرویس ×2 — از جمله 429 واقعیِ Fugu و بازبودن circuit breaker همان‌جا) و ۱ تای آن (consolidation_latent) فیکس همین نشست شد و در اجرای مجدد سبز است. علتِ «INTERNALERROR از ریشه»: تست‌های _ops اسکریپتِ خوداعتبارسنج‌اند (بدون def test_) — pytest از ریشه اساساً ابزارِ درستِ جمع‌زدنِ این سوئیت نیست؛ رانر رسمی همان run_all.py است"
  status: resolved (با نخستین اجرای کاملِ رسمی — 2026-08-15 شب)
  note: "هیچ‌کدام از ۱۵ شکستِ باقی‌مانده consolidation یا فایل‌های تغییرِ این نشست را import نمی‌کنند (بررسیِ import انجام شد)"
```

```yaml
contradiction:
  id: C-007
  claim: "تعداد تست سبز epistemics (ADR-039)"
  value_a: 133
  source_a: "سربرگ ADR-039 («C1-C4 پیاده و تست‌شده (۱۳۳ تست سبز)»)"
  value_b: "45/45 + 20/20 = 65"
  source_b: "OCTOPUS/CURRENT-TRUTH.md — بخش 2026-08-13"
  live_check: "سوئیت واقعی 2026-08-15 شب (جاروی تست T3): تست‌های _ops اسکریپتِ خوداعتبارسنج‌اند (بدون def test_) — برای همین pytest صفر collect می‌کرد. اجرای مستقیم ۱۵ فایل: همگی exit 0"
  likely: "هر دو عدد جزئی/کهنه بودند — عددِ زنده بزرگ‌تر از هر دو است"
  resolution: "خانوادهٔ epistemics (۱۱ فایلِ هسته): 45+20+6+9+8+19+11+24+14+13+8 = ۱۷۷ چکِ سبز، صفر شکست (+۴ فایلِ مجاور: ۳۷ چک → ۲۱۴). «۴۵/۴۵+۲۰/۲۰» دقیقاً دو فایلِ schemas و receipt_chain بود؛ ۱۳۳ به هیچ فایلِ فعلی نگاشت نشد (تاریخی)"
  status: resolved (با اجرای زندهٔ کامل — 2026-08-15 شب)
```

## روش نهایی

۱. هر دو مقدار ثبت شد. ۲. هیچ مقداری حذف/بازنویسی نشد. ۳. `likely` فقط نظر شواهدی است، نه رأی. ۴. resolution فقط با مالک یا runtime معتبر پر می‌شود.

```yaml
contradiction:
  id: C-009
  claim: "دکمه‌های تأیید/رد کارت‌های دکتر کار می‌کنند"
  value_a: "کارت با reply_markup ok/no ارسال می‌شود (ok:true) — به‌ظاهر کامل"
  source_a: "tg-outbox.jsonl — رسیدهای ارسال 2026-08-15 شب"
  value_b: "تپ مالک → پاسخ «نادیده»؛ رأی هرگز در tg-inbox.jsonl ثبت نمی‌شود"
  source_b: "گزارش مستقیم مالک 2026-08-15 شب + center.py:3308 («command ناشناس نادیده») + کانال دکتر mode=direct بدون OWNS_POLLING"
  live_check: "center فقط فعل‌های mo:/m:/توکن‌دار را route می‌کند؛ فرمت ok:intent: در واژگانش نیست"
  likely: "طراحی صدای اشتراکی ناقص است — دکمه به مقصد ندارد بدون ربات اختصاصی دکتر"
  resolution: "پیشنهاد دوگانه: (فوری) تایید چتی + (اصلی) ربات اختصاصی BotFather → OCTOPUS_DOCTOR_BOT_TOKEN جدید + OWNS_POLLING=1"
  status: open — owner_action
  note: "هم‌خانوادهٔ کشف 2026-07-28 (test_bridge_buttons.py: ۲۹ دکمهٔ در حال افتادن) — طبقهٔ باگ یکسان: مسیر رأی مالک بی‌صدا می‌میرد"
```

**به‌روزرسانی C-009 (2026-08-15 ~18:17):** پل ساخته و مستقر شد — هوک سه‌بخشی قبل از جدولِ verb در center.py + `_doctor_ingest` (importlib فایل‌لود به‌خاطر سایهٔ پکیج `_ops/doctor`) + ۵ تست سبز + کامیت «feat(center): doctor vote bridge». منتظر تپِ مالک روی همان دکمه‌ها برای تأیید حل کامل.

**✅ C-009 RESOLVED (2026-08-15 ~18:22):** پل رأی دکتر (کامیت feat(center)) مستقر شد و **۷ رأی واقعی مالک همان شب از همان دکمه‌ها ثبت شد** (هر سه کارت تایید؛ رأی‌دهنده با چت مالک تطبیق شد). یافتم جانبی: کارت‌ها دو مسیر داشتند (ارسال مستقیم ربات اصلی + پخش relay ربات center) — فقط دکمه‌های نسخهٔ center به poller می‌رسند؛ پیشنهاد آینده: حالت دکتر به outbox برگردد تا relay تنها صدای واحد باشد (نویز دو-copy برود).


---

## 📛 قانون تخصیص شناسهٔ تناقض (مستقر به حکم مالک — 2026-08-15 شب، پس از برخورد C-008)

1. شناسه‌ها فقط از **یک شمارندهٔ واحد** — آزاد بعدی: **C-034** (C-033 در 2026-08-16 ~16:3x: فایل‌های dir-TCB مثل core/model.py در digest-map نیستند؛ C-032 در 2026-08-16 ~15:4x: کاکپیت ابسیدین «validator زنده» با اسنپ‌شات ۰۷-۰۵؛ C-031 در 2026-08-16 ~15:1x: پنج کپی یک مشاهده در epistemics 0.1→0.9998؛ C-030 در 2026-08-16 ~14:2x: money_gate مبلغ منفی را allow می‌کرد؛ C-029 در 2026-08-16 ~14:2x: DARE با |ρ|=1 در TCB core می‌ترکد؛ C-028 در 2026-08-16 ~13:2x: verify() دمِ ledger را نمی‌بیند؛ C-027 در 2026-08-16 ~13:2x: deadline_cycles خودهدف اجرا نمی‌شد؛ C-026 در 2026-08-16 ~13:1x: self_code approve/reject بی‌گیتِ enabled()؛ C-025 در 2026-08-16 ~12:5x: دریفت نرمال‌سازی family_key پایتون/SQL؛ C-024 در 2026-08-16 ~12:0x: SELF_CODE در env دیمون نه flags.cmd؛ C-023: پوش agent-decided بدون «one word»؛ C-022: اسنپ‌شات circuit closed بدون ریکاوری اثبات‌شده؛ C-021: NaN در hash-as-float32 حلقهٔ recall؛ C-020: DEPRECATED.md لانچ 4d؛ C-019: docstringِ ConsolidationCycle/daemon؛ C-018: پیش‌فرض کهنهٔ PHASE01؛ C-017: DOCTOR_USE_CENTRAL_ROUTER — resolved؛ C-016: دریچهٔ فرار معمار؛ C-015: COUNCIL-MESH کهنه؛ C-014: fetch دوتایی؛ C-013: TCB)
2. قبل از تخصیص، `C-0NN` روی **هر دو مخزن** grep شود: `F:ackup` و working repo
3. دو ایجنتِ هم‌زمان بدون شمارندهٔ مشترک = برخوردِ حتمی (این‌طور C-008 دوبار ثبت شد)

```yaml
contradiction:
  id: C-008
  claim: "فرمول hash انبار شاهد نامعلوم بود (none of 15 candidates matched)"
  source_a: "موتور sync (verifier تعبیه‌شده با کاندیدهای قدیمی) — ثبت ~18:06 در پک"
  source_b: "scripts/verify_live_store.py اصلاح‌شده با src-formula — PASS 27/27 (17:1x)"
  resolution: "resolved — فرمول عین سورس بازتولید شد (evidence_store.py:125-130 + prediction_registry.py:91)؛ نسخهٔ تعبیه‌شدهٔ موتور همچنان کاندیدهای قدیمی دارد تا به‌روزرسانی صاحبش"
  status: resolved (روش حل: افزودن کاندید صحیح، نه تغییر کد انبار)
  cross_ref: "C-009 (پل رأی دکتر) — برخورد نام‌گذاری همین دو رکورد بود"
```

> **یادداشت تاریخی:** کامیت‌های `3156316` و `0823ce5` (پیش از این حکم) با «C-008» منظورشان پل رأی دکتر بود — پس از حکم، همان موضوع **C-009** است. تاریخ git تغییرناک است؛ این یادداشت مترجم آن است.

```yaml
contradiction:
  id: C-010
  claim: "مسیر پولیِ مغز (هر provider) سالم است"
  value_a: "deepseek secondary در 13:36 کار می‌کرد (paid-calls.jsonl)"
  source_a: "_ops/state/paid-calls.jsonl — رکورد 2026-08-15T13:36:39"
  value_b: "JSONDecodeError: Unexpected UTF-8 BOM در circuit_breaker._load_state → کل _ask_paid قبل از تماس می‌شکست"
  source_b: "اجرای زندهٔ probe در 19:2x + فایل _ops/state/circuit-state.json دارای BOM"
  resolution: "BOM از فایل strip شد (19:2x) → probe فوری ok:True؛ سخت‌سازی opslib.read با utf-8-sig = پیشنهاد (core مشترک، نیازمند تست در همان commit)"
  status: resolved (data-fix) — hardening proposed
  root_cause_fa: "BOM اثرِ نوشتن با PowerShell (Set-Content/Out-File پیش‌فرض BOM می‌نویسند) — درس: فایل‌های state هرگز با PowerShell نوشته نشوند یا خواننده BOM-تابلنت شود"
  registered_by: "laptop-agent (grep دو-مخزن انجام شد — قانون شناسه C-009 رعایت شد)"
```

```yaml
contradiction:
  id: C-011
  claim: "پیش‌بینی‌گر بیزی روی هر ورودی JSON معتبر graceful است"
  value_a: "ورودی‌های خالی/غیر-JSON/mag-تهی → fallback امن 0.490 (پروب جعبه‌سیاه)"
  source_a: "ماتریس استحکام 2026-08-15 شب — ۸ حالت"
  value_b: "«features: null» → TypeError: len(None) — کرش"
  source_b: "همان پروب؛ runner با fallback خودش زنده ماند ولی ماژول می‌شکست"
  resolution: "fixed همان شب: null-safe + تست (21/21 سبز) — تست-در-همان-کامیت"
  status: resolved (fix + test)
  registered_by: "laptop-agent (grep دو-مخزن: فقط رزروِ خودم)"
```

```yaml
contradiction:
  id: C-012
  claim: "مغز 4d یک حلقهٔ یادگیری دارد (حافظه وارد تصمیم می‌شود)"
  value_a: "مستندات/نام‌ها: hypothesis/experiment/memory — سیستمِ یادگیری"
  source_a: "4d_system/brain/automation.py و اسنادش"
  value_b: "automation.py: ۳ ارجاع نوشتن (save_*)، صفر خواندن (query/get_pending/search_vault) — حافظه write-only بود"
  source_b: "grep سطح A — 2026-08-15 شب؛ یافتهٔ مستقلِ ایجنت-معمار موازی + تأیید معمار ارشد؛ هم‌خانوادهٔ یافتهٔ «consolidation راکد» (MINDS.md)"
  resolution: "فاز صفر اجرا شد (2026-08-15 شب، جاروی تست T1): patch به مسیر اصلی automation وصل شد (introspect/create/conclude هر سه قبل از تصمیم می‌خوانند) + dedup + read-back از مسیر مصرف‌کننده + stale با transaction_time + تست ۱۲/۱۲. شاهد telemetry زنده: memory_read_before_decision_ratio=1.0 (18/18) · memory_readback_success_ratio=1.0 · از ۸ create فقط ۱ نوشت (dedup روی انبوهِ ۱۰۶۲ pending). جزئیات: [[../04-SYSTEMS/MEMORY-LOOP|MEMORY-LOOP]]"
  status: resolved (فاز صفر — با شاهد telemetry زنده؛ شرط معمار ارشد برآورده شد)
  registered_by: "senior-architect (grep دو-مخزن: C-012 خالی بود)"
  resolved_by: "test-sweep agent 2026-08-15 شب"
```

```yaml
contradiction:
  id: C-013
  claim: "گاردِ خودتغییریِ مغز 4d فقط TCB را می‌بندد و فایل‌های برگ را مجاز می‌داند"
  value_a: "تست‌های test_self_code_gate: data/real_api.py و ui/visuals.py و memory/store.py «باید مجاز باشند»"
  source_a: "4d_system/tests/test_self_code_gate.py:28-30 (خواستهٔ طراحی)"
  value_b: "اجرای زنده: هر سه (و هر فایل دیگری) رد می‌شوند — «فایلِ هسته‌ی موردِاعتماد (TCB)»"
  source_b: "python -c guardrails.assert_code_target_allowed → (False, 'TCB') برای هر سه — 2026-08-15 شب"
  live_check: "run_all سوئیت 4d: ۲۶۵ تست، ۴ شکستِ pre-existing همه در همین فایل (اثبات stash: بدون تغییرات ایجنت هم همان ۴ شکست)"
  likely: "value_b علتِ محیطی دارد: REFERENCE_DIR به SYSTEM_ROOT خودِ پروژه resolve می‌شود (پوشهٔ 4D/ غایب) → _protected_roots کلِ ریشه را می‌پوشاند → همه‌چیز TCB"
  resolution: "فیکس روی دیسک کامل است (2026-08-16): (۱) _resolve_reference_dir: REFERENCE_DIR==SYSTEM_ROOT یا جدِّ آن ⇒ fallback به SYSTEM_ROOT/'4D' با diagnostic (کامیت 6fc0f4b) (۲) manifest مرزِ اعتماد: 4d_system/config/trust-boundary.json با sha256 چهارده فایل TCB + digest پاکت NO-GO (R0a) + وریفای Ed25519 با کلید عمومی مالک (۳) مسیرِ هالت روی دستکاری TCB کد شده اما **غیرفعال** — تا امضای مالک + روشن‌کردن OCTOPUS_TCB_MANIFEST_ENFORCE (فلگ در flags.cmd نیست، عمداً)، دستکاری TCB هنوز halt نمی‌دهد (سایه‌ای). همان عمقِ غایبی که نمایشِ زندهٔ V1 (ویرایش automation.py بدون halt) نشان داد"
  evidence: "سطح A: py -m pytest 4d_system/tests/test_self_code_gate.py → 16/16 (قبلاً ۴ شکست) · test_trust_boundary_c013.py 12/12 · کل سوئیت 4d سبز · AEB-20260816-000508: digests_ok=True signature=unsigned"
  governance_note: "2026-08-16 ~00:3x (پس از نقد حاکمیتی Deep-Research/Opus 5): بستنِ این ردیف با «تفویضِ» ایجنت خلاف قاعدهٔ سربرگ همین دفتر بود («هیچ تناقضی بدون رأی مالک حل نشده») — اصلاح شد: کد و شواهد ثبت‌اند، حکمِ نهایی فقط با رأی صریح مالک (امضا → enforce → تأیید همین سطر). دامنهٔ manifest فعلی = TCB مغزِ 4d؛ شناسنامهٔ پنج‌پروسهٔ زندهٔ _ops (organism manifest، DA-5) قدمِ بعد است — manifest از چیزی محافظت می‌کند که observe-only است، نه از آنچه اجرا می‌کند"
  status: resolved — owner-ratified 2026-08-16 ~00:5x (سطح A، راستی‌آزمایی مستقل این نشست: امضای Ed25519 هر دو سند Verified با کلید عمومی · OCTOPUS_TCB_MANIFEST_ENFORCE=1 در flags-loaded هر ۴ عضو (339 فلگ، بوت 00:33:50) · پروب با env ست‌شده: enforcement=True/signature=valid/digests_ok=True — از این لحظه ویرایش TCB در ارگانیسم زنده = halt واقعی. رأی مالک «همرو موافقم» ثبت: OPEN-VERDICTS + کامیت 02db1ad)
  registered_by: "test-sweep agent (grep دو-مخزن قبل از ثبت انجام شد — C-013 فقط در فهرستِ «آزاد بعدی» بود)"
```

```yaml
contradiction:
  id: C-014
  claim: "کادنسِ fetch رصدخانه (STATE §4: «هر ساعت یک fetch واقعی»)"
  value_a: "۱ fetch در ساعت (تسکِ «OCTOPUS Observatory Hourly»، تریگر 17:06، PT1H)"
  source_a: "STATE-2026-08-15-NIGHT.md §4 + Get-ScheduledTask «OCTOPUS Observatory Hourly»"
  value_b: "۲ fetch در ساعت — دو سریِ موازیِ :06 و :36 در evidence.db (زنده)"
  source_b: "کوئری mode=ro روی evidence_chain: seq 0..9 — الگوی دقیقِ :06:02-04 و :36:28-31"
  live_check: "Get-ScheduledTask: دو تسکِ فعال — «OCTOPUS Observatory Hourly» (جدید، 17:06، مسیر مطلق) و «OCTOPUS-Observatory» (قدیمی، StartBoundary 15:36:27+10:00، PT1H، «python run_observatory.py» نسبی)"
  likely: "تسکِ قدیمی هنگامِ ساختِ تسکِ جدید امشب غیرفعال نشد — دوبارْثبت"
  resolution: "containment اجرا و اثبات شد (2026-08-16، تفویض مالک): Disable-ScheduledTask «OCTOPUS-Observatory» (قدیمی) ~22:46 local؛ اثباتِ سطح A: ردیفِ 13:36Z غایب — آخرین :36 = seq14 (12:36:32Z، قبل از Disable)، جدیدترین = seq15 (13:06:05Z سری Hourly)؛ بلوکِ کامل در 06-EVIDENCE/DEBT-SWEEP-2026-08-16.md §R3. ریشه‌سازیِ ساختاری (job registry یکتا + idempotency سطحِ اثر + content-addressed evidence — طراحی GPT-5.6 Sol) = مصنوع تصمیم برای صاحبِ خط dev؛ تا آن موقع این تناقضِ زیرین باز می‌ماند"
  note: "سابقه: رکوردِ evidence#4 (17:36:31) که «مبدأ نامشخص» بود = شلیکِ سومِ تسکِ قدیمی — معما حل شد. اثرِ دورهٔ دوتایی: مصرفِ ۲برابریِ بودجه (۴۸/۱۰۰ روزانه) و رشدِ ۲برابریِ زنجیرهٔ hash"
  status: contained (علتِ سطحی رفع؛ ریشهٔ ساختاری open — design ready)
  registered_by: "test-sweep agent (grep دو-مخزن قبل از ثبت — C-014 آزاد بود)"
```

```yaml
contradiction:
  id: C-015
  claim: "وضعیت سیم‌کشی حلقهٔ حافظهٔ مغز 4d (patch → automation)"
  value_a: "patch هنوز در درخت زنده import نشده — automation.py سه نوشتن / صفر خواندن"
  source_a: "08-PLANS/COUNCIL-MESH-v0.1.md (فرانت‌متر artifacts_verified + بند هستهٔ کشف‌شده) — سند معماری پیشنهادی همان شب، پیش از جاروی تست"
  value_b: "C-012 resolved: patch به مسیر اصلی وصل شد؛ telemetry زنده read-before-decision=1.0 (18/18) و readback=1.0"
  source_b: "کامیت 8a5e98b + 01-TRUTH/CONTRADICTIONS.md C-012 + 04-SYSTEMS/MEMORY-LOOP.md + TEST-SWEEP-REPORT"
  live_check: "2026-08-15 ~22:2x — سند COUNCIL-MESH هنوز متن کهنه دارد؛ کد زنده با value_b است"
  likely: value_b
  resolution: null — سند کهنه است نه کد؛ بنر کهنگی روی COUNCIL-MESH اضافه شد؛ بازنویسی محتوا بدون رأی مالک نه (improve-don't-rewrite روی تصمیم‌های معماری)
  status: open — documentation-stale (کد حل شده؛ سند گمراه می‌کند)
  registered_by: "council-import scan 2026-08-15 دیرشب (grep: C-015 فقط به‌عنوان آزاد بعدی بود)"
```

```yaml
contradiction:
  id: C-016
  claim: "تفکیک مسیر حل تعارض: عملیاتی→NBB-CP، معماری→Architect — بدون گاردِ بازچارچوب‌بندی"
  value_a: "NBB-V1 (قفل 2026-08-15): تعارض‌های عملیاتی به NBB-CP و معماری به Architect — قاعدهٔ رسمی حاکمیت"
  source_a: "02-DECISIONS/OPEN-VERDICTS.md (NBB-V1=A) + PHASE-1-DECISIONS.md (working repo)"
  value_b: "هر بازیگری که بخواهد از رأی/وتوی NBB-CP رد شود می‌تواند همان تعارض را «معماری» بازچارچوب‌بندی کند — مرزی بین دو دسته تعریف نشده و داورِ بازچارچوب‌بندی هم مشخص نیست"
  source_b: "شورای اول (Claude Sonnet 5.0: دریچهٔ فرار معمار به‌عنوان مسیر دورزدن مشخص) + کشف مجدد Deep-Research 2026-08-16 (GPT-5.6 Sol Thinking + Claude Opus 5) در مقایسهٔ مکرر با بریفینگ شب — در بریفینگ فهرست نشده بود؛ ثبت به‌عنوان شکاف"
  live_check: "2026-08-16: هیچ پروتکل/تست/PEPی وجود ندارد که ادعای «این تعارض معماری است» را بیازماید یا به داوری مقتضی بفرستد — گارد صفر (grep: تعریف مرز دو دسته در هیچ سند حاکمیتی نیست)"
  likely: value_b — دریچهٔ بالقوه، هنوز بدون سوءاستفادهٔ مشاهده‌شده
  resolution: null — نیاز به طراحی: (۱) تعریف عملیاتیِ دو دسته با معیار ماشینی (اثر روی پول/داده/پا = عملیاتی؛ تغییر مدل/لایه/قرارداد = معماری) (۲) مسیر شکایتِ بازچارچوب‌بندی با داورِ سوم (مالک) (۳) ثبت هر ارجاع معماری-ادعاشده در دفتر با receipt — جزء DA-4 (PEP/lease) می‌شود: برگه‌ی route در قرارداد ۱۵-فیلدی عمل
  status: open — owner_action (طراحی در DA-4 ضمیمه شد)
  registered_by: "debt-sweep agent 2026-08-16 ~00:4x (grep دو-مخزن: C-016 فقط به‌عنوان آزاد بود — منبع: Deep-Research council paste 00:26)"
```

```yaml
contradiction:
  id: C-017
  claim: "DOCTOR_USE_CENTRAL_ROUTER=1 یک تصمیمِ فعال است"
  value_a: "در OCTOPUS-flags.cmd تعریف و مسلح شده (=1)"
  source_a: "grep flags.cmd — 2026-08-16 (کاتالوگ کاشف، کلاس orphan_armed)"
  value_b: "صفر reader در _ops (grep پایتون: 0) — باقیماندهٔ rename"
  source_b: "grep دو-مخزن + کاتالوگ کاشف"
  resolution: "رأی مالک (هر پنج) + اجرا 2026-08-16 ~00:5x: خط از flags.cmd حذف شد (بکاپ) — غیبت در هر دو limb تأیید شد (flags-loaded: orphan False)"
  status: resolved (2026-08-16 — verified in organism+cortex)
  registered_by: "senior-architect (grep دو-مخزن: C-017 فقط به‌عنوان آزاد بعدی بود)"
```

```yaml
contradiction:
  id: C-018
  claim: "پیش‌فرض STEP 1-1 مگاپرامپت PHASE01 v2.0: «automation.py هنوز memory_read_patch را import نمی‌کند (تأیید شد 08-15: ۳ نوشتن/۰ خواندن)»"
  value_a: "مگاپرامپت PHASE01 v2.0 (معمار ارشد GLM، 2026-08-16 ~01:2x) — دستور اتصال دوبارهٔ پچ در سه نقطه"
  value_b: "درخت زنده: automation.py پچ را در ۴ نقطه import می‌کند (خطوط 377/436/467/623، کامیت 8a5e98b)؛ telemetry پنجرهٔ پس از سیم‌کشی (بعد از event 34218): read-before-decision=1.0 (30/30) و readback=1.0"
  source_b: "grep زنده + mrp.telemetry_metrics(after_id=34217) — همین نشست (PHASE01) 2026-08-16 ~0x:xx"
  live_check: "نکتهٔ حیاتی: automation.py اکنون فایل TCB است (manifest امضاشده) — اجرای STEP 1-1 هم غلط بود (کارِ انجام‌شده) هم ممنوع (بدون امضای مجدد)"
  likely: value_b — همان کلاسِ C-015 (حافظهٔ کهنهٔ ایجنت-معمار نسبت به کد زنده)
  resolution: "null — مستندسازی صرف؛ اجرا نشد (درست). پذیرش C-012 با پنجرهٔ درست اثبات شد. نکتهٔ all-time=0.769 (30/39) مربوط به ۹ رویدادِ پیش از سیم‌کشی است — متریک باید همیشه windowed گزارش شود (after_id از اولین memory.read پس از 8a5e98b)"
  resolution: "resolved (2026-08-16 ~05:5x): بنر ERRATA-C-018 روی خود مگاپرامپت PHASE01 نصب شد (سه پیش‌فرض کهنه: STEP1-1/4-2/4-4 — هیچ‌کدام اجرا نشدند) + قانون «فکت‌چک پیش‌فرض هر STEP» در مگاپرامپت PHASE02 v1.0 قفل شد. کد زنده هرگز لمس نشد"
  status: resolved (errata نصب شد؛ نسخهٔ بعدی مگاپرامپت‌ها از این قانون شروع می‌کنند)
  registered_by: "PHASE01 agent 2026-08-16 (grep دو-مخزن: C-018 فقط به‌عنوان آزاد بعدی در خود مگاپرامپت بود)"
```

```yaml
contradiction:
  id: C-021
  claim: "بازیابیِ دور (recall_reach) در مسیر latent زنده است"
  value_a: "similar() + LATENT_PERSIST + RECALL_TREND مسلح‌اند؛ events=58 یعنی بازیابی شلیک می‌کند"
  source_a: "ORGANISM-STATE.recall_reach · wiring._enrich_with_latent · flags LATENT_PERSIST=1 / RECALL_TREND=1"
  value_b: "از سیکل ۵۹۸ similar_keys تهی است؛ encode_rfc بایت SHA را float32 می‌کند → NaN؛ integrate نامتناهی → similar()=[] ؛ مصرف‌کنندهٔ تصمیم صفر"
  source_b: "پروب زنده 2026-08-16: ۳۱ ردیف latent_no_sk همه doctor+school؛ cosine(archive-618,archive-630)=NaN؛ grep similar_keys فقط metric/تست"
  live_check: "قبل: events=58 keys=267 median=2.0 coverage=0.0928 · بعد از فیکس+گرم: 90 / 987 / 21.0 / 0.144 — فرمان در 06-EVIDENCE/RECALL-LOOP-2026-08-16.md"
  likely: value_b
  resolution: "resolved (2026-08-16 ~11:5x): _hash_project→int16 متناهی · rfc_id بدون سیکل · select_recall_keys دور+نزدیک · similar NaN-safe · گرم UNION بدون حذف · تزریق cite به owner_recall/gather_signals · تسک ویندوزی 4d"
  status: resolved (کد+عدد قبل/بعد)
  registered_by: "recall-loop agent 2026-08-16 (grep دو-مخزن در لحظهٔ شروع C-019 آزاد بود؛ موازی unwired همان id را گرفت → این رکورد C-021 شد)"
```

```yaml
contradiction:
  id: C-019
  claim: "4d ConsolidationCycle به‌صورت دوره‌ای توسط daemon صدا زده می‌شود"
  value_a: "docstring brain/consolidation.py: «Wiring: called periodically by the daemon alongside housekeeping (DAEMON_CONSOLIDATION_EVERY)»"
  source_a: "4d_system/brain/consolidation.py (تا قبل از ERRATA 2026-08-16) + دیپ‌تست «R18 زنده»"
  value_b: "صفر فراخوان تولیدی: rg ConsolidationCycle در 4d_system → فقط خود فایل + tests/test_consolidation_delta_r18.py؛ daemon.py و automation.py هیچ importی ندارند"
  source_b: "grep سطح A 2026-08-16 ~11:3x · outputs/self_evolved/consolidation.json = ۳ ردیف دستی (سیکل ۲–۳ دیپ‌تست 10:35) · در آن لحظه هیچ تسک ویندوزی نبود"
  live_check: "2026-08-16 ~11:5x recall-loop: تسک «OCTOPUS 4d Consolidation Tick» ساخته شد + تیک دستی events 0→1 — daemon همچنان صدا نمی‌زند (TCB)"
  likely: value_b — کلاس NEVER-WIRED در daemon؛ زمان‌بند ویندوزی حالا هست
  resolution: "containment (2026-08-16 recall-loop): تسک ۶ساعته غیر-TCB + جاکارد insight. قلاب daemon = کارت ۲ (TCB + امضا)"
  status: contained (تسک ویندوزی زنده؛ daemon همچنان بی‌قلاب — owner_action)
  registered_by: "unwired-discovery agent 2026-08-16 (grep دو-مخزن: C-019 فقط به‌عنوان آزاد بعدی بود؛ working repo خالی)"
```

```yaml
contradiction:
  id: C-020
  claim: "4d_system لانچ نمی‌شود و به ارگانیسم زنده وصل نیست"
  value_a: "DEPRECATED.md 2026-07-18: «کد کامل است ولی لانچ نمی‌شود» · MANIFEST.yaml: «not currently running»"
  source_a: "4d_system/DEPRECATED.md · 4d_system/MANIFEST.yaml:25"
  value_b: "دیمون زنده: python -m brain.daemon · pid 27164 · resumed 10:34:38 · last_tick 11:30:27 · tick_this_run 86 · generation 9"
  source_b: "Get-CimInstance Win32_Process + outputs/daemon_state.json 2026-08-16 ~11:3x"
  live_check: "import از _ops به 4d_system همچنان صفر است (نیمهٔ DEPRECATED درست)؛ لانچ‌نشدن نادرست است"
  likely: value_b برای لانچ · value_a برای «عضو اعلان‌نشدهٔ ارگانیسم _ops» (پروسه جداست)
  resolution: "بنر ERRATA-C-020 روی DEPRECATED.md نصب شد (2026-08-16). بازنویسی کل سند بدون رأی نه"
  status: open — documentation-stale (مثل C-015)
  registered_by: "unwired-discovery agent 2026-08-16 (grep دو-مخزن: C-020 خالی بود)"
```

```yaml
contradiction:
  id: C-022
  claim: "circuit orchestr در circuit-state.json سالم/closed است"
  value_a: "targets.orchestr.state = closed · fail_count = 0"
  source_a: "_ops/state/circuit-state.json (خوانده‌شده 2026-08-16 ~11:2x)"
  value_b: "opened_at_ts پر است · last_ok_ts=2026-08-12T07:52:59 · recent_outcomes بیست false · ۴۹× circuit OPEN 429 در دفتر ۷روز"
  source_b: "همان فایل + governor-alerts.md (اولین OPEN پنجره 2026-08-09T00:15:55، آخرین 2026-08-15T13:25:40) · record_success واقعی opened_at را None می‌کند (circuit_breaker.py:183)"
  live_check: "مغز زنده روی reason/DeepSeek است (last_ok امروز 11:20:49، recent_outcomes همه true). orchestr مسیر اصلی نیست ولی اسنپ‌شات هنوز «سالم» دروغ می‌گفت. _target_entry از قبل به half_open تنزل می‌داد فقط در حافظه؛ status() خام فایل را برمی‌گرداند."
  likely: value_b — شکل ریست/نوشتهٔ بیرونی، نه closeِ اثبات‌شده
  resolution: "contained (ERRORHUNT 2026-08-16): persist تنزل روی دیسک + status() از _target_entry. تست test_circuit_demote_persist_errorhunt.py ۴/۴. فایل زنده این نشست نوشته نشد تا اولین check/status بعدی. خاموش‌کردن پروب = کارت ۱ (رأی)."
  status: contained (کد صادق شد؛ دیسک تا تماس بعدی ممکن است کهنه بماند)
  registered_by: "errorhunt agent 2026-08-16 (فکت‌چک: مگاپرامپت C-019 آزاد می‌گفت؛ دفتر زنده C-019..C-021 پر بود — آزاد C-022؛ working repo خالی از C-022)"
```

```yaml
contradiction:
  id: C-023
  claim: "پوش به germline فقط پس از یک کلمهٔ مالک انجام می‌شود"
  value_a: "قرارداد مگاپرامپت UPDATE-DEBUG-SWEEP و چند مگاپرامپت هم‌روز: Local commits only · End with N commits ahead · Owner speaks the word"
  source_a: "agent-prompts MEGAPROMPT Full Update & Debug Sweep 2026-08-16 · همین قاعده در PHASE02/discovery"
  value_b: "56899b7 (2026-08-16 10:36 +1000, deep-test 1h) و پس از آن c1c2caa و bfc673f روی germline هستند؛ git rev-list germline/master..HEAD = 0 در لحظهٔ پروب"
  source_b: "git log -1 56899b7 / merge-base --is-ancestor 56899b7 germline/master [A]"
  live_check: "ثبت برای صداقت دفتر است نه سرزنش. این نشست پوش نکرد."
  likely: value_b
  resolution: null
  status: open — owner_vote (closer = owner-vote, not agent)
  registered_by: "update-debug-sweep 2026-08-16 ~12:0x (grep: C-023 در 01-TRUTH خالی بود؛ C-019..C-022 را ایجنت‌های موازی گرفته بودند)"
```

```yaml
contradiction:
  id: C-024
  claim: "SELF_CODE_ENABLED در درخت زنده خاموش است (NO-GO / test_no_go_envelope)"
  value_a: "flags.cmd هیچ خط SELF_CODE_ENABLED ندارد؛ test_no_go_envelope می‌خواهد مقدار در (1,true,yes) نباشد"
  source_a: "_ops/OCTOPUS-flags.cmd [A grep] · _ops/tests/test_no_go_envelope.py"
  value_b: "دیمون زنده pid 27164: os.environ SELF_CODE_ENABLED=1؛ git_watcher.enabled در daemon_state=true (فلگ جدا، پیش‌فرض 1)؛ proposals_this_run=0"
  source_b: "psutil.Process(27164).environ() + daemon_state.json 2026-08-16 ~11:25 [A]"
  live_check: "STOP-CODE-AUTONOMY فایل _ops را می‌بندد نه brain.daemon. این نشست فلگ را خاموش نکرد."
  root_cause: "منبع مقدار = `4d_system/.env:32` (SELF_CODE_ENABLED — load_dotenv در هر پروسهٔ 4d آن را به env تزریق می‌کند؛ flags.cmd بی‌ربط است به مغز). یعنی C-024 همان کلاسِ درس دیپ‌تست است: دو منبع پیکربندی واگرا (flags.cmd برای _ops · .env برای 4d) — علاج ساختاری: یا حذف کلید از .env با رأی مالک، یا پل زدن NO-GO-envelope به env پروسهٔ 4d. [A: grep .env + C-024 خودنگاری ~12:0x]"
  likely: value_b for the 4d process; value_a for flags.cmd
  resolution: null
  status: open — owner_vote (do not flip in this session)
  registered_by: "update-debug-sweep 2026-08-16 ~12:0x (کلاس لانچر gen-3: env شل ≠ flags.cmd)"
```

## Owner-review flags (this sweep — status not mutated)

- **C-018** `status: resolved (errata)` by PHASE01 agent — closer was agent-errata, not owner vote. Flag for owner.
- **C-021** `status: resolved` by recall-loop agent — closer was agent. Flag for owner.
- **C-013** already marked owner-ratified.
- `"delegated-owner"` was not used.
```yaml
contradiction:
  id: C-025
  claim: "کلید خانوادهٔ R16 در پایتون و SQL یکسان محاسبه می‌شود (migration_dry_run و classify_for_insert یک نگاه دارند)"
  value_a: "family_key پایتونی (re.sub(r"\s+"," ")) برای ردیفِ آزمون: خانواده در صف نیست ⇒ prefilter «وارد شو» می‌دهد"
  source_a: "memory/hypothesis_policy.py:26-29 (migration/گزارش‌ها از همین کلید می‌گویند)"
  value_b: "classify_for_insert با SQLِ خودش (فقط replace \n/\t + lower) همان ردیف را dedup می‌کند به head موجود (شاهد: head=342 در سندباکس S1-G2)"
  source_b: "memory/hypothesis_policy.py:74-79 + بازتولید زندهٔ تست سخت S1 (2026-08-16 ~12:1x) — دو اجرای اول G2 دقیقاً همین دو داور را جدا دیدند"
  live_check: "اثر عملی: آمارِ خانوادهٔ گزارش‌ها (dry-run) با رفتار واقعیِ صف می‌تواند عددهای متفاوت بدهد؛ و دوقلوهای متنیِ با فاصلهٔ چندگانه از dedupِ خانواده فرار می‌کنند"
  likely: value_b رفتارِ نهاییِ ورود است (SQL داورِ واقعی)؛ value_a داورِ گزارش/مهاجرت است — دو نرمال‌سازِ هم‌نامِ ناهم‌ارز
  resolution: null — پیشنهاد: یکی‌سازی نرمال‌سازی (فشرده‌سازی \s+ در SQL با REPLACEهای زنجیره‌ای یا محاسبهٔ کلید در پایتون و پرس‌وجو با همان رشته) + تستِ دوقلوی فاصله؛ نیازمند رأی چون automation.py/مهاجرت TCB-مجاورند
  status: open — owner_vote
  registered_by: "hard-test agent 2026-08-16 ~12:5x (grep دو-مخزن پیش از ثبت: C-025 فقط به‌عنوان «آزاد بعدی» در پین‌ها بود؛ C-019..C-024 مصرفِ ایجنت‌های موازی)"
```

```yaml
contradiction:
  id: C-026
  claim: "SELF_CODE_ENABLED=0 یعنی هیچ تغییرِ خودکدی نمی‌تواند اعمال شود"
  value_a: "مستندِ ماژول self_code.py: خودمختاریِ کامل «پشتِ گاردِ brain/guardrails عبور می‌کند» + فلگ enabled() نگهبانِ اصلی است"
  value_b: "approve()/reject() (self_code.py:388-479) هرگز enabled() را چک نمی‌کنند — فقط propose_code_change/auto_propose_once (200-201, 529-530) چک می‌کنند. پیشنهادِ ساخته‌شده حین ON، بعد از OFF شدنِ فلگ هم approve/apply-پذیر می‌ماند. STOP-CODE-AUTONOMY صفر ارجاع در 4d_system دارد (grep)."
  source_b: "خواندنِ مستقیمِ کد 2026-08-16 (سشنِ کراس‌چکِ hard-test) — static read با line citation، بدون اجرای approve واقعی روی پیشنهادِ زنده"
  live_check: "2026-08-16 ~16:3x: approve()/reject() هر دو enabled() را در ورودی چک می‌کنند (SELF_CODE خاموش است (C-026)). تست test_seam_selfcode_gate_20260816 3/3 مثبت. STOP-CODE-AUTONOMY همچنان صفر ارجاع در 4d_system."
  likely: value_b (قبل از فیکس)
  resolution: "resolved-in-code + owner-ratified 2026-08-16 OWNER-EASE دروازه ۲ — گیت در approve/reject (SELFRUN F2a). manifest ۱۴/۱۴ digest_ok · signature=valid. regen تازه لازم نبود."
  status: resolved-in-code — owner-ratified 2026-08-16 ~16:3x
  registered_by: "hardtest-crosscheck agent 2026-08-16 ~13:1x (grep دو-مخزن پیش از ثبت: C-026 آزاد بود)"
  cross_ref: "هم‌خانوادهٔ C-024 (فلگِ زنده در env دیمون) ولی مکانیزمِ متفاوت — C-024 دربارهٔ روشن‌بودنِ فلگ است، این دربارهٔ بی‌اثریِ خاموش‌کردنش روی صفِ pending. جزئیات: [[../06-EVIDENCE/CAPABILITY-HARDTEST-CROSSCHECK-2026-08-16|HARDTEST-CROSSCHECK]]"
```

```yaml
contradiction:
  id: C-027
  claim: "deadline_cycles در کاتالوگِ خودهدف، پس از N شکست کاندیدای گیرکرده را کنار می‌گذارد"
  value_a: "goal_generator._CANDIDATES برای هر هدف deadline_cycles=2 می‌نویسد؛ validate آن را اجباری می‌کند؛ منشور می‌گوید KPI باید حرکت کند وگرنه تکمیل نیست"
  source_a: "_ops/cortex/goal_generator.py (فیلد + validate) · SELF-GOAL-CHARTER-2026-07-30 §۰ سؤال ۴"
  value_b: "تا 2026-08-16 propose() فیلد را هرگز برای skip نمی‌خواند — ۲۴/۲۴ cycle_verdict FAIL no-movement روی goal_key واحد f7ceb1b7dd0e (money-claimed)؛ attribution.claimed=0 در حالی که recall-events=90 روی دیسک بود و هرگز نوبت نگرفت"
  source_b: "_ops/state/test_cycle/verdicts.jsonl (۲۴ ردیف) · fitness-latest.json claimed=0 · neural/recall-trend آخرین events=90"
  live_check: "پس از فیکس additive: propose() روی درخت زنده → candidate_key=recall-events baseline=90 · skipped money-claimed deadline-exhausted fail_streak=24. تست: test_goal_generator 12/12 (کنترل منفی: یک FAIL هنوز money است)"
  likely: value_b (قبل از فیکس) — بعد از فیکس رفتار با value_a یکی شد
  resolution: "resolved-in-code 2026-08-16 — propose() حالا streak>=deadline را skip می‌کند؛ اگر همه exhausted باشند fallback با مهر deadline-fallback. رأی مالک اگر بخواهد money تا ابد قفل بماند (VOTE 3 Deep-Seams Ledger)"
  status: resolved-in-code — owner may revert via VOTE 3
  registered_by: "deep-seams agent 2026-08-16 ~13:2x (grep دو-مخزن: C-027 آزاد بود)"
  cross_ref: "[[../06-EVIDENCE/DEEP-SEAMS-2026-08-16|DEEP-SEAMS]]"
```

```yaml
contradiction:
  id: C-028
  claim: "ledger ژنوم tamper-evident است — هر ویرایشِ خاموشِ تاریخ زنجیره را می‌شکند"
  value_a: "ledger.py docstring: هر رکورد hashِ قبلی را دارد پس silent edit تاریخ را می‌شکند؛ organism روزانه verify() می‌کند"
  source_a: "07 - Knowledge/genome-system/ledger/ledger.py:1-7 · organism.py بلوک روزانه"
  value_b: "حذفِ آخرین ردیف از کپیِ زنده (۱۱٬۳۹۸→۱۱٬۳۹۷) → verify() همچنان True ok — همان کلاس epistemics E3-tail (صلیب‌چک HARDTEST). APPLY/GENOME_CHANGE در ۱۱٬۳۹۸ ردیف صفر است؛ ۸۶٪ SCHEDULER_DISPATCH"
  source_b: "بازتولید 2026-08-16 روی کپی tempfile از ledger.jsonl زنده"
  live_check: "verify() عمداً LAW-دست‌نخورده ماند. verify_tip() + sidecar .tip.json روی append؛ seal_tip اگر unsealed. تست test_ledger_tip_commit 4/4 (کنترل منفی: verify بعد از دم‌حذف هنوز ok)"
  likely: value_b برای verify()؛ tip-commit درز را می‌بندد بدون تغییر LAW
  resolution: "contained 2026-08-16 — روش جدید additive؛ سوئیچِ ledger_ok روزانه = verify∧tip نیازمند VOTE 4"
  status: contained — owner_vote برای ارتقای daily ledger_ok
  registered_by: "deep-seams agent 2026-08-16 ~13:2x (grep دو-مخزن: C-028 در CONTRADICTIONS نبود)"
  cross_ref: "[[../06-EVIDENCE/DEEP-SEAMS-2026-08-16|DEEP-SEAMS]] · HARDTEST-CROSSCHECK §S4 E3-tail"
```

```yaml
contradiction:
  id: C-029
  claim: "لنگرهای ریاضی SOG بازتولید می‌شوند و DARE برای پارامترهای مدل تعریف شده است"
  value_a: "guardrails.check_invariants → run_self_test؛ worst rel_err لنگرهای canonical = 8.8e-6؛ I_pred با settings 1.7e-6 می‌خواند"
  source_a: "4d_system/core/model.py::run_self_test · 4d_system/config/settings.py::ANCHORS"
  value_b: "P_closed(ρ=±1, λ=0) و solve() با |ρ|=1 → ZeroDivisionError؛ همان کلاس مخرج‌صفر C-021. نسخهٔ موازی _ops/heart/sog_math بعد از 2026-08-16 گارد دارد (nan)؛ TCB core ندارد"
  source_b: "پروب 2026-08-16 · test_sog_floor_guards t_tcb_core_still_raises"
  live_check: "2026-08-16 ~16:3x: P_closed(±1, λ=0) → 2.5e9 finite (کف 1e-12) نه ZeroDivision. sog_math همان ورودی را nan می‌دهد (گارد متفاوت، هر دو بی‌ترکیدگی). test_sog_floor_guards 5/5. SETTINGS_ANCHORS همچنان import مرده (VOTE B باز)."
  likely: هر دو — لنگرهای canonical سالم‌اند؛ لبهٔ |ρ|≥۱ در TCB با کف مهار شد نه با nan
  resolution: "resolved-in-code + owner-ratified 2026-08-16 OWNER-EASE دروازه ۳ — گارد کف در core.model (SELFRUN F2b). امضای manifest موجود valid بود؛ bytes عوض نشد پس re-sign نو لازم نبود. core/model.py dir-TCB است نه files-map → C-033."
  status: resolved-in-code — owner-ratified 2026-08-16 ~16:3x
  registered_by: "continuous-improve agent 2026-08-16 ~14:2x (grep: C-029 فقط به‌عنوان آزاد بعدی بود)"
  cross_ref: "[[../06-EVIDENCE/IMPROVE-ACF-2026-08-16|IMPROVE-ACF]]"
```

```yaml
contradiction:
  id: C-030
  claim: "money_gate fail-closed است — مبلغ نامعتبر هرگز allow نمی‌شود"
  value_a: "docstring: fail-closed؛ بالای آستانه بدون تأیید = deny؛ capability_gate.require هر دو گیت را AND می‌کند"
  source_a: "_ops/budget/money_gate.py · _ops/tests/test_money_gate.py (قبل از 2026-08-16 فقط ۱۵ و ۵۰ AUD)"
  value_b: "check(-1.0) و check(-0.01) → allow under-human-gate. NaN/Inf deny تصادفی با دلیل دروغین over-gate(AU$nan>20)"
  source_b: "پروب 2026-08-16 پیش از فیکس"
  live_check: "پس از فیکس: منفی/NaN/Inf → deny amount-not-a-spend؛ ۱۵ و ۰ همچنان allow. تست test_money_gate 9/9"
  likely: value_b قبل از فیکس
  resolution: "resolved-in-code 2026-08-16 — گارد finite و amt<0 در ابتدای check()"
  status: resolved-in-code
  registered_by: "continuous-improve agent 2026-08-16 ~14:2x (grep: C-030 آزاد بود)"
  cross_ref: "[[../06-EVIDENCE/IMPROVE-ACF-2026-08-16|IMPROVE-ACF]]"
```

```yaml
contradiction:
  id: C-031
  claim: "به‌روزرسانی باور epistemics نمی‌تواند از کپی‌های هم‌خانواده قطعیت بسازد"
  value_a: "policy.yaml فیلد independence دارد؛ HARDTEST گفت تلهٔ استقلال metadata است نه گارد مسیر آپدیت"
  source_a: "00 - Inbox/_scratch-hardtest/s4/run_s4.py · CAPABILITY-HARDTEST-2026-08-16 S4 E2"
  value_b: "۵ بار update_bayesian متوالی روی prior=0.1 با BF=9 → posterior≈0.9998؛ هیچ family_key روی مسیر آپدیت نبود"
  source_b: "HARDTEST 2026-08-16 · CROSSCHECK تأیید نسبت log-odds×2 برای دو کپی"
  live_check: "apply_once_per_family additive: ۵ کپی یک family = تک‌شاهد (نه 0.9998). update_bayesian خام عمداً primitive ماند. epistemics may_execute=False. تست: test_epistemic_bayes 17/17"
  likely: value_b برای مسیر خام؛ contained برای مسیر family
  resolution: "contained-in-code 2026-08-16 — گارد family additive؛ سیم‌کشی تولیدی epistemics همچنان VOTE 3"
  status: contained — owner_vote برای اجباری‌کردن family روی همهٔ آپدیت‌ها
  registered_by: "interview-organism agent 2026-08-16 ~15:1x (grep دو-مخزن: C-031 آزاد بود)"
  cross_ref: "[[../06-EVIDENCE/INTERVIEW-ORGANISM-2026-08-16|INTERVIEW-ORGANISM]]"
```

```yaml
contradiction:
  id: C-032
  claim: "کاکپیت ابسیدین متریک validator و git-init را زنده می‌فروشد"
  value_a: "CONTROL-PANEL.html «اجرای زندهٔ validatorها» + git init: باز؛ SYSTEM-DASHBOARD «مغز زنده»؛ generated 2026-07-05؛ frontmatter 210/30"
  source_a: "01 - Dashboard/CONTROL-PANEL.html model.metrics + SYSTEM-DASHBOARD.html h1"
  value_b: "vault git repo است؛ validator 2026-08-16: 625 نوت / 224 خطا؛ ارگانیسم زنده در CURRENT-TRUTH / :8773 /api/live"
  source_b: "validate_frontmatter.py 2026-08-16 · git status F:\\backup · live/server.py :8773"
  live_check: "بنر FROZEN-COCKPIT-BANNER additive؛ عنوان متریک به اسنپ‌شات تغییر کرد؛ اعداد JSON دست‌نخورده ماندند (حذف ممنوع). OWNER-EASE: نوار LIVE-STRIP هم additive است — validator امروز را از این صفحه نخوان."
  likely: value_b
  resolution: "contained-in-ui 2026-08-16 — برچسب صادق؛ بازتولید مدل زنده = کارت (مولد cockpit)"
  status: contained — owner_vote برای بازتولید CONTROL-PANEL از اسکن امروز
  registered_by: "webpanel-reality agent 2026-08-16 ~15:4x (grep: C-032 آزاد بود)"
  cross_ref: "[[../06-EVIDENCE/WEBPANEL-AUDIT-2026-08-16|WEBPANEL-AUDIT]]"
```

```yaml
contradiction:
  id: C-033
  claim: "هر تغییر TCB (از جمله فایل‌های زیر dirs) digest امضاشده را باطل می‌کند و نیازمند regen+sign است"
  value_a: "trust-boundary.json tcb.dirs = config/core/tests؛ منشور: فیکس TCB = رأی + regen + امضا. C-029 در core/model.py است"
  source_a: "4d_system/config/trust-boundary.json · generate_trust_boundary.py · MEGAPROMPT-OWNER-EASE دروازه ۳"
  value_b: "check_trust_boundary فقط tcb.files (۱۴ فایل CODE_TCB_FILES) را هش می‌کند. core/model.py در files-map نیست. پچ DARE روی دیسک است و signature=valid ماند بدون regen"
  source_b: "brain/guardrails.py::check_trust_boundary 2026-08-16 ~16:3x · P_closed گارد کف · openssl/python verify valid"
  live_check: "2026-08-16 ~16:5x OWNER-CLOSE دروازه ۲: core/model.py در CODE_TCB_FILES و tcb.files · files_listed=15 · digest_ok · signature=valid (openssl verify)"
  likely: value_b قبل از فیکس برای تشخیص امضایی
  resolution: "resolved-in-code + owner-ratified 2026-08-16 OWNER-CLOSE — core/model.py وارد digest-map شد + regen + امضا. is_tcb() از قبل write-block بود."
  status: resolved-in-code — owner-ratified 2026-08-16 ~16:5x
  registered_by: "owner-ease agent 2026-08-16 ~16:3x (grep دو-مخزن: C-033 آزاد بود؛ NBB-CP خالی)"
  cross_ref: "[[../06-EVIDENCE/OWNER-EASE-2026-08-16|OWNER-EASE]] · C-029"
```

```yaml
contradiction:
  id: C-034
  claim: "واقعیتِ کارهای 2026-08-17 ایجنت برد Sensorium (192.168.0.182) و وجود کانال TO/FROM-LAPTOP آن"
  value_a: "گزارش ایجنت Sensorium: P0–P6 با receipt (کاهش ۹۴.۱٪ نوشتن ایندکس)، کانال exchange زنده، unitهای systemd، آرشیو /root"
  source_a: "چت مالک با ایجنت Sensorium 2026-08-17 (از دید ویندوز: سطح C — غیرقابل‌راستی‌آزمایی)"
  value_b: "رد ایجنت ویندوز: «هیچ‌کدام را نساختم/ندیدم؛ TO-LAPTOP/FROM-LAPTOP هیچ‌جا وجود ندارد؛ کانال واقعی = germline+SMB+8801 و heartbeat برد منجمد است»"
  source_b: "پیام ایجنت ویندوز 2026-08-17 + بررسی مستقلش از سیستمِ germline/board-cp (F:\\backup و E:\\germline)"
  live_check: "2026-08-17 ~12:04Z مالک شخصاً از PowerShell ویندوز: ssh به .182 → TO-LAPTOP/exchange + ledger زنجیره‌دار + هر دو unit موجود ✅ · 12:15Z هر ۶ ادعای مشخص ایجنت ویندوز دربارهٔ .182 تست شد (پورت 8801/CIFS/germline/beat=1681/b003/TCB) → هیچ‌کدام روی .182 وجود ندارند؛ آن ادعاها متعلق به گرهٔ بردِ پاها/لپ‌تاپ‌اند"
  likely: "both — هر دو در قابِ خودشان درست"
  resolution: "مالک 2026-08-17: اتصال SMB دوطرفه برقرار و topology سه‌گره‌ای تأیید شد (لپ‌تاپ مغز · برد پاها ساکت · Sensorium رصد) — شرح کامل: [[../00 - Inbox/2026-08-17 SENSORIUM-NODE-ALIGNMENT|SENSORIUM-NODE-ALIGNMENT]]"
  status: resolved (owner-verified 2026-08-17)
```
