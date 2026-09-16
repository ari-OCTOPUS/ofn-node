---
type: proposal
status: draft
tags: [build-proposal, reflexion, spec-critique, mycelial, self-improving]
created: 2026-07-05
updated: 2026-07-05
sources: "[[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]], [[04 - Architect System/BUILD-BACKLOG|BUILD-BACKLOG]], [[04 - Architect System/architect/04-Docs/SYSTEM-STATE-2026-07-05|SYSTEM-STATE]]"
---

# Reflexion §۷ روی MYCELIAL-MASTER-SPEC — نقدِ adversarial + ۳ diffِ پیشنهادی

> **این چیست؟** خروجیِ آیتمِ ۳ صفِ حلقهٔ خودکارِ `build-planner-loop`: اجرای پروتکلِ خودبهبودیِ خودِ spec (§۷ Reflexion / Evaluator-Optimizer) روی خودش. نقشِ Evaluator را برداشتم، spec را در برابرِ §۹ و [[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]] adversarial نقد کردم، و ۳ diffِ کم‌ریسک را به‌صورتِ **قبل→بعد** پیشنهاد می‌دهم.
>
> **فقط-پیشنهاد (propose-only).** هیچ‌چیز روی [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] اعمال نشده؛ خودِ spec دست‌نخورده است (طبق §۷ گام۳: «اعمال نکن»). منتظرِ verdictِ آری.
> منابع: spec v0.1 · [[04 - Architect System/BUILD-BACKLOG|BUILD-BACKLOG]] (DoD/تستِ M0–M8) · [[04 - Architect System/architect/04-Docs/SYSTEM-STATE-2026-07-05|SYSTEM-STATE]] (زمان‌بندِ زنده) · صف/لاگ: [[04 - Architect System/architect/04-Docs/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]].

## خلاصهٔ سریع (Quick Summary)

spec **سالم و منسجم است** (SDD درست، §۳ اتصالِ ۸ پروژه، §۵ ماشینِ حالتِ امن، §۷ حلقهٔ نقد). سه ضعفِ ساختاری با blast-radius بالا پیدا شد که **همگی حولِ یک محور**اند: *فاصله میان policyِ نوشته‌شده و enforcementِ واقعی*.

1. **W1 — تنها rollback (M5/بکاپ) در آخرین موج ساخته می‌شود** درحالی‌که vault خارج از git است و M5 پیش‌شرطِ سختِ delete هم هست → طیِ موج۱–۲ هیچ تورِ ایمنی نیست.
2. **W2 — گاردِ DELETE (§۵) فقط policy است، گیتِ تکنیکی ندارد** — EffectorGate فعلاً فقط `finalize`ِ runtimeِ fusion را می‌بندد، نه file-opsِ vault را.
3. **W3 — §۹#۶ «validatorها سبز» برای خودِ spec برقرار نمی‌شود** — این پوشه (`04 - Architect System/`) از دامنهٔ `validate_frontmatter.py` بیرون است؛ frontmatterِ ستون هرگز اعتبارسنجی نمی‌شود.

هر سه با diffِ **doc-only / کم‌ریسک** رفع می‌شوند (یک reorder + دو تبصره). رفعِ ریشه‌ایِ W2/W3 نیاز به تغییرِ کد/verdict دارد و به‌عنوان کارِ باز علامت خورده.

---

## الف) نقدِ adversarial — ۳ ضعفِ برتر (بر حسبِ blast-radius)

