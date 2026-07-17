---
type: handoff
updated: 2026-07-18
---

# HANDOFF — وضعیت برای جلسه بعد

> قاعده: این فایل ایندکسِ wikilink است، زیرِ ۲۰۰ خط — نه آرشیو. تاریخچهٔ کاملِ قبلی: `_Archive/Logs/HANDOFF-archive-2026-07-16.md` (۲۶۳KB، قرنطینه‌شده 2026-07-16).

## وضعِ لحظه‌ای

- **2026-07-18 — فیکسِ atomicِ rate-limiterِ مغزِ محلی:** `_ops/cortex/local_llm.py` حالا check-then-write روی `_LAST_CALL` را با `threading.Lock` ماژول‌سطح می‌بندد (POSTِ ollama بیرونِ قفل). دو لاینِ همزمان (نخِ doctor self-knowledge + لِنِ cortex/llm_learn) دیگر با هم از rate-limit رد نمی‌شوند و روی یک GPU دو `/api/generate` هم‌زمان نمی‌زنند — فقط latency/fairness، بی‌crash/spend. تستِ رگرسیونِ قطعیِ `t_b2_local_llm_rate_limit_atomic_concurrent` در test_cortex (۱۰/۱۰). کامیت `569badd` روی master (فقط ۲ فایلِ کد stage شد، نه churnِ state)؛ اثر بعدِ ری‌استارتِ ارگانیسم. آیتمِ بستهٔ `task_f5d205e3`. شناسنامه: [[../04 - Architect System/architect/PROJECT|architect]].
- **2026-07-17 — اصلاح معماریِ اختاپوس توسط fugu:** گپ G1/G3 با Proposal Router سبک بسته شد: `_ops/live_loop.py` حالا proposalهای پا را gather/rank/dedupe و به کارت advisory تلگرام تبدیل می‌کند؛ `_emit_advisory` subscriberها را واقعاً notify می‌کند؛ `_ops/organism.py` Router را روی beat صدا می‌زند و `proposal_router` را در state می‌نویسد. سند تصمیم: [[../04 - Architect System/ANALYSES/2026-07-17_ARCHITECTURE-CORRECTION-DECISIONS|Architecture Correction Decisions]]. تست‌های live-loop اضافه شد، اما اجرای Python در این محیط در دسترس نبود؛ ایجنت بعدی اجرا کند: `python -X utf8 "F:\backup\_ops\tests\test_live_loop.py"` و سپس `run_all.py`.
- **2026-07-17 (ادامه، تأیید شد):** تست‌های fugu اجرا و همه سبز (live_loop کامل + سوئیتِ کاملِ ۱۸۹/۱۸۹). **P0-G3 وصل شد:** `organism.py` هر tick خروجیِ `proposal_metrics()` را در `ORGANISM-STATE.proposal_metrics` می‌نویسد و `goal_directed._baseline_metrics` آن را می‌خواند — `measure()` حالا proposals_delivered/outcomes/positive/accept_rate/value_aud را می‌بیند و شمارشی‌ها واردِ منطقِ moved شدند (accept_rate عمداً بیرون). **P0-static:** مسیرِ تلگرامِ کارت از redactionِ مرکزیِ INV-12 می‌گذرد (تأیید)؛ بهداشتِ state: payload خام دیگر واردِ خروجیِ router/ORGANISM-STATE نمی‌شود. **MVO flywheel در تستِ e2e بسته شد** (proposal→کارت→outcome→metrics→measure، صفر approve). تست‌های نو: goal_directed t_f + live_loop [MVO]. **نکردم (عمداً):** G4 canonical intake (جراحیِ چندماژوله، جلسهٔ خودش) + dedupe persistence (لازم نشد — هر دو سرِ dedupe در حافظهٔ یک پروسه‌اند و با هم ریست می‌شوند).
- **ارگانیسم:** زنده روی 8771 (پرچم‌های نو فقط بعدِ ری‌استارتِ تمیز اثر می‌کنند — دکمهٔ ♻️ تلگرام).
- **کورتکس (8772): زنده است ✅ — ادعای «مرده از 07-10» غلط بود** (تصحیحِ probe-محور 2026-07-16 20:24: ‏cycle ۱۸۸، ‏ts تازه، ‏HTTP پاسخ می‌دهد). ولی **coherence=0.235 و ۷ عضو کهنه گزارش می‌کند و هیچ‌کس نمی‌شنود** — کهنگیِ organism/heart/producers/work_pump/governor پیامدِ همین STOPِ عمدیِ توست، ولی **school ‏۱۸۰h کهنه (SLA=72h)** و **reconcile ‏`present:false` («state غایب»)** پوسیدگیِ واقعی و پیش از STOP‌اند. هشدارِ ساختاری: مسیرِ «سیستم می‌داند» → «مالک می‌داند» شکسته است.
- **مهرِ CAPABILITY-OK: غایب (عمداً fail-closed)** — احیا: run_all سبز روی درختِ زنده در پنجرهٔ خاموشیِ ارگانیسم. پول double-closed (LIVE-ENABLED هم غایب).
- **قلبِ هیبریدی LIVE است** (ACTIVATION-GO-LIVE سپرِ تاریخ را باز کرده) — الان ۹۰۰s استراحت به‌خاطرِ ته‌کشیدنِ بودجهٔ ضربان.

