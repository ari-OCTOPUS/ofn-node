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


def test_telegram_extractor_compiles_and_has_local_has_handler():
    src = EXTRACTOR.read_text("utf-8")
    tree = ast.parse(src)  # NameErrorِ سطح-ماژول اینجا نمی‌گیرد؛ برای آن، جستجوی تعریف:
    main_fn = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "main")
    assigned = {t.id for n in ast.walk(main_fn) if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)}
    used = {n.id for n in ast.walk(main_fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    undefined = {u for u in used if u not in assigned and u not in
                 {"print", "len", "dict", "set", "str", "int", "frozenset", "sorted"}}  # builtins رایج
    assert not undefined, f"متغیر بدون تعریف در main(): {undefined} (درزِ C1 همین بود: has_handler)"
