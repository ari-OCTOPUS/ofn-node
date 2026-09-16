---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[03 - Projects/اونلی فنز/PROJECT]]"
  - "[[03 - Projects/اونلی فنز/AGENT-CONTROL-INTERFACE]]"
tags: [project-f, opsec, refactor, studio, identifiers, privacy]
aliases: ["PROP-D4 Identifier Rename", "Creator-Name OpSec Refactor", "PF-CODE-REFACTOR-V1 proposal"]
---

# PROP-D4 — حذفِ نامِ سازنده از شناسه‌های سورس (OpSec)

> **وضعیت: PROPOSAL (idea).** هیچ‌چیز اینجا اجرا نمی‌شود. PLAN ≠ APPROVAL ≠ EXECUTION.
> این سند مستقیماً به وردیکتِ **PF-CODE-REFACTOR-V1** نگاشت می‌شود و منتظرِ رأیِ مالک است.
> کلِ متن با نام‌ها **ماسک‌شده** است؛ نامِ واقعیِ سازنده هیچ‌جا نوشته نشده.

## خلاصهٔ مدیریتی
[FACT] نامِ کوچکِ سازنده به‌صورتِ ریشهٔ ترانویسی‌شده در **نامِ فایل‌ها، نامِ کلاس، پارامترها، صفاتِ آبجکت، دو env-var، نامِ فایل‌های handoffِ زمان‌اجرا، دو نوعِ پیام (`kind`)، یک متدِ پل، یک دستورِ تلگرام و یک برچسبِ route** پخش است — در ۶ فایلِ کد + مانيفست + ۴ سند/رانبوک + چند نوتِ ناوبری.
[FACT] کاکپیت با یک **کدنیمِ خنثی** («langar» = لنگر/anchor) نام‌گذاری شده و نشتی ندارد؛ اما لایهٔ استودیو ریشهٔ نامِ سازنده (که با `<C>` ماسک می‌کنیم) و لایهٔ اعلان‌ها ریشهٔ نامِ اپراتور (`<A>`) را حمل می‌کنند. **این عدم‌تقارن، دقیقاً همان چیزی است که باید صاف شود.**
[EST] بلاست‌رِیدیوسِ ریفکتور کوچک و مهارشدنی است: ماژولِ نام‌دار فقط **یک** ایمپورتر دارد (`test_<C>_studio.py`)؛ ولی سه «قراردادِ رشته‌ایِ بین‌ماژولی» وجود دارد که producer و consumer باید **اتمیک با هم** عوض شوند، وگرنه wiring می‌شکند.

### لِجندِ ماسک
| نماد | یعنی | نمونهٔ ماسک‌شده |
|---|---|---|
| `<C>` | ریشهٔ نامِ کوچکِ **سازنده** (هم ترانویسیِ لاتین در شناسه‌ها، هم شکلِ فارسی در متن) | `<C>_studio.py`, `class <C>Studio`, `TELEGRAM_<C>_BOT_TOKEN` |
| `<A>` | ریشهٔ نامِ کوچکِ **اپراتور** | `to_<A>.json`, `report_<A>`, `TELEGRAM_<A>_CHAT_ID` |
| «neutral» | خنثی — دست‌نخورده می‌ماند | `langar`, `octopus-studio`, `content_studio`, `ContentStudio` |

> نکته: `config.json` (studio) و `orchestrator.py` **هیچ شناسهٔ نام‌داری ندارند** — بازبینی شد و پاک‌اند؛ در اینونتوری نمی‌آیند مگر به‌عنوان ایمپورتر (orchestrator فقط `content_studioِ` خنثی را ایمپورت می‌کند).

---

## PMO — Current / Delta / Preserved / Rollback (سطحِ کلان)

**Current**
- ریشهٔ نامِ سازنده (`<C>`) در ≥ ۷۰ نقطهٔ سورس؛ ریشهٔ نامِ اپراتور (`<A>`) در ≥ ۱۲ نقطه.
- ۴ فایلِ سورس نامشان نام‌دار است: `studio/<C>_studio.py`, `studio/test_<C>_studio.py`, `studio/<C>-STUDIO-SPEC.md`, `studio/README-<C>-RUNBOOK.md`.
- دو env-var پروداکشن نام‌دارند: `TELEGRAM_<C>_BOT_TOKEN`, `TELEGRAM_<C>_CHAT_ID` (+ اپراتور: `TELEGRAM_<A>_CHAT_ID`).
- دو فایلِ handoffِ زمان‌اجرا نام‌دارند: `for_<C>.json` (به سازنده), `to_<A>.json` (به اپراتور).