| # | ضعف | نقضِ چه چیزی | blast-radius | شدت |
|---|---|---|---|---|
| **W1** | M5 (بکاپِ off-box + restore) در **موج۳** است، ولی تنها rollbackِ vaultِ بدونِ git + پیش‌شرطِ delete | §۱ Risk-row۱ · §۵ DELETE·۴ · CHARTER «هیچ اقدامِ برگشت‌ناپذیر» | طیِ موج۱–۲ (M0–M4,M6) هر خطای پاک‌کننده/خرابیِ دیسک **بازگشت‌ناپذیر** است؛ سومِ «build/test/**delete**» تا انتها قفل می‌ماند | 🔴 بالا |
| **W2** | گاردِ DELETE §۵ متکی بر «`mv` نه `rm` + dry-run + verdict» است — **قاعدهٔ نوشته‌شده، نه choke-pointِ اجباری** | §۶ ادعای «EffectorGate = تنها دروازهٔ side-effect» vs §۳ «🟡 فقط finalize را می‌بندد» | یک ایجنت/buildِ باگ‌دار می‌تواند علی‌رغمِ قاعده `rm` بزند؛ خطرناک‌ترین عملیات ضعیف‌ترین enforcement را دارد | 🔴 بالا |
| **W3** | §۹#۶ «validatorها سبز» به‌عنوان معیارِ پذیرش، ولی `validate_frontmatter.py` پوشهٔ `04 - Architect System/` را چک نمی‌کند | §۹ DoD·۶ (self-referential) · §۱ هدفِ «ضدِّ drift» | frontmatterِ ستون (`canon_rank:1`) بی‌اعتبارسنجی می‌ماند → پوسیدگیِ بی‌صدای متادیتای منبعِ‌حقیقت (همان drift که spec قرار بود بکشد) | 🟡 متوسط‑بالا |

### شرحِ W1 — تورِ ایمنی آخر ساخته می‌شود
§۴ خودش M5 را «**پیش‌شرطِ delete §5**» برچسب زده و §۵ بند۴ می‌گوید تا M5 ساخته و restore-tested نشود delete فعال نمی‌شود — منطقِ درست. اما §۱۰ ترتیبِ ساخت را چنین قفل کرده: «موج۱ M0→M1→M2→M3 → موج۲ M4,M6 → **موج۳ M5**,M7,M8». یعنی تنها مکانیزمِ rollbackِ یک vaultِ **خارج از git** (که خودِ spec در §۱ Constraints و §۱۰ بند۲ تأکید می‌کند) در **آخرین** موج ساخته می‌شود. در [[04 - Architect System/BUILD-BACKLOG|BUILD-BACKLOG]]، M5 وابستگی‌اش «—» است (به هیچ‌چیز وابسته نیست) → هیچ دلیلِ فنی‌ای برای تأخیرش نیست. نتیجه: در کلِ موج۱–۲ اگر خطایی فایل‌های vault را از بین ببرد، بازیابی ممکن نیست؛ و قابلیتِ «delete» که یک‌سومِ عنوانِ سند است تا انتها در دسترس نیست.

> **پادسنجه (صادقانه):** M0–M3 در `fusion-mvp/` و MOCK‌اند و vault را دست نمی‌زنند، پس ریسکِ واقعیِ از‌بین‌رفتنِ vault در موج۱ کم است. ولی این «کم» متکی بر ایزولاسیونِ ضمنی است، نه تضمینِ صریح؛ و برهانِ «تورِ ایمنی را اول بساز» مستقل از آن برقرار است.

### شرحِ W2 — گاردِ delete اجرایی نیست، فقط قاعده است
§۵ DELETE چهار مهار دارد: (۱) هرگز hard-delete، `mv` به `_Duplicates`؛ (۲) dry-run manifest؛ (۳) verdictِ انسانی؛ (۴) پیش‌شرطِ M5. اما هر چهار مهار **policy**‌اند. §۶ ادعا می‌کند «EffectorGate = تنها دروازهٔ side-effect؛ هر `ToolGateway.call` permit می‌گیرد» — ولی جدولِ §۳ خودش وضعیتش را «🟡 فقط `finalize` را می‌بندد (G-10)» ثبت کرده. مهم‌تر: در [[04 - Architect System/BUILD-BACKLOG|BUILD-BACKLOG]] دامنهٔ M2 (EffectorGateِ یکپارچه) = `fusion-mvp/orchestrator.py`+`tools.py` است، یعنی tool-callهای **runtimeِ fusion** — نه `rm`/`mv`ای که ایجنت‌های فایل‌مدیریتی (همین Cowork/Claude) روی vault می‌زنند. پس حتی بعد از M2 هم، حذفِ فایلِ vault هرگز از EffectorGate عبور نمی‌کند. خطرناک‌ترین عملیاتِ سیستم، تنها با «قولِ» ایجنت مهار می‌شود.

### شرحِ W3 — معیارِ پذیرشی که روی خودِ سند اجرا نمی‌شود
§۹ بند۶ «validatorها سبز» را جزوِ DoDِ خودِ spec آورده. ولی `validate_frontmatter.py` (خط ۲۰–۳۳) تابعِ `in_scope` دارد که فقط `SYSTEM_FOLDERS = {00 - Inbox, 01 - Dashboard, 02 - Life OS, 05 - Agents, 06 - Architecture Maps, 09 - People, 10 - Telegram processing}` + ریشه + هر `PROJECT.md` + سطحِ‌بالای `03/07` را می‌پذیرد. **`04 - Architect System` در این فهرست نیست** → `in_scope(MYCELIAL-MASTER-SPEC.md)` = `False`. یعنی `type/status/version/canon_rank/salience/...`ِ ستون هرگز اعتبارسنجی نمی‌شود. نامتقارنی: `find_broken_links.py` این پوشه را **می‌پوشد** (فقط `_Archive/_Duplicates/.git/.claude/_code` را حذف می‌کند)، پس wikilinkِ شکسته گرفته می‌شود ولی frontmatterِ خراب نه. برای سندی با `canon_rank:1` که قرار است ضدِّ drift باشد، این نقطه‌کورِ خودارجاع است.

---

## ب) سه diffِ پیشنهادی (قبل→بعد) — **اعمال‌نشده**

### Diff-1 (W1): M5 را به «موج۰» جلو بیاور
**فایل/بخش:** §۱۰ خطِ ترتیبِ ساخت + سلولِ «موج»ِ M5 در جدولِ §۴.

**§۱۰ — قبل:**
> **Fable 5 می‌سازد (به‌ترتیب):** موج۱ M0→M1→M2→M3 (fusion، کم‌ریسک) → موج۲ M4,M6 (بدنهٔ langar) → موج۳ M5,M7,M8.

**§۱۰ — بعد:**
> **Fable 5 می‌سازد (به‌ترتیب):** **موج۰ = M5 (بکاپِ off-box + restore)** — تورِ ایمنیِ کلِ ساخت، چون vault خارج از git است و M5 پیش‌شرطِ delete هم هست (§۵·۴)؛ وابستگی‌اش «—» پس بدونِ بلاکر ساختنی‌ست → موج۱ M0→M1→M2→M3 (fusion، کم‌ریسک) → موج۲ M4,M6 → موج۳ M7,M8.

**§۴ جدول، ردیفِ M5، ستونِ «موج» — قبل:** `۳ (پیش‌شرطِ delete §5)`
**بعد:** `۰ (تورِ ایمنیِ کلِ ساخت + پیش‌شرطِ delete §5)`

*منطق:* هزینهٔ صفر (M5 بی‌وابستگی)، ریسک‌کاهیِ زیاد. اگر آری ترجیح دهد ترتیبِ fusion دست‌نخورده بماند، جایگزینِ کم‌هزینه‌تر: یک جملهٔ صریح در §۵ که «تا M5، هر build در sandboxِ ایزوله که فایل‌سیستمِ vault را لمس نمی‌کند اجرا شود».

### Diff-2 (W2): شکافِ enforcement را صریح کن + delete را «دست‌انسانی» نگه دار
**فایل/بخش:** §۵ DELETE (افزودنِ بند۵) + پانویسِ §۶ Tool design.

**§۵ DELETE — بعد از بند۴، بند۵ اضافه شود:**
> 5. **گیتِ تکنیکی هنوز نیست → پس دست‌انسانی.** EffectorGate فعلاً فقط `finalize`ِ runtimeِ fusion را می‌بندد (§۳: 🟡 G-10) و دامنهٔ M2 هم همان fusion است، نه file-opsِ vault. تا وقتی یک choke-pointِ واقعیِ فایل‌سیستم ساخته نشده، **هیچ ایجنتی خودش `mv`/`rm` را اجرا نمی‌کند**؛ فقط dry-run manifest پیشنهاد می‌دهد و اجرا با دستِ آری است. (این شکاف را صریح ثبت می‌کنیم تا «قاعده» با «تصورِ گیتِ فعال» اشتباه نشود.)

**§۶ Tool design — قبل:**
> **Tool design.** EffectorGate = تنها دروازهٔ side-effect؛ هر `ToolGateway.call` قبل از اجرا permit می‌گیرد و مصرف می‌کند (fail-closed)؛ آداپترهای MOCK برای تست بی‌کلید.

**§۶ Tool design — بعد:** (همان متن +) 
> …آداپترهای MOCK برای تست بی‌کلید. **دامنهٔ فعلیِ این دروازه = tool-callهای runtimeِ fusion؛ file-opsِ vault (`mv`/`rm`) هنوز خارج از آن‌اند — تا ساختِ گیتِ فایل‌سیستم، طبقِ §۵ بند۵ دست‌انسانی می‌مانند.**

*منطق:* diff فقط واقعیت را صریح می‌کند (بی‌ریسک)؛ رفعِ ریشه‌ای = گسترشِ EffectorGate به file-ops یا یک M نو «fs-effector-gate» → **کارِ باز، پشتِ verdict + کد**.

### Diff-3 (W3): تبصرهٔ دامنهٔ validator در §۹
**فایل/بخش:** §۹ معیارهای پذیرش، بند۶.

**§۹#۶ — قبل:** `(۶) validatorها سبز.`
**بعد:**
> (۶) validatorها سبز — **با تبصره:** این سند در `04 - Architect System/` است و `validate_frontmatter.py` این پوشه را چک نمی‌کند (`SYSTEM_FOLDERS` شاملش نیست)؛ پس frontmatterِ خودِ spec **خودکار اعتبارسنجی نمی‌شود** و فقط `find_broken_links.py` پوشش می‌دهد. بنابراین هر عبورِ §۷ باید یک چکِ **دستیِ** frontmatter + resolveِ wikilink انجام دهد. *(رفعِ ریشه‌ای = افزودنِ «04 - Architect System» به `SYSTEM_FOLDERS` — تغییرِ اسکریپت، پشتِ verdict.)*

*منطق:* بدونِ این تبصره، §۹#۶ یک تضمینِ کاذب است. diff صادقانه‌اش می‌کند و بارِ verify را به حلقهٔ §۷ می‌سپارد تا رفعِ کدْ verdict بگیرد.

---

## ج) ممیزیِ biomimicry [G]/[J] (طبقِ §۰.۴ و §۷ گام۳)

**جدولِ §۲ تمیز است:** ۸ ردیف، همه برچسب‌دار — ۱×**[G]** (Physarum γ-knob → مسیریابیِ تطبیقیِ توجه/بودجه؛ واقعاً مولّد است، یک الگوریتمِ قابلِ‌پیاده‌سازی) و ۷×**[J]** (نگاشت‌های یادیار). این دقیقاً چیزی‌ست که §۰.۴ می‌خواهد.

**اما چند استعارهٔ prose خارج از جدول بی‌برچسب مانده‌اند** (طبقِ §۰.۴ «اگر مکانیزم ندارد حذفش کن» یا برچسب بخورد):
- §۴ عنوان «زنده‌کردنِ دست‌وپای **فرانکنشتاین**» — استعارهٔ ادبی، بی‌مکانیزم، بی‌برچسب. پیشنهاد: یا [J] (یادیارِ «اندام‌های ناقصِ ازپیش‌موجود») یا ساده‌سازی به «تکمیلِ ماژول‌های نیمه‌ساخته».
- header/§۰ «**داربستِ بامبو**» و §۲ «the organism» — تزئینی. پیشنهاد: [J] یا حذف.

*شدت 🟢 پایین* (زیبایی‌شناختی)، ولی چون §۷ صریحاً این ممیزی را می‌خواهد و §۱ خودش «biomimicry-as-decoration» را ریسک شمرده، یک پاسِ سبکِ برچسب‌زنی توصیه می‌شود. **این را جزوِ ۳ diffِ اصلی نیاوردم** (blast-radius پایین)؛ اگر آری بخواهد، Diff-4 آماده می‌شود.

---

## د) drift با زمان‌بندِ زنده (طبقِ §۷ گام۴؛ منبع: [[04 - Architect System/architect/04-Docs/SYSTEM-STATE-2026-07-05|SYSTEM-STATE]] ~۱۲:۵۴ AEST)

- **D1 — §۳ رجیستریِ اتصال «همهٔ اندام‌ها را نمی‌شناسد».** §۳ خود را «اتصالِ رسمی» می‌نامد، ولی SYSTEM-STATE در زمان‌بندِ زنده **۳۴ enabled** یافت که دستِ‌کم ۵ تسکِ فعال در §۳ **غایب**اند: `ai-eng-radar-brief` · `ai-eng-week-in-review` · `research-radar-curator` (ناوگانِ Research Radar) + `survival-heartbeat` + `bio-synthesis-daily`. منبعِ‌حقیقتی که همه‌چیز را نمی‌شمارد، همان drift را می‌سازد که قرار بود بکشد. *(پیشنهاد: یک ردیفِ «اندام‌های مشاهده‌شده در زمان‌بند اما بی‌رجیستری» به §۳ افزوده شود — کارِ آیتمِ ۷ REVIEW-PACKET.)*
- **D2 — وضعیت‌های ✅/🟡 در §۳ بی‌تاریخ‌اند.** «Scout Fleet ✅ زنده»، «Kill-switch ✅»، «EffectorGate 🟡» هیچ‌کدام مُهرِ «verified-against-live on <date>» ندارند → بی‌صدا کهنه می‌شوند (تشدیدِ W3). پیشنهاد: ستونِ «آخرین verify (تاریخ/منبع)».
- **D3 — روایتِ «۶ هسته زنده / ۲۶ تاریک» وارونه است.** SYSTEM-STATE (خط ۲۳) نشان داد آن ۲۶ «تاریک» در واقع **enabled**‌اند و ۳ تا از ۶ هسته اصلاً در زمان‌بند نیستند. §۳ خودش این framing را تکرار نمی‌کند ولی §۱۰ بند۵ به «verdictهای بازِ SYSTEM-STATE §۵» ارجاع می‌دهد؛ خوب است این آشتی در خودِ §۳ سطحی‌شود تا خوانندهٔ §۳-تنها مدلِ ذهنیِ کهنه نگیرد.
- **D4 (جزئی) — ستونِ «بات (propose-only)» در §۳** نام‌هایی مثل `crypto-watcher`/`accounting-clerk` دارد که با نامِ تسک‌های زندهٔ زمان‌بند (`crypto`, `accounting` scouts) یکی نیستند → «نیتِ طراحی»‌اند نه ایجنتِ زنده؛ یک تبصرهٔ «planned vs live» کافی‌ست.

> **نکتهٔ روش‌شناختیِ حینِ اجرا (ثبت برای آری):** در همین اجرا، مِنتِ سندباکس **stale** بود (ledger سمتِ سندباکس ۵۰ خط با یک بایتِ ناقصِ `d8` در انتها؛ ویندوز ۵۵ خطِ کامل و سالم). طبقِ قاعدهٔ fresh-inode، همهٔ خواندن/نوشتنِ این اجرا **Windows-side** انجام شد. تأییدِ دوبارهٔ کلاسِ stale-view (ردیف‌های ۲۷/۵۳/۵۵ ledger).

---

## ه) جمع‌بندی، changelog، و گام بعد

**changelogِ پیشنهادی (اعمال‌نشده — بخشی از diff، با verdict اجرا شود):** ردیفِ §۱۱ از v0.1 → **v0.2** با شرحِ «Diff-1..3: reorder M5 به موج۰ · تبصرهٔ enforcementِ delete · تبصرهٔ دامنهٔ validator». `version:` frontmatter هم v0.1→v0.2. *(چون spec دست‌نخورده می‌ماند، این هم پیشنهاد است.)*

**Trade-off (چرا doc-only اول):** هر ۳ diff صفر خطِ کد را تغییر نمی‌دهند (reorder + دو تبصره) → Cost ۱/۱۰، Risk ۱/۱۰، ارزشِ ضدِّdrift و ضدِّ data-loss بالا. رفعِ ریشه‌ایِ W2 (گیتِ fs) و W3 (دامنهٔ validator) کدی‌اند و عمداً به کارِ باز/verdict موکول شدند.

**Next Steps (برای آری):**
1. verdict روی Diff-1 (reorder M5) — کم‌هزینه‌ترین، بیش‌ترین اثر.
2. verdict روی Diff-2/3 (دو تبصره) + آیا رفعِ ریشه‌ای (گیتِ fs · افزودنِ ۰۴ به validator) به BUILD-BACKLOG به‌عنوان M نو اضافه شود؟
3. اگر تأیید شد، این diffها + version-bump در یک جلسهٔ تعاملی روی spec اعمال و §۱۱ آپدیت شود.
4. D1/D3 → ورودیِ آیتمِ ۷ صف (REVIEW-PACKET).

---

> **پایان — propose-only.** خودِ [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] لمس نشده. هیچ‌چیزِ canonical/charter/کد/تسک بدونِ verdictِ آری تغییر نمی‌کند. یک خط برای ledger در [[04 - Architect System/architect/04-Docs/AUTONOMOUS-RUN-2026-07-05|صف/لاگ]] ثبت شد.
