# 🐙 ساختار کامل ربات اختاپوس — رییس + پاها (نقشهٔ یکپارچه)

> تاریخ سنتز: 2026-07-11
> منبع «رییس» (F:\backup) از این‌ها بازسازی شده: گزارش `نقشه اختاپوس/vault-report.md`
> (اسکن 2026-07-11)، `SYSTEM-PROMPT.md`، و ضمیمه‌های مالک (Domains Status / Brain /
> Home / CONTROL-PANEL / SYSTEM-DASHBOARD / BRAIN-FOCUS-BOARD / HANDOFF).
>
> ⚠️ **محدودیت دسترسی:** من فقط به `C:\Users\Armin\Desktop` دسترسی دارم.
> درایو `F:` بیرون از دسترس من است → هرچه دربارهٔ «رییس» می‌گویم **بازسازی از
> گزارش‌ها و ضمیمه‌هاست، نه خواندن مستقیم زندهٔ F:.**

---

## ۰. دو درخت (این نکته پایه است)

| درخت | چیست | اندازه | نقش |
|---|---|---|---|
| **F:\backup** | vault زندهٔ «رییس» (مادر/Architect + ارگانیسم `_ops`) | 7235 فایل · 535.7MB · ۳۶ آیتم top-level | مغزِ حاکم و همیشه‌روشن |
| **C:\…\پازل هشت پا** (دسکتاپ) | ورک‌اسپیس تمیزِ جعبه‌سیاه (۸ پا + ۲ مغز + ۱ ابزار) | ~۷۶MB | export قراردادی برای کار مرحله‌به‌مرحله |

**رابطه:** دسکتاپ = «پاها»یِ قراردادی‌شده؛ F:\backup = «رییس» که آن‌ها را حکمرانی می‌کند.
تصویر ارسالی مالک دقیقاً ریشهٔ F:\backup را نشان می‌دهد (۳۶ آیتم، منطبق با vault-report).

---

## ۱. رییس = ارگانیسم `_ops` («Project Octopus»)

قلبِ حکمرانی. یک سیستم خودبهبودِ همیشه‌روشن. لایه‌ها (از HANDOFF + SYSTEM-PROMPT):

```
                    ┌───────────────── مالک (آری) ─────────────────┐
                    │        تلگرام: کاکپیت + verdict + kill        │
                    └───────────────────────┬──────────────────────┘
                                            │ (فقط انسان)
        ┌───────────────────────────────────────────────────────────────┐
        │  organism.py  — حلقهٔ متابولیسمِ همیشه‌روشن + HTTP :8771/:8773  │
        │               (داشبورد /ops، run_cycle)                        │
        └───┬───────────────┬───────────────┬───────────────┬───────────┘
            │               │               │               │
   ┌────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼────────┐
   │ 🧠 cortex/     │ │ ❤️ heart/    │ │ 💰 budget/   │ │ 🧬 epistemics/ │
   │ (مغز/تصمیم)    │ │ (ضربان)      │ │ (پول/گاورنر) │ │ (fact/hype)    │
   └───────────────┘ └─────────────┘ └─────────────┘ └───────────────┘
   ignition(WTA)      control_law      governor_epoch   label+guard
   stress             producers(Gate0) organ_gate       hash-chain
   innervation        heartstate       fitness          guard_review
   self_model         replay_s         telemetry
   synthesis          doctor_setpoint  needs_digest
   goal_directed                       replication
   part_loops(۷بخش)
   auto_approve       ┌──────────────┐ ┌─────────────┐ ┌───────────────┐
   web_research       │ 🦿 neural/    │ │ 📡 events.py │ │ 🩺 governor/   │
   business_brain     │ consolidation │ │ 7 event type │ │ (watcher)      │
                      │ hebbian       │ │ +Envelope    │ │ governor-      │
                      │ latent_space  │ │ +Incident    │ │ alerts.md      │
                      │ nociceptor    │ └─────────────┘ │ (۴۷ خطای خطا)  │
                      └──────────────┘                  └───────────────┘

   ابزارها: chrono.py (HLC/EffectorGate) · vault_updater(+gate) (patch propose-only)
            registry_scan.py (URCP Phase-0، ۱۳ موجودیت) · state/ (ORGANISM-STATE,
            fitness-latest, ledger=ژنوم, pulse) · survival-gateway (Docker/LiteLLM)
```

### نقش‌ها طبق تاکسونومیِ خودِ سیستم (SYSTEM-PROMPT §3)
| نقش | معنی | نمونه در `_ops` |
|---|---|---|
| **Brain** (تصمیم) | تصمیم و مسیریابی | `cortex/`, `organism.py` |
| **Memory** (حافظه) | ذخیره | `_memory/`, `07 - Knowledge/`, `state/ledger` |
| **Arm** (اجرا) | کارِ اجرایی | `_ops/legs/`, رباتِ پروژه‌ها, scannerها |
| **Watcher** (ناظر) | رصد و هشدار | `governor/`, `neural/nociceptor.py`, incident log |