**Delta (پیشنهادی)**
- همهٔ شناسه‌های `<C>` → ریشهٔ خنثی `creator` (فایل/کلاس/پارامتر/صفت/env/kind/route/دستور).
- همهٔ شناسه‌های `<A>` → ریشهٔ خنثی `operator` (به‌شدت توصیه می‌شود در همان کامیتِ اتمیک؛ بلاست‌رِیدیوسِ مشترک).
- کدنیمِ `langar`، UAِ `octopus-studio`، و `content_studio`/`ContentStudio` **بدونِ تغییر** (خنثی‌اند).

**Preserved (تضمینِ عدمِ تغییرِ رفتار)**
- منطقِ auth/allowlist، دوکلیده، halt/boundary، fail-closed، صفر-رسانه — **بیت‌به‌بیت یکسان**. این ریفکتور صرفاً rename است، نه تغییرِ رفتار.
- callbackهای UI (`s:*`, `m:*`, `studio:*`)، شناسه‌های `DRAFT-XXXX`، و فایل‌های خنثیِ داده (`drafts.json`, `config.json`, `capacity.json`, `boundary_log.json`, `HALT`) دست‌نخورده.
- ترتیب/امضای متدهای عمومیِ منطق (`submit_draft`, `route`, `poll_once`) حفظ می‌شود؛ فقط توکنِ نام عوض می‌شود.

**Rollback**
- کلِ ریفکتور **یک‌کامیتی و یک‌فرمانه برگشت‌پذیر** طراحی شده: یک `agent-checkpoint:` قبل، `git mv` برای فایل‌ها (حفظِ history)، و `git revert`/`git reset --hard <checkpoint>` برای بازگشتِ کامل.
- برای env: fallbackِ زمان‌بندی‌شده (پایین §D5) اجازه می‌دهد نبودِ به‌روزرسانیِ env توسطِ مالک، **fail-soft** شود نه fail-closed.

---

## Deliverable 1 — اینونتوریِ کاملِ شناسه‌های نام‌دار (ماسک‌شده)

### گروهِ C — نامِ سازنده (in-scope مستقیمِ PF-CODE-REFACTOR-V1)

