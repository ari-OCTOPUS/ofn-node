---
type: project
kind: area
project: "[[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT]]"
status: active
owner: آری
risk_level: low
autonomy_level: read-only
tags: [knowledge, psychology, hypnosis, fusion]
created: 2026-07-03
updated: 2026-07-06
---

> **شناسنامهٔ canonical** — این نسخه (با Inventory کامل) در ۲۰۲۶-۰۷-۰۴ تأیید و جایگزینِ v1 شد (ارتقا از `PROJECT.v2-proposal`؛ همهٔ محتوا additive بود).

# پروژه: هیپنوتیزم و خودآگاهی

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

شناخت عمیق سایکی و خویشتن — ترکیب علم و شبه‌علم، به‌علاوه «دنیای فیوژن» (جهان فرضی/داستانی برای آزمایش فکری). اهمیت پژوهشی بالا، اثر مستقیم بیزنسی کم.

## قاعده معرفت‌شناختی (فاز ۱ — الزامی)

هر نوت این حوزه فرانت‌متر **`epistemic_status`** دارد: `peer-reviewed` | `speculative` | `fiction-canon`.

- نوت‌های **Fusion World = fiction-canon** و **هرگز** به‌عنوان evidence در نوت‌های بیزنسی/تصمیمی cite نمی‌شوند (charter §۶ هم‌راستا).
- ایندکس تفکیک تمرین از تئوری: [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/_Index - Practice vs Theory|Practice vs Theory]].
- برچسب‌گذاری اولیه folder-based انجام شد `[Assumption — بازبینی مالک: هر نوتی که peer-reviewed واقعی است ارتقا بده]`.
- وضعیت پوشش برچسب‌ها (2026-07-04): از ۵۵ نوت md — ۵۲ `speculative`، ۲ `fiction-canon` (هر دو در `Fusion-World/`)، ۱ فاقد برچسب: خود `PROJECT.md` (type: project) `[Verified: پارس فرانت‌متر ۵۵ نوت]`. هنوز هیچ نوتی `peer-reviewed` نیست.

## Current state (شواهد — snapshot 2026-07-04)

- محتوا: `knowledge_base.md`، `برنامه_تحقیق_و_چک‌لیست_مجهول‌ها.md`، پوشه `فیوژن هیپنوتیزم/` (شامل `Fusion-World/`، `Silabi-Bot/`، `00_Knowledge_Base/`) + PDFهای canon/roadmap `[Verified: ls]`
- ابعاد: **۸۶ فایل در ۳۰ پوشه، ~۶۴MB** که ~۶۱MB آن فقط `Marathon/` است (دادهٔ خام DNA/EEG) `[Verified: find/du]`
- نودهای تحقیق هیپنوتیزم ساخته‌شده: P0، P1، P2، P2b، P3، X1 — پرامپت‌های P4 تا P7 تعریف شده ولی نودشان ساخته نشده `[Verified: ls nodes/ + 00_RESEARCH_PROMPTS.md]`
- توکن تلگرام hardcode در `Silabi-Bot/silabi_bot.py` و `TODO.md` و `PROJECT_EXPORT_COMPLETE.md` در Phase 0 redact شد `[Verified: Phase 0 + grep — نشانگر REDACTED در محل‌ها دیده شد، هیچ مقدار زنده‌ای یافت نشد]`
- داده شخصی این حوزه (HRV/DNA/تمرین‌ها) طبق O-04: فقط لپ‌تاپ، به VPS نمی‌رود
- ۴ پوشه خالی: `خویشتن/`، `فیوژن آگاهی/`، `Marathon/ماریجوانا دیتوکس/`، `Marathon/ویتامینای مفید/` `[Verified: find]`
- ۱ جفت فایل byte-identical شناسایی شد (جزئیات در Inventory) `[Verified: md5sum]` → **حل شد 2026-07-04**: نسخه ریشه به `_Duplicates` منتقل و در گزارش تکراری‌ها ثبت شد؛ canonical: `Marathon/امواج مغزی/پیاده روی.zip`

