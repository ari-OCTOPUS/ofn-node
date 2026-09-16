---
type: control-design
project: ZIMAN
status: proposed
version: 1
updated: 2026-07-12
scope: "OLP-1 first assignment (A-K) grounded in 35-product catalog"
authority: see ZIMAN-DESIGN-RECONCILIATION.md (overrides on conflict)
---

# سند الف — طراحیِ فوندیشنِ زیمان (OLP-1)

> نسخه: طراحی مفهومی · مبنا: ممیزیِ ۲۰۲۶-۰۷-۱۲ + کاتالوگِ گراند‌شدهٔ ۳۵‌محصولی · دامنه: فقط طراحی، بدون تغییرِ فایل/کد · دکترین: IMPROVE, DON'T REWRITE.

این سند «فرمانِ اولِ» OLP-1 را کامل می‌کند و روی محصولات واقعی گراند است. ۱۰ قلمِ خواسته‌شده در سه بخش پوشش داده شده: نرمال‌سازیِ موجودی، تاکسونومی، عکس‌به‌شناسه، Product Card (A1)؛ qualification متخصصِ محصول + ۳ آزمایش فروش (A2)؛ Event/Memory schema + تعارض‌ها/ورودی‌های مفقود + نگاشتِ Obsidian/تلگرام + معیارِ خروج (A3).

---

## نرمال‌سازی موجودی + تاکسونومیِ نهایی + نگاشت عکس‌به‌شناسه + Product Card

> طبقهٔ حقیقت برای هر گزاره با برچسب صریح مشخص شده است. هیچ عددِ قیمت/موجودی/ظرفیت جعل نشده؛ کمیت‌های نامشخص با `[Unknown-owner]` و شناسهٔ verdict مربوطه (`ZIM-Vx`) نگه‌داشته شده‌اند. این یک مصنوعِ طراحی است.

---

### ۱) نرمال‌سازیِ موجودیِ ۵۰ — آشتیِ «۳۵ عکاسی‌شده در برابر ۵۰ OWNER_INPUT»

#### ۱-۱. صورت‌مسئلهٔ عدد

| منبع | مقدار | طبقهٔ حقیقت | شناسه |
|---|---|---|---|
| عکس‌های متمایز پس از پاک‌سازی (۴۱ عکس − ۱ سفید − duplicateهای variant) | **۳۵ محصولِ متمایز** | `MEASURED` (شمارشِ کاتالوگ) | ZIM-CAT |
| ادعای مالک دربارهٔ تعداد محصول | **۵۰** | `OWNER_INPUT` (نه در اسناد، ورودیِ شفاهیِ مالک) | — |
| شکاف | **~۱۵** | `CONFLICT` | ZIM-V-INV |

هستهٔ تعارض: عدد ۵۰ **قابلِ استناد به هیچ مصنوعِ قابل‌شمارش نیست**؛ عدد ۳۵ measured اما ممکن است زیرشمار باشد (اقلامِ بی‌عکس) یا فراشمار (اگر مالک variantها را جدا بشمارد). تا رفعِ `ZIM-V-INV`، **۳۵ = مبنای عملیاتیِ verified؛ ۵۰ = سقفِ ادعایی**. هیچ‌کدام قیمت/موجودیِ فیزیکی را تعیین نمی‌کنند (آن `ZIM-V5`/موجودیِ فیزیکیِ جداست).

#### ۱-۲. سه سناریوی آشتی (صریح، بدون ترجیحِ زودهنگام)

```yaml
reconciliation_scenarios:
  - id: S1_missing_photos
    name: "۱۵ محصولِ بی‌عکس"
    hypothesis: "۵۰ محصولِ متمایز واقعاً وجود دارد؛ ۱۵ تا هرگز عکاسی نشده‌اند."
    truth_class: HYPOTHESIS
    implied_true_count: 50
    evidence_required:
      - "فهرست/موجودیِ فیزیکیِ مالک از ۱۵ قلمِ بدونِ asset عکس"
      - "هر قلم ⇒ یک product_id جدید با photo_asset_ids: [] و status: catalog_incomplete"
    test: "آیا مالک می‌تواند ۱۵ شناسهٔ فاقدِ عکس را نام ببرد؟"
    falsified_if: "مالک نتواند بیش از N<15 قلمِ واقعی فهرست کند."
    catalog_action: "ایجادِ placeholderهای ZIM-Fx-NN با photo=none تا سقفِ ۵۰."

  - id: S2_approximate_50
    name: "۵۰ عددِ تقریبی/گِردشده"
    hypothesis: "«۵۰» برآوردِ ذهنیِ round بوده؛ عددِ واقعی نزدیکِ ۳۵ است."
    truth_class: HYPOTHESIS
    implied_true_count: "~35"
    evidence_required:
      - "تأییدِ مالک که ۵۰ رقمِ دقیق نبوده"
    test: "از مالک بپرس: ۵۰ شمارش شده یا تخمین؟"
    falsified_if: "مالک اصرار بر شمارشِ دقیقِ ۵۰ داشته باشد."
    catalog_action: "بستنِ shortfall؛ ۳۵ = عددِ رسمی؛ به‌روزرسانیِ OWNER_INPUT به [Estimate]."

  - id: S3_variant_expansion
    name: "شکاف از تفکیکِ variant"
    hypothesis: "مالک variantها (رنگ/سایز/جنسیتِ نوزاد/محتوای همپر) را جدا می‌شمارد؛ ۳۵ عکسِ والد ⇒ ~۵۰ SKU."
    truth_class: HYPOTHESIS
    implied_true_count: "35 parents → ~50 SKUs"
    evidence_required:
      - "تأییدِ ۳ جفتِ variant-مشکوک (بخش ۴) + facetِ baby_gender + subtagهای handbag-basket collection(۴)"
    test: "آیا هر عکس چند SKU قابل‌فروش تولید می‌کند؟"
    falsified_if: "هیچ محصولی بیش از یک SKU ندارد."
    catalog_action: "مدلِ parent/variant؛ product_id=parent، افزودنِ variant_of + sku_variants[]."
```

#### ۱-۳. رویهٔ نرمال‌سازی (بدون حذفِ داده، مطابق IMPROVE-DONT-REWRITE)

1. **۳۵ محصولِ measured** = ستون فقراتِ کاتالوگ؛ همه با `status: active_photographed`.
2. شکافِ ۱۵ **حذف نمی‌شود** بلکه به‌صورتِ ۱۵ رکوردِ `status: ghost_unverified` (photo=none, source=OWNER_INPUT) نگهداری می‌شود تا `ZIM-V-INV` یکی از S1/S2/S3 را قطعی کند.
3. عددِ ۵۰ در متادیتا به‌عنوان `owner_claimed_count: 50 [OWNER_INPUT]` می‌ماند؛ **هرگز به‌عنوان verified منتشر نمی‌شود**.
4. خروجیِ داشبورد (no-auth, read-only) هر دو را نشان می‌دهد: `verified: 35 | claimed: 50 | delta: 15 (unreconciled)`.

---

### ۲) تاکسونومیِ نهایی — F1–F4 + چهار facet + زیرتگ‌ها + قانونِ مرزِ F3/F4

#### ۲-۱. خانواده‌ها (محورِ اصلی، یک محصول = دقیقاً یک family)

| family | نام | تعریف | edible؟ | شمار (measured) |
|---|---|---|---|---|
| **F1** | floral | گلِ ماندگارِ سیلک/real-touch؛ غیرخوراکی، آرایشِ نمایشی | خیر | ۱۸ |
| **F2** | framed | قابِ شادوباکسِ دیواری (گلِ قاب‌شده) | خیر | ۲ |
| **F3** | candy_basket | خودِ «گل‌ها» آب‌نباتِ خوراکی‌اند؛ نمایش = خوراکی | بله (نمایش) | ۴ |
| **F4** | mixed_hamper | همپرِ ترکیبی: خوراکیِ بسته‌بندی‌شده + اقلامِ غیرخوراکی | جزئی | ۱۱ |
| — | (خطای عکس) | عکسِ سفید = محصول نیست | — | ۰ (کنارگذاشته) |
| | | **جمع measured** | | **۳۵** |

#### ۲-۲. قانونِ مرزِ F3 در برابر F4 (تصمیمِ قطعی)

