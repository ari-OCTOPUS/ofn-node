---
tags: [ofn, handoff, agent, owner-complete]
aliases: [دستورالعمل ایجنت بعدی, Agent Next]
updated: 2026-08-10
---

# دستورالعمل ایجنت بعدی — ادامهٔ MEGAPROMPT-OWNER-COMPLETE

> این فایل را کامل بخوان، بعد اجرا کن. اسناد قدیمی را باور نکن؛ با دستور زنده بسنج.
> مالک: **آری**. اصل: کرنل تصمیم می‌گیرد · مدل مشورت می‌دهد · انسان حکم می‌کند.

**پیوندها:** [[MEGAPROMPT-OWNER-COMPLETE]] · [[HANDOFF]] · [[CLAUDE]] · [[DECISIONS]] · [[INDEX]]

---

## ۰) قانون سخت — نقض نشود

```
❌ راز نخوان / echo نکن / در فایل ننویس   (~/.config/ofn/*.env)
❌ هیچ OFN_WIRE_* / OCTOPUS_WIRE_* را روشن نکن
❌ گیت بسته باز نکن: secret_rotation · partner_precondition · miner_isolation
❌ چیزی به بیرون نفرست (ایمیل، تلگرام مشتری، پست، SMS، خالی کردن outbox)
❌ rm -rf خارج از /tmp بدون تأیید صریح آری
❌ فایل‌های .bak-* را commit نکن
❌ اعمال deploy/firewall/APPLY.md نکن — فقط آری
```

آزاد: خواندن لاگ، pytest، ویرایش کد در `~/ofn` و `~/hypno-fugu-mini`، گزارش، پیشنهاد دستور sudo.

---

## ۱) حقیقت روی زمین — اندازه‌گیری ۲۰۲۶-۰۸-۱۰ ~۱۳:۲۵ AEST

قبل از هر کار دوباره بسنج:

```bash
cd ~/ofn && python3 -m pytest -q --tb=line
cd ~/ofn && python3 tools/repo_baseline.py --tests
systemctl is-active ofn hypno-fugu-mini cloudflared
for p in 8791 8792 8793 8794 8895; do
  curl -s -m3 -o /dev/null -w "$p %{http_code}\n" http://127.0.0.1:$p/
done
for h in panel ziman lead studio hypno; do
  curl -s -m8 -o /dev/null -w "$h %{http_code}\n" https://$h.master-painting.com/
done
timedatectl show -p NTP -p NTPSynchronized
ls -ld ~/.local/share/ofn/backups
git -C ~/ofn status -sb
git -C ~/hypno-fugu-mini status -sb
```

**آخرین اندازه‌گیری معتبر (ممکن است عوض شده باشد):**

| چک | نتیجه |
|---|---|
| pytest OFN | 1595 passed · 5 skipped · 0 failed |
| collected | 1600 |
| loopback 8791–8794 + 8895 | همه 200 |
| HTTPS بیرون | 530 (تونل مرده) |
| ofn / hypno-fugu-mini | active |
| cloudflared | **failed** از ~09:03 (Result: timeout) |
| NTP | NTP=no · sync نشده |
| backups dir | `~/.local/share/ofn/backups` → 0700 ✅ |
| پورت 8090 | مشاهده نشد |

---

## ۲) چه چیزی قبلاً انجام شده (دوباره نساز)

اگر کد/سند همین را می‌گوید، در گزارش «قبلاً بسته» بنویس و رد شو.

| ID | کار | وضعیت |
|---|---|---|
| A1 | CRIT-1 پورت 8090 | مشاهده نشد — دوباره با `ss` بسنج |
| A3 | chmod مقصد بک‌آپ 0700 | ✅ |
| B1 | D-23 بسته در DECISIONS | ✅ |
| B2 | شکاف #۱ لید در HANDOFF | ✅ |
| B3 | `tests/test_octopus_wire_drift.py` | نوشته شده (ممکن است هنوز untracked) |
| B4/B5 | اعداد کهنه + INDEX | تا حدی ✅ — اگر عدد ثابت دیدی به baseline ارجاع بده |
| C1 | `rating_is_trustworthy` fail-closed وقتی `first_metric_at is None` | ✅ + تست‌ها به‌روز |
| C2 | `except: pass` رجیستری → stderr WARN در `node.py` | ✅ |
| C3 | `tests/test_sysmetrics.py` | نوشته شده (ممکن است untracked) |
| web lead | `.catch` روی boot/refreshLeadCrm + `escLike` برای wildcard | ✅ `web/lead.html` |
| web panel | `.catch` روی `loadSurfaces` | ✅ `web/panel.html` |
| web hypno | async `.catch` + jargon فارسی | ✅ `hypno-fugu-mini/web/index.html` |

**تغییرات git هنوز commit نشده‌اند** مگر آری گفته باشد.

---

## ۳) صف کار تو — به همین ترتیب

### فاز ۱ — زیرساخت (فقط با تأیید صریح آری در همان جلسه)

اگر آری گفت «تونل/NTP را درست کن»:

```bash
# ۱) NTP
sudo timedatectl set-ntp true
timedatectl show -p NTP -p NTPSynchronized

# ۲) تونل — اول لاگ، بعد restart
sudo journalctl -u cloudflared -n 40 --no-pager
sudo systemctl restart cloudflared
sleep 3
systemctl is-active cloudflared
for h in panel ziman lead studio hypno; do
  curl -s -m8 -o /dev/null -w "$h %{http_code}\n" https://$h.master-painting.com/
done
```

