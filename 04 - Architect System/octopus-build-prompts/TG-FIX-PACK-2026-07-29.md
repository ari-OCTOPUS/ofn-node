---
type: prompt
status: ready
tags: [octopus, telegram, build-prompts, code, two-bot]
created: 2026-07-29
updated: 2026-07-29
created_by: agent
sources:
  - "[[06 - Architecture Maps/TG-SPLIT-INNER-OUTER-2026-07-29]]"
  - "[[06 - Architecture Maps/OCTOPUS-25-IMPROVEMENTS-2026-07-29]]"
  - "[[06 - Architecture Maps/OCTOPUS-25-A-کنترلِ-پاها-2026-07-29]]"
  - "[[_ops/telegram_center/surface-routing.json]]"
  - "[[_ops/BOTS-REGISTRY]]"
---

# TG-FIX-PACK — پرامپت‌های تعمیرِ کاملِ سطحِ تلگرام (کدنویسی)

> **v2 — پس از بازبینیِ متخاصمِ ۶-ایجنته (۳۳ یافته).** بازبینی یک خطای P0 معماری در نسخهٔ اول گرفت: طرحِ «دو poller» با pollerِ زندهٔ `approval_channel` روی توکنِ باتِ ۱ تصادم (409) می‌کرد و دکمه‌ها را می‌بلعید — دقیقاً همان باگی که split قرار است ببندد. طرحِ درست (سندِ مصوبِ مالک [[06 - Architecture Maps/TG-SPLIT-INNER-OUTER-2026-07-29|TG-SPLIT]]): **هیچ pollerِ نو؛ فقط clientِ دومِ «فقط-ارسال».**
>
> **هدف:** تلگرامِ دو-باتی *واقعاً* کار کند — کارت‌ها دکمه‌شان را نگه دارند، هر جریان به باتِ درست برسد (بدونِ ۴۰۹)، هر پا تاپیک داشته باشد، هر فرمان reachable باشد، گفتگو به مغز برسد. پنج بستهٔ مستقل؛ §۰ و §روش برای همه یکی است.

## نقشهٔ وابستگی

```
TG-P1 (یکپارچگیِ کارت) ──► بلاکر، اول
        ▼
TG-P2 (سطحِ دو-باتی: فقط-ارسال، بدونِ pollerِ نو) ──► هسته
        ├──► TG-P3 (اتاق و کنترلِ پاها)
        ├──► TG-P4 (بهداشتِ سطحِ فرمان)
        └──► TG-P5 (سطحِ گفتگو)
```
آرمِ فلگ‌ها آخر و owner-gated. هیچ بسته خودش فلگ روشن نمی‌کند.

## §۰ — ریل‌های ایمنی (غیرقابل‌مذاکره، هر ۵ بسته)

