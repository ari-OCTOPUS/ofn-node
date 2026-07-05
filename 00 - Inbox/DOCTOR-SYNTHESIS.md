---
type: knowledge
status: active
created_by: agent
updated: 2026-07-06
tags: [doctor, synthesis]
---

# DOCTOR-SYNTHESIS — نگاشت تحقیق به ۷ تصمیم باز §۹

> بازتولید خودکار توسط تسک `doctor-research-aggressive` (بدون جستجوی وب؛ فقط سنتز ۸ نوت `_doctor-research`). هر یافته به یک تصمیم باز §۹ فایل [[Prompt - دکتر مغز تکاملی (Evolutionary Doctor) 2026-07-05]] نگاشت شده. منابع = همان نوت‌ها؛ اینجا citation تکرار نمی‌شود.

منابع پایه (۸ نوت، ~۹۰ منبع پس از merge):
[[fitness-function-design]] · [[canary-adversarial-evaluator]] · [[invariant-mutable-boundary]] · [[active-mutation-ledger]] · [[loop-rhythm-convergence]] · [[tiered-memory-consolidation]] · [[injection-defense-loop]] · [[industry-benchmark-selfimprove]]

---

## §۹.۱ — مرزِ invariant ↔ mutable

**شاهد:** حتی رادیکال‌ترین سیستم‌های خودارجاع (HyperAgents، Gödel Agent، DGM) هستهٔ انتخاب/ارزیابی را **تغییرناپذیر** نگه می‌دارند؛ فقط لایهٔ رفتار/prompt/ابزار جهش می‌کند. نظرسنجی Misevolution نشان می‌دهد بازکردن این مرز → افت ۷۰٪ رد ایمنی پس از self-training + reward hacking در چهار مسیر (model/memory/tool/workflow).

**پیشنهاد عملی:** مرز سه‌لایه؛ enforcement با allowlist نه اعتماد:
- **هرگز (هستهٔ قفل):** تابع برازندگی، منطق ارزیاب/canary، خودِ `.agentignore`/gitignore secret، قواعد امنیتی §۱۰، دکمهٔ اضطراری. تغییر فقط با verdict آری.
- **میدان خلاقیت (mutable):** promptهای ستون‌ها، آستانه‌ها، ترتیب/انتخاب scoutها، heuristicهای triage.
- **enforcement per-pathway:** هر جهش برچسب مسیر (memory/tool/workflow/prompt) بگیرد و جدا اعتبارسنجی شود؛ نقض مرز = revert خودکار + ثبت در جهش‌نامه.

## §۹.۲ — تابعِ برازندگی

**شاهد:** تک‌متریک = metric-gaming. رویکرد غالب ۲۰۲۶: fitness چندبُعدی + held-out + reference runner مستقل + **evaluator locking** (داور جهشِ خودش نباشد). خطر تازه: ارزیاب هم به هدف حمله تبدیل می‌شود (hacker-fixer / co-evolving evaluator) → قفل‌کردن ارزیاب لازم ولی کافی نیست.

**پیشنهاد عملی (۳ بُعد، وزن‌دار):**
1. **سیگنال عینیِ پروژه** (درآمد lead، خطای کمتر، سرعت) — از لاگ واقعی پروژه‌ها، نه self-report دکتر.
2. **held-out anchor-set** ۵–۷ سناریوی ثابت (پایین) — pass/fail باینری، جدا از دادهٔ جهش.
3. **قضاوت آری** (verdict ستون _INDEX) به‌عنوان وتوی نهایی.
- جهش «خوب» = بهبود بُعد ۱ **بدون** افت بُعد ۲ **و** بدون وتوی منفی. تساوی → quarantine نه promote.

## §۹.۳ — سطحِ استقلالِ حلقه

**شاهد:** همهٔ بازیگران صنعتی (Anthropic Outcomes blind-grader، Plan-Execute-Verify، human-in-the-loop gate) عمداً promote نهایی را خودکار **نکرده‌اند**. الگوی امن: تولید خودکار، ارزیابی مستقل خودکار، **اما گیت انسانی برای inheritance**.

**پیشنهاد عملی:** شروع **L1 propose-only** با یک استثنا: جهش‌های داخل allowlist باریک (مثلاً بازچینش scoutها) می‌توانند L2 bounded-auto شوند وقتی ۲ دور anchor-set را پاس کردند. ارتقا به L2 عمومی فقط پس از ~۲ هفته اعتماد + صفر نقض مرز.

