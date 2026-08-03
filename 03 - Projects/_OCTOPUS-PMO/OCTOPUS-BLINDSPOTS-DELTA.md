# Octopus — نقاط کورِ جدید (DELTA: ۱۰۱–۱۳۰) + تصحیح‌های حیاتی

> اسکن گسترش‌یافته، ۲۰۲۶-۰۷-۲۷. مکملِ `OCTOPUS-BLINDSPOTS-100.md`.
> این سند حاصلِ ۴ اسکن موازیِ عمیق روی: (الف) پروژهٔ اونلی فنز به‌عنوان یک کل، (ب) تمام اتصالاتش به اختاپوس، (ج) نمایش/تعامل تو تلگرام، (د) مغزهای خارجی و ژنوم.
> **یک ایجنت (نقشهٔ سیم‌کشی) سقوط کرد** به‌خاطر سرریز context — یعنی نقشهٔ کاملِ سیم‌کشی هنوز ناقصه و اولویتِ پرامپتِ بعدیه.

---

## بخش ۰ — تصحیح‌های حیاتی (خطاهای لیست ۱۰۰تایی)

| # | آنچه در لیست ۱۰۰ گفتیم | واقعیتِ اسکن عمیق | منبع |
|---|---|---|---|
| C1 | «اونلی فنز» = business نقاشی | ❌ **creator-economy faceless feet-only (سبک OnlyFans، غیرصریح)**. فاز validation، صفر اجرا، گیت GATE-0 باز (blocker). | `PROJECT-F-CONTROL-MANIFEST.json:8-14` |
| C2 | lead-naghshi ≈ اونلی فنز | ❌ دو چیزِ متفاوت. lead-naghshi یک **پای نقاشیِ مستقل** در `_ops/legs/` است. اونلی فنز (Project-F) یک پروژهٔ دیگر. اختاپوس **چند-بیزینسی** است. | `_ops/legs/lead_scorer.py` vs `03 - Projects/اونلی فنز/` |
| C3 | «یک بات تلگرام» / نمایش تلگرام ناشناخته | ❌ **دو بات زندهٔ همزمان**: بات #۱ `approval_channel.py` (~۴۳۰۰ خط، صفحهٔ فرماندهی/پول واقعی) + بات #۲ `telegram_center/center.py` (هاب/نمایش). ۷ بات دیگر dormant. | `_ops/BOTS-REGISTRY.md` |
| C4 | pf_os کاملاً shadow/dormant | ⚠️ از ۲۰۲۶-۰۷-۲۵ **spine + cortex روشن** (`OCTOPUS_WIRE_PROJECTF_SPINE=1` در `run-langar.bat:18-19`). نیمه‌زنده. | `run-langar.bat`، `orchestrator.py:288-293` |
| C5 | هیچ اتصال مستقیمی بین PF و _ops نیست (در لیست ۱۰۰) | ❌ **پنج لایهٔ اتصال**: file-bridge، event-mirror، neural-import، cortex-router، STOP-walkup. همه یک‌طرفه (PF→octopus). | §۲ زیر |
| C6 | second-brain یک مغز فعال | ❌ **DEPRECATED ۲۰۲۶-۰۷-۱۸** (`DEPRECATED.md`). core.db ۳۲KB، آخرین نوشته ژوئیهٔ ۶. ولی brain_core parity هنوز بهش ارجاع می‌دهد. | `_launchpad/second-brain-live/control-brain/DEPRECATED.md` |
| C7 | منبعِ ژنوم نامشخص | ✅ `07 - Knowledge/genome-system/` — ledger.jsonl (۱۹۵۸ ورودی، hash-chain)، values.yaml. قراردادِ genome→behavior هنوز بسته‌نشده (سوال باز). | `genome-system/README.md`، `ledger.py` |

---

## بخش ۱ — نقاط کورِ جدید (آیتم ۱۰۱–۱۳۰)

### ۱.الف — معماری تلگرامِ ناشناخته (۱۰۱–۱۰۸)

