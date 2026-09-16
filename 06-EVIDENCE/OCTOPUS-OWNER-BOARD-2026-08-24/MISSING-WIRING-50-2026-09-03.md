# MISSING-WIRING-50 — سرشمری سیم‌کشی غایب در حلقه‌های حافظهٔ اختاپوس
شناسه: `MISSING-WIRING-50-2026-09-03` · سه کاوشگر read-only (والت `_ops` + مخزن main=`60dce961` + سه برد) + دو بدهی روز.
برچسب‌ها: H=فوری/پرخطر · M=میانه · L=آرایشی. هر آیتم: کجا — چه غایب است — فیکس یک‌خطی.
اقدام انجام‌شده همین ساعت: چهار تایمر خودمختاری (دکتر/شاهد/غیبت/self-model) روی ۱۳۸ نصب و مسلح شد → آیتم‌های ۱۳ و ۲۱ خودکار شدند.

## A — حلقه‌های ارگانیسم لپ‌تاپ (والت _ops)
1. [H] تسک‌های Observatory (دو تا، ساعتی) → دایرکتوری حذف‌شدهٔ `Desktop\OCTOPUS-NBB-CP-WORKING` — هر ساعت بی‌صدا fail — بازنشاندهی به `_ops\observatory\` بومی + حذف duplicate.
2. [H] تیک تجمیع حافظهٔ 4d از 2026-08-23 خاموش (تسک `OCTOPUS 4d Consolidation Tick`) — ۱۱ روز خوراک POISONING-WATCH نیامده — دوباره فعال‌سازی.
3. [H] واچ‌داگ ارگانیسم split-brain: تسک production اسکریپت `04 - Architect System` را می‌راند نه `watchdog.py` — بازنشاندهی (owner-gated).
4. [M] sidecar `ORGANISM-STATE.business_legs` وعده داده ولی هرگز نوشته نمی‌شود (`organism.py:1249` write=False) — یک پرچم.
5. [M] پل saba-bridge: تولیدکننده خاموش + مصرف‌کننده `saba_bridge_beat` بی‌صدا زننده — تصمیم: وصل یا DEAD-SOURCE.
6. [M] `effector_registry.py:95` به ماژول ناموجود `_ops/memory/consolidation.py` ارجاع می‌دهد — اصلاح provenance به cortex/consolidate.
7. [M] گیج‌های `self_improve_gauges.py:163` دو DB ناموجود می‌خوانند (4d_system/state/memory.db) — مسیر اصلاح.
8. [L] دو DB دوقلو صفربایت در ریشهٔ state (`state\memory.db`, `state$db`) — حذف.
9. [L] جداول بی‌نویسنده در chrono.db: gated_effect/heart_outbox/heart_anchor (۰ ردیف) — تصمیم ثبت یا حذف اسکیما.
10. [L] state های یتیم: control_plane/snapshot (از اوت)، board_cp/commands.sqlite، board-status.txt (بی‌خواننده)، romajan-seen —扫 یا وصل.
11. [L] `discoveries-seen.json` ۲۶ روز دست‌نخورده — پا-یافتن‌ها dedupe خوابیده.
12. [L] daily_loop مالک بی‌ساعت — یک یادآور تایمری.

## B — مغز مخزن (ofn-node)
13. [H→✓] تایمرهای خودمختاری فقط ران‌بوک بودند → الان نصب شدند؛ بدهی باقی: خود فایل‌های unit در deploy/ مخزن ثبت شود.
14. [H] گزارش دکتر (`state/doctor/report.json`) هیچ مصرف‌کننده‌ای ندارد — heartbeat ساعتی باید خلاصهٔ verdict را در پالس مالک بیاورد.
15. [H] SILENT_FLIP/STALE_CLAIM/تحریف لجر هیچ مسیر هشداری ندارد — در witness به `owner_notify.alert_owner` وصل شود.
16. [H] `OWNER-QUEUE.md` هیچ‌جا رندر نمی‌شود (گلاس /queue چیز دیگری می‌خواند؛ کارت کاکپیت صف داخلی نود است) — fallback خواندن فایل در /queue.
17. [H] FLAG-CLAIMS دست‌نوشته است؛ شاهد فقط سن را می‌سنجد نه مقدار — مود `--remeasure` که فرمان هر claim را اجرا کند.
18. [H] فایل claim برداشت زیمان می‌گوید «شاهد می‌خواندش» ولی شاهدش نمی‌خواند — `check_harvest_claim()` به run() اضافه شود.
19. [H] تولید SYSTEM-SELF-MODEL زمان‌بندی نداشت → تایمر نصب شد؛ بدهی: رکیت رسید تولید خودکار.
20. [M] memory_chain زنجیرهٔ ضدتحریف می‌نویسد ولی `chain_verify()` هیچ‌وقت صدا زده نمی‌شود — پروب در دکتر.
21. [M] لجر یادگیری اقتصادی فقط CLI دستی دارد — فیدر خودکار از رویدادهای کوت/فروش.
22. [M] `build_learning_snapshot` گلاس بی‌فراخوان است — با runner پاراگراف ۲۵ وصل شود.
23. [M] کارت economic_learning کاکپیت به run های دستی قدیمی می‌چسبد → کهنه می‌شود — همان فیدر ۲۱.
24. [M] اقتصاد بقا (`economy.py`) خروجی لِین یادگیری را نمی‌خواند — پل OutcomeScore→اپیزود learning.
25. [M] events.jsonl فقط دکتر-نبض می‌خواندش؛ `extract_m2_from_events` بی‌صدا زنندهٔ آینده — وصل یا حذف.
26. [M] telegram_glass پوستهٔ مصرف‌کننده بدون runner است (شش فرمان، همه‌شان منتظر snapshot) — سرویس poller بساز؛ باز می‌کند ۱۴/۱۶/۲۲ را.
27. [M] telegram_bridge (survival) هنوز فقط-فایل + تناقض اسناد (IGNITION «live» vs CURRENT-TRUTH «inactive») — تصمیم one-way.
28. [M] board_events قرارداد کامل بی‌فرستنده/بی‌گیرنده — docstring «contract-only» بنویس تا سرشمری دوباره پرچمش نکند.
29. [M] `ziman_tender_harvest.run()` بی‌صدا زننده (حتی با دو قفل روشن) — caller: systemd oneshot از source_registry.
30. [M] source_registry خروجی‌اش به جایی نمی‌رسد + با `data/painting_source_registry.json` نود دوقلوست — هم‌گرا یا مهاجرت اسکیما.
31. [M] وب‌هوک سفارش شاپ‌فای یتیم: ShopifyConnector هرگز در run.py ثبت نشده — ثبت زیر فلگ/سکرت خودش.
32. [M] BrainPort صفر فراخوان — تولید متن لید/زیمان از آن رد شود یا DEAD-SOURCE.
33. [M] callbudget سراسری است؛ پک‌ها بودجهٔ توکن per-business ندارند — کلید bucket به tenant.
34. [L] پروپوزال‌های experiments دد-اند — خروجی به فایلی که دکتر/کاکپیت بخواند.
35. [L] render-obsidian یادگیری «wired nowhere» — مقصد تعیین یا حذف کارت-نوت.
36. [L] ماژول یتیم cockpit_self_model — حذف یا callback شدن.

## C — بدن برد‌ها / مش
37. [H] outbox شاهد ۱۸۲: **۲,۳۳۰ verdict هرگز ارسال نشده** (هیچ state.json = هیچ تلاشی) — send/درین وصل شود.
38. [H] پای ۱۳۸→۱۸۲ مش از **۱ سپتامبر ۱۴:۰۶ مرده**؛ inbox ۱۸۲: **۱۰,۴۲۶ ping نمک‌خورده** (همه expired) — احیا فرستندهٔ دقیقه‌ای + پاکسازی expired.
39. [H] outbox ۱۳۸: ۱۱ پیام گیر از ۲۸ اوت + همتای اشتباه `203.0.113.1` (IP تستی در config) — octomesh_process زمان‌بندی شود + peer اصلاح.
40. [H] inbox ۱۳۸: ۵ پیام هضم‌نشده از ۲۶ اوت؛ هیچ پروسه‌ای inbox نمی‌خواند — مصرف‌کننده وصل شود.
41. [H] outbox ۱۸۰: ۲۸ پیام (شامل دو megaprompt) هرگز ارسال نشد؛ octopus-drain فقط retry-با-state را می‌گیرد — منطق drain اول-ارسال اضافه شود.
42. [H] NATS (JetStream روی ۱۸۲) دقیقاً یک کلاینت لوکال دارد؛ صفر ناشر/مشترک بین‌بردی — اولین مشترک: 138 (publish رویدادهای legs).
43. [M] آینهٔ ۱۸۰ از لپ‌تاپ هر ۱۵ دقیقه fail (rsync rc=255 / CIFS credential ندارد) — credential یا جایگزین.
44. [M] ارجاع متقابل صفر: هیچ‌کس 8090/8081 مغز یا 879x پای‌ها را از بیرون صدا نمی‌زند — یک کلاینت reference بنویس.
45. [M] اسکژولر ۱۳۸ سبزِ دروغین: transportش (octomesh_send) از ۲۷ اوت هیچ نفرستاده — سبزِ Result=success باید وابسته به receipt ارسال شود.
46. [M] ۱۸۲: miniscientist-daily از دیروز failed؛ world-model در stop هنگ می‌کند؛ sensorium D-state با ۵۲٪ RAM؛ events.jsonl شاهد ۲۹MB بی‌هرس — چهار ترمیم جدا.
47. [M] ساعت ۱۳۸: NTP خاموش، +۰٫۵ ثانیه جلو — با TTLهای ۶۰ثانیه‌ای مش، خطر آرام envelope-expire — chrony/systemd-timesyncd روشن.
48. [L] وضعیت timesync ۱۸۲ ناشناخته (dbus timedatectl خراب) — ابزار جایگزین.

## D — بدهی‌های امروزِ خودم
49. [M] مسیر پیش‌فرض repo-dir شاهد برای چیدمان بورد غلط است → main_head لوکال UNKNOWN — env/arg برای repo dir.
50. [M] نبض events از ۰۲:۰۰Z کهنه (دکتر旗 گرفت) — ریشه‌یابی: تایمر imap/quote بعد از deploy چرا رسید نمی‌نویسند؟

— پایان. منوی سرعتِ پنج‌حرکتی: (۱)✓ تایمرها نصب شد (۲) درین مش #37-41 (۳) runner گلاس #26 که چهار مصرف‌کننده را یکجا باز می‌کند (۴) پالسِ دکتر #14 (۵) chrony #47.