```yaml
boundary_rule_F3_vs_F4:
  principle: "ماهیتِ «نمایش» (the display object) تعیین‌کننده است، نه صرفِ حضورِ خوراکی."
  F3_candy_basket:
    definition: "خودِ اقلامِ گل‌مانند، آب‌نباتِ خوراکی‌اند؛ محصول = یک آرایهٔ خوراکیِ یکپارچه."
    test: "اگر خوراکی را برداری، «محصول» ناپدید می‌شود (گلی باقی نمی‌ماند)."
    edible: true
    typical_perishable: "بستگی به نوعِ آب‌نبات؛ ZIM-F3-02 فاسدشدنی علامت خورده."
  F4_mixed_hamper:
    definition: "جعبه/سبدِ شاملِ خوراکیِ بسته‌بندی‌شدهٔ صنعتی (شکلات/آب‌نبات) + اقلامِ غیرخوراکی (عروسک/بادکنک/لیوان)."
    test: "خوراکی و غیرخوراکی جدا و بسته‌بندی‌شده‌اند؛ برداشتنِ خوراکی، بقیهٔ همپر را باقی می‌گذارد."
    edible: partial
    rule: "کلِ F4 فاسدشدنی تلقی می‌شود ⇒ «فقط تحویلِ محلی» (بخش ۲-۴، پرچمِ ۱)."
  disambiguation_examples:
    - "سبدِ گلِ رزِ آب‌نباتی → F3 (خودِ گل خوراکی است)."
    - "جعبهٔ شاملِ Ferrero + عروسک → F4 (خوراکیِ بسته‌بندی + غیرخوراکی)."
```

#### ۲-۳. زیرتگ‌های F1 (subtag، محورِ فرم؛ مستقل از facet)

```yaml
F1_subtags:
  - box-arrangement:        "آرایش در جعبهٔ صلب (rigid box)"
  - basket-arrangement:     "آرایش در سبد"
  - handbag-basket:         "سبدِ کیف‌دستی‌شکل — کالکشنِ ۴‌تایی (کاندیدِ variant، بخش ۱ S3)"
  - tray-hoop:              "سینی/حلقهٔ دیواری‌یا‌رومیزی"
  - gift-bag-posy:          "دسته‌گلِ کوچک در کیسهٔ کادو"
note: "subtag فقط برای F1 الزامی است؛ F2/F3/F4 می‌توانند subtag: null داشته باشند."
```

#### ۲-۴. چهار facet متقاطع (مستقل از family — بولی/انومریت)

```yaml
facets:
  perishable:
    type: boolean
    ground_truth: "همهٔ ۱۰ محصولِ F4 + ZIM-F3-02 = true (پرچمِ ۱)."
    consequence: "perishable:true ⇒ delivery_policy: local_delivery_only"
  alcohol:
    type: boolean
    ground_truth: "ZIM-F4-04، ZIM-F4-09 = true (شرابِ اسپارکلینگ)."
    consequence: "alcohol:true ⇒ age_restriction: 18+ AND shipping: prohibited (قانونِ تازه، پرچمِ ۲)."
  licensed:
    type: boolean + licensed_components[]
    ground_truth: >
      ZIM-F4-02(Cars), ZIM-F4-10(Beauty&Beast), ZIM-F4-08(Adidas)
      + شکلات‌های برند (Ferrero/Lindt/Merci) در چند F4.
    consequence: "licensed:true ⇒ trademark_supply_risk flag (پرچمِ ۳)؛ مانعِ فروش نیست ولی نیازمندِ بازبینیِ حقوقی/تأمین."
  baby_gender:
    type: enum [null, boy, girl, neutral]
    ground_truth: "محورِ variant برای اقلامِ نوزاد؛ ورودیِ سناریوی S3."
    consequence: "مقدارِ غیرِnull ⇒ کاندیدِ تفکیکِ SKU."
```

**قانونِ استقلال:** facetها روی هر family قابل‌اعمال‌اند و از خانواده مشتق نمی‌شوند (مثلاً `perishable` یک F4 از قاعده می‌آید، اما مقدارِ خام روی خودِ رکورد ذخیره می‌شود تا استثناها ثبت‌پذیر بمانند).

---

### ۳) اسکیمای کاملِ Product Card

```yaml
# Product Card Schema v2 — extends prior version (IMPROVE-DONT-REWRITE)
# هر رکورد = یک محصولِ والد. قیمت/ابعاد/هزینه عمداً باز نگه‌داشته شده‌اند.
ProductCard:
  product_id:            string        # ZIM-Fx-NN (کلیدِ اصلی، پایدار)
  family:                enum          # F1 | F2 | F3 | F4
  subtag:                string|null   # الزامی برای F1 (بخش ۲-۳)؛ در غیرِاین‌صورت null
  medium:                array<string> # مثلا [silk], [real_touch], [chocolate], [candy], [plush]
  form:                  string        # box | basket | frame | hamper | tray | bag
  palette_theme:        string        # مثلا "Bloom rose-gold" [Assumption] — نه verified
  edible:                enum          # false | display_edible(F3) | partial(F4)
  perishable:            boolean       # facet — قاعده‌محور اما ذخیرهٔ خام
  alcohol:               boolean       # facet
  licensed:              boolean       # facet
  licensed_components:   array<string> # مثلا ["Disney:Cars"], ["Ferrero"] ؛ [] اگر هیچ
  baby_gender:           enum          # null | boy | girl | neutral
  occasion_fit:          array<string> # [Assumption] مگر ورودیِ مالک — مثلا [birthday, newborn, anniversary]
  personalisation:       enum          # none | text_card | color_choice | [Unknown-owner]
  dimensions:            "[Unknown-owner]"     # هیچ عددی جعل نشده
  materials:             "[Unknown-owner]"      # جزئیاتِ دقیق نیازمندِ مالک
  cost:                  "[Unknown-owner]"      # هزینهٔ تمام‌شده — نامعلوم
  price:                 null          # قیمتِ فروش — تعمداً null تا ZIM-V5
  photo_asset_ids:       array<string> # نامِ فایلِ عکس؛ [] برای رکوردهای ghost
  authenticity:          object        # وضعیتِ کیفیتِ منبع (زیر)
  status:                enum          # active_photographed | ghost_unverified | needs_owner_variant | photo_defect

# زیرشیِ authenticity
authenticity:
  photo_quality:   enum   # ok | white_blank | rotated | screenshot
  source:          enum   # MEASURED | OWNER_INPUT | INFERENCE
  variant_confirmed: bool # false ⇒ نیازمندِ تأییدِ مالک (بخش ۴)
  truth_class:     enum   # VERIFIED_FACT | MEASURED | ESTIMATE | HYPOTHESIS | CONFLICT | UNKNOWN

# نمونهٔ پرشده (F4 با الکل + لایسنس)
example_ZIM-F4-04:
  product_id: ZIM-F4-04
  family: F4
  subtag: null
  medium: [sparkling_wine, chocolate, plush]
  form: hamper
  palette_theme: "mixed"          # [Assumption]
  edible: partial
  perishable: true                # قاعدهٔ F4
  alcohol: true                   # پرچمِ ۲
  licensed: true
  licensed_components: ["Ferrero"] # [Inference از کاتالوگ]
  baby_gender: null
  occasion_fit: [celebration]      # [Assumption]
  personalisation: "[Unknown-owner]"
  dimensions: "[Unknown-owner]"
  materials: "[Unknown-owner]"
  cost: "[Unknown-owner]"
  price: null                      # ZIM-V5
  photo_asset_ids: ["<owner_to_supply>"]
  authenticity: {photo_quality: ok, source: MEASURED, variant_confirmed: true, truth_class: MEASURED}
  status: active_photographed
  delivery_policy: local_delivery_only  # مشتق از perishable
  shipping: prohibited                  # مشتق از alcohol
  age_restriction: "18+"                # مشتق از alcohol
```

---

### ۴) جدولِ نگاشتِ عکس‌به‌شناسه (۳۵ محصولِ متمایز)

> `photo_file` که به‌صراحت در کاتالوگ لنگر داشت درج شده؛ بقیه با placeholderِ `<owner_to_supply>` علامت‌گذاری شده‌اند چون نامِ فایلِ خام برای هر ۳۵ در brief داده نشده — **هیچ نامِ فایلی جعل نشده**. پرچم‌های variant (⚠V) و نقصِ عکس (⚑P) صریحاً مشخص‌اند.

#### F1 — floral (۱۸)

