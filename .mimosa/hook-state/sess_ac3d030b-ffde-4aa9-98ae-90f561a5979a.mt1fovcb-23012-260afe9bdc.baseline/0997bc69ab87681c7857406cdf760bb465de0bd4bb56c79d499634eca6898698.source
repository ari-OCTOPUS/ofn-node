# FINAL-VERDICT — مأموریتِ یکپارچه‌سازی · ۲۰۲۶-۰۷-۳۰

**وضعیتِ نهایی: `INTEGRATED_IN_SANDBOX` + `READY_FOR_OWNER_LIVE_GATE`**
(برای پلِ اقدام: در sandbox یکپارچه و اثبات‌شده؛ فلگش خاموش و منتظرِ رأی.)

## What changed

۱. **`_ops/goal_action_bridge.py` (نو، ۲۸۳ خط)** — صداکنندهٔ گمشدهٔ زنجیرهٔ
   «پیش‌ثبتِ دقیق → mission → عمل → رسید». هیچ subsystem ِ تازه‌ای ساخته نشد:
   سه قطعهٔ پل (`unified_control.pipeline.prepare_records`،
   `method_translator`، `action_bridge.planner/executor`) و قراردادِ
   `mission_contract` از قبل تست‌شده بودند و **فقط صداکننده نداشتند**. پل
   صدایشان می‌زند و دو چیزِ کم را اضافه می‌کند: دفترِ append-only ِ mission با
   گذارِ اجباریِ قانونی، و consolidation ِ حکمِ **مستقل** به حافظه.
۲. **`_ops/test_cycle.py`** — دو درزِ کمینه: (الف) `record()` حالا
   `prereg_id` ِ دقیق را حمل می‌کند (تا امروز اتصال از تصادفِ `cycle_id`
   بازسازی می‌شد — همان «حدسِ آخرین ردیف» که قرارداد ممنوع کرده)؛ (ب) دو
   فراخوانِ پل، هر دو پشتِ گیتِ فلگ.
۳. **`_ops/tests/test_goal_action_bridge.py` (نو، ۱۴ سنجه)**.
۴. پیش از این مأموریت، در همین جلسه: مسیریابیِ خروجیِ تلگرام، سیاستِ
   HOLD/تحویل، وصلِ مامور، مدلِ Task ِ پاها — همه LIVE با شاهدِ ران‌تایم.

## What was tested

- **baseline پیش از هر تغییر**: ۴۶۳/۴۶۳ در ۴۲ سوییت، صفر قرمز
  (`01-BASELINE-TESTS.{md,json}`). `run_all.py` ِ کامل **BLOCKED** با دلیلِ
  مکتوب (فایل‌های زندهٔ STOP می‌سازد؛ فقط با pin ِ ORG_ROOT در worktree).
- **بعد از تغییر**: ۲۰۵/۲۰۵ در ۱۵ سوییتِ متأثر + action_bridge ۴۹/۴۹ +
  unified_control سبز. صفر رگرسیون.
- **E2E read-only** (`06-E2E-TRACE.json`): یک `trace_id` واحد از جهت تا حافظه —
  `direction(7) → prereg(target منجمد) → mission(A0) → receipt=EXECUTED →
  metric=3.0 → verdict=PASS → memory consolidated=1`. ناوردی‌ها:
  `single_trace=True` · `mission_status=done` · `journal_has_prereg=True`.
  در sandbox ِ ایزوله؛ صفر ارسال/خرج/ری‌استارت/arm.

## What mutation proved

۷ جهشِ اجباریِ §۱۷.۲ روی پل، **۷/۷ قرمز** (`05-MUTATION-EVIDENCE.json`):
missing-prereg→execute · receipt/ledger-failure→success ·
illegal-transition→accepted · non-ALLOW→execute · متن→مجوز ·
memory flag-off→consolidated · journal بی‌`prereg_id` · درز بی‌فلگ.

پاسِ اول **۵/۷** بود. دو جهشِ سبز، دو گاردِ واقعیِ سنجیده‌نشده را لو دادند:
- **دفاعِ لایه‌ای بی‌سنجه**: گیتِ non-ALLOW ِ پل سبز ماند چون executor هم
  مستقلاً A3 را BLOCK می‌کند. لایه‌ای که سنجهٔ خودش را ندارد بی‌صدا می‌پوسد.
- **گاردِ رشته‌ای + پایهٔ غلط**: بندِ «درز flag-off است» فقط `"_gab.enabled()"`
  را در سورس می‌گشت و آن رشته **دو بار** هست؛ و بدتر، تست بدونِ
  `OCTOPUS_WIRE_TEST_CYCLE` پایه‌اش را زیرِ سطحِ هدف چیده بود (`run()` در خطِ
  اول برمی‌گشت، پس «action ساخته نشد» تصادفاً درست بود).

## What is integrated / What is not live

| | |
|---|---|
| **INTEGRATED_IN_SANDBOX** | پلِ اقدام (فلگ خاموش)، E2E، دفترِ mission، consolidation |
| **LIVE_PROVEN (پیش‌تر امروز)** | مسیریابیِ خروجیِ تلگرام · hold_policy · مامور (وصل) · leg_tasks |
| **NOT LIVE** | پلِ اقدام تا مسلح‌شدنِ `OCTOPUS_WIRE_ACTION_BRIDGE` **و** ری‌استارتِ organism |
| **BLOCKED_BY_OWNER** | A3/A4/A5 — کارتِ مالک/اثرِ بیرونی/خرج؛ هیچ مسیری از این پل به آن‌ها نیست |

