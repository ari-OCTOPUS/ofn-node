---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: ready
tags: [creator-business, marketing]
created: 2026-08-03
updated: 2026-08-03
---

# DEEP-SCAN کامل Project-F — 2026-08-03 + مقایسه با دیجیتال‌مارکتر OnlyFans ۲۰۲۶

> اسکن ۱۴-ایجنته (۱۱ خوانندهٔ read-only روی ~۲۳۰ فایل پروژه + ۱ سیم‌کشی اکوسیستم + ۲ تحقیق وب) + سنتز. هدف دوم: پایهٔ تصمیم برای «مینی‌اپ تلگرامی کنترل شبکه‌های اجتماعی» → [[03 - Projects/اونلی فنز/06 - Ops & Runtime/PROP-D5-MINIAPP-SOCIAL-COCKPIT|PROP-D5]].
> قاعدهٔ هویت رعایت شده: پارتنر = «C»؛ پوشهٔ `08 - Partner (PII)` طبق `.agentignore` باز نشد.

## ۰. حکم یک‌نگاهی

- **مغز و ترمز: جلوتر از میانگین بازار ۲۰۲۶.** صف HITL ساختاری (هیچ متد send در کد)، گاردهای fail-closed همه‌جا، KPI با آستانهٔ hard-coded، بندیت approval-gated — چیزهایی که اکثر اپراتورهای بازار ندارند.
- **دست و پا: صفر مطلق.** هیچ اکانت، هیچ پست، هیچ DM، هیچ دادهٔ زنده. ۱۴ روز است (از Forced Completion Sprint ِ ۰۷-۲۰) گلوگاه فقط و فقط **امضای انسانی** است، نه کد.
- **سه شکاف واقعی:** (۱) انسانی — GATE 0 + سه امضا + verdictهای قیمت/برند؛ (۲) طراحی — retention/CRM عملیاتی که هم اسناد خودمان و هم بازار ۲۰۲۶ بزرگ‌ترین اهرم LTV می‌دانند و **تنها بُعدی است که طراحی‌اش هم ناقص است**؛ (۳) چسب — همهٔ قطعات مینی‌اپ (gateway با HMAC، tunnel، صف‌ها، KPI store، فرمان‌های `/pf_*`) ساخته شده و فقط سیم‌کشی مانده.

## ۱. شناسنامه

| | |
|---|---|
| مدل | برند faceless «فقط پا»، غیر explicit؛ تیم دونفرهٔ ۵۰/۵۰ (A = ops/tech/marketing/finance؛ C = تولید محتوا) |
| فاز | validation؛ **صفر اجرای بیرونی**؛ `outward_actions_allowed=false` |
| پلتفرم هدف | OF free-page + Fansly mirror (discovery-first) + بعداً clip stores (ManyVids اولویت ۱) |
| کد cross-domain | فقط «Project-F» بیرون از پوشه؛ صفر echo هویت |
| حجم پروژه | ~۲۳۰ فایل: ~۱۶۰ سند + ~۷۰ فایل کد/تست پایتون (brain/langar/studio/pf_os/tests) |
| تست | ۲۰۹/۲۰۹ سبز (stamp ِ ۰۷-۲۰)؛ بازآرایی ۰۷-۲۴ عدد را ۳۶۶/۳۶۶ کرد (stamp عمداً دست‌نخورده — gate-abstention) |

## ۲. حاکمیت — دقیقاً کجا قفل است