1. **درختِ مشترک** (~۱۳۶ فایلِ `.py` uncommitted). **هرگز `git add -A`.** برنچِ `fix/tg-<pkg>-2026-07-29`؛ فقط هانکِ خودت را `git add -p`/`git apply --cached`.
2. **درختِ زنده مقدس.** هیچ تست/سوییت بدونِ pin صریحِ `ORG_ROOT`+`REAL_VAULT` به کپیِ temp — `run_all` بی‌pin ارگانیسم را می‌خوابانَد. هیچ ری‌استارت/فلگ/`STOP-*` خودت نزن.
3. **⚠️ ریلِ دو-باتی (تازه، حیاتی):** تست‌های ارسال/انتخابِ client **هرگز با توکنِ واقعیِ بات** اجرا نشوند. توکنِ باتِ ۱ (`TELEGRAM_BOT_TOKEN`) را همین حالا `approval_channel` زنده poll می‌کند؛ یک `getUpdates`ِ رقیب روی آن = **۴۰۹** و بلعیدنِ callbackهای واقعیِ مالک روی @Robo2725 — یک اثرِ سمتِ-تلگرام که pinِ فایل‌سیستمی جلویش را نمی‌گیرد و `poll_updates` هم آن را بی‌صدا `[]` می‌کند. **همیشه** با توکنِ فیک یا `get_fn`/`post_fn`ِ تزریقی (tg_api پشتیبانی می‌کند) تست کن؛ انتخابِ client را با stub بسنج، نه getUpdatesِ زنده.
4. **propose-only:** `MAY_MERGE` خاموش؛ دو رأیِ مالک. هر فلگِ تازه → کارتِ VERDICT_QUEUE + سطرِ ARMING-ORDER. اثر فقط با ری‌استارت (owner).
5. **گیت روی رگرسیون** (`candidate.failed ⊆ baseline.failed`) نه سبزِ مطلق — پس **تستِ pin‌شدهٔ موجود را قرمز نکن** (چند آیتمِ زیر صریحاً هشدار می‌دهند کدام تست pin است).
6. **AV `.git/objects` را می‌بندد** → کامیت را retry کن. **Edit فایلِ `.cmd/.bat` را LF می‌کند** → CRLF برگردان. خطِ پایان: organism/center=CRLF، cortex/live=LF، tests=LF؛ برای نوشتن `write_bytes`/`newline=''`.
7. **صفر secret/شناسهٔ عددی** echo — فقط نامِ envِ متغیر. `.agentignore` محترم.
8. **کارتِ فارسیِ RTL:** هر عددِ لاتین با ایزولهٔ `U+2066…U+2069` + رقمِ فارسی.

## §روش (هر آیتم)
۱. **بازتولیدِ شاهد** با grep/read (خطوطِ `file:line` با drift جابه‌جا شده‌اند — سمبل را grep کن). ادعای غلط → «رد شد» با شاهد. ۲. **فیکسِ حداقلی.** ۳. **اثباتِ اثر:** تستِ تازه را **تجربی** روی کپیِ pin‌شده اجرا کن، شمارِ pass/fail صریح؛ فایلِ pytest-style که مستقیم اجرا شود صفر assert می‌دود = سبزِ دروغ؛ هر تابعِ تازه **صداکننده** داشته باشد؛ هر گارد بگو کدام **جهش** قرمزش می‌کند و آن جهش واقعاً باید قرمز شود (نه inert).

---

## TG-P1 — یکپارچگیِ کارت (Card Integrity) · بلاکر · P1 · ~۱h
> بازبینی: **SOUND**. بدونِ تغییر.

**آیتم ۱ — A9-1: `_scrub_keyboard` کیبوردِ dict-شکلِ bridged را بی‌صدا `[]` می‌کند.**
- وضع: پل markup کاملِ `{"inline_keyboard":[[...]]}` را verbatim به `keyboard=kb` می‌دهد؛ `_scrub_keyboard` (`tg_api.py:84`) `list[list[dict]]` فرض می‌کند → روی dict به `dict(char)`→`ValueError`→`except`→`[]`. هر دکمه حذف، بی‌خطا. تنها گارد (`test_bridge_buttons.py`) clientِ فیک دارد → سبزِ کاذب.
- فیکس: قبل از حلقه `if isinstance(keyboard, dict): keyboard = keyboard.get("inline_keyboard")` + `for row in (keyboard or [])`. الگو از `doctor_link._keyboard:103`.
- گارد: `_scrub_keyboard`ِ **واقعی** با `{"inline_keyboard":[[{...}]]}` → ۱ ردیف نه `[]`. **جهش:** حذفِ unwrap → `[]`.
- P1 · ~۰٫۵h.

**آیتم ۲ — A9-2: سرریزِ `callback_data` از ۶۴B وقتی `OCTOPUS_WIRE_CB_TOKEN` آرم شود (نهفته).**
- `_TOKEN_LEN` (`callback_token.py`) از ۲۰→۹ (۶+۴۸+۱+۹=۶۴؛ lookup-safe). گارد: `CB_TOKEN=1`+jid ۴۸-کاراکتری → هر callback_data ≤۶۴B. **جهش:** `_TOKEN_LEN=20`. P1 · ~۰٫۵h · رأیِ مالک روی trade-offِ ۳۶-بیتی.

