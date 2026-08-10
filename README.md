# 🐙 پازل هشت‌پا — نقشهٔ قلب مشترک (Shared Heart)

> **یک میز کارِ ساختاری** که چهار ارگان اصلی را کنار هم گذاشته تا با هم بیدار شوند:
> ۶ پا (پروژه‌های کسب‌وکار) + ۲ مغز (سیستم‌های ایجنت) + ۱ ابزار تشخیص.
>
> هر پوشه یک **جعبهٔ سیاه مولتی‌ایجنتی** است با `MANIFEST.yaml` (قرارداد ماشین‌خوان) +
> `contracts/adapter.yaml` (رابط read-only API) + `README.md` (نقشهٔ ایجنت).

---

## 🗺️ نقشهٔ ارگانیسم (برون‌نگر)

```
                        ┌─────────────────────────────────┐
                        │     مغز مادر (ABSENT اینجا)      │
                        │  langar / 04-Architect System    │
                        │  _ops / ROTATION_CHECKLIST       │
                        │  → در F:\backup (کانونیکال)       │
                        └──────────────┬──────────────────┘
                                       │ (dangling — گیت بسته)
            ┌──────────────────────────┼──────────────────────┐
            │                          │                      │
   ┌────────▼────────┐    ┌───────────▼───────────┐  ┌───────▼────────┐
   │  ۶ پا (پروژه)    │    │  ۲ مغز مستقل          │  │  ۱ ابزار        │
   │  03 - Projects/  │    │  4d_system/ (پژوهش)   │  │  نقشه اختاپوس/  │
   │                  │    │  app/ (NBB-CP حاکم)   │  │  (تشخیص)        │
   └────────┬─────────┘    └───────────────────────┘  └────────────────┘
            │
   ┌────────┴────────┬──────────┬──────────┬──────────┬──────────┐
   │                 │          │          │          │          │
 Account-          Lead-      Mining    Crypto-    Ziman     Project-F
 ing               نقاشی      ⛏️        eToro      🌸        👣
 💰 قلب مالی        🎨 درآمد   🔬 پژوهش   📈 حسگر    🎁 هدیه    👣 creator
                   اصلی
```

---

## 📦 هر جعبهٔ سیاه در یک نگاه

| پا/مغز | نقش | بلوغ | جعبهٔ سیاه زنده؟ | بلاکر اصلی |
|---|---|---|---|---|
| **💰 Accounting** | قلب مالی | manifest کامل، اجرا صفر | ❌ طراحی شد، کد در `_code/` | حسابدار انتخاب نشده |
| **🎨 Lead-نقاشی** | درآمد اصلی | Brushline ۸/۹، کاریابی ۳۳ تست | ✅ کد موجود در `_code/` | rotation کلیدها |
| **⛏️ Mining** | پژوهش + ناوگان | پژوهش کامل، اجرا صفر | 🟡 کد در `_code/` | seed rotation + وضعیت نودها |
| **📈 Crypto-eToro** | حسگر/tenant | معماری کامل، NO_ACTION | 🟡 کد در `_code/` | EdgeClassifier bug + keys |
| **🌸 Ziman** | هدیه/تجارت | control-brain ۲۱ تست | ✅ کد در `_code/` | ظرفیت + عکس محصول |
| **👣 Project-F** | creator brand | brain+langar+studio ۲۹ تست | ✅ کد زنده اینجا | GATE 0 (محل اقامت) |
| **🧠 4d_system** | پژوهش مستقل | کامل، آماده اجرا | ✅ کد اینجا | تصمیم مالک برای run |
| **🏛️ app/NBB-CP** | حاکم (B6) | ۲۰۷ تست سبز | ✅ کد اینجا | Phase 4-5 + B1-B8 |
| **🔍 نقشه اختاپوس** | تشخیص | کار می‌کند | ✅ | retarget به این دایرکتوری |

---

## 🔗 جریان پول (قلب مالی مشترک)

```
Lead-نقاشی ──────── business income + GST 10% ──────┐
Mining ──────────── crypto @ AUD + electricity ─────┤
Crypto-eToro ────── CGT (شخصی، نه Pty Ltd) ─────────┼──► Accounting (قلب مالی)
Project-F ──────── creator income (۵۰٪ آری) ────────┤      ↓
Ziman ───────────── income + COGS ──────────────────┘   BAS/ATO (با verdict)
```

**سؤال ساختاری قفل‌کننده:** یک Pty Ltd یا چند شرکت برای نقاشی/ماینینگ/Project-F؟ → مالک + حسابدار.

---

## 🧬 خانوادهٔ حاکمیت (Shared DNA)

همهٔ جعبه‌ها از **همان خانوادهٔ حاکمیتی** آمده‌اند — الگوها تکرار می‌شوند:

| الگو | NBB-CP | Brushline | Project-F | 4D |
|---|---|---|---|---|
| **invariants مقدس** | ۱۲ تا (INV-1..12) | ۳ تا (INV-1..3) | ۸ hard rule | TCB list |
| **choke-point واحد** | ControlPlaneService.execute | Constitution Gate | brain+cockpit | guardrails |
| **kill-switch** | INV-3 (yield) | KILL_SWITCH file | /kill + /halt | daemon.stop |
| **audit hash-chain** | INV-5 (append-only) | SHA-256 chain | langar/boundary_log | events bus |
| **PII hash-ref** | INV-9 (quarantine) | INV-2 (sanitise) | zero-PII manifest | — |
| **fail-closed** | INV-12 | HARD_BLOCK | GATE 0 | anchor halt |
| **propose-only** | Governor proposes | draft→queue | propose-only | approve gate |
| **budget cap** | global cap (cents) | $5/action, $20/day | AUD 15/mo | 1000 calls/day |

> **این هم‌خانوادگی یعنی NBB-CP (app/) می‌تواند حاکمِ همهٔ پاها شود** — همانطور که طراحی شده (B6 بالای ۸ مغز).

---

## ⚠️ گیت‌های مشترک (همه را قفل می‌کنند)

### Security Gate (باز 🟢 — 2026-07-06)
۴ ردیف CRITICAL در `ROTATION_CHECKLIST` (نسخه canonical: `PRE-0/ROTATION_CHECKLIST.md`) — **همه ROTATED** (verdict صریح مالک 07-06):
1. **Monero wallet seed** — ROTATED
2. **Bybit keys** — ROTATED
3. **OKX keys** — ROTATED
4. **Anthropic keys** — ROTATED

> ⚠️ اصلاحِ drift سندی 2026-08-10: این بخش قبلاً «بسته 🔴» نوشته بود در حالی که
> گیت واقعاً LIFTED شده بود — تک‌منبع وضعیت: §۲ ARCHITECT_CHARTER + ROTATION_CHECKLIST.
> ردیف‌های HIGH/MEDIUM (۱۴ عدد) بازند ولی گیت نیستند و autonomy را قفل نمی‌کنند.

### GATE 0 (Project-F)
محل اقامت پارتنر ثبت نشده → هیچ‌چیز outward اجرا نمی‌شود.

---

## 📋 قالب استاندارد هر جعبهٔ سیاه

هر پوشهٔ پروژه این ساختار را دارد:

```
<project>/
├── README.md              ← نقشهٔ ایجنت (اول بخوان)
├── MANIFEST.yaml          ← قرارداد ماشین‌خوان جعبهٔ سیاه
├── contracts/adapter.yaml ← رابط read-only API
├── PROJECT.md             ← شناسنامه + Active Context
├── INDEX.md               ← MOC (نقشهٔ محتوا)
├── DecisionLog.md         ← تصمیمات + دلیل
├── OpenQuestions.md       ← مجهول‌ها
├── docs/                  ← اسناد، تحقیق، معماری
├── data/                  ← دادهٔ خام (PII محافظت‌شده)
└── archive/               ← دادهٔ کهنه / موارد زائد
```

---

## ⏭️ قدم‌های بعدی (به‌ترتیب اولویت)

### P0 — رفع انسداد مشترک
1. **چرخش ۴ ردیف CRITICAL** → Security Gate باز شود (کل اکوسیستم unblock).
2. **انتخاب حسابدار** (Accounting بلاکر #۱).
3. **GATE 0** (Project-F — ثبت محل اقامت پارتنر).

### P1 — احیای جعبه‌های سیاه
4. **پیدا کردن کد در `_code/`** یا `F:\backup` (Brushline، کاریابی، QuantumAlphaBot، sentinel، fleet، bot.js).
5. **اجرای تست‌ها** در همهٔ سیستم‌ها (green/red report).
6. **پر کردن Portfolio Registry** (Crypto) + Hardware Registry (Mining).

### P2 — اتصال
7. **NBB-CP را به حاکم تبدیل کن** (Phase 4-5) — همهٔ پاها از طریق adapter بهش وصل شوند.
8. **اجراهای یک‌ماههٔ 4D** (پژوهش مستقل).

---

## 🗂️ ساختار ریشه

```
پازل هشت پا/
├── README.md              ← تو اینجایی (نقشهٔ قلب مشترک)
├── 4D.md                  ← handoff 4D organism
├── 03 - Projects/         ← ۶ پا (پروژه‌های کسب‌وکار)
│   ├── Accounting/    Lead-نقاشی/    Mining/
│   ├── Crypto - etoro/    Ziman Galerry/    اونلی فنز/
├── 4d_system/             ← مغز پژوهش مستقل (خودکفا)
├── app/                   ← مغز حاکم NBB-CP (خودکفا)
├── نقشه اختاپوس/           ← ابزار تشخیص vault
└── NBB-Project-Scan-2026-07-11/ ← snapshot ثابت
```

---

> **جملهٔ پایانی:** این ارگانیسم صادق، جسور ولی محافظت‌شده است. هر جعبهٔ سیاه
> قرارداد دارد (`MANIFEST.yaml`)، رابط دارد (`adapter.yaml`)، و نقشه دارد (`README.md`).
> گیت‌ها بسته‌اند تا محافظت کنند، نه تا محدود کنند. وقتی مالک آماده باشد،
> قدم‌به‌قدم باز می‌شوند.
