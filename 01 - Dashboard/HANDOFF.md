---
type: handoff
updated: 2026-08-09
---

# HANDOFF — وضعیت برای جلسه بعد

> قاعده: این فایل ایندکسِ wikilink است، زیرِ ۲۰۰ خط — نه آرشیو. تاریخچهٔ کاملِ قبلی: `_Archive/Logs/HANDOFF-archive-2026-07-16.md` (۲۶۳KB، قرنطینه‌شده 2026-07-16). سرریزِ 2026-07-29 (ورودی‌های ≤ 07-24): `_Archive/Logs/HANDOFF-archive-2026-07-29.md`. سرریزِ 2026-08-01 (ورودی‌های ≤ 07-27): `_Archive/Logs/HANDOFF-archive-2026-08-01.md`. سرریزِ 2026-08-04 (ورودی‌های ≤ 08-02): `_Archive/Logs/HANDOFF-archive-2026-08-04.md`. سرریزِ 2026-08-05 (ورودی‌های ≤ 08-04): `_Archive/Logs/HANDOFF-archive-2026-08-05.md`. سرریزِ 2026-08-06 (ورودی‌های 08-05): `_Archive/Logs/HANDOFF-archive-2026-08-06.md`. سرریزِ 2026-08-07 (ورودی‌های 08-06): `_Archive/Logs/HANDOFF-archive-2026-08-07.md`. سرریزِ 2026-08-08 (ورودی‌های 08-06..08-07): `_Archive/Logs/HANDOFF-archive-2026-08-08.md`.
> 🧭 **ایجنتِ جدید؟** خلاصهٔ کاملِ کارِ 2026-08-02 + honest boundaries + قواعدی که این سشن رعایت کرد: [[00 - Inbox/SESSION-NOTES-2026-08-02|SESSION-NOTES-2026-08-02]]. درس‌های این سشن در [[../_memory/EXPERIENCE-LEDGER|ledger]] (§ 2026-08-02).

## 🔒 WORKLOCK — قفلِ کارِ موازی

<!-- WORKLOCK: بخشِ زندهٔ هماهنگی. ورودی‌های تاریخ‌دارِ پایین را دست نزن.
     lane که کارش تمام شد، ردیفِ خودش را به «آزاد» ببرد — ردیف را پاک نکند. -->

**چرا هست:** ۲۰۲۶-۰۸-۰۲ چهار deploy روی تصادمِ فایلِ مشترک سقط شد — نه باگِ منطقی، هر بار دو lane یک فایل. شاهد: `8af1924`/`b61d75c`/`5ff1119` (هر سه «union … registrations» روی `run_all.py`)، `6099de4` (`wiring.py`)، `b3fb9a5` (`orphan_scan.py`)، `f51a3dc` (`center.py`).
**و بدتر:** `.gitattributes` = `*.md merge=union` ⇒ تصادمِ markdown اصلاً conflict نمی‌دهد، **بلوکِ تکراری** می‌دهد. خطا ساکت است — بعد از merge روی `HANDOFF.md`/`PROJECT.md`ها چشمی چک کن.

**کی فعال است (2026-08-07 — سنجیده، نه از بریف):** خالی. سه ردیفِ ۰۸-۰۴
(`tg-ui-phases`/`cockpit-brain` ✅ تمام؛ `intel-spine` 🟡 سه روز بی‌به‌روزرسانی)
بازنشسته شدند — همان قاعدهٔ خودِ این بخش («lane ای که تمام شده ولی ✅ نخورده
بدتر از نبودِ جدول است»).

**همیشه رزرو:** `_ops/tests/run_all.py` (ثبتِ تست **مرکزی**؛ سه تصادم در یک روز — نامِ فایلِ تستت را **گزارش کن**، خودت ثبتش نکن) · `_ops/wiring.py` (فلگِ نو **بیرونِ** `PAPER_FULL_FLAGS` و خاموش) · `_ops/telegram_center/center.py` · `_ops/orphan_scan.py`.