## What remains blocked (صادقانه)

۱. **`self-model` و `ORGANISM-STATE` هنوز CONFLICTED** — `.tmp` تازه، فایلِ
   اصلی کهنه (WinError 5). فازِ ۴ ِ مأموریت را **انجام ندادم**: `LockedJson`
   قلبِ نوشتنِ کلِ ارگانیسم است و دست‌زدن به آن بدونِ inventory ِ کاملِ
   نویسنده‌ها ریسکی است که این جلسه ظرفیتش را نداشت. پل خودش fail-closed
   است (state ِ کهنه ⇒ `authority=STALE` ⇒ فقط read-only) پس این بلاکر
   جلوی درستیِ پل را نمی‌گیرد، ولی «۱۰۰٪ freshness» ادعا نمی‌کنم.
   کارت: **VQ-STATE-WRITE-001** (از قبل باز).
۲. **`VQ-HARNESS-STATEDIR-001` (نو)** — `harness` متغیرِ `OCTOPUS_STATE_DIR`
   را pin نمی‌کند، پس هر تستی که `MemoryStore()` بسازد در `memory.db` ِ
   **زنده** می‌نویسد. اشکال‌زداییِ خودم سه ردیف نوشت؛ با API ِ خودِ گیت
   `retract` شدند (RETRACTED، **حذف نشد** — هر ۱۰ ردیف سرِ جا). تستِ من
   حالا خودش pin می‌کند، ولی فیکسِ ریشه در harness است و روی هر سوییتِ
   حافظه اثر دارد ⇒ مالکِ آن فایل تصمیم بگیرد.
۳. **`os_v1/mission_runner.py` یتیم است** (تنها صداکننده: تستِ خودش) و با
   `telegram_center/mission_runner.py` هم‌پوشانیِ کارکردی دارد ⇒ نامزدِ
   `DEPRECATED`. **دست نزدم** — انتقال/بازنشستگی رأیِ مالک است.
۴. **`Mission Genome` (۱۲ وضعیت) با قراردادِ canonical (۶ وضعیت) ناسازگار
   است.** هر دو زنده‌اند. آشتی‌شان یک مهاجرتِ واقعی است، نه یک patch.
۵. گیت‌های تلگرام ۵ و ۹ (۱۲ سؤال در تلگرامِ واقعی + تستِ زندهٔ محدود) کارِ
   مالک‌اند. رسیدِ اولین بحرانی/دایجستِ **واقعی** منتظرِ رخدادِ طبیعی است —
   رخداد جعل نکردم.
۶. فازهای ۶ (trace سراسری)، ۷ (استانداردسازیِ ۱۰ manifest)، ۱۰ (World
   Discovery)، ۱۱ (Heart) **انجام نشدند** — طبق §۲۰ اولویتِ P0 تمام شد و
   P1/P2 به نشستِ بعد رفت. scaffold ِ جدید نساختم.

## Which owner decisions are required

| کارت | اثر |
|---|---|
| `LIVE-GATE-CARD-ORGANISM.md` | مسلح‌کردنِ `OCTOPUS_WIRE_ACTION_BRIDGE` + ری‌استارتِ organism |
| `LIVE-GATE-CARD-TELEGRAM.md` | ۱۲ سؤالِ گیت ۵ + تستِ زندهٔ محدودِ گیت ۹ |
| VQ-HARNESS-STATEDIR-001 | فیکسِ ریشه در `harness.py` (مالکِ فایل) |
| VQ-OSV1-DEPRECATE-001 | بازنشستگیِ `os_v1/mission_runner` |
| VQ-MISSION-RECONCILE-001 | آشتیِ دو ماشینِ حالتِ mission |

## Exact rollback

```text
کدِ این مأموریت      git -C F:\backup reset --keep 8d76618   (HEAD ِ پیش از فاز صفر)
فقط پلِ اقدام        فلگ را ست نکن — با فلگِ خاموش کد صفر اثر دارد (اثبات: M18)
تلگرامِ امروز        git -C F:\backup reset --keep 6b51c83
خاموشیِ آنی          _ops/STOP-ORGANISM  (کلِ ارگانیسم، تمیز)
حافظهٔ آلوده         سه ردیف RETRACTED شدند؛ برگشت: gate.promote(<memory_id>)
```

`reset --keep` عمدی است نه `--hard`: کارِ کامیت‌نشده را **رد می‌کند** به‌جای
پاک‌کردنِ بی‌صدا. هیچ push/merge/deploy انجام نشد.

## ناوردی‌های حفظ‌شده

صفر فلگِ تازه‌ای که مالک نخواسته · صفر poller/bot ِ تازه · صفر subsystem ِ
تکراری · هر ۱۰ هانکِ کامیت‌نشدهٔ دو جلسهٔ موازی در `center.py` و
`approval_channel.py` **دست‌نخورده** (staging جراحی با `git apply --cached`
روی پچِ فیلترشده، بیمه‌نامهٔ دیفِ کامل در scratchpad) · `organism.py` و
`wiring.py` و `run_all.py` لمس‌نشده · صفر ارسال/خرج · صفر مارکرِ توقف ·
ارگانیسم سالم.
