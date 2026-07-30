---
type: prompt
status: ready
tags: [octopus, telegram, tg-p2, two-bot-split, handoff, report]
created: 2026-07-30
updated: 2026-07-30
created_by: agent
sources:
  - "[[TG-FIX-PACK-2026-07-30]]"
  - "[[TG-SPLIT-INNER-OUTER-2026-07-29]]"
  - "[[HANDOFF-PROMPT-2026-07-30]]"
---

# گزارشِ اجرایِ TG-P2 (دو-باتیِ تلگرام) — تحویلِ ۲۰۲۶-۰۷-۳۰

> **به ایجنتِ ارشد:** این سند self-contained است. مالکِ ۲۰۲۶-۰۷-۳۰ این پنج آیتمِ هستهٔ TG-P2 را روی «دنیای A» (center/outer) سفارش داد و گرفتم. فقط «آنچه واقعاً روی دیسک گذاشت، با چه اثباتی» را اینجا می‌آورم تا ایجنتِ بعدی آن را دوباره کشف یا دوباره خراب نکند.

## §A — خلاصهٔ یک‌نگاه

- **برنچ:** `fix/tg-p2-2026-07-30` · **کامیتِ کد:** `70cba70` · **کامیتِ docs:** `9b41f75`
- **دامنه (تصمیمِ مالک):** فقط **دنیای A** (center/outer). دنیای B (organism/inner/approval_channel) دست‌نخورده.
- **پنج آیتم پیاده شد** (آیتم ۶/رسانه موکول شد): surface_router · clientِ فقط-ارسال · DM-safe · per-bot commands · backoff ۴۲۹.
- **تست‌ها:** صفر رگرسیون. `test_tg_surface_router` ۱۲/۱۲ (نو) · `test_tg_api` ۲۴/۲۴ (+۶) · `test_tg_center` ۳۰/۳۰ (+۴). `test_tg_stream_routing`/`approval_store` دست‌نخورده سبز.
- **propose-only:** `OCTOPUS_TG_SPLIT_V1` **خاموش می‌ماند**. فعال‌سازی = رأیِ مالک + کارتِ `VQ-SPLIT-001`.

## §B — حقایقِ راستی‌آزمایی‌شده روی درختِ فعلی (دوباره کشف نکن)

1. **سه لایهٔ روتینگِ متفاوت** وجود دارد، روی دو فلگِ جدا:
   - `approval_channel._stream_route` (فلگِ `ROUTE_FLAG`، **دنیای B**، با تستِ سبزِ `test_tg_stream_routing.py`) — دست‌نخورده.
   - `surface_policy.route` (فلگِ `OCTOPUS_TG_SURFACE_V2`، **دنیای B**) — دست‌نخورده.
   - `surface-routing.json` (نقشهٔ `current`/`target`، **صفر مصرف‌کننده بود**) — حالا `surface_router.py` آن را می‌خواند.
2. **دو دنیای کاملاً مجزا** که هرگز client همدیگر را به اشتراک نمی‌گذارند:
   - **دنیای A (center/outer):** کلاینتِ `tg_api.TgClient`، پروسهٔ `tg-center`، مفهومِ stream **نداشت**، همیشه `(chat_id, topic_id)` از config.
   - **دنیای B (organism/inner):** کلاینتِ `TelegramApprovalChannel` (urllib مستقیم)، پروسهٔ `organism`، `stream=` دارد و `surface_policy.route`/`_stream_route` را اجرا می‌کند.
3. **۴۲۹ کاملاً غایب بود** در کلِ لایهٔ تلگرام (در پاهای غیرتلگرامی مثل pocketsmith/books_xero بود). ۴۰۹ فقط تشخیصِ throttle داشت.
4. `tg_api.TgClient.send` (خط ~۳۴۳) بی‌قید و شرط `message_thread_id` را ست می‌کرد حتی در DM ⇒ ۴۰۰.
5. **هانکِ غریبه کشف و جداسازی شد** (§F): `center.py` یک بلوکِ `tool_request`/`tr` از یک جلسهٔ موازی داشت. فقط هانکِ این کار با `git update-index --cacheinfo` stage شد.