## جلسهٔ 2026-07-15/16 — موتورِ لید + دیباگِ مغز + موجِ ده‌برنامه

نقشه‌ها: [[../public/octopus-patches-2026-07-15/LEAD-ENGINE-PLAN-2026-07-15|نقشهٔ موتورِ لید (۸ مرحله)]] · [[../public/octopus-patches-2026-07-15/NEXT-10-PROGRAMS-2026-07-16|۱۰ برنامهٔ بعدی]] · [[../public/octopus-patches-2026-07-15/BUGS-FIXED-2026-07-15|۳ باگِ دیباگ‌شده]]

- **موتورِ خودکارِ لید — مراحل ۱–۵ ساخته/تست/زنده-اعمال:** پورتِ LeadScorer + `lead_discovery_beat` (صندوقِ `state/legs/lead-inbox/`) + پلِ ایمیل + غنی‌سازیِ LLMِ $0 + پیش‌فاکتورِ قیمت‌خوردهٔ واقعی (`create_quote` دیگر یتیم نیست؛ probeِ LEAD-PROBE حذف). commits ‏`f1e062d`+`bc24b4d`، پچ‌های ۱۲+۱۳. ارسال = مرحلهٔ ۸، ساختاراً غایب، owner-gated.
- **۳ باگِ دیباگ‌شده:** مغزِ پولی حالا واقعاً Fugu می‌زند (کلید-آگاه + alias) · دکتر بدونِ تست دیگر «accept» نمی‌گوید (`unvalidated`) · مدرسه persist=True.
- **اقتصادِ مغز:** ‏`OLLAMA_MODEL=qwen2.5:latest` (7Bِ از-قبل-دانلودشده، دودِ زنده ✅) + نردبانِ محلی-اول `CORTEX_LOCAL_FIRST` (ردهٔ میانی اول محلی + گیتِ کیفیت؛ فقط شکست→پولی؛ کارِ بزرگ مستقیم API) — test_brain_fix ‏6/6.
- **برنامهٔ ۱ (فلگ‌ها زده شد، منتظرِ ری‌استارت):** `LEAD_DISCOVERY` + `LEAD_DRAFT` + `HEARTSTATE_SHADOW` + `STRUCTLOG` در [[../_ops/OCTOPUS-flags.cmd|OCTOPUS-flags.cmd]].
- **برنامهٔ ۲:** قالبِ `web_research` به work-plan برگشت (۵ روز گرسنگیِ بی‌صدا تمام).
- **برنامهٔ ۳:** ۳ یتیمِ سبز ثبت (ui_truth/organ_console/organ_create)؛ ۴ فانتوم مستند (mining×2/drawdown/effector) + test_durable_journal قرمزِ واقعی.
- **برنامهٔ ۶:** لوپِ کالیبراسیون تعمیر شد — بیتِ `moved` حالا persist می‌شود + claimهای id-دار؛ probe اولین جفتِ n≥1 را در تست گرفت.
- **کاوش‌های چند-ایجنتی:** کالبدشکافیِ ریاضی (۱۰۱ ساختار؛ هومئوستاتِ SOC، نه مغزِ منیفولدی) → Artifact ‏`4fea3c03` · اسکنِ ۶-جبهه‌ای (۴۳ یافته) → `scratchpad/next10_full.json`.

