# 08 — MEMORY INTEGRATION · ۲۰۲۶-۰۷-۳۱

## واقعیتِ سنجیده (پیش از این جلسه)

- حافظه عملاً **write-only** بود: تنها مصرفِ تصمیمی در کلِ ارگانیسم
  `outcomes/lead_outcome_recorder.py:96-113` (demote/promote ِ lead)؛
  `consolidate.recent_semantic()` صفر صداکنندهٔ تولیدی؛ planner ِ cortex و
  چرخهٔ خودهدف صفر خواندن.
- مسیرِ نوشتن سالم بود: verdicts → `goal_action_bridge.consolidate_new_verdicts`
  → MemoryGate (episodic، outcome-bound، idempotent).

## چه چیزی وصل شد (این جلسه، flag-off)

`goal_action_bridge._recall_for_goal` — پیش از `prepare_records` در هر چرخه:

```text
query   goal ِ متن + goal_key + candidate_key   (goal_key عمداً: ردیف‌های
        consolidate دقیقاً «goal=<goal_key>» را حمل می‌کنند)
store   memory/memory_store.MemoryStore().search  (FTS، namespaceهای episodic/semantic)
output  ساخت‌یافته: memory_id / namespace / trust / created_at / why("fts:…")
        — متنِ خام هرگز (جهشِ MR2 قرمز)
sink    out["memory"] ِ پل → دفترِ چرخه: `action_memories_used` (مشاهده‌پذیر)
گارد    فلگ OCTOPUS_WIRE_MEMORY_READ خاموش=هیچ · fail-soft با reason ·
        plan با/بدونِ retrieval بایت‌به‌بایت یکسان (memory ≠ authority — سنجهٔ صریح)
```

## چه چیزی عمداً وصل **نشد**

مصرفِ تصمیمیِ retrieval (تغییرِ plan بر اساسِ حافظه). قاعدهٔ §۱۰.۵ مگاپرامپت:
اول A/B ِ ثابت (planner ± retrieved memory؛ کیفیتِ انتخاب/تکرارِ شکست/هزینه)،
و «فقط برای حافظه‌دار شدن» فعال نکن. سابقهٔ سیستم همین را حکم می‌کند:
lead_outcome_recorder قبلاً «۱ citation در ۳۲ receipt، صفر اثر» را ثبت کرده —
citation ِ تزئینی ارزش نیست. A/B = کارِ نشستِ بعد؛ ورودی‌اش حالا وجود دارد
(`action_memories_used` در دفترِ هر چرخه).

## قراردادِ لایه‌ها (بدونِ store ِ نو)

```text
machine memory   state/** + memory.db + outcomes.db + spine.db   (runtime می‌خواند)
human knowledge  Obsidian/_memory                                 (runtime هرگز authority نمی‌گیرد)
```
