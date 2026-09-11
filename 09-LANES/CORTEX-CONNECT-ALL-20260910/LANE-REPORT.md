GOV_VERSION=V8
LADDER=L2

# CORTEX-CONNECT-ALL-20260910 — سرنوشتِ کلیکِ 732409706 + چهار اتصالِ مغز (ساختِ محلی)

lane: `09-LANES/CORTEX-CONNECT-ALL-20260910/` · worktree: `F:/wt-cortex-connect-all-20260910` (شاخهٔ `codex/cortex-connect-all-20260910` از `1f941fe`؛ ایندکس=HEAD، فقط `_ops` + `AGENTS.md` بیرون کشیده شده؛ ۴۴٬۰۳۳ حذفِ unstaged هرگز stage نشده). مالکیت: فقط این پوشه + ۳ فایلِ فاز ۱ + ۷ فایلِ فاز ۲ (همه commit با مسیرِ صریح). هیچ فلگِ wire، هیچ راز، هیچ تماسِ تلگرام/پولی، هیچ ری‌استارت.

## ۱. سرنوشتِ کلیکِ مالک — update_id=732409706 (اول این)

**خلاصهٔ یک‌خطی:** کلیک رسید و حلقهٔ poll تا انتها رفت؛ به دکمه‌ای خورد که روی باتِ درونی handler نداشت؛ پاسخِ **استنباطی** (بدونِ رسیدِ مستقیم — مسیرِ موفقِ ACK هیچ ردیفی نمی‌نویسد) toastِ «نادیده» است و هیچ اثری ذخیره نشد. این یک دکمهٔ مردهٔ **ثبت‌شده از ۲۰۲۶-۰۸-۰۶** بود که در تستِ parity معاف شده بود. (اصلاحِ ۰۹-۱۱: نسخهٔ اولِ این خط «جوابش toast نادیده بود» را قطعی نوشته بود؛ شواهد فقط تا INFERRED می‌رسند.)

وضعیت‌های مستقل (منبع: `CLICK-TRACE.json` همین پوشه):

| حلقه | وضعیت | شاهدِ کلیدی |
|---|---|---|
| received | **CONFIRMED** | `_ops/state/telegram/inbound-log.jsonl` خط ۳۷؛ نویسنده = `approval_channel.py:667-690` (`poll_once`، literal `"bot": "inner"`) که در threadِ `organism.py:409` می‌دود. نبضِ همان poller در `pulse/telegram-poll.json` = 20:35:29 (۷ دقیقه بعد از کلیک) |
| dispatched | INFERRED | `telegram_offset.json` = 732409707 با mtime 20:28:32.976 (+۱٫۵ ثانیه) = ذخیرهٔ پایانِ حلقه (`:756-757`)؛ allowlist شاملِ مالک (`:339-341`)؛ هیچ هشدارِ `T-8 dispatch error` بین 20:21:58 و 20:37:54 در `_ops/governor/governor-alerts.md` |
| handler | INFERRED_STRONG → **هیچ (fallthrough «نادیده»)** | callback ۷ کاراکتر؛ تنها کیبوردِ ارسالی از باتِ درونی با callbackِ ۷کاراکتری = `initiative.card()` → `mr:know` («🪞 آینه»، `initiative.py:501-502`)، فرستنده `organism.py:915-916` از `_chan.send_text`. زنجیرهٔ زمانی: `initiative.jsonl` کارتِ «سوال» id=8186ef67275e در **20:22:06** → ردیفِ ارسالِ inner در `tg-send-log.jsonl` **20:22:08** (۶۱۵ کاراکتر، sent) → کلیک **20:28:31**. `dispatch_callback` پیش از وصله scheme `mr` نداشت (`:1144`). گزینهٔ دیگرِ ۷کاراکتری `tr:list` فقط از مرکز (`center.py:4482`) می‌رود → حذف |
| acknowledged | INFERRED_NO_ERROR | `_answer_callback_query` بی‌قید صدا زده می‌شود (`:731-732`)؛ شکست هشدار می‌دهد (`:780`)؛ آخرین چنین هشداری 2026-09-07T10:03:20. مسیرِ موفق **هیچ رسیدی** نمی‌نویسد → CONFIRMED نمی‌شود. toastِ استنباطی: «نادیده» |
| effect_persisted | **NONE** | ساختاری (بدونِ handler)؛ روی دیسک: در بازهٔ 20:27:30–20:30:00 در کلِ `_ops` فقط `inbound-log.jsonl` و `telegram_offset.json` تغییر کرده‌اند. (اسکنِ همان بازه در `F:/ofn-node` ناتمام ماند → UNKNOWN آن‌جا) |
| read_back | N/A | چیزی برای بازخوانی نیست. تأییدِ جانبی: کلیکِ ۷کاراکتریِ قبلی 732409705 (09-09 16:10:59) روی کارتِ 28b14a9f8068 → همان لجر در 21:38:46 آن را `ignored / window-elapsed` بست (سیستم صفر engagement دید) |
| گروهِ کنترل | **CONFIRMED** | سه کلیکِ ۱۷کاراکتریِ 09-09 (732409702/3/4) هر یک در **همان ثانیه** ردیفِ `tool_request.v1.answer / granted` در `tool-requests.jsonl` ساخته‌اند → مسیرِ inner برای `tr:*` تا ذخیره‌سازی سالم است |

