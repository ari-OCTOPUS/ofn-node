# Decision Log (continued) — SoT Unification Decisions

> این فایل ادامهٔ Decision Log در AUTHORITY-CHARTER.md است.
> هر تصمیم: ID · گزینه‌ها · انتخاب · دلیل · برگشت‌پذیر؟ · فاز

## تصمیم‌های معماری SoT (autonomous — برگشت‌پذیر)

| ID | موضوع | گزینه‌ها | انتخاب | دلیل | فاز |
|---|---|---|---|---|---|
| **D-F** | SoT رویداد | spine.db / unified_bus / events.py / ترکیب | **spine.db** | تنها storeای که از ابتدا برای SoT رویداد با HLC + replay طراحی شده؛ unified_bus substrate متابولیک است نه SoT رویداد؛ events.py dashboard log است | P1 |
| **D-G** | events.py | KEEP / MERGE / ARCHIVE | **MERGE → projection از spine** | رقیب حقیقت رویداد است؛ بعد از P4 فقط dashboard feed از spine می‌خواند، emit مستقل ممنوع | P4 |
| **D-H** | review_bus.py | KEEP / MERGE / ARCHIVE | **MERGE → projection از spine** | همان رقیب؛ handoff contract از spine ساخته می‌شود | P4 |
| **D-I** | chord/ | KEEP / MERGE / ARCHIVE | **ARCHIVE-candidate** (تصمیم نهایی P4) | تا خوانده نشود UNKNOWN؛ fail-closed → ARCHIVE-candidate | P4 |
| **D-J** | ۵ فایل ریشهٔ مرموز (2026-07-21 خالی، Fbackup، baseline/checkpoint/germline/idea_graph) | KEEP / ARCHIVE | **ARCHIVE-candidate** برای خالی/سوءتایپ؛ بقیه P4 خوانده و تصمیم | هیچ فایل بی‌صاحب در ریشهٔ مغز نمی‌ماند | P4 |
| **D-K** | سه vault_updater*.py | KEEP هر سه / MERGE apply→gate | **MERGE-candidate: apply→gate** | دو مسیر write = دوگانگی؛ اگر apply فقط wrapper است، ادغام | P4 |
| **D-L** | cardiac.py | KEEP / ARCHIVE | **KEEP** | نقش روشن (آلوستاتری قلب)، پشت فلگ، additive | — |
| **D-M** | قاعدهٔ فایل جدید | — | **هر فایل/Store/Bus جدید قبل از ساخت در SoT Charter ثبت شود** | پیشگیری از دوگانگی آینده — سادگی به‌عنوان معیار طراحی | همیشه |

## تصمیم‌های اجرای P0-DEPLOY (2026-07-23 · معمار shell‌دار)

| ID | تصمیم | انتخاب | دلیل | برگشت‌پذیر؟ |
|---|---|---|---|---|
| **D-N1** | ترتیب stop نسبت به merge | **stop ۳ پروسه + disable ۴ watchdog قبل از merge/migration** | نوشتنِ زندهٔ chrono.db حین migration = ریسک corruption؛ رانبوک restart را بعد می‌گذاشت ولی هیچ stopِ pre-merge نداشت | ✅ (restart + re-enable در پایان) |
| **D-N2** | استراتژی merge روی درختِ کثیف | **`git -c merge.autoStash=false merge --no-ff`** بعد از شکستِ autostash | autostashِ ۴۷ blobِ کثیف با file-watcher (node.exe) روی Windows مسابقه داد → Permission denied؛ merge با objectهای از پیش fetch‌شده فقط چند object می‌نویسد، بی‌stash موفق شد. صحت: merge disjoint از فایل‌های کثیف (اثبات‌شده) | ✅ (`revert -m 1 869a186`) |
| **D-N3** | migration اجرا | **controlled subprocess روی chrono.db زنده، بعد از dry-run روی کپی** | fail-closed + transactional؛ dry-run روی دادهٔ واقعی PASS قبل از دست‌زدن به live؛ pre-v4 anchor نگه‌داشته شد | ✅ (restore chrono.db.pre-v4) |
| **D-N4** | ۶ فلگ external-effect بعد از deploy | **DISARMED نگه داشته شد؛ re-arm نشد** | rule #14 «external effect روشن نشود» + Owner Packet §8 «مالک با برنامهٔ خودش re-arm کند» | ✅ (restore از .pre-disarm) |

**نتیجه:** merge `869a186` KEEP؛ organism زنده و سالم روی chrono v4؛ صفر effect خارجی؛ continuity حفظ شد.

## تصمیم‌های C2 (Resurrection-Safe Memory · 2026-07-23)

