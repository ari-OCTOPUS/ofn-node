---
tags: [ofn, index, mega-data, agent-context]
aliases: [مگا-دیتا, مرجع-کامل, INDEX-MASTER]
updated: 2026-09-03
---

# MEGA-DATA — نقشه‌ی کامل اختاپوس

> این فایل مرجع اصلی هر agent، هر session Claude Code، و هر ابزار Obsidian است.
> هر بار که جلسه‌ای شروع می‌شود، این را بخوان — نه به‌جای CLAUDE.md، بلکه کنار آن.
> آخرین update: **2026-09-03 · board138 · آری**

---

## ۰) چکیده — در یک صفحه

```
دستگاه:   OrangePi 5 Pro · RK3588S · 4GB · DietPi/Trixie · board138
مالک:     آری (شریک ۵۰٪ هر سه کسب‌وکار)
هدف:      سه کسب‌وکار واقعی را ۲۴ ساعته بدون نظارت مستمر اداره کند
فلسفه:    کرنل تصمیم می‌گیرد. مدل مشورت می‌دهد. انسان حکم می‌کند.
بقا:      اختاپوس باید منابع خودش را پیدا کند تا بقای همه را تامین کند
```

---

## ۱) پرتفوی — چهار tenant

| leg | نام تجاری | شریک | پورت | دامنه | وضعیت |
|---|---|---|---|---|---|
| `ziman` | GiftMesh Sydney | ملیحه | 8791 | ziman.master-painting.com | فعال |
| `lead` | Master Painting | عباس | 8792 | lead.master-painting.com | فعال |
| `studio` | Studio OFN | سبا | 8793 | studio.master-painting.com | منتظر charter |
| `hypno` | Hypno (برند نهایی نامشخص) | — | — | — | خارج از scope · باید دیده شود |
| `panel` | داشبورد مالک | آری | 8794 | panel.master-painting.com | فعال |

**پورت‌های رزرو:** 8770 (`control-brain`) · 8780 (`ziman_os`)

---

## ۲) ساختار دایرکتوری — کامل

```
ofn-node/
│
├── CLAUDE.md                    ← قانون اساسی · اول هر session بخوان
├── MEGA-DATA.md                 ← این فایل · نقشه کامل
├── HANDOFF.md                   ← وضعیت زنده · آخر هر session آپدیت کن
├── INDEX.md                     ← ورودی Obsidian
│
├── ofn/
│   ├── kernel/                  ← کرنل OFN (تصمیم‌گیری مرکزی)
│   ├── packs/
│   │   ├── ziman/               ← هدیه‌فروشی Ziman
│   │   ├── lead/                ← نقاشی ساختمان · عباس
│   │   ├── studio/              ← تولید محتوا · سبا
│   │   └── hypno/               ← tenant چهارم · بدون charter
│   └── agents/
│       ├── consent_store.py     ← مدیریت رضایت مشتریان
│       ├── demand_harvest.py    ← هارویست demand سیگنال‌ها
│       ├── h1_buysw.py          ← parse/score مناقصات NSW
│       ├── h1_buysw_dom.py      ← DOM parser برای buy.nsw
│       ├── h1_harvest.py        ← ⚰️ DEAD · feed مُرد فوریه ۲۰۲۵
│       ├── h3_strata.py         ← strata building leads
│       ├── heartbeat.py         ← سیگنال حیات دستگاه
│       ├── imap_listener.py     ← گوش دادن به ایمیل ورودی
│       ├── lead_email_writer.py ← نوشتن ایمیل به lead (outbox)
│       ├── mail_credentials.py  ← مدیریت اعتبارنامه‌ی ایمیل
│       ├── memory_chain.py      ← زنجیره حافظه بین session‌ها
│       ├── nsw_ocp_harvest.py   ← ⚠️ PARKED · داده خوب، مسیر غلط
│       ├── outbound_worker.py   ← کارگر outbox (بزرگ‌ترین فایل: 31KB)
│       ├── owner_notify.py      ← اعلان به مالک (GREEN cockpit)
│       ├── quote_engine.py      ← موتور قیمت‌دهی نقاشی
│       ├── quote_fingerprint.py ← dedup قیمت‌ها
│       ├── quote_pipeline.py    ← pipeline کامل quote
│       ├── seek_harvest.py      ← ✅ LIVE · Seek.com.au painter jobs
│       ├── source_registry.py   ← ✅ NEW (PR#142) · ۱۷ منبع خودمختار
│       └── ziman_tender_harvest.py ← ✅ NEW (PR#141) · Chromium browser
│
├── tests/
│   ├── test_source_registry.py  ← ✅ NEW
│   ├── test_ziman_tender_harvest.py ← ✅ NEW
│   └── [سایر تست‌ها...]
│
├── docs/
│   ├── ARBITER-FEEDBACK-138.md  ← بازخورد داور board138
│   ├── agent-context/           ← context برای agent session‌ها
│   ├── architecture/            ← مستندات معماری
│   ├── audit-138/               ← audit مخصوص board138
│   ├── audit/                   ← audit عمومی
│   ├── cockpit-v2/              ← طراحی داشبورد نسل دوم
│   ├── consent/                 ← مستندات رضایت
│   ├── day7/                    ← اسناد روز هفتم (منابع مرده تأیید شد)
│   ├── discovery-138/           ← کشف‌های board138
│   ├── handoffs/                ← تاریخچه handoff‌ها
│   ├── integrations/            ← یکپارچه‌سازی‌ها
│   ├── lanes/                   ← مسیرهای کاری
│   ├── lineage/                 ← ردیابی تغییرات
│   ├── octopus-mesh/            ← شبکه اختاپوس‌ها
│   ├── octopus-os/              ← سیستم‌عامل اختاپوس
│   ├── octopus-rapid/           ← چرخه سریع
│   ├── octopus-surgery/         ← جراحی سیستم
│   ├── operations/              ← عملیات روزانه
│   ├── prompts/                 ← prompt‌های ذخیره شده
│   ├── repository-hygiene/      ← بهداشت ریپو
│   ├── research/                ← تحقیقات
│   ├── runbooks/                ← دستورالعمل‌های عملیاتی
│   ├── season/                  ← فصل‌های پروژه
│   ├── security/                ← امنیت
│   ├── spine-138/               ← ستون فقرات board138
│   └── [سایر دایرکتوری‌ها...]
│
├── state/
│   └── legs/                    ← claim فایل‌ها برای شاهد مستقل
│
└── tools/
    └── repo_baseline.py         ← خط پایه ریپو
```