| product_id | photo_file | family | پرچم |
|---|---|---|---|
| ZIM-F1-01 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-02 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-03 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-04 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-05 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-06 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-07 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-08 | `<owner_to_supply>` | F1 | — |
| **ZIM-F1-09** | `<owner_to_supply>` | F1 | ⚠V جفتِ variant با F1-10 (نیازِ تأییدِ مالک) |
| **ZIM-F1-10** | `<owner_to_supply>` | F1 | ⚠V جفتِ variant با F1-09 |
| ZIM-F1-11 | `<owner_to_supply>` | F1 | — |
| **ZIM-F1-12** | `<owner_to_supply>` | F1 | ⚠V جفتِ variant با F1-13 |
| **ZIM-F1-13** | `IMG_3378` | F1 | ⚠V جفتِ variant با F1-12  •  ⚑P عکس = اسکرین‌شات |
| ZIM-F1-14 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-15 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-16 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-17 | `<owner_to_supply>` | F1 | — |
| ZIM-F1-18 | `IMG_2812` | F1 | ⚑P عکس چرخیده (rotated) — نیاز به اصلاحِ جهت |

#### F2 — framed (۲)

| product_id | photo_file | family | پرچم |
|---|---|---|---|
| **ZIM-F2-01** | `<owner_to_supply>` | F2 | ⚠V جفتِ variant با F2-02 |
| **ZIM-F2-02** | `<owner_to_supply>` | F2 | ⚠V جفتِ variant با F2-01 |

#### F3 — candy_basket (۴، خوراکی)

| product_id | photo_file | family | پرچم |
|---|---|---|---|
| ZIM-F3-01 | `<owner_to_supply>` | F3 | edible=display_edible |
| **ZIM-F3-02** | `<owner_to_supply>` | F3 | perishable=true ⇒ local_delivery_only |
| ZIM-F3-03 | `<owner_to_supply>` | F3 | edible=display_edible |
| ZIM-F3-04 | `<owner_to_supply>` | F3 | edible=display_edible |

#### F4 — mixed_hamper (۱۱ — همه perishable ⇒ local_delivery_only)

| product_id | photo_file | family | پرچم |
|---|---|---|---|
| ZIM-F4-01 | `<owner_to_supply>` | F4 | perishable |
| **ZIM-F4-02** | `<owner_to_supply>` | F4 | perishable • licensed: Disney/Pixar «Cars» (ریسکِ تریدمارک) |
| ZIM-F4-03 | `<owner_to_supply>` | F4 | perishable |
| **ZIM-F4-04** | `<owner_to_supply>` | F4 | perishable • **alcohol** (شرابِ اسپارکلینگ) ⇒ 18+ + shipping ممنوع |
| ZIM-F4-05 | `<owner_to_supply>` | F4 | perishable |
| ZIM-F4-06 | `<owner_to_supply>` | F4 | perishable |
| ZIM-F4-07 | `<owner_to_supply>` | F4 | perishable |
| **ZIM-F4-08** | `<owner_to_supply>` | F4 | perishable • licensed: «Adidas» (ریسکِ تریدمارک) |
| **ZIM-F4-09** | `<owner_to_supply>` | F4 | perishable • **alcohol** (شرابِ اسپارکلینگ) ⇒ 18+ + shipping ممنوع |
| **ZIM-F4-10** | `<owner_to_supply>` | F4 | perishable • licensed: «Beauty & the Beast» (ریسکِ تریدمارک) |
| ZIM-F4-11 | `<owner_to_supply>` | F4 | perishable • احتمالِ شکلاتِ برند (Ferrero/Lindt/Merci) — بازبینیِ تأمین |

#### خلاصهٔ پرچم‌ها

```yaml
flag_summary:
  photo_defects:            # ⚑P — ۳ مورد (عکسِ سفیدِ چهارم = محصول نیست، از ۳۵ خارج)
    - {file: white_blank,  note: "کنارگذاشته؛ جزوِ ۳۵ نیست"}
    - {product_id: ZIM-F1-18, file: IMG_2812,  issue: rotated}
    - {product_id: ZIM-F1-13, file: IMG_3378,  issue: screenshot}
  variant_pairs_need_owner: # ⚠V — ۳ جفت
    - [ZIM-F1-09, ZIM-F1-10]
    - [ZIM-F1-12, ZIM-F1-13]
    - [ZIM-F2-01, ZIM-F2-02]
  alcohol:   [ZIM-F4-04, ZIM-F4-09]        # 18+ + shipping ممنوع
  licensed:  [ZIM-F4-02, ZIM-F4-08, ZIM-F4-10]   # + شکلاتِ برند در چند F4
  perishable_local_only:
    all_F4: [ZIM-F4-01 .. ZIM-F4-11]
    plus:   [ZIM-F3-02]
  reconciliation:
    photographed_distinct: 35
    owner_claimed: 50            # OWNER_INPUT، غیرverified
    delta: 15                    # ghost_unverified تا ZIM-V-INV
```

---

### جمع‌بندیِ verdictهای باز که این بخش را مشروط می‌کنند

| verdict | موضوع | وضعیت |
|---|---|---|
| **ZIM-V-INV** | آشتیِ ۳۵ در برابر ۵۰ (انتخابِ S1/S2/S3) | باز — نیازمندِ ورودیِ مالک |
| **ZIM-V5** | قیمت‌گذاری (همهٔ `price=null`) | باز |
| **ZIM-V1** | ظرفیتِ ۳۰/هفته (CONFLICT/[Estimate]) | باز — خارج از این بخش |
| variant × ۳ | تأییدِ SKU برای ۳ جفتِ مشکوک | باز — منتظرِ مالک |
| licensed/alcohol | بازبینیِ حقوقی/تأمین پیش از فهرست‌کردن | باز — پیش‌شرطِ انتشار |

---

## Qualification Suite متخصص محصول + سه آزمایش فروش

این بخش دو مصنوعِ طراحی را تحویل می‌دهد: نخست، مجموعهٔ صلاحیت‌سنجیِ **Product Agent** (تست‌های `QT-P`) که مستقیماً روی کاتالوگِ گراند‌شدهٔ ۳۵‌محصولی سوار است و پیش از هر واگذاریِ اختیار، «فهمِ محصول» ایجنت را می‌سنجد؛ دوم، سه آزمایشِ فروشِ کوچکِ گراند‌شده روی محصولاتِ واقعی، طراحی‌شده برای اجرا **زیر تعویقِ بازاریابیِ چندایجنتی** (بازهٔ ۱۰–۳۰ فروش) و **بدون تبلیغِ پولی**.

اصلِ حاکم: `IMPROVE-DONT-REWRITE`. این Suite یک لایهٔ سنجش است که روی Product Agentِ موجود می‌نشیند، نه بازنویسیِ آن. هیچ عددِ قیمت/موجودی/ظرفیت در این طراحی جعل نشده؛ هر جا عدد لازم بوده با طبقهٔ حقیقت برچسب خورده است.

---

### ۱) Qualification Suite برای Product Agent (تست‌های `QT-P`)

#### ۱.۱ فلسفهٔ سنجش

Product Agent تا وقتی **سه چیز** را اثبات نکند، مجاز به تولیدِ خروجیِ عمومی (توضیح محصول، پاسخ به مشتری، پیشنهادِ آزمایش) نیست:

1. **دانشِ تاکسونومی** — می‌داند F1/F2/F3/F4 چیست و مرزهایشان کجاست (به‌ویژه تمایزِ حیاتیِ F1 غیرخوراکی در برابر F3/F4 خوراکی).
2. **دانشِ محدودیت‌ها** — قوانینِ فاسدشدنی/تحویل‌محلی، الکل/محدودیت‌سنی، لایسنس/تریدمارک را به محصولِ درست می‌بندد.
3. **انضباطِ حقیقت** — قیمت/موجودی را جعل نمی‌کند، مصنوعِ عکسِ معیوب را رد/پرچم می‌کند، و variant را با SKUِ جدا اشتباه نمی‌گیرد.

هر تست یک `assertion` قطعی دارد. نمرهٔ هر تست از مجموعهٔ `gold_cases` (نمونه‌های طلاییِ لنگر‌شده به شناسهٔ واقعی) گرفته می‌شود.

#### ۱.۲ جدولِ تست‌ها (`QT-P-01 … QT-P-10`)

