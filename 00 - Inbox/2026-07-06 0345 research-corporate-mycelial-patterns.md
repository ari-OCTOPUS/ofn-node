---
type: research
status: ready
tags: [mycelium, architecture, resilience, cell-based, reconciliation, chaos-engineering]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html"
  - "https://github.com/aws-solutions-library-samples/guidance-for-cell-based-architecture-on-aws"
  - "https://www.chainguard.dev/unchained/the-principle-of-reconciliation"
  - "https://arxiv.org/pdf/1702.05849"
  - "[[04 - Architect System/MYCELIAL-MASTER-SPEC]]"
---

# معماری قارچی در مقیاس شرکت‌های بزرگ — همان الگوها با اسم‌های دیگر

> خواسته آری: «شرکت‌های بزرگ این معماری قارچی را چطور پیاده کرده‌اند؟» جواب کوتاه: هیچ‌کدام اسمش را mycelium نمی‌گذارند، ولی چهار خاصیت اصلی میسلیوم — **بدون مرکز واحد، جداسازی خسارت، خودترمیمی از حالت مطلوب، تست بقا با آسیب عمدی** — دقیقاً چهار الگوی production استاندارد است. نگاشت هر یک به اندام موجود vault + درس قابل‌برداشت.

## ۱. AWS — Cell-based architecture + Shuffle sharding (جداسازی هیف‌ها)

**الگو:** سیستم به سلول‌های مستقل خودکفا partition می‌شود؛ خرابی هر سلول فقط زیرمجموعه کوچکی از کاربران را می‌گیرد (bulkhead کشتی). shuffle sharding هر tenant را به زیرمجموعه هم‌پوشان-ولی-یکتای سلول‌ها می‌دهد — تا ۷ برابر مؤثرتر از sharding عادی، با رشد factorial.
**معادل قارچی:** میسلیوم از هیف‌های جدا-ولی-متصل ساخته شده؛ قطع یک رشته کل شبکه را نمی‌کشد.
**معادل vault:** جداسازی per-tenant (P5)، پوشه مستقل هر پروژه با PROJECT.md خودش، data_classification در L2c، قاعده C17.
**درس قابل‌برداشت:** blast-radius هر جهش Engine باید صریح باشد — الان whitelist داریم (خوب) ولی «این جهش حداکثر چند فایل/تسک را می‌تواند خراب کند» محاسبه نمی‌شود. یک فیلد `blast_radius` در header هر PROMPT-vN ارزان و مفید است.

## ۲. Google/Kubernetes — Reconciliation loop (خودترمیمی میسلیومی)

**الگو:** controller دائماً «وضعیت واقعی» را با «وضعیت مطلوب اعلامی» مقایسه می‌کند و diff را می‌بندد — برای همیشه. node بمیرد، controller در sync بعدی جایگزین می‌سازد. سیستم‌های پیچیده = **پشته‌ای از controllerها، هر کدام مالک یک سطح انتزاع**.
**معادل قارچی:** میسلیوم بعد از قطع‌شدن، به‌سمت الگوی رشد قبلی بازمی‌روید — desired state در خود شبکه است.
**معادل vault:** این دقیقاً معماری موجود ماست و قبل از این تحقیق ساخته شده: RATIFIED-TASKS = desired state؛ چک «تطبیق زمان‌بند↔جدول ratified» هر جلسه = reconciliation؛ خودترمیمی §۳.۳ منشور = controller؛ HEARTBEAT = status. حفره bootstrap که کشف کردید (وقتی همه تسک‌ها بمیرند controller هم مرده) همان مسئله کلاسیک «چه کسی controller را reconcile می‌کند» است — جواب صنعت: controller سطح بالاتر خارج از سیستم (در ما: لنگر جلسه تعاملی + آری).
**درس قابل‌برداشت:** الگوی «پشته controller» را صریح کنیم: boot-interview → ratified-reconciler → learning-loop → scoutها، هر کدام فقط سطح خودش را ترمیم کند و بالادستی پایین‌دستی را.

## ۳. Netflix — Chaos engineering (تست بقای عمدی)

