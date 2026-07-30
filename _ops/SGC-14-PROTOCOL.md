---
type: protocol
project: OCTOPUS
status: active
scope: SGC-14 — پروتکل، مدلِ تهدید، runbook، بازگشت، گیت‌های مالک
tags: [octopus, self-goal, protocol, sgc-14, threat-model, runbook]
created: 2026-07-30
updated: 2026-07-30
---

# SGC-14 — پروتکلِ اجرایی

> ## ⚠️ نامِ صادقانهٔ آنچه امروز ساخته شده
>
> این **حلقهٔ ارزیابیِ خودهدف‌گذاری** است، نه **حلقهٔ خودتکمیلی**.
>
> امروز زنجیره این است:
> `جهت → هدف → پیش‌ثبت → مشاهده → حکم → روشِ بعدی`
>
> و چیزی که هنوز **نیست**:
> `جهت → هدف → نقشه → اقدامِ مجاز → رسید → مشاهده → حکم`
>
> `test_cycle.run()` متنِ روش را **ثبت** می‌کند و سنجه‌ها را **مشاهده** می‌کند؛
> آن متن را به یک اقدامِ اجرایی تبدیل نمی‌کند. پس وقتی هدف می‌گوید «لیدهای
> آمادهٔ claim را بررسی کن»، هیچ‌کس آن بررسی را انجام نمی‌دهد — ارزیاب درست
> `FAIL` می‌دهد و مولد روشِ دوم را انتخاب می‌کند، ولی روشِ دوم هم یک **رشته**
> می‌ماند.
>
> این شکاف عمدی و مستند است، نه پنهان: **پلِ اقدام (Goal Action Bridge)** فازِ
> بعد است و باید طبقه‌بندیِ اقدام داشته باشد —
> `measure-only` (خودکار) · `internal-reversible` (فقط allowlist) ·
> `owner-card` (کارتِ دقیق) · `external/spend` (BLOCKED_BY_OWNER) · `forbidden`.
> برای `attribution.claimed` خروجیِ امن هرگز ساختنِ claim مصنوعی نیست؛ یا لیدِ
> واجدِ شرایطِ مشخص است، یا blocker ِ واقعی. **نبودِ داده با تولیدِ داده حل نمی‌شود.**
> (کشفِ بازبینِ موازی، ۲۰۲۶-۰۷-۳۰ — پذیرفته شد.)

> آستانه‌ها این‌جا **نیستند** — عمداً. آن‌ها در
> [[SGC-14-PREREGISTRATION]] منجمدند با `mtime = 2026-07-30T13:30:39`،
> یعنی قبل از چرخهٔ ۱ (`2026-07-31#0`). این فایل می‌گوید *چطور*، آن فایل می‌گوید
> *چه چیزی قبول است*. جدا بودنشان عمدی است.

## ۱. ماشینِ حالتِ هر چرخه

```text
PROPOSED      goal_generator.propose() — کاندیدا از (جهت × وضع × سنجهٔ روی دیسک)
   ↓ validate() — سنجهٔ ناموجود / target بد / baseline بد ⇒ اینجا می‌میرد
VALIDATED
   ↓ prereg.register() — append-only، یک ردیف به‌ازای هر cycle_id
PREREGISTERED   ⟵ شکستِ نوشتن = fail-closed، چرخه اجرا نمی‌شود، اسلات هم نمی‌سوزد
   ↓ (v1: هیچ گیتِ مالکی لازم نیست — measure-only)
APPROVED_IF_REQUIRED
   ↓ test_cycle.run() — مشاهدهٔ سنجه‌ها + ثبتِ روش/چرخش + mark_done
EXECUTING → OBSERVED
   ↓ cycle_evaluator.evaluate_pending() — پس از deadline_cycles، از **دیسک**
EVALUATED
   ↓
COMPLETE(PASS) | PARTIAL | FAILED | BLOCKED
   ↓ حکم به دفترِ verdicts می‌رود و **مولدِ چرخهٔ بعد آن را می‌خواند**
CONSOLIDATED   ⟵ حلقه بسته: FAIL ⇒ روشِ بعدی (pivot مکانیکی، نه ادعایی)
```

هر گذارِ غیرمجاز fail-closed است. سه نقطهٔ قفل:
`validate()` · `prereg.register()` · `due()`؛ و `mark_done` فقط بعد از اجرای موفق.

## ۲. نقشهٔ فایل‌ها

