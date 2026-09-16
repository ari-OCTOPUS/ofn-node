---
type: proposal
status: draft
tags: [build-proposal, review-packet, verdict, autonomous, propose-only]
created: 2026-07-05
updated: 2026-07-05
sources: "[[00 - Inbox/build-proposals/_README - Build Proposals|build-proposals README]], [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]], [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]], [[04 - Architect System/BUILD-BACKLOG|BUILD-BACKLOG]], [[ROTATION_CHECKLIST]], [[_memory/EXPERIENCE-LEDGER|ledger]]"
---

# REVIEW-PACKET — جمع‌بندیِ ۶ پیشنهادِ حلقهٔ خودکار برای verdictِ آری (2026-07-05)

> [!info] این نوت = آیتمِ ۷ صف. یک برگهٔ تصمیمِ **تک‌توقفی**: هر ۶ پیشنهادِ `build-proposals/` را کنارِ هم می‌گذارد، هر verdict را چک‌باکس می‌کند، و بر حسبِ **وابستگی/ROI** مرتب می‌کند. **هیچ‌چیز اعمال نشده — همه propose-only.** خودِ این پکت هم فقط جمع‌بندی است، نه اعمال.

## ۱. خلاصهٔ سریع (Quick Summary)

- **چه داری:** ۶ پیشنهادِ آمادهٔ verdict — ۲ پکِ کدنویسِ Fable 5 (موج۱ · موج۲/۳)، ۱ Reflexion روی spec (۳ diff)، ۱ runbookِ git-init، ۲ digestِ تحقیق (AI-eng · opsec) با پیشنهادهای P-05/P-06.
- **گیتِ حاکم بر همه‌چیز = rotation.** چهار ردیفِ CRITICALِ [[ROTATION_CHECKLIST]] هنوز باز است؛ تا Revoke+Rotate+verify-at-service نشوند، Security Gate بسته می‌ماند و git-init/P-06/L2 منتظرند. **درسِ تأییدشدهٔ بیرونی (پیشنهادِ ۰۶): «حذفِ فایلِ محیطی ≠ چرخش»** — حذفِ سه فایلِ جلسهٔ ۱۳ فقط containment بود، نه بازکردنِ گیت.
- **بزرگ‌ترین اهرمِ تو (۱ اقدام):** یک sprintِ چرخش که هر چهار ردیف را ببندد → هم‌زمان git-init + P-06 + L2 + فعال‌سازیِ milestoneهایِ زنده را باز می‌کند.
- **کم‌هزینه‌ترین بسته‌بندی:** همهٔ diffهای «فقط-سند» (۰۳ + ۰۵ + ۰۶) را در **یک** جلسهٔ تعاملی با **یک** version-bump (spec v0.1→v0.2) اعمال کن.
- **چه ساختنی‌ست همین حالا، قبل از rotation:** M5 (بکاپِ off-box)، موج۱ (M0–M3، همه fusion/MOCK)، جایگزینیِ `.gitignore`ِ سخت، و همهٔ diffهای سند. هیچ‌کدام به چرخش/پول/شبکه وابسته نیستند.

## ۲. تحلیل (Problem · Goal · Constraints · Risks)

- **Problem:** ۶ پیشنهاد در ۶ اجرا انباشته شده؛ آری برای verdict یک نمای واحد لازم دارد، نه ۶ فایلِ جدا.
- **Goal:** هر تصمیم را atomic و چک‌باکس‌شده کن؛ وابستگی‌ها و ترتیبِ بهینه را نشان بده تا آری در چند دقیقه accept/reject کند.
- **Constraints:** propose-only مطلق؛ فقط جمع‌بندی؛ هیچ اعمال/کد/چرخش/git.
- **Risks اگر معطل بماند:** (۱) drift — §۳ spec دستِ‌کم ۵ تسکِ زندهٔ زمان‌بند را نمی‌شناسد (۰۳/D1)؛ (۲) دو گپِ امنیتیِ high-blast-radius که spec v0.1 ندارد (۰۵) روی سطحِ حملهٔ حافظه بازند؛ (۳) بدونِ M5، vaultِ بی‌git تنها rollback ندارد.

## ۳. جدولِ ۶ پیشنهاد (نگاهِ یک‌سطری)

