---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [debate, deepseek, ledger, stage-report]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 1930 PROMPT-PACK — سه پرامپت مرحله‌ای (متابولیسم-مناظره-تکثیر)]]"
  - "[[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه]]"
---

# STAGE2-REPORT — مناظره (لوپ دو ایجنت جعبه‌سیاه + ثبت تجربه)

## schema نهایی رویدادها (همه NOTE + payload.subtype در ledger زنجیرهٔ‌هش ژنوم)

- **هر دور مناظره** → ‏`NOTE` / ‏`subtype: EXPERIENCE`:
  `{loop: "debate", topic_id, topic_hash(sha256:16), round, verdict(pass|kill|needs-fix), cost_usd, stub}`
- **بازماندهٔ صف انسان** → رویداد واقعی `PROPOSAL` (نه NOTE — قرارداد هفت‌فیلدی humility تا دکتر ژنوم داوری کند):
  `{idea, why_it_might_be_genius, why_it_might_be_insane, confidence: 0.5, kill_criteria, smallest_test, reversible, origin:{loop:"debate", topic_id}}` با `actor="debate", to="doctor"`.
- **صف انسان‌خوان:** ‏`_ops/debate/SURVIVORS-QUEUE.md` (append-only) — ‏«بازمانده» فقط یعنی وارد صف شد؛ تأیید = verdict آری.
- قرارداد JSON دو نقش: ‏MUSE = ‏`{idea, why_genius, why_insane, est_tokens, quality_bar, epistemic_tag}` · ‏ARCHITECT = ‏`{verdict, kill_condition, cheapest_test, epistemic_tag}`؛ نقض قرارداد = ‏ValueError (نه ادامهٔ کور).

## آمار تست

- سوئیت ایزوله `_ops/tests/` (vault موقت در TEMP): **۶ فایل، ۳۲ چک، همه سبز، آفلاین $0** — شامل `test_debate.py` (چرخهٔ کامل stub، گیت deny → fail-closed بدون mock، تزریق) و `test_client.py` (گارد نشت host، قیمت قفل‌نشده=PriceNotLocked، usage غایب=TelemetryError، est بدترین‌حالت).
- پروتکل: ‏≤۳ دور (دور ۴ وجود ندارد — بی‌نتیجه = ‏undecided-after-3-rounds در صف انسان)؛ ‏needs-fix → دور بعد با قید معمار.

## تله‌های خورده

| تله | دفاع در کد |
|---|---|
| کلید DeepSeek در متغیر `ANTHROPIC_API_KEY` (قرارداد control-brain) | ‏client.py فقط `DEEPSEEK_API_KEY` می‌خواند؛ fallback ممنوع؛ assert ‏host = ‏api.deepseek.com |
| نشت آینه‌ای در genome-system (llm.py به api.anthropic.com هاردکد) | **این جلسه فیکس شد (v0.4.1):** ‏`ANTHROPIC_BASE_URL` + گارد `sk-ant-` پیش از I/O + ‏`tests/leak_guard_test.py` (۳ چک سبز) |
| تزریق از topic | فقط whitelist (seed + plan.yaml + ارگان‌های budgets)؛ truncate ۲۰۰۰؛ پوشش ‹‹‹ ››› + GUARD_SENTENCE در system prompt هر دو نقش؛ stub قطعی مستقل از محتوای topic = خودش تست تزریق |
| deny گیت وسط مناظره | ‏reserve→call→settle/release؛ استثنای call = ‏release؛ deny = توقف امن، هرگز mock |
| «تأیید» خیالی | ‏survive فقط بلیت صف؛ پذیرش = فقط APPROVAL فرایند صف (ضد reward-hacking — قرارداد fitness) |

## نرخ survive آفلاین

- ‏stub قطعی: معمار همیشه `pass` → ‏survive نرخ ۱۰۰٪ در تست (طراحی‌شده برای پوشش مسیر صف/PROPOSAL). نرخ واقعی فقط بعد از فعال‌سازی زنده معنا دارد؛ قرارداد نقش معمار: ‏survive پایدار بالای ~۳۰٪ = معمارِ زیادی نرم.

## پیشنهاد topicهای پرثمر (برای run زندهٔ اول، بعد از ۰۷/۲۱ + پرچم مالک)

1. ‏milestoneهای باز `plan.yaml` ژنوم (whitelist موجود) — مستقیم به کار فنی جاری وصل است.
2. ‏verdictهای باز §۸ HYBRID-SPEC — هر مناظره یک تصمیم معلق را برای مالک شفاف‌تر می‌کند.
3. ‏per-organ: از `topics/kpis` ژنوم هر بیزنس (ziman/painting/accounting) — خوراک fitness مرحلهٔ ۳.
4. موضوع‌های واگرایی تلمتری (وقتی `suspect_zero` بالا رفت) — مناظره دربارهٔ ریشهٔ متر صفر.

## آیتم‌های باز

- فعال‌سازی زنده: ‏۷ روز اجرای دستی نظارت‌شده؛ هر cron/تسک = verdict جدا (ناوگان الان ۰ تسک فعال).
- ‏quarantine ایده‌های وحشی (`MUSE-QUARANTINE-LEDGER.md`) در نسخهٔ فعلی minimal است — بازمانده‌ها همه به SURVIVORS-QUEUE می‌روند؛ تفکیک وحشی/عادی با دادهٔ زنده.
