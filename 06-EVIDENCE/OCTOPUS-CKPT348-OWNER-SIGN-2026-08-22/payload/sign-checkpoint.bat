@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (set PY=py -3) else (set PY=python)
%PY% -c "import nacl.signing" 2>nul || %PY% -m pip install --user pynacl
%PY% "%~dp0sign_checkpoint.py"
pause
