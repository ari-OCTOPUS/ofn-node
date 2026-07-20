"""
دریافت Telegram chat_id و ذخیره در .env
========================================
اول به ربات @Robo2725_bot یه پیام بفرست، بعد این اسکریپت رو اجرا کن.
"""
import sys, re, requests
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# C11: secrets come from .env via config.py (no python-dotenv dependency)
from config import TELEGRAM_TOKEN as TOKEN
if not TOKEN:
    print("[!] TELEGRAM_TOKEN در .env نیست")
    sys.exit(1)

print(f"Bot token: {TOKEN[:25]}...")
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=10)
updates = r.json().get("result", [])
print(f"Updates count: {len(updates)}")

if not updates:
    print()
    print("[!] No messages found.")
    print("[!] STEPS:")
    print("    1. Open Telegram")
    print("    2. Search: @Robo2725_bot")
    print("    3. Click START")
    print("    4. Send any message (e.g. hello)")
    print("    5. Re-run this script")
    sys.exit(1)

# آخرین پیام
msg = updates[-1].get("message", {})
chat = msg.get("chat", {})
chat_id = chat.get("id")
user_name = msg.get("from", {}).get("first_name", "?")
print(f"[OK] Chat ID: {chat_id}  (user: {user_name})")

# ذخیره در .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path, encoding="utf-8") as f:
    content = f.read()
if re.search(r"^TELEGRAM_CHAT_ID=.*$", content, flags=re.MULTILINE):
    content = re.sub(r"^TELEGRAM_CHAT_ID=.*$",
                     f"TELEGRAM_CHAT_ID={chat_id}",
                     content, flags=re.MULTILINE)
else:
    content += f"\nTELEGRAM_CHAT_ID={chat_id}\n"
with open(env_path, "w", encoding="utf-8") as f:
    f.write(content)
print("[OK] Saved to .env")

# پیام تست
r = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": chat_id,
        "text": "*QuantumAlpha v3*\nConnection OK!\nBot will send signals every 6 hours.",
        "parse_mode": "Markdown",
    },
    timeout=10,
)
print(f"Test message: HTTP {r.status_code}")
if r.status_code == 200:
    print("[OK] Check your Telegram!")
else:
    print(f"[!] Error: {r.text[:200]}")