## موجِ ده‌برنامه + پرورش + PF — همه رسید (2026-07-16)

- برنامه‌های ۷/۸/۹ ✅ live-اعمال (commit `babc702`، پچ ۱۴) · برنامهٔ ۱۰ فقط-پچ (منتظرِ رأی DUP-01).
- **پرورشِ همه‌پا زیرِ دکترِ تکاملی** ✅ (commit `e0ef64b`، پچ ۱۵، live-اعمال، پشتِ `OCTOPUS_WIRE_LEG_CULTIVATE` خاموش).
- **مأموریتِ PF (لنگر/صبا)** ✅ ۷۰/۷۰ سبز، ۵ کامیت `c3e81cf→c3e903f` فقط worktree — **merge با تو**: کابینِ راست‌گو + capability_registry + actuator (صفر adapterِ بیرونی) + event_bus/telemetry + `OCTOPUS-ACTUATION-ALIGNMENT.md` v1.0 + پچ‌های 001-003 در پوشهٔ PF. متریک‌های ساختگی حذف؛ مغزِ یادگیرِ PF هنوز صفر مصرف‌کننده (صادقانه).
- تنظیمِ سخت‌افزاری قلب ✅ (12t/16GB/1660Ti → timeout/فاصلهٔ ollama، سقفِ لید) + متابولیسمِ $0 مستند.
- **بستهٔ ممیزی** ✅ (رأی مالک «اره»): `_agent_audit_output/` — ۸ فایل (inventory/معماری/ریسک/سوال‌ها/مگاپرامپتِ خود-ممیزی/قالبِ پاسخ/V2/نقشهٔ تست).

## ممیزیِ امنیت‌ومعماریِ ۶-محوره + پرامپتِ ایجنت بعدی (2026-07-16، کامیت `4a1c5a5`)

- **[[../_agent_audit_output/20_security_architecture_review_2026-07-16|گزارش کامل]]** — ۳۰۵ ایجنت، ۲۱ محور × ۳ عدسیِ خصمانه، ۸۴ تأیید/۱۰ رد/۲ شکافِ منتقد. **صفر Critical.** سه High **دستی-تأییدشده**: `CWE-93` (RCE: `/save` مقدارِ profile را بدونِ CRLF-strip داخلِ `OCTOPUS-flags.cmd` می‌نویسد → `RUN-ORGANISM.bat:21` آن را `call` می‌کند؛ CSRF-پذیر از مرورگر) · `OCT-AUTHZ-3` (پاک‌کردنِ `STOP-ORGANISM` بی‌احرازهویت روی ۸۷۷۳) · `OWASP-A05` (`_write_env` بی‌صدا ۲۴/۲۹ فلگ + دو گاردِ امنیتی را پاک می‌کند). هر سه ریشه = RC1 («۱۲۷.۰.۰.۱ = مالک»).
- **[[../04 - Architect System/octopus-build-prompts/NEXT-AGENT-PROMPT-2026-07-16-security|پرامپتِ ایجنت بعدی (امنیت)]]** — S1 دروازهٔ auth مشترک (~۴۰خط، می‌بندد F-1+F-2) · S2 غیرمخرب‌کردنِ `_write_env` · S3 split-brainِ ناظر (=رأیِ [WATCHDOG-NOTE]) · S4 notifierِ بیرون‌بدنی+escape+SSRF · S5 chrono/package. **همه additive+flag-off+پیشنهاد-محور**؛ اعمالِ live/فلگ/schtasks = ردهٔ مهم، رأی مالک. رویِ [[../04 - Architect System/octopus-build-prompts/NEXT-AGENT-PROMPT-2026-07-16|پرامپتِ ادراک]] سوار است، نه جایگزینش.