**همیشه امن موازی:** سندِ نو در `06`/`07`/`00` (نه بخشِ دیگران در HANDOFF و PROJECT.mdها) · **فایلِ تستِ نو** با نامِ یکتا در `_ops/tests/` · ممیزیِ ایستا (grep، `git log`، اجرای read-only، هر دو validator).

**ثابت:** فقط داخلِ worktree بنویس — **`F:\backup` درختِ زندهٔ در حالِ اجراست** · `git add -A` هرگز · >~۵ فایل ⇒ اول `agent-checkpoint:` · «fatal: stash failed»/قفلِ `.git/objects` = قفلِ AV ⇒ **retry** نه دورزدن · lane که تمام کرد ردیفش را ✅ کند (پاک نکند).

## وضعِ لحظه‌ای

- 🛌🔧 **2026-08-09 صبح (کنترل‌پنل: تشخیصِ باگِ گزارش‌شدهٔ مالک + soak-test ۱۶۰دقیقه‌ایِ واقعی).**
  مالک از تلگرام گزارش داد کنترل‌پنل بالا نمی‌آید. **ریشه:** لپ‌تاپ ~۶ ساعت
  (۰۳:۴۸–۰۸:۴۱) خواب بود — هر ۵ پروسه + تونل cloudflared مردند (اثباتِ
  `HEARTBEAT.md`: `slept=21515.58s`). خودِ `OCTOPUS-MiniApp-Watchdog` (هر ۱۰
  دقیقه) در ۰۸:۴۸ خودش gateway+تونل را زنده کرد — کدی برای فیکس‌کردن نبود؛
  فقط قبل از تکمیلِ چرخهٔ watchdog باگ دیده شده بود. تأییدِ سلامت: ۴۷+۱۷+۱۵+۹
  تستِ کنترل‌پنل سبز (شاملِ فیکسِ حیاتیِ دیشب `91acaf6`)، کشِ دارایی‌ها
  (`?v=hash` → immutable) روی سرورِ زنده تأیید شد. یک کامنتِ کهنه در
  `miniapp_gateway.py` («Actions not wired yet» — درواقع از قبل وصل بود)
  اصلاح شد (`4e2a178`، fast-forward به master).
  **soak-test سه‌فازهٔ واقعی** (`_ops/tests/soak_gateway.py`، بعد از اینکه
  اولین تلاش با روشِ غلطِ backgrounding سه پروسهٔ هم‌زمان و اعلانِ زودهنگام
  ساخت — کشف و پاکسازی شد، درس برایِ جلسهٔ بعد: هرگز `nohup … & echo` را
  داخلِ `run_in_background` نگذار، مستقیم دستور را background کن):
  ۱۰+۳۰+۱۲۰ دقیقه، PID=6764 یک‌بار هم عوض نشد (~۳ ساعتِ پیوسته)، ۱۵٬۲۶۴ پروب،
  ۹۹.۹۷٪ موفق — تنها ۴ شکست همه `504` رویِ `/api/ask` دقیقاً سرِ سقفِ
  ۶۰ثانیه‌ای (رفتارِ درستِ timeout-wrapper، نه رگرسیون). حافظه ۲.۲→۳۳.۵MB
  (رشدِ آرام نه صعودِ بی‌سقف)، HandleCount بینِ چک‌پوینتِ ۳۰ و ۱۲۰ دقیقه
  **دقیقاً ثابت** (۱۴۴=۱۴۴، صفر نشتِ handle). سهمیهٔ رایگانِ محلیِ ask_brain
  امروز به سقفِ ۱۰۰ رسید (هزینه‌اش صفر، فردا ریست می‌شود)؛ سهمیهٔ پولی صفر
  دست‌نخورده ماند. Owner-Cockpit (پورت ۸۷۸۷/۸۷۸۸، سایدِ دیشب) در حالِ حاضر
  بالا نیست — جداست از مینی‌اپِ اصلی، اینترنتی expose نشده، تصمیمِ راه‌اندازی
  با مالک.

