# ۰۱ — مدلِ خود (`ziman_self.v1`) · شناختِ خود و اهداف

این قلبِ بازطراحی است: یک ساختارِ واحد که زیمان هر ضربان می‌سازد تا **بداند کی‌ست، هدفش
چیست، و کجای راه است**. این مدل واردِ ماتریس می‌شود و اولویتِ پیشنهادها را تعیین می‌کند.

## قاعدهٔ «یک مدلِ خود»
فقط **یک** ماژول: `_ops/legs/ziman_self_model.py` که در `state/cortex/ziman-self-model.json`
عکسِ لحظه‌ای می‌نویسد. (هر ماژولِ رقیبِ دیگری در طراحیِ ستون‌ها به نفعِ همین یکی حذف شد —
رجوع به `08-CONFLICTS-AND-GAPS.md`.) این ماژول فقط از منابعِ **فقط‌خواندنیِ موجود** می‌خواند
و هیچ‌چیز canonical نمی‌نویسد.

## طرح (schema) — چهار بخش
```
ziman_self.v1 = {
  schema: "ziman_self.v1", beat, ts, freshness_beats,

  identity: {                         # «من کی‌ام» — ثابت‌ها و مرزها
    name: "Ziman Gift", market: "Sydney warm/Iranian",
    offering: [F1 floral, F2 framed, F3 candy, F4 hamper],   # از کاتالوگِ واقعی
    facets: {alcohol_skus, local_only_families:[F4], perishable},
    brand_rules: ["artificial florals only", "no fabricated testimonials", ...],
    hard_gated: [publish, send, dm, spend, price, ...],
    authorities: {price:false, delivery_promise:false, publish:false}   # همه false
  },

  objective: {                        # «هدفم چیست» — از GOALS-ZIMAN.md
    north_star: "10–30 real sales (validation)",
    real_sales: <از evt.v1 sale:confirmed>,           # تنها منبعِ حقیقت
    validation_progress_pct: min(real_sales,10)/10 * 100,
    directives: [<بولت‌های GOALS-ZIMAN.md>],           # OWNER_INPUT
    priorities: [<ترتیبِ محصول/مناسبت>]
  },

  standing: {                         # «کجای راهم» — وضعیتِ سنجش‌پذیر
    catalog: {total, priced:0, families},
    inventory: {count, evidence_class: OWNER_INPUT/UNKNOWN},
    drafts_count, budget_headroom_aud,
    capacity: {raw_yaml:30, evidence: CONFLICT, effective:<=6},   # هرگز عمومی
    funnel: {cold, warm, proposed, won}                # از lead.v1
  },

  biology: {pain_level, protective_mode},              # از heart/doctor (read-only)

  gap_vector: [                        # فاصلهٔ هر هدف تا وضعیتِ فعلی (رانِ اولویت)
    {goal, current, target, gap, confidence, truth_tier}
  ],

  truth_tiers: {<هر فیلد>: VERIFIED_FACT|OWNER_INPUT|MEASURED|ESTIMATE|CONFLICT}
}
```

## منابعِ واقعی (همه فقط‌خواندنی و موجود)
| بخش | از کجا خوانده می‌شود |
|---|---|
| offering/facets | `catalog_loader.load_catalog()` (کاتالوگِ ۳۵‌تایی) |
| directives/priorities | `GOALS-ZIMAN.md` (parse با `steering.py`) |
| real_sales | دفترِ `evt.v1` رویدادِ `sale:confirmed` (control-brain) |
| catalog/inventory/capacity | `ziman.yaml` + `product.py` (با گاردِ anti-misread) |
| budget_headroom | `budget.remaining_aud()` |
| funnel | `data/leads.jsonl` (`lead.v1`) |
| biology | read-modelِ قلب/دکترِ اُرگانیسم (بدونِ نوشتن) |

## تراز‌تیرِ حقیقت (چرا مهم است)
هر فیلد برچسبِ صداقت دارد. مثلاً `capacity.raw_yaml=30` هست ولی `evidence=CONFLICT` است؛
پس ماتریس هر پیشنهادی که بخواهد «۳۰/هفته» را عمومی کند **جریمه/وتو** می‌کند. هیچ عددی جعل
نمی‌شود؛ اگر داده‌ای نیست، `UNKNOWN` می‌ماند (امن‌تر از حدس).

## چطور اولویت‌ساز می‌شود (self-directed)
`gap_vector` رانِ اصلیِ خودمختاری است: هدفی که بیشترین فاصله × اطمینان را دارد، بیشترین
«impact» را در ماتریس می‌گیرد. مثال: اگر `real_sales=0` و بزرگ‌ترین شکاف «اولین گفت‌وگو با
مشتری» است، پیشنهادهای CACِ بازارِ گرم بالاتر از پیشنهادهای محتوای تزئینی رتبه می‌گیرند.
این «شناختِ خود که واردِ ماتریسِ محاسبات می‌شود» را عملی می‌کند.

## همگامی با ضربان
مدلِ خود هر ضربان (پشتِ فلگ) بازساخته می‌شود، با mtime-cache روی فایل‌ها تا تقریباً رایگان
باشد. `freshness_beats` می‌گوید چند ضربان از آخرین به‌روزرسانیِ هر منبع گذشته — داده‌ی کهنه
اعتمادش پایین می‌آید. قرارداد در `03-HEARTBEAT-CONTRACT.md`.

## مرزِ propose-only
مدلِ خود هرگز چیزی نمی‌نویسد جز عکسِ لحظه‌ایِ خودش (advisory). `real_sales` فقط از رویدادِ
مالک‌محورِ `sale:confirmed` می‌آید — نه از حدسِ ایجنت. هیچ authority (قیمت/انتشار/تحویل)
هرگز true نمی‌شود.
