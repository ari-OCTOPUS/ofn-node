---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, research, deep-scan, all-dimensions, 2026-08-24]
created: 2026-08-24
updated: 2026-08-24
created_by: owner-requested-research
method: "اسکن مستقیم درخت (find/ls/grep/read) + وضعیت زنده (netstat/tasklist) + git log — بدون تغییر هیچ فایلی جز همین سند"
sources:
  - "[[06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH]]"
  - "[[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-29]]"
  - "[[06 - Architecture Maps/OCTOPUS-NEXT-ACTIONS]]"
  - "[[06 - Architecture Maps/OCTOPUS-KNOWN-RISKS]]"
  - "[[OCTOPUS/CURRENT-TRUTH]]"
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[01-TRUTH/CONTRADICTIONS]]"
---

# 🐙 تحقیق جامع اختاپوس — همهٔ ابعاد (۲۰۲۶-۰۸-۲۴)

> این سند حاصلِ اسکنِ مستقیمِ درختِ زندهٔ `F:\backup` است (نه بازسازی از گزارش).
> هر ادعا مسیر دارد؛ هر وضعیت، شاهدِ فایل/پورت/PID. هیچ چیز جعل یا «احتمالاً» نشده.
> خوانندهٔ تازه‌وارد: اول [[00-README-START-HERE|۰۰]] و [[01-ALL-AGENTS-INSTRUCTION|۰۱]] را بخوان.

---

## ۱) اختاپوس چیست؟ (یک‌خطی)

**اختاپوس = «رییس»: یک ارگانیسمِ نرم‌افزاریِ همیشه‌روشنِ پایتون (`_ops/`، ~۷۰۰ ماژول که ~۴۰۰ تایشان تست‌اند) که در یک vaultِ Obsidian (F:\backup) زندگی می‌کند، با مالکش از طریق دو باتِ تلگرام حرف می‌زند، حافظه‌اش markdown+git+ledgerِ هش‌زنجیره‌ای است، و ۸–۹ «پا» (پروژه‌های کسب‌وکار) را زیرِ چترِ حاکمیتِ گیت‌محور و budget-محور اداره می‌کند.**

باورِ مرکزی: *evidence over claim* — هر ادعا باید با مسیرِ واقعی لنگر داشته باشد؛ درختِ زنده برنده است نه گزارشِ قبلی.

---

## ۲) معماری لایه‌ای (مستندِ مرجع: `06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-29.md`)

| لایه | نقش | فناوریِ واقعی | مسیر |
|---|---|---|---|
| L0 Constitution | قانونِ ماشین‌خوان | `CLAUDE.md` · `_PROJECT_INSTRUCTIONS.md` · `.agentignore` | ریشه |
| L1 Substrate | حافظهٔ پایدار | Obsidian · git · JSONL · SQLite · ledger هش‌زنجیره‌ای | `07 - Knowledge/` · `_ops/state/` |
| L2 Business | ۸–۹ tenant (پاها) | `03 - Projects/` + `_ops/legs/` (۵۶ ماژول) | `03 - Projects/` |
| L3 Organism | سازوارهٔ همیشه‌روشن | `_ops/` — organism.py · cortex · heart · budget · neural · epistemics · events · governor | `_ops/` |
| L4 Meta-brain | معمار + دکتر + پرایم | `04 - Architect System/` · `OCTOPUS-DOCTOR/` · `OCTOPUS-PRIME/` | پوشه‌های ریشه |
| L5 Governance | انسان + دو بات | مالک (تنها منبعِ verdict) + بات ۱ (درون‌ارگانیسم) + بات ۲ (رابط شخصی) | `_ops/telegram_center/` |

**پروسه‌های زنده در لحظهٔ این اسکن (netstat + tasklist، 2026-08-24):**

| پورت | PID | سرویس |
|---|---|---|
| 8771 | 15272 | organism (حلقهٔ متابولیسم + beat) |
| 8772 | 21056 | cortex (مغز/مسیریاب مدل) |
| 8773 | 11196 | live cockpit (داشبورد) |
| 8774 | 6452 | miniapp gateway (فقط localhost — URL عمومی منتشر نشده) |
| 8776/8777 | 6432/15272 | اضافی/پایپلاین |
| 11434 | 20280 | ollama (مدل محلی) |

---

## ۳) مؤلفه‌های اصلی (عضوی به‌عضوی)

