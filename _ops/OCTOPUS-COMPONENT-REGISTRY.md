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