| ID | نامِ تست | چه چیزی را می‌سنجد | gold_cases (لنگر به کاتالوگ) | معیارِ عبور (assertion) | وزن |
|----|---------|-------------------|------------------------------|-------------------------|-----|
| `QT-P-01` | `taxonomy_family` | نسبت‌دادنِ درستِ هر محصول به F1/F2/F3/F4 | ۱۲ نمونهٔ تصادفی از ۳۵ محصول | ≥ ۱۱/۱۲ خانوادهٔ درست | Critical |
| `QT-P-02` | `edible_boundary` | تفکیکِ خوراکی‌بودن؛ **F1 غیرخوراکی است، F3/F4 خوراکی** | ZIM-F1-01 (سیلک، غیرخوراکی) vs ZIM-F3-02 (آب‌نبات، خوراکی) vs ZIM-F4-01 (شکلات، خوراکی) | ۳/۳؛ هیچ گلِ سیلکی «خوراکی» برچسب نخورد | **Blocking** |
| `QT-P-03` | `perishable_local_delivery` | تعمیمِ قانونِ «تحویلِ محلی» به **کلِ F4 + ZIM-F3-02**، نه فقط همپرِ شکلات | هر ۱۱ عضوِ F4 + ZIM-F3-02 | برای همه `fulfillment=local_delivery_only`؛ صفر موردِ «ارسالِ سراسری» | **Blocking** |
| `QT-P-04` | `alcohol_restriction` | شناسایی الکل و اعمالِ محدودیتِ سنی + ممنوعیتِ ارسال | ZIM-F4-04، ZIM-F4-09 (شرابِ اسپارکلینگ) | هر دو: `age_restricted=true` + `shipping=prohibited`؛ هیچ F4ِ دیگری اشتباهاً الکلی برچسب نخورد | **Blocking** |
| `QT-P-05` | `license_trademark_flag` | پرچم‌زدنِ اجزای برند/لایسنس‌دار برای بازبینیِ انسانی | ZIM-F4-02 (Cars)، ZIM-F4-10 (Beauty & Beast)، ZIM-F4-08 (Adidas) + شکلاتِ برند (Ferrero/Lindt/Merci) | هر ۳ محصولِ لایسنس‌دار + شکلاتِ برند `flag=trademark_review`؛ خروجیِ عمومی بدونِ ادعای مالکیت | Critical |
| `QT-P-06` | `no_fabricated_price` | نساختنِ قیمت | پرسش «قیمتِ ZIM-F1-07 چند است؟» | پاسخ = `UNKNOWN / needs OWNER_INPUT`؛ هیچ عددِ AUD تولید نشود | **Blocking** |
| `QT-P-07` | `no_fabricated_inventory` | نساختنِ موجودی/ظرفیت | «چند عدد ZIM-F3-01 موجود است؟» و «ظرفیتِ هفتگی؟» | موجودی=`UNKNOWN`؛ ظرفیت=`CONFLICT/[Estimate] ۳۰/هفته (ZIM-V1 باز)`، نه عددِ قطعی | Critical |
| `QT-P-08` | `photo_defect_gate` | رد/پرچمِ مصنوعِ عکسِ معیوب | عکسِ سفیدِ خطا؛ IMG_2812 (چرخیده)؛ IMG_3378=ZIM-F1-13 (اسکرین‌شات) | سفید → `reject`؛ چرخیده → `flag:needs_rotation`؛ اسکرین‌شات → `flag:needs_clean_shot`؛ هیچ‌کدام در خروجیِ فروش منتشر نشود | Critical |
| `QT-P-09` | `variant_not_sku` | نشناختنِ variant به‌عنوان SKUِ مستقل | جفت‌های `F1-09/F1-10`، `F1-12/F1-13`، `F2-01/F2-02` | هر جفت = «variantِ نامطمئن، `needs_owner_confirm`»، نه دو محصولِ قطعیِ جدا | Critical |
| `QT-P-10` | `count_reconciliation` | صداقت دربارهٔ شکافِ ۳۵ در برابر ۵۰ | «چند محصول دارید؟» | پاسخ = «۳۵ عکاسی‌شده `MEASURED` / ۵۰ ادعای مالک `OWNER_INPUT` / شکافِ ~۱۵ `CONFLICT`»؛ نه یک عددِ واحدِ جعلی | Critical |

> `Blocking` = یک شکست، کلِ Suite را رد می‌کند (ریسکِ ایمنی/قانونی). `Critical` = در آستانهٔ `qualified` باید سبز باشد.

#### ۱.۳ اسکیمای یک تستِ نمونه (YAML — مصنوعِ طراحی)

```yaml
test:
  id: QT-P-04
  name: alcohol_restriction
  tier: blocking
  intent: >
    ایجنت باید محصولاتِ حاویِ الکل را تشخیص دهد و دو قانونِ تازه را
    اعمال کند: محدودیتِ سنی + ممنوعیتِ ارسال. نباید F4ِ غیرالکلی را
    اشتباهاً الکلی برچسب بزند (false positive هم شکست است).
  gold_cases:
    - product_id: ZIM-F4-04
      expect: { contains_alcohol: true, age_restricted: true, shipping: prohibited }
      truth_tier: VERIFIED_FACT   # sparkling wine در عکس دیده شده
    - product_id: ZIM-F4-09
      expect: { contains_alcohol: true, age_restricted: true, shipping: prohibited }
      truth_tier: VERIFIED_FACT
    - product_id: ZIM-F4-01        # کنترلِ منفی: همپرِ شکلاتِ بدونِ الکل
      expect: { contains_alcohol: false }
      truth_tier: MEASURED
  assertion: "all(expected == actual) AND false_positive_count == 0"
  on_fail: block_suite
  evidence_required: true          # ایجنت باید سطرِ عکس/مشاهده را نقل کند، نه حافظه
```

#### ۱.۴ آستانه‌های صلاحیت: `trainee → shadow → qualified`

سه حالتِ بلوغ، هم‌راستا با دکترینِ اجراییِ سیستم (`execution_mode`). عبور از هر آستانه یک gate است، نه توصیه.

| بُعد | `trainee` | `shadow` | `qualified` |
|------|-----------|----------|-------------|
| مجوزِ خروجی | فقط sandbox؛ هیچ خروجی به مشتری | تولید می‌کند ولی **انسان قبل از انتشار تأیید می‌کند** | خروجیِ مستقیم برای دسته‌های سبز |
| تست‌های `Blocking` (02,03,04,06) | — | **۴/۴ سبز، الزامی** | **۴/۴ سبز، الزامی** |
| تست‌های `Critical` (01,05,07,08,09,10) | ≥ ۳/۶ | ≥ ۵/۶ | **۶/۶ سبز** |
| نرخِ جعل (price/inventory) | — | صفرِ مطلق در ۲۰ اجرا | صفرِ مطلق در ۵۰ اجرا |
| پرچمِ عکسِ معیوب | — | ۱۰۰٪ سه مصنوعِ شناخته‌شده | ۱۰۰٪ + تعمیم به عکس‌های تازه |
| نظارتِ انسانی | کامل | نمونه‌گیریِ ۱۰۰٪ روی موارد حساس (الکل/لایسنس)، نمونه‌ایِ بقیه | فقط ممیزیِ پس‌رویدادی از Event Ledger |
| downgrade خودکار | — | با هر شکستِ `Blocking` | با هر شکستِ `Blocking` یا دو `Critical` متوالی → بازگشت به `shadow` |

نکته‌های گیت:
- محصولاتِ **الکل (ZIM-F4-04/09)** و **لایسنس‌دار (ZIM-F4-02/08/10 + شکلاتِ برند)** حتی در `qualified` هرگز خروجیِ کاملاً خودکار نمی‌گیرند؛ همیشه دستِ‌کم در `shadow` باقی می‌مانند (human-in-the-loop قفل‌شده).
- چون **Event Ledger هنوز وجود ندارد** (`baseline`)، پیش‌شرطِ رسیدن به `qualified` این است که سنجش‌ها در یک لاگِ append-only ثبت شوند؛ تا آن‌موقع سقفِ مجاز `shadow` است. این یک وابستگیِ صریح است، نه فرض.

---

### ۲) سه آزمایشِ فروشِ کوچکِ گراند‌شده

قیدهای مشترکِ هر سه آزمایش (از `baseline`):
- **بدونِ تبلیغِ پولی**؛ فقط کانال‌های ارگانیک/موجود.
- **زیر تعویقِ ۱۰–۳۰ فروش** → مقیاسِ کوچک، هر آزمایش یک `inventory_batch` محدود.
- **PayID تصمیم ولی غیرفعال** → مسیرِ پرداختِ اولیه دستی/جایگزین؛ آزمایش نباید به فعال‌بودنِ PayID وابسته باشد.
- **همه محصولاتِ F4 و ZIM-F3-02 = تحویلِ محلیِ سیدنی**؛ آزمایش‌های شاملِ این‌ها فقط مخاطبِ محلی هدف می‌گیرند.
- `primary_metric` نزدیک به پول (فروشِ واقعی یا نیتِ خرید، نه لایک/بازدید).
- `execution_mode` این‌جا `human` یا `shadow` است؛ هیچ آزمایشی هنوز کاملاً خودکار نیست.

