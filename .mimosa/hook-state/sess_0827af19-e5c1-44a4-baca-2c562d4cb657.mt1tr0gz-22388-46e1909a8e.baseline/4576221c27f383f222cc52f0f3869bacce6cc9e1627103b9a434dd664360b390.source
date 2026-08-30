"""
راهنمای نصب Telegram برای QuantumAlpha
=========================================
اجرا کنید:  python setup_telegram.py

این اسکریپت:
  1. توکن ربات Telegram رو از شما می‌گیره
  2. صحیح بودنش رو آزمایش می‌کنه
  3. chat_id شما رو به‌صورت خودکار پیدا می‌کنه
  4. یک پیام آزمایشی ارسال می‌کنه
  5. مقادیر رو در .env ذخیره می‌کنه
"""

import sys
import os
import re
import time
import webbrowser

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests


# ── Step 1: توضیح ─────────────────────────────────────────────────────────────

print("""
============================================================
  QuantumAlpha — Telegram Setup
============================================================

مراحل:
  1. تلگرام را باز کنید
  2. جستجو کنید: @BotFather
  3. بنویسید: /newbot
  4. یک اسم انتخاب کنید (مثلاً: QuantumAlphaBot)
  5. یک username انتخاب کنید که به "bot" ختم شه (مثلاً: MyQuantumBot)
  6. BotFather یک توکن به شکل زیر می‌دهد:
       <REDACTED-TELEGRAM-TOKEN>
  7. آن توکن را اینجا وارد کنید.

------------------------------------------------------------
""")

# ── Step 2: گرفتن توکن ────────────────────────────────────────────────────────

while True:
    token = input("توکن ربات (از BotFather): ").strip()
    if not token:
        print("توکن خالی است. لطفا دوباره وارد کنید.")
        continue

    # تست توکن
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=10,
    )
    if r.status_code == 200:
        bot_info = r.json().get("result", {})
        bot_name = bot_info.get("username", "?")
        print(f"\n[OK] ربات شناسایی شد: @{bot_name}\n")
        break
    else:
        print(f"[Error] توکن اشتباه است (HTTP {r.status_code}). دوباره امتحان کنید.\n")

# ── Step 3: پیدا کردن Chat ID ─────────────────────────────────────────────────

print(f"""
حالا به ربات @{bot_name} یک پیام بفرستید.
  1. در تلگرام ربات خود را جستجو کنید: @{bot_name}
  2. روی Start کلیک کنید
  3. هر پیامی بنویسید (مثلاً: hello)

سپس Enter بزنید تا chat ID خوانده شود...
""")

input("بعد از ارسال پیام، Enter بزنید...")

chat_id = ""
for attempt in range(3):
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        timeout=10,
    )
    updates = r.json().get("result", [])
    if updates:
        msg = updates[-1].get("message", {})
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id:
            user_name = msg.get("from", {}).get("first_name", "?")
            print(f"[OK] Chat ID پیدا شد: {chat_id}  (کاربر: {user_name})")
            break
    if attempt < 2:
        print(f"پیامی دریافت نشد. لطفاً در تلگرام به ربات @{bot_name} پیام بفرستید...")
        time.sleep(3)

if not chat_id:
    print("[Error] Chat ID پیدا نشد. لطفاً دستی وارد کنید.")
    chat_id = input("Chat ID: ").strip()

# ── Step 4: ارسال پیام آزمایشی ────────────────────────────────────────────────

print("\nارسال پیام آزمایشی...")
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={
        "chat_id": chat_id,
        "text": (
            "*QuantumAlpha v3* — اتصال برقرار شد!\n\n"
            "ربات معاملاتی آماده است.\n"
            "هر 6 ساعت گزارش تحلیل ارسال می‌شود."
        ),
        "parse_mode": "Markdown",
    },
    timeout=10,
)

if r.status_code == 200:
    print("[OK] پیام آزمایشی ارسال شد — گوشی خود را چک کنید!")
else:
    print(f"[Error] ارسال ناموفق: {r.text}")

# ── Step 5: ذخیره در .env ─────────────────────────────────────────────────────

env_path = os.path.join(os.path.dirname(__file__), ".env")

# خواندن .env فعلی
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        env_content = f.read()
else:
    env_content = ""

# جایگزینی یا اضافه کردن مقادیر
def set_env_var(content: str, key: str, value: str) -> str:
    pattern = rf"^{key}=.*$"
    replacement = f"{key}={value}"
    if re.search(pattern, content, flags=re.MULTILINE):
        return re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        return content + f"\n{key}={value}"

env_content = set_env_var(env_content, "TELEGRAM_TOKEN", token)
env_content = set_env_var(env_content, "TELEGRAM_CHAT_ID", chat_id)

with open(env_path, "w", encoding="utf-8") as f:
    f.write(env_content)

print(f"""
============================================================
  [OK] تنظیمات ذخیره شد در .env

  TELEGRAM_TOKEN   = {token[:20]}...
  TELEGRAM_CHAT_ID = {chat_id}

  حالا ربات شما هر 6 ساعت گزارش می‌فرستد.
  برای اجرا:  python main.py
============================================================
""")