| اندام | نقش | مسیر کانونیکال | وضعیت |
|---|---|---|---|
| organism | حلقهٔ ضربان (beat ~47k)، HTTP 8771 | `_ops/organism.py` | 🟢 LIVE |
| cortex | مغز: `model_router.ask()` تنها choke-point مدل (خط ۴۲۶) | `_ops/cortex/model_router.py` | 🟢 LIVE |
| heart | ضربان/هومئوستاز | `_ops/heart/` | 🟢 (کارت‌ها قبلاً HOLD می‌شدند) |
| budget | گیت‌ها و متابولیسم پول؛ governor جدا | `_ops/budget/` | 🟡 governor **untracked** |
| governor | مسیریاب بودجه (primary/secondary/local) | `_ops/budget/governor.py` (۲۶.۸KB) | 🟡 untracked + تست ۱۷/۱۷ سبز + فلگ خاموش |
| neural | تثبیت حافظه (Hebbian) | `_ops/neural/` | 🟢 |
| epistemics | برچسب fact/hype + رسید | `_ops/epistemics/` | 🟢 ADR-039 (۴۵+۲۰ تست، default-OFF) |
| events | ۷ نوع رویداد تایپ‌شده + Envelope | `_ops/events.py` | 🟢 |
| telegram_center | بات ۲ + gateway + miniapp | `_ops/telegram_center/center.py` (۴۵۷۱ خط) | 🟢 (قفل‌های ارسال سخت) |
| agi2027_control | کنترل‌پلین (۱۱ فرمان) + owner-auth | `_ops/agi2027_control/` | 🟢 |
| wiring | ثبت مرکزی فلگ‌ها (PAPER_FULL_FLAGS، ۱۳ عضو) | `_ops/wiring.py` | 🟢 — فلگِ نو بیرونِ tuple و خاموش |
| nervous_recovery | لایهٔ بازیابی/دریافت | `_ops/nervous_recovery/` | 🟢 |
| octopus_mcp | سرور MCP (سخت‌سازی DoS اخیر) | `_ops/octopus_mcp/` | 🟢 کامیت‌های `f9f294b`/`d883867` |

**فلگ‌های runtime فعلی (`_ops/agi2027_runtime/managed_flags.json`):** `OCTOPUS_WIRE_TG_CONTROL=1` · `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL=1` · `OCTOPUS_WIRE_VALUE_LEDGER=1` · `OCTOPUS_WIRE_KILL_SEAM=1`. فلگ‌های مهمِ خاموش: `OCTOPUS_WIRE_GOVERNOR` (عمداً بیرونِ PAPER_FULL_FLAGS)، `OCTOPUS_UNIFIED_CHAT=0` (ADR-040)، `OCTOPUS_WIRE_WLOS`.

---

## ۴) لایهٔ حاکمیت و ایمنی

- **نردبان استقلال L0–L3** + **نردبان ریسک چهاررنگ** (سبز=فقط‌خواندنی … قرمز=verdict انسانی؛ R4/R5 هرگز خودکار) — `06 - Architecture Maps/RISK-LADDER-2026-07-11.md`.
- **گیت‌های زنجیره‌ای:** `HALT-ALL` → `STOP-ORGANISM` → `capability_gate`/`arm_gate` → `live_gate_open` → HITL (پول/بیرونی/حذف/کد/secret → کارتِ approval به مالک) — `_ops/opslib.py`.
- **kill-switch‌ها:** `_ops/state/STOP-TG-HEARTBEAT`، `STOP-ORGANISM`، `/panic` `/halt` در تلگرام؛ halt drill فقط با پنجرهٔ انتخابیِ مالک (`04-SYSTEMS/HALT-DRILL-RUNBOOK-2026-08-16.md` — تمرین ۰۸-۲۳: همهٔ چک‌ها PASS، ولی live اجرا نشد).
- **بودجه:** سقف AU$30/ماه → «life-currency» (daily cap=1000، اولین تخصیص غیرصفر تاریخ در beat 42165 طبق `02-DECISIONS/ACTIVATION-REPORT-2026-08-20.md` §۲).
- **owner-auth:** `POST /api/actions` بدون توکن/initData معتبر → `403 owner_auth_required`. دور زدنش ممنوع.
- **مرزِ دائمی مالک (Blocked Forever):** اتوماسیونِ لاگینِ OnlyFans/Fansly · scraping · API مهندسی‌معکوس · auto-DM · mass messaging · cookie import — هم متن (`OCTOPUS-CURRENT-TRUTH` §Blocked Forever) هم کد (`_ops/agi2027_control/ops_actions.py::BLOCKED_PREFIXES`).

---

## ۵) سطح تلگرام — دو بات، سی جریان