---

## TG-P2 — سطحِ دو-باتیِ زنده (Two-Bot Split) · هسته · P1 · ~۱۰–۱۶h · owner arms
> **بازنویسیِ کامل پس از P0.** طرح از سندِ مصوبِ [[06 - Architecture Maps/TG-SPLIT-INNER-OUTER-2026-07-29|TG-SPLIT]] پیروی می‌کند: **هیچ pollerِ نو.**

**پیش‌نیاز:** TG-P1. **گراندینگِ اجباری:** `TG-SPLIT-INNER-OUTER-2026-07-29.md` (قاعده‌های سخت §۳۳–۴۴)، `surface-routing.json`، `BOTS-REGISTRY.md`.

**حقیقتِ پایه (تصحیح‌شده):**
- `surface-routing.json` صفر مصرف‌کننده در کد؛ `OCTOPUS_TG_SPLIT_V1` غایب=خاموش.
- **inner = @Robo2725 = `TELEGRAM_BOT_TOKEN`** — همین حالا توسطِ `approval_channel.py` (پروسهٔ ارگانیسم، `poll_once`/`run_forever`) poll می‌شود. **outer = @intergrade2725 = `TG_CENTER_BOT_TOKEN`** — توسطِ center. (نامِ envها همین‌هاست؛ `TELEGRAM_INNER/OUTER_BOT_TOKEN` **وجود ندارد**.)
- یک لایهٔ روتینگِ زندهٔ دیگر هست که با این هم‌پوشان است: `surface_policy.py` (پشتِ `OCTOPUS_TG_SURFACE_V2`) که GROUP/DM/HOLD تصمیم می‌گیرد و در `approval_channel`/`leg_room_report`/`wiring` مصرف می‌شود. **باید با آن آشتی داده شود** (کدام فلگ روی مسیرِ ارسال برنده است).

**قاعده‌های معماری (چرا این نسخه امن است):**
- **هیچ `getUpdates`ِ نو.** `sendMessage` آپدیت مصرف نمی‌کند، پس clientِ فقط-ارسال روی توکنِ inner امن است. هرگز روی توکنی که جای دیگری poll می‌شود getUpdates نزن.
- **جریانِ دکمه‌دار جایی می‌رود که pollerش callback را می‌فهمد.** کارتِ سه‌تکهٔ دکتر فقط در center handler دارد → `doctor-intent/diff` روی **outer** می‌ماند تا (گامِ ۵، پچِ جدا + رأی) `doctor_link.handle_callback` به مسیرِ callbackِ `approval_channel` اضافه شود. کارتِ دکتر را بی این handler به inner نفرست، وگرنه رأی گم می‌شود.

**آیتم‌ها:**

**۱ — خوانندهٔ `surface-routing.json` + انتخابِ مقصدِ ارسال (helperِ مشترک).**
- (ب) شکاف: نقشه هست، مصرف‌کننده نیست. (ج) فیکس: `telegram_center/surface_router.py` که برای هر `stream` تاپلِ `(bot, surface, topic)` از `current` می‌دهد مگر `flag('OCTOPUS_TG_SPLIT_V1')` → `target`. **helperِ مشترک** (نه center-only): چون emitterها پخش‌اند — `doctor_link.beat`، `money_pulse.beat`، digest/alertِ center، و `approvals-organism` که در **پروسهٔ جدای** `approval_channel` تولید می‌شود. هر emitter از این helper client را انتخاب کند؛ برای `approval_channel` (پروسهٔ دیگر) helper را آن‌جا هم import کن.
- (د) گارد: **سطحِ یکپارچگی، نه نگاشتِ خالص.** با فلگ خاموش، `(client,chat,topic)`ِ انتخاب‌شدهٔ center برای **هر جریانی که واقعاً می‌فرستد** (≈۷ جریان، نه هر ۱۱) = ارسالِ تک-clientِ گروهیِ امروز، بایت‌به‌بایت. **جهش:** hardcode کردنِ bot یک جریان → پاریتی قرمز. یک unit-testِ نگاشتِ خالص جدا بگذار ولی آن را «پاریتی» نشمار.
- (ه) ~۳h + یکپارچگی (زیر).