| # | شناسهٔ فعلی (ماسک‌شده) | نوع | file:line |
|---|---|---|---|
| C-1 | `<C>_studio.py` | نامِ فایلِ ماژول | `studio/<C>_studio.py` (خودِ فایل)؛ docstring `:2`؛ `__main__` `:443–444` |
| C-2 | `class <C>Studio` | نامِ کلاس | `studio/<C>_studio.py:80`, `:105` (repr `<<C>Studio …>`), `:444`؛ `studio/test_<C>_studio.py:36` (`S.<C>Studio(...)`) |
| C-3 | `import <C>_studio as S` | ایمپورتِ ماژول | `studio/test_<C>_studio.py:9` |
| C-4 | `TELEGRAM_<C>_BOT_TOKEN` | env-var | `studio/<C>_studio.py:88`, `:413`؛ `studio/studio_telegram.py:15`, `:90`؛ `studio/studio_telegram_v3.py:65`؛ `PROJECT-F-CONTROL-MANIFEST.json:153`؛ `studio/README-<C>-RUNBOOK.md:30`؛ `studio/<C>-STUDIO-SPEC.md:49` |
| C-5 | `TELEGRAM_<C>_CHAT_ID` | env-var | `studio/<C>_studio.py:89`, `:413`؛ `studio/studio_telegram.py:92`؛ `studio/studio_telegram_v3.py:66`؛ `PROJECT-F-CONTROL-MANIFEST.json:154`؛ `studio/README-<C>-RUNBOOK.md:31`؛ `studio/<C>-STUDIO-SPEC.md:49` |
| C-6 | `<C>_chat_id` | پارامترِ `__init__` | `studio/<C>_studio.py:85`, `:89`؛ `studio/studio_telegram.py:87`, `:91`؛ `studio/studio_telegram_v3.py:61`, `:66` |
| C-7 | `self.<C>` / `self._<C>` | صفتِ آبجکت | `studio/<C>_studio.py:90,102,107,111,416` (`self.<C>`)؛ `studio/studio_telegram.py:91,104,108,135,219` (`self._<C>`)؛ `studio/studio_telegram_v3.py:66,78,79,92,179` (`self._<C>`) |
| C-8 | `name = "<C>-studio"` | شناسهٔ نامِ کامپوننت | `studio/<C>_studio.py:83` |
| C-9 | `"<C>-studio/1.0"` | رشتهٔ User-Agent | `studio/<C>_studio.py:71`, `:76` (توجه: `studio_telegram*.py` از `octopus-studio/0.1`ِ خنثی استفاده می‌کنند) |
| C-10 | `<C>=` در repr | برچسبِ دیباگ | `studio/studio_telegram.py:108`؛ `studio/studio_telegram_v3.py:79` (`f"… <C>={self._<C>} …"`) |
| C-11 | `for_<C>.json` | فایلِ handoff (اپراتور→سازنده) | consumer `studio/<C>_studio.py:28`؛ `studio/test_<C>_studio.py:19`؛ `PROJECT-F-CONTROL-MANIFEST.json:115`؛ `studio/<C>-STUDIO-SPEC.md:20,27`؛ `studio/README-<C>-RUNBOOK.md:39`؛ `AGENT-CONTROL-INTERFACE.md:67` (producer = مسیرِ `/report`ِ اپراتور، manifest `:97` — دستی، producerِ کد در langar یافت نشد) |
| C-12 | `<C>_bridge` (متد) | پلِ کاکپیت→سازنده | `langar/langar_bot.py:182` (def), `:331`, `:346` (فراخوان) |
| C-13 | `"<C>_halted"` (کلید) | کلیدِ dict | `langar/langar_bot.py:192` (نوشتن), `:333`, `:347` (خواندن) |
| C-14 | `/<C>` (دستورِ تلگرام) | فرمانِ کاکپیت | `langar/langar_bot.py:321` (help), `:345` (`if cmd in ("/<C>","/drafts")`)؛ `PROJECT-F-CONTROL-MANIFEST.json:91`, `:92` (`"alias of /<C>"`) |
| C-15 | `kind="brief_<C>"` | نوعِ پیام (قراردادِ رشته‌ای) | producer: `brain/dual_brain.py:256`؛ `brain/dual_brain_v3.py:336`؛ **consumer: `studio/studio_telegram_v3.py:159`** (`m["kind"] == "brief_<C>"`)؛ کامنت `dual_brain.py:40`, `dual_brain_v3.py:17` |
| C-16 | `brief_for_<C>` (متد) | متدِ کامیونیکیتور | `brain/dual_brain.py:236` (def), `:313` (call)؛ `brain/dual_brain_v3.py:305` (def), `:410` (call) |
| C-17 | `"route": "<C>"` | برچسبِ مسیریابی | `brain/project_f_brain.py:206` |
| C-18 | `<C>-STUDIO-SPEC.md` | نامِ فایلِ spec | خودِ فایل؛ ارجاع: `PROJECT-F-CONTROL-MANIFEST.json:185`؛ `INDEX.md:37,55`؛ `LANGAR-SPEC.md:44`؛ `BASE-DATA-REPORT-2026-07-12.md:285,450,735`؛ `00 - Control/SOURCE-OF-TRUTH-MATRIX.md:66`؛ frontmatter tag/alias داخلِ خودِ spec `:8,:9` |
| C-19 | `README-<C>-RUNBOOK.md` | نامِ فایلِ رانبوک | خودِ فایل؛ ارجاع: `PROJECT-F-CONTROL-MANIFEST.json:185`؛ `INDEX.md:37,55`؛ `<C>-STUDIO-SPEC.md:49`؛ frontmatter `up:` داخلِ خودِ رانبوک `:5` |
| C-20 | `test_<C>_studio.py` | نامِ فایلِ تست | خودِ فایل؛ ارجاع: `PROJECT-F-CONTROL-MANIFEST.json:170`؛ `<C>-STUDIO-SPEC.md:45`؛ `README-<C>-RUNBOOK.md:16`؛ `AGENT-CONTROL-INTERFACE.md:94`؛ `BASE-DATA-REPORT-2026-07-12.md:769` |
| C-21 | ارجاع به `studio/<C>_studio.py` در اسناد | مسیرِ entrypoint در مستندات | `PROJECT-F-CONTROL-MANIFEST.json:65,106,148`؛ `README-<C>-RUNBOOK.md:21,32`؛ `<C>-STUDIO-SPEC.md:18`؛ `AGENT-CONTROL-INTERFACE.md:25,96`؛ `INDEX.md:37`؛ `00 - Control/CARTOGRAPHY-2026-07-12.md:45`؛ `00 - Control/SOURCE-OF-TRUTH-MATRIX.md:66`؛ `BASE-DATA-REPORT-2026-07-12.md:661`؛ `04 - Content Studio/_INDEX.md:3` |

