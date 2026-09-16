// config.js — قابل‌ویرایش توسط مالک. هیچ secret اینجا نیست.
// این فایل «قواعد دسته‌بندی و انطباق» است؛ importer از این می‌خواند.
// ⚠️ همه‌ی خروجی‌ها draft هستند و نیاز به verdict انسانی دارند (ARCHITECT_CHARTER §1).

module.exports = {
  // حساب‌هایی که «شرکت» هستند. بقیه = شخصی/مختلط.
  // ← مالک: نام دقیق حساب‌های بیزنس را تأیید/کامل کن.
  BUSINESS_ACCOUNTS: ['ANZ Business Essentials'],

  // Associates برای تشخیص Division 7A (مدیر + خانواده + پرداخت‌گیرندگان مرتبط).
  // اگر پرداختی به این‌ها از حساب بیزنس برود، به‌عنوان «برداشت مدیر/Div7A» پرچم می‌خورد.
  // ← مالک: این لیست را تأیید/کامل کن (نام‌ها همان‌طور که در توضیح تراکنش می‌آیند).
  ASSOCIATES: ['Armin Mohebiafzal', 'Maliheh Khalajijou', 'Sume Asadi', 'Behzad', 'Ehsan Zamani'],

  // نگاشت فروشنده → دسته. اولین match در متن Merchant برنده است.
  // scope: 'business' یا 'personal'. gstFree:true یعنی GST ندارد (خارجی/معاف).
  VENDOR_MAP: [
    { match: 'bunnings',          category: 'Materials',             scope: 'business' },
    { match: 'inspirations paint',category: 'Materials',             scope: 'business' },
    { match: 'paint',             category: 'Materials',             scope: 'business' },
    { match: 'bp ',               category: 'Fuel',                  scope: 'business' },
    { match: 'caltex',            category: 'Fuel',                  scope: 'business' },
    { match: 'coles express',     category: 'Fuel',                  scope: 'business' },
    { match: 'allianz',           category: 'Insurance',             scope: 'business' },
    { match: 'xero',              category: 'Software/Subscriptions',scope: 'business' },
    { match: 'myob',              category: 'Software/Subscriptions',scope: 'business' },
    { match: 'google ad',         category: 'Marketing',             scope: 'business' },
    { match: 'call dynamics',     category: 'Marketing',             scope: 'business' },
    { match: 'ezidebit',          category: 'Professional Fees',     scope: 'business' },
    { match: 'rent',              category: 'Rent',                  scope: 'business' }, // ← تأیید: تجاری (GST دارد) یا مسکونی (بدون GST)؟
    { match: 'woolworths',        category: 'Groceries',             scope: 'personal' },
    { match: 'coles',             category: 'Groceries',             scope: 'personal' },
    { match: 'aldi',              category: 'Groceries',             scope: 'personal' },
    { match: 'big w',             category: 'Shopping',              scope: 'personal' },
    { match: 'kmart',             category: 'Shopping',              scope: 'personal' },
    { match: 'netflix',           category: 'Subscriptions',         scope: 'personal' },
    { match: 'apple.com',         category: 'Subscriptions',         scope: 'personal' },
    { match: 'uber',              category: 'Transport',             scope: 'personal' },
    { match: 'amazon',            category: 'Shopping',              scope: 'personal' },
    { match: 'temu',              category: 'Shopping',              scope: 'personal', gstFree: true }, // خارجی
    { match: 'aliexpress',        category: 'Shopping',              scope: 'personal', gstFree: true },
  ],

  // نشانه‌های GST-free در متن (بهره، مالیات، حقوق، سوپر، کارمزد بانک، دولت).
  GST_FREE_HINTS: ['interest', 'withhold tax', 'resident withhold', 'wage', 'salary',
                   'super', 'gov ', 'council', 'bank fee', 'ato '],

  // آستانه‌ها (ATO)
  ABN_THRESHOLD: 75,        // پرداخت بیزنسِ بالای این مبلغ بدون ABN → پرچم
  AUSTRAC_THRESHOLD: 10000, // تراکنش نقدی ≥ این مبلغ → پرچم گزارش‌دهی
};