**۲ — clientِ دومِ «فقط-ارسال» (بدونِ getUpdates).**
- نام‌های واقعی: `outer→TG_CENTER_BOT_TOKEN`، `inner→TELEGRAM_BOT_TOKEN` (⚠️ همان توکنِ approval — فقط send، هرگز poll). token غایب → fail-soft به تک-باتیِ امروز + alert. گارد: با `post_fn`ِ تزریقی client درست انتخاب شد (ریلِ ۳: توکنِ واقعی ممنوع). **جهش:** پین به یک client → تستِ دو-clientی قرمز. ~۱٫۵h.

**۳ — سطحِ DM: `message_thread_id` را در DM بینداز.**
- (ب) شکاف: `target` چند جریان را به `surface:dm` می‌برد، ولی همهٔ topic-wiring فرضِ سوپرگروهِ forum دارد؛ فرستادنِ `message_thread_id` به DM = **۴۰۰ Bad Request** و گمِ کلِ کارت (`tg_api.send` هنگامِ topic_id بی‌قید thread ست می‌کند). (ج) فیکس: selector وقتی `surface==dm` است `topic_id` را حذف کند، `create_topic` را skip کند، و تاپیکِ per-leg فقط وقتی `surface==group`. (د) گارد: ارسالِ DM-routed هیچ `message_thread_id` ندارد. **جهش:** نگه‌داشتنِ thread در DM → تست قرمز. ~۲h.

**۴ — `setMyCommands` per-bot.**
- امروز فقط یک‌بار روی یک client ثبت می‌شود (`center.py` setup). زیرِ split، inner و outer باید منوهای فرمانِ متفاوت داشته باشند (یا inner هیچ). دو پروفایلِ COMMANDS، هرکدام روی clientِ خودش. flag-off = همان ثبتِ تک-outerِ امروز بایت‌به‌بایت. گارد: منویِ تبلیغ‌شدهٔ هر بات = مجموعهٔ فرمانِ reachableاش. ~۱٫۵h.

**۵ — backoffِ ۴۰۹/۴۲۹ per-token.**
- امروز `poll_updates` هر خطا را `[]` و `_call_post` را `None` می‌کند بی‌backoff؛ ۴۲۹ `retry_after` رعایت نمی‌شود. با ارسالِ بیشتر روی دو توکن سطحِ rate-limit بزرگ‌تر است. `error_code==429` + `parameters.retry_after` را parse و per-token backoff کن؛ روی ۴۰۹ pollerِ مقصر را عقب بکش نه spin. fail-soft per-token. ~۲h.

**۶ (اختیاری) — رسانه (عکس/ویس) اگر مالک بخواهد.**
- ⚠️ **تصحیحِ بازبینی:** `allowed_updates=['message','callback_query']` عکس/ویس را *همین حالا* می‌رساند (photo/voice یک `message` است، نوعِ جدا نیست). drop در `_handle_message` (`center.py:735`) است که فقط `msg.get('text')` می‌خواند و روی خالی `None`. اگر رسانه لازم است، همان‌جا `caption`/`voice`/`photo` را بخوان؛ **به `allowed_updates` دست نزن.** گارد: پیامِ photo-دار → هندلر پردازش کند. ~۱h.

