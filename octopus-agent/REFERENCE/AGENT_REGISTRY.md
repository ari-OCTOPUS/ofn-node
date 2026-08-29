---
type: reference
status: active
tags: [agents, registry, governance]
created: 2026-07-03
updated: 2026-07-20
---

# AGENT_REGISTRY — رجیستری ایجنت‌های برنامه‌ریزی‌شده

> **هر ردیف وارث §Security Gate است:** تا CRITICALهای [[ROTATION_CHECKLIST]] باز است، autonomy مؤثر همه = read-only — فارغ از ستون autonomy. تعریف سطح‌ها و ماتریس تشدید: [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]. هیچ‌کدام هنوز deploy نشده‌اند (فاز ۴).

| ایجنت | دامنه | هدف | autonomy هدف | می‌خواند | می‌نویسد | ممنوع |
|---|---|---|---|---|---|---|
| architect-researcher | architect | تحقیق و پیشنهاد خودبهبودی | propose-only | کل vault (منهای ignore) | نوت پیشنهاد در 02-Research | اعمال تغییر؛ دستکاری charter |
| architect-orchestrator | architect | جمع وضعیت، رابط تلگرام | propose-only | manifestها، Active Contextها | digest، پیشنهاد با ID در ledger | صدور verdict؛ اکشن خارجی |
| accounting-clerk | Accounting | دسته‌بندی رسید/فاکتور | propose-only | Inbox رسیدها، manifest | draft دسته‌بندی `[Unverified]` | lodge به ATO/ASIC؛ پرداخت |
| lead-pipeline | Lead-نقاشی | pipeline لید + گزارش آزمایش | propose-only | pipeline، لاگ آزمایش | آپدیت pipeline (draft)، گزارش هفتگی | ارسال outreach بدون verdict |
| crypto-watcher | Crypto-etoro | پایش exit_rules + هشدار | execute-with-verdict → bounded-auto (فقط SELL/TRIM ثبت‌شده، بعد از گیت) | Portfolio Registry، دیتا | هشدار، evidence، ورودی ledger | هر BUY؛ SELL خارج قاعده؛ دسترسی کلید (D-11) |
| mining-deathwatch | Mining | ارزیابی death-watch کوین‌ها | propose-only | لاگ آزمایش، دیتای شبکه | گزارش death-watch | SSH مستقیم (D-20)؛ هر اکشن مالی (D-10) |
| ziman-capacity-guard | Ziman | گارد سقف ظرفیت + draft کمپین | propose-only | Capacity & Channels | draft زیر سقف؛ رد بالای سقف | انتشار بدون verdict |
| projectF-reporter | Project-F 🔒 | گزارش چک‌لیست/تسک | propose-only | PROJECT.md حوزه | گزارش با کد Project-F | هر اشاره به هویت/پلتفرم/محتوا؛ دست زدن به media |
| knowledge-indexer | هیپنوتیزم | ایندکس و خلاصه | read-only | نوت‌های حوزه | ایندکس (پیشنهادی) | cite کردن fiction-canon بیرون حوزه؛ خروج داده شخصی از لپ‌تاپ (O-04) |
| vault-cartographer | architect (نقشه‌برداری) — **limb/OLP-1**، parent=Architect/_ops · **boot-coupled 2026-07-12** (PAPER_FULL_FLAGS) · telegram via center key `cartographer` | نقشه/ممیزیِ معماری + گراندینگِ design↔reality از repoِ واقعی | read-only floor / propose-only ceiling | کل vault منهای `.agentignore`/`_Duplicates`/`_Archive`/secrets/هویتِ Project-F | فقط `06 - Architecture Maps/MASTER-*` + پیشنهاد در `00 - Inbox` (propose) | تغییرِ کد/charter/genome؛ verdict؛ اکشنِ خارجی؛ echo از secret یا هویتِ Project-F · شناسنامه: [[05 - Agents/Vault Cartographer]] · لیمب: [[05 - Agents/Vault-Cartographer-LIMB]] |
| wlos-coach | WLOS (شخصی — [[03 - Projects/WLOS - Weight Loss OS/PROJECT\|PROJECT]]) | کوچ کاهش وزن مالک؛ اندام «شناخت مالک» برای مغز اصلی (دستور مالک 2026-07-20) | ایمنی داخلی خودش (outbox-only، سقف ۲۰/روز، quiet hours) + هر self-mod فقط با تأیید مالک | DB محلی خودش (پستگرس، بیرون git) | فقط تلگرام به مالک از مسیر outbox خودش | خروج PII سلامت به vault/چت/لاگ؛ auto-apply self-mod؛ توکن جدا از @Robo2725 (409-safe)؛ **هنوز live نشده — نیاز به اولین اجرای مالک** |
| learning-engine | architect (spine عرضی L1–L9) | حلقه یادگیری contract-محور — spec: [[04 - Architect System/architect/04-Docs/2026-07-06 0222 LEARNING-ENGINE-DEPENDENCY-CONTRACT-v1.1-verdicts|v1.1]] · `trigger: loop` · risk posture: **maximum-within-charter** (verdict 2026-07-06) | **L0-shadow اکنون** → L3 (پشت Gate+git+budget) | manifest/ledger/HEARTBEAT/Active Contextها | `learning-engine/LEARNING-STATE.json` خودش + سطر HEARTBEAT + پیشنهاد propose-only | **هر call خارجی (Fugu/partner) تا ثبت کلید+budget = halt**؛ فایل خارج از manifest؛ charter/secret/پول |