### گروهِ A — نامِ اپراتور (adjacent؛ همان بلاست‌رِیدیوس)

| # | شناسهٔ فعلی (ماسک‌شده) | نوع | file:line |
|---|---|---|---|
| A-1 | `to_<A>.json` | فایلِ handoff (سازنده→اپراتور) | producer `studio/<C>_studio.py:341–343` (متدِ `_to_<A>`), فراخوان‌ها `:317,:358,:364`؛ **consumer `langar/langar_bot.py:188`**؛ test `studio/test_<C>_studio.py:24,59,111`؛ `PROJECT-F-CONTROL-MANIFEST.json:114`؛ `<C>-STUDIO-SPEC.md:22,26`؛ `README-<C>-RUNBOOK.md:38`؛ `AGENT-CONTROL-INTERFACE.md:55` |
| A-2 | `_to_<A>` (متد) | متدِ اعلان | `studio/<C>_studio.py:317,341,358,364` |
| A-3 | `kind="report_<A>"` | نوعِ پیام | `brain/dual_brain.py:40,272`؛ `brain/dual_brain_v3.py:17,353` |
| A-4 | `TELEGRAM_<A>_CHAT_ID` | env-var | `langar/langar_bot.py:257,456`؛ `PROJECT-F-CONTROL-MANIFEST.json:152`؛ `langar/README-RUNBOOK.md:31` |

### گروهِ P2 — نامِ خام در متن/کامنت/frontmatter (نه شناسه؛ پاس‌سازیِ ثانویه)
[FACT] شکلِ فارسیِ نامِ سازنده در docstring/کامنتِ سورس: `studio/<C>_studio.py` (پرتکرار)، `studio/content_studio.py:2–4,69`، `studio/studio_telegram.py:2,4,8,82`، `studio/studio_telegram_v3.py:1,57,138`، و `brain/dual_brain.py:146` («check-in with `<C>`»). به‌علاوه frontmatterِ spec: tag `<C>` (`:8`) و aliasها «`<C>` Studio»/«استودیوی `<C>`» (`:9`).
[FACT] یک فایلِ داده در ریشهٔ پروژه نامش نامِ سازنده را حمل می‌کند: `پرسشنامه پارتنر - پاسخ‌های <C>.md` (سند PII — خارج از «شناسهٔ سورس»؛ در §Caveats پرچم شد).

---

## Deliverable 2 — جایگزین‌های خنثیِ پیشنهادی

