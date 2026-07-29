---
type: registry
status: living
phase: P0
date: 2026-07-18
tags: [octopus, registry, components, freeze, connections, source-of-truth]
parent: "[[../04 - Architect System/OCTOPUS-OS — استراتژی یکپارچه (تلگرام‌محور)]]"
method: "شواهدمحور: ممیزیِ اتصالاتِ 07-18 (۲۴ اندام) + BOTS-REGISTRY + پروبِ زندهٔ post-restart 16:39. Registry = منبعِ حقیقتِ اجزا."
---

# 🗂️ OCTOPUS — رجیستریِ واحدِ اجزا (P0)

> **این چیست.** منبعِ **واحدِ** حقیقت برای «هر جزء برای چیست، مالکش کیست، سالم است یا نه، و تصمیمِ ما دربارهٔ آن». همراهِ [[BOTS-REGISTRY|رجیستریِ بات‌ها]] کاملِ نقشهٔ عصبیِ اختاپوس را می‌دهد.
>
> **قانونِ Freeze (P0):** تا پایانِ فازها **هیچ حذفِ دائمی، هیچ merge، هیچ باتِ/UIِ جدید.** فقط: علامت‌گذاری، مخفی‌کردنِ برگشت‌پذیر، یا آرشیو (mv). هر تغییرِ کد فقط در worktreeِ ایزوله.

## وضعِ زندهٔ لحظه‌ای (پروبِ post-restart، ۱۶:۳۹) `[FACT]`

- **مغز زنده است** ✅ — `cortex/journal.jsonl` تازهٔ ۱۶:۳۹، `pulse/work-state.json` ۱۶:۲۰.
- **باتِ تلگرام poll نمی‌کند** ⚠️ — `_octopus/logs/telegram.log` = ۰ بایت. **ری‌استارتِ ارگانیسم بات را روشن نمی‌کند؛ باید `RUN-TG-CENTER.bat` جدا اجرا شود** (owner-gated؛ auto-launch ممنوع).
- **حالتِ کاغذی حفظ است** ✅ — `LIVE-ENABLED.flag` غایب، پول قفل. (درست — P7.)
- **فلگِ `OCTOPUS_WIRE_MISSION_RUNNER` هنوز غایب** → دکمهٔ 🧪 رفتارِ قدیمی دارد.

## راهنمای ستون‌ها
**Health:** 🟢 زنده‌ووصل · 🟡 نیمه‌وصل · 🔴 قطع/نمایشی · ⚫ یتیم/رقیب · 💤 خوابیده.
**تصمیم:** KEEP · CONNECT (وصل به bus/tick) · MERGE · HIDE (مخفیِ برگشت‌پذیر) · ARCHIVE (mv به `_Archive`) · DECIDE (رأیِ مالک).

---

## ۱) هسته و مغز — Core / Brain

| ID | جزء | نقش | مالک | Health | ریسک | تصمیم |
|---|---|---|---|---|---|---|
| C1 | `organism.py` + `cortex/` | رییس/مغز، beat loop | Core | 🟢 | high | **KEEP** |
| C2 | `cortex/model_router.py` | روترِ LLM سه‌لایه (local→GLM→Fugu) | Core | 🟢 | high | **KEEP** (رییس=frontier) |
| C3 | `heart/cardiac.py` | ضربان/setpoint | Core | 🟢 | high | **KEEP** |
| C4 | `budget/` + `telemetry.py` | بودجه/هزینه (AU$0.03/mo) | Core | 🟢 | high | **KEEP** |
| C5 | `mission_contract.py` ✨نو | ستون‌فقراتِ قرارداد (envelope/sha/validate) — ۶/۶ تست سبز، stdlib، inert تا import | Core | 🟢 | low | **KEEP** (همه به آن conform) |

## ۲) دروازهٔ تلگرام — Gateway (تنها درگاهِ تو)

