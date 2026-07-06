@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Second Brain — Setup
cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
  echo [!] Python پیدا نشد. از python.org نصبش کن و "Add to PATH" را تیک بزن.
  pause & exit /b 1
)

if not exist control-brain\.venv (
  echo [1/3] ساخت محیط مجازی و نصب پکیج‌ها (فقط بار اول، ~۱-۲ دقیقه)...
  python -m venv control-brain\.venv
  call control-brain\.venv\Scripts\activate
  pip install -q -r control-brain\requirements.txt
  if exist painting-bot\requirements.txt pip install -q -r painting-bot\requirements.txt
) else (
  call control-brain\.venv\Scripts\activate
)

where node >nul 2>nul
if not errorlevel 1 (
  if exist accounting-bot\package.json if not exist accounting-bot\node_modules (
    echo [+] نصب پکیج‌های ربات حسابداری (npm)...
    pushd accounting-bot & call npm install --silent & popd
  )
)

echo [2/3] باز کردن صفحهٔ راه‌اندازی مغز دوم در مرورگر...
echo [3/3] ترتیب: فرم → ذخیره → 📡 گزارش اتصال → 🚀 روشن کردن. این پنجره با