| از (ماسک‌شده) | به (خنثی) | یادداشت |
|---|---|---|
| فایل `<C>_studio.py` | `creator_studio.py` | با `git mv` (حفظِ history) |
| کلاس `<C>Studio` | `CreatorStudio` | |
| فایل `test_<C>_studio.py` | `test_creator_studio.py` | + سطرِ ایمپورت `import creator_studio as S` |
| env `TELEGRAM_<C>_BOT_TOKEN` | `TELEGRAM_CREATOR_BOT_TOKEN` | **اکشنِ مالک** (پایین §D5) |
| env `TELEGRAM_<C>_CHAT_ID` | `TELEGRAM_CREATOR_CHAT_ID` | **اکشنِ مالک** |
| param `<C>_chat_id` | `creator_chat_id` | |
| صفت `self.<C>` / `self._<C>` | `self.creator` / `self._creator` | ویزیبیلیتی حفظ می‌شود |
| `name="<C>-studio"` | `name="creator-studio"` | |
| UA `"<C>-studio/1.0"` | `"creator-studio/1.0"` | یا هم‌ترازِ `octopus-studio` |
| repr `<C>=…` | `creator=…` | فقط برچسبِ دیباگ |
| فایل `for_<C>.json` | `for_creator.json` | قراردادِ handoff (پایین §D3) |
| متد `<C>_bridge` | `creator_bridge` | داخلِ langar، خودبسنده |
| کلید `"<C>_halted"` | `"creator_halted"` | داخلِ langar، خودبسنده |
| دستور `/<C>` | `/studio` (یا `/creator`) | اپراتور-فِیسینگ؛ `/<C>` را یک ریلیز به‌عنوانِ aliasِ مخفی نگه دار |
| kind `"brief_<C>"` | `"brief_creator"` | producer+consumer اتمیک |
| متد `brief_for_<C>` | `brief_for_creator` | |
| route `"<C>"` | `"creator"` | |
| spec `<C>-STUDIO-SPEC.md` | `CREATOR-STUDIO-SPEC.md` | + به‌روزرسانیِ wikilinkها |
| runbook `README-<C>-RUNBOOK.md` | `README-CREATOR-RUNBOOK.md` | + wikilinkها |
| — گروهِ A (توصیه‌شدهٔ هم‌زمان) — | | |
| فایل `to_<A>.json` | `to_operator.json` | producer+consumer اتمیک |
| متد `_to_<A>` | `_to_operator` | |
| kind `"report_<A>"` | `"report_operator"` | |
| env `TELEGRAM_<A>_CHAT_ID` | `TELEGRAM_OPERATOR_CHAT_ID` | **اکشنِ مالک** |
| — بدونِ تغییر (خنثی) — | | |
| `langar`, `TELEGRAM_LANGAR_BOT_TOKEN` | (بماند) | «langar» کدنیمِ خنثی است، نه نام |
| `content_studio` / `ContentStudio` | (بماند) | از قبل خنثی |
| `octopus-studio/0.1` | (بماند) | از قبل خنثی |

---

## Deliverable 3 — بلاست‌رِیدیوس (چه چیزهایی باید با هم عوض شوند)

**۱) ایمپورترِ ماژول (کوچک):** ماژولِ `<C>_studio` فقط **یک** ایمپورتر دارد — `studio/test_<C>_studio.py:9`. [FACT] `orchestrator.py`، `langar_bot.py` و `studio_telegram*.py` این ماژول را ایمپورت **نمی‌کنند** (فقط `content_studioِ` خنثی را). پس rename فایل، مستقیماً فقط تست + entrypointهای مستند را می‌شکند.

**۲) قراردادهای رشته‌ایِ بین‌ماژولی (پرریسک — باید اتمیک):**
- `to_<A>.json`: producer `studio/<C>_studio.py:343` ↔ consumer `langar/langar_bot.py:188`. اگر فقط یک‌طرف عوض شود، اعلان‌های سازنده به کاکپیت **بی‌صدا قطع** می‌شود.
- `brief_<C>` (kind): producer `dual_brain.py:256`/`dual_brain_v3.py:336` ↔ consumer `studio_telegram_v3.py:159`. عدمِ هماهنگی = بریفِ هفته دیگر رندر نمی‌شود.
- `for_<C>.json`: consumer `studio/<C>_studio.py:28` ↔ producer = مسیرِ `/report`ِ اپراتور (manifest `:97`). چون producer دستی است، migrationِ فایلِ زندهٔ روی دیسک لازم است (بند بعد).

**۳) فایل‌های زندهٔ زمان‌اجرا (migration):** اگر ربات‌ها قبلاً اجرا شده باشند، ممکن است `to_<A>.json` / `for_<C>.json` روی دیسک وجود داشته باشند (صفِ pendingِ اعلان‌ها/inbox). rename باید فایلِ دادهٔ موجود را هم منتقل کند، وگرنه آیتم‌های در صف **یتیم** می‌شوند. [EST] در فازِ فعلی «zero execution» (manifest `status_snapshot`)، احتمالاً این فایل‌ها هنوز خالی/غایب‌اند — اما اسکریپتِ rollout باید idempotent باشد و «اگر موجود بود منتقل کن».

**۴) مانيفستِ کنترل (`PROJECT-F-CONTROL-MANIFEST.json`):** کلیدها/مقادیرِ زیر باید هم‌زمان عوض شوند: `:65, :91, :92, :106, :114, :115, :148, :152, :153, :154, :170, :185`.