**متنِ callback به‌طورِ طراحی‌شده UNKNOWN است** (§۱۰: لاگِ ورودی فقط شکل/طول). شناساییِ `mr:know` استنباطِ قوی از طول + کارتِ ارسالی + زمان‌بندی + نبودِ اثر است، نه خواندنِ متن.

**ریشه:** `_ops/tests/test_tg_callback_emitter_parity.py:68-81` — `KNOWN_OPEN_GAPS[("initiative.py","mr")]`، ثبت‌شده ۲۰۲۶-۰۸-۰۶ با متنِ «تلهٔ دو-باتی، زنده و هنوز رفع‌نشده، TODO مالک». تست ۹/۹ سبز می‌ماند در حالی که مالک ۳۵ روز «نادیده» می‌گرفت.

**هم‌زمانیِ چند نویسنده:** ادعا **نمی‌شود**. یک poller ِ inner زنده (نبض)، هیچ 409 در بازه، توکن باز نشد.

**دامنهٔ poll-health (بندِ ۴ پرامپت):** `poll-health.json` را فقط `telegram_center/health_metrics.py` و `tg_api.py` (باتِ **بیرونی/مرکز**) می‌نویسند؛ مصرف‌کننده‌ها `seed_beat`/`config_manager`/`durable_loop`/`self_insight`/`self_audit`. `approval_channel.py` صفر ارجاع. پس `last_update_received_at`/`last_dispatch_completed_at` ِ کهنه = حقایقِ باتِ بیرونی، **نه** شاهدی دربارهٔ کلیکِ inner. وصله‌ای روی poll-health زده نشد (ایرادِ کد ثابت نشد). شکافِ واقعی: poller ِ inner فقط نبض (ts+batch) دارد و هیچ رسیدِ dispatch/ACK نمی‌نویسد — همین است که «acknowledged» را از CONFIRMED پایین نگه می‌دارد (قدمِ بعدیِ پیشنهادی، نه وصلهٔ این لِین).

