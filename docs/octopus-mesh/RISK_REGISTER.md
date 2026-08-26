# RISK REGISTER — octopus-mesh / session-bridge

| # | مورد | وضعیت | اقدام |
|---|---|---|---|
| R1 | پورت **9101** روی برد ۱۸۲ باز است (کاوش ۲۰۲۶-08-26: روی ۱۳۸ و ۱۸۰ بسته) | ثبت‌شده — طبق حکم تغییر داده نشد |needs_owner_review: مالک سرویسِ روی 182 مشخص نیست |
| R2 | کلیدهای mesh بین سه برد توزیع شده‌اند؛ سرقت هر برد = دسترسی SSH به دو برد دیگر | پذیرفته‌شده در MVP | چرخش کلید در فاز بعد؛ محدودسازی command= در authorized_keys |
| R3 | redaction مبتنی بر pattern است و تضمین کامل نیست | کاهش‌یافته | payload به‌صورت پیش‌فرض نمایش داده نمی‌شود؛ محتوای key-like کلاً بلاک می‌شود (needs_human_review) |
| R4 | lease recovery تضمین «حداکثر یک‌بار پردازش» نمی‌دهد اگر session بعد از ارسال reply و قبل از ACK بمیرد | شناخته‌شده | receipt شناسه reply را ذخیره می‌کند؛ idempotency_key=reply-<mid> ارسال دوباره را در گیرنده duplicate می‌کند |
| R5 | inbox نامحدود پر می‌شود اگر session ای claim نکند | شناخته‌شده | status/peek برای پایش؛ بدون daemon، انباشت فقط با پردازش دستی رخ می‌دهد |
| R6 | os.replace بین filesystemهای مختلف کار نمی‌کند | طراحی‌شده | همهٔ دایرکتوری‌ها زیر همان ~/octopus-mesh هستند |
| R7 | پیام‌های verification_task/observation/evidence در policy.json transporte نیستند؛ ارسال آن‌ها fail-closed رد می‌شود | ثبت‌شده | نقش در agent_roles.json اجازه می‌دهد؛ افزودن به transport نیازمند حکم جدا |
| R8 | bridge بدون احراز فراخواننده است؛ هر فرایند محلی با دسترسی کاربر می‌تواند claim کند | پذیرفته‌شده در MVP (terminal execution همان کاربر است) | در فاز بعد: nonce چالش-پاسخ برای session |