- 🧹✅ **2026-08-08 شبِ دیرتر (پاکسازیِ frontmatter/لینکِ لایهٔ دست‌چین — ۳۰ فایل).**
  ۳۳ خطایِ frontmatter + ۲ لینکِ شکستهٔ درون‌دامنه (همه پیش‌ازاین موجود) → هر دو
  validator حالا تمیزند به‌جز نوتِ ۳۴ (بلاکِ PII/PHI guard روی Read — نیازِ دستِ
  مالک). جزئیات: [[../04 - Architect System/architect/PROJECT|PROJECT]].

- 🕹️✅ **2026-08-08 (شب — کنترل‌پنلِ مینی‌اپ: کارایی + دو سیم‌کشیِ نو + soak-test ۱۶۰ دقیقه).**
  رأیِ صریحِ مالک در چت («سیم‌کشیاشو کامل کن... رأیِ من رو همینجا بده و برو جلو»).
  ۶ کامیت (`c08c9eb`→`dcb6d2a`): (۱) فیکسِ `t_unknown_paths_are_404` (کهنه از commit
  `1d0a6fd`)؛ (۲) کارایی — کشِ `assets_version` (mtime-محور، قبلاً هر بازکردنِ اپ
  ۴ فایل هش می‌شد) + `Cache-Control` درست برایِ دارایی‌هایِ نسخه‌دار (`?v=hash`) که
  قبلاً هم `no-store` می‌گرفتند و نسخه‌گذاری را بی‌اثر می‌کردند؛ (۳) `POST /api/ask`
  — چت‌باکسِ مینی‌اپ، نردبانِ ask_vault→ask_brain، تبِ نوِ «پرسش»؛ (۴) `POST /api/mirror`
  + چیپِ «🪞 با حافظه» — نقطهٔ ورودِ mirror_room از پنل (تصمیمِ معماری: به‌جایِ
  deep-link به یک تاپیکِ تلگرام، خودِ `mirror_room.ask()` مستقیم صدا زده می‌شود —
  صفر reimplementation). هر ۴ فیکس/فیچر mutation-tested (۳۸ تستِ نو). هر دو
  سیم‌کشیِ نو نیازِ `RESTART-PROCESS.ps1 gateway` داشتند (کدِ commit‌شده تا لود
  نشود بی‌اثر است) — با اثباتِ PID انجام شد (۲۱۳۶→۱۶۴۱۶→۱۴۳۷۶).
  **soak-test سه‌فازه (Browser pane زنده رویِ app.master-painting.com/miniapp):**
  ۱۰+۳۰+۱۲۰ دقیقه، همان PID در کلِ ۱۶۰ دقیقه، صفر کدِ HTTP غیرمنتظره در ۷۵۰+ چک،
  پاسخ ۱۰-۴۳ms، حافظه بدونِ روندِ صعودی. **رصدِ یادگیری (درخواستِ جداگانهٔ مالک،
  همراهِ soak-test):** mirror_room (سوییتِ موجود ۱۷/۱۷، شاملِ رسیدنِ تصحیح به
  نوبتِ بعد) · doctor/self_patch (`rules_store.add_rule` هنوز صفر caller —
  یافتهٔ فازِ ۳ دوباره تأیید شد؛ ولی `defect_queue_card.py`ِ تازه — کارِ یک
  ایجنتِ موازیِ دیگر — حالا رویت‌پذیریِ ۱۲ ردیفِ واقعی می‌دهد، نه یادگیریِ خودکار)
  · حافظه/consolidation کلی (`semantic_memory.jsonl` واقعاً رشد کرد +۸ در ۱۴۳
  دقیقه؛ `hebbian.json`/`events.jsonl` پیوسته زنده؛ `bcm_step`/`recall_trend`
  کاملاً صاف — بعداً در `wiring.py::_apply_bcm` تأیید شد این‌ها به چرخهٔ
  ۱۲ساعتهٔ consolidation گره‌خورده‌اند، نه تیک‌محور — صافی طبیعی است نه توقف).