## Agent interface

- **می‌خواند:** همه نوت‌های حوزه (با احترام به epistemic_status).
- **می‌نویسد:** ایندکس/خلاصه (read-only indexer)؛ نوت جدید فقط پیشنهادی.
- **ممنوع:** cite کردن fiction-canon در هر نوت بیرون این حوزه؛ انتقال داده شخصی به بیرون لپ‌تاپ.

## Active Context

- تمرکز فعلی: تفکیک معرفت‌شناختی محتوا (تمرین vs تئوری vs داستان)
- تغییرات اخیر: 2026-07-04 (agent، آدیت) — Inventory snapshot + دو فایل پیشنهادی ساخته شد (همین فایل + [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/MAP|MAP]])؛ هیچ فایل موجودی تغییر نکرد. | 2026-07-04 (agent) — دو گزارش تحقیقاتی به Inbox: [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/Report - هیپنوتیزم - Cardew و حلقه New Thought سیدنی|Cardew/New Thought]] و [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/Report - هیپنوتیزم - HRV و خودهیپنوتیزم|HRV × خودهیپنوتیزم]]. یافته‌های Cardew در چک‌لیست مجهول‌ها §یافته‌های 2026-07-04 و لینک HRV در Practice-vs-Theory ادغام شد (همه additive، در انتظار بازبینی). | 2026-07-04 (triage، verdict آری) — هر دو گزارش + [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/Prompt - هیپنوتیزم - آدیت و بازسازی PROJECT + نقشه 2026-07-04|پرامپت آدیت اجراشده]] از Inbox به همین پوشه منتقل شدند (status: done + epistemic_status)؛ `files.zip` → `_Archive` (قاعده ۳)؛ zip تکراری mindMonitor → `_Duplicates` (قاعده ۴) | 2026-07-03 — manifest فاز ۱ + epistemic_status + ایندکس Practice vs Theory
- ۳ قدم بعدی: (۱) بازبینی برچسب‌های [Assumption] توسط مالک (۲) ثبت لاگ‌های تمرین آینده زیر Practice (۳) ارتقای نوت‌های دارای منبع به peer-reviewed
- تصمیم‌های باز: O-04 (HRV فقط لپ‌تاپ) پابرجا؛ پروتکل n-of-1 آماده اجرا؛ تصمیم‌های تازهٔ آدیت در «Next actions»

## Progress

- چه کار می‌کند: بدنه دانش + جهان فیوژن موجود و ایندکس‌شده؛ Inventory کامل و نقشهٔ ساختار (proposal) موجود
- چه مانده: بازبینی انسانی برچسب‌ها؛ لاگ تمرین ساختاریافته؛ نودهای P4–P7؛ verdict مالک روی proposals
- مشکلات شناخته: برچسب‌ها فعلاً folder-based و فرضی‌اند؛ کد اجرایی (`silabi_bot.py`) داخل پوشهٔ دانشی است (خلاف قاعدهٔ ۳/۴ فایل‌گذاری)؛ ~~یک جفت zip تکراری~~ (حل شد 2026-07-04)

## Next actions

- [ ] بازبینی برچسب‌های epistemic_status (مالک)
- [ ] اولین لاگ تمرین با قالب ایندکس
- [ ] تأیید/رد جایگزینی `PROJECT.md` با این نسخه و پذیرش `MAP.md` (مالک)
- [ ] تصمیم: انتقال `silabi_bot.py` به `_code` پس از باز شدن گیت rotation (قاعدهٔ ۴)
- [x] تصمیم: جفت zip تکراری (Inventory §تکراری‌ها) → `_Duplicates` — اجرا شد 2026-07-04 (verdict آری در جلسه triage)
- [ ] تصمیم: چهار پوشهٔ خالی — placeholder بمانند یا حذف شوند
- [ ] تصمیم: آیا فایل‌های `type: project` مشمول قاعدهٔ epistemic_status هستند یا معاف

## Inventory (snapshot 2026-07-04)

