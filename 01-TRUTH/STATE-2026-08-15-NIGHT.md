---
type: master-state
audience: external-agents
created: 2026-08-15 (night ~19:00 local)
supersedes: همهٔ اسنپ‌شات‌های قبل از شب 2026-08-15
entry_point: این فایل نقطهٔ شروع هر ایجنت خارجی است
---

# 🐙 STATE — وضعیت جامع سیستم در پایان شب 2026-08-15

> ایجنت خارجی؟ این فایل را بخوان، بعد [[../00-INDEX|00-INDEX]] (نقشهٔ کامل vault) و [[../07-HANDOFF/NEXT-AGENT-HANDOFF|NEXT-AGENT-HANDOFF]] (۶ الحاقیهٔ اجرایی). اعداد این فایل همه با فرمان/فایل منبع‌دار شده‌اند.

## ۰. دو مخزن، دو نقش — اول این را بفهم

| مخزن | نقش | هشدار |
|------|-----|-------|
| `F:\backup` | **درختِ زندهٔ ارگانیسم + vault کانونیکال** — ۵ پروسهٔ python دائم روشن | درختِ در حالِ اجراست؛ تغییر فلگ = ری‌استارت رسمی (`_ops/RESTART-ALL.ps1`)؛ هرگز دستی kill نکن |
| `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` | خطِ توسعهٔ NBB-CP + **رصدخانهٔ اینترنت** (کد/تست/دیتابیس) | شاخهٔ `claude/second-brain-governor-v02-2a6e36` |

## ۱. ارگانیسم — زنده و سالم (سطح A)

> **STALE-SYNC 2026-08-16 ~11:2x [A]:** این اسنپ‌شات شب ۱۵ هنوز «۵ عضو» می‌گوید. زنده: همان پنج عضو با پورت (organism 25912 :8771 · center 11500 :8776 · gateway 20572 :8774 · live 9836 :8773 · cortex 22796 :8772) + دو ناشناس مستند (pid 5780 `http.server:8765`؛ pid 27164 `brain.daemon`). `CURRENT-TRUTH.members_present=11` شمارِ آگاهی است نه شمارِ پروسه. beat زنده **37785** · coherence **0.972** · HEAD git **bfc673f**. نکش ناشناس‌ها. جزئیات: [[../06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16|UPDATE-DEBUG-SWEEP]].

- بوت 18:30:42 · **beat 36803+** · **coherence 0.977** (از 0.942 امشب بالا آمد) · halted=False · conflicts=[]
- ۵ عضو: organism · center · gateway · live · cortex — همه با PID تازه (ری‌استارت کنترل‌شدهٔ سوم امشب)
- منبع زنده: `OCTOPUS/CURRENT-TRUTH.md` (runtime می‌نویسد — تو فقط بخوان) · `_ops/state/ORGANISM-STATE.json`
- کلیدهای کشتن (همه سالم): فلگ `halted` در DB · فایل STOP · `_ops/observatory/data/kill.switch`

## ۲. مغز و فلگ‌ها

**مغز اصلی از ~19:24 روی DeepSeek است** (`_TIER_ROLE.primary → reason`؛ deepseek-v4-flash thinking؛ rollback یک‌خطی). فوگو کنار گذاشته شد به رأی مالک («گرونه»)؛ اثبات زنده: `ask('deep') → '4'` + لاگ paid با tier=primary. باگ مسیر: C-010 (BOM).

## ۲-ب. فلگ‌های روشن (مکانیزم: `_ops/OCTOPUS-flags.cmd` — ۱۴۸۲ خط CRLF؛ تغییر = بکاپ + ری‌استارت)

`OCTOPUS_UNIFIED_CHAT=1` · `CORTEX_HYPOTHESIS=1` · `OCTOPUS_WIRE_VAULT_RAG=1` (حافظهٔ RAG والت) · `OCTOPUS_WIRE_DOCTOR_TG=1` (relay دکتر) — همه با تأیید چتی مالک 2026-08-15. بقیهٔ WIREها عمداً خاموش. **`OBSERVATORY` فلگ ندارد چون آداپتور فاز ۳ هنوز ساخته نشده — روشن‌کردنش بی‌معناست.**

## ۳. دکتر — تک‌صدا و رأی‌گیر (معماری نهایی امشب)