| نقش | فایل | صداکننده |
|---|---|---|
| مولدِ هدف | `_ops/cortex/goal_generator.py` | `test_cycle.beat` |
| پیش‌ثبت | `_ops/prereg.py` | `test_cycle.beat` |
| اجرای چرخه | `_ops/test_cycle.py` (`beat`/`run`/`record`/`scorecard`) | `organism.py:761` (هر تیک، خودش گیتِ کادنس دارد) |
| ارزیابِ مستقل | `_ops/cycle_evaluator.py` | `test_cycle.beat` (اولین قدم) |
| سنجهٔ ابزار | `_ops/tool_request.py` | `organism.py:733` |
| سنجهٔ بازیابی | `_ops/recall_trend.py` | `organism.py:751` |
| گاردِ مقصدِ پچ | `_ops/cortex/target_guard.py` | `code_autonomy.allowed_target` |

**دفترها** (همه append-only، زیرِ `_ops/state/`):
`test_cycle/prereg.jsonl` · `test_cycle/journal.jsonl` · `test_cycle/verdicts.jsonl` ·
`test_cycle/state.json` (اسلات‌های سوخته) · `neural/recall-trend.jsonl` ·
`telegram/tool-requests.jsonl`

## ۳. مدلِ تهدید — و اینکه کدام کنترل کجاست

| # | تهدید | کنترلِ پیشگیر | شاهدِ آشکارساز | تست |
|---|---|---|---|---|
| ۱ | هدفِ دایره‌ای برای بالا بردنِ نمرهٔ خودش | کاتالوگِ rule-based؛ هیچ کاندیدا الگوی `_CIRCULAR` را نمی‌زند | `candidate_key` در prereg | `test_goal_generator` |
| ۲ | هدفِ بی‌ترازو («بعداً می‌سازمش») | `validate()` سنجه را **همین حالا** روی دیسک می‌خواند | `skipped[].reason = metric-not-on-disk` | `t_no_metric_on_disk_means_no_goal` |
| ۳ | غیابِ شاهد = موفقیت | `read_metric` روی فایلِ غایب `None` می‌دهد نه ۰ | حکمِ `BLOCKED` | `t_absent_file_reads_none_not_zero` |
| ۴ | جابه‌جاییِ آستانه پس از نتیجه | target فقط در prereg؛ evaluator APIای برای تغییرش ندارد | ناوردیِ بایتیِ prereg | `t_evaluator_never_mutates_the_preregistration` |
| ۵ | تکرارِ روش به‌عنوان pivot | کلیدِ روش روی **محتوا**؛ چرخش فقط پس از `FAIL` | `method_note=pivot-after-FAIL` | `t_pivot_only_after_independent_fail` |
| ۶ | تستِ سبز روی تابعِ بی‌صداکننده | `beat` تابعی اجرا می‌شود، نه grep ِ سورس | ردیفِ واقعی روی دیسک | `t_beat_runs_the_full_chain...` |
| ۷ | دوبار-شلیک در یک اسلات | `due()` + `state.json` (بین ری‌استارت‌ها هم می‌ماند) | ۱ ردیف به‌ازای هر `cycle_id` | همان تست + اثباتِ زندهٔ ری‌استارتِ ۱۳:۱۸ |
| ۸ | پیش‌ثبتِ شکسته ولی اجرا ادامه | `prereg-failed` ⇒ صفر اجرا، اسلاتِ نسوخته | — | `t_prereg_failure_blocks_execution` |
| ۹ | دروغِ سنجش از تصادمِ صداکننده | چرخه سنجه را **مشاهده** می‌کند نه دوباره شلیک | ناوردیِ بایتیِ دو دفتر | `t_the_cycle_observes_the_meters...` |
| ۱۰ | نویزِ per-tick که سری را بی‌معنا کند | dedupe روی محتوا + نبضِ ۶ساعته | رشدِ +۱ به‌جای +۶ در ۴ دقیقه (سنجیده) | ۳+۲ چکِ نو |
| ۱۱ | پچ به قانونِ اساسی/سوییت/کیل‌سوییچ | `target_guard`: resolve → containment → deny | `reason=outside-allow-roots` / `deny:*` | `test_target_guard` (۱۴) |
| ۱۲ | صفِ خالی به‌عنوان تضمینِ ایمنی | ⚠️ **هنوز باز** — `PATCH_CARD` خاموش است، ولی این گارد نیست | — | VQ-AUTONOMY-QUEUE-001 |
| ۱۳ | ری‌استارت که فیکس را زنده نکند | هر ادعا با جفتِ قبل/بعدِ بوت سنجیده شد | `HEARTBEAT.md` + PID | این جلسه: ۳ ری‌استارت، هر سه سنجیده |
| ۱۴ | نوشتنِ بی‌صدا-شکسته | ⚠️ **کشف‌شده و باز** — `ORGANISM-STATE.json` از ۱۱:۵۱ گیر است | mtime در برابرِ heartbeat | VQ-STATE-WRITE-001 |
| ۱۵ | هانکِ بیگانه واردِ کامیت | هیچ `git add -A`؛ فقط pathهای دقیق | `git status` قبل/بعدِ هر کامیت | این جلسه: ۴ فایلِ dirty دست‌نخورده ماند |

