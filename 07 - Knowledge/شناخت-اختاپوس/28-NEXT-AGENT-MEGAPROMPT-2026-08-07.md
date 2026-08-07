---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, megaprompt, next-agent, memory, redesign]
created: 2026-08-07
updated: 2026-08-07
created_by: agent
sources:
  - "دنبالهٔ مستقیمِ نوتِ 27 (اسکنِ بازطراحیِ حافظه‌محور، مگاپرامپت v2)، همان جلسه، 2026-08-07"
---

# مگاپرامپتِ ایجنتِ بعدی — تکمیلِ بازطراحیِ حافظه‌محورِ اختاپوس — ۲۰۲۶-۰۸-۰۷

> این نوت خروجیِ چت است برای کپی‌پیستِ مستقیم به یک جلسهٔ جدید. مرجعِ کامل: [[27-REDESIGN-SCAN-MEMORY-ARCHITECTURE-2026-08-07|نوتِ ۲۷]] + `Desktop\OCTOPUS-REDESIGN-SCAN-2026-08-07\` (فاز-۱..۷.md + REDESIGN-PROPOSAL.md).
>
> **وضعِ ۲۰۲۶-۰۸-۰۸ — این مگاپرامپت تکمیل شد.** یک ایجنتِ موازیِ دیگر بخشِ ب را کامل
> برداشت: `fbc650b`/`41d13f6`/`701a5bc` (۳ فیکسِ کم‌ریسکِ باقی‌مانده) + `b8c59dd`
> (هر ۱۱ موردِ بخشِ الف + ۳ موردِ بازطبقه‌بندی‌شده از بخشِ ب — که کاوش ثابت کرد
> سطحِ تعاملیِ نو می‌سازند نه یک‌خطی — به `00 - Inbox/AGENT_QUESTIONS.md` append
> شد). هر چهار کامیت مستقلاً راستی‌آزمایی شد (git show + ۱۱/۱۱ route_scorer +
> ۹/۹ phantom_guards + CRLF بایت‌به‌بایت، صفر لمسِ wiring.py/center.py/legs/).
> **سؤال‌هایِ بازِ رأیِ مالک از این پس در AGENT_QUESTIONS.md است، نه اینجا.**

---

## متنِ آمادهٔ کپی‌پیست

```
تو ادامه‌دهندهٔ یک اسکنِ بازطراحیِ حافظه‌محورِ اختاپوس هستی که امروز (۲۰۲۶-۰۸-۰۷) با
یک Workflow ۸-ایجنته (۷ فاز + سنتز) انجام شد. قبل از هر کاری این‌ها را بخوان:

1. 07 - Knowledge/شناخت-اختاپوس/27-REDESIGN-SCAN-MEMORY-ARCHITECTURE-2026-08-07.md
2. Desktop\OCTOPUS-REDESIGN-SCAN-2026-08-07\REDESIGN-PROPOSAL.md (سنتزِ کامل + ۸ ستونِ حافظه)
3. فاز-N.md مربوط به دامنه‌ای که می‌خواهی کار کنی (لیستِ کامل زیر)

کارِ من امروز: ۷ فیکسِ REAL-BUG/DEAD-MEMORYِ کم‌ریسک اعمال و کامیت شد (a7daa7b،
98b8075). دو دسته کار باقی مانده — بخشِ الف (رأیِ مالک لازم دارد، تو نمی‌توانی
تصمیم بگیری، فقط می‌توانی گزینه‌ها را واضح‌تر کنی یا سؤال را در AGENT_QUESTIONS.md
ثبت کنی) و بخشِ ب (کدنویسیِ مستقیم، رأیِ مالک لازم ندارد یا از قبل روشن است).

## بخشِ الف — رأیِ مالک لازم (این‌ها را خودت اجرا نکن)

۱. FUGU_DAILY_CALL_CAP=60 در OCTOPUS-flags.cmd:376 — کامنتِ خودِ فایل می‌گوید عمداً
   «از ۳۰۰ به ۶۰ سفت شد، ترمزِ عملیاتی نه پولی». ولی ۲۰۲۶-۰۸-۰۷ >۱۰ ساعت پشتِ‌هم
   Fugu را با هزینهٔ صفر (subscription=max) بست. آیا هنوز توجیه دارد؟
۲. ask_brain.py::_context_for() — افزودنِ حافظهٔ نوبت‌به‌نوبت (recent_turns) مستقیماً
   ناقضِ مرزِ صریحِ خودِ فایل است («هیچ متنِ مالک در context تکرار نمی‌شود جز خودِ
   سؤال»). آیا این مرز هنوز مطلوب است؟
۳. debate/debate_loop.py — حلقهٔ سه‌دورهٔ Muse/Architect محلی، دقیقاً نقشِ
   Thinker/Verifierِ Fugu را بازسازی می‌کند ($۰ عمدی). نگه داشته شود یا با یک
   تک‌callِ Fugu جایگزین شود؟
