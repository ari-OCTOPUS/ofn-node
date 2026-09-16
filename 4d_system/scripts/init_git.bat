@echo off
REM ============================================================
REM B10: independent git repo for 4d_system + pre-commit hook
REM Why: this folder sat under the parent home repo (C:\Users\Armin)
REM      -> no independent history, no pre-evolve tags.
REM Run: double-click, or from cmd:  scripts\init_git.bat
REM
REM NOTE: messages are ASCII-only on purpose. cmd.exe parses this
REM       file in the OEM codepage; Persian text inside the .bat
REM       broke execution (verified 2026-07-11 - script jumped to
REM       :err and never ran git init). Logic is unchanged.
REM ============================================================
cd /d "%~dp0.."

if exist .git (
    echo [i] .git already exists - only configuring the hook.
) else (
    git init || goto :err
)

git config core.hooksPath scripts/hooks
echo [i] pre-commit hook active: no commit without a green suite.

git add -A
git commit -m "baseline: 4d_system independent repo (post-audit, suite green)" || echo [i] nothing to commit.

echo.
echo [OK] Done. Before any big evolve: git tag pre-evolve-YYYYMMDD
goto :eof

:err
echo [X] git not found - install Git for Windows (git-scm.com)
exit /b 1
