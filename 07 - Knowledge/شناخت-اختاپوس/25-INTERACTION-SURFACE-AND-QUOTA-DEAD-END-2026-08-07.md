---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, interaction-surface, quota, mirror-room, ask_vault, miniapp, telegram]
created: 2026-08-07
updated: 2026-08-07
created_by: agent
sources:
  - "parallel agent (interaction-surface megaprompt), commits 972a1e7 + 9e06a1f, 2026-08-07"
  - "live end-to-end test against running processes (5/5 alive, beat 28201+), 2026-08-07"
---

# سطحِ تعامل و بن‌بستِ سهمیه — چرا «نمی‌شه باهاش حرف زد» — ۲۰۲۶-۰۸-۰۷

> مالک: «الان به عنوان هوش مصنوعی هیچ کاری انجام نمی‌ده، هیچ‌جایی نیست بشه باهاش
> حرف زد یا تعامل گرفت، با اینکه کنترل‌پنلم هست.» این نوت ریشهٔ آن را با شاهدِ
> واقعی پیدا می‌کند و دو فیکسِ انجام‌شده را مستند می‌کند. مکملِ نوتِ ۲۴
> (همگرایی/سینکِ آگاهی-حافظه) — آن یکی دربارهٔ «آیا درست فکر می‌کند»، این یکی
> دربارهٔ «آیا مالک می‌تواند با آن فکر تعامل بگیرد».

## خلاصهٔ یک‌خطی

«نمی‌شه حرف زد» **دو ریشهٔ واقعی و زنده** داشت، هر دو در دامنهٔ این ایجنت: (۱) مسیرِ
RAG ِ vault (`ask_vault`) به‌طور سیستماتیک با timeout می‌مرد، (۲) مسیرِ چتِ آزاد
(`mirror_room`) وقتی سهمیهٔ روزانهٔ فوگو پر می‌شود (که تقریباً هر روز پر می‌شود)
بن‌بست می‌شود، و پیامِ خطا گمراه‌کننده بود. هر دو فیکس شد. مینی‌اپ سالم بود.

## شاهدِ زنده — تستِ end-to-endِ واقعی

همهٔ ۵ پروسه (center/cortex/live/organism/gateway) زنده بودند (beat=28201+،
`ORGANISM-STATE.json` تازه). تست با همان محیطی که پروسهٔ زنده دارد (همهٔ فلگ‌های
`OCTOPUS-flags.cmd` load شده):

**۱. مسیرِ چتِ آزاد (mirror_room):**
```
model_router.ask('deep', tier='primary')
  -> ok=True tier='local' fallback_from='primary: paid-call-failed'
     (مغزِ پولی DENIED، fallback به qwen محلی)

mirror_room.ask('تو چه می‌دانی؟')  [clean single call, بعدِ rate-limit reset]
  elapsed: 120.0s  (مغزِ پولی کلِ timeout را مصرف کرد قبل از deny)
  -> ok=False reason='not-a-paid-brain' tier='local'
```
این **بن‌بست** است: سؤالِ مالک هیچ جوابی نمی‌گیرد. `center.py` این `reason` را
به پیامِ تلگرام نگاشت می‌کرد.

## 🔴 ریشهٔ اول — مسیرِ RAG ِ vault (`ask_vault`) کاملاً مرده بود (فیکس شد)

`ask_vault.query()` هر بار با `reason='rg-error'` برمی‌گشت. علت: ripgrep بعد از
۲۰ ثانیه timeout می‌زد.

**چرا:** دایرکتوریِ `.claude/` (کشِ ایجنت‌های موازیِ Claude Code) ۱۲٬۷۴۶ فایلِ
markdown داشت — از جمله **پنج کپی** از `Lead-نقاشی.md`ِ ۹۴۰کیلوبایتی در پنج
worktreeِ مختلف (`.claude/worktrees/*/03 - Projects/Lead-نقاشی/`). `_build/`،
`_archive-binaries/`، `_portable-build/` هم همین. هیچ‌کدام نه در `_ALWAYS_EXCLUDE`
بودند نه در `.agentignore`. پس هر جست‌وجو کلِ workspace را سه‌برابر اسکن می‌کرد.

**شاهدِ قبل/بعد (زنده):**
- قبل: `rg -i -c` روی ۲۰٬۶۷۶ فایلِ md → TIMEOUT >20s → `query()` ok=False reason='rg-error'
- بعد: همان کوئری 0.3s (count) + 0.1s (snippets) = ۲۶۷ فایلِ واقعی، `query()` ok=True
  با جوابِ مستند و ۴ منبع (`اختاپوس-شبه‌هولوگرافیک.md`، `DEEP-SCAN × اختاپوس`، ...).