---

## ۳) وضعیت PR‌های باز — امروز 2026-09-03

| PR | عنوان | وضعیت | اولویت |
|---|---|---|---|
| [#141](https://github.com/ari-OCTOPUS/ofn-node/pull/141) | ziman_tender_harvest — Chromium headless | ⏳ منتظر تأیید URL مالک | 🔴 بلوکر |
| [#142](https://github.com/ari-OCTOPUS/ofn-node/pull/142) | source_registry — ۱۷ منبع خودمختار | ⏳ آماده merge | 🟡 مهم |
| [#143](https://github.com/ari-OCTOPUS/ofn-node/pull/143) | این فایل (MEGA-DATA) | ⏳ آماده merge | 🟢 مستند |

---

## ۴) نقشه منابع — کدام سایت اختاپوس می‌تواند بگردد

### ✅ الان زنده — harvest_module دارد

| سایت | ماژول | نوع lead |
|---|---|---|
| [seek.com.au/painter-jobs/in-sydney-nsw](https://www.seek.com.au/painter-jobs/in-sydney-nsw) | `seek_harvest.py` | کارفرما نیازمند نقاش |
| [tenders.nsw.gov.au](https://www.tenders.nsw.gov.au) | `ziman_tender_harvest.py` (PR#141) | مناقصه دولتی |

### ⚠️ دارای داده — نیاز به repoint

| سایت | ماژول | مشکل |
|---|---|---|
| [data.open-contracting.org/en/publication/11](https://data.open-contracting.org/en/publication/11) | `nsw_ocp_harvest.py` | PARKED · mismatch مسیر |

### 🔵 stub — PR آینده

| سایت | tier | نوع | نیاز |
|---|---|---|---|
| [au.indeed.com/jobs?q=painter&l=Sydney](https://au.indeed.com/jobs?q=painter&l=Sydney+NSW) | T2 | job board | کپی pattern از seek |
| [airtasker.com/au/s/?q=painting](https://www.airtasker.com/au/s/?q=painting&location=Sydney%2C+NSW) | T2 | homeowner tasks | Chromium (PR#141 pattern) |
| [hipages.com.au/find/painters/sydney](https://hipages.com.au/find/painters/sydney) | T2 | quotes از homeowner | Chromium |
| [gateway.icn.org.au](https://gateway.icn.org.au/opportunities?state=NSW&category=painting) | T1 | subcontract | Chromium |
| [gumtree.com.au/s-services/sydney/painting](https://www.gumtree.com.au/s-services/sydney/painting/k0c18310l3004152) | T4 | classified | HTML regex |
| [api.tenders.gov.au](https://api.tenders.gov.au/api/contractnotice/search?keyword=painting&limit=1) | T1 | federal | JSON API |
| [fairtrading.nsw.gov.au](https://www.fairtrading.nsw.gov.au/trades-and-businesses/construction-and-trade-licensing/licence-search) | T5 | licence register | Chromium |

### 🔒 auth لازم — هرگز خودکار

- VendorPanel (councils/health)
- Facebook Marketplace
- Nextdoor

---

## ۵) گیت‌های بسته — دست نزن

```
secret_rotation      ← چهار راز CRITICAL هنوز چرخانده نشده‌اند
partner_precondition ← پیش‌شرط انتشار استودیو ثبت نشده
```

**اگر کاری به این‌ها خورد: گزارش بده، اجرا نکن.**

---

## ۶) flag‌های خروجی — همه باید 0 باشند

```bash
OCTOPUS_WIRE_LEAD_OUTBOUND=0
OCTOPUS_WIRE_EMAIL=0
OCTOPUS_WIRE_LEAD_VERDICT_EFFECT=0
OCTOPUS_WIRE_HARVEST=0        # ← فقط با تأیید صریح آری: 1 کن
OCTOPUS_WIRE_LEAD_DRAFT=0
OCTOPUS_WIRE_PROJECTF_*=0
OCTOPUS_WIRE_SABA_BRIDGE=0
```

---

## ۷) محدودیت‌های سخت‌افزار — board138

```
دستگاه:    OrangePi 5 Pro · RK3588S
RAM:       4GB کل
DietPi:    300-500 MB
Claude Code: 500-1000 MB
مدل محلی:   ~1800 MB (وقتی نصب شد)
باقی:       کم — مدیریت کن

Chromium:  --single-process (برای board 4GB)
هسته‌ها:   A76 cores 4-7 برای مدل (taskset -c 4-7)
SQL:       WAL + FULL sync (هرگز NORMAL)
RTC:       باتری ندارد → timedatectl set-ntp true
```

---

## ۸) قراردادهای امنیتی harvest

```
read-only:     هیچ POST، هیچ login، هیچ form submit
double-lock:   owner_approval=True + OFN_WIRE_HARVEST=1 (هر دو صریح)
ask-first:     URL stub است تا مالک تأیید کند
fail-closed:   هر exception → HARVEST_FAILED، بدون partial write
claim:         نتیجه در state/legs/ برای شاهد مستقل
```

---

## ۹) ساب‌دامنه‌ها و تونل

```
panel.master-painting.com  → 127.0.0.1:8794   آری
ziman.master-painting.com  → 127.0.0.1:8791   ملیحه
lead.master-painting.com   → 127.0.0.1:8792   عباس
studio.master-painting.com → 127.0.0.1:8793   سبا
```

**Cloudflare Tunnel:** فعال · 4 ساب‌دامنه · گواهی خودکار

---

## ۱۰) چرخه بقا — loop شبانه

```
00:00  source_registry.probe_all()     ← همه ۱۷ منبع HEAD-check
00:05  seek_harvest.cycle()            ← ✅ LIVE
00:10  ziman_tender_harvest.cycle()    ← بعد از merge PR#141 + تأیید URL
00:30  nsw_ocp_harvest (بعد از repoint) ← منتظر
06:00  imap_listener.cycle()           ← ایمیل ورودی
08:00  owner_notify: daily report      ← GREEN cockpit
```

---

## ۱۱) کارهای باقی‌مانده — به ترتیب اولویت

### 🔴 بلوکر (منتظر مالک)
1. **تأیید URL سایت منبع مناقصات** → PR#141 deploy می‌شود
2. **تأیید OFN_WIRE_HARVEST=1** → اولین harvest واقعی

### 🟡 مهم (Claude Code روی board138 می‌تواند انجام دهد)
3. merge PR#142 (source_registry) → probe_all شبانه فعال
4. indeed_harvest.py → کپی seek pattern، تغییر URL
5. nsw_ocp_harvest repoint → از lead به renewal-radar
6. اجرای `python3 -m pytest -q` → مطمئن شو همه سبز

### 🟢 آینده
7. airtasker_harvest (Chromium PR#141 pattern)
8. hipages_harvest (JSON API probe اول)
9. cockpit-v2 source status dashboard
10. VendorPanel → owner ABN registration → IMAP listener

---

## ۱۲) دستورات سریع

```bash
# خط پایه
cd ~/ofn && python3 -m pytest -q
cd ~/ofn && python3 tools/repo_baseline.py --tests

# تست‌های جدید
python3 -m pytest tests/test_source_registry.py -v
python3 -m pytest tests/test_ziman_tender_harvest.py -v

# نصب Chromium روی board138
sudo apt-get install -y chromium-browser chromium-chromedriver python3-selenium

# probe همه منابع (بدون browser)
python3 -c "from ofn.agents.source_registry import probe_all, report; probe_all(); print(report())"

# وضعیت تونل
journalctl -u cloudflared -n 30

# دما
cat /sys/class/thermal/thermal_zone*/temp
```

---

## ۱۳) Obsidian Graph — لینک‌های مهم

```
[[CLAUDE]]          ← قانون اساسی
[[HANDOFF]]         ← وضعیت زنده
[[MEGA-DATA]]       ← این فایل
[[INDEX]]           ← ورودی اصلی
[[PORTFOLIO-TENANT-MAP]] ← نقشه tenant‌ها
[[DECISIONS]]       ← تصمیمات ثبت شده
```

---

## ۱۴) اصل بنیادین

> اختاپوس خودمختار است — یعنی باید منابع خودش را پیدا کند.
> صاحب قلمرو را مشخص می‌کند (سیدنی · نقاشی).
> اختاپوس هر آب عمومی قابل شنا را پیدا می‌کند، می‌گردد، و گزارش می‌دهد.
> هیچ حرکتی بدون تأیید مالک به دنیای بیرون نمی‌رود.
> بقای اختاپوس = بقای همه.

---
*آخرین update: Perplexity research agent · 2026-09-03 13:12 AEST*
*ریپو: [ari-OCTOPUS/ofn-node](https://github.com/ari-OCTOPUS/ofn-node)*