۴. budget/governor.py — لایهٔ کاملِ tier-routing، armed (OCTOPUS_WIRE_GOVERNOR=1) ولی
   صفر caller در تولید (کشفِ مستقلِ دو فاز، ۳ و ۶). واقعاً وصل شود جلویِ
   model_router.ask، یا رسماً deprecated اعلام شود؟
۵. heart/budget_judge.py — plan()/emit() از هیچ beat/tick صدا زده نمی‌شود؛ خودِ کد
   اذعان می‌کند «مصرف‌کننده ندارد». یک beat واقعی در organism.py وصل شود یا رها؟
۶. control_plane/supervisor.py — armed، خوش‌طراحی، ولی هیچ launcher/scheduled-task
   ندارد؛ پروسه‌اش ۵ روز است متوقف است. launcher واقعی بسازیم یا به _Archive برود؟
۷. telegram_center/mirror_room.py — کاملاً سیم‌کشی‌شده، ولی ۱۱ روز ساکت چون الگویِ
   واقعیِ مالک دکمه‌محور است نه متن‌محور. دکمهٔ ورودیِ دائمی (مثلاً «🪞 حرف بزن»
   در منویِ اصلی) اضافه شود؟
۸. event-taxonomy-v1.md + octopus_logger.py در برابرِ events.py — دو سیستمِ لاگِ
   رویدادِ ناسازگار؛ فقط events.py زنده است. کدام canonical؟ ادغام یا بازنشستگیِ
   رسمیِ یکی؟
۹. budget/approval_queue_unified.py + approval_channel_merge.py — هر دو کاملاً
   ساخته شده‌اند، خودشان در docstring اعتراف کرده‌اند «wiring به زنجیرهٔ launch
   تلگرام قدمِ بعدی است» ولی هنوز برداشته نشده. الان بردار یا retire رسمی؟
۱۰. budget/governor_epoch.py (allocate_dry/allocate_llm/barbell_allocate) — هر
    epoch (۷۰۱ فایل تا امروز) یک محاسبهٔ کاملِ تخصیصِ بودجه با تگِ صریحِ
    «shadow — صفر enforce» تولید می‌کند. اتصالِ organ_gate به grants باز شود، یا
    فرکانسِ نوشتن/آرشیوِ خودکار کم شود تا حجم رشد نکند؟
۱۱. integrations/world_discovery_action/ — ۲۸ فایل کاملاً ساخته، ولی هیچ ورودیِ
    لایوِ wiring.py/organism.py آن را import نمی‌کند؛ INTEGRATION-MANIFEST.md ادعایِ
    اتصال دارد که در کد نیست. سیم‌کشی شود یا رسماً prototype/dry-run-only اعلام؟

## بخشِ ب — کدنویسیِ مستقیم (رأیِ مالک لازم ندارد یا ساده است)

۱. mission_kernel.py — joinِ زنجیرهٔ prereg→journal→mission→receipt→verdict→memory
   ساخته شده ولی صفر caller دارد. به یک فرمانِ تلگرامِ نو (/resume یا /fsck) یا به
   حلقهٔ improve.py وصل کن — یک سطحِ نمایشیِ کوچک، کم‌ریسک.
۲. cortex/consolidate.py::summary()/recent_semantic() — پایپ‌لاینِ اصلی زنده است،
   فقط توابعِ رو-به-داشبورد صفر caller دارند. به یک کارتِ تلگرام یا بخشِ /status
   وصل کن.
۳. vault_updater_apply.py::apply / doctor/self_knowledge.py — صفِ vault-proposals.jsonl
   (۶ رکوردِ زندهٔ GATE) صفر خواننده دارد. مثلِ goal_action_bridge.emit_mission_cards
   یک کارتِ owner بساز.
۴. capabilities.py::effects() — دفترِ capability-effects.jsonl نوشته می‌شود ولی
   خوانده نمی‌شود. یک خطِ خلاصه به capability_registry.card() یا doctor digest
   اضافه کن.
۵. budget/drawdown_guard.py (نسخهٔ _ops/budget/، نه scripts/) — صفر caller، API متفاوت
   از نسخهٔ زندهٔ «04 - Architect System/scripts/drawdown_guard.py». حذف/آرشیو کن یا
   با یک خطِ ارجاع مستند کن.
۶. telegram_center/ask_vault.py — لاگِ امروز دو شکستِ rg-error دقیقاً روی سقفِ
   ۲۰ثانیه‌ای ثبت کرده، همان روزی که کدِ فایل ادعا می‌کند فیکسِ exclude-list این را
   به ۲ ثانیه رساند. بررسی کن آیا پروسهٔ زندهٔ center.py بعد از آن پچ ری‌استارت شده؛
   اگر نه، یک ری‌استارتِ کنترل‌شدهٔ هدفمند (فقط center، نه کلِ ارگانیسم) کافی است.
