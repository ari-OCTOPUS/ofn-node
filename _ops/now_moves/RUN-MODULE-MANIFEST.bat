@echo off
REM RUN-MODULE-MANIFEST.bat — M6: build a read-only registry of Octopus's own code
REM modules (purpose/entrypoints/deps/imported-by/wire-flags) + resolved flag state
REM + innervation freshness → state/cortex/module-manifest.json. Read-only scan.
REM Add --dry to print the summary WITHOUT writing the manifest file.
setlocal
cd /d "%~dp0"
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
python -X utf8 module_self_manifest.py %*
endlocal