| # | عنوان | نوع | ریسک | برگشت‌پذیر؟ | بستهٔ verdict | بلاکِر |
|---|---|:--:|:--:|:--:|---|---|
| [[00 - Inbox/build-proposals/01-fable5-codepack-wave1-2026-07-05\|۰۱]] | پکِ کدِ Fable موج۱ (M0→M1→M2→M3) | proposal | 🟢 کم | بله (کد MOCK) | ۳ سؤال + تأییدِ hand-off | — (fusion/MOCK؛ pre-rotation امن) |
| [[00 - Inbox/build-proposals/02-fable5-codepack-wave2-3-2026-07-05\|۰۲]] | پکِ کدِ موج۲ (M4·M6) + موج۳ (M5·M7·M8) | proposal | 🟡 متوسط | بله | ۴ سؤال | موج۱ (M4/M6 کدِ langarِ زنده) |
| [[00 - Inbox/build-proposals/03-mycelial-spec-reflexion-2026-07-05\|۰۳]] | Reflexion §۷ روی spec (۳ diff) | proposal | 🟢 کم | بله (سند) | ۳ diff + ۲ کارِ باز | — |
| [[00 - Inbox/build-proposals/04-git-init-runbook-2026-07-05\|۰۴]] | runbookِ git-init + `.gitignore`ِ سخت | runbook | 🟢 کم (اجرا با آری) | بله (rollback محلی) | اجرا + جایگزینیِ `.gitignore` | **rotation** |
| [[00 - Inbox/build-proposals/05-ai-agent-eng-2026-2026-07-05\|۰۵]] | تحقیقِ AI-eng ۲۰۲۶ → P-05 | research | 🟢 کم | بله (سند) | ۲ diff + schema | — |
| [[00 - Inbox/build-proposals/06-opsec-rotation-2026-07-05\|۰۶]] | تحقیقِ opsec/چرخش ۲۰۲۶ → P-06 | research | 🟢 کم (چرخش دستِ آری) | — (چرخش برگشت‌ناپذیر) | runbookِ ۴-گامی + سخت‌سازی | **rotation** |

## ۴. verdictهای موردنیاز — چک‌باکس به تفکیکِ پیشنهاد

### پیشنهادِ ۰۱ — پکِ کدِ موج۱ (fusion، MOCK، کم‌ریسک)

خلاصه: چهار پرامپتِ آمادهٔ کدنویس — M0 (سبز کردنِ سوئیت)، M1 (fail-closed کردنِ fallbackِ IGK)، M2 (EffectorGateِ واقعی روی side-effectها)، M3 (تنزلِ `[DEGRADED]` به‌جای جعل). همه در MOCK، بی‌کلیدِ واقعی.

