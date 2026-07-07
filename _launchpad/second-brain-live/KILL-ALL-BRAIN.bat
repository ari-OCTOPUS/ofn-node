@echo off
chcp 65001 >nul
title Kill all brain instances
echo در حال بستن همهٔ نمونه‌های مغز: app.py / wizard / panels ...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
echo تمام شد. حالا START-HERE.bat را دوباره اجرا کن (فقط یک‌بار 🚀).
pause
