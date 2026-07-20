---
type: architecture
status: active
tags: [architecture, integration, telegram, spine, fence, metrics, verification]
created: 2026-07-21
updated: 2026-07-21
---

# ادغام دو-موجی 2026-07-21 — تعمیر حلقهٔ ارزشِ تلگرام‌محور (Coordinator)

> مأموریت مالک: پنج کارگر موازی (A تلگرام/رأی · B فنس LLM · C ستون رویداد · D متریک · E ممیز read-only)
> از یک BASE_SHA مشترک، ادغام سریالی توسط Coordinator، سپس موج دوم (F ‏e2e پیپر · G راستی‌آزمای متخاصم).
> همه additive/flag-off/fail-soft؛ صفر فعال‌سازی/شبکه/پول/لمسِ درخت زنده.

## زنجیرهٔ SHA

- **BASE_SHA** = `70481b5` (سرِ `integration/2026-07-20`؛ شامل Sol-T0..T7 که تک‌به‌تک بازرسی و تستِ ادعاهایش توسط Coordinator بازاجرا شد)
- مبنای ادغام (بعد از reconcile با جلسهٔ موازی Sol) = **master `4e9ab3e`** (Sol تا Paper-MVO ‏e2e و فیکس purity ‏live_loop جلو رفته بود)
- **INTEGRATED_SHA** = `0f60c4e` — ‏cherry-pick سریالی ‏B(`7d7820b`)→C(`ae2ba02`)→D(`3c12184`)→A(`d639baf`,`d491761`) + وصله‌های Coordinator
- سپس `f01139f` (hermetic کردن ۴ تستِ وابسته به تقویم) و `c723a0e` (ادغام F بعد از حکم G)
- **FINAL_SHA** = کامیتِ همین سند (master به آن fast-forward شده؛ germline×2 پوش شده)

## DecisionLog — تصمیم‌های پذیرفته‌شدهٔ Coordinator (تک‌به‌تک)

- **DL-W-01 · BASE_SHA=70481b5 نه f2f500d:** برنچ integration هفت کامیت Sol-T جلوتر از master بود؛ diff همه بازرسی شد (additive/flag-off، صفر ناحیهٔ ممنوعه) و تست‌هایش مستقلاً سبز بازاجرا شد (menu_v2 ‏5/5، ‏verdict ‏8/8، ‏fence-guard ‏3/3). بازسازی از f2f500d فقط پیاده‌سازی موازیِ متعارض می‌ساخت.
- **DL-W-02 · reconcile با جلسهٔ زندهٔ Sol:** حین موج اول، Sol چهار کامیت دیگر زد (Step5 ‏e2e، ‏Step6/7 ممیزی، فیکس purity، ‏state-churn) و master را تا `4e9ab3e` برد. مبنای ادغام به سرِ جدید ارتقا یافت؛ کارگرها روی 70481b5 پین ماندند و cherry-pick روی 4e9ab3e نشست.
- **DL-W-03 · حل تعارض `live_loop.py`:** برخورد نسخهٔ inline ‏Worker A با کپسولهٔ `record_verdict_durably` ‏Sol — معماری Sol حفظ شد (لایهٔ wire خالص، ناوردی `t_no_production_import`) و `lead_id`/`source` ‏A روی امضای هر دو تابع سوار شد. هرگز ours/theirs کور انتخاب نشد.
- **DL-W-04 · پچ producer صادق (از Worker D):** ‏`proposal_metrics` حالا `proposals_sent`/`proposals_fake_delivered` می‌دهد؛ تحویلِ `sent=False` دیگر جای کارِ واقعی حساب نمی‌شود (goal_directed از قبل fallback-سازگار).
- **DL-W-05 · هوک mission-created (از Worker C):** ‏`owner_menu.handle_new_mission` حالا پشتِ `OCTOPUS_WIRE_SPINE` رویداد canonical ‏mission-created می‌فرستد (fail-soft؛ smoke مستقل Coordinator و probe ‏7/7 ‏Worker G هر دو PASS) → ستون رویداد ۵ دامنهٔ دارای caller واقعی دارد: lead، proposal، doctor، ziman، mission.
- **DL-W-06 · بهداشت run_all:** ثبت ۶ تست موج اول + حذف ثبتِ دوبارهٔ `test_txn_store`/`test_attributor` (یافتهٔ Worker E) → ۲۳۰ ورودی یکتا، صفر غایب.
- **DL-W-07 · rollover تقویم:** ‏`LIVE_GATE_DATE=2026-07-21` امروز رسید؛ ۴ تستِ «live locked until» با پینِ تاریخ (الگوی `test_cockpit_golive_honesty`) hermetic شدند — heart_loop ‏13/13، ‏cortex ‏10/10. رفتار production صفر تغییر.
- **DL-W-08 · ادغام F فقط بعد از حکم G:** ‏G هر ۱۵ ادعا را PASS داد (صفر فیکس بلاک‌کننده) → ‏F ‏(`83ad17f`→`c723a0e`) ادغام شد؛ ‏e2e حالا 2/2 با نخ‌کشی کامل IDها، ‏duplicate-verdict، ‏failed-fake-delivery، بازسازی قطعی بعد از reopen و گارد سوکت.
- این فرمان مالک فقط پیاده‌سازی امن را مجاز کرد؛ **سیاست مالی، فعال‌سازی و اثر خارجی مجاز نشد و انجام هم نشد.**

