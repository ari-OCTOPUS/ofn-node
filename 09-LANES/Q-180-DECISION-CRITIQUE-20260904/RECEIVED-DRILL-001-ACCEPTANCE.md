---
type: received-proposal
status: not_authorization
as_of: 2026-09-04
lane: Q-180-DECISION-CRITIQUE-20260904
provenance: C:/Users/Armin/Downloads/MIGRATION-DRILL-001-ACCEPTANCE.md
note: Copied into this lane so the Downloads file is not the only copy. Commands below are acceptance intent; the execution packet remains the procedure. See CRITIQUE.md.
---

# DRILL-001 — تمرین بازیابی، معیار پذیرش اجرایی

**هدف:** تبدیل `restore_drill: NOT_RUN` به `PASSED` یا `FAILED` با شاهد.
**دامنه:** فقط بستهٔ مشورتی self-model/organism-shadow. کل ارگانیسم نه.
**پیش‌نیاز:** MIRROR-001 ثبت شده · مقصد انتخاب شده · هیچ writer فعالی روی journal مبدأ نباشد.
**این سند مجوز نیست.** بدون واژهٔ صریح مالک اجرا نشود.

---

## 0. چرا این اولین تحویل واقعی است

مهاجرت با «کپی شد» اثبات نمی‌شود. با این اثبات می‌شود:
**در مقصد ادامه داد، هیچ رکوردی گم نشد، و می‌توان برگشت.**
اگر این تمرین در محیط ایزوله پاس نشود، مهاجرت واقعی صرفاً یک شکست گران‌تر است.

---

## 1. سه گزینهٔ مقصد (مالک باید یکی را انتخاب کند)

| گزینه | مسیر | مزیت | ریسک |
|---|---|---|---|
| A — root ایزوله روی خود ۱۳۸ | `/home/ari/drill-001/` | صفر ریسک شبکه، سریع‌ترین، مستقل از تصمیم نقش ۱۸۰ | همان سخت‌افزار؛ استقلال سخت‌افزاری را اثبات نمی‌کند |
| B — root تازه روی ۱۸۰ | `/opt/octopus/drill-001/` | معماری متفاوت را واقعاً آزمایش می‌کند | نقش ۱۸۰ `UNDECIDED` است؛ نباید با replica اشتباه شود |
| C — سخت‌افزار تازه | — | نزدیک‌ترین به مهاجرت واقعی | هنوز وجود ندارد؛ مسدودکنندهٔ زمانی |

**توصیه:** ابتدا A، سپس بلافاصله B با همان اسکریپت. A سرعت می‌دهد، B معنا.
هیچ‌کدام نباید روی `state/` موجود بنویسد.

---

## 2. مرحلهٔ صفر — عکس‌برداری مبدأ (فقط‌خواندنی)

```bash
SRC=/home/ari/ofn
python3 -m ofn.tools.verify_chain --journal $SRC/state/self-model/organism-shadow/   # باید از رکورد صفر پاس شود
sha256sum $SRC/state/self-model/organism-shadow/*                                    # همه هش‌ها ثبت شوند
stat -c '%n %s %y' $SRC/state/self-model/organism-shadow/*
git -C $SRC rev-parse HEAD
```

ثبت در `DRILL-001/SOURCE-SNAPSHOT.json`. اگر `verify_chain` پیش از شروع پاس نشود، **تمرین را شروع نکن** — مبدأ خودش خراب است و آن یک incident جداست.

---

## 3. مرحلهٔ یک — quiesce

```text
1. تایمر ساعتی self-model را برای مدت تمرین متوقف نکن؛ به‌جایش لحظه‌ای را انتخاب کن
   که بین دو اجرا باشد و mtime را قبل و بعد مقایسه کن.
   (توقف تایمر = تغییر سرویس = نیاز به مجوز جدا)
2. اگر mtime وسط کپی تغییر کرد ⇒ کپی باطل است، دوباره انجام شود.
3. هرگز journal در حال تغییر را کپی نکن.
```

قاعدهٔ سخت: **checkpoint هرگز جلوتر از ledger نباشد.** اگر checkpoint رکوردی را ارجاع داد که در journal نیست، کپی رد می‌شود.

---

## 4. مرحلهٔ دو — کپی به مقصد

```bash
DST=/home/ari/drill-001            # یا مسیر گزینهٔ B
mkdir -p $DST && chmod 700 $DST
cp -a $SRC/state/self-model/organism-shadow/. $DST/state-in/
# سپس readback و مقایسهٔ هش، فایل‌به‌فایل
sha256sum $DST/state-in/* > $DST/READBACK.sha256
diff <(cut -d' ' -f1 SOURCE.sha256 | sort) <(cut -d' ' -f1 $DST/READBACK.sha256 | sort)
```

