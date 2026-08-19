---
type: research-report
created: 2026-08-20 (overnight, owner-requested research + operations guide)
basis: owner research order + live measurements 2026-08-19/20
tags: [llm-judge, position-bias, vllm, reasoning-content]
---

# بازو در برابر داور — تحلیل + راهنمای عملیاتی vLLM

## بخش ۱ — چرا داورها با ارزیابی انسانی همسو نیستند (ادبیات + اندازهٔ ما)

### ۱.۱ چهار سوگیری شناخته‌شده (ادبیات)

| سوگیری | سازوکار | شواهد مرجع (تقریبی، عمداً بدون عدد دقیق) |
|---|---|---|
| **Position bias** | داور A/B را در جایگاه ثابت ترجیح می‌دهد، نه محتوا | در بنچمارک‌های LLM-as-a-judge (از MT-Bench به بعد) نرخ flip ترتیب به‌طور پایدار بالای صفر است؛ بهترین داورها با swap-test کالیبره می‌شوند |
| **Length bias** | پاسخ بلندتر «کامل‌تر» به نظر می‌رسد؛ داورها بدون دیدن محتوا پاسخ بلند را ترجیح می‌دهند | در PandaLM و تحلیل‌های LLM-Arena، همبستگی رای با طول پاسخ مشاهده شده؛ همین که پاسخ طولانی تلفیق‌پذیرتر است، امتیاز را بالا می‌برد |
| **Self-preference bias** | داورِ خانوادهٔ A، خروجی‌های مدل A را ترجیح می‌دهد | RewardBench و مطالعات تعصب‌خودخواهانه: حتی داورهای قوی، خروجی سازندهٔ خود را امتیاز بهتری می‌دهند |
| **Reasoning-capacity asymmetry** | داور باید دربارهٔ کیفیت *استدلال دیگران* استدلال کند — وظیفه‌ای سخت‌تر از تولید | JudgeBench (2025) نشان داد داورهای عمومی روی تشخیص خطای استدلالی ضعیف‌ترند؛ اگر داور از بازو ضعیف‌تر باشد، قضاوتش نویز است |

### ۱.۲ اندازه‌گیری واقعی روی داور خودمان (۲۰۲۶-۰۸-۲۰)

- **Position-bias probe** (۴ جفت ثابت، هر دو ترتیب، seed+temp پین): **flip rate ‏۱/۴ = ۲۵٪** — و الگوی flip کلاسیک است: در جفتِ flip، داور در **هر دو ترتیب موقعیت B را انتخاب کرد** (ترجیح جایگاه، نه محتوا).
- **Field-split bug** (گام ۰): client در `content` خالی، `reasoning_content` را به‌جای پاسخ برمی‌گرداند — یعنی «پاسخِ» داور گاهی خودِ استدلال است؛ یک باگ چندخطی که «بیماری preamble» دو روزه را توضیح می‌داد. فیکس: content-only.
- **VOID نهایی پس از fallback** (۲۰ نمونه): **۰٪** — مقاوم‌سازی جواب داد، ولی این تحملِ واریانس است نه حذف آن.

### ۱.۳ پیامد برای ما

۱. ترجیح موقعیتِ داور ما را می‌توان با **جابه‌جایی متقابل** (هر جفت در هر دو ترتیب، رأی محتوایی، نه جایگاهی) خنثی کرد — هزینه‌اش ۲× است، اما برای هر جفتِ شمرده‌شدهٔ primary ارزش دارد.
۲. داورِ هم‌خانواده (DeepSeek) self-preference دارد — محدودیتِ مستندِ `judge_independence_limited` دقیقاً همین است؛ راه‌حل نهایی = داور از خانوادهٔ دیگر (GLM پس از شارژ) و در نبودش، گزارش سوگیری به‌عنوان confounder.
۳. سوگیری طول: در پروتکل، بازوها هم‌سقف (۲۰۰–۳۰۰) هستند و خط‌اولِ answer-first آن را مهار می‌کند — ولی باید در هر تحلیل پایش شود.

---

## بخش ۲ — راهنمای عملیاتی vLLM

### ۲.۱ استخراج و مدیریت reasoning_content (OpenAI-compatible)