> همهٔ اعداد این بخش `[Verified: find/du/grep/md5sum 2026-07-04]` مگر خلافش ذکر شود. هیچ محتوای حساسی نقل نشده — فقط نام/محل.

### شمارش

- **۸۶ فایل · ۳۰ پوشه · ~۶۴MB** (که ~۶۱MB = `Marathon/`، عمدتاً دادهٔ خام DNA)
- بر اساس پسوند: md ۵۵ · pdf ۱۱ · zip ۶ · txt ۵ · html ۳ · py ۱ · و تک‌فایل‌های vcf / ped / map / json / jpg
- فرانت‌متر: هر ۵۵ نوت md دارای type / status / updated؛ توزیع type: project ۱ · moc ۱ · reference ۲ · telegram-log ۱ · knowledge ۵۰

### زیرشاخه‌ها و نقش‌ها

| مسیر نسبی | نقش | نکته |
|---|---|---|
| (ریشه) | اسناد مرجع: `knowledge_base.md` (بدنه دانش، ۷ بخش)، `برنامه_تحقیق_و_چک‌لیست_مجهول‌ها.md` (پروژه Cardew/New Thought، ۷ مسیر + ۱۶ مجهول)، لاگ تلگرام `هیپنوتیزم و خودآگاهی.md` (~۱۰۸KB)، `_Index - Practice vs Theory.md` | + `تحقیق مخفی.txt` (متن کاربردی با استعاره‌های فیوژن؛ بدون فرانت‌متر — نامزد تبدیل به md و برچسب‌گذاری) و ~~`files.zip`~~ (محتوا بررسی نشد؛ → `_Archive/from-vault-2026-07-04` منتقل شد 2026-07-04 طبق قاعده ۳) |
| (ریشه — PDFها) | canon فیوژن ×۴: masque، mutuality، jahan-e-fusion-gostaresh، warp-machine (همه fiction-canon) · build/roadmap ×۲: fusion-build-roadmap، fusion-multiagent-2026-checklist · مفهومی: LANGAR BLUEPRINT، PATTERNS OF TRANSFORMATION، 10 AI VARIABLES · heart-awareness-map (pdf + دو نسخه html) | PDFها طبق قاعدهٔ ۲ کنار نوت هم‌موضوع‌اند |
| `فیوژن هیپنوتیزم/00_Knowledge_Base/` | پایگاه دانش ۱۷ بخش شماره‌دار (01_AI تا 17_Archive، هرکدام README) + ۱۷ نوت موضوعی (INDEX، KnowledgeGraph، OpenQuestions، DecisionLog، …) | سنگین‌ترین بخش نوت‌ها |
| `فیوژن هیپنوتیزم/Hypnosis-Research/` | تحقیق هیپنوتیزم واقعی: `00_RESEARCH_PROMPTS.md` (P0–P7) + `nodes/` (P0، P1، P2، P2b، P3، X1) + `Hamfazi_Qodrat_Dual_Register_v1.md` | P4–P7 نساخته |
| `فیوژن هیپنوتیزم/Neuro-HRV-Nof1/` | پروتکل n-of-1 (هندآف، master prompt، چک‌لیست، نقشهٔ html) — مرتبط O-04 | هنوز داده/لاگی ثبت نشده |
| `فیوژن هیپنوتیزم/Fusion-World/` | **fiction-canon** — ۲ نوت (CONTEXT handoff، THEORY seam detective) | هرگز evidence نیست |
| `فیوژن هیپنوتیزم/Silabi-Bot/` | ربات تلگرام: `roadmap.md` (فاز ۰–۴) + `silabi_bot.py` | کد اجرایی داخل پوشهٔ دانشی — تصمیم انتقال به `_code` |
| `فیوژن هیپنوتیزم/` (ریشه) | `PROJECT_EXPORT_COMPLETE.md` (~۲۲۲KB، export کامل قدیمی) + `_PROJECT_INSTRUCTIONS.md` | export حجیم؛ نامزد بازبینی |
| `Marathon/` | بدن/عملکرد: `امواج مغزی/` (گزارش و دادهٔ خام DNA + سه zip جلسات EEG) · `تمرینات ورزشب/دیتا.txt` · GenomeInsight PDF · `Plan is to copy this guy.txt` (لینک مربی) | دادهٔ شخصی — بخش بعد |
| `photos/` | ۱ عکس (photo_786…jpg) | طبق قاعدهٔ ۶ جای عکس‌ها `08 - Assets` است — تصمیم مالک |
| `خویشتن/` · `فیوژن آگاهی/` · `Marathon/ماریجوانا دیتوکس/` · `Marathon/ویتامینای مفید/` | **خالی** | placeholder یا حذف؟ |