### وصلهٔ حداقلی (فاز ۱) — commit `5685b89`، LOCAL_TESTED
- `_ops/budget/approval_channel.py` (+۴۷): `_mirror_room_mod()` (هم‌الگوی `load_surface_policy`)، شاخهٔ `mr` در `dispatch_callback` کنارِ `iv`/`tr`، و `_dispatch_mirror()`: `mr:know` → `mirror_room.know_card()`، `mr:corr` → `corrections_card()` (هر دو read-only، $0، بدونِ مدل، بدونِ state)؛ فلگِ خاموش/نبودِ ماژول/خطا → toastِ توضیح‌دار، **هرگز «نادیده»**. sha256: pre `4b77da64…dfada` → post `39965142…8e5b`.
- `_ops/tests/test_inner_mirror_callback.py` (نو، ۸ سنجه، transport جعلی، بدونِ شبکه): شکلِ ردیفِ دریافت == ردیفِ مالک، ACK، sendMessage، مهرِ `update_id` روی رسیدِ ارسالِ inner، fail-soft در خطای handler، ادامهٔ batch پس از خطای dispatch با هشدار، پاریتیِ رفتاریِ همهٔ دکمه‌های `initiative.card()`. **قرمز ۲/۸ پیش از وصله** (toast دقیقاً `{'callback_query_id': 'cbq732409706', 'text': 'نادیده'}`) → **سبز ۸/۸**.
- `_ops/tests/test_tg_callback_emitter_parity.py`: معافیت حذف شد (خودِ تست حذفِ معافیتِ بی‌مصرف را اجبار می‌کند) → ۹/۹.
- همسایه‌ها: `test_telegram_poll_e2e` 7/7 · `test_both_bots_log_inbound` 9/9 · `test_tg_callback_answer` 5/5 · `test_phase0_receipt_rig` 15/17 — دو شکستِ `t_g`/`t_p` **عیناً روی baseline ِ وصله‌نخورده** هم هست (سمتِ مرکز) → رگرسیونِ این لِین نیست.
- **کلیک دوباره پخش نشد. ری‌استارت نشد.** ارگانیسمِ زنده تا ری‌استارت کدِ قدیمی را می‌دود؛ دکمهٔ «🪞 آینه» در تلگرام هم‌چنان «نادیده» می‌دهد.

## ۲. اتصال‌های مغز (فاز ۲) — commit `81835fa`، LOCAL_TESTED، ۱۴/۱۴

پیش‌نیازِ ادعاهای LIVE مگاپرامپت: `CORTEX-DEPLOY-RECEIPT.json` / `OWNER-VOTE-RESTART-20260910` در جستجوی محدود (`09-LANES`, `07-HANDOFF`, `06-EVIDENCE`, `_ops` تا عمقِ ۳) **پیدا نشد** (E0 در این دامنه؛ ادعای غیاب سراسری نیست). ولی قراردادِ لجر خودش زنده است (E2): `paid-calls.jsonl` فیلدِ `burned_without_output` دارد (۱۶ ردیف در ۳۰۰ ردیفِ آخر) و `model_router.py:454-465` آن را می‌نویسد. PID 10416 در این لِین دوباره تأیید نشد.

سطحِ API واقعی (خوانده‌شده): `model_router.ask(task, prompt, system, max_tokens, tier) -> dict{ok,text,tier,fallback_from,finish_reason,model,reason}`؛ **`customer_reply` در `TASK_TIERS` نیست** و task ِ ناشناخته به `local` می‌افتد → wrapper همیشه `tier="secondary"` را صریح می‌دهد (به‌جای ویرایشِ ماژولِ زنده). `is_useless_truncation(text, finish_reason)` عیناً مصرف شد. `fugu_quota.reserve` داخلِ `_ask_impl` است؛ سقفِ روزانهٔ این اتصال‌ها **اضافه** بر آن است.

| # | اتصال | ماژول | trigger/seam واقعی | consumer | storage | fallback |
|---|---|---|---|---|---|---|
| ۰ | اسکرابرِ راز | `_ops/cortex/scrub.py` | پیش از هر `ask` و هر لاگ | `brain_link` | — | — |
| ۰ | درِ واحد | `_ops/cortex/brain_link.py` | همهٔ اتصال‌ها | `model_router.ask` (تنها مسیر) | `state/cortex/connect-calls.jsonl` (sha، نه متن) + `connect-daily.json` | `ok=False + reason` |
| ۱ | پیامِ مشتری | `_ops/legs/store_reply.py` | `drive_loops.sync_store_watch()` → `state/store-watch.json` (فقط **سفارش** دارد: `orders.last_order_id`؛ پیامِ متنیِ مشتری در watch نیست) — `event_from_store_watch(prev,cur)` | مالک: کارتِ **متنی** از باتِ درونی (`propose(row, channel)`) | `state/store/replies.jsonl` (`sent=false`, `delivery=null`, `production_authorized=false`) | قالبِ ثابتِ محافظه‌کارانه، هرگز سکوت؛ فیلترِ واژگانِ ممنوعه |
| ۲ | غربالِ لید | `_ops/legs/lead_triage.py` | dictِ لید (`description`,`address` مثلِ `lead_scorer._haystack` + `score` از intake v2). مسیرِ فایلِ intake روی ۱۳۸: **UNKNOWN** | `lead_pipeline._card_text` (خطِ `card_line(row)`) | `state/leads/triage.jsonl` (`queued_for_owner`, `decided=false`) | قاعدهٔ score (≥70 high / ≥40 medium / low) با `fallback=true` |
| ۳ | hero/محتوا | `_ops/legs/content_draft.py` | brief از مالک | مالک انتخاب می‌کند؛ `publish()` **همیشه** `PermissionError` | `state/content/hero-drafts.jsonl` (`published=false`) | هیچ پیش‌نویسِ جعلی؛ `ok=false` |
| ۴ | digestِ مالک | `_ops/legs/owner_digest.py` | `wiring.brain_digest_beat`/`doctor_digest_beat` پیش از `_send_stream` (`d["text"]`) | همان ارسالِ موجود | `state/cortex/digest-summaries.jsonl` (sha) | همان متنِ خام برمی‌گردد |