| بات | توکن/نقش | مسیر |
|---|---|---|
| بات ۱ `@Robo2725_bot` | درونِ ارگانیسم: approval channel، خودترمیمی، کارت‌های سلامت | `_ops/budget/approval_channel.py` |
| بات ۲ `@intergrade2725_Bot` | رابطِ شخصیِ مالک: چت/فرمان/منوها | `_ops/telegram_center/center.py` (پروسهٔ جدا) |

نکته‌های ساختاریِ سنجیده‌شده (MASTER-ARCHITECTURE §۲):
- بات ۱ فیزیکاً **داخلِ گروهِ بات ۲** می‌نویسد (`approval_channel.py:1596-1602`).
- دستورهای ناشناختهٔ مرکز → پلِ یک‌طرفه به `approval_channel.handle_command` (عکسش نیست).
- **شکافِ شناخته‌شده:** `surface_policy.route()` سه سطل دارد؛ `heart`/`doctor`/`needs` در هیچ‌کدام نیستند ⇒ HOLD (روزی ۱۰۹ پیامِ محیطی نگه‌داشته‌شدند؛ تا ۰۸-۲۳ قفل‌های ارسال سخت‌تر شده‌اند).
- حلقهٔ بستهٔ تلگرام: A9–A17 PASS · **A18 Full Loop inbound هنوز BLOCKED** (canary باریکِ owner-chat ۰۸-۲۳ PASS — `06-EVIDENCE/OCTOPUS-A18-OWNER-CHAT-CANARY-2026-08-23/`) · A19 handoff صادر شد.
- **MiniApp cockpit:** ۸ تب (`index.html`)، رجیستری ۱۱ live/۵ staged/۱ unknown، gateway روی `127.0.0.1:8774`؛ URL عمومی منتشر نشده ⇒ منوی تلگرام `/ui` = `CONFIG_NEEDED` تا مالک `OCTOPUS_MINIAPP_URL` + `OCTOPUS_TG_MINIAPP=1` بدهد.

---

## ۶) حقیقت و حافظه

- **سه‌لایهٔ حقیقت:** `OCTOPUS/CURRENT-TRUTH.md` (بلوک autoِ runtime: coherence 0.95–0.98، beat ~47k، halted=False، members_present=11 که شمارِ «آگاهی» است نه فرایندِ OS) · `06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH.md` (سندِ lane) · `01-TRUTH/` (آینه/تناقض/گیت).
- **نقصِ شناخته‌شده (N-1):** دو خوانندهٔ `/truth` و `/api/current-truth` فایلِ ریشهٔ تاریخ‌دار `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` را hardcode کرده‌اند نه فایلِ vault — تا تعویض نشود، سندِ vault برای cockpit نامرئی است.
- **ژنوم-لجر:** `07 - Knowledge/genome-system/ledger/ledger.jsonl` — append-only + hash-chain؛ **۱۴٬۱۶۸ رکورد**، tip `b8a0da75…` (آخرین به‌روزرسانی 2026-08-23T21:34Z)؛ در 2026-07-31 به‌خاطر fork همروند (رکورد ۹۶۴۶) re-anchor شد.
- **رجیستری تناقض‌ها:** `01-TRUTH/CONTRADICTIONS.md` — C-001 تا C-053+؛ قاعده: هر دو مقدار ثبت می‌شوند، `likely` فقط با شواهد قوی، و هیچ تناقضی بدون رأیِ مالک «حل» نمی‌شود.

---

## ۷) خط زمانیِ شواهد (خلاصهٔ ۶ هفته)

| بازه | رویدادهای کلیدی |
|---|---|
| 07-09 → 07-29 | پایه‌گذاری؛ Waves 0–5؛ دو بات؛ doctor LIVE؛ کشف ۱۰۹ HOLD؛ `os_v1` بی‌صداکننده |
| 08-02 → 08-05 | سندهای lane (CURRENT-TRUTH/NEXT-ACTIONS)؛ تصادم‌های ۴-deploy روی `run_all.py` ⇒ WORKLOCK |
| 08-06 → 08-10 | مگاپرامپت‌های متوالی؛ آدیت‌های حافظه/تعرفه؛ deployment intervention |
| 08-11 → 08-12 | ADR-035 (APPLY روی همهٔ limbs)؛ golden trace 5/5؛ no-boundary rollout؛ Integration Wave A→H |
| 08-13 → 08-15 | ADR-039 (epistemics)؛ ADR-040 (conversation hub)؛ D1–D8 Desktop Lab؛ C-001..C-005 + رأی‌های مالک |
| 08-16 | EQUIP G1–G10؛ UNWIRED (اثرِ صفرِ مسیرهای قطع)؛ halt-drill/lease/launcher اسناد؛ errorhunt |
| 08-18 → 08-19 | AUDIT-191؛ RCPT/F3/D-B/CONTRADICTION_RADAR بسته؛ K=9 pilot (فرضیهٔ artifact **ابطال شد**)؛ WAR24 |
| 08-20 | Nervous Recovery + WAVE0/1؛ تلگرام Closed Loop A1–A19؛ T14–T51؛ امضای Ed25519؛ activation |
| 08-21 | WAVE1 authorized؛ ۱۶۳/۱۶۳ reproducible؛ SIG-IV؛ مگاپرامپت ۱–۳؛ ری‌استارت کنترل‌شده‌ی center (PASS) |
| 08-22 → 08-23 | Board2 سیزن (Ziman/OFN/Painting/Studio/Shopify)؛ OrangePi/LAN/ESP32؛ A18 canary PASS؛ MiniApp gateway LIVE؛ UPDATE-DEBUG-SWEEP T1–T8 PASS_WITH_FINDINGS؛ MCP hardening ضد DoS |

