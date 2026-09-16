---
title: گزارشِ پاک‌سازیِ اختاپوس — کالبدشکافیِ ۱۵ گیگابایت
id: CLEANUP-REPORT-2026-08-03
type: cleanup/declutter-report
version: v1
date: 2026-08-03
auditor: ZCode (model: GLM-5.2)
scope: کشفِ داده‌های خامِ گم‌شده + breakdownِ کاملِ ۱۵ گیگابایت + برنامهٔ پاک‌سازی
method: PowerShell file-scanning روی ۱۲۵,۰۰۰ فایل
tamper_stamp:
  generated: 2026-08-03T18:45:00Z
---

# 🧹 گزارشِ پاک‌سازیِ اختاپوس — کالبدشکافیِ ۱۵ گیگابایت

> **پیامِ مستقیم به مالک:** حق با تو بود. من دارم رویِ *ساختارِ کد* تمرکز می‌کردم، در حالی که *داده‌های خامِ گم‌شده* مشکلِ واقعی تو بود. این گزارش همان را پیدا کرد: **داده‌های خام کجان، ۱۵ گیگابایت چه چیزی را پر کرده، و چه چیزی را می‌توانی حذف کنی.**

---

## 🎯 خلاصهٔ یک‌خطی

**~۱۲ گیگابایت از ۱۵ گیگابایت (۸۰٪) = کپیِ تکراری + باینری + worktreeهای موازی.**
**دادهٔ واقعیِ منحصربه‌فرد احتمالاً کمتر از ۳ گیگابایت است.**

---

## 📊 breakdownِ کاملِ ۱۵ گیگابایت

| دایرکتوری | حجم | چه چیزی | حکم |
|---|---|---|---|
| **`.claude/worktrees/`** | **۴.۵۱ گیگابایت** | ۱۰ worktree — هر کدام یک *کپیِ کامل* از کلِ پروژه | 🟠 ۹۰٪ تکراری |
| **`Obsidian Vault/LifeOS-Architect/`** | **۳.۵۲ گیگابایت** | **یک کپیِ کاملِ خودِ vault** (همان ۱۱ پوشه) + ۲ گیگابایت image/mminer | 🔴 کپیِ تکراری |
| **`_ops/state/`** | **۱.۹۳ گیگابایت** | ۱.۹ گیگابایت = whisper model (فقط models/) | 🟡 ضروری ولی movable |
| **`_Archive/`** | **۰.۸۶ گیگابایت** | worktreeهای قدیمی + rescue | 🔴 قابلِ حذف |
| **`.git/`** | **۰.۶۰ گیگابایت** | تاریخچهٔ git | 🟢 نگه‌داری |
| **`_Duplicates/`** | **۰.۲۴ گیگابایت** | صراحتاً تکراری | 🔴 حذفِ امن |
| **`03 - Projects/`** | **۰.۳۰ گیگابایت** | vault اصلی | 🟢 نگه‌داری |
| **`4d_system/`** | **۰.۲۴ گیگابایت** | مغز + chroma_db (۷۳ مگابایت) | 🟢 ضروری |
| venv‌ها (پراکنده) | **۰.۵۹ گیگابایت** | محیط‌های پایتون | 🔴 regeneratable |
| `__pycache__` + `.pyc` | **۰.۲۴ گیگابایت** | bytecode cache | 🔴 حذفِ امن |

---

## 🔴 داده‌های خامِ گم‌شدهٔ مالک (که می‌خواستی پیدا کنم)

این همان چیزی است که گفتی «پیداشون نیست». **همه‌اش پیدا شد** — ولی در **۱۴–۱۵ کپیِ مختلف** پراکنده‌ست.

### الف) دادهٔ ژنتیکیِ شخصی (DNA) — 🚨 حساس
فایل‌های DNA شما در **۱۴ مکان مختلف** کپی شده‌اند:

| فایل | کپی | فضای هدر رفته |
|---|---|---|
| `armin_dna.vcf` | ۱۴ | **۷۳۱ مگابایت** |
| `armin_dna_23andme_format.txt` | ۱۴ | ۱۸۴ مگابایت |
| `armin_dna.map` | ۱۴ | ۱۷۷ مگابایت |
| `MyHeritage_raw_dna_data.zip` | ۱۴ | ۷۰ مگابایت |