| ID | جزء | نقش | Health | تصمیم |
|---|---|---|---|---|
| G1 | `center.py` (TG Center bot) | Gateway، منو/فرمان/گزارش | 🟡 poll نمی‌کند | **KEEP + CONNECT** (منوی ۶‌گزینه) |
| G2 | `approval_channel.py` (Unified bot) | Overseer، کارتِ ✅/❌ | 🟢 | **KEEP** |
| G3 | `render.py` | ساختِ کارت/منو | 🟢 | **KEEP** (منبعِ callback واحد شود) |
| G4 | `actions.py` | اسکلتِ ۱۷۱خطیِ callback | ⚫ یتیم (صفر import) | **MERGE→G3 یا DELETE-PENDING** |
| G5 | دکمه‌های `ms:test`/`ms:review` | اجرا | 🔴 فقط add_note | **HIDE تا P1** |
| G6 | `langar_bridge` | دستورهای استودیو (Project-F) | 🟡 fail-open | **KEEP + سخت‌سازی** (fail-closed) |
| G7 | `owner_menu.py` ✨نو | منبعِ واحدِ منوی ۶‌گزینه + routing + new-mission→contract — ۶/۶ سبز، graceful تا GLM-A | 🟢 | low | **KEEP** (جایگزینِ یتیمِ G4؛ حلِ D-009) |
| G8 | `owner_views.py` ✨نو | read-modelِ ①③④ (pending/legs-RAG/dashboard) از state واقعی — ۴/۴ سبز + smokeِ زندهٔ read-only | 🟢 | low | **KEEP** (داده، نه رقیبِ render.py) |
| G9 | `owner_debug.py` ✨نو | ⑤ اسکنِ زندهٔ read-only (خطا/قطع/تکراری/UIِ‌زائد) — ۳/۳ سبز + smokeِ زنده ۷ یافته | 🟢 | low | **KEEP** (doctor-lite، نه رقیبِ doctor/) |
| G10 | `menu_integration.py` ✨نو | delegateِ `center.py` برای پنلِ ۶‌گزینه — ۶/۶ سبز + smokeِ زنده | 🟢 | low | **KEEP** |
| G11 | `center.py` **سیم شد** | `/panel` + verbِ `m:` پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_MENU_V2` — **صفر حذف**، ast سالم، +۲۹ خط، flag-off=رفتارِ قبلی | 🟢 | low | **KEEP** |

**پوششِ منوی ۶‌گزینه:** ① `owner_views.dashboard` · ② `owner_menu.handle_new_mission`→`mission_contract` · ③ `owner_views.pending_decisions` · ④ `owner_views.legs_status` · ⑤ `owner_debug.scan` · ⑥ `/stop`,`/panic` موجود (route، نه بازسازی). **همه ۶ پشتوانه دارند.**

## 🧩 خروجی‌های موازیِ GLM (2026-07-18) — راستی‌آزمایی‌شده

| کارگر | تحویل | امضا | وضعیت | wiring (لِینِ Claude) |
|---|---|---|---|---|
| GLM-A | `legs/lead_leg_inbox.py` | `register_lead/list_leads/get_lead` → `{ok,status,lead_id,reason}` | **روی برنچ `claude/lead-leg-backend`** (merge نشده) · ۱۳/۱۳ سبز (ویندوز) · gate `OCTOPUS_WIRE_LEAD_INBOX` | `owner_menu` آشتی شد (نام+قرارداد)؛ merge با مالک |
| GLM-B | `doctor.advance_rfcs()` | `advance_rfcs(max_n=1)` | **نشسته در master** · ۲۰/۲۰ (ویندوز) · gate `OCTOPUS_WIRE_DOCTOR_ADVANCE` | وصل به cortex tick |
| GLM-C | `observability/health_check.run()` + `render_status_summary()` | `run()->dict` | **نشسته در master** · ۱۶/۱۶ (ویندوز) | وصل به governor epoch + صفحهٔ ①؛ می‌تواند جایگزینِ منطقِ داخلیِ `owner_views` شود |
| GLM-D | `approval_store.verify_scope()` + `content_sha256` | `verify_scope(jid,payload)->bool` | **نشسته در master** · ۸/۸ + ۲۴/۲۴ + run_all ۲۰۳ (ویندوز) · از `mission_contract`ِ ما استفاده کرد ✅ | وصل به مسیرِ apply (`power.py`/`mission_runner`) |

> **نکتهٔ سندباکس:** سه سوئیتِ نشسته را در سندباکسِ لینوکسیِ من نمی‌شود اجرا کرد (وابسته به `genome-system/ledger` با مسیرِ خامِ ویندوزی — تلهٔ [[../../…/vault-sandbox-quirks]]). روی ویندوزِ مالک سبزند. چهار ماژولِ stdlib‌ِ Claude اینجا هم سبزند (۲۰/۲۰).
> **نکتهٔ قرارداد (از GLM-B):** `make_envelope` مقدارِ `payload` را برای هش مصرف می‌کند ولی در envelope ذخیره نمی‌کند (عمدی — ضدِنشت؛ `verify_scope` payload را جدا در زمانِ apply می‌گیرد). اگر بعداً echo لازم شد، تصمیمِ لِنز است.

## ۳) پاها — Legs (Leg Owners)

| ID | پا | مالک | Health | تصمیم |
|---|---|---|---|---|
| L1 | `legs/lead_leg.py` (نقاشی) | Lead Owner | 🔴 lead-inbox نیست، `/lead` وصل نیست | **CONNECT (P2)** |
| L2 | زیمان (کاتالوگ) | مامان | 🔴 `ziman-catalog.json` نیست | **CONNECT** |
| L3 | `legs/accountant.py` | Accounting Owner | 🟡 DATA-ONLY (بی bank-feed) | **CONNECT تدریجی** |
| L4 | Mining | Mining Owner | 💤 flag، Round-2 باز | **KEEP (منتظرِ رأی)** |
| L5 | Crypto | — | 🟡 فقط freshness از دادهٔ stale | **KEEP/بازبینی** |
| L6 | `mission_runner.py` | Worker | 🟡 ساخته، فلگ خاموش | **CONNECT (P1)** |

## ۴) دکتر و یادگیری — Doctor / Learning

| ID | جزء | نقش | Health | تصمیم |
|---|---|---|---|---|
| D1 | `doctor/doctor.py` + `rfcs` | سنجش/RFC | 🟡 RFC در `submitted` گیر | **CONNECT** (`advance_rfcs` به tick) |
| D2 | `cortex/code_autonomy.py` | خودتغییرِ کد (worktree واقعی) | 🟢 ولی جدا از mission | **MERGE** با Mission Bus |
| D3 | `doctor/chamber.py` | مناظرهٔ خصمانه | 🔴 stubِ بی‌صدا | **DECIDE** (پیاده یا ARCHIVE) |
| D4 | `observability/*` | مانیتور | 🔴 فقط CLI دستی | **CONNECT** به governor epoch |

## ۵) حافظه و state — Memory / State

| ID | جزء | Health | تصمیم |
|---|---|---|---|
| M1 | `memory` SQLite + Chroma | 🟢 | **KEEP** |
| M2 | `_memory/` (نوشتهٔ ایجنت‌ها) | ⚫ مصرف‌نشده توسط `_ops` | **DECIDE** (ماشین یا مستنداتِ انسانی) |
| M3 | vault ابسیدین | 🟢 | **KEEP** |

## ۶) یتیم‌ها و رقیب‌ها — Orphans / Competing (کارِ ایجنت‌های موازی)

| ID | جزء | واقعیت | تصمیم |
|---|---|---|---|
| O1 | `octopus_core/` | رقیب؛ **صفر importِ واقعی تأیید شد** (۴ «ارجاع» فقط رشتهٔ `owner="octopus_core"` بود، نه import) | **ARCHIVE امن** (با «برو»ی مالک) |
| O2 | `07 - Knowledge/genome-system/` | `.git` مستقل؛ **⚠ `ledger/ledger.py` را `health_check`/telemetry واقعاً import می‌کند** (کشفِ یکپارچه‌سازی 07-18) | **DECIDE — آرشیوِ کورکورانه telemetry را می‌شکند** |
| O3 | `_launchpad/*` (بات‌های نودجی‌اس) | Painting/Accounting/Control-brain، ID مشترک | **ARCHIVE/deprecate** |
| O4 | `4d_system/` | «ایده‌یاب»، تنانتِ جدا | **KEEP جدا** (منبعِ حقیقت = این، نه کپیِ دسکتاپ) |
| O5 | `OCTOPUS/nervous-system/` | اسنپ‌شاتِ منجمدِ 07-12، مسیرِ دسکتاپ | **ARCHIVE** (یا repoint، TASK-REFRESH) |

## ۷) بات‌ها — خلاصه (کاملش در [[BOTS-REGISTRY]])

از ۹ تعریف، **۲ زنده** (G1, G2). ۷ خوابیده؛ سه‌تا ID/توکنِ مشترک (مینِ ۴۰۹) → **ARCHIVE/deprecate رسمی**: Control-Brain، Accounting-node، 4D-Brain-bot.

---

## 🔌 اتصالاتِ نامرئی (کوپلینگِ پنهان که در تلگرام دیده نمی‌شود) `[FACT از ممیزی]`

1. **دو دنیای تأییدِ موازی:** `mission.py` (تأییدِ مأموریت) و `code_autonomy.py` (تأییدِ کد) هم را import نمی‌کنند → دو صفِ جدا که می‌توانند drift کنند. **پل:** `mission_runner` (D-005).
2. **genome-system↔telemetry:** فقط از راهِ `ledger.jsonl` وصل‌اند (تله‌متری هزینه می‌خواند) — بقیهٔ genome جزیره است.
3. **`_memory`↔هیچ‌کس:** ایجنت‌ها می‌نویسند، `_ops` نمی‌خوانَد (کوپلینگِ صفر، توهمِ حافظه).
4. **observability↔هیچ tick:** ابزارها هستند، صداکننده ندارند.
5. **center↔render callbackها hardcode:** `actions.py` (منبعِ قرار بود واحد باشد) دور زده شده → drift.

---

## ✂️ تصمیم‌های هرسِ UI (برگشت‌پذیر، اجرا در worktree)

| UI | چرا | اقدام |
|---|---|---|
| 🧪 `ms:test`/`ms:review` | فقط add_note، اجرا نمی‌کند | **HIDE** تا P1 وصل شود |
| منوهای تکراریِ status/refresh | چند نسخه | **یکی‌کن** در منوی ۶‌گزینه |
| CLIهای observability در دیدِ کاربر | مصرفِ runtime ندارند | **پشت‌صحنه** |

---

## 📊 جمع‌بندیِ تصمیم‌ها

**KEEP:** ۱۲ · **CONNECT:** ۷ · **MERGE:** ۲ · **HIDE:** ۲ · **ARCHIVE:** ۴ · **DECIDE (رأیِ تو):** ۳ (`chamber` · `genome-system` · `_memory`).

**قدمِ بعدِ P0 (بازنگری‌شده پس از راستی‌آزمایی):** آرشیوِ کورکورانه لغو شد — **هم `octopus_core` (۴ ارجاع) هم `genome-system` (ledgerِ زندهٔ telemetry) وابستگیِ احتمالی دارند.** فقط `O5 nervous-system` (اسنپ‌شاتِ منجمدِ 07-12) کاندیدِ امنِ آرشیو است. برای O1/O2 اول یک import-graphِ واقعی (نه grepِ رشته) لازم است — کارِ بعدیِ من اگر بخوای. طبقِ Freeze هیچ حذف/آرشیوی بی‌«برو»ی تو نیست.

*شواهد: `OCTOPUS-DEEP-CONNECTIVITY-AUDIT-2026-07-18` · `BOTS-REGISTRY` · پروبِ زندهٔ ۱۶:۳۹. هیچ کدِ زنده‌ای تغییر نکرد؛ این سند فقط نقشه است.*

## 🧭 CHORD — فیلترِ وترِ ریاضی (نو، 2026-07-18)

| ID | جزء | نقش | مالک | Health | ریسک | تصمیم |
|---|---|---|---|---|---|---|
| CH1 | `_ops/chord/` ✨نو | داورِ شواهدمحورِ تعمیر برای دکتر/خودترمیم‌ها (وترِ وزن‌دار + گیتِ عدم‌قطعیت + policy + ledger هش‌زنجیره؛ shadow-only، ۳۰/۳۰ تست سبز، LLM فقط از درِ `model_router` با JSON سخت‌گیر) | Doctor | 💤 off-loop، صفر وایرینگ | low | **KEEP + CONNECT در فاز C** (worktree، پشتِ `OCTOPUS_WIRE_CHORD_SHADOW` خاموش؛ کارتِ تلگرام = مأموریتِ جدا پشتِ `OCTOPUS_WIRE_CHORD`) |

سند: `04 - Architect System/CHORD — معماری فیلترِ وتر (v0).md` · پرامپتِ فاز C: `octopus-build-prompts/CHORD-AGENT-PROMPT-2026-07-18.md`

## 🔗 الحاق دو پروژهٔ مالک (نو، 2026-07-20 — دستور مالک)

| ID | جزء | نقش | مالک | Health | ریسک | تصمیم |
|---|---|---|---|---|---|---|
| TQ1 | `03 - Projects/Lead-نقاشی/tradequote_local/` ✨نو | اپ آفلاین کوتیشن/فاکتور (Flutter/Drift، GST/ABN، PDF) — ابزار دستِ مالک برای پای لید نقاشی؛ MVP کامل، **هنوز کامپایل‌نشده** (build مالک: `docs/BUILD_AND_RELEASE.md` §1) | Lead-نقاشی | 💤 خارج از loop | low | **KEEP** (کد در vault؛ `.git` داخلی عمداً حذف شد) |
| TQ2 | `_ops/legs/tradequote_bridge.py` ✨نو | پل propose-only: draft کوتیشن lead_quote → بستهٔ handoff (JSON سنت‌صحیح + TXT انسان‌خوان) در `state/legs/tradequote-outbox/`؛ E1 خالص، صفر شبکه | Lead-نقاشی | 💤 پشت `OCTOPUS_WIRE_TRADEQUOTE` (خاموش) | low | **KEEP + فعال‌سازی با رأی مالک** (۵/۵ تست سبز) |
| WL1 | `03 - Projects/WLOS - Weight Loss OS/wlos/` ✨نو | کوچ کاهش وزن مالک (TS monorepo، v0.1.1، 135/135 تست) — «اندام شناخت مالک» برای مغز اصلی؛ **هنوز live نشده** (اولین اجرا: owner-only) | مالک/مغز | 💤 مستقل | med (PII سلامت — DB بیرون git) | **KEEP** (`.env.example` عمداً وارد نشد) |
| WL2 | `_ops/cortex/wlos_bridge.py` ✨نو | سیگنال sanitized مالک برای مغز: خواندن whitelist-فقط از `state/wlos/owner-summary.json` (بدون هویت/بدون weight خام)؛ مصرف: `doctor/self_knowledge.snapshot()` فقط وقتی سیگنال هست | Doctor/Cortex | 💤 پشت `OCTOPUS_WIRE_WLOS` (خاموش) | low | **KEEP + فعال‌سازی با رأی مالک** (۵/۵ تست سبز؛ OCTOPUS هرگز در فایل سیگنال نمی‌نویسد) |

شواهد: دلتا-اسکن 2026-07-20 (بستهٔ A/B/C در چت مالک) · تست‌ها: `_ops/tests/test_tradequote_bridge.py` + `test_wlos_bridge.py`.

## 🎯 TRUST ENGINE — لولهٔ ارزشِ لید (فاز C، نو 2026-07-21، رأی تامِ مالک)

طراحیِ حاکم: `03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/PHASE-B-CONTRACTS/` (متخاصم-verify). همه flag-off، propose-only، صفر ارسالِ بیرونی.

| ID | جزء | نقش | فلگ (خاموش) | Health | تست |
|---|---|---|---|---|---|
| TE1 | `_ops/legs/consent_firewall.py` ✨ | دیوارِ رضایتِ fail-closed (market_signal هرگز outreach؛ هر استثنا→بسته) — تابعِ خالص | — (کتابخانه، همیشه fail-closed) | ✅ قوسِ داخلی | `test_consent_firewall.py` 7/7 |
| TE2 | `_ops/legs/lead_candidate_inbox.py` ✨ | آداپترِ canonicalِ ورودی (submit_candidate): validate→firewall→dedup→receipt→routing؛ market_signal فایلِ draft نمی‌سازد | `OCTOPUS_WIRE_LEAD_CANDIDATES` | 💤 | `test_lead_candidate_inbox.py` 8/8 (synthetic E2E) |
| TE3 | `_ops/legs/lead_boundary_http.py` ✨ | مرزِ امضاشدهٔ `POST /api/v1/lead-candidates` روی 127.0.0.1:8774 (HMAC/nonce/idempotency/quarantine) | `OCTOPUS_WIRE_LEAD_BOUNDARY` | 💤 listener بالا نمی‌آید | `test_lead_boundary_http.py` 9/9 (+smoke سوکت) |
| TE4 | `_ops/legs/effector_gate_bridge.py` ✨ | گاردِ stalenessِ releasable (settle_fresh): releasableِ کهنه refuse؛ chrono دست‌نخورده | — (کتابخانه) | ✅ | `test_effector_gate_bridge.py` 5/5 |
| TE5 | `_ops/telegram_center/llm_intent.py` ✨ | فهمِ free-text مالک→پیشنهادِ مأموریتِ گیت‌شده (propose-only)؛ wired در `center._handle_ask` | `OCTOPUS_TG_LLM_ASK` | 💤 wired-shadow | `test_llm_intent.py` 8/8 + `test_llm_intent_wiring.py` 4/4 |
| TE6 | `_ops/heart/cognition_effect.py` ✨ | ثبتِ effectِ شناختیِ بیرونی-تأییدشده (کانالِ value قلب) | `OCTOPUS_WIRE_COGNITION_EFFECT` | 💤 | `test_heart_cognition.py` 7/7 |
| TE7 | `_ops/heart/fuel_meter.py` ✨ | مترِ سوختِ واقعیِ API/Ollama (خونِ قلب) + consumer در `producers.velocity_meter` | `OCTOPUS_WIRE_HEART_FUEL` | 💤 | `test_heart_fuel.py` 7/7 |

فعال‌سازیِ کاملِ لوله (owner-gated، پس از رأی روی قراردادها): `set OCTOPUS_WIRE_LEAD_CANDIDATES=1` + `OCTOPUS_WIRE_LEAD_BOUNDARY=1` + secretهای `OCTOPUS_INGEST_SECRET_<SRC>` (فقط .env مالک) + restart. فاز C پیاده شد؛ فاز D (workerِ outbound واقعی) = رأیِ جدا.

## 🧠 SELF-ACCURACY — معیارِ دقتِ خودمدل C3 (نو ۲۰۲۶-۰۷-۲۸)

اولین سنجهٔ ملموسِ «چقدر از خودم نمی‌دانم». بازسنجیِ ۲۰۲۶-۰۷-۲۵ گفت C3 «NOT_MEASURED» است؛ این شکاف را می‌بندد. پیش‌نیازِ خود-اصلاحیِ ایمن (C4): تا امروز ارگانیسم می‌توانست با اطمینانِ کامل غلط بگوید (۰۷-۲۵: ۱ لِگ به‌جای ۴؛ ۰۷-۲۷: خرج به‌جای درآمد).

| ID | جزء | نقش | فلگ (خاموش) | Health | تست |
|---|---|---|---|---|---|
| SA1 | `_ops/doctor/self_accuracy.py` ✨ | سنجشِ ادعای `snapshot()` در برابرِ منابعِ حقیقتِ مستقل (legs/revenue/wire_on) → `{accuracy, drifts[]}`؛ سریِ زمانیِ صداقت | `OCTOPUS_SELFKNOW_ACCURACY` | 💤 shadow | `test_self_accuracy.py` ۱۳/۱۳ سبز |
| SA2 | wiring در `doctor/self_knowledge.run()` ✨ | تزریقِ `self_accuracy` به هر دو شاخه (cached/changed)؛ flag-off = byte-identical | همان فلگ | 💤 | اثباتِ زنده: flag-on → فیلد ظاهر؛ flag-off → ناپدید |

خروجی: append-only به `_ops/state/doctor/self-accuracy.jsonl` (سریِ زمانیِ صداقتِ C3 — شکافِ «حاضر ولی نه سنجش‌پذیر» از ۰۷-۲۵). خطِ قرمز: فقط‌خواندنی نسبت به state/ژنوم/ledger؛ $0؛ fail-soft. فعال‌سازی: `set OCTOPUS_SELFKNOW_ACCURACY=1` در flags.cmd + restart ♻️.

## 👁 SYNAPSE SENSE — بیداریِ حسِ خود-ارجاعی C8 (نو ۲۰۲۶-۰۷-۲۸)

سه ماژولِ synapse از ۲۰۲۶-۰۷-۲۴ کاملاً ساخته بودند ولی **ادغامِ رانتایمِ صفر** داشتند: هیچ beat/وایرینگ/فلگی آن‌ها را صدا نمی‌زد و `out/` هیچ‌وقت فایل نگرفت. این اولین وصل‌کردن به رانتایم است.

| ID | جزء | نقش | فلگ (خاموش) | Health | تست |
|---|---|---|---|---|---|
| SN1 | `wiring.synapse_beat()` + `organism.py` tick ✨ | وصل‌کردنِ SENSE به ضربان: هر N beat یک چرخهٔ `sense_once`؛ flag-gated، STOP-aware، non-blocking | `OCTOPUS_SYNAPSE_ENABLED` | 💤 shadow | `test_synapse_beat.py` ۷/۷ سبز |
| SN2 | `_ops/synapse/sense.py::_append_trail` ✨ | سریِ زمانیِ صداقتِ C8: هر چرخه ردیفی با `{ts, cpm, self_referential, gate0, delta, kind}` به `state/synapse-trail.jsonl` | همان فلگ | 💤 | `test_synapse_sense.py` ۳ چکِ trailِ نو سبز |

خروجی: proposal در `_ops/synapse/out/` + ردیفِ صداقت در `state/synapse-trail.jsonl`. این دقیقاً شکافِ «sinkها per-cycle نه self_referential می‌نوشتند نه gate0 را نه علامتِ Δ» (از ۰۷-۲۵) را می‌بندد. `sense.flag_on()` هر دو نامِ `OCTOPUS_SYNAPSE_ENABLED` (canonical) و `SYNAPSE_ENABLED` (backward-compat) را می‌پذیرد. $0 (صرفاً ریاضی)، propose-only، fail-closed. فعال‌سازی: `set OCTOPUS_SYNAPSE_ENABLED=1` در flags.cmd + restart ♻️. نقطهٔ بعدی: مرحلهٔ ۳ (C4/خود-اصلاحیِ twin-tested) — ولی پیش‌نیازش R5-prevent (مهارِ واقعی).

## 🩺 OCTOPUS-DOCTOR — دکترِ اختاپوس: چشم/ذهن/انگشت/بازو/صدا (نو ۲۰۲۶-۰۷-۲۹)

دو بستهٔ نشست‌های ابری نصب شد و برای اولین بار **روی خودِ لپ‌تاپ** سنجیده شد (۲۲۱ سبز، نه ابری). دکتر = پکیجِ stdlib-only با والتِ Obsidian به‌عنوانِ حافظه؛ حلقهٔ آینده: پیامِ مالک در تلگرام → کارتِ نیت → worktree → سوئیت → کارتِ دیف → رأی → merge. نامِ importیِ `doctor` ملکِ `_ops/doctor` می‌ماند — پل عمداً subprocess/JSONL است، صفر import.

| ID | جزء | نقش | فلگ (خاموش) | Health | تست |
|---|---|---|---|---|---|
| DR1 | `OCTOPUS-DOCTOR/doctor/` ✨ | چشم (`scanner` فقط‌خواندنی) · ذهن (`mind` = ناخودآگاهِ جمعی، رنگ می‌دهد تصمیم نمی‌گیرد) · انگشت (`propose` با ۸ گیتِ در-کد + R-09) · مغز (`fugu` با دو سقفِ روزانه: ۶۰ فراخوان + $۲) · صدا (`channel` حالتِ outbox) | مغز: `SAKANA_API_KEY` **یا** `FUGU_API_KEY` (نامِ مالک؛ از `.env` via `_ops/run_doctor_day.py`) | 🟢 **LIVE** — اولین ask واقعی `fugu·418tok·exit 0` (۰۷-۲۹) | `test_doctor.py` ۱۵۷/۱۵۷ سبز |
| DR2 | `_ops/os_v1/` ✨ | کتابخانهٔ OS: `honest_metric`/`outcome_ledger`/`efe`/`policy_sampler` (قید حذف می‌کند نه جریمه)/`silence`/`leg_failure`/`mission_runner` (worktree + گیتِ سوئیت + merge فقط با رأی؛ `env_root_key` سوئیت را به درختِ زیرِ آزمون pin می‌کند) | — (library، بدونِ side-effect) | 💤 (صفر صداکنندهٔ زنده تا VQ-DR-003) | `test_os_v1.py` **۷۸/۷۸** سبز |
| DR3 | `_ops/telegram_center/doctor_link.py` ✨ | پلِ outboxِ دکتر → clientِ مرکز (بدونِ اتصالِ دومِ تلگرام) + جداسازیِ رأیِ سه‌تکهٔ `ok\|no:gate:mission` قبل از fallbackِ approval → `cli.py votes`؛ cursorِ بایتی + dedupِ mission:gate + سقفِ ۲۰/روز | `OCTOPUS_WIRE_DOCTOR_TG` = **1** (رأیِ مالک ۰۷-۲۹، VQ-DR-001) | 🟢 **LIVE** — کارتِ تست `message_id=323` تحویل شد | `test_doctor_link.py` ۱۸/۱۸ سبز؛ ثبت در `run_all.py`؛ تسکِ روزانه `OCTOPUS-doctor-day` ۰۷:۰۰ |

خطِ قرمزِ دکتر (در کد، با تست): در `_ops` نمی‌نویسد · پچ اعمال نمی‌کند · merge سه‌قفله (رأیِ ✅ دیف + `--apply` + `OCTOPUS_DOCTOR_MAY_MERGE=1` که **تنظیم نشده**). فعال‌سازیِ پل: `set OCTOPUS_WIRE_DOCTOR_TG=1` در flags.cmd + ری‌استارتِ TG-center ♻️. پلهٔ بعد (رأیِ مالک): کلیدِ Sakana برای پله‌های ۱–۲ (ask/diagnose/propose)، و `day --live` فقط زیرِ چشمِ مالک.

## 🌐 SPLIT + شهود — درون/بیرون و اندامِ حسیِ نو (نو ۲۰۲۶-۰۷-۲۹)

رأیِ مالک: هسته بینِ دو بات تقسیم شود — باتِ ۱ «درون» (خودترمیمی/سلامت) و باتِ ۲ «بیرون» (رابطِ شخصی). طرح: `06 - Architecture Maps/TG-SPLIT-INNER-OUTER-2026-07-29.md`.

| ID | جزء | نقش | فلگ (خاموش) | Health | تست |
|---|---|---|---|---|---|
| SP1 | `_ops/telegram_center/surface-routing.json` ✨ | نگاشتِ جریان→بات/تاپیک — **مالِ مالک، قابلِ ویرایشِ دستی**؛ current=واقعیتِ امروز، target=طرحِ درون/بیرون | `OCTOPUS_TG_SPLIT_V1` (مصرف‌کننده هنوز ساخته نشده) | 💤 config-only | — |
| INT1 | `_ops/os_v1/schumann_rx.py` + `OCTOPUS-DOCTOR/40-اندام‌ها/ORG-08-شهود.md` ✨ | اندامِ شهود (شومان): معادلات از امروز در context ِ مغز؛ فیدِ حسگر تا سخت‌افزار **[UNKNOWN] — هیچ دادهٔ ساختگی**؛ پروتکلِ ۳۰ روزِ منفعلِ MAG-09 بعد از ساخت | — (تا حسگر) | 🟡 ریاضی+کد سبز، حسگر غایب | `test_os_v1.py` (schumann_rx داخلِ سوئیت) |