## ناوگان اسکات تحقیق (Research Scout Fleet — فعال، استثنای گیت آری 2026-07-04)

> **⛔ زمین‌سنجی 2026-07-05 (بامداد):** زمان‌بندِ زنده **صفر** تسک داشت — کل ناوگان از 2026-07-04 21:29 خاموش (آخرین دیجست خودکار؛ مانیفست آرتیفکت هم خالی = reset state جلسه). دو تسک هستهٔ چرخه با پرامپت بهبودیافته re-arm شدند: `brain-focus-board` (`50 */3 * * *`، بی‌صدا) و `experience-review` (`30 21 * * 0`، notification) · verdict تکمیلی همان بامداد («هستهٔ کم‌مصرف»): + `brain-pulse` (`0 */3 * * *`) · `system-dashboard` (`20 */6 * * *`) · `mycelial-consolidator` (`0 22 * * *` — بازگشت از scale-up؛ اسکات‌ها تاریک) · `fleet-selection` (`0 23 * * 0`) → **۶ تسک زنده**. ۱۹ اسکات + ۶ لاین selfimprove عمداً تاریک (سنجش جدا + پلن). **قاعدهٔ نو ([[_memory/EXPERIENCE-LEDGER|ledger]]):** منبع حقیقت fleet = خروجی زندهٔ زمان‌بند؛ جدول‌های این نوت سندِ نیت‌اند، نه اثبات اجرا. re-arm بقیهٔ ردیف‌ها = pending-verdict آری.

> **⛔ زمین‌سنجی دوم 2026-07-05 (~۱۰:۵۵ صبح):** زمان‌بند **دوباره ۰ تسک** — reset دومِ همان روز (session قطع‌شده). با verdict آری («اجرا کن پرامپت‌های خودتو») [[04 - Architect System/architect/04-Docs/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور استقلال]] ratified شد و هر ۶ تسک با پرامپت autonomy-protocol-دار از نو ساخته شدند. **حفرهٔ bootstrap کشف شد:** وقتی همهٔ تسک‌ها هم‌زمان می‌میرند، هیچ تسکی نمی‌ماند که خودترمیمی §۳.۳ را اجرا کند → دو مهار: متن کامل پرامپت‌ها در [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]] (تک‌منبع بازسازی، داخل vault) + چک تطبیق زمان‌بند↔جدول ratified در شروع هر جلسهٔ تعاملی (HANDOFF). جدول ratified ↓

> برخلاف جدول بالا (بات‌های مستقرِ فاز ۴)، این ناوگان **زنده** است: تسک‌های زمان‌بندی Cowork که روی اشتراک Max آری اجرا می‌شوند. آری استثنای صریح گیت داد: autonomy = **propose-only با نوشتن فقط در `00 - Inbox/scout-digests/`**. پروتکل: [[05 - Agents/Research Scout Fleet|Research Scout Fleet]] · طراحی: [[05 - Agents/Mycelium Scout|Mycelium Scout]]. بودجه: اشتراک Max (نه D-25).