- **GATE 0 = OPEN.** سه مسدودکننده، هر سه انسانی: (۱) نوع منبع اقامت C ثبت نشده (Branch A فقط «اظهار A»)، (۲) تأیید مکتوب C روی توافق ۱۲بندی (A امضا کرده)، (۳) سؤال آخر پرسشنامهٔ C.
- **PAGE_SETUP = NO-GO** ([[03 - Projects/اونلی فنز/00 - Control/GATE-STAMP-2026-07-20|GATE-STAMP]]). شرط GO: بستن ۱۲ P0 (۹ بسته، ۳ بازماندهٔ انسانی) + سه امضای DL + برداشتن STOP + بازنویسی stamp **فقط توسط مالک**.
- **PF-V5 «Full Aggressive» = REVOKED** (رأی صریح ۰۷-۲۰)؛ مسیر لانچ SYNTH-05 هم SUPERSEDED.
- **RISK-LADDER:** RED (اکانت/پست/DM/پرداخت/login/echo هویت/BotFather/اجرای کد) = فقط انسان و تا GATE 0 + Security Gate قفل. Security Gate بسته تا تیک چک‌لیست ۲۴بندی OpSec (R11).
- **DecisionLog = تنها SoT تصمیم**؛ VERDICT_QUEUE فقط سینی رأی (DL-2026-07-20-DECISION-SOT)؛ در تعارض، OPEN برنده.
- گیت‌های عددی: G1 (هفتهٔ ۶) ≥۲۰۰ کلیک + ≥۱۰٪ click→follow + delivery ِ C ≥۸۰٪ · G2 (هفتهٔ ۱۲) ≥۳۰ free-sub + ≥۵٪ free→paid + اولین AUD 100 · G3 = AUD 2k/ماه ×۳ + churn<30٪ · G4 = ۱۲ ماه سودده.
- Body-expansion = FROZEN (رد صریح C؛ DL-BODY-FREEZE)؛ بازگشایی فقط با رضایت مکتوب دوطرفه.

## ۳. استراتژی و برند