## §C — آیتم‌ها (شاهدِ `file:symbol` + دیف + اثباتِ اثر)

### آیتم ۱ — `surface_router.py` (فایلِ نو)
- **فایل:** `_ops/telegram_center/surface_router.py` · **تست:** `_ops/tests/test_tg_surface_router.py`
- **سمبلِ کلیدی:** `resolve(stream, *, clients, cfg) -> (client, chat_id, topic_id)`
- **رفتار:** از `surface-routing.json` بلوکِ `current` (flag-off) یا `target` (flag-on) را می‌خواند. flag-off = ارسالِ تک-کلاینتِ outer بایت‌به‌بایت. هر شکست → سقوط به outer (نه سکوت). `bot=none` → `(None,None,None)`.
- **جهش‌های قرمزکننده (واقعاً اجراشده):**
  - حذفِ گاردِ DM (`if surface != "group"`) → `t_dm_surface_never_returns_topic_even_with_spec` قرمز (۱۱/۱۲).
  - هاردکدِ bot=outer → ۲ تست قرمز (۹/۱۲).

### آیتم ۲ — کلاینتِ دومِ فقط-ارسال (inner)
- **فایل:** `_ops/telegram_center/center.py` · **سمبل:** `Center._inner_client` / `Center._clients_map`
- **رفتار:** inner روی `TELEGRAM_BOT_TOKEN` ساخته می‌شود (همان توکنِ approval، فقط برایِ send). **هرگز `poll_updates`** (قاعدهٔ ۲ِ TG-SPLIT). نبودِ توکن → `None` + alert، و surface_router به outer سقوط می‌کند.
- **جهش:** inner همیشه None → `t_inner_client_built_from_telegram_bot_token` قرمز (۲۸/۳۰).

### آیتم ۳ — DM-safe (message_thread_id)
- **فایل:** `_ops/telegram_center/tg_api.py` · **سمبل:** `TgClient.send` (~خط ۳۴۳)
- **تغییر:** `if topic_id is not None and isinstance(cid, int) and cid < -1000:` — فقط روی سوپرگروهِ forum. قانون: سوپرگروه‌ها همیشه `chat_id < -1000`؛ DM/چتِ خصوصی `≥ ۰`.
- **جهش:** حذفِ `cid < -1000` → `t_c2_send_to_dm_never_sets_message_thread_id` قرمز (۱۸/۱۹).

### آیتم ۴ — setMyCommands per-bot
- **فایل:** `_ops/telegram_center/center.py` · **سمبل:** `COMMANDS_INNER` (ثابت) + `ensure_setup`
- **رفتار:** `COMMANDS_OUTER` (= `COMMANDS` امروز) + `COMMANDS_INNER` (کوچک). flag-off → فقط outer (پاریتیِ امروز). flag-on → هر بات منویِ خودش، با پرچمِ جداگانهٔ `commands_set_inner`.
- **جهش:** inner هم `COMMANDS` بگیرد → `t_set_my_commands_per_bot_under_split` قرمز (۲۹/۳۰).

### آیتم ۵ — backoff ۴۲۹ (همیشه روشن، تصمیمِ مالک)
- **فایل:** `_ops/telegram_center/tg_api.py` · **سمبل‌ها:** `_call_post` + `poll_updates` + `_retry_after_from_429` + `_http_err_json` + `self._sleep` (تزریقی)
- **رفتار:** پاسخِ `{"ok": False, "error_code": 429, "parameters": {"retry_after": N}}` → `min(N, 30)` ثانیه sleep + **یک** retry (نه storm). سقفِ ۳۰s ضدِ سوءاستفاده. fail-soft دست‌نخورده. **تصمیمِ مالک:** همیشه روشن (نه flag-gated) — ۴۲۹ باگِ واقعی است.
- **تله‌ای که رفع شد:** `_http_err_desc` و `_http_err_json` از یک `HTTPError` می‌خواندند؛ بدنه یک stream است و دوبار `read()` دفعهٔ دوم خالی بود ⇒ `t_z_edit_not_modified` رگرسیون داد. اصلاح: یک‌بار JSON خوانده، هر دو از آن محاسبه شد.
- **جهش:** حذفِ retry (`range(1)`) → ۲ تست قرمز (۲۱/۲۳).