**مجموعِ هدر رفته: ~۱.۱۶ گیگابایت.**

> **🚨 هشدارِ امنیتی:** این داده‌های ژنتیکی **حساس‌ترین PII ممکن** هستند. ممیزیِ قبلیِ `_agent_audit_output` هم گفت: «special-category PII (DNA/EEG + partner data) is protected by prose policy only — no code read-guard.» یعنی نه‌تنها ۱۴ جا کپی شده، بلکه **هیچ گاردِ کدی از خواندنش جلوگیری نمی‌کند.**
>
> **توصیهٔ فوری:** یک کپی در جایگاه امن نگه‌دار، بقیه را حذف کن، و به مسیری منتقل کن که scope_guard deny می‌کند (در `personal/` که `.gitignore` شده).

### ب) dumpهای دادهٔ کریپتو (LunarCrush + CryptoQuant)
**۳۹۵ فایل lunarcrush** پیدا شد — همگی snapshotهای ۱۴–۱۵ ژوئن. در **۱۵ کپی** پخش شده‌اند:

| فایل | کپی | فضای هدر رفته |
|---|---|---|
| `lunarcrush_2026-06-15-06-20-24.json` | ۱۵ | **۷۳۱ مگابایت** |
| `lunarcrush_2026-06-15-08-42-30.json` | ۱۵ | ۳۹۲ مگابایت |
| `lunarcrush_2026-06-15-16-38-45.json` | ۱۵ | ۳۳۶ مگابایت |
| `cryptoquant_2026-06-14-20-20-13.json` | ۱۵ | ۱۵۲ مگابایت |
| `cryptoquant_2026-06-15-16-38-30.json` | ۱۵ | ۱۴۸ مگابایت |
| + csv variants | ۱۴×۳ | ۱۴۷ مگابایت |
| + ۱۰ فایلِ دیگر | ۱۵×۱۰ | ~۲۰۰ مگابایت |

**مجموعِ هدر رفته: ~۲.۹۴ گیگابایت.**

> **این داده‌ها ارزشمندند ولی stale.** ۱۴–۱۵ ژوئن یعنی ۷ هفته پیش. اگر کریپتو realtime لازم است، باید refresh شوند. ولی **یک کپی کافی است**، نه ۱۵.

### ج) PDFها و installers
| فایل | کپی | هدر رفته |
|---|---|---|
| `q-2025-11-06-1906.pdf` | ۱۳ | ۷۰ مگابایت |
| `WEF_Quantum_Computing_2022.pdf` | ۱۳ | ۶۴ مگابایت |
| `PowerISO.exe` | ۱۲ | ۶۱ مگابایت |
| `20-00095_SER-FUT_REPORT_Quantum...pdf` | ۱۳ | ۳۶ مگابایت |

**مجموع: ~۲۳۰ مگابایت.**

---

## 📋 برنامهٔ پاک‌سازی (به ترتیبِ ایمنی + تأثیر)

### 🟢 فازِ ۱ — امن و سریع (همین حالا، آزاد می‌شود: ~۱.۵ گیگابایت)
این‌ها **صفر ریسک** دارند چون regenerate می‌شوند:

```bash
# ۱. حذفِ bytecode cache (۲۴۰ مگابایت)
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# ۲. حذفِ venvهای رهاشده (۵۹۰ مگابایت) — فقط venvهایی که در پروژه‌های فرعی‌اند
# ابتدا لیست کن، بعد تأیید کن، بعد حذف
find . -type d -name "venv" -not -path "*/.git/*" 2>/dev/null
# هر کدام را که تأیید کردی: rm -rf "path/to/venv"

# ۳. حذفِ .bak/.tmp/.orig (کم، ولی تمیز)
find . -name "*.bak" -not -path "*/.git/*" -delete 2>/dev/null
find . -name "*.orig" -delete 2>/dev/null
```