| اسکات | دامنه | autonomy | می‌نویسد | کران (سیدنی) | گارد ویژه |
|---|---|---|---|---|---|
| `mycelium` | طبیعت/architect | propose-only | دیجست در scout-digests | `0 7 * * *` | — |
| `crypto` | Crypto-etoro | propose-only | همان | `0 6 * * *` | — |
| `mining` | Mining | propose-only | همان | `0 8 * * *` | — |
| `lead` | Lead-نقاشی | propose-only | همان | `0 9 * * *` | — |
| `ziman` | Ziman | propose-only | همان | `0 10 * * *` | — |
| `accounting` | Accounting | propose-only | همان | `0 11 * * *` | فقط منابع رسمی AU |
| `hypnosis` | هیپنوتیزم | propose-only | همان | `0 12 * * *` | `epistemic_status` اجباری؛ fiction-canon = evidence نیست |
| `projectf` 🔒 | Project-F | propose-only | همان | `0 13 * * *` | فقط تحقیق عمومی؛ هیچ هویت/پلتفرم/محتوا echo نشود |
| `ai-watch` | قابلیت‌های نو AI | propose-only | همان | `0 14 * * *` | خوراک architect؛ فقط تحقیق |
| `security` | opsec/امنیت vault | propose-only | همان | `0 16 * * *` | هرگز secret واقعی نخواند/تست نکند؛ فقط دانش عمومی |
| `markets` | ماکرو/بازار | propose-only | همان | `0 15 * * *` | فقط تحقیق؛ هیچ ترید |
| `jobs` | بازار کار سیدنی | propose-only | همان | `0 17 * * *` | فقط تحقیق؛ بدون outreach |
| `health` | سلامت/بدن | propose-only | همان | `0 18 * * *` | epistemic؛ نه توصیهٔ پزشکی |
| `tools` | ابزار/اتوماسیون | propose-only | همان | `0 19 * * *` | بدون ثبت‌نام؛ pricing/lock-in ذکر شود |
| `philosophy` | فلسفه/مدل ذهنی | propose-only | همان | `0 20 * * *` | — |
| `world` | ژئوپلیتیک/جهانی | propose-only | همان | `0 21 * * *` | even-handed؛ بدون جانب‌داری سیاسی |
| `science` | علم مرزی | propose-only | همان | `0 23 * * *` | — |
| `learning` | یادگیری/مهارت | propose-only | همان | `0 2 * * *` | — |
| `local` | سیدنی/NSW محلی | propose-only | همان | `0 4 * * *` | — |
| `architect-selfimprove` ★ | خودبهبودی architect — لاین general/overflow | propose-only | همان (slug `selfimprove`) | `*/3 * * * *` (scale-up 10x؛ قبلاً `*/15`) | بک‌لاگ + synthesis + اسپور mycelium؛ هرگز apply/charter/blueprint edit؛ anti-overlap |

**جمع ناوگان: ۱۹ اسکات روزانه** (۶:۰۰–۰۴:۰۰، پوشش ~۲۴ساعته) + selfimprove هر۱۵دقیقه + consolidator (هر ۳ ساعت، سنتز کامل شبانه) + fleet-selection (یکشنبه) + brain-pulse (هر ۳ ساعت) + system-dashboard (هر ۶ ساعت، دقیقهٔ ۲۰) + **۶ لاین selfimprove (scale-up 10x)** + brain-focus-board (هر ۳ ساعت، دقیقهٔ ۵۰) + experience-review (یکشنبه ۲۱:۳۰) = **۳۲ تسک (کاغذی — زمین‌سنجی 2026-07-05: زمان‌بند ۰ داشت؛ فقط ۲ تسک هسته re-arm شده‌اند ⬆)** (ثبت brain-pulse/system-dashboard: verdict آری جلسهٔ دهم‌ب · ثبت لاین‌ها و cronهای 10x طبق [[04 - Architect System/architect/04-Docs/2026-07-04 1922 Scale-up ناوگان خودبهبودی (aggressive 10x)|runbook scale-up]] — throughput ≈ ~۱٬۰۰۸ اجرای selfimprove/روز · دو تسک چرخهٔ خودبهبودی: دستور آری بامداد ۰۵، [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]]). اسکات‌های شب (۲۳/۰۲/۰۴) در دور بعدی consolidator سنتز می‌شوند. fleet-selection کم‌سیگنال‌ها را هفتگی retire می‌کند.

**تخصیص خودبهبودی:** `architect-selfimprove` هر ۳۰ دقیقه (۴۸/روز) در برابر ۸ اسکات روزانه ≈ **~۸۵٪ اجراها**. adaptive (بک‌لاگ خالی → پاس سبک). دایال: `*/15` تندتر · `0 * * * *` ساعتی/۷۵٪. سقف واقعی = نرخ پلن Max.

### لایهٔ ارکستراسیون (propose-only)