### آیتم ۶ — رسانه (photo/voice): **موفّق به جلسهٔ بعد**
سند خودش «اختیاری» است. پنج آیتمِ هسته کامل و تست‌شده تحویل شد تا فشارِ محدوده پایین بماند.

## §D — رگرسیون (gate = `candidate.failed ⊆ baseline.failed`)

| سوئیت | baseline | بعدِ کار | جهش‌ها |
|---|---|---|---|
| `test_tg_api` | ۱۸/۱۸ | **۲۴/۲۴** (+۶) | ۴ جهش قرمز شد |
| `test_tg_center` | ۲۶/۲۶ | **۳۰/۳۰** (+۴) | ۳ جهش قرمز شد |
| `test_tg_surface_router` | — | **۱۲/۱۲** (نو) | ۲ جهش قرمز شد |
| `test_tg_stream_routing` | ۱۰/۱۰ | **۱۰/۱۰** (دست‌نخورده) | — |
| `test_tg_approval_store` | ۱۴/۱۴ | **۱۴/۱۴** (دست‌نخورده) | — |
| frontmatter validator | ۴۱۷/۴۱۷ | **۴۱۷/۴۱۷** | — |
| broken_links | ۷۷ | **۷۷** (صفر رگرسیون؛ خطاها پیش‌موجود در `obsidian/`) | — |

## §E — رأیِ مالک لازم است (خودم نزدم، فقط کارت)

- **`OCTOPUS_TG_SPLIT_V1` خاموش می‌ماند.** فعال‌سازی: `OWNER_AUTH: ARM FLAG OCTOPUS_TG_SPLIT_V1`. **پیش از arm، ستونِ `target` در `surface-routing.json` را بازبینی کن** — الان `target` بدون رأی فعال نمی‌شود ولی مقصدِ مصوب در آن است.
- کارت: `VQ-SPLIT-001` در `VERDICT_QUEUE.md` (به‌روز شد: «سیم‌کشی انجام شد، فقط arm ماند»).
- `VQ-SPLIT-002` **بسته شد**: نامِ env مشخص شد = `TELEGRAM_BOT_TOKEN`.

## §F — هانکِ غریبه (درسِ عملیاتی مهم)

`center.py` یک بلوکِ `tool_request`/verb `tr` (~۴۸ خط) داشت که **مالِ یک جلسهٔ موازی** بود (کارِ ناتمامِ دیگر، بدونِ تست). فقط هانکِ این کار با الگویِ `git update-index --cacheinfo 100644,<sha>,<path>` stage شد؛ هانکِ غریبه **دست‌نخورده** در working tree ماند. تأیید: staged diff صفر `tool_request` دارد، working diff هنوز ۴۸ خط دارد. EOL محترم شد (`center.py` = CRLF، `tg_api.py` = LF).

**درس:** هر فایلِ ویرایش‌شده را قبل از stage با `git diff -- <file>` بازبینی کن؛ اگر هانکِ غریبه داری، آن را با بلبِ تمیز از ایندکس عبور بده، نه با `git add`.

## §G — کارِ باز (ایجنتِ بعدی)

۱. **آرم کردنِ `OCTOPUS_TG_SPLIT_V1`** (رأیِ مالک) — بعد از بازبینیِ ستونِ `target`.
۲. **آیتم ۶ (رسانه)** در `_handle_message` (~خط ۷۳۵) — photo/voice/caption. اختیاری.
۳. **به canonical بردنِ این برنچ** (`fix/tg-p2-2026-07-30`) با worktreeِ تمیز، نه merge روی درختِ کثیف.

⚠️ این پرامپت به تو اجازهٔ **هیچ** تغییرِ رفتارِ بیشتر، آرمِ فلگ، merge، ری‌استارت، ارسالِ بیرونی یا خرجِ پول نمی‌دهد. اگر جایی احساس کردی «این را باید همین الان درست کنم» — پچش را در گزارش بنویس و به مالک بده.