## خروجی کارگرها (همه SOURCE+TEST-verified؛ هیچ‌کدام RUNTIME)

| کارگر | کامیت | تحویل | تست |
|---|---|---|---|
| A تلگرام/رأی | `d639baf`,`d491761` | صداقت منو (صفر دستور مرده) + `_durable_verdict_outcome` در center (بعد از گیت is_owner؛ ap:/legacy/mission) | honesty ‏7/7 + ‏verdict_durable ‏13/13 |
| B فنس LLM | `7d7820b` | ‏`fence_adapter` + عبور ۴ ‏bypass (debate/setpoint/epoch/chord-fallback)؛ inventory ماشین‌چک، صفر باقی‌مانده | ‏6/6 + ‏9/9 |
| C ستون رویداد | `ae2ba02` | ‏۵ نام canonical + ‏`spine_adapters` ضدPII + producerهای doctor/ziman | ‏9/9 |
| D متریک | `3c12184` | حکم reachability=FIXED_ALREADY؛ جدایی ۸-لایهٔ liveness/کار/ارزش از store ‏durable | ‏10/10 |
| E ممیز | (read-only) | ۲۶ حکم claim + manifest ‏deployment ‏۵ سرویس + تحلیل run_all | صفر write، STOP هش‌شده قبل/بعد |
| F ‏e2e | `83ad17f` | بستن ۶ شکاف e2e ‏Sol (فقط تست) | ‏2/2 |
| G راستی‌آزما | (read-only) | ‏**۱۵/۱۵ PASS**، صفر فیکس بلاک‌کننده، probeهای مستقل seam | — |

## یافته‌های داغ برای مالک (رأی لازم — هیچ‌کدام توسط این مأموریت تغییر داده نشد)