**۵) اسناد/رانبوک/MOC (شکستنِ wikilink):** rename فایل‌های `.md` باعثِ **broken link** می‌شود. باید در همان بَچ به‌روز شوند:
- wikilinkها به spec/runbook: `INDEX.md:37,55`؛ `LANGAR-SPEC.md:44`؛ frontmatter `up:` در `README-<C>-RUNBOOK.md:5`؛ alias «`<C>` Studio» در `<C>-STUDIO-SPEC.md:9`.
- ارجاع‌های مسیر/نام در: `AGENT-CONTROL-INTERFACE.md:25,55,67,94,96`؛ `00 - Control/CARTOGRAPHY-2026-07-12.md:45`؛ `00 - Control/SOURCE-OF-TRUTH-MATRIX.md:66`؛ `BASE-DATA-REPORT-2026-07-12.md:285,450,661,735,769`؛ `04 - Content Studio/_INDEX.md:3`؛ `langar/README-RUNBOOK.md:31` (env `<A>`).

**۶) بایت‌کدِ کهنه:** `studio/__pycache__/*<C>_studio*.pyc` و `__pycache__` ریشه پس از rename بی‌اعتبارند؛ باید پاک شوند تا importِ گمراه‌کننده رخ ندهد (regenerate خودکار است).

---

## Deliverable 4 — ترتیبِ امنِ rollout + rollback

> همه به‌صورتِ **پیشنهاد**. اجرای واقعی منوط به رأیِ PF-CODE-REFACTOR-V1 است.

**ترتیبِ پیشنهادی (rename → fix imports → update manifest+specs → tests → commit):**
1. **Checkpoint.** یک کامیتِ `agent-checkpoint: pre PF-CODE-REFACTOR-V1` روی درختِ تمیز (طبق قانونِ «قبل از بَچِ >۵ فایل»). این نقطهٔ برگشتِ یک‌فرمانه است.
2. **Rename فایل‌ها با `git mv`** (حفظِ history): `<C>_studio.py`, `test_<C>_studio.py`, `<C>-STUDIO-SPEC.md`, `README-<C>-RUNBOOK.md` → نام‌های `creator*`.
3. **اصلاحِ شناسه‌های درون‌کد** در ۶ فایل: کلاس، پارامتر، صفت، `name`, UA, repr، متدها، routeها — و **قراردادهای رشته‌ای (`to_<A>.json`, `for_<C>.json`, `brief_<C>`, `report_<A>`) را producer+consumer در همین کامیت** تا هرگز واگرا نشوند.
4. **rename فایل‌های handoff** در producer+consumer + یک migrationِ یک‌بارهٔ idempotent برای فایل‌های زندهٔ احتمالی.
5. **env-varها:** نامِ جدید در کد + fallbackِ زمان‌بندی‌شده (§D5)؛ به‌روزرسانیِ محیط = **اکشنِ مالک**.
6. **مانيفست + همهٔ specs/runbooks/MOC/INDEX** به‌روز؛ wikilinkهای شکسته اصلاح.
7. **تست‌ها:** `python -m unittest test_creator_studio -v` (باید ۱۰/۱۰)، سوئیتِ langar (۸/۸)، سوئیتِ brain؛ سپس هر دو ولیدیتورِ vault: `validate_frontmatter.py` و `find_broken_links.py` (چون نامِ فایل‌های `.md` عوض شده).
8. **گِیتِ باقی‌مانده:** `git grep -in` برای ریشهٔ نام (هم لاتین هم فارسی) باید در سورس/شناسه‌ها **صفر** برگرداند (به‌جز لاگ‌های تاریخی که عمداً می‌مانند).
9. **کامیتِ نهایی** `agent-checkpoint: PF-CODE-REFACTOR-V1 — neutralize creator/operator name identifiers`.

**Rollback:**
- **کد/فایل:** `git revert <final-commit>` یا `git reset --hard <checkpoint-از-گامِ۱>`. چون همه‌چیز `git mv` + یک بَچ است، بازگشت **یک‌فرمانه و کامل** است (منطبق با قانونِ اساسیِ «کل جلسه یک‌فرمانه برگشت‌پذیر»).
- **env:** با fallbackِ §D5، حتی اگر مالک env را عقب نبرد، سیستم fail-soft می‌ماند؛ حذفِ fallback در ریلیزِ بعدی.
- **فایلِ زندهٔ handoff:** migration باید معکوس‌پذیر باشد (نگه‌داشتنِ نامِ قدیمی به‌عنوانِ کپی تا یک چرخهٔ سالم مشاهده شود) — نه حذف، فقط انتقال (منطبق با «هرگز حذف نکن؛ فقط منتقل کن»).