۱۰۱. **دو بات همزمان poll می‌کنند** — ریسکِ ۴۰۹ Conflict (سندِ غالبِ خرابی). بات #۱ token مشترک با باتِ بازنشستهٔ `control-brain` داشت. `BOTS-REGISTRY.md:100-108`.
۱۰۲. **۹ بات در registry**، فقط ۲ زنده. بقیه بدون token یا بدون مصرف‌کننده. زدنِ اشتباهِ آن‌ها = ۴۰۹ یا بی‌اثری. `BOTS-REGISTRY.md:17-23`.
۱۰۳. **`approval_channel.py` (~۴۳۰۰ خط) زیراسکن‌نرفته** — تنها مسیرِ settle پول، و کلِ صفحهٔ فرماندهی. بزرگ‌ترین گودالِ ناشناخته.
۱۰۴. **`pending_card_recovery.py`** — تأییدِ callbackِ مقاوم + بازصدورِ کارت در بوت. مرکزِ مدلِ امنیتیِ verdictِ پول. زیراسکن‌نرفته.
۱۰۵. **`cockpit_readmodel.py::redact()`** — هر خروجیِ بات #۱ از این می‌گذرد. اگر fail-open بشه، PII نشت می‌کند. حساس‌ترین مهرهٔ OPESEC.
۱۰۶. **`autonomy_matrix.py`** — gate دفاع-در-عمق که `llm_intent` دوباره چک می‌کند. مدلِ کاملِ «چه کاری autonomous/propose-only/human-gated است» زیراسکن‌نرفته.
۱۰۷. **`instant_alert_bridge.py`** — مسیرِ «همین حالا» (۳ سیگنال: fear، c6_new، card_debt). **default-off** → موجودی بین beatها کاملاً خاموشه.
۱۰۸. **HMAC `callback_token.py` + سقفِ ۶۴ بایت** — تنشِ امنیت/عملکرد. یک کارتِ C6 واقعاً ۲۴ ساعت گم شد (۷۵ بایت، Telegram کل sendMessage را 400 کرد، استثنا بلعیده شد).

### ۱.ب — اتصالاتِ ناشناختهٔ اونلی فنز ↔ اختاپوس (۱۰۹–۱۱۵)

۱۰۹. **پنج لایهٔ اتصال**، همه یک‌طرفه (PF→octopus): (۱) file-bridge `saba-bridge.jsonl`، (۲) event-mirror به `_ops/state/events.jsonl`، (۳) neural-import در `orchestrator.py`، (۴) cortex-router HTTP `127.0.0.1:8772`، (۵) STOP-file walkup.
۱۱۰. **مصرف‌کنندهٔ bridge وصل نیست.** `pf_os/bridge_beat.py` وجود داره ولی `wiring.py`/`organism.py` در octopus هنوز `saba_bridge_beat()` را صدا نمی‌زنند. پل می‌سازد، کسی عبور نمی‌کند. docstring: «ready for integration — needs one line».
۱۱۱. **دو دایرکتوریِ سرگردانِ `F:backup/_ops/state/`** (PUA-escaped مسیر) — اثرِ باگِ مسیر نسبی، اکنون fix شده در `config.py:31-48`. ولی فایل‌های event.jsonl خالی سرگردان ماندند.
۱۱۲. **Compliance gate fail-closed** — اگر manifest مفقود/خراب باشد، کلِ tickها بلاک. خوب برای ایمنی، بد برای رزلیانس. `orchestrator.py:111-153`.
۱۱۳. **orchestrator فقط با vault کامل کار می‌کند** — `_ops/neural/*` import می‌کند، اگر نباشد stub no-op. standalone نیست.
۱۱۴. **cortex HTTP در `8772`** — augmention مغز. فقط اعدادِ abstract (بدون PII). `cortex_augmented.py:68-86`.
۱۱۵. **هیچ مسیرِ برگشت (octopus→PF) نیست** — verdictها، spawnها، یادگیریِ organism به‌طور خودکار به رفتارِ PF برنمی‌گردد. PF یک سنسورِ یک‌طرفهٔ اختاپوس است.

### ۱.ج — مغزهای خارجیِ نیمه‌مرده (۱۱۶–۱۲۱)