**فیکس (commit `972a1e7`):** تاپلِ نو `_BUILD_EXCLUDE = (".claude", "_build",
"_archive-binaries", "_portable-build")` به `_exclude_globs` + `_is_excluded`
(کمربندِ دوم) اضافه شد. افزودنیِ محافظه‌کارانه، نه بازطراحی. ۳۵/۳۵
`test_tg_ask_vault` سبز؛ mutation-check هر دو لایه را verify کرد.

## 🔴 ریشهٔ دوم — چتِ آزاد بن‌بستِ سهمیه + پیامِ گمراه‌کننده (فیکس شد)

`mirror_room.ask()` **by design** فقط با مغزِ پولی (tier `primary`) حرف می‌زند —
جوابِ مغزِ محلیِ $۰ را رد می‌کند (این تصمیمِ طراحی است، نه باگ، و در docstringِ
ماژول مستند است). ولی وقتی سهمیهٔ روزانهٔ فوگو تمام می‌شود، مسیر کاملاً بن‌بست
می‌شود.

**شاهدِ زنده — سهمیه هر روزِ اخیر پر می‌شود** (`state/paid-calls.jsonl`):
```
2026-07-27: ok=58  quota-denied=0
2026-07-30: ok=60  quota-denied=0   ← cap (=60) پر شد
2026-08-02: ok=59  quota-denied=0   ← هر روز به سقف می‌رسد
2026-08-05: ok=60  quota-denied=0
2026-08-06: ok=60  quota-denied=80  ← بعد از سقف، ۸۰ درخواست رد شد
2026-08-07: ok=56  quota-denied=51  ← امروز: 51 درخواستِ ردشده (این ایجنت هم یکی)
```
`fugu-quota.json` امروز: `used_total=60/60`، هر دو primary (orchestr/Fugu) و
secondary (glm) با `quota_daily-cap` رد می‌شوند. `FUGU_DAILY_CALL_CAP=60` در
`OCTOPUS-flags.cmd` (پایین‌تر از پیش‌فرضِ ۳۰۰).

**مشکلِ پیام:** قبل از فیکس، center.py می‌گفت: «مغزِ گرانم الان در دسترس نیست —
چند دقیقهٔ دیگر دوباره بپرس.» این **دو غلط** داشت: (۱) «چند دقیقه» دروغ است —
سهمیه تا نیمه‌شب ریست نمی‌شود؛ (۲) «در دسترس نیست» شبیهِ خرابی است، درحالی‌که این
محافظتِ طراحی‌شده‌ی بودجه‌ست. دقیقاً همان تجربهٔ «بی‌فایده به نظر می‌رسد» که مالک
گفت.

**فیکس (commit `9e06a1f`):** دو نگاشتِ رشته (async + sync) در center.py فقط
صادقانه شد: «سهمیهٔ امروزِ فکرِ عمیقم تمام شد — فردا (ریستِ خودکارِ سهمیه) دوباره
بپرس.» فقط نمایش؛ `reason`-key (`not-a-paid-brain`) که mirror_room تولید می‌کند
دست‌نخورده ماند. ۱۷/۱۷ + ۱۲/۱۲ + ۴/۴ تست سبز.

> ⚠️ **نکتهٔ روشی:** تست‌های سریالِ من در همان پروسه چندبار `no-answer` برگرداندند
> — این **rate-limitِ خودِ ایجنت بود** (`ask_brain._take` حداقل ۲۰s بین دو call)،
> نه باگِ سیستم. تمیزترینِ شاهد: یک callِ منفرد بعد از reset دقیقاً
> `not-a-paid-brain` برگرداند. هرگز «چون کد درست به نظر می‌رسد» جواب را فرض نکن.

## ✅ مینی‌اپ — ۷ تب همگی سالم (دادهٔ زنده)

هر ۷ تب با فراخوانِ توابعِ واقعیِ `miniapp_state` (همان که gateway می‌خواند)
تست شد، و خروجی با `ORGANISM-STATE` ِ زنده مقایسه شد:

| تب | endpoint | وضعیت |
|---|---|---|
| خانه | `/api/state` | ✅ beat=28210 = beatِ زنده (MATCH) |
| تأییدها | `/api/approvals` | ✅ items=0 (درست — هیچ pending) |
| پول | `/api/value` | ✅ total=118 (دادهٔ واقعی) |
| لیدها | `/api/legs` | ✅ legs live |
| کارها | `/api/ops/tasks` | ✅ tasks_total=5 done, 0 open (درست خالی) |
| سیستم | `/api/ops/brain` | ✅ فکرِ cortex را نشان می‌دهد (پایین) |
| سیستم | `/api/lifecycle` | ✅ lifecycle live |
| اعلان‌ها | `/api/notifications` | ✅ items=[] unread=0 (notif_inbox هنوز flag-off) |