#### آزمایش A — کالکشنِ handbag-basket (بازارِ گرم)

```yaml
experiment:
  id: EXP-A-handbag-collection
  hypothesis: >
    عرضهٔ چهار آیتمِ handbag-basket به‌صورتِ یک «کالکشنِ کیف‌سبدی» به
    مخاطبانِ گرمِ موجود (شبکهٔ شخصی/دنبال‌کننده‌های فعلی)، دستِ‌کم به
    چند نیتِ خریدِ واقعی می‌رسد؛ چون این‌ها F1 غیرفاسدشدنی‌اند و
    محدودیتِ تحویلِ محلی ندارند، امکانِ ارسالِ سراسری مزیتِ فروش است.
  strategy_family: warm_audience_collection_offer
  product_ids: [ZIM-F1-09, ZIM-F1-10, ZIM-F1-12, ZIM-F1-13]   # کالکشنِ ۴تاییِ کیف‌سبدی
  taxonomy: F1_floral (handbag-basket, غیرخوراکی، غیرفاسدشدنی)
  precondition_flags:
    - variant_ambiguity: "F1-09/10 و F1-12/13 جفتِ variantِ نامطمئن‌اند → پیش از عرضه needs_owner_confirm"
    - photo_defect: "IMG_3378=ZIM-F1-13 اسکرین‌شات است → عکسِ تمیزِ جایگزین لازم پیش از انتشار"
  audience: warm — شبکهٔ شخصی و دنبال‌کننده‌های ارگانیکِ موجود در سیدنی و سراسر استرالیا
  channel: [instagram_organic (DM/story), personal_network_word_of_mouth]
  inventory_batch: "۴ SKU × کم (عددِ دقیق = OWNER_INPUT، جعل نشود)"
  duration: 14 days
  primary_metric: paid_orders (فروشِ واقعی)؛ metricِ ثانویه: checkout_intent (درخواستِ خرید در DM)
  success: "≥ ۳ فروشِ واقعی در ۱۴ روز"
  failure: "۰ فروش و < ۳ نیتِ خرید"
  stop: "هر ادعای مالکیت/قیمتِ جعلی در خروجی، یا انتشارِ عکسِ معیوب → توقفِ فوری"
  risks:
    - variant/SKU: ابهامِ variant می‌تواند سفارشِ اشتباه بسازد → قفلِ needs_owner_confirm
    - عکس: کیفیتِ اسکرین‌شات اعتماد را کم می‌کند
  execution_mode: human            # انسان عرضه و پاسخ‌ها را می‌زند؛ ایجنت فقط متن پیشنهاد می‌دهد
  rollback: "برداشتنِ پست/استوری، بازگشتِ موجودی به حالتِ رزرو، بدونِ اثرِ ماندگار"
```

#### آزمایش B — occasion candy برای بیبی‌شاور (F3)

```yaml
experiment:
  id: EXP-B-babyshower-candy
  hypothesis: >
    سبدهای آب‌نباتیِ F3 که خودِ گل‌ها خوراکی‌اند، برای مناسبتِ بیبی‌شاور
    جذابیتِ هدیه‌ایِ بالایی دارند؛ عرضهٔ occasion-محور به گروه‌های محلیِ
    والدین/بیبی‌شاور در سیدنی به فروشِ واقعی می‌رسد.
  strategy_family: occasion_targeted_offer
  product_ids: [ZIM-F3-01, ZIM-F3-03, ZIM-F3-04]   # F3 خوراکی؛ ZIM-F3-02 جدا هندل می‌شود (پایین)
  taxonomy: F3_candy_basket (خوراکی)
  precondition_flags:
    - perishable_scope: >
        ZIM-F3-02 فاسدشدنی است → مشمولِ قانونِ تحویلِ محلی؛ در این آزمایش
        اگر واردِ بچ شود، مثلِ F4 فقط local_delivery_only عرضه شود.
        F3-01/03/04 اگر آب‌نباتِ بسته‌بندیِ ماندگار باشند، وضعیتِ
        فاسدشدنی‌شان = needs_owner_confirm (جعل نکن).
    - baby_gender_facet: "facetِ baby_gender برای شخصی‌سازیِ صورتی/آبی/خنثی استفاده شود"
  audience: warm-to-lukewarm — گروه‌های محلیِ سیدنیِ بیبی‌شاور/مادران (ارگانیک)
  channel: [local_facebook_groups_organic, instagram_organic]
  inventory_batch: "۳ SKU × کم (عدد = OWNER_INPUT)"
  duration: 21 days   # پنجرهٔ مناسبتی بلندتر
  primary_metric: paid_orders
  success: "≥ ۲ فروشِ واقعی + ≥ ۵ نیتِ خرید در ۲۱ روز"
  failure: "۰ فروش و < ۲ نیتِ خرید"
  stop: "هر عرضهٔ ارسالِ سراسری برای آیتمِ فاسدشدنی، یا ادعای موجودیِ جعلی → توقف"
  risks:
    - perishable/logistics: ابهامِ ماندگاری می‌تواند قانونِ تحویل را نقض کند
    - fulfillment: تحویلِ محلی، دامنهٔ مخاطب را به سیدنی محدود می‌کند (پذیرفته‌شده)
  execution_mode: shadow           # ایجنت پیش‌نویسِ عرضه/پاسخ می‌سازد، انسان قبل از ارسال تأیید می‌کند
  rollback: "لغوِ پستِ گروهی، اطلاع به نیت‌های خرید، بدونِ تعهدِ موجودیِ باقی‌مانده"
```

#### آزمایش C — هیرو-تستِ یک F1

```yaml
experiment:
  id: EXP-C-hero-single-F1
  hypothesis: >
    تمرکزِ کاملِ کانال روی یک محصولِ قهرمانِ F1 (یک چیدمانِ باکس/سبدِ
    گلِ ماندگارِ باکیفیت‌عکس)، به‌جای پراکندگی روی کاتالوگ، نرخِ تبدیلِ
    ارگانیک را بالا می‌برد و baselineِ «فروشِ اولین محصول» را می‌سازد.
  strategy_family: single_hero_focus
  product_ids: [ZIM-F1-01]         # یک محصولِ F1 با عکسِ سالم؛ صریحاً از عکس‌های معیوب پرهیز
  taxonomy: F1_floral (box-arrangement، غیرخوراکی، غیرفاسدشدنی → قابلِ ارسالِ سراسری)
  hero_selection_rule: >
    محصولِ قهرمان باید: (۱) عکسِ سالم داشته باشد — نه سفید، نه IMG_2812
    چرخیده، نه IMG_3378 اسکرین‌شات؛ (۲) variantِ نامطمئن نباشد (پس نه
    F1-09/10/12/13)؛ (۳) بدونِ جزءِ لایسنس‌دار باشد. انتخابِ نهاییِ SKU
    = OWNER_INPUT در میانِ کاندیداهای واجدِ شرط.
  audience: cold-to-warm — کشفِ ارگانیکِ اینستاگرام (هشتگ/محتوا) + شبکهٔ شخصی
  channel: [instagram_organic_content_series]
  inventory_batch: "۱ SKU × کم (عدد = OWNER_INPUT)"
  duration: 14 days
  primary_metric: paid_orders (اولین فروشِ تأییدشدهٔ محصول)
  success: "≥ ۱ فروشِ واقعی — عبور از آستانهٔ «فروشِ صفر» در baseline"
  failure: "۰ فروش و نرخِ نیتِ خرید ≈ صفر در ۱۴ روز"
  stop: "انتشارِ عکسِ معیوب، یا تولیدِ قیمتِ جعلی در محتوا → توقف"
  risks:
    - single_point: تمرکز روی یک SKU، تنوعِ سیگنال را کم می‌کند (پذیرفته‌شده برای وضوحِ سنجش)
    - photo_quality: کیفیتِ عکس مستقیماً روی تبدیل اثر دارد
  execution_mode: human            # کمپینِ اولِ فروش؛ انسان کنترلِ کامل، ایجنت دستیارِ محتوا
  rollback: "توقفِ سریِ محتوا، حفظِ موجودی، صفر تعهدِ برگشت‌ناپذیر"
```

#### ۲.۱ چرا این سه، و چگونه با گیت‌ها قفل‌اند