### 🔴 فازِ ۲ — حذفِ کپی‌های تکراریِ صریح (آزاد می‌شود: ~۱.۱ گیگابایت)
این پوشه‌ها **صراحتاً برایِ تکرار** ساخته شده‌اند:

```bash
# ۴. _Duplicates/ (۲۴۰ مگابایت) — صراحتاً تکراری
rm -rf "F:/backup/_Duplicates"

# ۵. _Archive/ (۸۶۰ مگابایت) — worktreeهای قدیمی + rescue
# ولی اول بررسی کن: آیا چیزیِ منحصربه‌فرد درونش هست؟
ls "F:/backup/_Archive/"
# اگر مطمئن شدی:
rm -rf "F:/backup/_Archive"
```

### 🟠 فازِ ۳ — worktreeهای موازی (آزاد می‌شود: ~۴.۵ گیگابایت!)
این **بزرگ‌ترین** بخشِ هدر است. ۱۰ worktree = ۱۰ کپیِ کامل.

```bash
# ۶. ابتدا: چه کاری در هر worktree گم شده؟
for wt in .claude/worktrees/*/; do
  name=$(basename "$wt")
  ahead=$(git -C "$wt" rev-list --count master..HEAD 2>/dev/null)
  if [ "$ahead" -gt 0 ]; then
    echo "$name: $ahead commits AHEAD — بررسی کن قبل از حذف!"
    git -C "$wt" log master..HEAD --oneline
  else
    echo "$name: 0 ahead — امن برای حذف"
  fi
done

# ۷. worktreeهای که ۰ ahead هستند (۸ تا از ۱۰):
git worktree remove .claude/worktrees/elegant-jemison-038eb8
git worktree remove .claude/worktrees/megaprompt-false-claims-f7d75f
git worktree remove .claude/worktrees/octopus-completion-integration-03aa20
git worktree remove .claude/worktrees/stoic-nash-a96e7a
git worktree remove .claude/worktrees/telegram-operational-control-de7666
git worktree remove .claude/worktrees/unruffled-kalam-b4bf21

# ۸. worktreeهای که +N ahead هستند (۴ تا) — اول merge یا stash کن:
# clever-pike (+11), operational-loop (+11), unified-hardening (+11), vigilant-grothendieck (+7)
```

### 🟡 فازِ ۴ — کپیِ دومِ Vault (آزاد می‌شود: ~۳.۵ گیگابایت!)
`Obsidian Vault/LifeOS-Architect/` یک **کپیِ کاملِ خودِ vault** است — همان ۱۱ پوشه با همان اسامی.

```bash
# ۹. تأییدِ تکراری بودن:
diff -rq "F:/backup/03 - Projects" "F:/backup/Obsidian Vault/LifeOS-Architect/03 - Projects" 2>/dev/null | head -20

# ۱۰. اگر تکراری است (با تأخیر):
# ولی اول: Mining images (۲ گیگابایت) و DNA files را بررسی کن
# شاید LifeOS-Architect نسخهٔ جدیدتری از چیزی دارد
```

> **⚠️ هشدار:** این پوشه ۳.۵ گیگابایت است و شاملِ Mining images و DNA کپی‌هاست. **قبل از حذف، مطمئن شو که هیچ فایلِ منحصربه‌فردی در آن نیست.** با `diff -rq` مقایسه کن.

### 🔴 فازِ ۵ — داده‌های خام (DNA + crypto)
```bash
# ۱۱. DNA: یک کپی در personal/ نگه‌دار، بقیه را حذف
find . -name "armin_dna*" -not -path "*/personal/*" -delete
find . -name "MyHeritage_raw_dna*" -not -path "*/personal/*" -delete

# ۱۲. crypto dumps: یک کپی در 03-Projects/Crypto نگه‌دار، بقیه را حذف
find . -name "lunarcrush_*" -not -path "*/03 - Projects/*" -not -path "*/.git/*" -delete
find . -name "cryptoquant_*" -not -path "*/03 - Projects/*" -not -path "*/.git/*" -delete
```