## حسابدارِ مولتی‌ایجنت + کارتِ /finance (2026-07-16)

- **شبکهٔ حسابداریِ واقعی ساخته شد:** PocketSmith زندهٔ read-only + CSVها → ۵۷۶ تراکنشِ یکتا، سنتِ صحیح، reconcile GREEN. کد در `_ops/legs/` (money·txn_store·attributor·accountant·pocketsmith_api·txn_categorize). گزارش + دادهٔ خام همه **gitignore** در `03 - Projects/Accounting/personal/` (نه در چت، نه در git).
- **کارتِ `/finance` تلگرام** به خلاصهٔ **PII-امنِ** شبکه وصل شد (`accountant.network_summary_card` + بخشِ ۳ در `approval_channel`) — commit `a236590`. verifyِ خصمانهٔ ۵-لنزی (۱۸ ایجنت): ۶ فیکس (k-ناشناسی، scrub مبالغِ کاما/اعشاری، fail-soft، برچسب‌های صادق).
- **حسابدارِ گفتگومحورِ `/review`** ساخته شد (commit `4e532ec`): بات دونه‌دونه از صفِ مرور می‌پرسد «مالِ کیه؟ درآمد/خرج/حقوق/عبور؟»، تو با دکمه یا متنِ آزاد جواب می‌دهی، اعمال (confirmed=یادگیری)، سوالِ بعدی. propose-only، مبلغ به هیچ LLM نمی‌رود، فقط تو. `_ops/legs/acct_review.py`. verifyِ خصمانهٔ ۵-لنزی (۲۳ ایجنت): ۶ فیکس — مهم‌ترین **[HIGH] گاردِ هویت**. تست: acct_review 10/10 · review_telegram 7/7. **فعلاً pause** (رأی: اول فازِ صفر).
- **نقدِ بیرونیِ متخصص پذیرفته شد** («برچسب‌زنی ≠ حسابداری») → **فازِ صفرِ دفترِ واقعی** (commit `c5d5604`): `ledger_core` (دوطرفهٔ متوازن، سنتِ صحیح، قفلِ فایل، fsync، reversal-نه-overwrite، قفلِ دوره، GST fail-closed) + `raw_store` (شواهدِ خامِ immutable) + `recon` (reconciliation واقعی — netِ برابر هرگز سبز نیست). verifyِ ۴۸-ایجنتی: **۴۳ یافته (۹ HIGH با probe) همه رفع/ثبت** — تست: ledger 20/20 · raw 6/6 · recon 9/9، رگرسیون‌ها سبز، همه در run_all. واقعیتِ entity (رأی مالک): **Pty Ltd به نامِ آرمین، GST-registered**؛ عباس related-party → `policy-profile.json` (gitignored) پر شد؛ `money.gst_component` (۱/۱۱ قطعی)؛ invoice هم پشتِ گیتِ profile. ریسک‌ها: [[../03 - Projects/Accounting/RISK-DECISIONS|RISK-DECISIONS]] (RD-001 تلگرام، RD-002 GST). **مانده برای مالک:** ABN/نامِ قانونی در policy-profile.json + gst_basis/فرکانسِ BAS از حسابدار.
- **فازِ ۱ — حلقهٔ کاملِ حسابداریِ تلگرام** (رأی مالک «درحدی که شروع کنم»): `/sync` (pull→شواهدِ خامِ immutable→attribute با **حفظِ تأییدها** — sync_network) → `/review` → `journal_bridge` (پیشنهادِ ثبتِ متوازن، بی‌tax_code) → `/books` (تأییدِ دوم → post_journal) → `/finance` (تراز + صفِ ثبت). دو-تأییدی، ikey=txn-id ضدِ double-post. verifyِ دومِ خصمانه (۴۴ ایجنت): ۳۳ یافته (۵ HIGH با probe) همه رفع — apply هرگز صف را باور نمی‌کند (بازاشتقاق از store)، pin با content-hash (ضدِ double-postِ مهاجرتِ id)، گاردِ حسابِ entity، صفِ قفل‌دارِ fail-closed. commit `a2436ff`. تست: bridge 7/7 · books 4/4 · accountant 9/9. **شروع: ری‌استارتِ ♻️ → `/sync` → `/review` → `/books`.** گزارشِ octopus_coreِ ایجنتِ موازی = فضای PF/Ziman (containment؛ جدا می‌ماند) — حسابداری اصولی از سطحِ `_ops` وصل شد.
- **دو-ریله + Xero (رأی مالک):** ریلِ خانوادگی (آرمین↔عباس) = PocketSmith + همان حلقهٔ تلگرام؛ ریلِ شرکت (ATO) = **Xero** (تحقیقِ ۵-ایجنتی + قاضی؛ Ignite+CustomConnection A$47/ماه؛ client_credentials بدونِ refresh-token). ساخته: `company_books.py` (آداپتور، DRAFT-only تحمیلی) + `books_xero.py` (stdlib، تستِ بی‌شبکه 6/6) + بخشِ «🏢 ریلِ شرکت» در /finance. معماری: [[../03 - Projects/Accounting/ARCHITECTURE-TWO-RAILS|TWO-RAILS]] (گام‌های C0 مالک: خرید+scopeها+کلیدها در .env). ارتیفکتِ استفاده: `d5832acc`. commits `e9cc9c8`+`da4fbc1`+`2d66d91`(RD-003: ATO فقط شرکت؛ عباس خانوادگی). verifyِ خصمانهٔ providerِ Xero = قبل از اولین اتصالِ زنده (C1).
- **write-backِ PocketSmith (رأی مالک، جلسهٔ جدا 07-16):** دسته‌بندی‌های `/review` حالا (پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_PS_WRITEBACK`) به‌صورتِ برچسبِ `oct-…` روی خودِ تراکنش در پاکت‌اسمیت هم می‌نشینند — `_ops/legs/ps_writeback.py`، فقط PUT labels، HALT-محترم، قفل/سقف/مهلت، auto-backfill، تست ۳۲چکی + verify ۵-لنزی (۲ HIGH بسته: gitignoreِ صف/لاگ + نمایشِ 403 در کارتِ /sync). **فعال‌سازیِ مالک:** کلیدِ full-access در .env → فلگ → ری‌استارت ♻️ → `/sync`. سند: [[../03 - Projects/Accounting/RISK-DECISIONS|RISK-DECISIONS §RD-004]].
- **جریانِ زنده + ضدِ فراموشی** (اسکنِ ۶-لنزیِ ۶۷-یافته‌ای + ساخت): `acct_memory` (قاعدهٔ merchant از تأییدها، کفِ ۳ نمونه، drift-سنج، بازتولیدپذیر) · نردبانِ حدسِ /review (قطعی→حافظه→LLMِ ماندگار→اولامای زنده) · `acct_beat` (فلگ‌خاموش `OCTOPUS_WIRE_ACCT_BEAT`، الگوی epoch) · needs_nudge حالا صفِ حسابداری را پیش‌فعالانه پینگ می‌کند · گاردِ pullِ ناقص + تک-fetchِ /sync + دکمه‌های تبِ مالی. commits `08b4f3c`+`be1f676`. backlog: recon-wiring، category-learning، invoice→Xero (C2).
- **منتظرِ مالک:** ۳ موردِ بازِ گزارش (یک ورودیِ برچسب‌مبهم به حسابِ آرمین · چند خروجیِ بی‌صاحب · تأییدِ مشتری‌ها) + استثناهای صف مرور (T##/W##) برای بالا بردنِ دقت. جزئیات در گزارشِ gitignore.
- شناسنامه: [[../03 - Projects/Accounting/PROJECT|Accounting PROJECT]].

## آشتیِ 4d_system — هم‌سطح‌سازیِ C→F ‏durable شد (2026-07-16، جلسهٔ جدا)

- **راستی‌آزماییِ ۵-ایجنته و کامیتِ حفاظتی `5a69f2c` (۱۱۱ فایل):** sync ایجنتِ موازی سالم بود (۷ فیکس md5=snapshot · ۲۷۵ تستِ هسته سبز · suite کامل ۴۱۸ سبز+۴۷ خطای fixture ارثیِ nbb_cp · secret صفر) ولی **کامیت‌نشده** بود — حالا برگشت‌پذیر است (`git revert` یا `F:\backup_snapshots\4d_system_20260716_154902`).
- **منبعِ حقیقتِ 4D حالا `F:\backup\4d_system`** — نقشهٔ [[../06 - Architecture Maps/TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane|TRI-PLANE]] که معکوس شده بود اصلاح شد (§۷ + خطِ قرمزِ §۵). کپیِ C دسکتاپ منسوخ.
- **B6 گامِ ۱** (رأی فوگو، گزینهٔ B — تحلیل‌گرِ فقط‌خواندنیِ SOG): سند `4d_system/docs/B6-SOG-INTEGRATION-STEP1.md` + schemaی منجمد `b6.sog.proposal.v1.json`؛ **صفر سیم‌کشی، B6 هیچ write authority ندارد.** دکترین: [[../07 - Knowledge/AUTHORITY-TREE-doctrine-v1|AUTHORITY-TREE-doctrine-v1]].
- سخت‌سازی: gitignoreِ ‏4d_system برای cassettes (فقط دموی سنتتیک whitelisted) + ‏.test-venv.
- **۳ رأیِ نو:** ‏[4D-C-ARCHIVE] ‏· [B6-BUS] (الف/ب) ‏· [NBB-INSTALL] — بخشِ «4d_system» در AGENT_QUESTIONS.

## بازتنظیمِ گیتِ خودمختاری (2026-07-16 19:30، رأی صریح مالک) ⚡

- **«گیتِ انسانی فقط برای مهم‌ها؛ بقیه تصمیم بگیر و انجام بده، سوال نپرس»** → ساخته و فعال شد: [[../06 - Architecture Maps/AUTONOMY-MATRIX-2026-07-16|AUTONOMY-MATRIX]] + ماژول `_ops/cortex/autonomy_matrix.py` + ردهٔ **self** در `auto_approve` (خودتصمیمِ ثبت‌شده در ledger، `AUTONOMY_SELF_VERDICT`) + فلگ `OCTOPUS_AUTONOMY_FREE=1` — **اثر در ری‌استارتِ ♻️ بعدی**. ردهٔ مهم (پول/secret/حذف/ارسال/کد/kill/PII/schtasks) هرگز آزاد نمی‌شود؛ تست ۶چکی + رگرسیون auto_approve ‏۷/۷ سبز.
- طبق همین رأی: OPT-ARCHIVE-NS اجرا شد (snapshot → ‏_Archive)؛ OPT-EXTRACT/CONFIG/BIND ‏approve و در بک‌لاگِ بلوکِ بعدی؛ AGENT_QUESTIONS از این پس فقط برای ردهٔ مهم.

## داوریِ گزارشِ بهینه‌سازیِ Orchestrator (2026-07-16، جلسهٔ جدا) — هیچ حذفی اجرا نشد

- ۴ از ۶ «حذفِ سریعِ» گزارش با راستی‌آزماییِ ۶-ایجنته **رد شد** — دوتایش مرگبار بود: `approval_channel.py` = باتِ زندهٔ تأیید انسانی (نه dead code)؛ `unified_bus.py` = نخاعِ default-ON. توصیهٔ «NBB-CP مغزِ canonical» = گزینهٔ Cِ ممنوعِ [[../06 - Architecture Maps/TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane|TRI-PLANE]]. داوری کامل: [[../00 - Inbox/2026-07-16 VERDICT — گزارش بهینه‌سازی Orchestrator (راستی‌آزمایی شواهدمحور)|VERDICT]].
- **کشف جانبی ⚠️:** تسکِ `OctopusLiveDataRefresh` از ۰۷-۱۲ شکسته (به batِ دسکتاپِ حذف‌شده اشاره دارد) — داشبوردها دادهٔ منجمد نشان می‌دهند ([TASK-REFRESH]). فیکسِ کامیت‌نشدهٔ watchdog/cortex-supervision با `b317c0a` محافظت شد.
- `STOP-ORGANISM` فعلی = kill-switchِ عمدیِ مالک (16:07 امروز) — هیچ ایجنتی دست نزند.
- ۶ رأیِ نو: TASK-REFRESH ‏· OPT-EXTRACT ‏· OPT-CONFIG ‏· OPT-BIND ‏· OPT-ARCHIVE-NS ‏· OPT-APP-FATE.

## منتظرِ رأی/اقدامِ مالک — [[../00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] بخشِ 2026-07-16

AXON-PHI · DUP-01-APPLY · DRAWDOWN (فانتوم: merge یا حذف) · ~~CORTEX-REVIVE~~ → **CORTEX-ONLOGON** (فقط گامِ ۲؛ کورتکس زنده است، batِ دستی منتفی) · WATCHDOG-NOTE (کامنتِ وارونه در `_ops`) · CAPABILITY-REBLESS (پنجرهٔ خاموشی) · mergeِ برنچ‌ها (احکام #17-35) · **4d_system: ‏4D-C-ARCHIVE ‏· B6-BUS ‏· NBB-INSTALL**.

## نقشه‌های فعال

[[../03 - Projects/Lead-نقاشی/PROJECT|Lead-نقاشی]] (موتورِ لید اینجاست) · [[../03 - Projects/Ziman Galerry/PROJECT|Ziman]] (کاتالوگِ ۳۵محصولی منتظرِ پل) · [[../03 - Projects/Mining/PROJECT|Mining]] (تناقضِ ۶-vs-162 نود در [[../03 - Projects/Mining/OpenQuestions|OpenQuestions]] #6/#7 باز) · [[../04 - Architect System/architect/PROJECT|architect]]

## گوچاهای ماندگارِ ops

- run_all را روی ارگانیسمِ در حالِ اجرا هرگز اجرا نکن (تصادفِ 07-15) — سلامت از `/health` + تازگیِ pulse.
- STOP-ORGANISM سرگردان = مرگِ هر بوت در چند ثانیه؛ ایجنت نه می‌سازد نه پاک می‌کند (owner-gated).
- ویرایشِ approval_channel/موارد پولی = revokeِ خودکارِ capability تا سوئیتِ سبزِ بعدی (درست، fail-closed).
- AV گاهی `.git/objects` را قفل می‌کند → retry بعد از چند ثانیه.
- مسیرِ `F:\backup\...` = درختِ زنده؛ کدِ آزمایشی فقط در worktree با `REAL_VAULT=worktree`.