قواعدِ اجراشده: task صریح در هر ردیف · اسکرابر روی prompt/system **و خروجیِ مدل** · تکرارِ رویداد ⇒ همان ردیف، بدونِ تماسِ دوم · سقفِ روزانه attempt-counted و fail-closed **پیش از** تماس · کارت‌ها بدونِ verbِ callbackِ تازه (تا دکمهٔ مردهٔ پنجم ساخته نشود؛ parity ۹/۹ ماند).

تست `_ops/tests/test_cortex_connect_all.py` (۱۴/۱۴): socket مسدود (هر connect = AssertionError؛ صفر تلاش)؛ قرمز → سبز برای راز (تابعِ خام توکنِ ساختگی را می‌گیرد؛ از `brain_link` فقط `[REDACTED]`) و برای سکوت (مغز None → قالب)؛ ماتریسِ شکست (exception/None/غیر-dict/ok=false/غیرپولی/بریدهٔ بی‌متن/خالی)؛ بریدهٔ طولانی می‌گذرد؛ سقف پیش از تماس؛ replay؛ واژهٔ ممنوعه؛ `publish` می‌شکند؛ هیچ مقدارِ ساختگی در هیچ لاگِ sandbox؛ هیچ `paid-calls.jsonl` در sandbox؛ هیچ نوشتنی زیرِ `F:/backup`.

**به production وصل نشد** (هیچ صداکنندهٔ زنده‌ای ویرایش نشد): splice ِ هر اتصال = یک تغییرِ رفتارِ ارسال/تصمیمِ زنده و پشتِ گیت. رسیدِ `paid-calls.jsonl` برای taskهای تازه فقط پس از splice و اولین تماسِ واقعی پدید می‌آید (**NOT_RUN**).