---

## ۸) وضعیت سلامت فعلی (جمع‌بندی شواهد ۰۸-۲۳/۲۴)

- 🟢 ارگانیسم و مغزها LIVE (پورت‌ها بالا، beat پیش می‌رود، coherence 0.98 در آخرین بلوک auto).
- 🟢 Halt-drill readiness: همهٔ چک‌ها PASS (فقط تمرین، نه اجرا).
- 🟢 UPDATE-DEBUG-SWEEP ۰۸-۲۳: PASS_WITH_FINDINGS — T1..T8 (حافظهٔ بایگانی‌شده، scheduler، lease، halt) رفع شد.
- 🟢 SESSION-HARVEST ۰۸-۲۱: ۳ حلقه بسته · ۳ contained · ۲ quarantined_uncertain · ۸ باز؛ نیازها ۱۲ (۹ خودحل‌شونده، ۳ منتظر مالک)؛ صفِ approval: ۲۰ claimِ معلق، ۰ پیشنهادِ تأییدنشده.
- 🟡 `governor.py` + تستش هنوز untracked (N-2) — ریسکِ `git clean`.
- 🟡 دو خوانندهٔ truth هنوز فایلِ ریشهٔ تاریخ‌دار را می‌خوانند (N-1).
- 🔴 Full Loop تلگرام (inbound) بسته نیست؛ SIG-IV منتظرِ ممیزِ مستقل؛ URL عمومی MiniApp + توکن/چتِ مالک منتظرِ مالک؛ Project-F بی‌credential BLOCKED.
- 🔴 درختِ کاری: **۹۰۱ فایل modified/untracked** در برنچِ `rescue/octopus-live-tree-20260821` (بزرگ‌ترین دسته: 00 - Inbox و 06-EVIDENCE و 07 - Knowledge — عمدتاً رسیدهای laneها).

---

## ۹) ریسک‌ها و گیت‌های باز

- `06 - Architecture Maps/OCTOPUS-KNOWN-RISKS.md`: R-01..R-16 — اکثراً mitigated؛ بازِ مهم: R-03 (باتِ تلگرام stub→fail-closed)، R-14 (credentialها)، R-15 (rollback دستی)، R-12 (رشد ideas).
- `06-RISKS/OPEN-GATES.md` (آخرین نسل ۰۸-۱۹): D-B/V4 در صفِ مالک؛ `LIVE4_PRIMARY_V2` نتیجهٔ منفیِ معتبر (نرخ برد 59%، خوانایی داور در batch 73%) — گزارش و گزینه‌ها نزد مالک.
- تناقض‌های C-042..C-053 عمدتاً بسته/سنجیده شدند (میلی‌گرد کردن، دورهٔ دوگانه، رنگ‌های خالی).

---

## ۱۰) سیستم‌های جانبی