## ۴. Runbook

**شروع** (از فردا، `2026-07-31#0`): کاری لازم نیست — ارگانیسم زنده است، سه فلگ
مسلح‌اند، و `due()` خودش اسلات را باز می‌کند. فقط هر روز یک نگاه:

```bash
python -X utf8 "F:\backup\_ops\test_cycle.py"
```

(کارتِ نمرهٔ خام + وضعِ اسلات. بی‌آرگومان، read-only.)

**دیدنِ حکم‌ها:**

```bash
python -X utf8 "F:\backup\_ops\cycle_evaluator.py"
```

**کارتِ تلگرام:** `test_cycle.card()` و `tool_request.card()` هر دو zero-arg اند،
پس `capability_registry` خودش پیدایشان می‌کند.

## ۵. بازگشت (rollback)

| چه چیزی | دستور | اثر |
|---|---|---|
| خاموشیِ نرم | سه فلگ در `OCTOPUS-flags.cmd` را `0` کن + ری‌استارت | صفر I/O، دفترها می‌مانند |
| توقفِ آنی | ساختنِ `_ops/STOP-ORGANISM` | کلِ ارگانیسم، تمیز |
| برگشتِ کد | `git -C F:\backup reset --keep 1ddc058` | HEADِ قبل از این جلسه |
| برگشتِ فلگ‌ها | فایلِ پشتیبانِ `OCTOPUS-flags.cmd.bak-20260730` در scratchpad | ۳۱٬۳۶۰ بایت، CRLF=709 |
| برگشتِ دو فایلِ dirty | `LIVE-code_autonomy.py.bak` / `LIVE-test_code_autonomy.py.bak` | نسخهٔ پیش از ویرایشِ من |

`reset --keep` عمدی است نه `--hard`: اگر کارِ کامیت‌نشده‌ای از دست برود، **رد
می‌کند** به‌جای اینکه بی‌صدا پاکش کند.

## ۶. گیت‌های مالک — چه چیزی هنوز تپِ توست

```text
✅ داده شد (۲۰۲۶-۰۷-۳۰): آرم‌کردنِ سه فلگ · ری‌استارتِ organism ·
   وصل‌کردنِ target_guard · برداشتنِ telegram_center از allowlist ·
   چرخشِ لاگ N=30 · هدفِ اولِ چرخه = attribution.claimed ·
   max_circular=6 تا ۰۸-۰۶ (تاریخ‌دار، خودبه‌خود برمی‌گردد)

⛔ هنوز تپِ تو لازم است:
   OCTOPUS_WIRE_PATCH_CARD          قفلِ چهارمِ اعمالِ خودکارِ کد
   merge به master · deploy · push
   هر خرجِ فراتر از US$200 پنجرهٔ آزمون
   ارسالِ واقعی به بیرون (غیر از کارتِ خودت)
   L3 واقعی (چهار پیش‌شرطِ مکانیکیِ §۲.۵ منشور، هیچ‌کدام انجام نشده)
```

## ۷. پنجره‌های تاریخ‌دار — چه چیزی خودبه‌خود تمام می‌شود

هر استثنای این آزمون تاریخِ انقضا دارد، در **خودِ کد** نه در یادِ کسی. یک استثنای
بی‌تاریخ، استثنا نیست — قاعدهٔ نو است.

| استثنا | مقدار | تا | بعدش | مکانیزم |
|---|---|---|---|---|
| سقفِ خرج | US$200 | ۲۰۲۶-۰۸-۰۶ | AU$30/ماه | `GOALS-OCTOPUS.md` (متنی — **دستی**) |
| سهمیهٔ دایره‌ای | 6 | ۲۰۲۶-۰۸-۰۶ | 2 | `goal_directed.max_circular_now()` (**خودکار**) |

⚠️ تفاوتشان مهم است: دومی خودش برمی‌گردد و تستش (`t_rerank_enforces_the_expiry_without_anyone_editing_anything`) این را قفل کرده؛ اولی هنوز به یادآوریِ انسان وابسته است.