**بودجهٔ بازنگری‌شده:** با helperِ مشترکِ چند-emitter + ~۴۰ نقطهٔ `self._client.send` در center + DM + per-bot commands + backoff، این **~۱۰–۱۶h** است نه ۳h. یا center را تک-clientِ outer نگه‌دار و فقط جریان‌های صریحِ inner-مقصد را route کن (کوچک‌تر)، یا selector را در همهٔ send-siteها بریز (بزرگ‌تر) — یکی را انتخاب و بودجه کن.

**پذیرشِ TG-P2:** پاریتیِ flag-off (سطحِ یکپارچگی) بایت‌به‌بایت = امروز؛ flag-on (روی کپیِ تست، با stub نه توکنِ واقعی) جریان‌های inner را به clientِ inner می‌فرستد، هیچ getUpdatesِ نو، کارتِ دکتر روی outer می‌ماند؛ آشتیِ صریح با `surface_policy`؛ کارتِ VQ-SPLIT-001 + سطرِ ARMING-ORDER؛ صفر توکن echo.

---

## TG-P3 — اتاق و کنترلِ پاها (Leg Rooms + Control) · P1 · ~۵h
> بازبینی: A6 «raw-merge» یک no-opِ بی‌صدا بود؛ به **projection** تصحیح شد.

**آیتم ۱ — A6: اتاقِ ziman/cartographer/studio_pf ساختاراً ساکت.**
- (الف) وضع: `leg_rooms_beat` از `business_legs` (۵ پا، `wiring.py:2518` `_BUSINESS_LEGS_SPEC`) تغذیه می‌شود؛ `leg_room_report.LABEL` هفت کلید (شاملِ ziman/cartographer، بدونِ studio_pf). حالتِ ziman/cartographer در `ORGANISM-STATE.json` است، studio_pf در `business_brain`.
- (ب) شکاف + دامِ حیاتی: **raw-merge کار نمی‌کند.** `signal_hash` (`leg_room_report.py:135-150`) فقط کلیدهای `live/signal/note/status` + عددی‌های whitelist را می‌خواند؛ بلوکِ خامِ ziman (`money_link/inventory_hint/drafts_count…`) و cartographer (`mood/map_age_days/drift_files…`) هیچ‌کدام را ندارند → `signal_hash=""` → `due()` skip (`:191-192`) → صفر کارت، **دقیقاً مثلِ امروز**. `render._collect_legs` (`render.py:228-254`) درست عمل می‌کند چون هر بلوک را به سلولِ نرمال **projection** می‌کند.
- (ج) فیکس: قبل از `due()`، ziman/cartographer را به شکلِ `{live,signal,note}` **projection** کن (آینهٔ `render._collect_legs`): مثلاً `ziman→{'live':money_link=='active','signal':money_link,'note':inventory_hint}`؛ `cartographer→{'live': not map_stale,'signal':mood,'note':f'drift {drift_files}'}`. `ORGANISM-STATE.json` را با `json.loads(opslib.STATE_DIR/'ORGANISM-STATE.json')` بخوان (fail-soft؛ opslib **API خواندن ندارد**، فقط `STATE_DIR`؛ آینهٔ `render._read_json`). ziman/cartographer در فایلِ اصلیِ merged هستند (نویسندهٔ یگانه organism.py).
- **studio_pf (درزِ جدا):** کلیدِ leg همه‌جا `studio_pf` است ولی `surface_policy.LEG_TOPIC` استریمِ `'studio'`→تاپیکِ `studio_pf` را می‌شناسد (کلیدِ `studio_pf` نیست) → `route('studio_pf')`=HOLD. پس یا با `stream='studio'` بفرست یا `'studio_pf'` را به `LEG_TOPIC` alias کن. سلولش را از `business_brain.summary().projects` (نامِ 'project-f') بگیر، **نه** ORGANISM-STATE. LABEL را با special-case در `leg_room_report` بده (`LABEL={**_labels(),'studio_pf':'🎬 استودیو'}`)، **نه** با ویرایشِ `chat_room.LEGS` (قراردادِ content-freeِ venture را می‌شکند).
- (د) گارد (ضدِ green-by-seed): سلول را با **شکلِ بلوکِ واقعی** seed کن (ziman: `money_link/drafts_count/inventory_hint`؛ cartographer: `mood/map_age_days/drift_files/refresh_recommended`) و assert کارت ارسال شد — این projection را مجبور می‌کند. assertِ دوم: بلوکِ خام **بدونِ** `live/signal/note/status` نباید کارت بدهد (اثباتِ اینکه projection واقعی است نه seedِ میان‌بر). **جهش:** raw-merge بدونِ projection → `signal_hash=""` → صفر کارت → قرمز.
- (ه) P1 · ~۳h.