- 🏗️🔐 **2026-08-08 (شب — Seed Agent v1 + Owner-Cockpit stack + StateGuard).**
  سه فازِ بزرگ در یک session: (الف) **StateGuard** — repair + harden،
  (ب) **Seed Agent v1** — context assembler + bridge، (ج) **Owner-Cockpit** — ۸ WP.
  **فازِ الف — StateGuard** (۵ commit، `c566c9a`→`35ba960`):
  ۶ فایلِ corrupt JSONL repair شد (null stripped، ۵۴۴۶۲ رکوردِ معتبر حفظ شد،
  صفر داده از دست‌رفته). ریشه: `opslib.append_jsonl` بدون fsync → با fsync harden شد.
  ۲ نویسندهٔ raw (tick_timing, reach_probe) migrate شدند. arm gate + maintenance lock.
  **فازِ ب — Seed Agent v1** (`9415b9e` + session موازی `066e3be`→`7999e6a`):
  `_ops/seed/context_assembler.py` — ۷-slot prompt assembler (RULES/MISSION/STATE/
  FACTS/EPISODES/TRACE/USER). `_ops/seed/octopus_reader.py` — bridge read-only به
  live_snapshot/retrieval_router/semantic_memory. Seed Pack v1+v1.1+v1.2 ingested.
  EvolutionGate (safe self-improvement با evaluator مستقل) + red-team harness.
  همه پشت `OCTOPUS_WIRE_SEED_ASSEMBLER` (default OFF).
  **فازِ ج — Owner-Cockpit** (`92b0bfa`→`b314a9f`، ۸ WP):
  `_ops/owner_cockpit/` — fugu_proxy (:8787) + otel_setup + db.py (hash-chained
  audit) + owner_api (:8788، HMAC initData، ۷ لایه امنیت) + miniapp (۵ تب RTL).
  قیمت‌های Fugu verify‌شده از console.sakana.ai: $5/$30/$0.50 per 1M.
  ۶۴ تست سبز. ۶/۷ چک‌لیست verify سبز (۱ pending: live call با کلید واقعی).
  ADR: fugu_quota (circuit breaker) vs provider_usage (financial ledger) reconciled.
  جزئیات: [[../07 - Knowledge/شناخت-اختاپوس/34-SEED-AGENT-OWNER-COCKPIT-2026-08-08|نوتِ ۳۴]].

- 🐙🔧 **2026-08-08 (عصر — مینی‌اپِ تلگرام دیپ‌اسکن + لایهٔ ۱ SDK بومی).**
  دو فازِ کار روی وب‌اپ: (الف) **دیپ‌اسکن + فیکسِ ۴ باگ**، (ب) **لایهٔ ۱ SDK بومیِ تلگرام**.
  **فازِ الف — ۴ باگِ بحرانی** (همه در `miniapp_state.py`):
  `get_cognitive_scan_state`/`get_agent_log_state` سه تابعِ تعریف‌نشده صدا می‌زدند
  (`_runtime()`،`_read_json()`،`_now_iso()`) → NameError → تبِ اسکن‌ها ۵۰۰ می‌داد.
  فیکس: `STATE_DIR`/`_read_json_safe()`/`time.strftime` (همان helper‌های موجود).
  باگِ چهارم: `self_accuracy` در فایلِ doctor یک **object** بود نه عدد →
  `Math.round(dict*100)` = NaN → «NaN٪» نمایش داده می‌شد. فیکس: backend `.accuracy` استخراج
  می‌کند، frontend با `typeof === "number"` محافظ می‌کند.
  **فازِ ب — لایهٔ ۱ SDK بومی** (تلگرام Bot API 7.10+، تحقیقِ اینترنت + مستنداتِ رسمی):
  `BottomButton` (MainButton) روی تب‌های tasks و notifications، `selectionChanged()` haptic
  روی هر ۳ چیپ‌گروپ، `enableClosingConfirmation` روی focusِ input. همه با feature-detection.
  **هم‌چنین:** DNS misroute پیدا و فیکس شد — `app.master-painting.com` به تونلِ Content
  Studio وصله بود (مرده)، به `octopus-miniapp` repoint شد. CNAME از طریقِ Cloudflare API
  (cert.pem decode → zoneID + apiToken). URL نهایی: `app.master-painting.com/miniapp`.
  کامیت: `e798722`. ۱۹ تست سبز. مگاپرامپتِ هماهنگ‌شده برای ایجنتِ موازی در
  `_ops/MEGAPROMPT-PARALLEL-AGENT-CONTROL-PANEL-2026-08-08.md`.