---

## ۲. لایهٔ حکمرانی (روی همهٔ پاها اعمال می‌شود)

- **Autonomy Ladder L0–L3** (منشور استقلال، ratified 2026-07-05).
- **Risk Ladder چهاررنگ** سبز/زرد/نارنجی/قرمز + **کانال حیاتی** (RISK-LADDER-2026-07-11).
  - سبز = فقط خواندن/گزارش/فایل نو · زرد = اجرای مستقیم + لاگ + rollback-note ·
    نارنجی/قرمز = verdict انسانی · R4/R5 هرگز خودکار.
- **propose-only** به‌صورت پیش‌فرض؛ هر اکشن بیرونی/پول = verdict انسانی.
- **kill-switch**ها + سقف بودجه (AU$30/ماه؛ گیت پول).
- **Gate-0 قلب = ۲۹/۴۸** (خطِ live قلب پشتِ ۴ دروازهٔ مالک بسته).
- **URCP Registry** (owner/risk_tier برای هر موجودیت) — «چیزی که نمی‌بینی را نمی‌توانی حکمرانی کنی».

---

## ۳. ساختار vault رییس (۳۶ آیتم top-level — از تصویر + vault-report)

| بخش | نقش | فایل/حجم | وضعیت |
|---|---|---|---|
| `00 - Inbox` | ورودی خام + AGENT_QUESTIONS + scout-digests | 180 · 2.1MB | 🟡 شلوغ (۷۶ فایل پراکنده) |
| `01 - Dashboard` | Home · Brain · HANDOFF · CONTROL-PANEL | 10 · 375KB | 🟢 |
| `02 - Life OS` | سیستم زندگی | 2 | 🟡 stub خالی |
| `03 - Projects` | ۸ پروژه (پاها) | 397 · 170.9MB | 🟢 |
| `04 - Architect System` | لایهٔ مادر + build-prompts + MYCELIAL-MASTER-SPEC | 191 · 3.8MB | 🟡 شلوغ |
| `05 - Agents` | AGENT_REGISTRY · Research Scout Fleet | 6 | 🟢 |
| `06 - Architecture Maps` | ECOSYSTEM · ADRها · URCP · RISK-LADDER | 16 | 🟢 |
| `07 - Knowledge` | دانش + genome-system + هیپنوتیزم + Time-Arch | 128 · 5.3MB | 🟢 |
| `08 - Assets` | عکس/مدیا (Telegram/WhatsApp) | 633 · 88.4MB | 🟢 |
| `09 - People` | افراد | 1 | 🟡 stub خالی |
| `10 - Telegram processing` | SOP · ROUTING | 4 | 🟢 |
| `_ops` | **ارگانیسم زنده (رییس واقعی)** | 459 · 7.5MB | 🟡 شلوغ + ۴۷ خطای گاورنر |
| `_memory` | حافظهٔ ماندگار + HEARTBEAT + EXPERIENCE-LEDGER | 13 | 🟢 |
| `_launchpad` | پایپ‌لاین زندهٔ ربات‌ها (ziman-live و…) | 55 | 🟢 |
| `_code` | آینهٔ کد قدیمی پروژه‌ها | 73 · 3.2MB | 🟡 احتمالاً کهنه |
| `_Templates` | قالب نوت | 9 | 🟢 |
| `_Archive` / `_Duplicates` | فقط مقصد انتقال | 2 / 76 | 🟢 |
| `CHRONOS-FABLE-OS` | لایهٔ تئوری/معماری | 37 | 🟢 |
| `survival-gateway` | Docker/LiteLLM gateway | 14 | 🟢 |
| `.env` | 🔴 secrets | — | 🔴 ASK OWNER |
| `.git` | تاریخچه | 4830 · 229.6MB | 🟢 |
| فایل‌های ریشه | ROTATION_CHECKLIST · Octopus_Heart_Design · MycoCardium · Evolutionary-Doctor… | — | 🟡 پراکنده در ریشه |

---

## ۴. هشت دامنه (ادغام مستقیم Domains Status.md) + نگاشت به پا و رییس

| دامنه | status | risk | autonomy | بلاکر اصلی (Domains Status) | پایِ دسکتاپ | ارگانِ رییس |
|---|---|---|---|---|---|---|
| **Accounting** | active | high | read-only ⛔ | رجیستر انطباق خالی؛ حسابدار ندارد | `03 - Projects/Accounting` | business_brain (مالی) |
| **Lead-نقاشی** | active | medium | read-only ⛔ | rotation کلیدها؛ آزمایش #۱ | `03 - Projects/Lead-نقاشی` | business_brain (🎯 lead، درآمد واقعی) |
| **Mining** | active | medium | read-only ⛔ | چرخش wallet؛ رجیستری نودها خالی | `03 - Projects/Mining` | fleet/legs |
| **Crypto-etoro** | active | **critical** | read-only ⛔ | کلیدهای exchange؛ رجیستری خالی | `03 - Projects/Crypto - etoro` | legs + alert |
| **Ziman** | active | low | read-only ⛔ | عدد ظرفیت ثبت نشده | `03 - Projects/Ziman Galerry` | `_launchpad/ziman-live` |
| **Project-F** 🔒 | active | high | read-only ⛔ | Track A/B/C؛ مرز body باز | `03 - Projects/اونلی فنز` | business_brain (🎬 content-free) |
| **architect** | active | **critical** | read-only ⛔ | TOP-5 آدیت؛ گیت بسته | `04 - Architect System` | خودِ رییس/`_ops` |
| **هیپنوتیزم** | active | low | read-only | بازبینی برچسب‌های epistemic | `07 - Knowledge/هیپنوتیزم` | Knowledge/Memory |