- **دو سند master ِ متعارض:** MASTER-BUILD (واقع‌بین، spine ِ پیشنهادی) ↔ Playbook (تاکتیک‌محور، در ~۶ نقطه «Sydney» متنی دارد = نقض قاعدهٔ #۶). Reconcile ‏(R0) هنوز رأی ندارد.
- **سه نردبان قیمت زنده** (CONFLICT ِ باز #۱۰): MASTER-BUILD ‏($6–8/$10–15/$12–18، VIP $35) · Playbook ‏($6/$12/$30، VIP $20) · EXT-04 ‏(ورودی $3–5 / استاندارد $8–15 / پرمیوم $15–30 / کاستوم $25+، بدون VIP تا روز ۹۰ — متمایل ِ verdict-queue). نسخهٔ آشتی‌شده در `drafts-awaiting-gate/ppv-ladder.md` آماده است.
- **برند:** پیشنهاد #۱ = Anar Soles (صفر collision)، رزرو Yalda Arch؛ default رسمی = defer-until-#9. نام‌های شهری حذف شدند. صدای برند: warm/unhurried/wry؛ سه کلمهٔ ممنوع sexy/hot/babe؛ USP: بی‌چهرگی خودِ محصول.
- **فانل:** Reddit (~۶۰٪ تلاش، موتور #۱) → X (~۳۰٪، reply-game دستی، تنها پلتفرم با لینک مستقیم مجاز) → GAML link-hub (age-gate + geo-block ایران) → OF Free ۹۰ روز → First PPV → Repeat/Custom؛ SFW short-video از ماه ۳ (سند ترند ۲۰۲۷ می‌گوید زودتر — تعارض ثبت‌شده).
- **اقتصاد صادقانه:** میانهٔ OF ‏≈$180/ماه، مُد = صفر، Gini ≈0.83؛ سناریوی ماه ۳: Floor ‏$0–80 (۴۰–۵۰٪) / Base ‏$150–500 / Upside ‏$500–1500؛ LTV هر خریدار $15–45 خالص؛ CAC پولی اجباراً ~صفر (تبلیغ adult ممنوع) یعنی CAC واقعی = زمان.
- Monetization-Expansion: اصل Atomization (هر شوت ≥۸ خروجی، هر asset ≥۳ مسیر درآمد)؛ mix هدف ماه ۳+: Sub+PPV ~۴۵٪ / Custom ~۲۵٪ / Clip stores ~۱۵٪ / Tips ~۱۰٪ / Passive ~۵٪.

## ۴. تحقیق داخلی (corpus)

- سه راند integration همگرا: dual-platform، Reddit موتور #۱ (قانون ۳:۱ و ۹۰/۱۰)، پول واقعی در PPV+custom نه اشتراک، مارکت‌پلیس‌ها (FeetFinder) موتور رشد نیستند (سه شاهد مستقل صفر-درآمد؛ تعارض با سند ۰۷-۱۲ که هنوز توصیه‌اش می‌کند — reconcile نشده).
- **Retention = بزرگ‌ترین گاف اعلام‌شدهٔ خود پروژه:** پنجرهٔ ۷۲ ساعت، auto-renew پایه ۲۰–۳۰٪ در برابر برترها ۴۰–۵۰٪، DM پیش-از-تمدید ۳۵–۶۰٪ نگه می‌دارد — «طراحی صریح ندارد».
- AI-chat ِ full-auto در DM ممنوع ToS ‏[FACT—Reuters]؛ الگوی قفل‌شده: «AI درفت می‌زند، انسان می‌فرستد» + افشای ملایم دستیار (EU AI Act ماده ۵۰ از 2026-08-02 + ACL استرالیا عملاً اجباری‌اش کرده‌اند).
- ریسک پلتفرم بالا رفته: فوت Radvinsky + فروش ~۱۶٪ OF ‏@$3.15B؛ قاعدهٔ پیشنهادی «هیچ بالانس >$100 نماند» (proposal، رأی ندارد). بند مصادرهٔ ۱۲ماههٔ Fanvue ‏[FACT].
- research-results ‏P1–P10: geo-block ایران ۵لایه؛ ESPهای مین‌استریم همه adult-ban → SendX ‏$9.99؛ Zapier ممنوع → n8n self-hosted؛ لیست سیاه/سبز ابزار کامل؛ انضباط آماری small-sample (قاعدهٔ 3/n، قضاوت قبل از ~۵۰ کلیک ممنوع)؛ kill-criteria عددی per-کانال.
- `marketing-automation-100-topics-2026.md` = نزدیک‌ترین سند داخلی به «دیجیتال مارکتر ۲۰۲۶»: اولویت GEO → Agentic Commerce → پیام‌رسان → سیستم‌های خودبهینه‌شونده؛ برای Project-F فقط C5/D1/E10/G9/I1/I7/J10 ‏relevant اعلام شده.

## ۵. محتوا و جذب — موجودی آماده

- **۳۰ کارت کلیپ faceless آمادهٔ فیلم‌برداری** (۷ دستهٔ A–G، هر کارت Hook/Shot/Overlay/Sound/طول؛ ۲ جلسهٔ ضبط ۹۰+۶۰ دقیقه = ~۳ هفته مهمات).
- **VaultBank با ۲۲ asset ِ seed** (۱۲ reddit-SFW + ۷ x + ۳ of-softcta) با fair-rotation — ⚠️ همه cert ِ خالی دارند (از مسیر رسمی handoff نگذشته‌اند).
- ۶ درفت منتظر گیت: kpi-dashboard-spec (آستانه‌های hard-coded سبز/زرد/قرمز) · tracking-link-design (۸ کد بدون PII) · ppv-ladder · link-hub-copy · x-profile · msg-to-C-question8. دو تای اول مستقیم‌ترین خوراک مینی‌اپ‌اند.
- بلوپرینت جذب خودکار: state machine ِ draft→schedule→queue→ONE-TAP approve→publish(گیت‌دار خاموش)→KPI→feedback؛ فلگ‌های `PF_LIVE_PUBLISH`/`PF_LIVE_DM` پیش‌فرض ۰.

## ۶. عملیات و Runtime

- KPI-DASHBOARD: جدول هفتگی ۱۸ستونه + آستانه‌های hard-coded («تصمیم احساسی ممنوع») — فقط ردیف هفتهٔ صفر؛ SOP جمعهٔ ≤۳۰ دقیقه دستی.
- VERDICT_QUEUE: **۱۱ verdict معلق** + AGENT-CONTROL-INTERFACE: ایجنت مادر فقط Observe/Task(propose-only)/Kill.
- روتین‌ها seed شده: بریف دوشنبه، chores چهارشنبه، KPI جمعه، درفت یکشنبه برای C.
- **گاف‌های OpSec ِ High:** (۱) نام C در شناسه‌های سورس (refactor ِ C1 روی برنچ پیاده، ratify = ballot Q11)؛ (۲) blocklist ِ `langar_config.json` خالی = عملاً fail-open در creator_brain (لنگر خودش deny-by-default است). PII هنوز git-tracked: ۲ سند + ۸ عکس `test/` (R10) + تاریخچهٔ git.
- لاگ تلگرام پروژه (`06 - Ops & Runtime/اونلی فنز.md`) عملاً مرده است (۳ پیام مالی از 2024).

## ۷. کد — لایه‌به‌لایه

### brain/ + orchestrator (مغز advisory-only، stdlib، $0)
- `orchestrator.py`: حلقهٔ tick با گیت compliance ِ fail-closed از MANIFEST (فیکس بای‌پس ۰۷-۲۰)؛ بدون `_ops/neural` با stub بالا می‌آید.
- `dual_brain_v3.py` مغز فعال (۱۰ ساب‌عامل + Pricer یادگیر + Ethics-Guard)؛ `project_f_brain.py` = legacy ِ **يتیم** (PROP-D1 منتظر رأی).
- دو صف HITL: `acquisition_pipeline` ‏(drafted→approved→ready، dedup md5، دو گارد روی finalize) و `dm_pipeline` ‏(pending_review→ready_for_manual_send؛ **ساختاراً هیچ متد send**).
- `guards.py`: WarmupGuard (کارما<۲۰=deny) + ChannelLocks (۱ warning=قفل کانال، ≥۲=full_stop؛ فایل خراب=fail-closed).
- `store.py` ‏DataSpine: پنج store ِ صفر-PII در `langar/` (fan_db/vault/kpi/link_state/octopus).
- `learning.py`: ThompsonBandit ‏approval-gated (از greedy ‏۴۹٪ بهتر) — **به مسیر production سیم نیست** (PROP-D2؛ فلگ `PF_LEARNING_WIRED` خاموش)؛ `ab_tracker.py` و `lifecycle.py` هم يتیم‌اند.
- `audit.py`: ‏approvals.jsonl ِ append-only ‏content-free با مهر origin=live|test.

### langar/ (کاکپیت تلگرامی A) + studio/ (استودیوی C)
- لنگر ~۳۵+ فرمان: `/pf_*` ‏(plan/queue/ok/no/ready/dryrun) · `/dm_*` · `/fan_*` · `/vault_*` · `/kpi*` · `/guards` · `/kill|/revive` · `/agreement*`؛ OpsecGuard ِ deny-by-default؛ CostMeter ِ fail-closed ‏(AUD 15/ماه).
- 🔴 **باگ قطعی:** `/dm_inbox` کرش می‌کند — `def _dm_inbox` وجود ندارد (بدنه‌اش کد مردهٔ داخل `_code_card` است، `langar_bot.py` ~سطر ۹۴۵).
- استودیوی C: منوی سه‌سطحی + self-cert چهارگانهٔ اجباری + `/halt` مقدم مطلق؛ creator_brain با Ollama محلی + fallback ِ Fugu؛ ⚠️ runbook ِ استودیو stale (به نام‌های pre-rename ارجاع می‌دهد).
- ⚠️ هر دو `.bat` به درخت زندهٔ `F:\backup` اشاره می‌کنند نه worktree.

### pf_os/ (OS ماژولار — incubating طبق ADR)
- ۵ فلگ default-OFF ‏(`OCTOPUS_WIRE_PROJECTF_{CORTEX,LOOP,API,EVAL}` + `OCTOPUS_WIRE_SABA_BRIDGE`)؛ flag-off = بایت‌به‌بایت no-op.
- `actuator.py` سه‌حالته shadow/dry-run/live — مسیر live چهار دیوار + در انتها عمداً `NotImplementedError` (adapter زنده اصلاً در build نیست).
- `capabilities.py`: registry ِ green/amber/red با `{name, level, executable, reason}` — پنج قابلیت red بدون هیچ env-bypass.
- `bridge.py`/`bridge_beat.py`: file-pubsub به `_ops/state/saba-bridge.jsonl` با whitelist ِ ۸ kind + scrub ِ سه‌لایه؛ consumer آماده ولی **صفر صداکننده در `_ops`** («یک خط وصل» در wiring مانده — G-007 ِ verified).
- REST ‏`api.py` روی 127.0.0.1:8780 ‏(~۱۲ endpoint ِ content-free).
- 🔴 **آرتیفکت باگ مسیر:** پوشهٔ «F꞉backup» (کاراکترهای PUA به‌جای `:`/`\`) داخل پروژه — یک runtime ِ POSIX-نما رشتهٔ `F:\backup` را پوشهٔ نسبی کرده؛ ۲۲۸ رویداد pf_os ِ 2026-07-19 به مقصد مرکزی نرسیده. منشأ: `pf_os/config.py` ‏(VAULT-resolution). فیکس نشده.
- ⚠️ `api.py::/api/draft/submit` درفت واقعی نمی‌سازد (فقط event می‌فرستد و «queued» می‌گوید) — کاندید سبز دروغین.

### وضعیت در ارگانیسم
- `studio_pf` در `ORGANISM-STATE.business_legs` **غایب** است (نه زنده گزارش می‌شود نه مرده)؛ فایل leg ِ استاندارد ندارد؛ تنها اثرش نگاشت pause در `wiring.py::leg_paused`. کنترل زندهٔ فعلی فقط از مسیر `_ops/legs/langar_bridge.py` (پل لا‌مزاحم به `LangarBot.handle()`).

## ۸. زیرساخت مینی‌اپ که همین الان موجود است (نساز، سوار شو)

- `_ops/telegram_center/miniapp_gateway.py`: bind ‏127.0.0.1:8774، احراز HMAC ِ initData ‏(auth_date ≤ ۳۰۰s، compare_digest، allowlist تک‌مالکه)، شل استاتیک ۳فایله + تزریق خودکار `X-Tg-Init-Data`، ۸ endpoint ِ read-only → `miniapp_state.dispatch_api()`، **`POST /api/actions`** ِ owner-gated → `OpsActionEngine` ‏(idempotent با action_id)، redaction دولایه، `STOP-MINIAPP` ‏fail-closed، فلگ `OCTOPUS_TG_MINIAPP`.
- tunnel: ‏`run-miniapp-tunnel.ps1` ‏(cloudflared quick-tunnel، $0) → `_ops/state/telegram/miniapp-url.json`؛ مرکز دکمهٔ web_app را از همین فایل می‌سازد (تازگی ۲۴h). رسید هر تپ در `miniapp-hits.jsonl`.
- قرارداد مرزی SHADOW_ONLY ‏(سند 05): schema ِ دقیق `GET /pf/status` = فقط `{beat, mode, drafts_count, dm_pending, acq_ready, full_stop, karma_met}` — نه یک فیلد بیشتر.
- ⚠️ دو ناسازگاری سند/کد برای رأی: PLAN-T4 می‌گفت «هیچ POST» ولی کد `POST /api/actions` دارد؛ و tunnel-on-demand ‏(TTL ۳۰د) در طرح در برابر تونل بلندعمر ِ پیاده‌شده.

## ۹. مقایسه با دیجیتال‌مارکتر حرفه‌ای OnlyFans ۲۰۲۶ (تحقیق وب — تقریباً همهٔ اعداد vendor-سوگیر، [EST])

ستون‌های کاری اپراتور حرفه‌ای ۲۰۲۶: کشف با short-video ِ SFW ‏(۲–۴ کلیپ/روز) · X ‏۳–۵ پست/روز (پیک 19–23 EST = ‏۹–۱۲ صبح سیدنی) · Reddit ‏۳–۸ پست/روز در ۱۵–۳۰ ساب با دیتابیس قوانین هر ساب · لندینگ/link-hub با UTM کامل · **چت = موتور ~۵۹٪ درآمد** (AI-assist با افشا مجاز، full-auto = بن) · retention ماه اول = بزرگ‌ترین اهرم LTV ‏(rebill سالم ۵۰–۷۰٪، churn تاپ‌تیر ۱۵–۲۵٪) · analytics از CSV رسمی OF ‏(ابزارهای session-based = خاکستری ToS) · لیبل sensitive-media ‏X + پایش لیک/DMCA.

| بُعد | وضع vault | بازار ۲۰۲۶ | شکاف | اولویت |
|---|---|---|---|---|
| جذب per-channel | طراحی کامل، صفر اجرا | دیتابیس قوانین per-sub + چک shadowban هفتگی | دیتابیس ساب‌ها و مانیتور shadowban ساخته نشده؛ اجرا پشت GATE 0 | **P0** |
| DM/چت | drafter ِ HITL بدون send | welcome ‏۲۴h، follow-up، upsell ساخت‌یافته | playbook ِ عملیاتی چت با تایمر/یادآور وجود ندارد | **P0** |
| قیمت/PPV | ۳ نردبان متعارض + Pricer ِ يتیم | ورودی $12–25 یا free+PPV؛ unlock هدف ۱۵–۲۵٪؛ A/B مستمر | verdict #۱۰ باز؛ ab_tracker به هیچ‌جا سیم نیست | **P0** |
| Retention | فقط FanDB + lifecycle ِ يتیم | پنجرهٔ ۷۲h، ردیاب rebill، صف winback، سیگنال at-risk | **تنها بُعد با طراحی ناقص** — ساختنش امروز مجاز است (propose-only) | **P0** |
| محتوا | ۳۰ کارت + VaultBank ۲۲ | ۲–۴ کلیپ/روز، block-shooting، دو خط SFW/NSFW | صفر شوت واقعی (C + GATE 0)؛ ردیاب asset→پلتفرم روی کاغذ | P1 |
| فانل/لینک | کپی hub + ۸ کد tracking درفت | لندینگ self-hosted با مالکیت داده | hub نساخته؛ attribution دستی CSV؛ گزینهٔ self-hosted بررسی نشده | P1 |
| اتوماسیون | همه propose-only، فلگ خاموش | X تنها کانال auto-post ِ رسمی NSFW ‏($0.015/پست)؛ Reddit نیمه‌دستی | زمان‌بند shadow (صف زمان‌دار + یادآور) هم ساخته نشده | P1 |
| Compliance | قوی‌تر از بازار (fail-closed چندلایه) | اسکنر لیک/DMCA + سلامت اکانت | R9/R10 رأی مالک؛ اسکنر لیک در backlog | P1 |
| Analytics/KPI | زیرساخت تقریباً کامل، ورود دستی | LTV/churn/درآمد per-source از CSV رسمی | فرم ورود سریع + per-source/LTV در schema نیست | P2 |
| استک ابزار | $0 خودساخته (تصمیم درست: ابزار session-based نخریدن) | Infloww/Supercreator (خاکستری ToS)، Postiz self-hosted | فقط دادهٔ زنده کم است؛ خرید بعد از GATE 0 | P2 |

## ۱۰. تصمیم‌های باز مالک (گلوگاه واقعی — فهرست کامل)

1. **GATE 0**: نوع منبع اقامت C + تاریخ (DL-G0) — بزرگ‌ترین تصمیم کل معماری (Branch B = توقف Track A).
2. تأیید مکتوب C روی توافق ۱۲بندی (مسیر `/agreement_signed` آماده).
3. سؤال آخر پرسشنامهٔ C (پیام بازپرسی درفت شده: `drafts-awaiting-gate/msg-to-saba-question8.md`).
4. نردبان قیمت #۱۰ (پیشنهاد: EXT-04 + ‏VIP منجمد تا G2) — CONFLICT.
5. برند #۶ (پیشنهاد: Anar Soles + رزرو Yalda Arch) — تصمیم دونفره.
6. ‏«Persian/Sydney» در کپی #۹ ‏[P0-opsec] + scrub ‏R9.
7. R10: انتقال PII ِ tracked ‏(۲ سند + ۸ عکس `test/`) — الزامی قبل از هر remote.
8. R11: چک‌لیست OpSec ‏۲۴بندی → بازشدن Security Gate.
9. حالت labeling ِ X ‏(T6) · بلاک AU ‏(#۱۹) · نقش Fansly (پیشنهاد قفل‌شده: mirror+discovery-first) · Day-Zero (تعیین نشده = NO-GO).
10. PROP-D1 (سرنوشت project_f_brain) · PROP-D2 ‏(فلگ PF_LEARNING_WIRED) · PROP-D4 ‏(ratify ِ rename، ballot Q11).
11. reconcile ِ R0 (کدام master ‏spine است) + تنش FeetFinder + سقف مغز AUD 15 ‏(#۲۰) + قاعدهٔ بالانس >$100.
12. index.lock ِ کهنهٔ `.git` درخت زنده (مانع commit/merge) — فقط دست مالک.
13. برای مینی‌اپ: رأی‌های §۸ ِ [[03 - Projects/اونلی فنز/06 - Ops & Runtime/PROP-D5-MINIAPP-SOCIAL-COCKPIT|PROP-D5]].

## ۱۱. باگ‌ها و بدهی‌های فنی پیداشده در این اسکن

| # | مورد | شدت |
|---|---|---|
| 1 | `/dm_inbox` ‏AttributeError ‏(متد `_dm_inbox` تعریف ندارد؛ کد مرده داخل `_code_card`) | 🔴 قطعی |
| 2 | پوشهٔ آرتیفکت «F꞉backup» + ۲۲۸ event ِ گم‌شده؛ ریشه در `pf_os/config.py` | 🔴 |
| 3 | `OCTOPUS_WIRE_SABA_BRIDGE` صفر صداکننده در `_ops` (consumer هست، وصل نیست — G-007) | 🔴 |
| 4 | ۲۲ asset ِ vault با cert ِ خالی (کنارگذر مسیر رسمی) | 🟡 |
| 5 | `api.py::/api/draft/submit` فقط event می‌فرستد ولی «queued» ادعا می‌کند | 🟡 |
| 6 | dm_pipeline ‏approve/reject/mark_sent بدون `self._lock` (ریسک race ِ تئوریک) | 🟡 |
| 7 | runbook ِ استودیو stale ‏(نام‌های pre-rename)؛ `_INDEX` ِ آرشیو خالی؛ MANIFEST از ۰۷-۲۰ sync نشده؛ PLAN ‏۰۸-۰۱ به ARMING-ORDER ِ منسوخ ارجاع می‌دهد | 🟡 |
| 8 | `LearningBridge` مسیر `/dev/null` ‏POSIX (بی‌اثر ولی شکننده)؛ KPIRollup هفتهٔ epoch-محور ≠ جمعهٔ اپراتور؛ storeها fail-soft ِ بی‌صدا | 🟢 |
| 9 | GATE-STAMP عدد تست کهنه (209 در برابر واقعیت 366) — فقط مالک بازنویسی کند | 🟢 |

## ۱۲. منابع

- اسکن: ۱۱ خوانندهٔ read-only روی پوشه‌های 00–09 + ریشه + brain/langar/studio/pf_os/tests + `_ops` ‏(miniapp/wiring) — journal ِ workflow ‏`wf_35d84a2c`.
- وب (نمونه): Aruna Talent ‏(playbook/traffic ‏2026) · Inro ‏(funnels/IG-DM) · Sozee ‏(retention) · SirenCY ‏(pricing) · Postiz ‏(Reddit API) · Postproxy ‏(X API pricing) · X Help ‏(automation rules) · core.telegram.org ‏(Mini Apps/initData) · docs.telegram-mini-apps.com — فهرست کامل در گزارش دسکتاپ.
