# 02 — CONFLICT MAP · درخت زنده در برابر گیت · ۲۰۲۶-۰۷-۳۱

> بزرگ‌ترین یافتهٔ ساختاری این مأموریت. مگاپرامپت §۴.۱: «هیچ فایلِ dirty ِ
> ناشناخته را overwrite نکن؛ conflict map بساز». این همان نقشه است.

## صورت مسئله

درخت زنده (`F:\backup`، شاخهٔ `fix/tg-p2-2026-07-30`) **~۱۲۰ فایلِ tracked ِ
تغییرکردهٔ کامیت‌نشده** زیر `_ops` دارد (‏+۲۶٬۴۸۰ / −۵٬۳۲۶ خط) به‌علاوهٔ
~۶۵ فایلِ کد/تستِ untracked (پیش از نجاتِ این جلسه). ارگانیسمِ زنده **همین
نسخهٔ dirty را اجرا می‌کند** — یعنی گیت دیگر منبعِ حقیقتِ رفتارِ زنده نیست.
هر checkout/clean یک ریسکِ واقعیِ regression ِ زنده است.

## چه چیزی در این جلسه حل شد (کمینهٔ لازم برای سازگاری شاخه)

| اقدام | فایل‌ها | چرا مجاز |
|---|---|---|
| نجاتِ untracked (کپی، بایت‌به‌بایت) | owner_console (۱۳) + ۷ ماژول + ۴۴ تست | کد tracked (center.py:1384، wiring.py:77، run_all TESTS) به آن‌ها وابسته بود؛ کپی هیچ‌چیزِ زنده را لمس نکرد |
| پذیرشِ ۳ فایلِ dirty | mission_contract.py، memory/gate.py، memory/memory_store.py | `pipeline.py` ِ tracked و تست‌های tracked بدونشان TypeError می‌دهند؛ عیناً بایت‌های در حالِ اجرای زنده |

## چه چیزی عمداً حل نشد (رأی/جلسهٔ مالکِ آن لِین)

~۲۵ فایلِ کدِ dirty ِ دیگر، از جمله پرریسک‌ها:

```text
telegram_center/center.py (+verb tr و بیشتر)   budget/approval_channel.py
telegram_center/render.py · mission.py · mission_runner.py · power.py · intent.py
cortex/self_model.py · auto_approve.py · code_autonomy.py · stress.py · web_research.py
doctor/self_knowledge.py · heart/control_law.py · legs/lead_scorer.py · self_patch.py
live/server.py · live_loop.py · organ_dialogue.py · synapse/sense.py · phase_gate.py
held_out_evaluator.py · c6_producer.py · budget/capability_gate.py · needs_digest.py
+ ~۲۰ فایلِ تستِ tracked ِ dirty
```

اثرِ مستقیم روی سوییت: **۲۹ از ۳۶ قرمزِ baseline** ‏CONFLICTED اند — تست یا
سوژه‌اش فقط با نسخهٔ dirty سبز می‌شود (`baseline-classification.json`).
نمونهٔ صریح: `test_tg_callback_emitter_parity` (verb ِ `tr` فقط در center ِ
dirty) — عمداً در run_all ثبت **نشد**.

## کارتِ رأی پیشنهادی — VQ-LIVE-DIRTY-RECONCILE-001

```text
Decision   کارِ کامیت‌نشدهٔ جلسه‌های موازی روی درخت زنده یا کامیت شود یا رد
Effect     git add/commit ِ انتخابی روی F:\backup (شاخهٔ tg-p2) توسطِ جلسه‌ای
           که مالکِ آن فایل‌هاست — نه این شاخه
Why        درخت زنده و گیت هم‌گرا شوند؛ ۲۹ سوییتِ CONFLICTED قابلِ‌قضاوت شوند؛
           ریسکِ «clean = regression زنده» بسته شود
Blast      صفر رفتاری (کد از قبل در حال اجراست)؛ فقط ثبتِ گیت
Rollback   git reset --keep به کامیتِ قبلِ ثبت
Stop       اگر فایلِ dirty حاوی secret بود → توقف + چرخش
```