**⛔ = Security Gate:** طبق Domains Status همه read-only تا چرخش ۴ ردیف CRITICAL در ROTATION_CHECKLIST.

> نکتهٔ دامنهٔ نهم: `Home.md` و `Brain.md` یک دامنهٔ نهم هم دارند —
> **Time-Architecture** (`07 - Knowledge`) — که در Domains Status.md (که قدیمی‌تر است)
> هنوز نیامده. پس «۸ دامنه» عدد رسمیِ Domains Status است، ولی نقشهٔ زنده ۹ حوزه دارد.

---

## ۵. اتصال پا ↔ رییس (چطور به هم وصل‌اند)

1. **قرارداد:** هر پا روی دسکتاپ `MANIFEST.yaml` + `contracts/adapter.yaml` دارد.
2. **کشف:** `_ops/registry_scan.py` فرانت‌مترِ `03 - Projects/*/PROJECT.md` را می‌خواند →
   owner/risk_tier (۱۳ موجودیت؛ Crypto-etoro زرد=R4-pending).
3. **رصد:** `cortex/business_brain.py` سیگنالِ واقعی دو کسب‌وکار (Lead + Project-F
   content-free) را می‌خواند؛ `Brain.md` هر ۳ ساعت وضعیت زنده می‌سازد.
4. **دوقلوی حاکم:** روی دسکتاپ، `app/` = **NBB-CP** (control-plane سخت‌شده، ۲۰۷ تست).
   این طراحی‌شده که همان نقشِ `_ops/governor`+`cortex` را با ۱۲ invariant ایفا کند.
   ⚠️ **عدم‌قطعیت:** رابطهٔ دقیقِ NBB-CP (دسکتاپ) با `_ops` زندهٔ F: هنوز سیم‌کشی‌نشده —
   دو پیاده‌سازیِ هم‌دکترین‌اند، نه یک کد واحد.

---

## ۶. ⚠️ تناقض‌ها و عدم‌قطعیت‌ها (باید مالک تعیین‌تکلیف کند)

1. **Security Gate — تناقض تاریخ‌ها:**
   - `Domains Status.md` (2026-07-03): بسته ⛔، ۴ CRITICAL باز.
   - `SYSTEM-DASHBOARD.html` (07-05): بسته، rotation_critical_open=4.
   - `CONTROL-PANEL.html` (07-05): بسته، 4.
   - `Brain.md` (07-06) + `BRAIN-FOCUS-BOARD` (07-06): **LIFTED**، rotation_critical_open=0.
   → **منبع حقیقتِ فعلی = Brain.md/07-06 (LIFTED)**؛ بقیه snapshotهای قدیمی‌ترند.
2. **ناوگان تاریک (fleet dark):** طبق Brain.md همهٔ تسک‌های تکرارشونده self-disable شدند
   (fireAt یک‌باره به‌جای cron) → «re-arm» منتظر verdict مالک.
3. **گاورنر ۴۷ خطا:** `price_in/price_out در budgets.yaml قفل نشده` + `debate KeyError:'text'`
   (از vault-report). = پول‌مسیر معیوب تا قفلِ قیمت با verdict.
4. **دسترسی من به F::** ندارم → این نقشه بازسازی است، نه اسکن زندهٔ امروز.
5. **کهنگی Domains Status.md:** تاریخ 2026-07-03؛ نسبت به HANDOFF (07-11) خیلی عقب است.
6. **شمار «۸ مغز»:** dashboardها گاهی brushline را جدا و paused می‌شمارند و گاهی
   Time-Architecture را نمی‌آورند → عدد ۸ بسته به منبع فرق دارد.

---

## ۷. یک‌خطی

> **رییس = ارگانیسمِ `_ops` در F:\backup** (organism.py + cortex + heart + budget +
> epistemics + neural + events + governor)، زیرِ حکمرانیِ Autonomy/Risk Ladder و
> تلگرامِ مالک؛ **پاها = ۸ (عملاً ۹) دامنهٔ `03 - Projects`/`07 - Knowledge`** که با
> MANIFEST/adapter قراردادی و با registry_scan به رییس وصل‌اند. همه فعلاً read-only /
> propose-only تا دروازه‌ها با verdict مالک باز شوند.
