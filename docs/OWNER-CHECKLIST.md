# OWNER CHECKLIST — چهار اقدامی که فقط از دست مالک می‌شود (به‌روز ۲۰۲۶-۰۹-۰۱)

> سیستم بقیه را خودش انجام می‌دهد. این چهار مورد با هر ابزارِ جایگزینی که
> ایجنت‌ها بتوانند، خودکار شده‌اند — اینجا فقط آنچه ذاتاً انسانی است.

## 1. ABN + بیمه → identity.json (رأی Q1: هر دو موجود — فقط ثبت شود)
- در بورد فایل `/home/ari/.config/ofn/identity.json` آماده است؛ این فیلدها را پر کن:
  - `abn` — شمارهٔ ABN (۱۱ رقم)
  - `insurer` و `insurance_policy` و `insurance_valid_until`
- از این به بعد هر ایمیل/کوتی که ABN یا بیمه بگوید از همین فایل می‌خواند؛
  تا پر نشود، ایمیل‌ها **بدونِ آن ادعاها** می‌روند (قاعدهٔ صداقت R6).
- ABN در استرالیا دادهٔ عمومی است؛ در صورت تمایل همین‌جا در چت هم بده.

## 2. دامنهٔ .com.au (رأی Q2)
- یک registrar استرالیایی (CrazyDomains/GoDaddy AU/VentraIP)؛ لازم است ACN/ABN.
- پیشنهاد نام: `masterpainting.com.au` → اگر گرفته بود: `masterpaintingnsw.com.au`
- بعد از خرید، به ایجنت بگو؛ کارهای او: DNS + SPF/DKIM/DMARC + صندوق
  `quotes@<domain>` + ترنسپورت دوم؛ Gmail شخصی به fallback می‌رود.

## 3. GitHub Org: اجازهٔ Deploy keys (رأی Q9 — ۱ دقیقه)
- github.com → سازمان ari-OCTOPUS → Settings → Security → Deploy keys → **Allow**
- کلید بورد ساخته‌شده منتظر است: `~/.ssh/ofn_deploy.pub` روی بورد؛
  بعد از Allow فقط یک فرمان ایجنت آن را وصل می‌کند.

## 4. ثبت‌نام‌های دولتی NSW (مسیر واقعی فروش به دولت)
- **buy.nsw eTendering**: حساب بساز؛ ایجنت کلید API را می‌گیرد → مناقصه‌ها مستقیم می‌آیند.
- **Schemeهای پیمانکار** (بسته به سایز کار): Small Works Scheme، QBuildNC؟ نه —
  برای NSW: State Panel Arrangements و Aboriginal Procurement Policy اگر مزیت داری.
- بررسی **Home Building Act**: کارهای بالای $5,000 در NSW نیاز به licence پیمانکار
  رنگ دارد (نقاشی = painting trade). اگر licence نداری، کارهای دولتی بزرگ
  گیر دارند — یا شریکِ دارای licence لازم است (ایجنت می‌تواند شریک‌یابی کند).

## بازنگری دوره‌ای (رأی GAPS-95)
- اولین یکشنبهٔ هر ماه: ۱۵ دقیقه بازبینی digestها + این چک‌لیست؛
  ایجنت یادآوریِ ماهانه در digest اولِ ماه می‌گذارد.
