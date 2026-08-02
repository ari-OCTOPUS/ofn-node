---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [telegram, audit, uniformity, falsifiable]
created: 2026-07-28
---

# ممیزیِ مسیرِ ارسال — **دو فرستنده، دو سیاستِ تاپیک**

## ۱) اول یک سبزِ دروغین که خودم ساختم

اولین ممیزیِ ایستا روی `center.py` گفت **صفر تخلف**: هر ۱۰ مسیرِ پاسخ
`topic_id=` را پاس می‌دادند. همان لحظه لاگِ زنده ۴۸ پیامِ بی‌تاپیک نشان می‌داد.
هر دو راست می‌گفتند:

```python
topic_id=self._reply_thread(msg)     # ایستا ✅ پاس داده شده
                                     # زنده  ❌ None، چون فلگ لود نیست
```

پس ابزارِ تشخیصِ نقطهٔ کور، خودش یک نقطهٔ کور داشت. `_ops/tg_send_audit.py`
حالا **سه** طبقه دارد نه دو، و `certain` فقط به لیترالِ عددی داده می‌شود:

| طبقه | یعنی | تعداد در درخت |
|---|---|---|
| `certain` | `topic_id=28` — ایستا اثبات‌شده | **۰** |
| `conditional` | `topic_id=<هر عبارتِ اجرایی>` — **ممکن است زنده None شود** | **۲۲** |
| `absent` | اصلاً تاپیک ندارد — قطعاً General | **۵** |
| `dm` | خصوصیِ مالک، تاپیک بی‌معناست | **۲** |

> صفر بودنِ `certain` عمدی نیست ولی گویاست: **هیچ ارسالی در کلِ سیستم تاپیکش
> ایستا تضمین‌شده نیست.** همه‌شان به یک مقدارِ زمانِ‌اجرا وابسته‌اند.

## ۲) کشفِ اصلی: دو فرستندهٔ کاملاً مستقل

```
tg_api.TgClient.send(text, *, topic_id=…)        ← پارامترِ صریحِ تاپیک دارد
approval_channel.ApprovalChannel.send_text(…)    ← topic_id **ندارد**
```

`send_text` تاپیک را فقط از روی `stream` حدس می‌زند، و آن هم مشروط
(`approval_channel.py:1467`):

```python
thread = None
if chat_id is None and stream:          # ← فقط این‌جا تاپیک می‌خورد
    r_chat, r_topic = _stream_route(stream)
    ...
```

یعنی: **هر پاسخِ مستقیمی که `chat_id`ِ گروه بگیرد، از این مسیر همیشه بی‌تاپیک
می‌رود.** هیچ فلگی این را درست نمی‌کند. سه نمونهٔ زنده، همه در `poll_once()` —
یعنی مسیرِ جوابِ فرمان:

```
approval_channel.py:530   send_text(..., chat_id=chat_id, reply_markup=…)
approval_channel.py:543   send_text(..., chat_id=chat_id, reply_markup=…)
approval_channel.py:547   send_text(reply, chat_id=chat_id)
```

دو تای دیگر در `center.py`:

```
center.py:430    ensure_setup()          chat_id + pin=True   ← پیامِ pin‌شده،
                                                                General درست است
center.py:1613   _handle_map_callback()  فقط chat_id          ← احتمالاً باگ
```

## ۳) پس ۴۸ پیامِ General از کجا آمد

`stream` در لاگ برای `TgClient.send` **هاردکد** است روی `"center"`
(`tg_api.py:298`). هر ۴۸ پیامِ بدمسیر `stream=center` دارند → از مسیرِ اول
آمده‌اند. و در `center.py` توزیعِ عباراتِ تاپیک این است:

| عبارت | تعداد | زنده چه می‌شود |
|---|---|---|
| `self._reply_thread(msg)` | **۱۷** | `None` تا وقتی فلگ لود نشود |
| `topics.get('system')` | ۳ | ۲۸ — درست |
| `topics.get(leg)` | ۱ | درست (burstِ ۲۲:۰۳ ثابتش کرد) |
| هیچ | ۲ | General |

**نتیجه‌گیری (VERIFIED از ترکیبِ ایستا + لاگِ زنده):** بخشِ بزرگِ ۴۸ پیام از
`_reply_thread(msg) → None` می‌آید، و **فقط با ری‌استارت** درست می‌شود.
مسیرِ `approval_channel` جدا و **درست نمی‌شود** — کد لازم دارد.

## ۴) اصلاحِ پیشنهادی برای مسیرِ دوم (افزودنی، پیش‌فرض بی‌اثر)

```python
def send_text(self, text, reply_markup=None, chat_id=None,
              stream=None, topic_id=None):     # ← پارامترِ نو
    ...
    thread = _coerce_id(topic_id) if topic_id is not None else None
    if thread is None and chat_id is None and stream:
        ...                                    # منطقِ فعلی، دست‌نخورده
```
بدونِ پاس‌دادنِ `topic_id` رفتار **بایت‌به‌بایت** همان است. بعد در `poll_once`
هر سه فراخوان `topic_id=<threadِ پیامِ ورودی>` بگیرند، پشتِ همان فلگِ
`OCTOPUS_TG_TOPIC_REPLY` تا یک رأیِ رفتاری دو مسیر را هم‌زمان روشن کند.

## ۵) چرخ‌دنده‌ای که از این به بعد نگهش می‌دارد

`_ops/tests/test_tg_send_audit.py` — **۲۰/۲۰**. دو سنجه ratchet شده‌اند و
خط‌پایه‌شان را بارِ اول **از واقعیت** می‌سازند
(`_ops/tests/_baselines/tg-send-audit.json`) نه از عددِ هاردکد — چون این ممیزی
روی یک کپیِ ناقص از درخت اندازه گرفته شد و خط‌پایهٔ ثابت می‌توانست روی ماشینِ
کامل یک **قرمزِ دروغین** بسازد.

| سنجه | حالا | قاعده |
|---|---|---|
| `absent` | ۵ | فقط اجازهٔ کم‌شدن دارد |
| `reply_absent` | ۰ | فقط اجازهٔ کم‌شدن دارد |

هر ویرایشی که یک ارسالِ بی‌تاپیکِ تازه اضافه کند، سوئیت قرمز می‌شود.
هر اصلاحی که یکی کم کند، خط‌پایه خودکار سفت‌تر و برگشت‌ناپذیر می‌شود.

## ۶) اجرا

```
python _ops/tg_send_audit.py            # کلِ درخت، خلاصهٔ انسانی
python _ops/tg_send_audit.py --json     # ماشین‌خوان
python _ops/tests/test_tg_send_audit.py
```

ثبت در سوئیت (کنارِ سه تستِ قبلی):
```python
    "test_gate_report.py", "test_flag_drift.py", "test_tg_trace.py",
    "test_tg_send_audit.py",
```

## ۷) آنچه هنوز **NOT VERIFIED** است

* کدام‌یک از ۱۷ فراخوانِ `_reply_thread` دقیقاً آن ۴۸ پیام را ساخت — لاگ
  `sha` دارد نه نامِ تابع. اگر لازم شد، افزودنِ `site=` به `tg_send_log.record`
  این را برای همیشه حل می‌کند.
* آیا در درختِ کامل فایلِ دیگری هم `.send(`/`.send_text(` دارد — این ممیزی روی
  ~۲۵ فایلِ staged اجرا شد. `python _ops/tg_send_audit.py` روی خودِ ماشین
  جوابِ کامل را می‌دهد، و ratchet بارِ اول همان را خط‌پایه می‌کند.
* هیچ تستی روی خودِ ماشین اجرا نشد (این نشست شل نداشت).