۷. ✅ **انجام شد (بعد از نوشتنِ این نوت، ایجنتِ موازیِ دیگری برداشت):**
   `commit fbc650b` — گیتِ persistence هم همان تلهٔ coercion را داشت
   (`os.environ.get(FLAG)` truthy-check خام، `"0"`/`"false"` را روشن می‌خواند)،
   فیکس شد + تستِ `t_j` (پوششِ sensitive/private/critical/architecture) و `t_k`
   (persistence-gate) اضافه و mutation-tested. **باقیِ راستی‌آزماییِ آن گزارش که
   هنوز نشده:** اولین‌کلیدِ non-None برنده در ترکیب‌هایِ متناقض (مثلِ
   `{"architecture": False, "is_architecture": True}`)، tokenizer فقط ASCII
   (ورودیِ فارسی → unknown).
۸. ✅ **انجام شد (خارج از دامنهٔ اسکنِ اصلی، کشفِ ایجنتِ دیگر):**
   `commit 8522562` — `live_loop.py::effect_id` برای کارت‌هایِ تأییدِ Project-F
   از سقفِ ۶۴بایتیِ callback_data ِ تلگرام رد می‌شد (عنوانِ فارسی تا ۹۴ بایت) →
   کارت هرگز فرستاده نمی‌شد، `except` در approval_channel خاموش می‌بلعید. فیکس شد
   با `_pf_eid()` (فشرده‌سازیِ بایت-محور)، تست‌شده روی ورودی‌هایِ مخرب.

## بخشِ ج — اسکنِ ادامه (فایل‌هایی که این جلسه فقط caller-count سنجید، نه محتوای کامل)

اگر می‌خواهی عمقِ اسکن را ادامه بدهی (نه لزوماً فیکس)، این‌ها کاندیدِ طبیعیِ پاسِ
دوم‌اند — لیستِ دقیق در scope_unclear_or_skipped هر فاز:

- cortex/: business_brain.py, autonomy_matrix.py, execution_board.py, guidance_box.py,
  owner_guidance.py, registry.py, discoveries.py, self_audit.py, stress.py,
  synthesis.py, local_llm.py, improve.py, part_loops.py, context_fence.py,
  fence_adapter.py, fence_ledger.py, target_guard.py, approval_actuator.py,
  calibration_probe.py, indicator_scorecard.py
- teacher_loop.py, collab_coding.py, coherence.py, identity.py, identity_equations.py,
  context_bundle.py, live_loop.py — اصلاً باز نشدند
- epistemics/*.py, spine/*.py, intel_spine/*.py, chord/{ledger,metrics,observation,
  repair_policy,schemas,state_vector,uncertainty_gate}.py — فقط caller-count
- doctor/box/*.py (۹ فایل)، doctor/self_knowledge.py کامل، doctor/self_accuracy.py،
  chrono.py (۱۵۲۵ خط، ستونِ فقراتِ pacemaker)، c6_probes.py (۹۴۰ خط)،
  c6_producer.py، self_scan.py (۵۱۳ خط)
- unified_control/*.py، owner_console/*.py — فقط caller/import
- budget/approval_channel.py (۴۹۱۷ خط، کلاسِ TelegramApprovalChannel به‌تنهایی
  ۴۳۶۰ خط) — فقط ساختاری
- tests/ (۶۲۱ فایل) — فقط نمونه‌برداریِ mtime، نه محتوا

## نکتهٔ جانبیِ کشف‌شده (خارج از دامنهٔ این جلسه، نیازمندِ تریاژ)

test_phantom_guards.py::t_every_flag_read_has_a_declaration_site الان شکسته —
OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV (از commit da9ab3b، **نه** این جلسه) در دفترِ
UNDECLARED_FLAGS نیست. به‌نظر یک فلگِ dev-only (پسوندِ _DEV) است که شاید عمداً
نباید در OCTOPUS-flags.cmd اعلام شود — تصمیم/بررسیِ کوتاه لازم دارد.

مرزهای سخت (تکرار، از منشورِ vault): هرگز .git/_code/secret دست نزن ·
_ops/legs/** فقط‌خواندنیِ سخت · wiring.py/center.py «داغ»اند، قبل از commit دوباره
git diff · git add -A هرگز · هر فیکسِ REAL-BUG = تست+mutation-test(git-stash
trick)+CRLF-check+رگرسیون · CRLF/LF را بایت‌به‌بایت بسنج · >~۵ فایل ⇒ اول
agent-checkpoint · اگر رأیِ مالک لازم بود توقف کن، سؤال را در AGENT_QUESTIONS.md
اضافه کن، خودسرانه فیکس نکن.
```

مرتبط: [[27-REDESIGN-SCAN-MEMORY-ARCHITECTURE-2026-08-07]]