## ۳. چه ماند / چه شکست
- **شکست/ناتمام:** اسکنِ فایل‌های تغییریافتهٔ بازهٔ کلیک در `F:/ofn-node` کشته شد (زمان) → آن سمت UNKNOWN. تستِ طلاییِ H9 با این نام در `_ops/tests` پیدا نشد (فقط ارجاعِ `H9` در `three_role.py`)؛ هیچ فایلِ حافظه/`three_role.py` لمس نشده (`git show --stat 5685b89 81835fa`).
- **باز (unverified):** PID ِ میزبانِ poller ِ inner در این لِین؛ رسیدِ مثبتِ ACK (ساختاری وجود ندارد)؛ مسیرِ فایلِ intake روی ۱۳۸؛ محلِ واقعیِ `CORTEX-DEPLOY-RECEIPT.json`.
- **قدمِ بعدی (به ترتیب):**
  1. **انتقالِ وصله به مسیرِ اجراییِ تأییدشده (اصلاحِ ۰۹-۱۱ — ری‌استارت به‌تنهایی وصله را فعال نمی‌کند):** ارگانیسم از `F:\backup\_ops` بار می‌شود؛ `approval_channel.py` آن‌جا هنوز `4b77da64…` است و نسخهٔ وصله‌شده (`39965142…`) فقط در worktree است. پس ابتدا merge/cherry-pick ِ شاخهٔ `codex/cortex-connect-all-20260910` به درختِ زندهٔ `F:/backup` (خودش تغییرِ کدِ زنده = گیت‌دار)، با sha ِ پس‌از‌انتقال به‌عنوانِ رسید.
  2. **ری‌استارتِ ارگانیسم (کلاس Z، رأیِ مالک):** `_ops/RESTART-ORGANISM.bat` (detached) تا ماژولِ تازه بار شود؛ رسید = هشِ `approval_channel.py` ِ بارشده در process-identity/startup record == `39965142…`.
  3. **اثباتِ زنده با یک کلیکِ تازهٔ مالک** روی کارتِ initiative → ردیفِ inner با `update_id` در `tg-send-log.jsonl` (تا امروز صفر ردیفِ inner با `update_id` در ۴۸ ساعت) + پیامِ «فهمِ من از خودم» (اگر `OCTOPUS_TG_MIRROR=1`) یا toastِ «خاموش است» (فلگ خاموش). تا پیش از ۱→۲→۳، دکمهٔ «🪞 آینه» هم‌چنان «نادیده» می‌دهد.
  4. رسیدِ disposition برای poller ِ inner (هم‌قراردادِ `center._log_disposition`، همان فایل، `update_id` مشترک) — تا ردیابیِ بعدی CONFIRMED باشد نه INFERRED.
  5. روشن‌کردنِ اتصال‌ها (دورِ دومِ ۰۹-۱۱ splice ِ هر سه caller را **پشتِ فلگِ پیش‌فرض-خاموش** انجام داد؛ روشن‌کردن = رأیِ جدا برای هر فلگ + ری‌استارت): `OCTOPUS_CONNECT_STORE_REPLY` (drive_loops.sync_store_watch → پیش‌نویس؛ organism epoch → کارتِ مالک) · `OCTOPUS_CONNECT_LEAD_TRIAGE` (lead_pipeline._card_text) · `OCTOPUS_CONNECT_OWNER_DIGEST` (wiring.brain_digest_beat، خودش پشتِ OCTOPUS_WIRE_BRAIN_DIGEST). `content_draft` فقط با brief ِ مالک، بدونِ caller ِ خودکار. اولین ارسالِ واقعی به مشتری = کارتِ یک‌تصمیمیِ مالک (این کد هیچ transportی به مشتری ندارد).
- **ادغام:** این شاخه از `1f941fe` جدا شده؛ `F:/backup` هم‌زمان توسطِ ایجنت‌های دیگر جلو می‌رود → rebase/merge پیش از هر استقرار؛ PR/push انجام نشده.

## ۴. شواهد
- `09-LANES/CORTEX-CONNECT-ALL-20260910/CLICK-TRACE.json` (همین پوشه)
- ورودی‌ها: `F:/wt-tg-claim-audit-20260910/09-LANES/TG-CLAIM-AUDIT-20260910/{LANE-REPORT.md,CLICK-OBSERVATION.json,NEXT-AGENT-PROMPT.md}` · `F:/backup/07-HANDOFF/MEGAPROMPT-CORTEX-CONNECT-ALL-2026-09-10.md` (untracked در git)
- state ِ خوانده‌شده (فقط‌خواندنی): `_ops/state/telegram/{inbound-log.jsonl,initiative.jsonl,tool-requests.jsonl,poll-health.json}`, `_ops/state/telegram_offset.json`, `_ops/state/pulse/telegram-poll.json`, `_ops/state/tg-send-log.jsonl`, `_ops/state/paid-calls.jsonl`, `_ops/state/store-watch.json`, `_ops/governor/governor-alerts.md`
- کد: `_ops/budget/approval_channel.py` (:329-351, :574-758, :766-781, :1006-1144), `_ops/organism.py:409,912-932`, `_ops/initiative.py:501-502`, `_ops/tool_request.py:267,537-555`, `_ops/telegram_center/{center.py:4254-4267,4482; mirror_room.py:407-460; health_metrics.py}`, `_ops/tests/{test_tg_callback_emitter_parity.py,tg_callback_scanner.py}`, `_ops/cortex/model_router.py (:153,:239,:807)`, `_ops/cortex/fugu_quota.py:290`, `_ops/wiring.py:4292`, `_ops/legs/{lead_scorer.py:289,lead_pipeline.py}`
- commitها (worktree): `5685b89` (فاز ۱)، `81835fa` (فاز ۲)، + commit ِ همین گزارش

