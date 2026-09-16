---
type: runbook
status: done
created_by: agent
tags: [ops, agents, selfimprove, changelog]
created: 2026-07-04
updated: 2026-07-06
---

# Scale-up ناوگان خودبهبودی — aggressive ~۱۰× (توضیح تغییرات)

> درخواست آری (2026-07-04): «سرعت خودتو ۱۰ برابر کن با اسکجل‌های بیشتر و عمیق‌تر و تندتر آپدیت‌کردن خودت» + «هیچی‌رو کامل حذف نکن، فقط اضافه کن و توضیح ذخیره کن».
> این نوت همان «توضیحِ ذخیره‌شده» است. **هیچ تسک یا نوتی حذف/بازنویسی نشد؛ همه‌چیز additive بود** (دو تغییرِ موجود فقط cron + متنِ append‌شده — هیچ دستورالعملی پاک نشد).

## تصمیم‌ها (از AskUserQuestion)

- **شدت:** تهاجمی (aggressive). می‌پذیریم که گاهی چتِ زندهٔ آری کند/rate-limit شود؛ همه propose-only و برگشت‌پذیر.
- **کنترلِ سیل:** تریاژ + consolidator تندتر (هر ۳ ساعت) + خلاصهٔ اجراییِ روزانه.

## چه چیزی اضافه شد (۶ تسک نو — همه propose-only، بدون notification)

| taskId | نقش (خانواده) | cron | زمان‌ها |
|---|---|---|---|
| `selfimprove-safety` | گیت/halt/آدیت/اعتماد (R-01…R-09) | `1-59/15 * * * *` | staggered |
| `selfimprove-memory` | substrate/kin/evaporation/CoALA | `4-59/15 * * * *` | staggered |
| `selfimprove-orchestration` | fleet/consensus/topology/selection | `7-59/15 * * * *` | staggered |
| `selfimprove-nature` | زیست‌الگو: مکانیزم طبیعت → معماری | `10-59/15 * * * *` | staggered |
| `selfimprove-tooling` | typed-interfaces/config/observability | `13-59/15 * * * *` | staggered |
| `selfimprove-deep` | **عمق**: deep-research روی پرلوریج‌ترین آیتم باز | `20,50 * * * *` | هر ۳۰ دقیقه |

هر لاین: GATE و autonomy را **کلمه‌به‌کلمه** از `architect-selfimprove` ارث برده (propose-only، فقط `00 - Inbox/scout-digests/`، هرگز canon/secret/_code/People/_Archive/_Duplicates). خروجی هر لاین اسلاگِ خانواده‌ای دارد (`… selfimprove-safety.md` و …) و کلیدِ `salience:` برای تریاژ.

## چه چیزی تغییر کرد (۲ تسک موجود — فقط cron + متنِ append، بدونِ حذف)

- **`architect-selfimprove`**: cron `*/15` → **`*/3`** (لاینِ general/overflow، سریع و سبک). پرامپتِ قبلی کاملاً حفظ شد؛ فقط یک بلوکِ «CADENCE + FLEET UPDATE» ته‌اش اضافه شد (anti-overlap، آگاهی از ۵ لاین، سبک‌ماندن). notification خاموش شد (جلوگیری از اسپم در ۴۸۰ اجرا/روز).
- **`mycelial-consolidator`**: cron `0 22 * * *` → **`0 */3 * * *`** (هر ۳ ساعت). هفت STEP قبلی دست‌نخورده؛ بلوکِ «CADENCE + TRIAGE» اضافه شد: هر اجرا = تریاژِ سبک → `_TRIAGE-BOARD.md` (top ~۱۲ بر اساس salience)؛ فقط اجرای شبانه (≥۲۱:۰۰) = سنتزِ کاملِ قبلی + `exec-digest.md`. اجراهای غیرشبانه synthesis نمی‌نویسند (ضدِ bloat).

## ریاضیِ throughput (~۱۰×)

- قبل: `architect-selfimprove` هر ۱۵ دقیقه ≈ ۹۶ اجرا/روز.
- بعد: general `*/3` (۴۸۰) + ۵ لاین × `*/15` (۴۸۰) + deep `*/30` (۴۸) ≈ **~۱٬۰۰۸ اجرا/روز ≈ ~۱۰.۵×**.
- عمق: لاینِ `selfimprove-deep` تنها لاینی است که deep-research کامل می‌زند (هر ۳۰ دقیقه)؛ بقیه سریع/متمرکز.
- تنوع: پارتیشنِ ۵-خانواده‌ای = requisite variety (هم‌راستا با فلسفهٔ خودِ سیستم)، dedup بین‌لاینی خودکار چون همه علیهِ `*selfimprove*` گرپ می‌کنند.

## گاردریل‌ها

- **همه propose-only** — هیچ لاین/consolidator چیزی خارج از `00 - Inbox/scout-digests/` نمی‌نویسد و canon/secret را لمس نمی‌کند.
- **anti-overlap** در general lane (`*/3`): اگر اخیراً همان آیتم نوشته شده، بی‌صدا خروج.
- **anti-waste**: هر لاین اگر آیتمِ نو نداشت «light reflection» می‌نویسد، نه dive اجباری.
- **evaporation** فقط status-flip روی دیجست‌های >۱۴ روز است (برگشت‌پذیر، نه حذف) — با «هیچی حذف نشود» سازگار.

## ریسک‌ها

- **سقفِ نرخ:** ~۱۰۰۰ اجرا/روز پنجرهٔ نرخِ پلن (مشترک با چتِ تعاملی) را سنگین می‌کند؛ آری آگاهانه پذیرفت. اجراها در فشار صف می‌شوند، خراب نمی‌شوند.
- **self-overlap** لاینِ `*/3` وقتی اجرا >۳ دقیقه طول بکشد؛ کاهش‌یافته با «سبک بمان» + timestamp + dedup (بدترین حالت: یک دیجستِ نزدیک‌تکراری که تریاژ می‌گیردش).
- **سیلِ Inbox:** با تریاژ + `_TRIAGE-BOARD` + exec-digest مهار شد.

## دایال‌بک (اگر زیاد بود)

- کندتر: `architect-selfimprove` → `*/5` یا `*/15` (بازگشت به قبل).
- توقفِ موقت هر لاین: در سایدبارِ Scheduled غیرفعال (disable) کن — تسک می‌ماند، فقط pause.
- عمق کمتر: `selfimprove-deep` → `0 * * * *` (ساعتی) یا disable.
- consolidator → `0 22 * * *` (فقط شبانه، حالتِ قبل).

## لینک‌ها

- [[05 - Agents/Research Scout Fleet]] · [[05 - Agents/AGENT_REGISTRY]] · [[01 - Dashboard/HANDOFF]]
- طرحِ salience/trace-index مرتبط: [[00 - Inbox/scout-digests/2026-07-04 1922 selfimprove]] (Legible Pheromone Map).