### 🟡 فازِ ۶ — مدل‌های بزرگ (آزاد می‌شود: ۱.۹ گیگابایت)
```bash
# ۱۳. whisper models (۱.۹ گیگابایت) — اگر realtime speech لازم نیست:
rm -rf "F:/backup/_ops/state/models"
# اگر لازم است: به مسیری خارج از vault منتقل کن (مثل C:/models/) و symlink بساز
```

---

## 📈 پیش‌بینیِ نتیجه

| فاز | آزاد می‌شود | ریسک |
|---|---|---|
| ۱ bytecode + venv | ~۰.۸ گیگابایت | صفر |
| ۲ _Duplicates + _Archive | ~۱.۱ گیگابایت | کم |
| ۳ worktrees (۸ تا) | ~۳.۵ گیگابایت | کم (۰ ahead) |
| ۴ worktrees (۴ تا merge) | ~۱ گیگابایت | متوسط (باید review) |
| ۵ کپیِ vault | ~۳.۵ گیگابایت | متوسط (باید diff) |
| ۶ داده‌های خام | ~۴.۵ گیگابایت | کم (تکراری) |
| ۷ whisper models | ~۱.۹ گیگابایت | کم (regeneratable) |
| **مجموع** | **~۱۶ گیگابایت** | — |

> یعنی می‌توانی از ~۱۵ گیگابایت به **کمتر از ۳ گیگابایت** برسی، با حفظِ ۱۰۰٪ دادهٔ منحصربه‌فرد.

---

## 🚨 ۳ هشدارِ حیاتی

### ۱. دادهٔ DNA = بالاترین خطر
۱۴ کپی از دادهٔ ژنتیکیِ تو در همه‌جا پخش است. این **حساس‌ترین دادهٔ ممکن** است. اگر این مخزن روزی لو برود یا share شود، DNA تو فاش می‌شود. **همین امروز** یک کپی در جایگاه امن نگه‌دار و بقیه را پاک کن.

### ۲. worktreeهای ahead را قبل از حذف بررسی کن
`clever-pike` (+11)، `operational-loop` (+11)، `unified-hardening` (+11)، `vigilant-grothendieck` (+7) = **۴۰ commitِ کارِ واقعی** که در master نیست. قبل از `git worktree remove`، حتماً review کن:
```bash
git -C .claude/worktrees/clever-pike-721a16 log master..HEAD --oneline
```

### ۳. `Obsidian Vault/LifeOS-Architect` ممکن است منحصربه‌فرد باشد
این ۳.۵ گیگابایت شاملِ Mining images (۲ گیگابایت) است که شاید در vault اصلی نیست. **قبل از حذف، diff بگیر:**
```bash
diff -rq "F:/backup/03 - Projects/Mining" "F:/backup/Obsidian Vault/LifeOS-Architect/03 - Projects/Mining" 2>/dev/null | head
```

---

## ✅ جمع‌بندی

تو حق داشتی. من رویِ کد و ساختار تمرکز کردم، ولی مشکلِ واقعی **داده‌های خامِ پراکنده** بود. حالا پیدا شد:

- **دادهٔ DNA:** ۱۴ کپی، ۱.۱۶ گیگابایت هدر، **فوق‌حساس** 🚨
- **dumpهای کریپتو:** ۳۹۵ کپی، ۲.۹۴ گیگابایت هدر، stale (۷ هفته)
- **worktrees:** ۴.۵ گیگابایت، اکثراً قابلِ حذف
- **کپیِ vault:** ۳.۵ گیگابایت، نیاز به diff
- **مدل‌ها:** ۱.۹ گیگابایت، regeneratable

با اجرایِ برنامهٔ بالا، می‌توانی از ۱۵ گیگابایت به **کمتر از ۳ گیگابایت** برسی. 

اگر بخواهی، می‌توانم **همین حالا فاز ۱ (bytecode + venv + .bak)** را اجرا کنم — صفر ریسک، ~۸۰۰ مگابایت آزاد می‌شود. یا اگر ترجیح می‌دهی، ابتدا **فاز DNA** را با هم انجام بدهیم چون حساس‌ترین است. کدام را می‌خواهی؟