## ۵. rollback
- کد: `git -C F:/wt-cortex-connect-all-20260910 revert <commitهای این شاخه، جدید به قدیم>` (5685b89، 81835fa، f22bdcb و commit ِ دورِ دوم) یا حذفِ شاخه؛ `F:/backup` هیچ تغییری نگرفته (worktree مستقل). worktree: `git worktree remove F:/wt-cortex-connect-all-20260910` (پس از merge/آرشیو).
- runtime: چیزی تغییر نکرده — هیچ ری‌استارت/فلگ/ارسال/state ِ زنده. فایل‌های state فقط خوانده شدند.
- تست‌ها فقط در sandbox ِ harness نوشتند (`t_h`/`t_m` هر دو فایل این را assert می‌کنند).

## ۶. بازبینیِ ۰۹-۱۱ (فقط‌خواندنی، توسطِ ایجنتِ بازبین) → دورِ دوم — commit بعدی

**پذیرفته‌شده و اصلاح‌شده:**
- **ادعای فراتر از شاهد:** «toast نادیده نمایش داده شد» قطعی نوشته شده بود؛ ACK رسیدِ مستقیم ندارد و متنِ callback ذخیره نمی‌شود → در §۱ به INFERRED برگردانده شد (CLICK-TRACE از ابتدا INFERRED_NO_ERROR بود).
- **ری‌استارت ≠ فعال‌سازی:** مسیرِ اجرایی `F:/backup/_ops` است (هشِ زنده `4b77da64…`)؛ وصله فقط در worktree است (`39965142…`). ترتیبِ گیت در §۳ اصلاح شد: انتقال → ری‌استارت → کلیکِ تازه.
- **سه شکافِ `brain_link.py` (هر سه واقعی؛ تست‌های دورِ اول آن‌ها را نمی‌گرفتند چون فیک‌ها همیشه tier داشتند و reason بی‌راز بود):**
  1. مسیرِ خطا اسکرابر را دور می‌زد (`reason` ِ router خام به رسید می‌رفت) → `_clean()`: هر رشتهٔ بیرونی (reason/tier/model) پیش از رسید **و** پیش از بازگشت اسکراب می‌شود. تست `t_o`.
  2. `_receipt()` خطای نوشتن را می‌بلعید و `ok=True` برمی‌گشت → حالا bool برمی‌گرداند؛ مسیرِ موفق بدونِ رسید = `ok=False, reason=receipt-io-failclosed, receipt_ok=False` (هم‌فلسفهٔ fugu_quota: I/O شکست ⇒ اجازه نه)؛ مصرف‌کننده fallback می‌دهد. تست `t_p` (شاملِ store_reply روی همین شکست).
  3. tierِ خالی پذیرفته می‌شد → فقط `primary/secondary` صریح عبور می‌کند؛ None/""/"unknown" = `not-a-paid-brain`. تست `t_q`.
  `test_cortex_connect_all`: ۱۴/۱۴ → **۱۸/۱۸** (+ `t_z` جاروی نهاییِ راز).
- **consumerها وصل نبودند** → هر سه caller ِ واقعی splice شد، همه پشتِ فلگِ **پیش‌فرض-خاموش** (هیچ `OCTOPUS_WIRE_*` لمس نشد؛ با فلگِ خاموش رفتارِ production بایت‌به‌بایت قبلی است):
  - `drive_loops.sync_store_watch` → `_maybe_store_reply(prev_raw, cur_raw)` (snapshot ِ قبلی پیش از بازنویسی نگه داشته می‌شود) → `store_reply.draft_reply` → `state/store/replies.jsonl`.
  - `organism.py` epoch (کنارِ بلوکِ tool_request، همان‌جا که `_chan` هست) → `store_reply.propose_pending(_chan)` → کارتِ **متنی** به مالک، هر پیش‌نویس فقط یک‌بار (ردیفِ `store_reply.v1.proposed`، append-only)؛ `sent` هرگز True نمی‌شود.
  - `lead_pipeline._card_text` → `_triage_line(lead_id, sc)` → `lead_triage.triage(sc.lead)` → یک خطِ اولویت در کارتِ مالک.
  - `wiring.brain_digest_beat` → `_digest_text_with_brain(d["text"])` **بعد از** `_dialogue_gate` و پیش از `_send_stream` (تماسِ پولی برای digest ِ فرستاده‌نشده = سوختن).
  تستِ مسیرِ کامل `tests/test_cortex_connect_callers.py` **۱۰/۱۰**: ssh جعلی (`subprocess.run`)، `model_router.ask` جعلی در سطحِ ماژول (همان seam ِ brain_link)، socket مسدود، فلگ خاموش ⇒ صفر اثر/صفر تماس، سفارشِ جدید ⇒ ردیف + تماس با task/tier/max_tokens درست، idempotent، خطای router در caller ⇒ قالب نه سکوت، کارتِ مالک دقیقاً یک‌بار و هرگز به مشتری، کانالِ ناموفق ⇒ تلاشِ دوباره، AST: بلوکِ organism پشتِ `enabled()` و داخلِ try؛ splice ِ digest بعد از گیت. `drive_loops.STATE` (نسبت به فایل، نه opslib) در تست به دایرکتوریِ موقت monkeypatch شد.