- [ ] **V1.1 دانه‌بندی:** milestone-به-milestone با مرور بینِ هر تکه (پیش‌فرضِ امن) · یا M0→M3 یک‌جا؟
- [ ] **V1.2 `IGK_REQUIRED=True`** (fail-closed) پیش‌فرض بماند؟ (امن‌تر ولی در dev اصطکاک)
- [ ] **V1.3 دامنهٔ M2:** فقط side-effectها گیت شوند (پیش‌فرض، اصلِ صفحهٔ effector) · یا هر reasoning-call هم؟
- [ ] **V1.4 hand-off:** پرامپتِ **M0** به Fable 5 داده شود؟ (= verdictِ بازِ §۱۰ spec / HANDOFF #۵؛ کم‌ریسک‌ترین شروع)

### پیشنهادِ ۰۲ — پکِ کدِ موج۲/۳ (کدِ langarِ زنده + تابِ بقا)

خلاصه: M4 (گاردِ بودجهٔ سراسری + دیسک)، M6 (سیم‌کشیِ observability)، M5 (بکاپِ off-box)، M7 (پنلِ واقعی)، M8 (promote استرس-گیتی). **موج۲ کدِ باتِ زنده را لمس می‌کند — شعاعِ بزرگ‌تر از موج۱.**

- [ ] **V2.1 دانه‌بندی:** milestone-به-milestone (توصیه، چون M4/M6 زنده‌اند)؟
- [ ] **V2.2 M4:** halt در معادلِ AU$30/ماه (D-25) درست است؟ alertهای ۵۰/۸۰٪ → notification یا فقط audit؟
- [ ] **V2.3 سیگنالِ استرسِ M8:** از observabilityِ M6 (یک منبعِ حقیقت، دیرتر) · یا ورودیِ سادهٔ مستقل (زودتر)؟
- [ ] **V2.4 مقصدِ بکاپِ M5:** مسیرِ ثابت (USB/دیسکِ دوم) تعیین می‌کنی تا در اسکریپت پیش‌فرض شود؟

### پیشنهادِ ۰۳ — Reflexion روی spec (۳ diffِ فقط-سند، اعمال‌نشده)

خلاصه: نقدِ adversarial ۳ ضعف یافت — W1 تورِ ایمنی (M5) آخر ساخته می‌شود · W2 گاردِ delete فقط policy است نه گیتِ اجرایی · W3 معیارِ «validator سبز» روی خودِ spec اجرا نمی‌شود.

- [ ] **V3.1 Diff-1:** M5 را به **موج۰** جلو بیاور (بی‌وابستگی، تورِ ایمنیِ کلِ ساخت + پیش‌شرطِ delete). **کم‌هزینه‌ترین، بیش‌ترین اثر.**
- [ ] **V3.2 Diff-2/3:** دو تبصره (delete تا ساختِ گیتِ fs «دست‌انسانی» بماند · دامنهٔ validator §۹ صریح شود).
- [ ] **V3.3 کارِ باز:** رفعِ ریشه‌ای (M نو «fs-effector-gate» + افزودنِ «04 - Architect System» به `SYSTEM_FOLDERS`ِ validator) به BUILD-BACKLOG افزوده شود؟
- [ ] **V3.4 اختیاری Diff-4:** یک پاسِ سبکِ برچسبِ biomimicry ([G]/[J]) روی استعاره‌های prose (فرانکنشتاین/بامبو)؟
- توجه: D1/D3 (drift §۳ + وارونگیِ روایتِ «۶ زنده/۲۶ تاریک») در همین پکت لحاظ شد → بخشِ ۶.

### پیشنهادِ ۰۴ — runbookِ git-init + `.gitignore`ِ سخت

خلاصه: کپی-چسبانِ PowerShell برای اجرای **دستیِ** آری. `.gitignore` قبل از `add` → دو گیتِ pre-commit → gitleaks روی staged → اولین commitِ clean → rollback با حذفِ `.git`. یافته: `.gitignore`ِ فعلی سه گپ دارد که با `.agentignore` هماهنگ نیست.

- [ ] **V4.1 گیت:** آیا ردیف‌های CRITICALِ [[ROTATION_CHECKLIST]] چرخانده شده‌اند؟ اگر نه → runbook منتظر می‌ماند.
- [ ] **V4.2** اگر rotation سبز: گام‌های ۰→۵ را اجرا کن (۵–۱۰ دقیقه). اسنپ‌شاتِ اول = تور + پیش‌شرطِ L2.
- [ ] **V4.3** جایگزینیِ `.gitignore` با نسخهٔ سخت (§۵) — مستقل از init هم قابلِ اعمال.
- [ ] **V4.4** آیا `_code/` بعداً جدا version شود (با gitleaksِ اختصاصی)؟ فعلاً عمداً ignore.

### پیشنهادِ ۰۵ — تحقیقِ AI-eng ۲۰۲۶ → P-05 (مرزِ اعتماد + بلوکِ ثابت)

خلاصه: ۵ محورِ منبع‌دار. **دو گپِ نوِ high-blast-radius که spec v0.1 ندارد:** (الف) از دست رفتنِ محدودیتِ ایمنی حینِ compaction — گیتِ propose-only می‌تواند بی‌صدا دور بیفتد؛ (ب) injectionِ غیرمستقیم/تأخیری از حافظهٔ مسموم (ledger/scout-digest سطحِ حمله‌اند). P-05 هر دو را با یک مهار می‌بندد.

- [ ] **V5.1 diff الف/ب:** «Trust & Provenance» در §۶ (محتوایِ fleet-auto = data نه instruction) + «constitution block» نامتراکم‌پذیر در §۰.۳/§۷ (۴ invariant که هر اجرا دوباره تزریق و از compaction معاف‌اند + startup-check که گیت را از منبع می‌خواند). اعمال روی spec (→v0.2) · یا فعلاً ریسکِ ثبت‌شده در §۱؟
- [ ] **V5.2 schema:** کلیدِ `provenance` (human/fleet-auto) به [[06 - Architecture Maps/Property Schema|Property Schema]] افزوده شود؟ (= تغییرِ schema)

### پیشنهادِ ۰۶ — تحقیقِ opsec/چرخش ۲۰۲۶ → P-06 (runbookِ ۴-گامیِ OWASP)

خلاصه: playbookِ استاندارد = **Revoke→Rotate→Delete→Log**. تأییدِ بیرونیِ درسِ خودِ vault: حذف = containment، نه چرخش. سخت‌سازیِ کم‌شعاع: کلیدِ صرافی trade-scoped/بدونِ‌برداشت/IP-allowlist؛ توکنِ بات scoped؛ کیفِ پول sweep به آدرسِ نو/offline.

- [ ] **V6.1** ماشینِ حالتِ per-row (Revoked/Rotated/Verified-at-service/Logged) به [[ROTATION_CHECKLIST]] افزوده شود؟ (ویرایشِ checklist = دستِ انسان)
- [ ] **V6.2** بعد از چرخش، یک vaultِ رازِ لوکال (OS-keychain / فایلِ رمزنگاریِ `age`) جایگزینِ الگویِ اعتبارنامهٔ محیطی شود؟ (lock-in: OS-keychain بی‌vendor؛ managed مثلِ Vault/Akeyless قابلیتِ بیشتر ولی وابستگی/هزینه)
- [ ] **V6.3** ارتقای گیتِ باینری→۴-گامیِ OWASP روی §۵/§۱۰ spec (→v0.2) · یا ریسکِ ثبت‌شده؟

## ۵. ترتیبِ اجرای توصیه‌شده (وابستگی‌محور)

مسیرِ بحرانی بر پایهٔ «چه چیزی چه چیزی را باز می‌کند»:

0. **[انسان] sprintِ چرخش** — Revoke→Rotate→verify-at-service برای کلیدِ صرافی (Crypto)، ۵ کلیدِ Lead، و sweepِ کیفِ پول (Mining). **بالاترین اهرم:** هم‌زمان Security Gate + git-init + P-06 + L2 را باز می‌کند. (V4.1، V6.1)
1. **[حالا · pre-rotation] M5 بکاپِ off-box** — بی‌وابستگی، تورِ ایمنی + پیش‌شرطِ delete. اگر V3.1 accept شود، این «موج۰» است. (V2.4، V3.1)
2. **[حالا · pre-rotation] موج۱ کدنویس** M0→M1→M2→M3 — همه fusion/MOCK، بی‌کلیدِ واقعی. (V1.*)
3. **[حالا · pre-rotation] بستهٔ spec v0.2 در یک جلسه** — Diff-1/2/3 (۰۳) + P-05 (۰۵) + گیتِ ۴-گامیِ P-06 (۰۶) + Diff-4 اختیاری، همه با یک version-bump. (V3.1/2، V5.1، V6.3)
4. **[بعد از rotation] git-init + `.gitignore`ِ سخت** (۰۴) — rollback + پیش‌شرطِ L2. (V4.2)
5. **[بعد از rotation] سخت‌سازیِ P-06** — کلیدهایِ نو least-privilege. (V6.2)
6. **[بعد از موج۱] موج۲/۳ کدنویس** — M4·M6 (langarِ زنده)، سپس M7·M8 (M5 اگر در گام۱ ساخته نشد). (V2.*)

> نکته: گام‌های ۱–۳ به چرخش وابسته **نیستند** و با verdictِ تعاملی همین حالا جلو می‌روند؛ گام‌های ۰/۴/۵ گیتِ انسانیِ چرخش دارند.

## ۶. یافته‌های میان‌بخشی (برای آگاهیِ آری، نه verdict)

- **drift §۳ (از ۰۳/D1):** «رجیستریِ اتصالِ رسمیِ» §۳ spec دستِ‌کم ۵ تسکِ enabledِ زمان‌بند را نمی‌شناسد: `ai-eng-radar-brief` · `ai-eng-week-in-review` · `research-radar-curator` · `survival-heartbeat` · `bio-synthesis-daily`. منبعِ‌حقیقتی که همه را نمی‌شمارد همان drift را می‌سازد که قرار بود بکشد → پیشنهاد: ردیفِ «اندام‌های مشاهده‌شده اما بی‌رجیستری» + ستونِ «آخرین verify (تاریخ)» در §۳ (کارِ جلسهٔ تعاملی، با verdict).
- **روایتِ وارونه (۰۳/D3):** «۶ هسته زنده / ۲۶ تاریک» — [[00 - Inbox/SYSTEM-STATE-2026-07-05|SYSTEM-STATE]] نشان داد آن ۲۶ در واقع enabled بودند و ۳ از ۶ هسته غایب. این اجرا (۷) زمان‌بندِ زنده را **۷ تسک** دید (۶ هسته + خودِ `build-planner-loop`)، همه ۶ ratified حاضر و enabled (system-dashboard عمداً disabled) → آشتیِ فعلی سالم، ولی framing در §۳ بهتر است سطحی‌شود.
- **همگراییِ نسخه:** هر سه پیشنهادِ سند (۰۳/۰۵/۰۶) به یک version-bump v0.1→v0.2 اشاره می‌کنند → در یک جلسه bundle شوند (بخشِ ۵ گام۳).
- **حلقهٔ درسِ تأییدشده:** پیشنهادِ ۰۶ به‌طورِ مستقل درسِ ردیف ۴۹/۵۰ ledger («حذف ≠ چرخش») را با منبعِ بیرونی (OWASP/Truffle/GitHub) تأیید کرد → اعتماد به آن درس ↑.

## ۷. Trade-off — چرا این ترتیب (خلاصهٔ نمرات از خودِ پیشنهادها)

| بسته | Cost | Complexity | Security-ROI | چه‌وقت |
|---|:--:|:--:|:--:|---|
| sprintِ چرخش (P-06) | سند ارزان · اجرا دستِ آری | ۴/۱۰ | **۱۰/۱۰** | اول — بازکنندهٔ کل |
| M5 + موج۱ | ۱–۲/۱۰ | ۲/۱۰ | ۷/۱۰ | حالا (pre-rotation) |
| بستهٔ spec v0.2 (۰۳+۰۵+۰۶-diff) | ۱/۱۰ | ۳/۱۰ | ۹/۱۰ (P-05 دو گپ) | حالا (یک جلسه) |
| git-init (۰۴) | ۱/۱۰ | ۲/۱۰ | ۸/۱۰ | بعد از چرخش |
| موج۲/۳ | ۳/۱۰ | ۵/۱۰ | ۶/۱۰ | بعد از موج۱ |

> نمرات از جداولِ trade-offِ پیشنهادهای ۰۴/۰۵/۰۶ برداشته شد. توجه به جهتِ مقیاسِ Cost: در ۰۴ پایین‌تر=ارزان‌تر، در ۰۵/۰۶ بالاتر=ارزان‌تر؛ برای جزئیات به متنِ هر پیشنهاد رجوع کن.

## ۸. آنچه هنوز تصمیم‌نشده / تغییراتِ schema

- کلیدِ `provenance` در Property Schema (V5.2) — تغییرِ schema.
- ماشینِ حالتِ per-row در ROTATION_CHECKLIST (V6.1) — ویرایشِ انسانی.
- افزودنِ «04 - Architect System» به `SYSTEM_FOLDERS`ِ validator (V3.3) — تغییرِ اسکریپت.
- vaultِ رازِ لوکال بعد از چرخش (V6.2) — تصمیمِ معماری.

همه پشتِ verdict؛ هیچ‌کدام در این اجرا لمس نشد.

## ۹. راستی‌آزمایی و ثبت (این اجرا)

- **اسکنِ راز:** این نوت صفر مقدارِ رازِ واقعی/PII دارد؛ همهٔ ارجاع‌ها به اعتبارنامه/کلید/کیفِ پول فارسی و مفهومی‌اند. AU$30 سقفِ عمومیِ D-25 است. قاعدهٔ Project-F: هیچ نام/پلتفرمِ Project-F اینجا نیست.
- **زمان:** از `lastRunAt`ِ زمان‌بندِ `build-planner-loop` = `2026-07-05T10:54:16Z` ≈ **۲۰:۵۴ AEST (Sydney)**، نه `date`ِ سندباکس.
- **stale-view:** خواندنِ ۶ پیشنهاد + ledger با inodeِ تازه؛ منبعِ اعداد = خروجیِ زندهٔ زمان‌بند (۷ تسک) نه markdown.
- **validatorها:** هر دو اسکریپتِ `04 - Architect System/scripts/` بعد از افزودنِ این نوت اجرا شد؛ نباید خطای نو بسازد (این فایل در `00 - Inbox/` = SYSTEM_FOLDER، پس frontmatter چک می‌شود).

## ۱۰. گام بعد (برای آری)

1. **اول:** تصمیمِ sprintِ چرخش (بخشِ ۵ گام۰) — بالاترین اهرم؛ کلِ build-spine را باز می‌کند.
2. verdict روی V1–V6 (چک‌باکس‌ها بالا) — می‌توانی گام۱–۳ (pre-rotation) را همین حالا سبز کنی بدونِ اینکه منتظرِ چرخش بمانی.
3. برای توقفِ حلقه: تسکِ `build-planner-loop` را disable کن؛ وگرنه از آیتمِ ۸ (idle) وارد **حالتِ تحقیقِ پیوسته** می‌شود و هر ۳۰ دقیقه یک digestِ نو می‌سازد.

> **پایان — propose-only.** این پکت فقط جمع‌بندی است؛ هیچ پیشنهادی اعمال، هیچ specی/کدی/تسکی/رازی/گیتی لمس نشد. صف: آیتم۷ `[x]`. لینک در README + ردیفِ ledger + خطِ لاگِ اجراها ثبت شد.