| تسک | نقش | کران | خروجی |
|---|---|---|---|
| `mycelial-consolidator` | تریاژ هر اجرا (`_TRIAGE-BOARD.md`) + سنتز کامل فقط شبانه (≥۲۱:۰۰) | `0 22 * * *` (بازگشت 2026-07-05 — اسکات‌ها تاریک؛ در scale-up `0 */3` بود) | `synthesis.md` + `exec-digest.md` |
| `selfimprove-safety` | لاین خودبهبودی: گیت/halt/آدیت/اعتماد (R-01…R-09) | `1-59/15 * * * *` | دیجست خانواده‌دار در scout-digests |
| `selfimprove-memory` | لاین خودبهبودی: substrate/kin/evaporation/CoALA | `4-59/15 * * * *` | همان |
| `selfimprove-orchestration` | لاین خودبهبودی: fleet/consensus/topology/selection | `7-59/15 * * * *` | همان |
| `selfimprove-nature` | لاین خودبهبودی: زیست‌الگو → معماری | `10-59/15 * * * *` | همان |
| `selfimprove-tooling` | لاین خودبهبودی: typed-interfaces/config/observability | `13-59/15 * * * *` | همان |
| `selfimprove-deep` | لاین عمق: deep-research روی پرلوریج‌ترین آیتم باز | `20,50 * * * *` | همان |
| `brain-focus-board` | چرخهٔ idempotent تابلوی تمرکز + انباشت درس در [[_memory/EXPERIENCE-LEDGER\|EXPERIENCE-LEDGER]] (propose-only جز پارامترهای نمایشی) | `50 */3 * * *` | `01 - Dashboard/BRAIN-FOCUS-BOARD.html` + append در ledger |
| `experience-review` | بازوی verdict چرخهٔ خودبهبودی — مرور هفتگی ledger + سنجش اثر (propose-only) | `30 21 * * 0` | دیجست review در scout-digests + notification آری |
| `fleet-selection` | ارزیابی هفتگی و تنظیم ناوگان (retire/spawn) | `0 23 * * 0` | `fleet-eval.md` |
| `brain-pulse` | بازنویسی نبض مغز زنده از Active Contextها + آخرین synthesis (فقط لینک/state، نه secret) | `0 */3 * * *` (طبق HANDOFF جلسهٔ ۷ب) | [[01 - Dashboard/Brain\|Brain.md]] — overwrite (ratify §۸ هنوز باز) |
| `system-dashboard` | چرخهٔ idempotent داشبورد + ماژول Doctor (propose-only، طبق [[04 - Architect System/architect/04-Docs/Prompt - System Dashboard Artifact\|پرامپت]]) | `20 */6 * * *` (تأیید زنده 2026-07-04) | `01 - Dashboard/SYSTEM-DASHBOARD.html` |

### جدول تسک‌های ratified (مرجع خودترمیمی §۳.۳ منشور — restore فقط همین ۶)

> **قاعدهٔ سخت:** ۱۹ اسکات و ۶ لاین selfimprove **در این جدول نیستند** (عمداً تاریک، verdict «هستهٔ کم‌مصرف») — خودترمیمی هرگز آن‌ها را برنمی‌گرداند؛ re-arm آن‌ها فقط با verdict آری. متن کامل هر پرامپت: [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]].

| taskId | cron (سیدنی) | notify | نقش |
|---|---|---|---|
| `brain-focus-board` | `50 */3 * * *` | ✗ | تابلوی تمرکز + انباشت درس + شاخص استقلال |
| `brain-pulse` | `0 */3 * * *` | ✗ | بازنویسی Brain.md (استثنای overwrite) |
| `system-dashboard` | `20 */6 * * *` | ✗ | داشبورد سیستم + Doctor، سرکوب تک‌منبع |
| `mycelial-consolidator` | `0 22 * * *` | ✗ | سنتز شبانه + evaporation (بدون دیجست نو = خروج بی‌صدا) |
| `experience-review` | `30 21 * * 0` | ✓ | بازوی verdict هفتگی + چک HEARTBEAT |
| `fleet-selection` | `0 23 * * 0` | ✗ | ارزیابی هفتگی ناوگان (propose-only) |

**استثنای overwrite نو (ثبت §۸.۳ منشور):** `_memory/HEARTBEAT.md` — مشتق؛ هر تسک فقط سطر خودش را به‌روز می‌کند؛ جلسات تعاملی با نام `interactive`.

## قواعد سراسری

1. خطای خاموش = باگ درجه‌یک؛ هر شکست باید به HITL برسد (یافته آدیت fusion).
2. هر اکشن = ورودی Anchor Ledger؛ timeout تأیید = DENY (D-13).
3. بودجه API جمعی: hard-stop AU$30/ماه (D-25).
4. deploy هر ردیف فقط بعد از: rotation کامل + TOP-5 آدیت + پرامپت Phase 4 + verdict per-domain.

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
- [[03 - Projects/Ziman Galerry/Capacity & Channels|Ziman — Capacity & Channels]]
- [[03 - Projects/Crypto - etoro/Portfolio Registry|Portfolio Registry]]