### نوت‌های فاقد epistemic_status

فقط ۱ مورد: `PROJECT.md` (type: project — احتمالاً شناسنامه‌ها معاف‌اند `[Assumption — بازبینی مالک]`). سایر ۵۴ نوت برچسب دارند.

### اسناد شخصی حساس (O-04 — فقط لپ‌تاپ؛ ارجاع فقط با نام)

`ARMIN_DNA_REPORT.md` · `armin_dna.vcf` / `.ped` / `.map` · `armin_dna_23andme_format.txt` · `armin_dna_summary.json` · `MyHeritage_raw_dna_data.zip` · `GenomeInsight Report — MyHeritage_raw_dna_data.csv.pdf` · zipهای EEG (`خونه`، `رندوم`، `پیاده روی`، `mindMonitor_2026-01-24…`) · `تمرینات ورزشب/دیتا.txt` · `photos/photo_786…jpg`

### تکراری‌ها (فقط گزارش — گیت read-only، هیچ انتقالی انجام نشد)

- `mindMonitor_2026-01-24--19-12-19_….zip` (ریشه) ≡ `Marathon/امواج مغزی/پیاده روی.zip` — **byte-identical** `[Verified: md5sum]`. پیشنهاد: پس از گیت، یکی به `_Duplicates` + ثبت در گزارش تکراری‌ها (کدام نسخه canonical بماند = تصمیم مالک؛ پیشنهاد: نسخهٔ داخل `امواج مغزی` بماند چون هم‌بافت است). → **✅ اجرا شد 2026-07-04**: hash دوباره تایید، نسخه ریشه → `_Duplicates` + ثبت در `_گزارش تکراری‌ها.txt`؛ نسخه `امواج مغزی` ماند.

### چک امنیتی سبک (grep الگوها — فقط کلیدواژه، بدون مقدار)

- محل‌های دارای الگوی secret — همگی placeholder ردکت‌شده یا صرفاً نام متغیر، **هیچ مقدار زنده‌ای دیده نشد**: `Silabi-Bot/silabi_bot.py` (خط ۲۶، ۶۶) · `Silabi-Bot/roadmap.md` (۴۲) · `00_Knowledge_Base/TODO.md` (۱۴) · `Architecture.md` (۲۵) · `Experiments.md` (۳۳) · `Projects.md` (۴۵) · `01_AI/README.md` (۱۹) · `PROJECT_EXPORT_COMPLETE.md` (۲۰۶۲، ۲۱۵۷، ۲۱۹۷، ۲۷۷۲، ۲۸۰۹) — همه «[secret — redacted]»
- هیچ فایل `.env` / wallet / seed / key در این پوشه وجود ندارد `[Verified: find]`
- چرخش توکن ردکت‌شده همچنان ذیل [[ROTATION_CHECKLIST]] پیگیری می‌شود

### پل مفهومی بیرونی (رابطه — نه evidence)

مفهوم «لنگر/لنگرزاد» (fiction) در ۱۲ نوت این پروژه + `LANGAR BLUEPRINT.pdf` حاضر است و با «Anchor Ledger» در سیستم واقعی architect/fusion-mvp (charter + اسناد fusion-audit) هم‌ریشه است `[Verified: grep دو طرف]`. این صرفاً ردیابی خاستگاه ایده است؛ طبق قاعدهٔ معرفت‌شناختی، سمت fiction هرگز evidence سمت واقعی نیست.