- 🔍✅ **2026-08-08 (بعدظهر — راستی‌آزماییِ مستقل: فیکس‌ها تأیید شدند، عددِ dark gates کهنه بود).**
  قاعدهٔ §۰ اعمال شد: گزارش‌های ۱۴+ کامیتِ ایجنت‌های موازی مستقل رویِ دیسک بررسی شدند،
  نه باور شده. **نتیجه:** همهٔ فیکس‌ها واقعی‌اند (snapshot کار می‌کند، اعداد با raw
  هم‌خوان، applied فیکس شده، تست‌ها سبز). **اما یک یافتهٔ مهم:** عددِ «۱۲۸ dark از ۳۲۶»
  که در نوتِ ۲۶ و PROJECT.md بود کهنه بود — واقعیتِ زنده (`dark_capabilities.scan()`):
  **۶۴ dark از ۳۴۷** (`n_partial=0`، `n_tuning=76`). سیستم در همان روز بهتر شده.
  شدتِ شکافِ #۵ از 🟠 HIGH به 🟡 MEDIUM-LOW. نوتِ ۲۶ (۳ نقطه) + PROJECT.md حاشیه‌نوت شدند.
  جزئیاتِ کامل: [[../07 - Knowledge/شناخت-اختاپوس/32-INDEPENDENT-VERIFICATION-2026-08-08|نوتِ ۳۲]].
  کامیتِ مستندسازی: `3d8a8f2`. درس: قبل از تصمیم بر اساسِ هر عددی در نوت‌ها، آن را با
  اسکنِ زنده بازبینی کن — اعداد در یک سیستمِ زنده به‌سرعت کهنه می‌شوند.

- 📊🔍 **2026-08-08 (عصر — snapshot(): جمع‌کنندهٔ واحدِ حالت ساخته شد؛ پایهٔ وب‌اپ).**
  مگاپرامپتِ سومِ سه‌گانه. اختاپوس ۷ لایه داشت ولی هیچ تابعی که کلِ حالت را در یک JSON
  برگرداند نبود — مالک نمی‌توانست وضعیت را ببیند، وب‌اپ داده نداشت.
  `_ops/control_plane/live_snapshot.py` — `snapshot()` با ۸ بخش (organism/budget/brain/
  flags/approvals/memory/health/processes)، کاملاً read-only، $0، fail-soft، cache TTL 5s.
  **یافتهٔ تشخیصی + فیکس:** تشخیصِ aliveبودنِ pid روی ویندوز با `os.kill(pid,0)` غلط بود
  (WinError 87 → همهٔ ۵ پروسه alive=False در حالی که زنده بودند) → فیکس با ctypes
  `OpenProcess`. **کشفِ معماری:** یک پکیجِ `control_plane/` از ۰۸-۰۳ وجود داشت؛ فایلِ من
  به‌عنوانِ `live_snapshot.py` درونِ همان پکیج نشست (مکملِ collector، نه جایگزین).
  `test_control_plane_live_snapshot` 10/10 سبز. جزئیاتِ کامل: [[../07 - Knowledge/شناخت-
  اختاپوس/30-CONTROL-PLANE-SNAPSHOT-2026-08-08|نوتِ ۳۰]].