**آیتم ۲ — A1: قراردادِ کنترلِ پاها (مالکِ ناوردیِ روستر).**
- (ج) فیکس: به‌جای برابریِ مسطحِ چهار جدول (که عمداً واگرایند)، یک **روستر canonical + محمول‌های نقش** تعریف کن: `is_pausable`/`has_chat_entry`/`topic_only`، و **زیرمجموعه** assert کن: `menu2._PAUSABLE ⊆ power.PAUSABLE_LEGS ⊆ (render.LEGS − ROOMS)`، و `power` عمداً `system` را حذف می‌کند. driftِ واقعی که باید فیکس شود: `menu_integration._PAUSABLE` ادعا می‌کند = `power.PAUSABLE_LEGS` ولی `studio_pf/knowledge/cartographer` را کم دارد.
- (د) گارد: subset-aware (نه flat-equality). **جهش:** افزودنِ پای تازه به `render.LEGS` بدونِ ثبتِ نقش → قرمز.
- (ه) P1 · ~۲h. (این آیتم **مالکِ** ناوردیِ روستر است؛ A8-5 آن را تکرار نکند.)

---

## TG-P4 — بهداشتِ سطحِ فرمان · P2 · ~۷–۱۲h · موازی با P3/P5
> بازبینی: چند over-claim/guard-trap تصحیح شد.

- **A8-1 — `/lead` و `/verdicts` دو معنا:** center معنیِ ارگانیسم را سایه می‌کند. ولی organism `/lead` در ≥۵ جا سیم است (`_OWNER_ONLY…:1630`، `_GROUP_READONLY…:1638`، `setMyCommands:735`، `server.py:2546`) و تستِ pin `test_telegram_channel.py:699` (`/lead is not None`). پس **organism `/lead` (ثبت) را نگه‌دار و فرمانِ quoteِ center را rename کن** (`/quote` گرفته است `center.py:817` → نامِ آزادِ دیگر)؛ setMyCommands + تستِ pin را به‌روز کن. گاردِ پاریتی: قبل از اشتراک، توکن‌ها را normalize کن (trailing-space بردار، startswith-prefix را به head حل کن) و whitelist بگذار (`/start`،`/help` هم تصادم دارند). ⚠️ این ~یک‌خطی **نیست**. ~۲h.
- **A8-2 — `/start_exp<N>` بی‌روتر:** ⚠️ **فقط مسیرِ بازنشستگی.** سیم‌کردنش تستِ pinِ `test_telegram_channel.py:702` (`is None`، عمداً button-only) را قرمز می‌کند = نقضِ ریلِ ۵. از `_OWNER_ONLY_COMMAND_PREFIXES` + رشتهٔ خطا/spec حذف کن؛ ورودیِ دکمهٔ `act:lab` را دست نزن. گارد **استاتیک** (assert وجودِ برنچِ روتر per prefix)، **نه** فراخوانِ زنده — فراخوانِ `/review،/books،/sync،/neworgan` اثرِ جانبیِ واقعی دارد (`/sync` شبکه) و ریلِ ۲ را می‌شکند. ~۱h.
- **A8-3 — فرمان‌های phantom لنگر:** ⚠️ `langar_bridge.ready()` **وجود ندارد** — اول بسازش (probeِ `_get_langar_bot()`/`_langar_dir()` بی‌اثر). `_GROUP_READONLY_COMMANDS` مجموعهٔ **مجوز** است نه تبلیغ (نگهش دار static)؛ فقط سطحِ advertised/dispatch-reply را روی `ready()` گیت کن و «langar خفته» صریح برگردان نه `None`ِ خاموش. ~۲h · PLAUSIBLE.
- **A8-4 — `chat_room` mining→`/mining`ِ مرده:** فقط **شرطی-به-فلگ** (mining→`/mining` وقتی `OCTOPUS_WIRE_MINING_UI` روشن، وگرنه `/organs mining`) — `/organs mining`ِ بی‌قید UIِ غنی را تنزل می‌دهد. گارد را به `chat_room.ROOMS` هم گسترش بده (phantomِ `/brief`ِ venture) یا به A8-3 بسپار. ~۱h.
- **A8-5 — یگانه‌سازیِ callback/roster:** ⚠️ **over-claimِ «actions.py بی‌مصرف» را حذف کن** — `render.py:709-729` (`_ap_callback`) زنده مصرفش می‌کند (approve/reject روی هر کارت). ناوردیِ roster را به **TG-P3/A1** بسپار (subset، نه تکرار). گاردِ «هر وربِ dispatch در `actions.ACTIONS`» را به وربی که فیکس واقعاً لمس می‌کند scope کن (`mn/lg/ap`) + مجموعهٔ exemptِ صریح برای `rev/menu/act/verdict` (وگرنه امروز قرمز است). driftِ واقعی: `menu2._PAUSABLE ↔ power`. ~۲–۶h · owner-gated.