1. **[P0-مجاور] ‏ps_writeback مسلح در config زنده:** ‏flags.cmd زنده هر سه گیت (`OCTOPUS_WIRE_PS_WRITEBACK`+`ACCT_BEAT_SYNC`+`OCTOPUS_WIRE_POCKETSMITH`) را ست کرده؛ تنها مانع PUT خارجی به PocketSmith = halt بودن ارگانیسم. سیاست per-item-verdict قبل از هر restart لازم است (Worker E، claim 23).
2. **گیت پولی cortex از امروز باز:** سپر تاریخ (`opslib.py:167`) رسید **و** هر دو اهرم `ACTIVATION-RESEARCH-EARLY.flag`/`ACTIVATION-CORTEX-PAID.flag` ‏tracked/موجودند (کامیت قدیمی «Wave 0») → ‏`paid_gate()=True` در restart بعدی (metering ‏organ_gate برقرار). تصمیم: untrack کردن اهرم‌ها یا پذیرش آگاهانه.
3. **شکاف‌های deployment (Worker E):** واچ‌داگ ثبت‌شدهٔ organism = دوقلوی `04 - Architect System` (بدون HALT-ALL، ‏cortex را هم supervise می‌کند)؛ هر ۴ scheduled task اسکریپت‌های درخت زنده (قبل از D-G) را اجرا می‌کنند؛ ‏tg-center واچ‌داگ ثبت‌شده ندارد؛ task کهنهٔ `OctopusLiveDataRefresh` به Desktop اشاره دارد.
4. **سخت‌سازی‌های پیشنهادی G (غیر-بلاکر):** پینِ `_OPS` تست‌ها به درخت خودشان (اجرای unpinned بی‌صدا درخت زنده را تست می‌کند) · گسترش CB_TOKEN به verbهای legacy `ok/no/later` و `ms:` · ‏sanitize داخل `event_spine.dual_write`.
5. **کاسمتیک:** ‏`verdict_recorder` فیلد `spine=True` را حتی روی duplicate ‏spine برمی‌گرداند (Worker F).

## نتیجهٔ suite و validatorها

- **run_all کامل (env پین‌شده به worktree ادغام، صفر credential در محیط): هر ۲۳۰ فایل تست سبز؛ مهر CAPABILITY با fingerprint توسط مکانیزم رسمیِ fail-closedِ خود run_all در همان درختِ تست‌شده (worktree ایزوله) نوشته شد.** دور اول ۲ قرمز داشت (`test_heart_work`، `test_go_live`) که هر دو ادامهٔ همان کلاس rollover تقویم بودند — hermetic شدند و دور دوم تماماً سبز.
- شمارش صادقانهٔ run_all: ‏**۲۳۰ ورودی، ۲۳۰ یکتا** (دو ثبتِ تکراری حذف شد) + ‏۲ تستِ EXTRA خارج از `_ops/tests` + ‏۶ تستِ pytest-mode ‏ziman/cartographer + ‏۴ phantom ‏**عمداً** خارج از لیست با دلیلِ مکتوب (`test_effector_idempotency`، `test_drawdown_enforcer`، `test_mining_leg`، `test_tg_approval_store`).
- **validatorها (dry-run):** فرانت‌متر = **۲۲۲ خطا، دقیقاً برابر بک‌لاگ شناخته‌شدهٔ قبلی — دلتای این موج صفر**؛ لینک شکسته = ۷۵ (بک‌لاگ ۷۱ + ‏۴ لینکِ جلسه‌های ۰۷-۲۰ به نوت‌هایی که فقط untracked در درخت زنده‌اند، مثل `2026-07-20_LEGS-DEEP-SCAN.md` — از این موج نیست؛ فیکسش = کامیتِ آن نوت‌ها توسط لاینِ خودش). فایل‌های نوی این موج: صفر خطا در هر دو validator.
- برچسب صداقت: همهٔ ادعاهای این موج **SOURCE+TEST-VERIFIED**؛ هیچ‌چیز RUNTIME-OPERATIONAL ادعا نمی‌شود — درخت زنده همچنان روی `a2183c3` است و ارگانیسم halt.

## ناوردی‌های حفظ‌شده

- ‏STOP-ORGANISM بایت‌به‌بایت (sha256 ‏`C8FE7176…5CD099`، ۳۳ بایت) — قبل، وسط و انتهای مأموریت هش شد.
- درخت زنده `F:\backup` کاملاً untouched؛ صفر restart/فعال‌سازی/flag-flip؛ صفر شبکه/تلگرام/پول/writeback.
- همهٔ کارها در worktreeهای ایزوله (wave1-*/wave2-*)؛ کارگرها هرگز merge/push نکردند؛ فقط Coordinator ادغام کرد.
- بکاپ off-disk: هر دو `E:/germline/octopus.git` (فیکس `receive.unpackLimit=0` برای خطای loose-object) و `E:/germline/octopus-wave-20260721.git` (نو).