**رگرسیون (کدِ وصله‌شده):** organ_dialogue rc=0 · debate_owner_verdict 15/15 · parity 9/9 · inner_mirror 8/8 · lead_card_wiring 6/6 · lead_processed_fallback 6/6 · lead_scorer_farsi 11/11 · lowrisk_and_brier 19/19 · **lead_pipeline 7/7** — این آخری در worktree ابتدا با `ModuleNotFoundError: mail_credentials` می‌شکست: `_ops/legs/mail_credentials.py` روی دیسکِ زنده هست ولی در `.gitignore:278` است ⇒ در **هیچ** worktree ِ تازه‌ای وجود ندارد (وابستگیِ زندهٔ خارج از git — همان کلاسِ خطرِ قانونِ سه‌سطحیِ غیبت). فایلی با این نام کپی نشد؛ فقط برای همان پروسهٔ تست یک stub ِ بی‌راز در دایرکتوریِ موقت (خارج از worktree، حذف‌شده) روی PYTHONPATH گذاشته شد → ۷/۷.

**هنوز باز / تغییرنکرده:** ACK همچنان بدونِ رسیدِ مثبت (قدمِ ۴)؛ `paid-calls.jsonl` برای taskهای تازه NOT_RUN تا splice روشن شود؛ هیچ انتقال/ری‌استارت/ارسال/انتشار انجام نشد. **وضعیت: LOCAL_TESTED — «آمادهٔ اجرای زنده» اعلام نمی‌شود.**

## ۷. ۱۱-۰۹ صبح (۰۹:۳۰ محلی) — تأییدِ مستقلِ استقرارِ آینه + OP-3 با دادهٔ واقعی

**استقرار (گزارشِ ایجنتِ NEXT-20260911-MIRROR، بازبینی‌شده از runtime/repo، نه از متنِ گزارش):** `F:/backup` HEAD = `42d3085` (cherry-pick ِ دقیقِ 5685b89؛ همان ۳ فایل، +315/−12، 09:09:58) روی `cbe029d`؛ `_ops/budget/approval_channel.py` زنده = `399651420bdd2c75…` (== نسخهٔ آزموده)؛ PID 23708 روی `127.0.0.1:8771` LISTENING؛ نبضِ poller ِ درونی 09:27:25 (تازه، پس از ری‌استارتِ 09:12:20)؛ `RUN-ORGANISM.bat` فایلِ `OCTOPUS-flags.cmd` را source می‌کند و آن‌جا `OCTOPUS_TG_MIRROR=1` است (خط ۶۲۳) ⇒ فرایندِ جدید فلگِ آینه را روشن دارد. **کلیکِ تازهٔ مالک هنوز نرسیده** (آخرین ردیفِ inbound همچنان 732409709). انتظارِ دقیق برای کلیکِ بعدی روی «🪞 آینه»: answerCallbackQuery «✅» + یک پیامِ **نو** «🪞 فهمِ من از خودم — نسخهٔ …» در همان چت + برای اولین بار یک ردیفِ `bot_role=inner` با `update_id` در `tg-send-log.jsonl` (اثباتِ مثبت). اگر به‌جای پیام فقط toast دیدید = فلگ در فرایند خاموش است (بررسیِ env)؛ اگر «نادیده» = کدِ قدیمی هنوز بار است.

