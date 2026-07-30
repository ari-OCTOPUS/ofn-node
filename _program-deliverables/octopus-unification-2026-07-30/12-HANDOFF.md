# 12 — HANDOFF · مأموریتِ یکپارچه‌سازی ۲۰۲۶-۰۷-۳۰

## وضعیت در یک نگاه

```text
Branch      fix/tg-p2-2026-07-30    HEAD f6b82e9
Status      INTEGRATED_IN_SANDBOX + READY_FOR_OWNER_LIVE_GATE
Baseline    463/463 (42 سوییت)  →  بعد: 205/205 متأثر + ab 49/49 + uc سبز
Mutation    7/7 قرمز (پاسِ اول 5/7 بود — دو گاردِ سنجیده‌نشده پیدا و بسته شد)
E2E         سبز، یک trace_id واحد، در sandbox
```

## آنچه در این نشست ساخته شد (به ترتیب)

| کامیت | چه چیزی |
|---|---|
| `2718921` | مسیریابیِ خروجیِ تلگرام — `surface_router.resolve` صداکننده گرفت + خانه/پالسِ لنگر |
| `4c36362` | `live_output=true` با شاهدِ ران‌تایم (`center-pulse → DM`) |
| `85ce915` | ناگفته‌ها → DM (رأیِ اولِ مالک) |
| `1abc23c` | ماشینِ حالتِ VQ-TG-HOLD-001 (بحرانی فوری · نو digest · تکراری HOLD) |
| `0025064` | مامور (owner_console) به Outer DM |
| `8d76618` | مدلِ Task ِ پاها (کارتِ زنده، ۴ دکمه، ۴ وضعیت) |
| `02a2af5` | **پلِ اقدامِ SGC-14** — exact prereg → mission → A0 → receipt → verdict → memory |
| `f6b82e9` | دو گاردِ رفتاری جای دو جهشِ سبز |

## قدمِ بعدیِ نشستِ بعد (به ترتیبِ اولویت)

۱. **کارتِ `VQ-ACTION-BRIDGE-ARM-001`** را به مالک نشان بده. تا رأی، پل
   کد است نه رفتار.
۲. **P1 ِ §۲۰ که انجام نشد**: trace سراسری (فاز ۶) · استانداردسازیِ ۱۰
   manifest (فاز ۷، با schema drift ِ ثبت‌شده: ۴ از ۵ نامعتبر و فایلِ schema
   مرکزی **هیچ خواننده‌ای ندارد**) · World Discovery (فاز ۱۰).
۳. **`VQ-STATE-WRITE-001`** — freshness ِ self-model/ORGANISM-STATE. عمداً
   دست نزدم: `LockedJson` قلبِ نوشتنِ کلِ ارگانیسم است و بدونِ inventory ِ
   کاملِ نویسنده‌ها ریسکی است. inventory را کاوشگرِ D ِ همین مأموریت شروع
   کرده — نتیجه‌اش در `02-CALL-GRAPH.md`.
۴. **`VQ-HARNESS-STATEDIR-001`** — فیکسِ ریشه در `harness.py`؛ روی هر
   سوییتِ حافظه اثر دارد پس مالکِ آن فایل باید بزند.

## تله‌هایی که این نشست خورد — تکرارشان نکن

۱. **`git checkout --` وسطِ جهش، هانکِ بیگانه را می‌برد.** سه بار امروز.
   قاعده: روی فایلی که هانکِ کامیت‌نشدهٔ دیگری دارد، بازیابیِ جهش **همیشه از
   کپیِ فایل** است، و دیفِ کامل را قبل از هر `git apply --cached` در
   scratchpad نگه دار — همان فایل بیمه‌نامهٔ بازسازی است (یک بار جانِ کارِ
   جلسهٔ موازی را نجات داد).
۲. **backtick در پیامِ کامیتِ heredoc**، bash می‌بلعدش. چهار واژه از پیامِ
   `02a2af5` گم شد؛ با `-F file` اصلاح شد. از این به بعد پیامِ بلند از فایل.
۳. **`harness` همه‌چیز را ایزوله نمی‌کند.** `OCTOPUS_STATE_DIR` را pin
   نمی‌کند ⇒ `MemoryStore()` به DB ِ زنده می‌رود. سه ردیف نوشتم و با
   `gate.retract` برگرداندم (RETRACTED، حذف نشد).
۴. **`skip` در MemoryGate دو معنی دارد** (flag-off و dedupe). با `reason`
   تفکیک کن، نه با `verb`.
۵. **جهشِ سبز، دو ریشهٔ متفاوت داشت**: گاردِ رشته‌ای که نمونهٔ دومِ همان رشته
   سبزش نگه می‌داشت، و پایه‌ای که زیرِ سطحِ هدف نشسته بود (`run()` قبل از
   رسیدن به درز برمی‌گشت). هر دو فقط با سنجهٔ **رفتاری** بسته شدند.
۶. **`_cycles_elapsed` روی slot ِ غیرعددی `None` می‌دهد** — پس `2026-07-30#e2e`
   هرگز حکم نمی‌گیرد. برای fixture ِ E2E از چرخهٔ گذشته با slot ِ عددی استفاده کن.
۷. **`read_metric` نسبت به `opslib.STATE_DIR` است**، نه نسبت به `_ops`.

## فایل‌هایی که هرگز لمس نشدند (عمداً)

```text
_ops/organism.py · _ops/wiring.py · _ops/tests/run_all.py
_ops/OCTOPUS-flags.cmd (این مأموریت هیچ فلگی ست نکرد)
PRE-0/** · ARCHITECTURE-SOT.md (به‌روزرسانی‌اش بعد از رأیِ مالک)
_ops/world_discovery/** (namespace ِ GLM)
۱۰ هانکِ کامیت‌نشده در center.py و approval_channel.py (دو جلسهٔ موازی)
```

## خروجی‌های این دایرکتوری

```text
00-REALITY-BASELINE.md      قانون، git inventory، جدولِ وضعیتِ اجزا
01-BASELINE-TESTS.{md,json} ۴۲ سوییت پیش از تغییر + BLOCKED ِ run_all با دلیل
05-MUTATION-EVIDENCE.json   ۷ جهش، command و نتیجهٔ عددی
06-E2E-TRACE.json           ۸ span با یک trace_id
FINAL-VERDICT.md            حکمِ صادق + rollback ِ دقیق
LIVE-GATE-CARD-ORGANISM.md  کارتِ رأیِ مسلح‌کردنِ پل
12-HANDOFF.md               همین فایل
```

اسنادِ `02-CALL-GRAPH` / `03-CANONICAL-CONTRACTS` / `07..11` **ساخته نشدند** —
یافته‌هایشان در `00-REALITY-BASELINE` و `FINAL-VERDICT` خلاصه شده و ساختنِ
فایلِ خالی برای پرکردنِ فهرست، همان «گزارشِ صرف» است که پرامپت ممنوع کرده.