- مبدأ **دست‌نخورده** می‌ماند. این کپی است، نه move.
- کش، مدل، دیتابیس نامرتبط و secret به‌صورت پیش‌فرض **وارد نمی‌شود**.
- secret از مکانیزم خصوصی مالک تأمین می‌شود، نه از این کپی.

---

## 5. مرحلهٔ سه — اثبات ادامه‌پذیری (قلب تمرین)

```bash
cd $DST
python3 -B -m unittest -v tests.test_self_model tests.test_self_model_input_trust \
  tests.test_kernel_purity tests.test_self_model_producer \
  tests.test_organism_shadow tests.test_runtime_provenance
python3 -m ofn.tools.verify_chain --journal $DST/state-in/
python3 -m ofn.adapters.self_model_producer --repo $DST --output $DST/private-out/SYSTEM-SELF-MODEL.json
```

سپس یک اجرای **دوم** بزن و بررسی کن:

| بررسی | انتظار |
|---|---|
| زنجیرهٔ هش از رکورد صفر | PASS |
| ۹۰ تست | PASS، بدون skip پنهان |
| exit code producer | 0 |
| تطابق کد انتخاب‌شده | مطابق منبع مقصد (fingerprint تابع باید **بازاندازه‌گیری** شود، قابل حمل نیست) |
| اجرای دوم روی همان ورودی | idempotent — رکورد تکراری ثبت نشود |
| رکورد جدید | `prev_hash` آن به آخرین رکورد منتقل‌شده وصل باشد |
| وضعیت مغز/فیزیولوژی | `UNKNOWN` بماند — سبز شدن یعنی تست دروغ می‌گوید |
| `executable` | `false` |

---

## 6. مرحلهٔ چهار — تست تخریب عمدی

```text
1. یک بایت از وسط آخرین رکورد journal مقصد را خراب کن.
2. producer را اجرا کن.
   انتظار: exit code غیرصفر · شاهد حفظ‌شده · هیچ نوشتن جزئی.
3. از نسخهٔ سالم بازگردان و verify_chain را دوباره بزن.
4. یک torn write بساز: کپی را وسط کار قطع کن، سپس اجرا کن.
   انتظار: fail-closed، بدون تعمیر خودکار.
```

اگر سیستم خرابی را نادیده گرفت و ادامه داد، **DRILL-001 شکست خورده است** — حتی اگر همهٔ ۹۰ تست سبز باشند.

---

## 7. مرحلهٔ پنج — تست برگشت

```text
1. مقصد را کامل حذف کن.
2. verify_chain روی مبدأ را دوباره بزن.
   انتظار: مبدأ بدون تغییر، همان هش‌های مرحلهٔ صفر.
3. یک اجرای معمولی روی مبدأ بزن و تأیید کن چیزی نشکسته است.
```

معیار: **حذف کامل مقصد هیچ اثری روی مبدأ نداشته باشد.** اگر داشت، جداسازی توهم بوده.

---

## 8. معیار پذیرش نهایی (هر هفت مورد لازم است)

```text
[ ] verify_chain در مبدأ و مقصد، هر دو از رکورد صفر PASS
[ ] هیچ رکوردی گم یا تکراری نشد (شمارش دقیق قبل و بعد)
[ ] ۹۰ تست در مقصد PASS، بدون skip
[ ] producer در مقصد exit 0 و state readback واقعی
[ ] تخریب عمدی ⇒ fail-closed اثبات‌شده
[ ] حذف مقصد ⇒ صفر اثر روی مبدأ
[ ] receipt نهایی با prev_hash، budget_after و هش همهٔ artifactها
```

نتیجه در `DRILL-001/RESULT.json` با یکی از دو مقدار: `PASSED` یا `FAILED`.
مقدار سوم وجود ندارد. «تقریباً پاس شد» یعنی `FAILED`.

---

## 9. آنچه این تمرین اثبات **نمی‌کند**

```text
- مهاجرت کل ارگانیسم (سرویس‌ها، mesh، پاهای کسب‌وکار، ledgerهای واقعی)
- بارگذاری کد جدید در daemon بلندمدت — همچنان UNVERIFIED
- نقش نود ۱۸۰ — همچنان UNDECIDED
- سلامت فیزیولوژی و اتصال بین‌اندامی — همچنان UNKNOWN
- استقلال سخت‌افزاری، اگر گزینهٔ A انتخاب شده باشد
```

این پنج مورد باید در `RESULT.json` هم تکرار شوند تا ایجنت بعدی موفقیت تمرین را با موفقیت مهاجرت اشتباه نگیرد.