---

## TG-P5 — سطحِ گفتگو · P1/P2 · ~۳h · ری‌استارتِ center لازم
> بازبینی: goalِ B10 over-claim بود؛ محلِ دفترِ dispatch و ترتیبِ B16 تصحیح شد.

**آیتم ۱ — B10: `chat_room` پیش از `ask_brain`/`mirror`.**
- (الف) وضع: `center.py:869` `_chat_room` قبل از `_handle_ask` (`:872`)؛ mirror `:1149`، ask_brain else-شاخهٔ `:1259`.
- (ج) فیکس: (الف) گاردِ آینه در `_chat_room` (`if room=="mirror": return None`)؛ (ب) **دفترِ تصمیمِ dispatch — داخلِ شاخهٔ free-text** (دورِ فراخوان‌های `_chat_room`/`_handle_ask` در `center.py:869-872`، قبل از return لاگ کن) — **نه** «تهِ `_handle_message`» (free-text آن‌جا زودتر return می‌کند، `:871`/`:872`). برچسبِ `ask_brain:<ok|reason>` را **داخلِ else-شاخهٔ `_handle_ask` (`:1259-1272`)** بزن جایی که ok/reason معلوم است — از `kind`ِ برگشتی نمی‌آید (روی `ask_unknown` می‌ماند).
- (د) گارد: ⚠️ تست **باید** `OCTOPUS_WIRE_CHAT_ROOM=1` و `room=='mirror'` را ست کند (`msg['_room']='mirror'` via `_wire()` فیک) وگرنه فلگ-off در `:1031-1032` short-circuit می‌کند و جهش inert می‌شود (سبزِ دروغ). با آن ست: حذفِ خطِ گاردِ mirror → «خودت چطوری؟» به /reveal → قرمز. و دقیقاً یک رکوردِ dispatch per free-text.
- (ه) P1 · ~۲h. ⚠️ **goal دقیق:** «متنِ گفتگویی در تاپیکِ mirror به mirror می‌رسد + دفترِ dispatch در همهٔ تاپیک‌ها hijack-vs-ask را قابلِ‌ممیزی می‌کند.» در تاپیک‌های غیر-mirror، متنِ کلیدواژه‌دار **عمداً** به فرمانِ کارمند می‌رود (رأیِ chat_room)؛ ادعا نکن ask_brain برای آن‌ها برمی‌گردد — دفتر فقط **می‌بیند**، فیکس نمی‌کند.