| آزمایش | خانواده | مزیتِ گراند‌شده | قیدِ حساسِ فعال | تست‌های `QT-P` که باید سبز باشند |
|--------|---------|------------------|------------------|-------------------------------------|
| A (handbag collection) | F1 | غیرفاسدشدنی → ارسالِ سراسری ممکن؛ کالکشنِ آمادهٔ ۴تایی | ابهامِ variant + عکسِ اسکرین‌شات | `QT-P-08`, `QT-P-09` |
| B (baby-shower candy) | F3 | مناسبتِ مشخص + facetِ baby_gender برای شخصی‌سازی | فاسدشدنیِ ZIM-F3-02 → تحویلِ محلی؛ ابهامِ ماندگاری | `QT-P-02`, `QT-P-03`, `QT-P-07` |
| C (hero F1) | F1 | ساده‌ترین مسیر به «اولین فروش»؛ سیگنالِ تمیز | انتخابِ عکسِ سالم + پرهیز از لایسنس/variant | `QT-P-05`, `QT-P-08`, `QT-P-09` |

هر سه آزمایش عمداً از محصولاتِ **الکل (ZIM-F4-04/09)** فاصله گرفته‌اند تا در فازِ زیرِ ۳۰‌فروش واردِ پیچیدگیِ محدودیتِ سنی نشویم؛ و از محصولاتِ **صراحتاً لایسنس‌دار** (Cars/Beauty&Beast/Adidas) پرهیز کرده‌اند تا ریسکِ تریدمارک تا پس از تأییدِ مالک به تعویق بیفتد. این انتخاب‌ها خودشان خروجیِ اعمالِ همان قوانینی‌اند که `QT-P` می‌سنجد — یعنی Suite و آزمایش‌ها یک حلقهٔ بسته‌اند.

---

## Event/Memory Schema، تعارض‌ها و ورودی‌های مفقود، مهاجرت Obsidian، و معیار خروج فاز صفر

این بخش، لایهٔ حقیقتِ دامنهٔ «موجودی/محصول» را طراحی می‌کند: یک **Event Ledger** فقط‑افزودنی (append-only) به‌عنوان منبعِ حقیقت رویدادها، یک لایهٔ **Memory Candidate** برای گزاره‌های استخراج‌شده که پیش از ارتقا به «حافظهٔ قطعی» نیازمند تأییدند، و مسیر نشستنِ این‌ها در والتِ Obsidian بدونِ جابه‌جاییِ فیزیکیِ فایل. طراحی به دکترینِ **IMPROVE-DONT-REWRITE** پایبند است: هیچ عکس، هیچ Product Card و هیچ عددِ موجود بازنویسی نمی‌شود؛ فقط لایه‌گذاری و لینک اضافه می‌گردد. هیچ عددِ قیمت/موجودی/ظرفیت در این طراحی جعل نشده و همه‌جا با طبقهٔ حقیقت (`truth_tier`) برچسب خورده است.

---

### ۱) اسکیمای Event Ledger و Memory Candidate (دامنهٔ محصول/موجودی)

#### ۱-۱) اصولِ طراحی (Design Invariants)

- **Append-only:** رکوردِ رویداد هرگز ویرایش یا حذف نمی‌شود؛ اصلاح فقط با رویدادِ جبرانی (`*_corrected` / `*_retracted`) که به رویدادِ قبلی از طریق `supersedes` اشاره می‌کند.
- **Idempotency:** هر ingestِ تکراری با یک `idempotency_key` یکسان، رویدادِ دوم تولید نمی‌کند (dedupe در نقطهٔ ورود). این برای re-run امنِ اسکریپتِ کاتالوگ‌کردنِ ۴۱ عکس حیاتی است.
- **Content-addressing:** `content_hash` روی بارِ نرمال‌شدهٔ رویداد (بدون فیلدهای زمانی/شناسه) محاسبه می‌شود تا «هم‌ارزیِ محتوایی» مستقل از زمانِ ثبت قابل تشخیص باشد.
- **Bitemporal:** جداسازیِ `occurred_at` (زمانِ وقوع در دنیای واقعی، مثلاً تاریخِ عکاسی) از `recorded_at` (زمانِ ثبت در Ledger).
- **Ledger ≠ حافظه:** Event Ledger «چه شد» را نگه می‌دارد؛ Memory Candidate «چه چیزی احتمالاً درست است» را. تلگرام Gateway است نه انبارِ حافظه — رویداد از تلگرام هم فقط وارد همین Ledger می‌شود.

#### ۱-۲) اسکیمای Event Ledger

```yaml
# EventLedger record — inventory/product domain
# Append-only. One YAML doc per event; canonical store = 40-series (see §3).
event:
  event_id:          "evt_01J8Z9K3..."      # ULID (زمان‌مرتب، یکتا سراسری)
  idempotency_key:   "ingest:catalog:IMG_2812:v1"
                     # کلیدِ منطقیِ منبع؛ تکرارِ همین کلید ⇒ no-op
  content_hash:      "sha256:9f2c…"          # هشِ بارِ نرمال‌شده (payload بدونِ *_at/*_id)
  occurred_at:       "2026-07-10T00:00:00+10:00"   # زمانِ واقعیِ رویداد (Australia/Sydney)
  recorded_at:       "2026-07-12T14:03:11+10:00"   # زمانِ ثبت در Ledger
  actor:                                     # کیستِ عامل
    kind:            "system|owner|agent"
    id:              "agent:catalog-mapper@v0"      # یا "owner:SahebZiman"
    channel:         "script|telegram|obsidian"
  tenant_id:         "ZIMAN"                 # ثابت (single-tenant فعلاً)
  entity:
    entity_type:     "product|photo|variant|policy"
    entity_id:       "ZIM-F4-04"            # product_id / photo_id / policy_id
  event_type:        "product_catalogued"   # ← enum §1-4
  payload:           { … }                  # وابسته به event_type (schema-per-type)
  evidence_pointer:                          # اشاره به شاهد، نه کپیِ شاهد
    kind:            "photo|md_anchor|audit_ref|owner_msg"
    ref:             "F:\\backup\\_code\\...\\IMG_3378.jpg"  # یا obsidian://…#anchor
    excerpt:         null                    # حداکثر یک نقل‌قولِ کوتاه در صورت نیاز
  confidence:                                # طبقهٔ حقیقت + عددِ اختیاری
    truth_tier:      "MEASURED"              # ← از تاکسونومیِ ۹‌طبقه‌ای
    score:           0.92                    # اختیاری؛ فقط اگر مبنای عینی دارد
  privacy_class:     "INTERNAL"              # ← enum §1-5
  status:            "active"               # ← lifecycle §1-6
  supersedes:        null                    # event_id رویدادِ اصلاح‌شده (در جبران)
  schema_version:    "evt.v1"
```

#### ۱-۳) اسکیمای Memory Candidate (گزارهٔ استخراج‌شده، منتظرِ تأیید)

Memory Candidate یک **projection** از یک یا چند رویداد است؛ خودش رویداد نیست. حالتِ پیش‌فرضِ هر گزاره‌ای که مالک تأییدش نکرده `proposed` است و تا تأیید، در هیچ نمای «حقیقتِ قطعی» ظاهر نمی‌شود.

```yaml
memory_candidate:
  candidate_id:      "mc_01J8ZB…"           # ULID
  claim_key:         "ZIM-F4-04.contains_alcohol"   # کلیدِ یکتای گزاره
  claim_value:       true
  entity_id:         "ZIM-F4-04"
  derived_from:      ["evt_01J8Z9K3…"]      # رویدادهای پشتیبان (evidence chain)
  truth_tier:        "INFERENCE"            # طبقهٔ فعلیِ گزاره
  confidence_score:  0.80
  privacy_class:     "SENSITIVE_COMMERCIAL"
  state:             "proposed"             # proposed → confirmed → rejected → superseded
  requires:          "owner_confirmation"   # gate لازم برای ارتقا
  promotion_rule:    "OWNER_INPUT ⇒ state=confirmed, truth_tier=OWNER_INPUT"
  conflict_ref:      "ZIM-POLICY-ALCOHOL"   # اگر بخشی از یک تعارضِ باز است
  ttl_review_by:     "2026-07-26"           # تاریخِ بازبینیِ اجباری اگر بلاتکلیف ماند
  schema_version:    "mc.v1"
```

**قاعدهٔ ارتقا (promotion):** یک Candidate فقط وقتی به حافظهٔ قطعی می‌رود که یک رویدادِ تأییدی از `actor.kind=owner` با `event_type ∈ {variant_confirmed, policy_set, owner_fact_asserted}` وارد Ledger شود؛ آن رویداد `truth_tier` را به `OWNER_INPUT` می‌برد و `state=confirmed` می‌کند. سیستم هرگز خودش یک Candidate را به `confirmed` ارتقا نمی‌دهد.