۱۱۶. **second-brain DEAD** ولی parity هنوز صفر را باهاش مقایسه می‌کند. مغازب: یک سیم به یک جسد. `_launchpad/second-brain-live/control-brain/DEPRECATED.md`.
۱۱۷. **ژنوم ۱۹۵۸ ورودی، hash-chain فعال** — ولی قراردادِ «درسِ آموخته → ورودیِ ژنوم → تأثیر بر رفتار» بسته‌نشده. genome write-only است.
۱۱۸. **romajan claims (۱۷+۲۷ تأییدشده)** در `F:\romajan\` (بیرون از repo!) از طریق `romajan_bridge.py` به C6 می‌رسند. یک منبعِ یادگیریِ خارجی که کم‌نقشه‌بوده.
۱۱۹. **منابعِ consolidation افتاده‌اند** — `acquisition` و `doctor_archive` از consolidation حذف شدند؛ `school_awareness` باقی‌مانده با مقادیر استاتیک. «سوختِ یادگیری فعلاً قطعه».
۱۲۰. **self-model.json (۱۵۷KB، ۳۱۸ ماژول)** هر beat بازنویسی می‌شود. خودآگاهیِ فایل‌محور. churn بالا، ریسکِ خرابیِ وسطِ write.
۱۲۱. **PocketSmith/ING disabled** — `pocketsmith_api.py`/`txn_store.py` موجوده ولی وصل نیست. دادهٔ مالیِ واقعی در دسترس ولی استفاده نمی‌شود.

### ۱.د — لایهٔ مغز/یادگیریِ Project-F (۱۲۲–۱۲۸)

۱۲۲. **`dual_brain_v3.py` ۱۰ sub-agent** (Strategist، Pricer، Scheduler، ...) — «مغزِ گرانِ» سمتِ PF. زیراسکن‌نرفته.
۱۲۳. **`brain/learning.py` ThompsonBandit** — یک یادگیرندهٔ واقعی (نمونه‌گیریِ تامپسون)، جدا از BCM خواب‌شده. این سوختِ یادگیریِ واقعیه که نادیده گرفته شده.
۱۲۴. **`brain/store.py` (FanDB/VaultBank/OctopusState)** — لایهٔ ماندگاریِ PF. زیراسکن‌نرفته.
۱۲۵. **`eval_loop.py` loop را می‌بندد با MockSource** — آمادهٔ دادهٔ واقعی ولی هرگز swap نشده. Goodhart-trap tag در MockSource هوشمندانه.
۱۲۶. **`pf_os/actuator.py:169` `raise NotImplementedError`** — live adapters عمداً ساخته‌نشدند. حتی اگر همهٔ گیت‌ها باز شوند، اجرا نمی‌شود. طراحیِ fail-closed.
۱۲۷. **دو کلید (دو-کلیده)** برای هر draft — C ثبت، A تأیید. publish دستی. صفر auto-post.
۱۲۸. **`hebb_orch.json` (سمتِ PF)** ۴ جفتِ saturated — و `hebbian.json` (سمتِ octopus) ۱ جفت. دو مغزِ hebbian جدا، هیچ‌کدام کامل.

### ۱.ه — ایمنی/استقرارِ نقاط کورِ جدید (۱۲۹–۱۳۰)

۱۲۹. **هیچ alertی وقتی بات #۲ (center) خاموش می‌شود نیست** — `RUN-TG-CENTER.bat` loop می‌زند، ولی اگر center.py با «not wired» خارج شود، bat بی‌صدا هیچ‌کاری نمی‌کند. مرکزِ تاریک، بدون آگاهیِ مالک.
۱۳۰. **دو `.bat` مسیرِ hardcoded** (`F:\backup\03 - Projects\اونلی فنز`) — خطرِ جابجایی. همه‌چیزِ portability را می‌شکند.

---

## بخش ۲ — پنج لایهٔ اتصال (مرجع)

```
اونلی فنز (Project-F)                              اختاپوس (_ops/)
─────────────────────────                          ──────────────────
pf_os/bridge.py ───(1)──► _ops/state/saba-bridge.jsonl      [consumed? NO]
pf_os/events.py ───(2)──► _ops/state/events.jsonl           [consumed? YES]
orchestrator.py  ───(3)──► import _ops/neural/*             [stub fallback]
pf_os/cortex_client ─(4)──► HTTP 127.0.0.1:8772/ask         [flag-gated]
langar/studio    ───(5)──► _ops/STOP-ORGANISM walkup        [kill-switch]

    ⟵ هیچ مسیرِ برگشتی نیست (octopus → PF فقط دستی، از طریق مالک) ⟶
```

---

## بخش ۳ — سوختِ جدید برای پرامپتِ عمیق‌تر

این نقاط کورِ جدید، سوال‌هایِ عمیق‌تری باز می‌کنند که پرامپتِ بعدی باید جواب دهد:

- آیا genome→behavior loop واقعاً بسته است؟ (آیتم ۱۱۷)
- آیا bridge واقعاً مصرف می‌شود؟ (آیتم ۱۱۰)
- مدلِ کاملِ autonomy_matrix چیست؟ (آیتم ۱۰۶)
- مسیرِ settleِ پول از click تا ledger چه‌قدر مقاوم است؟ (آیتم ۱۰۳، ۱۰۴)
- آیا ThompsonBandit سمتِ PF می‌تواند BCM خواب‌شده را بیدار کند؟ (آیتم ۱۲۳)
- ۹-بات topology: کدام‌ها در استقرارِ واقعی ۴۰۹ می‌سازند؟ (آیتم ۱۰۲)
- نقشهٔ کاملِ سیم‌کشی (که ایجنتِ آن سقوط کرد) — اولویتِ یک.