| ID | تصمیم | انتخاب | دلیل | برگشت‌پذیر؟ |
|---|---|---|---|---|
| **D-O1** | فلگِ گیتِ deferral-rebuild | PROPOSAL_BUTTONS (caller) + VERDICT_OUTCOME (ماژول) — نه WIRE_SPINE که specِ GAP3 در پرانتز گفته بود | دادهٔ rebuild در outcomes.db است که زیرِ VERDICT_OUTCOME نوشته می‌شود؛ code-reality بر متنِ approximate spec مقدم؛ فلگ جدید ساخته نشد | ✅ |
| **D-O2** | ownerBinding توکنِ pb1 | داخلِ HMAC canon (صفر بایتِ اضافه) نه فیلدِ جدا | wrong-owner ساختاراً = bad-sig؛ سقفِ ۶۴ بایت حفظ | ✅ |
| **D-O3** | تحویلِ durable برای rehydration | event_type=`delivered` موجود در taxonomy + idem `deliv\|pid` در outcomes.db | store/vocab جدید ممنوع (D-M

## تصمیم‌های C4 (One Event Spine — evidence-based، 2026-07-23)

بر پایهٔ نقشهٔ producer/consumer با شواهدِ file:line (cartographer). این‌ها جدولِ SoT بالا را
با **واقعیتِ زنده** تطبیق می‌دهند:

| ID | تصمیم | یافتهٔ کلیدی | انتخاب | برگشت‌پذیر؟ |
|---|---|---|---|---|
| **D-O3** | نقشِ spine.db | spine امروز shadowِ dual-write است (۲ ردیف)؛ truthِ واقعیِ رأی/تصمیم در outcomes.db و ledger است | **spine = ایندکس/projectionِ cross-domain برای replay/correlation** — نه رقیبِ SoTِ outcomes.db. «SoTِ رویداد» به‌معنای *ایندکسِ یگانهٔ رویداد*، نه *store رقیب* | ✅ |
| **D-O4** | events.py + review_bus → projection از spine؟ | ❌ **رد شد با شواهد**: صافیِ ضدPIIِ spine (`event_spine.py:61-74`) دقیقاً فیلدهای متن‌آزادِ آن‌ها (summary/next_action/verdict_note/payload) را حذف می‌کند → projection = داشبوردِ کور | **events.py و review_bus projectionهای مستقل می‌مانند** (نه spine-derived). مأموریتِ step-6 اجرا نشد چون شواهد باطلش کرد | ✅ (بدونِ تغییر) |
| **D-O5** | سطحِ تولیدِ spine | ۲ callerِ مستقیمِ `event_spine.dual_write` (verdict_recorder، wiring) موازیِ spine_adapters بودند | **سطحِ تولیدِ واحد**: `spine_adapters.emit_event` تنها در است؛ ۲ caller پشتِ `OCTOPUS_SPINE_VIA_ADAPTER` (پیش‌فرض 0، parity اثبات‌شده) به آن مسیر داده شدند. loop قدیمی تا soak دست‌نخورده | ✅ (compat flag → 0) |
| **D-O6** | provenance + قراردادِ envelope | برخی رویدادها producer=None داشتند | `publish` حالا producer را به `unknown` default می‌کند؛ `validate_row` قرارداد ۱۰-فیلده را pin می‌کند (test) | ✅ |
| **D-O7** | OVERLAP-0 (هشدارِ watchdog) | either/or: unified_bus **یا** events.jsonl → اگر bus روشن شود داشبورد کور | events.jsonl **همیشه** نوشته می‌شود؛ unified_bus علاوه بر آن | ✅ |
| **D-O8** | archive-candidates | chord/, vault_updater*.py صفر callerِ زنده | **Archive Packet** (`ARCHIVE-PACKET-C4.md`) — propose-only، `git mv` نه `rm`، منتظرِ تأییدِ مالک | ✅ |

**نتیجهٔ حاکمیتی:** «یک SoT برای هر نوع دانش» با تفکیکِ صریحِ نقش‌ها محقق شد — outcomes.db/ledger=substrate،
spine=indexِ replay، events/review=projectionِ داشبورد، chrono=cache. صفر producerِ بی‌صاحب پس از
اتصالِ durable_journal (C2-D). emitِ موازیِ مستقل پشتِ compat flag قرنطینه شد.

## قاعدهٔ فراتصمیم (Meta-rule)

> **هر PR/فاز جدید باید به این سؤال پاسخ دهد: «SoT این دانش کجاست؟»**
> اگر پاسخ «در چند جا» یا «هنوز نمی‌دانم» باشد → مسدود تا روشن شدن.

## وضعیت Keep/Merge/Archive (خلاصه)

| KEEP (SoT یا نقش روشن) | MERGE (projection شود) | ARCHIVE (پس از تأیید P4) |
|---|---|---|
| spine.db, outcomes.db, memory.db, genome ledger, chrono.db, approvals.json, flags.cmd, .env, budgets.yaml, unified_bus (substrate), cardiac.py, vault_updater.py, vault_updater_gate.py | events.py, review_bus.py, vault_updater_apply.py | 2026-07-21 (خالی), Fbackup (سوءتایپ), staging/ (پس از merge), telegram_center/legacy, chord/ (پس از خواندن), baseline/checkpoint/germline/idea_graph (پس از خواندن) |

## ⚠️ مرز مالک (APPROVAL-category — هیچ‌کدام اجرا نشده)

هیچ فایلی **حذف نشده** و هیچ فلگ در runtime **تغییر نکرده**. همهٔ ARCHIVEها
«candidate» هستند و در Phase 4 (بعد از merge + خواندن محتوا) با گزارش به مالک نهایی می‌شوند.
اصل مالک رعایت شد: «هر چیزی که به مغز کمک نمی‌کند → حذف/ادغام/لایه‌بندی» — ولی حذف فیزیکی
= APPROVAL، نه autonomous.