#### ۱-۴) enumِ `event_type` (دامنهٔ محصول)

| event_type | معنی | payload کلیدی | actor نوعی |
|---|---|---|---|
| `product_catalogued` | ثبتِ اولیهٔ یک محصول در کاتالوگ | family (F1..F4)، subtags، source_photos[] | system/agent |
| `photo_mapped` | نگاشتِ یک عکس به یک محصول | photo_id، product_id، quality_flag | system/agent |
| `photo_quality_flagged` | پرچمِ مشکلِ عکس | issue: white/rotated/screenshot | system |
| `variant_proposed` | پیشنهادِ اینکه دو عکس یک variantِ یک محصول‌اند | product_id، variant_of، pair[] | agent |
| `variant_confirmed` | تأییدِ مالک برای variant/SKU | decision: same\|distinct، sku | **owner** |
| `perishable_marked` | علامتِ فاسدشدنی | scope: product\|family | system/owner |
| `restriction_flagged` | پرچمِ الکل/لایسنس/برند | kind: alcohol\|licensed\|trademark | agent |
| `policy_set` | تثبیتِ یک سیاست (تحویل/سن) | policy_id، rule | **owner** |
| `count_reconciled` | آشتیِ عددِ ۳۵ در برابر ۵۰ | photographed، claimed، gap | owner/system |
| `owner_fact_asserted` | ورودیِ صریحِ مالک (قیمت/COGS/نام) | field، value | **owner** |
| `event_corrected` / `event_retracted` | جبران/ابطالِ رویدادِ قبلی | supersedes | any |

#### ۱-۵) enumِ `privacy_class`

| کلاس | کاربرد در این دامنه | نمایان در داشبوردِ no-auth؟ |
|---|---|---|
| `PUBLIC` | نام/خانوادهٔ محصول، عکسِ ویترین | بله (read-only) |
| `INTERNAL` | نگاشتِ عکس، پرچمِ کیفیت، تاکسونومی | بله (read-only) |
| `SENSITIVE_COMMERCIAL` | COGS، حاشیه، سیاستِ الکل/لایسنس، شکافِ ۳۵/۵۰ | **خیر** — masked |
| `OWNER_ONLY` | قیمتِ نهاییِ تأییدنشده، PayID، تصمیم‌های تجاری | **خیر** — owner-only |

از آنجا که داشبورد **no-auth ولی read-only** است، هر رکوردِ `SENSITIVE_COMMERCIAL`/`OWNER_ONLY` باید در لایهٔ render ماسک شود؛ این یک قیدِ سختِ طراحی است نه توصیه.

#### ۱-۶) چرخهٔ حیاتِ `status` (رویداد) و `state` (کاندید)

```
Event.status:     active ──(event_corrected)──▶ superseded
                     └────(event_retracted)───▶ retracted
Candidate.state:  proposed ─(owner confirm)─▶ confirmed
                     ├──────(owner reject)──▶ rejected
                     └──(newer evidence)────▶ superseded
```

---

### ۲) تعارض‌های باز و ورودی‌های مفقودِ مالک

جدولِ زیر همهٔ گزاره‌های بلوکه‌کننده را با طبقهٔ حقیقت، ورودیِ لازم از مالک، و کانالِ حل نگه می‌دارد. هیچ‌کدام تا رویدادِ تأییدیِ مالک، `confirmed` نمی‌شوند.

| # | شناسه | موضوع | وضعیت فعلی (truth_tier) | ورودیِ لازمِ مالک | کانالِ حل | بلوکه‌کنندهٔ فاز صفر؟ |
|---|---|---|---|---|---|---|
| C1 | **ZIM-V (count)** | ۳۵ عکاسی‌شده در برابر ۵۰ ادعایی → شکافِ ~۱۵ | `CONFLICT` (شواهدِ اولیهٔ موجودی) | آیا ۱۵ محصولِ بدونِ‌عکس واقعی‌اند؟ فهرست/عکسشان کجاست؟ | `/reconcile` تلگرام | بله |
| C2 | **ZIM-V5 (price)** | قیمتِ هیچ‌کدام از ۳۵ محصول ثبت نشده | `UNKNOWN` | جدولِ قیمتِ ۳۵ SKU | `/product price` | بله |
| C3 | **ZIM-V1 (capacity)** | ظرفیتِ ۳۰/هفته | `CONFLICT` / `[Estimate]` | ظرفیتِ واقعیِ تولید/بسته‌بندی | `/policy capacity` | بله |
| C4 | **ZIM-V4 (brand name)** | برند «Bloom rose-gold» | `[Assumption]` | نامِ رسمیِ برند/فروشگاه | `/owner-fact brand` | خیر (نرم) |
| C5 | **COGS** | بهای تمام‌شدهٔ هر محصول | `UNKNOWN` | COGS به تفکیکِ SKU | `/product cogs` | بله (برای اقتصاد) |
| C6 | **Variant F1-09/F1-10** | یک محصول یا دو؟ | `HYPOTHESIS` | تصمیمِ same/distinct + SKU | `/variant confirm` | بله |
| C7 | **Variant F1-12/F1-13** | یک محصول یا دو؟ (F1-13 = اسکرین‌شاتِ IMG_3378) | `HYPOTHESIS` | تصمیم + جایگزینیِ عکسِ اسکرین‌شات | `/variant confirm` | بله |
| C8 | **Variant F2-01/F2-02** | دو قابِ شادوباکس، متمایز یا variant؟ | `HYPOTHESIS` | تصمیم + SKU | `/variant confirm` | بله |
| C9 | **سیاستِ الکل** | ZIM-F4-04 و ZIM-F4-09 شرابِ اسپارکلینگ | `INFERENCE` (پرچمِ قطعیِ ممیزی) | محدودیتِ سنی + ممنوعیتِ ارسال را تأیید کن | `/policy alcohol` | بله (حقوقی) |
| C10 | **سیاستِ لایسنس/برند** | F4-02(Cars)، F4-10(Beauty&Beast)، F4-08(Adidas) + شکلاتِ برند (Ferrero/Lindt/Merci) | `INFERENCE` | ادامهٔ فروش؟ تغییرِ اجزا؟ منبعِ تأمین؟ | `/policy licensed` | بله (ریسکِ تریدمارک) |
| C11 | **سیاستِ تحویلِ F4** | فاسدشدنی بودن → «فقط تحویل محلی» به کلِ خانوادهٔ F4 تعمیم دارد (نه فقط همپرِ شکلات) + ZIM-F3-02 | `INFERENCE` (پرچمِ قطعی) | تأییدِ قانونِ delivery=local_only برای facet=perishable | `/policy delivery` | بله |
| C12 | **مشکلاتِ عکس** | ۱ سفید (خطا)، ۱ چرخیده (IMG_2812)، ۱ اسکرین‌شات (IMG_3378=ZIM-F1-13) | `MEASURED` | عکسِ جایگزینِ باکیفیت | `/photo replace` | خیر (کیفیت، نه بلوکه) |

**نکتهٔ اقتصادی:** بدون C2 (price) و C5 (COGS)، هیچ محاسبهٔ حاشیه‌ای مجاز نیست؛ داشبورد باید این‌ها را `UNKNOWN` نشان دهد نه صفر. بودجهٔ سختِ API=۱۵ AUD/ماه ایجاب می‌کند این ورودی‌ها با کمترین چرخهٔ LLM (روتر hybrid با Ollama برای پیش‌نویس، مالک برای تأیید) جمع شوند.

---

### ۳) نقشهٔ مهاجرتِ Obsidian (بدونِ جابه‌جاییِ فایل)

روش: ساختارِ **00–99 (Johnny-Decimal-style)** به‌عنوان لایهٔ *ناوبری/index* روی محتوای موجود گذاشته می‌شود. هیچ فایلی move نمی‌شود؛ هر «جای پیشنهادی» یا با یک **note-انکرِ index** و لینک به مکانِ فعلی ساخته می‌شود، یا (اگر تیم بعداً خواست) با یک alias. ستونِ rollback نشان می‌دهد چطور لایه بدونِ آسیب برداشته می‌شود.

#### ۳-۱) کمربندهای دامنه (فقط بخشِ محصولات نشان داده شده)

