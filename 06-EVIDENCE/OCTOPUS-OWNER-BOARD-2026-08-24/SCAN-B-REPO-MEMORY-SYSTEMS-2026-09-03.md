# SCAN B — سیستم‌های حافظهٔ مخزن ofn-node — گزارش کامل کاوشگر
شناسه: `SCAN-B-REPO-MEMORY-SYSTEMS-2026-09-03` · read-only · پایه: origin/main = 60dce961

## یافته‌ها (۲۵، با file:line) — قالب: تولیدکننده→مصرف‌کنندهٔ غایب
1. [M] `memory_chain.chain_verify()` (memory_chain.py:51) هرگز صدا زده نمی‌شود — تولیدکنندگان زنده‌اند (imap_listener:37,177,219,265 و quote_engine:32,58,212 → state/memory-chain.jsonl) ولی ضدتحریف بی‌بازرس. فیکس: پروب در doctor.
2. [M] لجر یادگیری اقتصادی فقط با CLI دستی (`ofn/learning/cli.py:40-117`) نوشته می‌شود؛ رویدادهای زندهٔ نود به لجر دیگری می‌روند (`ofn/adapters/ledger.py` در node.py:687+).
3. [M] `telegram_glass.build_learning_snapshot` (telegram_glass.py:134-160) برای /money بی‌فراخوان است — مسیر لجر باید فراخوان‌دهنده بدهد، هیچ‌کس نمی‌دهد.
4. [M] کارت economic_learning کاکپیت به `09-LANES/ECONOMIC-LEARNING/runs/*/run-summary.json` می‌چسبد (cockpit_v2_read_model.py:199,3364) — تنها run دستی ۰۹-۰۲ است؛ کارت به UNKNOWN پیر می‌شود.
5. [M] `octopus_survival/economy.py:40,46` یادگیری را فقط تاکسونومی می‌داند؛ هیچ import از ofn.learning — خروجی یادگیری هرگز بر اقتصاد بقا اثر ندارد.
6. [L] پروپوزال‌های `ofn/learning/experiments.py:52,91-97` (PR_CREATED) به هیچ صف/فایلی نمی‌رسند.
7. [L] `learning.cli render-obsidian` (cli.py:129-173) «wired nowhere» (خود کارت surface.js:41 اعتراف می‌کند).
8. [H] مصرف‌کنندهٔ SYSTEM-SELF-MODEL.json وصل است (read_model:197,3269 → surface.js:26) ولی **تولیدش زمان‌بند ندارد** — تنها رسید، دستی (LA-SELF-AWARENESS/RECEIPT.md). [نکتهٔ به‌روزرسانی: تایمر octopus-selfmodel همان ساعت نصب شد]
9. [L] `ofn/adapters/cockpit_self_model.py` ماژول یتیم — صفر importer.
10. [H] `state/doctor/report.json` (doctor.py:42,512) صفر مصرف‌کننده — کارت «doctor» کاکپیت دکترِ LB-والت را می‌خواند (read_model:198,3151) نه این را؛ heartbeat هم نمی‌خواندش؛ /doctor گلاس منتظر caller-supplied snapshot است.
11. [H] SILENT_FLIP/STALE_CLAIM/تحریف لجر (external_witness.py:184,104) هیچ مسیر هشداری ندارد — هیچ‌یک از سه ماژول خودمختاری owner_notify را import نمی‌کنند؛ حتی گزارش شاهد فایل هم نمی‌شود (فقط stdout).
12. [H] `state/OWNER-QUEUE.md` (owner_absence.py:33,174-234) هیچ رندرکننده‌ای ندارد — /queue گلاس open_pr گیت‌هاب می‌خواند (telegram_glass.py:341) و کارت کاکپیت صف داخلی نود (run.py:331→node.py:2432) — نه این فایل را.
13. [✓] conservation-mode.json وصل است (نویسنده owner_absence:32، مصرف‌کننده قلاب deny در outbound_worker:226).
14. [L] تایمرهای خودمختاری فقط در ران‌بوک بودند (docs/runbooks/DEPLOY-doctor-witness-timers.md) نه در deploy/ مخزن. [تایمرها نصب شدند؛ ثبت درخزین باز]
15. [M] events.jsonl: نویسندگان چهارگانه (imap:58، outbound:134، owner_notify:46,68، quote:51) ولی خوانندگان فقط doctor.probe_pulse (تازگی) و `quote_pipeline.extract_m2_from_events` (110-119) که خودش «future use» بی‌فراخوان است.
16. [H] FLAG-CLAIMS دست‌نوشته؛ شاهد فقط سن measured_at را می‌سنجد (external_witness.py:154-176) نه مقدار — claimِ غلطِ تازه می‌گذرد؛ SILENT_FLIP فقط ویرایشِ فایل را می‌گیرد نه فاصله از واقعیت. فیکس: مود --remeasure با اجرای فرمان‌های فقط-خواندن هر claim.
17. [M] telegram_bridge (survival) فقط-فایل؛ اسناد متناقض (IGNITION-20260901:35 «E3 live» vs 138-CURRENT-TRUTH:6 «inactive_by_design»)؛ کارت گلاس config/telegram_policy.json می‌خواند نه این ماژول را.
18. [M] board_events: قرارداد کامل (HMAC+SQLite) بی‌فرستنده/بی‌گیرنده روی main — تنها مصرف‌کننده تست. (خانواده‌اش در DECISIONS.md:492 ممنوع).
19. [M] `ziman_tender_harvest.run()` (دوقفل owner_approval+OFN_WIRE_HARVEST) هیچ مسیر فراخوانی ندارد — حتی source_registry.py:90 فقط رشته‌اش را می‌نویسد، importlib ندارد.
20. [H] فایل claim برداشت زیمان (ziman_tender_harvest.py:23,41) می‌گوید «شاهد بیرونی می‌خواند» — witness.run() (208-223) فقط main_head و flag_claims را چک می‌کند؛ claim جایی در شاهد نیست.
21. [M] source_registry: probe_all فقط فرمان دستی MEGA-DATA؛ نود رجیستری جدا و دست‌نویس می‌خواند (node.py:3841→lead_store.ensure_source_registry:1655 از data/painting_source_registry.json) — دو رجیستری ناهم‌خوان.
22. [M] ShopifyConnector (shopify_connector.py:24+) صفر instantiation؛ run.py:160-168 فقط CommerceConnector عمومی را ثبت می‌کند → POST سفارش شاپ‌فای به /api/v1/webhooks/{tenant}/shopify (http_api.py:430) fail-closed «unknown connector» — سفارش هرگز نمی‌رسد.
23. [M] BrainPort (helpers/brainport.py) صفر فراخوان در کل مخزن — ALLOW چهارتایی بی‌استفاده.
24. [M] CallBudget تک‌نمونهٔ سراسری (run.py:568؛ تحلیل در node.py:326,422,1707,3587) — پک‌ها کلید بودجهٔ مدل ندارند (packs/ziman.yaml فقط gate-tier).
25. [M] telegram_glass پوستهٔ شش-فرمانی بی‌runner — هیچ ماژولی روی main آن را import نمی‌کند؛ همه‌شان منتظر snapshotهای بی‌عرضه (doctor_snapshot:252، ledger_rows:134، open_prs:341). فراهم‌کردن runner = کلید یافته‌های ۳/۱۰/۱۲.

## مثبت‌های وصل (برای صداقت سرشمری)
کاکپیت→SELF-MODEL/LB-runs/ECON-runs/صف داخلی؛ قلاب conservation؛ نبض دکتر؛ سنِ FLAG-CLAIMS در شاهد؛ نود→painting_source_registry؛ http_api→CommerceConnector؛ heartbeat→owner_notify.