- 🔌✅ **2026-08-07 (عصر — Reader Map + وصلهٔ مصرف‌کنندگان: دو DEAD-OUTPUT وصل شد).**
  نوتِ [[../07 - Knowledge/شناخت-اختاپوس/31-READER-MAP-AND-CONSUMER-WIRING-2026-08-07|۳۱]].
  مأموریت: «هر لایه باید لایهٔ زیرِ خودش را بخواند» (ARCHITECTURE-LAYERS §۰). Reader Mapِ
  ۷ producer ساخته شد — ۳ DEAD-OUTPUT (hebbian، latent-vectors، smallest_fix)، ۱ نیمه‌زندهٔ
  تکراری (consolidation **۹۵.۲٪ تکرار**). **دو وصلهٔ افزودنی:** (الف) `f234d52` consolidation
  dedup فازی (جاکاردی، آستانهٔ ۰.۷، محافظه‌کارانه — تک‌عددی تکرار شمرده نمی‌شود)؛
  (ج) `0ead7d0` smallest_fixِ دکتر → proposalِ propose-only (مهم‌ترین DEAD-OUTPUT). وصلهٔ ۲(ب)
  deep_synth **نیازی نداشت** — از قبل خود-خوان است (راستی‌آزمایی شد). **تکمیلِ نوتِ ۲۷:**
  همان‌جا smallest_fix به‌عنوان مهم‌ترین DEAD-OUTPUTِ باز معرفی شده بود؛ اینجا وصل شد.
  هر وصله: تست + mutation-test قرمز + regression سبز. فلگ‌ها دست‌نخورده؛ $0 (فقط خواندنِ محلی).

- 🗺️🔧 **2026-08-08 (عصر — Effector Registry: نقشهٔ بیماریِ actuator-poor ساخته شد).**
  `_ops/effector_registry.py` (commit این جلسه) — رجیستریِ اعلانیِ ۱۰ حسِ اختاپوس
  به اکچوئیتورهایشان. نتیجه: **۳ وصل** (bcm.learned_pressure، c6، vault_bridge)،
  **۳ display-only** (smallest_fix، self_model، latent)، **۳ dead-output** (bcm.weights،
  hebbian، consolidation)، ۱ shadow. بیماریِ «sensor-rich/actuator-poor» حالا
  قابل‌دیدن است. **کشفِ مهم:** `applied` field قبلاً توسط ایجنتِ موازی فیکس شده بود
  (۵ ردیفِ applied=true، wiring.py:1702) — مگاپرامپت از وضعیتِ قدیمی می‌آمد. مهم‌ترین
  DEAD-OUTPUT باقی‌مانده: `smallest_fix` (دقیق‌ترین خروجیِ تصمیم، فقط نمایش، نه action).
  جزئیات: [[../07 - Knowledge/شناخت-اختاپوس/37-EFFECTOR-REGISTRY-ACTUATOR-POOR-2026-08-08|37-EFFECTOR-REGISTRY]].