**OP-3 — ریشهٔ سوختِ مغزِ پولی (فقط‌خواندنی، `paid-calls.jsonl` از deploy ِ صداقت ۱۰-۰۹ 16:53 تا 09:13):** ۳۶۶ ردیف: **۱۱۷ سوخته / ۸۷ موفق** (۱۶۲ ردیفِ دیگر = رد/تعویق بدونِ تماس). سوخته به تفکیکِ task: synthesize ۵۴ (**۶۷٫۵٪** از تماس‌هایش)، deep ۵۱ (۵۸٫۶٪)، summarize ۵ (۵۰٪)، plan ۳، orchestrate ۳ (۱۵٪). سقفِ توکنی که سوخته به آن خورده: **۷۰۰ ×۳۷** (= `initiative.py`/`tool_request.py` MAX_TOKENS=700، task deep) · **۸۰۰ ×۳۵** (تولیدکننده‌های synthesize: doctor/chamber، self_knowledge) · **۲۰۰۰ ×۱۸ + ۱۷۵۰ ×۱۰** (= retry ِ «بودجهٔ صریح» که **باز هم می‌سوزد**: ۲۹ retry سوخته در برابر ۵۹ retry موفق) · ۱۲۰۰ ×۵ (deep_think) · ۲۲۰ ×۵. همه `role=reason` = `deepseek-v4-flash` در حالتِ thinking (هر دو tier؛ `_TIER_ROLE` هر دو را به reason می‌برد). تماس‌های **موفق** هم میانهٔ tokens_out=۱۳۲۶ برای میانهٔ chars_out=۳۹۵ دارند ⇒ ~۹۰۰ توکنِ تفکرِ پنهان در هر پاسخِ سالم. تأخیر یکسان (میانه ~۵s) ⇒ سوخت = برخورد به سقف، نه timeout. **هزینه: سوخته $0.073 > موفق $0.064** — بیش از نیمی از خرجِ پولی از deploy هیچ متنی نداده. کد عمداً پارامترِ thinking اختراع نمی‌کند (`model_router.py:510`).
**گزینه‌ها برای کارتِ مالک (یک تصمیم، ≤۳ گزینه؛ هیچ تغییری تا رأی):**
1. **سقفِ پایه را بالا ببر** (initiative/tool_request 700→≥1500؛ synthesize 800→≥1500) و retry ِ دوم را حذف کن — با همین لجر: زنجیرهٔ فعلیِ «سوختِ ۷۰۰ + retry ۲۰۰۰» = ۲۷۰۰ توکن وقتی retry موفق است؛ یک تماسِ ۱۵۰۰ی ارزان‌تر است اگر نرخِ سوختش زیرِ ~۴۰٪ بماند — **باید اندازه‌گیری شود** (یک روز، با سقفِ روزانه)، فرضِ بی‌شاهد نمی‌کنیم.
2. **taskهای کوتاه (summarize/synthesize کوتاه/triage) را به roleِ غیر-thinking ببر** (budgets.yaml role های `routing`/glm-4.6 موجودند؛ کدام‌شان thinking ندارد باید از خودِ پاسخ‌های لجر/مستندِ provider تأیید شود، نه حدس).
3. **پارامترِ خاموش‌کردنِ thinking برای provider** — تغییرِ client (قاعدهٔ «اختراع نکن» ⇒ فقط با مستندِ رسمیِ provider + تستِ قرمز از ردیف‌های واقعی).

## ۸. ۱۱-۰۹ 15:13 — اثباتِ زندهٔ آینه (پایانِ OP-1)

کلیکِ تازهٔ مالک روی «🪞 آینه»: **update_id 732409713 @ 15:10:17** → کارتِ «فهمِ من از خودم» (اسکرین‌شات مالک، هم‌زمان 3:10 PM) → **اولین ردیفِ inner با `update_id` در تاریخِ tg-send-log** (414 کاراکتر، ok، sent، dm، 15:10:23.707) → offset همان ثانیه 732409714. جزئیات: `CLICK-TRACE-2.json`. دکمهٔ مردهٔ ۳۵ روزه، سر تا سر بسته شد. OP-2 (رسیدِ disposition) هنوز در worktree است (`1807ff4`) — انتقالِ دوم لازم دارد.