| سیستم | چیستی | وضعیت |
|---|---|---|
| **OCTOPUS-DOCTOR** | والتِ Obsidianِ جدا + ماژول پایتونِ stdlib-خالص (چشم `scanner` · ذهن `mind` · مغز `fugu` · انگشت `propose` · صدا `channel` · حلقه `daemon`)؛ ۱۵۷/۱۵۷ تست | 🟢 LIVE؛ در `_ops` نمی‌نویسد؛ پچ اعمال نمی‌کند؛ outbox-mode؛ تسک روزانه ۰۷:۰۰ |
| **OCTOPUS-PRIME** | phase-0: barrier-review ها، C-AUDIT، CHRONO-MIGRATION، port-plans | 🟡 در حال کار |
| **4d_system + 4D-Vault** | مغزِ پژوهشِ مستقل (SOG، هندسهٔ ابعاد، مولتی‌ایجنت)؛ daemonِ خودش؛ حافظه‌اش سالم (jobs/read ratio 1.0، recall 91 رویداد) | 🟢 به‌صورت مستقل؛ **به ارگانیسم وصل نیست** |
| **NBB-Control-Plane** | دوقلوی حاکم (۱۷۱ تست، ۱۲ invariant) | 🟢 در `03 - Projects/` |
| **WLOS** | پروژهٔ کاهش وزن با ۱۰ پکیج (fugu-provider اشتباهاً «دروازهٔ مدل» خوانده می‌شود — نیست؛ پلِ واقعی `_ops/cortex/wlos_bridge.py` پشت فلگِ خاموش) | 🟡 مستقل |
| **پاها (legs)** | Accounting (بدون حسابدار) · Lead-نقاشی (درآمد اصلی) · Mining · Crypto-eToro · Ziman Galerry · Project-F/اونلی‌فنز (GATE 0) · Chord · VibeGuard · research-spec-compiler · OFN-Board | مخلوط؛ اکثراً read-only/propose-only |
| **ایجنت‌ها** | رجیستری (`05 - Agents/AGENT_REGISTRY.md`) — همهٔ ردیف‌ها وارث Security Gate؛ Research Scout Fleet + Vault Cartographer (limb) زنده | 🟢 |

---

## ۱۱) قواعد خانه (برای هر ایجنت/لین)

- **WORKLOCK** (`01 - Dashboard/HANDOFF.md`): فایل‌های همیشه‌رزرو: `_ops/tests/run_all.py` (ثبتِ تست مرکزی)، `_ops/wiring.py`، `_ops/telegram_center/center.py`، `_ops/orphan_scan.py`. سندِ نو در `06`/`07`/`00` همیشه امنِ موازی است.
- `F:\backup` **درختِ زندهٔ در حال اجراست** — laneها فقط داخلِ worktree بنویسند.
- تستِ pytest-style ممنوع؛ شکلِ مستقیم‌اجرای صفر-assert بی‌صدا سبز شمرده می‌شود (الگو: `test_tg_poll_health.py`).
- هرگز حذف نکن؛ منتقل کن (`_Archive`/`_Duplicates`).
- `.cmd`/`.bat` را با ابزارِ متنی ویرایش نکن (CRLF).
- گزارشِ بین‌گرهی بدون Evidence Envelope خام قبول نیست (نوت ۶۶).
- منبعِ حقیقت: کدِ زنده > STATE > مگاپرامپت (نوت ۰۱ §تقدمِ منابع).

---

## ۱۲) ابعادِ ناشناخته/صادقانه (محدودهٔ منفیِ همین تحقیق)

- محتوای `_ops/legs/` (مرزِ عمدی)، secrets/`.env`، `_Archive`/`_Duplicates`، و هویتِ Project-F خوانده/لمس نشد — طبق قواعد خودِ سیستم.
- رفتارِ زندهٔ HTTP روی پورتِ واقعی و Telegramِ زنده (ارسال واقعی) سنجیده نشد — فقط شواهدِ روی دیسک.
- شمارِ دقیقِ تستِ کلِ repo از اجرای زنده‌ی `run_all.py` (۴۹۲+ فایل تست) بازاجرا نشد؛ اعداد از مستندات/رسیدها نقل شدند.
- وضعیتِ گیت ۹۰۱ فایلِ آلوده، مربوط به laneهای موازیِ جاری است؛ نه فرایندِ این تحقیق.

---

## ۱۳) جمع‌بندی در یک نگاه

> **اختاپوس یک ارگانیسمِ واقعاً زنده و گیت‌محور است** که حدودِ ایمنی‌اش (fail-closed، owner-verdict، budget cap، kill-switch) سخت‌تر از هر ادعای marketing ای اجرا می‌شود — با شواهدِ دیسکی. مغز، قلب، بودجه، دکتر، مینی‌اپ و دو بات تلگرام همگی LIVE‌اند؛ حلقهٔ بستهٔ کاملِ تلگرام (inbound) هنوز باز است؛ `governor.py` تنها مؤلفه‌ی مهمِ بی‌گیت است؛ و صفِ مالک شامل URL عمومی مینی‌اپ، توکن‌ها، Wave-2 CRM و credentialهای Project-F است. فرهنگِ مستندسازی (رسید→کامیت→evidence) در کل درخت یکدست و جدی است — این بزرگ‌ترین داراییِ سیستم است.

<!-- EOF -->