- پاسخ reasoning مدل‌های thinking در میدان `message.reasoning_content` می‌آید؛ `message.content` پاسخ نهایی است. **هرگز آن‌ها را با `or` به‌هم نچسبان** (همان باگ ما) و `reasoning_content` را به‌جای `content` به عنوان پاسخ نفرست.
- نمونهٔ استخراج:

```python
msg = data["choices"][0]["message"]
content = msg.get("content") or ""            # فقط پاسخ
reasoning = msg.get("reasoning_content") or ""  # فقط شواهد/لاگ
```

- **Multi-turn و خطای 400**: اگر `reasoning_content` دریافتی را در پیام بعدی به‌عنوان `content` یا در `messages` بازفرستید، بسیاری از APIها 400 می‌دهند (میدان ناسازگار با نقش user/assistant). قانون: یا آن را کامل حذف کنید، یا در میدان اختصاصی (در صورت پشتیبانی) بازگردانید — هرگز به‌جای content.
- برای لاگ: reasoning را جدا ذخیره کنید (خود ما `raw_output_sha256` + اکنون `reasoning_content` را در رسید می‌گذاریم).

### ۲.۲ stop sequences بهینه بر اساس سناریو

| سناریو | stop | max_tokens | چرا |
|---|---|---|---|
| حکم تک‌حرفی (A/B/T) | `["\n", " "]` | ۲–۴ | تولید بعد از حرف اول قطع می‌شود؛ preamble ناممکن |
| خط اول + rationale جدا | `["\n\n"]` | ۵۱۲ | اولین پاراگراف حکم، rationale بعد از بلوک |
| JSON دقیق | `response_format={"type":"json_object"}` (در صورت پشتیبانی) | طبق اسکیما | الزام در سطح تولید، نه درخواست |
| پاسخ بلند مستند | بدون stop | فرمول پایین | — |

### ۲.۳ فرمول سایزینگ max_tokens (ضد اتلاف)

```
T = ceil( chars_expected / tokens_per_char ) + headroom
  tokens_per_char ≈ 3.5 برای فارسی/لاتین (حدس محافظه‌کارانه)
  headroom = 1.15 × T  برای جملات بلند + نشانه‌گذاری
```

- حکم: ‏`T = ceil(1/3.5) + 1 = 2` → در عمل ۲–۴ با stop.
- خط اول + rationale کوتاه: ‏`T = ceil(60/3.5)×1.15 ≈ 20` (اگر stop خط اول را نگه دارد؛ وگرنه ۵۱۲ و سقف واقعی همان stop است).
- اصل: **سقف توکن فقط بیمه است، stop کنترلی واقعی است** — سقف بالا + stop زودهنگام = هیچ اتلافی؛ سقف پایین بدون stop = بریدگی (ریشهٔ اصلی ۲ روز گذشته ما).

### ۲.۴ کد نمونه (OpenAI-compatible، با seed/temperature برای کاهش واریانس)

```python
import openai
client = openai.OpenAI(base_url=..., api_key=...)
r = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=2, temperature=0.0, seed=42,
    stop=["\n", " "],
)
msg = r.choices[0].message
verdict = (msg.content or "").strip().splitlines()[0]  # 'A'|'B'|'T'
reasoning = getattr(msg, "reasoning_content", None)     # فقط برای لاگ
```

> نکتهٔ سازگاری: پشتیبانی `seed`، `reasoning_content` و `json_object` به مدل/نسخه بستگی دارد — پیش از اتکا یک probe کوچک بزنید (همان الگوی ما با GLM: «یک‌بار تست، بعد اطمینان»).

---

## ضمیمه — اثر فوری در OCTOPUS

- باگ میدان‌ها در `_ops/debate/client.py` فیکس شد (content-only؛ reasoning برای شواهد).
- داورِ تک‌حرفی با stop و سقف ۲–۸ اثبات شد: **VOID نهایی ۰٪ روی ۲۰ نمونه**.
- position-bias ‏۲۵٪ ثبت شد → کاندید گام بعدی: جفت‌های swap-test برای هر pairِ شمرده‌شده (پیشنهاد برای گیت‌های آینده؛ primary فقط با مالک).
