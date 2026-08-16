"""test_seam_live_refresh_20260816.py — SEAM-LOOP C1: قفلِ درزِ OctopusLiveDataRefresh.

درز سه‌لایه بود (2026-08-16):
  1) اکشن تسک به مسیر Desktopِ mojibake می‌رفت → FILE_NOT_FOUND (-2147024894)
  2) bat با «python» لخت → در بافت تسک پیدا نمی‌شود؛ cmd خطاها را می‌بلعد و
     کد خروجِ آخرین echo صفر است = «موفقیتِ دروغگو» (تسک سبز، کار صفر)
  3) extract_telegram_commands.py:220 → NameError: has_handler (محلیِ تابع دیگر)
     → خروجی از 2026-07-13 مرده بود

این تست دو رگرسیونِ ساختاری را قفل می‌کند (سبک و قطعی، بدون اجرای کامل):
  A) bat باید CRLF خالص باشد و هیچ «python» لختی نداشته باشد (python مطلق)
  B) extract_telegram_commands.py باید compile شود و has_handler در main تعریف شده باشد
"""
import ast
from pathlib import Path

NVS = Path(__file__).resolve().parents[2] / "nervous-system"
BAT = NVS / "refresh-live-data.bat"
EXTRACTOR = NVS / "extract_telegram_commands.py"


def test_bat_pure_crlf():
    b = BAT.read_bytes()
    assert b.count(b"\r\n") > 100, "bat باید CRLF باشد — LF خالص پارسِ cmd را می‌شکند"
    assert b.replace(b"\r\n", b"").count(b"\n") == 0, "LF لخت ممنوع (درس SEAM-LOOP C1)"


def test_bat_no_bare_python_absolute_only():
    for line in BAT.read_text("utf-8", errors="replace").splitlines():
        ls = line.strip()
        if ls.lower().startswith("python "):
            raise AssertionError(f"python لخت در بافت تسک = no-op بی‌صدا: {ls[:60]}")
    assert 'set "PY_EXE=C:\\Program Files\\Python313\\python.exe"' in BAT.read_text("utf-8", errors="replace"), \
        "PY_EXE مطلق (الگوی Watch) باید تعریف باشد"


def test_telegram_extractor_runs_clean():
    """قفلِ واقعی C1: استخراجگر باید بدون NameError تا انتها برود و خروجی بدهد.
    (رگرسیونِ has_handler — قبل از فیکس همین اجرا می‌ترکید.)"""
    import subprocess, sys
    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(EXTRACTOR)],
        cwd=str(NVS), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"extractor failed:
{r.stderr[-400:]}"
    assert "refreshed" in (r.stdout or ""), f"خروجی انتظار 'refreshed': {r.stdout[-200:]}"
