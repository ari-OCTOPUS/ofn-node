# studio/ — استودیوی محتوای صبا

> نقشهٔ ماژول · ۲۰۲۶-۰۸-۰۳

## نقش
استودیوی creator برای صبا. تولید، تأیید، و انتشار درفت‌های compliant (faceless/feet-only). دوکلیده: صبا ثبت → آری تأیید → انتشار. self-cert اجباری.

## Entry points
| فایل | دستور | نقش |
|---|---|---|
| `creator_brain.py` | `python studio/creator_brain.py` | مغزِ creator standalone |
| `creator_studio.py` | `python studio/creator_studio.py` | استودیوی standalone |
| `run-studio.bat` | `.bat` | بوتِ ویندوزی |

## کتابخانه‌ها
`content_studio` (هسته) · `affirm` · `studio_telegram_v3` (در langar_bot reference شده)

## فایل‌های state
- `config.json` — پیکربندی (analytics، PPV prices، trend feed، calendar)
- `drafts.json` — لیستِ درفت‌ها (persistence، restart-safe)
- `for_saba.json` — پیام‌های outgoing به creator
- `HALT` — file-existence = halt
- `capacity.json` — ظرفیتِ creator

## Env vars
| کلید | نقش |
|---|---|
| `PF_STUDIO_DIR` | مسیرِ studio (تست/harness؛ default = کنارِ ماژول) |

## وابستگی‌ها
- **درون‌پروژه‌ای**: `brain/dual_brain_v3`، `brain/store`
- **خارجی**: صفر (stdlib-only)

## قواعد قفل‌شده
- فقط متادیتا/پلن — هرگز رسانه/هویت/PII
- self-cert اجباری (faceless ✅ · فقط‌پا ✅ · بدون explicit ✅ · ۱۸+/رضایت ✅)
- پرداخت فقط درون‌پلتفرم
- محدودهٔ صبا مقدمِ مطلق (یک‌ضربه halt)

## تست‌ها
`test_affirm` · `test_creator_brain` · `test_creator_studio` + `tests/test_state_machines.py`
