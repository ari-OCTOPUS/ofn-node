# RUNBOOKS — دو بحرانی که دوباره پیش می‌آیند (از درس‌های سیزن ۲۰۲۶-۰۸/۰۹)

## RB-1: رمز اپ Gmail منقضی/رد شد (SMTPAuthenticationError 535)

1. مالک در myaccount.google.com → Security → 2-Step Verification →
   App passwords → جدید (نام: octopus)
2. اگر گوگل گفت «۶ روز دیگر امتحان کنید»: تأیید هویت (ایمیل بک‌آپ/موبایل)
   همان لحظه قفل را باز می‌کند — منتظر ۶ روز نمان.
3. مقدار جدید فقط در بورد:
   `~/.config/ofn/secrets.env` → خط GMAIL_APP_PASSWORD=... (**هرگز در چت/گیت ننویس**)
4. تست بدون ارسال:
   `cd ~/ofn/ofn/agents && set -a && . ~/.config/ofn/secrets.env && set +a && \
    python3 -c "import mail_credentials as m; print(m.status())"`
   بعد یک IMAP خشک: `python3 imap_listener.py --dry`
5. Passkey ≠ App Password — گوگل طرف passkey می‌فرستد، ما ۱۶ حرف می‌خواهیم.

## RB-2: پوش گیت‌هاب از بورد 403 می‌دهد

- علت فعلی: توکن ari322 پوش به ari-OCTOPUS ندارد + ارگان Deploy keys را بسته.
- رلهٔ کارآمد (الان): از ویندوزِ `F:\ofn-node`:
  `git fetch board138 release/p0 && git push origin refs/remotes/board138/release/p0:refs/heads/release/p0`
- ریشه‌درمانی (رأی مالک Q9): کلید آماده است `~/.ssh/ofn_deploy.pub`؛
  مالک: Org Settings → Security → Deploy keys → Allow؛ سپس:
  `gh api repos/ari-OCTOPUS/ofn-node/keys -f title=board138-deploy -f key="$(cat ~/.ssh/ofn_deploy.pub)" -F read_only=false`
  و remote بورد به SSH.

## RB-3: ریسک شناخته‌شده — رمز در لاگ چت (رأی مالک: قفل نشد)
- اگر روزی رمز چرخید: فقط secrets.env بورد؛ تاریخچهٔ چت پاک‌شدنی نیست —
  این ریسک با رأی ۲۰۲۶-09-01 پذیرفته و ثبت شده (#64).
