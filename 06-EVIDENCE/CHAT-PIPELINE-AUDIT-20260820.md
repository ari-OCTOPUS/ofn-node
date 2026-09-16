# CHAT-PIPELINE-AUDIT — reasoning/structured-output/reliability (2026-08-20 ~01:0xZ)

## ۱) نقشهٔ خط لولهٔ چت (verified by grep)

| لایه | ماژول | نقش | وضعیت reasoning |
|---|---|---|---|
| Client | `_ops/debate/client.py` | تنها مصرف‌کنندهٔ خام API؛ content-only (فیکس 261030f) + reasoning_content برای شواهد | ✅ هیچ `or`-fallback |
| مرکز تلگرام | `telegram_center/chat_room.py`, `ask_brain.py` | چت مالک | ✅ صفر ارجاع reasoning_content |
| لوپ | `live_loop.py` | رأی/چت | ✅ صفر ارجاع |
| داور Live-4 | `live4_harness.judge_choice_v3` | قرارداد سخت تک‌کلید | ✅ فقط content |
| کل مخزن | grep `reasoning_content` | فقط client.py | ✅ **نشت: صفر سطح** |

## ۲) یافته‌ها

| # | یافته | درجه |
|---|---|---|
| F1 | نشت reasoning به history: **هیچ مسیری** reasoning را در messages بازنمی‌گرداند — multi-turn امن از نظر سازنده | VERIFIED (grep) |
| F2 | قرارداد داور فقط content را می‌خواند؛ fallback تک‌توکنی جدا | VERIFIED |
| F3 | خروجی plain judge در probe اخیر **خالی** برگشت → همان نویز ۱۳.۶٪؛ فرمت اولیه به‌تنهایی کافی نیست | OBSERVED |
| F4 | `--reasoning-parser` در این دپلوی (client-hosted API) N/A است؛ فقط برای vLLM خودمیزبان | VOID (محلی) |
| F5 | structured_outputs: هنوز probe نشده (endpoint میزبان پشتیبانی‌اش را باید سنجید) | UNKNOWN |

## ۳) توصیه‌های پیکربندی (برای vLLM/Dynamo خودمیزبان آینده)

```bash
# reasoning
vllm serve deepseek-ai/DeepSeek-V3 \
  --enable-reasoning --reasoning-parser deepseek_r1        # DeepSeek: تگ‌های think
vllm serve Qwen/Qwen3-8B \
  --enable-reasoning --reasoning-parser qwen3              # Qwen3: فیلد reasoning مستقل

# داور: ساختار اجباری، نه prompt
#   extra_body={"structured_outputs": {"choice": ["A","B","TIE"]}}   ← روش اصلی
#   stop=["\n"," "] فقط fallback سازگاری (whitespace ابتدایی → خروجی خالی ممکن است)

# تعیّن
VLLM_BATCH_INVARIANT=1   # کرنل‌های deterministic؛ throughput پایین‌تر، قابل‌قبول برای داور
# پین نسخه: مدل، vLLM version، reasoning-parser، structured-output backend → در receipt
```

## ۴) گام‌های بعدی (پیش از اتکا)

1. probe سازگاری structured_outputs روی endpoint میزبان (یک فراخوان؛ اگر 400/unknown → LEGACY_GUIDED_CHOICE → stop → fallback تک‌توکنی، هر مرحله با ثبت)
2. normalizer چندمرحله‌ای: content→history، reasoning→evidence (الگوی normalize_assistant_message)
3. بعد از پایداری ابزار: ablation چهاربازویی M+/M−/P/B
