# mining_os — ACTIVATION (رانبوکِ مالک)

> وضعیت: **وصل‌شده، flag-off.** تا این قدم‌ها را نزنی هیچ رفتاری تغییر نمی‌کند (flag-off = بایت‌به‌بایت).

> ### ⚠️ تصحیحِ ۲۰۲۶-۰۷-۲۸ — این سند ۹ روز غلط بود
> نسخهٔ قبلی می‌نوشت «هوکِ additive در `_ops/organism.py:712`». آن خط در واقع بلوکِ
> **متریکِ فیشر** است، و grep روی کلِ `_ops` **صفر** ارجاع به `mining_os` می‌داد. سه فلگی
> هم که پایین «روشن کن» گفته شده بود (`_OS`/`_UI`/`_VERDICT_SYNC`) در هیچ `.py` و هیچ
> `.cmd` وجود نداشتند — یعنی قدمِ ۳ اجراشدنی نبود. بسته کامیت شد (`88aaa29`، ۲۴ فایل)،
> هوک‌هایش نه؛ و بعد زیرِ تکاملِ `organism.py`/`center.py` گم شدند.
>
> نتیجه: ۳۲ تستِ سبز روی کدی که **هرگز اجرا نمی‌شد**. تست‌های بسته این را نمی‌دیدند
> چون همه درون-بسته‌اند. سیم‌کشی امروز واقعاً ساخته شد + گاردِ call-site
> (`_ops/tests/test_mining_os_wiring.py`، ۹/۹، هر ۵ جهش گرفته شد) تا دوباره بی‌صدا نیفتد.

## چه چیزی واقعاً در درخت هست (۲۰۲۶-۰۷-۲۸، راستی‌آزمایی‌شده)
- بستهٔ `mining_os/` در `03 - Projects/Mining/mining_os/` — **۳۲** تستِ سبز، pure-stdlib.
- `_ops/wiring.py` → `mining_os_beat()` پشتِ `OCTOPUS_WIRE_MINING_OS` (kill-switch مقدم، cadence با `CHRONO_MINING_OS_EVERY_N_BEATS`، پیش‌فرض ۰ = هر beat، سایدکارِ اتمیکِ `ORGANISM-STATE.mining_os`).
- `_ops/organism.py` → صداکنندهٔ additive کنارِ `business_legs`/`asset_map` + merge در ORGANISM-STATE.
- `_ops/telegram_center/center.py` → سه هوک: `_mining_ui()` (lazy، اول فلگ بعد import)، `/mining` در handlers + در `_CENTRE_GATED` (تا پلِ دو-باتی تصمیمِ فلگ را دور نزند)، و مسیرِ فعلِ `mo:` در `_handle_callback`.
- راستی‌آزمایی: `py_compile` ✅ · flag-off → `None` (فلگ در هیچ `.cmd` نیست) ✅ · flag-on smoke → اسکلتِ صادق `live=False` ✅ · گاردهای مجاور سبز (callback_routing 6/6، two_bot_bridge 9/9، tg_center 24/24) ✅.

## قدم‌های فعال‌سازی (روی ویندوز)
1. **Commit checkpoint** — git از سندباکس بلاک است (کوییرک‌های سندباکسِ vault)، پس روی ویندوز:
   - تغییرها: `_ops/wiring.py` (+`mining_os_beat`)، `_ops/organism.py` (صداکننده + merge)، `_ops/telegram_center/center.py` (۳ هوک)، `_ops/tests/test_mining_os_wiring.py` (تازه) + ثبتش در `run_all.py`، و همین سند.
   - پیام پیشنهادی: `fix(mining): rebuild the lost mining_os wiring flag-off + call-site guard`.
2. **(اختیاری) دادهٔ واقعی:** `mining_os/state/MINING-STATE.json` را با ناوگان/کوین/برقِ واقعی پر کن (اسکیما در `state.py`). تا آن‌موقع `live=False` (اسکلتِ صادق) درست است.
3. **روشن‌کردنِ فلگ‌ها:** در `OCTOPUS-flags.cmd`: `set OCTOPUS_WIRE_MINING_OS=1` (ضربانِ leg)، `set OCTOPUS_WIRE_MINING_UI=1` (منوی تلگرامِ Topic ⛏ + دستورِ `/mining`)، و (اختیاری) `set OCTOPUS_WIRE_MINING_VERDICT_SYNC=1` (سینکِ verdict به بلوکِ auto-managed در `VERDICT_QUEUE.md`). هر سه مستقل‌اند.
4. **ری‌استارت:** `_ops/STOP-ORGANISM` را بردار / ارگانیسم را ری‌استارت کن → هر beat، `mining_os.loop.tick` صدا زده می‌شود و snapshot در `mining_os/state/last-beat.json` می‌نشیند.

## خط‌قرمزها
- پول همیشه **P7** (`capability ∧ LIVE_ENABLED ∧ approval`). این فلگ فقط سنجش/گزارش است، هیچ خرجی.
- هرگز به `Ai bots/fleet` (SSH/subprocess) وصل نشو مگر پشتِ **P5+** و کارتِ تأیید.
- UI تلگرام (Topic ⛏، منوی ۶-گزینهٔ `mo:` + `/mining`) **پیاده و flag-off وصل شد** به `center.py` (۳ هوکِ additive، پشتِ `OCTOPUS_WIRE_MINING_UI`). verdictها به `mining_os/state/verdict-actions.jsonl` می‌روند. **سینکِ canonical پیاده شد** (`tg_mining.sync_verdicts_to_queue`): پشتِ فلگِ `OCTOPUS_WIRE_MINING_VERDICT_SYNC` (flag-off = دست‌نخورده)، append-only در بلوکِ `MINING-AUTO-VERDICTS` با dedup آخرین‌تصمیم — هرگز داغ‌ویرایشِ کورِ جدولِ انسانی. صفر لمسِ `center.py`؛ ۳۲ تستِ سبز.

## Rollback
- فلگ را خاموش کن (`=0`) — کافی است (flag-off = بایت‌به‌بایت).
- یا بلوکِ `_ops/organism.py:711-720` را بردار (additive و بی‌عارضه).