## مجهول‌ها / سوالات باز (هم‌گرا از OpenQuestions + برنامه تحقیق + knowledge_base §۵ — فقط عنوان و وضعیت)

### الف) علمی — هیپنوتیزم

| # | سوال | وضعیت |
|---|---|---|
| OQ1 | نام دقیق هیپنوتیزم‌گر مرتبط با تایسون/دامیاتو | ⬜ باز |
| OQ2 | آیا مطالعهٔ «Basel 1997» (هماهنگی ضربان تماشاگران) اصلاً وجود دارد؟ | ⬜ باز — بدون منبع تأییدشده |
| OQ3 | آیا «عمق» هیپنوتیک آموختنی است؟ (CSTP–Spanos، نود P3) | ⬜ مناقشهٔ حل‌نشده |
| OQ4 | کدام لنز نظری: state/non-state، neo-dissociation، predictive-processing؟ | ⬜ باز (P0: رقیب‌اند نه مکمل) |
| OQ5 | آیا هیپنوتیزم/flow/peak-performance یک الگوی واحدند؟ | ⬜ منتظر ساخت نود P4 |

### ب) عملیاتی

| # | سوال | وضعیت |
|---|---|---|
| OQ6 | دادهٔ Neuro-HRV هنوز جمع‌آوری نشده | ⬜ باز — پروتکل n-of-1 و سنسور پیشنهادی آماده |
| OQ7 | وضعیت فاز ۲–۴ Silabi-Bot و فایل `silabi.db` | ⬜ باز — پوشهٔ «خویشتن» اینجا خالی است `[Verified]` |
| OQ8 | توکن hardcode در `silabi_bot.py` | 🟦 redact شد (Phase 0)؛ چرخش ذیل ROTATION_CHECKLIST |
| OQ9 | کلید ادعایی در `.env.example`ِ fusion-mvp | 🟦 خارج از این پوشه — ذیل rotation |
| OQ10 | تعریف رسمی INV-1/2/3 | ⬜ باز |
| OQ11 | مرجع: `SERVER_ARCHITECTURE.md` یا `infra-control`؟ | ⬜ باز |
| OQ12 | آیا دامنهٔ «همین پوشه + دایجست» کافی است؟ | ⬜ تصمیم مالک (DecisionLog #۱) |

### ج) تاریخی — Cardew / New Thought سیدنی

۱۶ مجهول در «بخش ۳» برنامهٔ تحقیق (سوژه، بیوگرافی، پیکرهٔ نشریات، شبکه، سانسور، …). وضعیت 2026-07-04: توالی نشریات و شبکهٔ سیدنی تأیید شد (§یافته‌های 2026-07-04)؛ نام کامل/تاریخ‌های Cardew همچنان باز (Trove/BDM قابل کوئری نبود). بقیهٔ ردیف‌ها ⬜.

## نوت‌های مرتبط

- [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/_Index - Practice vs Theory|_Index - Practice vs Theory]]
- [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/knowledge_base|knowledge_base]]
- [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/برنامه_تحقیق_و_چک‌لیست_مجهول‌ها|برنامه تحقیق و چک‌لیست مجهول‌ها]]
- [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/هیپنوتیزم و خودآگاهی|لاگ پیام‌های تلگرام]]
- [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/MAP|MAP — نقشهٔ ساختار (canonical)]]

## 🎛 کابین کنترل (two-brain)

- کابین مشترک: ارتیفکت `fleet-live-dashboard` · نقشه: [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN]] · نقشهٔ ساخت: [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]]
- عملیات استاندارد از کابین (intent → sendPrompt): «تست <پروژه>» = validators + چک کد + تست قرارداد · «بساز» = اسکلت از `_Templates` + ثبت همین‌جا · «آرشیو» = فقط انتقال به `_Archive`/`_Duplicates` (هرگز حذف واقعی).
- تست قرارداد این پروژه: هنوز تعریف نشده — طبق BUILD-PLAN §۲ تعریف شود.