- دکتر در حالت **outbox**: کارت‌ها فقط در `OCTOPUS-DOCTOR/90-_meta/state/tg-outbox.jsonl` صف می‌شوند
- **صدای واحد** = ربات center از طریق `_ops/telegram_center/doctor_link.py` (relay) — دیگر هیچ ارسال مستقیم/دوتایی نیست (توکن مستقیم از `.env` حذف شد)
- **پل رأی** (کامیت `3156316`): هوک سه‌بخشی `ok|no:<gate>:<mission_id>` در `center._handle_callback` قبل از جدول verb → `_doctor_ingest` → صندوق `tg-inbox.jsonl` (گیت مالک + ضدتکرار در کد). تست: `_ops/tests/test_doctor_vote_bridge.py` (۵/۵)
- اثبات زنده: **۷ رأی واقعی مالک** همین شب ثبت شد (رأی‌دهنده با چت مالک bool-verified)
- سابقه: باگ «نادیده» = C-009 (بسته شد) — هم‌خانوادهٔ باگ ۲۹-دکمه‌ای 2026-07-28

## ۴. رصدخانهٔ اینترنت — چشمِ ساعتی

- تسک ویندوزی **«OCTOPUS Observatory Hourly»** — هر ساعت یک fetch واقعی USGS + پیش‌بینی pre-registered (نبض امشب: ۴→۵→۶ ردیف)
- بودجه با `EvidenceStore.begin_epoch()` هر روز UTC ریست (کامیت `e3e9d36`؛ سقف USGS = 100/روز)
- زنجیره‌های hash **مستقل تأییدشده**: `scripts/verify_live_store.py` → **PASS 27/27** (فرمول‌های src در فایل)
- allowlist **v2** = ۷ دامنه با شاهد robots (USGS: robots 404→allow طبق RFC 9309 §2.3.1.3 · hacker-news: صریح `Allow: /*.json$`) — `_ops/observatory/architecture/observatory-allowlist.yaml` + کپی `F:\backup\architecture\`
- ADR-041 نوشته شد (پرش ۰۴۰→۰۴۲ بسته) · ناسازگاری‌های باز: استراتژی = persistence (0.80=0.80؛ ریشه: `run_observatory.py:120-135`)
- **قضاوت n≥60**: رصد روزانه ۱۹:۰۰×۵روز (خودکار؛ گزارش در `00 - Inbox/OBSERVATORY-WATCH-*`)

## ۵. حاکمیت — شبِ رأی و امضا

- **امضای Ed25519 مالک**: `MANIFEST.sig` + `SIG-RECEIPT.md` در `_ops/D1-AUDIT-PACKAGE-2026-08-15/` — «Signature Verified Successfully» · کلید عمومی: `_ops/owner-signing/` · خصوصی: `~/.octopus-signing/` (بیرون از repo — هرگز واردش نکن)
- **رأی ORANGE 4d**: ثبت در addendum خودِ ADR-008 — سیم‌کشی shadow→live مجاز، کارِ نشستِ بعد
- D1 ممیزی مستقل: بسته آماده، **NOT_STARTED** تا ممیز بیرونی اجرا کند · D7/production: قفل تا قضاوت n≥60
- دفتر تناقض‌ها: **C-001…C-009** در [[CONTRADICTIONS]] — همه ثبت، اکثراً بسته با شواهد

## ۶. تست‌ها (همه سطح A)

NBB-CP vault: **171** · رصدخانه: **93** · hypothesis: **23** (پس از stash رأی NEW-4) · سوئیت working: **320** · پل رأی: **5** · کل `_ops` از ریشه: INTERNALERROR (رانر رسمی=`_ops/tests/run_all.py`، ~۱۷min — باز)

## ۷. قواعد خانه برای ایجنت خارجی — نقض = توقف

1. **شواهد نه ادعا** — هر عدد با فرمان/فایل منبع‌دار شود؛ سطح‌بندی A (اجرا دیدم) / B (ایجنت دیگر) / C (فقط سند)
2. **propose-only** · حذف ممنوع · improve-don't-rewrite · fail-closed · نقض invariant = halt نه retry
3. **رازها**: `.env` فقط نام کلید، هرگز مقدار؛ کلید خصوصی امضا دست‌نخوردنی
4. فلگ‌ها فقط از `OCTOPUS-flags.cmd` + ری‌استارت رسمی + گیت پذیرش (پنجرهٔ پیشنهادی: ۳۰۰s)
5. WORKLOCK را در [[../01 - Dashboard/HANDOFF|HANDOFF]] بخوان قبل از هر کار موازی؛ تستِ نو = فایل نام‌یکتا در `_ops/tests/`
6. ماینینگ: تحلیل آزاد، **اجراهای مالی هرگز** (D-10) · brain_core: promote ممنوع تا شاهد بخلاف (missing_old=3473)

## ۸. کارِ باز (به ترتیب درسِ معلم)

> **📌 2026-08-16 ~13:2x — OPS (فرمانِ مستقیم مالک): «لپ‌تاپ هنگ کرده — از اولاما کم کار بکش»:** هر سه مدل از RAM اولاما تخلیه شد (`ollama stop`؛ رم سرویس ۶۱MB) — ریشه: `flags.cmd:195` مقدار `OLLAMA_MODEL=qwen2.5:latest` (۷بی، ۵٫۱GB، ۸۲٪ CPU) می‌داد به پروسه‌های زنده (cortex/local_llm هر generate = ۱–۲ دقیقه اشباع؛ لاگ سرور 12:42–12:47: 1m58s/1m07s/1m04s). **اصلاح پایدار:** همان خط به `qwen2.5:1.5b` با بکاپ `OCTOPUS-flags.cmd.bak-20260816-ollama-light` — **تا ری‌استارت رسمی، پروسه‌های زنده هنوز latest را می‌خواهند** (drift عمدیِ مستندشده، هم‌کلاس C-024)؛ ری‌استارت با مالک. شاهد نهایی: عضوِ فراخوان (organism.py، بوتِ تازه pid 29028) با `qwen2.5:1.5b` تماس زد — **قبل: latest 5.1GB · 82% CPU ⇒ بعد: 1.5b · 1.2GB · 100% GPU** (CPU آزاد؛ ریشهٔ هنگ برطرف). درس batch: `rem` هم‌خطی با `set` بخشی از مقدار می‌شود — کامنت به خطِ خودش رفت. بکاپ: `OCTOPUS-flags.cmd.bak-20260816-ollama-light`.

> **📌 2026-08-16 ~13:0x — CAPABILITY HARD-TEST EXECUTED (مگاپرامپت چهارم):** شش قابلیت با حمله آزموده شد — **S5 خودترمیمی = REAL (تنها بازندهٔ کامل؛ ۹۲ تسک در پنجرهٔ ۱۱ خطا بدون ری‌استارت)** · S1/S2/S3/S4 = PARTIAL (سمِ حافظه ۱۰/۱۰ منحرف کرد؛ حاکمیتی ۹/۱۳ بلاک؛ شورا 0.3 در برابر 0.0؛ تلهٔ استقلال 0.9998) · **S6 مدل پیش‌بینی ثبت‌شده = METAPHOR (۱/۱۶ زیرمجموعه؛ 0.0978 در برابر ثابت 0.0829) اما مسیر بهبود واقعی: پایداری 0.0472 در برابر اوراکل 0.0617، CV 4/5**. C-025 ثبت (دریفت نرمال‌سازی family_key). پنج کارت رأی: منشای حافظه · ماندگاری ابطال PEP (پیش‌نیاز enforce) · گارد استقلال belief · جایگزینی پیش‌بینی‌گر · پیکربندی عضو شورا. صفر حذف/فلگ/TCB/ارسال. [[../06-EVIDENCE/CAPABILITY-HARDTEST-2026-08-16|HARDTEST]] · [[../00 - Inbox/2026-08-16 DISCOVERY — Capability Hard-Test Scorecard|SCORECARD]]. آزاد بعدی: **C-026**.

> **📌 2026-08-16 ~12:0x — UPDATE-DEBUG-SWEEP (PROPOSE-ONLY):** T1–T8 بدون فلگ/پوش/TCB. دیمون مسلح enforce=True و همزمان `SELF_CODE_ENABLED=1` در env پروسه (در flags.cmd نیست). تسک R18 موازی Ready ولی هرگز اجرا نشده (267011 / `py`). آزاد بعدی پس از C-023/C-024 این نشست. [[../06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16|UPDATE-DEBUG-SWEEP]]

> **📌 2026-08-16 ~11:5x — ERRORHUNT EXECUTED:** ۷روز خطا خوشه‌بندی شد. readback پس از 05:00 = **67/67 صفر fail**. cortex ۲۴ساعت: ۰ REVIVE / ۸ STOP عمدی. فیکس: persist تنزل circuit (C-022) + `mark_nudged(high_water)`. مانیتور Poisoning Watch در 10:08 = FILE_NOT_FOUND. کارت ۵تایی. آزاد بعدی: **C-023**. [[../06-EVIDENCE/ERRORHUNT-2026-08-16|ERRORHUNT]] · [[../07-HANDOFF/ERRORHUNT-REPORT-2026-08-16|گزارش]]

> **📌 2026-08-16 ~11:5x — حلقهٔ recall EXECUTED:** ریشه = NaN از hash-as-float32 در doctor encode + انتخاب nearest (نه آستانه). M3 **58/2.0/9.28٪ → 90/21.0/14.4٪** · 4d **0→1** با تسک `OCTOPUS 4d Consolidation Tick`. C-021 resolved · C-019 contained (تسک ویندوزی). کارت‌ها: ری‌استارت ارگانیسم · daemon در برابر تسک · عمق تزریق. شواهد: [[../06-EVIDENCE/RECALL-LOOP-2026-08-16|RECALL-LOOP]] · [[../07-HANDOFF/RECALL-REPORT-2026-08-16|RECALL-REPORT]]. آزاد بعدی: **C-023** (C-022 = errorhunt).

> **📌 2026-08-16 (~00:1x): جاروی بدهی EXECUTED** (مگاپرامپت v1.1/v1.2، تفویض کامل مالک «اجازه تصمیم‌گیری داری»): R0a/R13 ✅ (manifest مرز اعتماد + هش‌چک TCB؛ **C-013 resolved** — امضای مالک + فلگ OCTOPUS_TCB_MANIFEST_ENFORCE قدمِ بعد) · R3/C-014 ✅ containment اثبات‌شده (بلوک §R3 در شواهد) · R4-R14 ✅ (۱۵ شکست بسته + **۱ باگ تولیدی واقعی**: def callback در collaborator از کامیت 55720f7) · R19 AEB ✅ · R20/R16/R18 مصنوع ✅ · R21-R27 طبق جدول · R2 push ✅. **بازِ دستِ مالک: R1 چرخش PAT (پچ آماده) · امضای trust-boundary.json + AEB.txt · روشن‌کردن enforce · R21 انتخاب ممیز · رأی سیاست صف R16 و DA-1/2/3.** جزئیات: [[../06-EVIDENCE/DEBT-SWEEP-2026-08-16|DEBT-SWEEP]] · [[../02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/|مصنوعات تصمیم]].

> **📌 مأموریت فاز صفر-یک (2026-08-16 ~01:2x):** `agent-prompts/MEGAPROMPT-PHASE01-MEMORY-COUNCILS-2026-08-16.md` v2.0 — حلقهٔ حافظه (C-012، پذیرش telemetry زنده ≥0.95/≥0.99) · کرنل شوراها سایه (Architecture+Epistemic، صفر tool) · اجرای R16 (dry-run→تراکنشی) · ریزکارها (cortex-2nd-try، پنجرهٔ 300s، manifest پکیج‌های نامرئی، FUZZY طراحی‌شده-نه-روشن، بستهٔ ممیز). آزاد بعدی C-018.
» **📌 2026-08-16 ~11:4x — DISCOVERY UNWIRED EXECUTED:** کلاس ۹ نظام‌مند شد. C-019 docstring/daemon · C-020 DEPRECATED کهنه. تسک Tick موازی **اعلام شد ولی هرگز اجرا نشده** (LastResult 267011) و `py` دارد — VOTE 1=تعویض لانچر. کاتالوگ: [[../00 - Inbox/2026-08-16 DISCOVERY — Unwired & Dead Paths Catalog]] · [[../07-HANDOFF/UNWIRED-REPORT-2026-08-16]]. آزاد: **C-025**. صفر فلگ · صفر TCB · 8765 کشته نشد.

» **📌 2026-08-16 ~10:4x — سه مگاپرامپت بعدی آمادهٔ ارسال:** کشفِ کدِ بی‌فراخوان (`MEGAPROMPT-DISCOVERY-UNWIRED`) · شکار خطا/گیرکردن (`MEGAPROMPT-DEBUG-ERRORHUNT`) · حلقهٔ recall — ضعیف‌ترین حلقه (`MEGAPROMPT-DEBUG-RECALL-LOOP`). هر سه با قانون فکت‌چک پیش‌فرض + درس‌های دیپ‌تست (فلگ‌در-فرایندها · R18 بی‌زمان‌بند). مبنای مشترک: DEEP-TEST-1H. آزاد: **C-019**.

» **📌 2026-08-16 ~06:0x — PHASE02 EXECUTED:** `06-EVIDENCE/PHASE02-2026-08-16.md` — PEP سایهٔ مرز تلگرام نصب (۸ منفی، صفر تغییر رفتار، ADR پیش‌نویس) · **هولداوت L1 زنده و یافتهٔ بزرگ: gaming (base-rate) مدل را در بری‌ری شکست داد (0.0829<0.0978) — مزیت T10 فقط در برابر کمپارتور ضعیف** · readback-metric فیکس (r16-view؛ ۱/۹ کاذب) · دیمون نسل دو (R18+فیکس لود) · C-018 بسته (errata) · C-016 route در DA-4 · manifest⇄AEB. بازِ رأی: فعال‌سازی PEP · DA-6 (B/C) · DA-1 L2/L3 · ممیز D1 · PAT. شناسهٔ آزاد: C-019.

» **📌 2026-08-16 ~04:5x — مأموریت بعدی تعریف شد:** `agent-prompts/MEGAPROMPT-PHASE02-STRUCTURAL-2026-08-16.md` **v1.0** — پل به کنترل‌های ساختاری: PEP سایه روی مرز ارسال تلگرام (DA-4-P1) · هولداوت پنهان (DA-1-L1) · تعمیم دلتا به doctor/web-research · سنجش سوم M1..M10 با روش یکدست · بستن C-018. پیش‌نیازها زنده‌اند: FUZZY/TCB در ۴ عضو، daemon + پایش ۶ساعته، readback=8 و در حال رشد. قانون تازه در سربرگ: فکت‌چک پیش‌فرضِ هر STEP (درس C-015/C-018).

» **📌 مأموریت قبلی تعریف شد:** `agent-prompts/MEGAPROMPT-MEASUREMENT-2026-08-16.md` — راستی‌آزماییِ بازتولیدپذیر baseline سنجش (M1..M10) و سپس ادامهٔ `MEGAPROMPT-DEBT-SWEEP-2026-08-16.md` **v1.2** (R v2.0 — ایجنت debt-sweep از ~00:4x فعال است). سنجش ۸ساعته: [[../06-EVIDENCE/MEASUREMENT-2026-08-16|MEASUREMENT]] · شورای دوم: [[../07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/README|README]] · مالک رأی **NO-GO دقیق‌تر** را پذیرفت. شناسهٔ آزاد تناقض: **C-017** (C-015/C-016 ثبت شدند).

۱. قضاوت n≥60 — **فقط پیش‌بینی‌های bayes-v1** (ادغام شد؛ اولین نفس: 0.99 در برابر 0.80) ۲. ~~جداسازی استراتژی~~ **✅ انجام شد 2026-08-15 ~21:00** (کامیت 18fd88a؛ تست بیزی 20/20 پس از اصلاح مسیر import؛ fallback fail-closed) ۳. آداپتور observation.v1 (فاز ۳) ۴. سیم‌کشی 4d shadow→live ۵. NBB-CP به پاها (فاز ۴-۵؛ V2/V3/V4) ۶. فرمان‌دهی برد پس از بازبینی امنیتی ۷. ممیز مستقل D1 ۸. ریزکارها (شناسهٔ آزاد بعدی: **C-013** (C-012 در 2026-08-15 ~22:0x ثبت شد: حافظهٔ write-only مغز 4d) — قبل از تخصیص، هر دو مخزن grep شود): shortfall=4 فلگ · پنجرهٔ گیت ۳۰۰s · run_all کامل · خاستگاه رکورد evidence#۴ (17:36) · سرنوشت brain_core

## ۹. جای همه‌چیز

نقشهٔ کامل: [[../00-INDEX|00-INDEX]] · حقیقت زنده: [[CURRENT-TRUTH]] · تست‌ها: [[TEST-COUNT]] · سرویس‌ها: [[SERVICE-STATUS]] · تناقض‌ها: [[CONTRADICTIONS]] · تصمیم‌ها/بازها: [[../02-DECISIONS/OPEN-VERDICTS|OPEN-VERDICTS]] · سیستم‌ها: [[../04-SYSTEMS/OCTOPUS|04-SYSTEMS/*]] · لاگ شب: [[../00 - Inbox/2026-08-15 NIGHT — Activation & Test Session (all gates)|SESSION NIGHT]] · پک رصدخانه: `07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/` (تا 17:09 دقیق است؛ پس از آن این فایل مقدم است)