## §۹.۴ — بودجهٔ Fugu

**شاهد:** حلقهٔ خودمختار توکن می‌سوزاند؛ الگوی budget-per-cycle + act-or-defer با کران قابلیت‌اطمینان بهترین مهار است. صنعت: سقف سخت + observability هزینه پیش‌شرط روشن‌شدن.

**پیشنهاد عملی:** pay-as-you-go تا بسته‌شدن rotation (نه اشتراک Max زودهنگام). **سقف سخت روزانه** (پیشنهاد شروع محافظه‌کار — عدد را آری قفل کند) + توقف خودکار در سقف + خط هزینه در HEARTBEAT هر چرخه. تخمین: burst کران‌دار «فقط وقت اپ باز» ارزان‌تر از daemon.

## §۹.۵ — ریتمِ حلقه

**شاهد:** daemon پیوسته → context-rot + runaway. الگوی همگرایی: MAX_ROUNDS، توقف پس از ۲ دورِ بهبودِ زیر آستانه، kill-switch per-round. مناسبِ «فقط وقتی اپ باز است».

**پیشنهاد عملی:** **burst زمان‌بندی‌شدهٔ کران‌دار** نه daemon. هر burst: `MAX_ROUNDS=3`، توقف زودهنگام اگر Δبرازندگی < آستانه دو دور پیاپی، هر round یک kill-switch. context تازه per-review (نه انباشت حلقهٔ بلند).

## §۹.۶ — دامنهٔ دکمهٔ اضطراری

**شاهد:** الگوی rollback چهارراهه (accept/revise/escalate/rollback) + سطوح مهار. صنعت هر سه سطح را جدا نگه می‌دارد.

**پیشنهاد عملی:** **هر سه سطح**، مجزا: (۱) pause چرخهٔ جاری، (۲) revert آخرین جهش از جهش‌نامه (`status → reverted`)، (۳) kill کل ناوگان. سطح ۲ باید بی‌خطر و یک‌فرمانه باشد چون پرکاربردترین است.

## §۹.۷ — تأییدِ گیت

**شاهد:** governance صنعتی = گیت انسانی صریح قبل از فعال‌شدنِ لایهٔ عمل؛ تاریک‌ماندن تا بسته‌شدن rotation ریسک را حذف می‌کند نه فقط کم.

**پیشنهاد عملی:** بله — ستون ۳ (لایهٔ عمل) تا بسته‌شدن rotation تاریک بماند. تا آن‌موقع فقط propose + ثبت در جهش‌نامه؛ هیچ inheritance خودکار.

---

## زیرساخت پشتیبان (فرا-تصمیمی)

- **جهش‌نامهٔ فعال ([[active-mutation-ledger]]):** append-only تنها کافی نیست؛ الگوی FAILURE→REPAIR (counterfactual + lifecycle سبک Mem0) هر شکست را به یک اصلاح مینیمال تبدیل می‌کند. رشد بی‌مرز با decayِ امتیاز (نه حذف داده) مهار شود.
- **حافظهٔ دوفازی ([[tiered-memory-consolidation]]):** ارتقای EXPERIENCE-LEDGER به working/long-term/core + consolidation شبانه + retrieval هیبرید (BM25+vector+RRF). شاهد: بدون tiering ~۱۴pp افت موفقیت ابزار.
- **دفاع تزریق ([[injection-defense-loop]]):** برای هر call با `web_search`: external=data (برچسب `<external_data>`)، provenance، بلوک نامتراکم‌پذیر برای قواعد حساس، sanitize. این هستهٔ قفل §۹.۱ است، نه mutable.

---

## verdictهای لازم از آری (قفل قبل از بلوپرینت)

- [ ] **§۹.۲ وزن سه بُعد** برازندگی (عینی/anchor/قضاوت) — نسبت پیشنهادی؟
- [ ] **§۹.۳** تأیید L1 propose-only با استثنای allowlist باریک برای L2؟
- [ ] **§۹.۴ عدد سقف سخت روزانهٔ** توکن/دلار؟
- [ ] **§۹.۶** تأیید هر سه سطح دکمهٔ اضطراری؟
- [ ] verdict «مفید/نه» روی ۸ نوت `_doctor-research` (ستون _INDEX) → خوراک بُعد ۳ برازندگی.