انتظار: cloudflared active · دامنه‌ها 200 (نه 530).

اگر بدون تأیید آری هستی: **فقط گزارش بده، restart نکن.**

### فاز ۲ — فیکس‌های کد باز (بدون WIRE، بدون گیت)

به ترتیب اولویت:

#### 2.1 · ziman · ارقام فارسی (E3)

مشکل: ارقام فارسی خام ممکن است به `/api/v1/products` برود.
اقدام:
- تبدیل ارقام فارسی/عربی → لاتین در **مرز API** (نه فقط در JS)
- `inputMode=decimal` و `type=text` در فرم (درس ۳ زیمان)
- تست واحد برای `۱۲۵` و `٤٠`

#### 2.2 · hypno · H6 حذف research

`DELETE`/`/api/research/delete` را بسنج.
پیشنهاد پیش‌فرض (تا آری خلافش را بگوید):
- یا endpoint را برای غیر-owner ببند
- یا soft-delete + ledger
- **هیچ دیتایی را واقعاً wipe نکن بدون تأیید**

#### 2.3 · panel · D2 فرم‌های POST میز نقاشی

**غلط تفسیر نکن.** پنل مالک از قدیم CRM نوشتنی نقاشی دارد.
«فقط‌خواندنی» در مگاپرامپت یعنی endpointهای جدید جلسهٔ ۰۸-۰۹ (outbox/ledger/levels/brain)، نه حذف کل POSTهای نقاشی.
اقدام: در HANDOFF یک خط بنویس که D2 عمداً باز است برای مالک؛ مگر آری بگوید قفل شوند.

#### 2.4 · panel · کلمهٔ «مدل» در فوتر

اگر جملهٔ فلسفی قانون اساسی است («مدل مشورت می‌دهد») — عمدی؛ دست نزن مگر آری بخواهد.
اگر jargon فنی است — طبق D-22 عوض کن.

#### 2.5 · studio · G1 هدر تلگرام

اگر هنوز باز است: `tg().setHeaderColor` / `setBackgroundColor` با پالت پوسته.
بعد از ویرایش `web/`: **restart ofn + curl بایت عوض‌شده**.

### فاز ۳ — بهداشت git و تست

```bash
cd ~/ofn && python3 -m pytest -q
cd ~/hypno-fugu-mini && python3 -m pytest -q
# فایل‌های جدید باید track شوند اگر آری commit خواست:
#   tests/test_octopus_wire_drift.py
#   tests/test_sysmetrics.py
#   MEGAPROMPT-OWNER-COMPLETE.md
#   AGENT-NEXT-OWNER-COMPLETE.md
# .bak-* را add نکن
```

Commit **فقط** وقتی آری بگوید. پیام پیشنهادی:

```
agent-checkpoint: owner-complete A–J harden (fail-closed rating, wire drift, web catches)
```

### فاز ۴ — HANDOFF و گزارش به آری

قالب:

```
## حقیقت روی زمین
- pytest / services / ports / HTTPS / NTP / outbox count

## انجام‌شده این جلسه
- ID → تغییر → تست قفل

## منتظر تو
- cloudflared restart؟
- NTP؟
- commit؟
- H6 delete research: ببند / soft / بگذار؟
- E3 فارسی: تأیید الگوی تبدیل؟

## عمداً دست‌نخورده
- secret_rotation · partner_precondition · miner_isolation
- WIRE خاموش · outbox ارسال نشده · فایروال APPLY
```

---

## ۴) تصمیم‌هایی که فقط آری می‌گیرد

| موضوع | پیش‌فرض ایجنت تا جواب |
|---|---|
| restart cloudflared | نکن؛ بپرس |
| set-ntp | نکن؛ بپرس |
| commit | نکن؛ بپرس |
| حذف research در hypno | نساز wipe؛ پیشنهاد بستن |
| فرم‌های POST پنل نقاشی | عمدی برای مالک؛ حذف نکن |
| فایروال روی 22 | فقط یادآوری |
| چرخش راز | فقط یادآوری؛ مقدار نبین |

---

## ۵) قرارداد وب‌اپ (اگر دست زدی)

بعد از هر ویرایش `web/` یا `hypno/.../web/`:

```bash
# OFN
cd ~/ofn && python3 -m pytest -q tests/test_web_serving.py tests/test_shell_reachability.py
sudo systemctl restart ofn
curl -s -H "Host: studio.master-painting.com" http://127.0.0.1:8793/sabaapp | grep -n "const tg"
# hypno
cd ~/hypno-fugu-mini && python3 -m pytest -q
sudo systemctl restart hypno-fugu-mini
curl -s -m3 http://127.0.0.1:8895/health
```

قواعد: D-22 (بدون jargon) · اسم قبل از auth نه · async بدون `.catch` نه · «اصلاح شد» فقط بعد از curl سرو‌شده.

---

## ۶) شروع سریع

```
۱. این فایل + CLAUDE.md + HANDOFF.md (بخش قلم‌های باز)
۲. §۱ را زنده اجرا کن
۳. اگر HTTPS=530 و آری اجازه داد → فاز ۱ تونل+NTP
۴. فاز ۲.۱ (ziman فارسی) و ۲.۲ (hypno delete) را انجام بده
۵. suite سبز · HANDOFF تازه · از آری برای commit بپرس
```

اگر تست قرمز دیدی: **نام تست + چرا** را گزارش کن؛ دور نزن و حذف نکن.