- 🏁✅ **2026-08-08 (شب/سحر — نوتِ ۲۸ کامل شد: ایجنتِ موازیِ سوم بخشِ ب را تمام کرد).**
  چهار کامیتِ دیگر: `fbc650b` (persistence-gate ِ route_scorer، همان تلهٔ coercion که
  در `_maybe_persist` باز مانده بود) · `41d13f6` (فیکسِ `t_every_flag_read_has_a_
  declaration_site` — ثبتِ `OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV` در دفترِ بی‌اعلان)
  · `701a5bc` (cross-reference در `drawdown_guard.py` به نسخهٔ زندهٔ scripts/) ·
  `b8c59dd` (**۱۵ رأیِ باز** append شد به `AGENT_QUESTIONS.md` — ۱۱ موردِ بخشِ الف
  + ۳ موردِ بازطبقه‌بندی‌شده از بخشِ ب که ثابت شد سطحِ تعاملیِ نو می‌سازند + ری‌استارتِ
  center.py که به مالک سپرده شد). هر چهار مستقلاً راستی‌آزمایی شد: ۱۱/۱۱
  `test_route_scorer` + ۹/۹ `test_phantom_guards` سبز، CRLF بایت‌به‌بایت (append ِ
  AGENT_QUESTIONS.md دقیقاً byte-exact — bare-LFِ موجود ۴۸ دست‌نخورده ماند)، صفر
  لمسِ wiring.py/center.py/legs/. **نوتِ ۲۸ اکنون کامل است**؛ سؤال‌هایِ باز از این
  پس در [[../00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] است.

- 🔁✅ **2026-08-07 (شب — راستی‌آزماییِ ادامهٔ کارِ ایجنتِ موازی، دو کامیتِ بیشتر).**
  `fbc650b` (ایجنتِ دیگر برداشتِ آیتمِ ب-۷ از نوتِ ۲۸: گیتِ persistence ِ
  route_scorer همان تلهٔ coercion را داشت، فیکس+۲ تستِ نو mutation-tested) +
  `8522562` (کشفِ خارج از دامنه: `live_loop.py::effect_id` برایِ کارت‌هایِ
  تأییدِ Project-F از سقفِ ۶۴بایتیِ callback_data ِ تلگرام رد می‌شد — عنوانِ
  فارسی تا ۹۴ بایت، کارت هرگز فرستاده نمی‌شد، `except` خاموش می‌بلعید).
  هر دو مستقلاً راستی‌آزمایی شد: `git show`، ۱۱/۱۱ `test_route_scorer` +
  ۱۵/۱۵ `test_live_loop` سبز، صفر تصادم با کارِ من. نوتِ ۲۸ به‌روز شد.

- 🧠✅ **2026-08-07 (شب — مگاپرامپتِ v2: اسکنِ بازطراحیِ حافظه‌محور، ۸-ایجنتیِ Workflow).**
  کامیت‌های `a7daa7b` (۵ فیکس) + `98b8075` (۲ فیکسِ دیگر از یافتهٔ ایجنتِ موازیِ همکار روی
  `route_scorer.py`) = **۷ فیکسِ REAL-BUG/DEAD-MEMORYِ کم‌ریسک**، هرکدام تست+mutation-test
  (git-stash trick)+CRLF+رگرسیون. تزِ مالک («اهرمِ واقعی حافظه، Fugu خودش ارکستراتور») **جزئاً
  تأیید شد** — جزئیاتِ کامل: [[../07 - Knowledge/شناخت-اختاپوس/27-REDESIGN-SCAN-MEMORY-ARCHITECTURE-2026-08-07|نوتِ ۲۷]].
  **دو سؤالِ باز برایِ رأیِ مالک** (عمداً فیکس نشد چون بررسیِ عمیق‌تر نشان داد تصمیمِ ثبت‌شدهٔ
  قبلی بوده، نه فراموشی): (۱) `FUGU_DAILY_CALL_CAP=60` — کامنتِ خودِ flags.cmd می‌گوید
  «ترمزِ عملیاتی نه پولی»، ولی امروز >۱۰ ساعت Fugu را با هزینهٔ صفر می‌بندد؛ (۲)
  `ask_brain._context_for()` بدونِ حافظهٔ نوبت‌به‌نوبت مانده چون افزودنِ آن ناقضِ مرزِ صریحِ
  PIIِ خودِ فایل («هیچ متنِ مالک در context تکرار نمی‌شود») بود. ۷ فایلِ فازِ اسکن +
  REDESIGN-PROPOSAL.md روی دسکتاپ (`Desktop\OCTOPUS-REDESIGN-SCAN-2026-08-07\`).