---

## Deliverable 5 — تذکرِ صریح: env-varها اکشنِ مالک‌اند

[FACT] تغییرِ نامِ `TELEGRAM_<C>_BOT_TOKEN` / `TELEGRAM_<C>_CHAT_ID` (و اپراتور: `TELEGRAM_<A>_CHAT_ID`) **در کد** بدونِ به‌روزرسانیِ **محیطِ اجراییِ مالک** یعنی ربات‌ها توکن/chat-id را `""`/`0` می‌خوانند و به no-opِ امن (fail-closed) می‌روند — یعنی استودیو بی‌صدا خاموش می‌شود.

- ✳️ **اکشنِ مالک (خارج از اختیارِ ایجنت):** به‌روزرسانیِ export/`.env`/تنظیماتِ محیط. طبق قوانین، ایجنت هرگز مقدارِ توکن/سکرت را نمی‌بیند، نمی‌نویسد و در چت/نوت/HANDOFF echo نمی‌کند.
- **الگوی fail-softِ پیشنهادی (زمان‌بندی‌شده):** برای یک ریلیز، خواندنِ env با fallback:
  `os.environ.get("TELEGRAM_CREATOR_BOT_TOKEN") or os.environ.get("TELEGRAM_<C>_BOT_TOKEN")`.
  این باعث می‌شود جاافتادنِ به‌روزرسانیِ مالک، سیستم را نشکند. **هزینه:** خطِ fallback برای یک بازه ریشهٔ نام را در سورس نگه می‌دارد (کامنت‌دار، زمان‌بندی‌شده). گزینهٔ جایگزینِ تمیزتر: بدونِ fallback، و صرفاً «قبل از restart، env را عوض کن» به‌عنوانِ پیش‌شرطِ مالک ثبت شود. **تصمیم با مالک.**

---

## Caveats و ریسک‌های باقی‌مانده
1. **تاریخچهٔ گیت پاک نمی‌شود.** rename، نام را از کامیت‌های قبلی حذف نمی‌کند؛ ریشهٔ نام در history باقی می‌ماند. OpSecِ کامل نیازمندِ history-rewrite (مثلِ `git filter-repo`) است که **مخرب، جداگانه و فقط با رأیِ صریحِ مالک** است — خارج از دامنهٔ این پراپوزال. پرچمِ «⚑ برای معمار».
2. **سندِ PII در ریشه:** `پرسشنامه پارتنر - پاسخ‌های <C>.md` نامِ سازنده را در نامِ فایل حمل می‌کند. این «شناسهٔ سورس» نیست؛ متعلق به حوزهٔ `08 - Partner (PII)` / `07 - Compliance`. تصمیمِ جدا (rename/انتقال) — نه بخشِ کامیتِ کد.
3. **پاس‌سازیِ P2 (متن/کامنت):** حذفِ نامِ خام از docstringها/aliasها یک پاسِ جدا و کم‌ریسک است؛ می‌تواند در همان بَچ یا بلافاصله بعد انجام شود، اما با شناسه‌ها قاطی نشود تا diff خوانا بماند.
4. **`/saba` اپراتور-فِیسینگ است:** فقط اپراتور در چتِ خصوصی‌اش می‌بیندش؛ نشتِ بیرونیِ کم — اما در سورس هست. rename به `/studio` توصیه می‌شود با نگه‌داشتنِ aliasِ مخفی یک ریلیز (حفظِ عادتِ اپراتور).

## سوال‌های باز برای رأیِ مالک
- آیا گروهِ A (نامِ اپراتور) در همان کامیتِ اتمیک با C برود؟ (توصیه: بله — بلاست‌رِیدیوسِ مشترک، دوباره‌کاری کمتر.)
- fallbackِ env بله/خیر؟ (پاکیِ سورس در برابرِ ایمنیِ fail-soft.)
- پاس‌سازیِ P2 و rename سندِ PII — همین جلسه یا جداگانه؟
- history-rewrite: در دستورِ کار قرار بگیرد یا صرفاً پرچمِ ریسکِ پذیرفته‌شده بماند؟