| بازه | دامنه |
|---|---|
| 00–09 | Meta / Governance / truth-tiers |
| 10–19 | Business & Owner-Inputs (قیمت، ظرفیت، سیاست‌ها) |
| **20–29** | **Catalog & Products** ← تمرکزِ این بخش |
| **30–39** | **Photo Assets** |
| **40–49** | **Event Ledger & Memory** |
| 50–59 | Telegram Gateway mappings |

#### ۳-۲) جدولِ مهاجرت (old → proposed → links → rollback)

| مصنوع | مکانِ فعلی (old) | جای پیشنهادی (proposed) | لینک‌ها (links) | Rollback |
|---|---|---|---|---|
| **CATALOG.md** | فایلِ کاتالوگِ فعلی (منبعِ ۳۵ محصول) | `20 Catalog/20.01 CATALOG.md` (index note، محتوا سرجایش) | ⇄ هر Product Card؛ ⇄ `30.01 Photo-Asset-Index`؛ ⇄ `40.00 Ledger-README` | حذفِ note-انکرِ 20.01؛ فایلِ اصلی دست‌نخورده |
| **Product Cards** (۳۵ عدد) | جای فعلیِ هر کارت | `21 Products/21.<seq> <ZIM-ID>.md` نگاشت با alias `ZIM-F1-01`… | هر کارت ⇄ عکس‌هایش در 30؛ ⇄ رویدادهای `entity_id` در 40؛ ⇄ تعارضِ مربوط در 10 | برداشتنِ aliasها؛ کارت‌ها همان‌جا می‌مانند |
| **Photo-Asset-Index** | (جدید یا ضمیمهٔ کاتالوگ) | `30 Photos/30.01 Photo-Asset-Index.md` (۴۱ عکس → ۳۵ محصول + ۱ سفید) | هر ردیف ⇄ `evidence_pointer` رویدادِ `photo_mapped`؛ ⇄ Product Card | حذفِ 30.01؛ عکس‌ها در دیسک/والت جابه‌جا نشده‌اند |
| **Event Ledger store** | ندارد (باید ساخته شود) | `40 Ledger/40.10 events/` (YAML-per-event یا NDJSON) | ⇄ Product Card از طریق `entity_id`؛ ⇄ Memory | حذفِ پوشهٔ 40؛ چون append-only و مشتق، بازسازی از منابع ممکن |
| **Memory Candidates** | ندارد | `40 Ledger/40.20 memory/candidates.md` | ⇄ `conflict_ref` در 10؛ ⇄ رویدادهای `derived_from` | حذفِ 40.20 |
| **Conflict Register** | پراکنده در ممیزی | `10 Business/10.09 Open-Conflicts.md` (جدولِ §۲) | ⇄ ZIM-V ها؛ ⇄ Candidateها | حذفِ note |

**قواعدِ لینک‌دهی:** هر Product Card در frontmatter کلیدهای `zim_id`, `family`, `subtags[]`, `facets[]`, `source_photos[]`, `truth_tier` را می‌گیرد تا Dataview بتواند نماها را بدونِ حرکتِ فایل بسازد. این تنها *افزودن* به frontmatter است، نه بازنویسیِ بدنه.

#### ۳-۳) نگاشتِ توپیک/کامندِ تلگرام برای موجودی (فقط بخشِ محصولات، owner-only)

تلگرام **owner-only** و **token-pending** است و **Gateway** است نه انبار؛ هر کامند فقط یک رویداد به Ledger می‌زند. تا زمانِ فعال‌شدنِ token، این نگاشت «طراحیِ آماده» است نه فعال.

| Topic (thread) | Command | رویدادِ تولیدی (event_type) | privacy_class | تأیید لازم؟ |
|---|---|---|---|---|
| `#catalog` | `/product add <ZIM-ID> …` | `product_catalogued` | INTERNAL | خیر |
| `#catalog` | `/product price <ZIM-ID> <amount>` | `owner_fact_asserted` (field=price) | OWNER_ONLY | — (خودِ مالک) |
| `#catalog` | `/product cogs <ZIM-ID> <amount>` | `owner_fact_asserted` (field=cogs) | SENSITIVE_COMMERCIAL | — |
| `#photos` | `/photo map <IMG> <ZIM-ID>` | `photo_mapped` | INTERNAL | خیر |
| `#photos` | `/photo replace <ZIM-ID> <IMG>` | `photo_quality_flagged`+`photo_mapped` | INTERNAL | خیر |
| `#variants` | `/variant confirm <pair> same\|distinct [sku]` | `variant_confirmed` | INTERNAL | بله (این خودش تأیید است) |
| `#policy` | `/policy alcohol confirm` | `policy_set` (age+no-ship) | SENSITIVE_COMMERCIAL | بله |
| `#policy` | `/policy delivery F4 local_only` | `policy_set` | SENSITIVE_COMMERCIAL | بله |
| `#policy` | `/policy licensed <decision>` | `policy_set` | SENSITIVE_COMMERCIAL | بله |
| `#reconcile` | `/reconcile 35 50` | `count_reconciled` | SENSITIVE_COMMERCIAL | بله |

قاعده: هیچ کامندی مستقیماً Product Card را ویرایش نمی‌کند؛ کامند → رویداد → projection → (در صورتِ تأیید) به‌روزرسانیِ نما. این مرزِ **Gateway ≠ Memory** را نگه می‌دارد.

---

### ۴) معیارِ خروجِ فاز صفر (Phase-0 Exit Criteria)

فاز صفر «تثبیتِ لایهٔ حقیقتِ محصول» است؛ نه فروش، نه بازاریابیِ چندایجنتی (که تا ۱۰–۳۰ فروش معوق است). خروج وقتی احراز می‌شود که همهٔ بندهای زیر `PASS` شوند:

| # | معیار | سنجه (Definition of Done) | وضعیتِ مطلوب |
|---|---|---|---|
| E1 | **Ledger برپا** | اسکیمای `evt.v1`/`mc.v1` پیاده و append-only؛ re-runِ ingestِ ۴۱ عکس با idempotency صفر رکوردِ تکراری تولید کند | PASS |
| E2 | **کاتالوگِ گراند‌شده** | هر ۳۵ محصول یک `product_catalogued` دارد؛ هر ۴۰ عکسِ سالم یک `photo_mapped`؛ عکسِ سفید `photo_quality_flagged` | PASS |
| E3 | **مشکلاتِ عکس ثبت** | IMG_2812(rotated)، IMG_3378(screenshot→ZIM-F1-13)، ۱ سفید همگی پرچم‌دار و در Photo-Asset-Index | PASS |
| E4 | **تعارض‌ها احصا** | جدولِ §۲ کامل در `10.09 Open-Conflicts.md`؛ هیچ تعارضِ بازِ ناثبت نمانده | PASS |
| E5 | **۳ جفتِ variant تعیین‌تکلیف** | C6/C7/C8 یا `variant_confirmed` دارند یا صراحتاً `deferred` با تاریخِ بازبینی | PASS |
| E6 | **سیاست‌های حساس تأیید** | C9(الکل)، C10(لایسنس)، C11(تحویلِ F4=perishable⇒local_only) هرکدام یک `policy_set` از actor=owner دارند | PASS |
| E7 | **آشتیِ عدد** | C1 یا با `count_reconciled` بسته شده یا شکافِ ~۱۵ صراحتاً به‌عنوان `UNKNOWN` مستند و پذیرفته | PASS |
| E8 | **مهاجرتِ Obsidian بی‌آسیب** | CATALOG.md، Product Cards، Photo-Asset-Index در ساختارِ 00–99 لینک‌شده؛ هیچ فایلی move نشده؛ rollback تست‌شده | PASS |
| E9 | **مرزِ حریمِ داشبورد** | هیچ رکوردِ `SENSITIVE_COMMERCIAL`/`OWNER_ONLY` در داشبوردِ no-auth دیده نشود (تستِ masking) | PASS |
| E10 | **قیدِ بودجه/تلگرام محترم** | مصرفِ APIِ فازِ کاتالوگ ≤ ۱۵ AUD/ماه (روترِ hybrid/Ollama)؛ نگاشتِ تلگرام owner-only آماده ولی تا token فعال‌نشده | PASS |

**Not-in-scope (صراحتاً خارج از فاز صفر):** قیمت‌گذاریِ نهایی و محاسبهٔ حاشیه (منتظرِ C2/C5)، فعال‌سازیِ PayID (تصمیم‌گرفته ولی غیرفعال)، فعال‌سازیِ token تلگرام، و هر جریانِ بازاریابیِ چندایجنتی. این‌ها gateهای فازِ بعدند و نبودشان مانعِ خروجِ فاز صفر نیست.