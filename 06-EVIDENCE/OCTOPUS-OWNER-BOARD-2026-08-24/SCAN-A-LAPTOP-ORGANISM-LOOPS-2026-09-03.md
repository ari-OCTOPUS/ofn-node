# SCAN A — حلقه‌های حافظهٔ ارگانیسم والت (لپ‌تاپ) — گزارش کامل کاوشگر
شناسه: `SCAN-A-LAPTOP-ORGANISM-LOOPS-2026-09-03` · read-only · ساعت ~16:10 AEST
موضوع: F:\backup\_ops — حلقه‌های بازگشتی خودگردان و سیم‌کشی غایبشان.

## وضعیت کلی: ارگانیسم زنده است
- هستهٔ متابولیک `organism.py` (تیک ۳۰۰ث، تک‌نمونه با قفل پورت 8771) — **تنها نویسندهٔ ORGANISM-STATE.json** (انحصار با تست قفل شده: test_state_write_monopoly.py) + ۹ sidecar تازه (۸ نوشته‌شده امروز، یکی هرگز — یافتهٔ ۴).
- قلب v2 روی BeatScheduler (زنده: آخرین beat ۳۶ ثانیه قبل از اسکن) → chrono.db (جداول heart_run/beat/event) + pulse/heartstate-latest.json که cortex ریتمش را می‌خواند.
- chrono: جداول heartbeat (۶۰,۴۲۹ ردیف) و checkpoint (۶۰,۴۲۸) تازه — خواننده دارد (wiring/doctor/داشبوردها).
- cortex (پورت 8772): خوانندهٔ همهٔ stateها + **تجمیع‌گر واقعی حافظه** (cortex/consolidate.py → semantic_memory.jsonl + cursor، فعال با CORTEX_CONSOLIDATE=1، اجرای تازه امروز).
- حافظهٔ اپی‌زودیک: memory/self_loop_ingest + research_ingest → memory.db (۱,۰۵۸ ردیف، آخرین 04:21Z) → خوانندگان واقعی (retrieval_router، daily_loop، c6_trigger، verdict_recorder). قرارداد قدیمی «write-only» با memory_read_loop (سیم‌کشی‌شده در organism.py:633) حل شده.
- تلگرام-سنتر: poll زنده + outbox دوام‌دار + دو واچ‌داگ ۵دقیقه‌ای (شناسایی hang دارد).
- اتاق کنترل زنده (8773، هر ۴ث) + کاکپیت-برین (تسک ۵دقیقه‌ای، کارت واحد به مالک).
- شبانه: دکترِ روزانه ۰۷:۰۰ (dry-run، بدون --apply) + نگهبان مسمومیت 4d (۶ساعته، فعال).

## دوازده یافتهٔ غیبتِ سیم (برچسب H/M/L)
1. [H] دو تسک Observatory ساعتی → `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\...run_observatory.py` — دایرکتوری حذف‌شده؛ Last Result=2 ولی Status=Ready = fail بی‌صدا. بستهٔ بومی `_ops\observatory\` هیچ تسکی ندارد. فیکس: بازنشاندهی تسک‌ها به بومی + حذف duplicate.
2. [H] تسک «OCTOPUS 4d Consolidation Tick» (۶ساعته) از 2026-08-23 05:49 **خاموش** — اسکریپت و ورودی‌ها (4d_system/outputs/...) سالم؛ خوراک POISONING-WATCH-4d.md ۱۱ روز قطع. cortex-consolidate فقط events.jsonl را می‌پوشاند، جایگزین 4d نیست.
3. [H] split-brain واچ‌داگ: تسک production (۱۵دقیقه‌ای) `04 - Architect System\scripts\organism-watchdog.ps1` را می‌راند که هیچ ارجاعی به `watchdog.py` ندارد — منطق تشخیص-دامادگیِ واقعی در `_ops\organism-watchdog.ps1`+`watchdog.py` بلااستفاده. بازنشاندهی owner-gated است (یادداشت SPLIT-BRAIN در خود فایل).
4. [M] `wiring.py:3563-3571` sidecar `ORGANISM-STATE.business_legs` را فقط با write=True می‌نویسد؛ تنها فراخوان زنده write=False دارد (organism.py:1249) — فایل هرگز نمی‌آید در حالی که ۸ خواهرش تازه‌اند.
5. [M] saba-bridge: `legs/studio_pf_leg.py:136-147` تولیدکننده خاموش + مصرف‌کننده `saba_bridge_beat` هیچ فراخوانی در کل _ops ندارد؛ state/saba-bridge.jsonl از ۰۸-۰۸ کهنه.
6. [M] `effector_registry.py:95` تولیدکننده را `_ops/memory/consolidation.py` می‌گوید — ماژول ناموجود (واقعی: cortex/cortex.py:497→consolidate.py).
7. [M] `cortex/self_improve_gauges.py:163-165` دو DB ناموجود (4d_system/state/memory.db و 4d_system/memory/memory.db) را می‌کاود — گیج بی‌شمار.
8. [L] `state\memory.db` و `state$db` صفربایت (۰۷-۰۷/۰۷-۲۵) — دوقلوهای مرده؛ خوانندهٔ آینده DB خالی می‌گیرد نه خطا.
9. [L] جداول صفرنویسنده در chrono.db: `gated_effect`، `heart_outbox`، `heart_anchor` (طراحی‌شده برای فاز ACT خشک).
10. [L] stateهای یتیم: `control_plane/snapshot.json` (از ۰۸-۰۳؛ کتابخانه‌اش فقط-خواندنی و بی‌زمان‌بند)، `board_cp/commands.sqlite` (۰۸-۱۷) + `board-status.txt` (۰۸-۲۰، صفر ارجاع در کد)، `chat/chat-log.jsonl` (۰۸-۲۹)، `c6/romajan-seen.json` (۰۷-۳۰).
11. [L] `state/discoveries-seen.json` از ۰۸-۰۸ دست‌نخورده — پا-یافتن‌ها (cortex/discoveries.py) بی‌dedupe مانده.
12. [L] `daily/daily_loop.py` عمداً بدون زمان‌بند (مالکی) — هیچ یادآوری‌ای هم نیست.

## نکتهٔ اعتماد
انحصار نویسندهٔ ORGANISM-STATE دقیقاً برقرار (یک ماژول + تست قفل + brain_worker ادغامی) — مسیر تعارض دوتایی یافت نشد.
