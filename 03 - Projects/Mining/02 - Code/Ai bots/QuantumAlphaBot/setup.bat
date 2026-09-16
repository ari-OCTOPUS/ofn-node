@echo off
echo ================================
echo   QuantumAlpha Bot - Setup
echo ================================

:: بررسی وجود Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.11 from https://python.org
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Installing packages...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt

echo [3/3] Setting up .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created — please edit it and add your API keys!
) else (
    echo .env already exists, skipping.
)

echo.
echo ================================
echo   Setup complete!
echo   Next steps:
echo   1. Edit .env and add your API keys
echo   2. Run: venv\Scripts\activate
echo   3. Run: python main.py --once --no-exec
echo ================================
pause