**آیتم ۲ — B16: `record_correction`.**
- (ج) فیکس: `record_correction` را به مسیرِ موفق (بعد از چکِ `MIN_CHARS` در `mirror_room.py:245`) ببر. ⚠️ **دامِ ترتیب:** `prev = recent_turns(1)` را **قبل از** append به HISTORY (`:248`) بگیر، وگرنه `about` به جوابِ همین نوبت bind می‌شود. `corrected` را up-front حساب کن.
- (د) گارد: به **تستِ harness-isolatedِ موجود `test_mirror_room.py`** اضافه کن (ORG_ROOT/REAL_VAULT را با `harness.setup` **قبل از** import ِ mr/ab پین می‌کند)؛ `_on()/_reset()/_fn()` را بازاستفاده کن. ⚠️ `mirror_room.ask()` به `owner-corrections.jsonl` می‌نویسد (که `self_knowledge` حالا می‌خواند) و quotaِ ask_brain مصرف می‌کند؛ `STATE_DIR` سرِ import bind می‌شود → تستِ standalone درختِ زنده را مسموم می‌کند. نوبتِ شکسته نباید سطرِ correction بگذارد. **جهش:** record قبل از ask → سطرِ نویز → قرمز.
- (ه) P2 · ~۱h.

---

## معیارِ پذیرشِ کلِ پک
- **کارت‌ها دکمه دارند** (A9-1، تستِ واقعیِ scrub)؛ هیچ callback > ۶۴B.
- **دو-باتی بدونِ ۴۰۹:** `surface_router`ِ مشترک؛ **هیچ getUpdatesِ نو**؛ flag-off سطحِ-یکپارچگی بایت‌به‌بایت = امروز؛ کارتِ دکتر روی outer؛ DM بدونِ thread؛ per-bot setMyCommands؛ backoffِ ۴۲۹؛ آشتی با `surface_policy`.
- **پاها صدا دارند** (projection نه raw-merge؛ گاردِ بلوکِ واقعی)؛ ماتریسِ subset-aware.
- **فرمان‌ها reachable**؛ تست‌های pin (`:699`،`:702`) قرمز نشوند.
- **گفتگو در mirror به مغز؛ دفترِ dispatch شاهد.**
- **همیشه:** هر دو validator سبز؛ `day --live` بدونِ رگرسیون؛ کامیت با هانکِ خودت؛ کارتِ VERDICT_QUEUE + ARMING-ORDER برای هر فلگِ تازه؛ صفر secret/شناسه echo؛ تست‌ها با توکنِ فیک/تزریقی (ریلِ ۳).

## خارج از دامنه (عمداً)
- **شهود (شومان):** جریانِ `intuition` تا سخت‌افزار `[UNKNOWN]` — کدِ ارسال نساز.
- **آرمِ فلگ/merge/ری‌استارت/خرجِ پول/ارسالِ بیرونی:** رأیِ مالک. این پک فقط می‌سازد و تست می‌کند.

## وضعیتِ اجرا
- **TG-P1:** انجام‌شده (A9-1 + A9-2، روی برنچِ canonical).
- **TG-P2:** **انجام‌شده (۲۰۲۶-۰۷-۳۰)** — پنج آیتمِ هسته روی «دنیای A» (center). کامیتِ `70cba70` روی `fix/tg-p2-2026-07-30`. گزارشِ کامل: [[TG-P2-EXECUTION-REPORT-2026-07-30]]. آیتم ۶ (رسانه) موکول شد. **خاموش می‌ماند تا رأیِ armِ `OCTOPUS_TG_SPLIT_V1`** (کارتِ `VQ-SPLIT-001`).
- **TG-P3/P4/P5:** هنوز اجرا نشده.
