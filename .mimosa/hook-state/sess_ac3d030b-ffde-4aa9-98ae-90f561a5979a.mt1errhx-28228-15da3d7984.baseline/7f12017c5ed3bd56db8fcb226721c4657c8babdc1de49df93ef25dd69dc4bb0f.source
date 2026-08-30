"""
Setup Script — TESSERACT v0.4
==============================
این اسکریپت بررسی می‌کند که محیط آماده اجرا هست یا نه.

اجرا:
    python setup_v04.py
"""

import sys
import os
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 60)
print("  TESSERACT v0.4 — Environment Check")
print("=" * 60)

# ── ۱. Python version ─────────────────────────────────────────────────────────
print(f"\n[1/5] Python version: {sys.version.split()[0]}")
if sys.version_info < (3, 9):
    print("   [!] نیاز به Python 3.9+ داری")
    sys.exit(1)
print("   [OK]")

# ── ۲. کتابخانه‌ها ────────────────────────────────────────────────────────────
print("\n[2/5] Required packages...")
required = ["requests", "beautifulsoup4", "python-dotenv"]
missing = []
for pkg in required:
    try:
        if pkg == "beautifulsoup4":
            import bs4
        elif pkg == "python-dotenv":
            from dotenv import load_dotenv
        else:
            __import__(pkg)
        print(f"   [OK] {pkg}")
    except ImportError:
        missing.append(pkg)
        print(f"   [!!] {pkg} — نصب نشده")

if missing:
    print(f"\n   نصب: pip install {' '.join(missing)}")
    answer = input("\n   الان نصب کنم؟ (y/n): ").strip().lower()
    if answer == "y":
        subprocess.run([sys.executable, "-m", "pip", "install", *missing])

# ── ۳. .env ──────────────────────────────────────────────────────────────────
print("\n[3/5] .env file...")
env_path = os.path.join(os.path.dirname(__file__), ".env")
env_example = os.path.join(os.path.dirname(__file__), ".env.example")

if not os.path.exists(env_path):
    if os.path.exists(env_example):
        print("   [!] .env موجود نیست — از .env.example کپی می‌کنم")
        with open(env_example, encoding="utf-8") as f:
            content = f.read()
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   [OK] .env ساخته شد. لطفاً کلیدها رو پر کن: {env_path}")
    else:
        print("   [!!] .env و .env.example هر دو موجود نیستن")
else:
    print(f"   [OK] {env_path}")

# ── ۴. کلیدها ────────────────────────────────────────────────────────────────
print("\n[4/5] API keys check...")
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

keys = {
    "GITHUB_TOKEN":      "required",
    "COINGECKO_API_KEY": "optional",
    "SOCHAIN_API_KEY":   "optional",
    "ANTHROPIC_API_KEY": "optional",
}
for k, status in keys.items():
    val = os.getenv(k, "")
    if val:
        masked = val[:8] + "..." if len(val) > 8 else "[short]"
        print(f"   [OK] {k} = {masked}  ({status})")
    else:
        tag = "[!!]" if status == "required" else "[--]"
        print(f"   {tag} {k} — empty  ({status})")

# ── ۵. ساختار فایل‌ها ────────────────────────────────────────────────────────
print("\n[5/5] Project files...")
required_files = ["config.py", "pqc_classifier.py", "tesseract_v04.py"]
project_dir = os.path.dirname(__file__)
for f in required_files:
    path = os.path.join(project_dir, f)
    if os.path.exists(path):
        size_kb = os.path.getsize(path) / 1024
        print(f"   [OK] {f}  ({size_kb:.1f} KB)")
    else:
        print(f"   [!!] {f} — موجود نیست!")

print("\n" + "=" * 60)
print("  آماده اجرا!  دستور:  python tesseract_v04.py")
print("=" * 60)