**هیچ تبی خراب نیست.** تب‌های خالی (کارها/اعلان‌ها) به‌درستی خالی‌اند، نه دادهٔ کهنه/غلط.

## ✅ افکارِ cortex قابلِ دیدن‌اند (سؤال ۴)

تبِ «سیستم» → بخشِ brain در مینی‌اپ، فکرِ فعلیِ cortex را نشان می‌دهد:
```
reachable=True cycle=5 coherence=0.922
thought: "[local] البته، مهم‌ترین کار این است که بخش‌های نیازمند توجه را ..."
```
این فکرِ محلیِ qwen است (echo). فلگِ `CORTEX_RICH_THINK` آرم شد ولی cortex
هنوز یک tick لازم دارد تا فکرِ غنی تولید کند. **هیچ ویژگیِ نو برای visibility لازم
نیست** — شکاف وجود نداشت. (شکافِ واقعی در مسیرِ *پاسخ‌دادن به مالک* بود، نه در
visibility.)

## توصیهٔ آرم‌کردنِ `notif_inbox` + `restart_control`

سوییتِ تست‌ها امروز دوباره اجرا شد و کاملاً سبز است:
`test_notif_inbox` 14/14 · `test_restart_control` 16/16 ·
`test_center_notif_inbox` 3/3 · `test_restart_center_wiring` 10/10.

**توصیه: امن برای آرم‌کردن.** دلیل:
- `notif_inbox.route()` وقتی فلگ خاموش است دقیقاً همان `send_fn()` قبلی را صدا
  می‌زند — byte-identical. روشن فقط یک لایهٔ صف اضافه می‌کند.
- `restart_control.execute_restart` فقط بعد از یک `approval_store` approve واقعی
  صدا زده می‌شود — این ماژول هرگز خودش تصمیم نمی‌گیرد کِی ری‌استارت شود.
- هر دو فلگ (`OCTOPUS_WIRE_NOTIF_INBOX`، `OCTOPUS_WIRE_RESTART_CONTROL`) هنوز در
  `OCTOPUS-flags.cmd` **نیستند** و هیچ پروسه‌ای load نکرده‌اشان (تأیید: هر ۵
  `flags-loaded-*.json` نشان می‌دهد `<missing>`). آرم‌کردن یعنی اضافه‌کردنِ
  `set ...=1` به flags + ری‌استارت.

**تصمیم با مالک.** این ایجنت خودش آرم نکرد.

## سؤالِ باز برای مالک (در AGENT_QUESTIONS نرفته — اینجا)

۱. **آیا سقفِ روزانهٔ فوگو باید بالاتر برود؟** `FUGU_DAILY_CALL_CAP=60` در
   flags.cmd (پیش‌فرضِ کد ۳۰۰). هر روزِ اخیر به ۶۰ می‌رسد و بعد از آن چتِ عمیق
   بن‌بست می‌شود. اگر مالک می‌خواهد بتواند هر روزِ کاری با اختاپوس حرف بزند،
   سقفِ ۶۰ کافی نیست — یا باید بالا برود، یا mirror_room باید یک مسیرِ
   *graceful-degradation* داشته باشد (مثلاً وقتی پولی بسته است، با هشدارِ واضح
   از محلی جواب دهد، نه سکوتِ کامل). این تصمیمِ طراحیِ بزرگ است، نه این جلسه.

۲. **آیا `notif_inbox`/`restart_control` همین حالا آرم شوند؟** (طبقِ توصیهٔ بالا).
   فقط نیاز به اضافه‌کردنِ دو خطِ `set ...=1` + یک ری‌استارت دارد.

## فیکس‌های این جلسه (commitها)

- `972a1e7` fix(ask_vault): exclude `.claude`/`_build`/`_archive-binaries`/`_portable-build`
  از rg — kill `rg-error` timeout
- `9e06a1f` fix(center): پیامِ صادقانه برای `not-a-paid-brain` در آینه — سهمیه‌ست،
  نه خرابی

## بکاپِ خام

`C:\Users\Armin\Desktop\OCTOPUS-SCAN-INTERACTION-2026-08-07\` — لاگِ کاملِ
end-to-end، snapshot ِ ORGANISM-STATE، وضعیتِ fugu-quota، خروجیِ خامِ هر endpoint،
خروجیِ هر دو validator.