**الگو:** از مهاجرت ۲۰۰۸ به cloud: به‌جای امید به سلامت، **خرابی عمدی تزریق کن** (Chaos Monkey) و ببین سیستم خودش ترمیم می‌کند یا نه؛ بعد پلتفرم خودکارِ تولید و اجرای آزمایش‌های chaos ساختند و آن را به تیم‌ها decentralize کردند.
**معادل قارچی:** قارچ در جنگل دائماً جویده/قطع می‌شود؛ بقا یعنی طراحی برای آسیبِ همیشگی، نه آسیبِ استثنایی.
**معادل vault:** منشور §۸.۶ «تست پذیرش: حذف عمدی یک تسک» — طراحی شده ولی هنوز اجرا نشده (معوق ۲ beat موفق). Layer-Isolated Evaluation در DEEP-GAP (شکاف ۶) هم همین regression-injection را می‌خواهد.
**درس قابل‌برداشت:** یک «Chaos Friday» ماهانه سبک: عمداً یک تسک ratified را disable کن، ببین reconciler جلسه بعد می‌گیردش؛ عمداً یک فایل با الگوی secret بساز (فیک)، ببین گاردها می‌گیرند. نتیجه در ledger. این ارزان‌ترین راه سنجش «خودترمیمی واقعی vs کاغذی» است.

## ۴. Amazon Dynamo / Cassandra — Gossip (اطلاعات بدون مرکز)

**الگو:** هر node دوره‌ای با چند node تصادفی «شایعه» مبادله می‌کند؛ membership و سلامت بدون هیچ مرکز واحدی به کل خوشه می‌رسد؛ مرگ هر node را همسایه‌ها کشف می‌کنند. (طراحی پایه Dynamo paper و Cassandra؛ جزئیات نسخه‌های امروزی را جدا verify کن.)
**معادل قارچی:** سیگنال شیمیایی در شبکه هیفی — نزدیک‌ترین معادل واقعی به «mycelial network».
**معادل vault:** دیجست‌های scout + `_Mycorrhizal Map` + consolidator شبانه = نسخه‌ی ما؛ ولی جریان ما **ستاره‌ای** است (همه به consolidator)، نه گسیپی (scoutها همدیگر را نمی‌بینند).
**درس قابل‌برداشت:** لازم نیست گسیپ واقعی بسازیم (P7: بودجه پیچیدگی)؛ نسخه ارزانش را داریم — فقط قاعده «هر دیجست، خط Cross-domain اجباری» را به «هر scout اول دیجست دیروزِ دو scout همسایه‌اش را بخواند» ارتقا بدهیم؛ گسیپ یک‌طرفه با هزینه صفر زیرساخت.

## ۵. جمع‌بندی — ما کجاییم

| خاصیت میسلیوم | الگوی صنعت | وضعیت vault |
|---|---|---|
| جداسازی خسارت | cell/bulkhead/shuffle-shard (AWS) | ✅ طراحی per-tenant؛ ⬜ بدون blast_radius عددی |
| خودترمیمی از desired state | reconciliation loop (K8s) | ✅ ساخته و زنده (RATIFIED + §۳.۳)؛ ⬜ پشته controller صریح نیست |
| تست بقا | chaos engineering (Netflix) | ⬜ طراحی‌شده (§۸.۶)، هرگز اجرا نشده |
| سیگنال بدون مرکز | gossip (Dynamo/Cassandra) | 🟡 ستاره‌ای از طریق consolidator؛ گسیپ همسایه‌ای = ارتقای ارزان |

نکته استراتژیک: شرکت‌ها این الگوها را در **زیرساخت تعیینی** (کد/کانتینر) پیاده کرده‌اند؛ نوآوری واقعی vault این است که همین‌ها را روی **لایه markdown + LLM-tasks** پیاده می‌کند. ریسک آشنا هم همان است که DEEP-GAP گفت: بدون ارزیاب تعیینی، خودترمیمیِ LLM-محور می‌تواند «ترمیمِ به‌ظاهر» باشد — پیشنهاد canary (تحقیق قبلی) پادزهر همین است.

## پیشنهادهای verdict-خواه (به ترتیب هزینه)

1. Chaos-test اول: همان تست §۸.۶ منشور را بعد از ۲ beat موفق اجرا کنیم (تقریباً مجانی).
2. فیلد `blast_radius` در header نسخه‌های PROMPT-vN (یک خط).
3. گسیپ همسایه‌ای یک‌طرفه در پرامپت scoutها (ویرایش پرامپت، پشت verdict چون تسک‌های دیگر است).
4. مستندکردن «پشته controller» در MYCELIAL-MASTER-SPEC §معماری (افزایشی).
