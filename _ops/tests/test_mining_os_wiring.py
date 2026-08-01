#!/usr/bin/env python3
"""test_mining_os_wiring.py — زیر-OSِ Mining باید **صداکننده** داشته باشد.

باگی که این فایل را ساخت (۲۰۲۶-۰۷-۲۸): بستهٔ `mining_os/` در `88aaa29` کامیت شد —
۲۴ فایل، ۳۲ تستِ سبز — ولی هوکِ صداکننده‌اش هرگز کامیت نشد. `ACTIVATION.md`
می‌نوشت «وصل‌شده به organism.py:712»؛ آن خط در واقع بلوکِ **فیشر** بود و grep روی
کلِ `_ops` صفر ارجاع به mining_os می‌داد. سه فلگی هم که رانبوک «روشن کن» می‌گفت
(`_OS`/`_UI`/`_VERDICT_SYNC`) در هیچ `.py` و هیچ `.cmd` وجود نداشتند.

یعنی یک بستهٔ کامل با تست‌های سبز که **هرگز اجرا نمی‌شد** — و تست‌های خودش این را
نمی‌دیدند، چون همه درون-بسته‌اند: «سبز به‌خاطرِ نبودِ صداکننده».

پس این فایل شکلِ بسته را نمی‌سنجد (کارِ `mining_os/tests`)؛ فقط می‌سنجد که
**راهی از ارگانیسم به آن وجود دارد** و فلگ‌خاموش بایت‌به‌بایتِ امروز است.
"""
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness   # noqa: E402
ENV = harness.setup("mining-os-wiring")

import wiring    # noqa: E402

_ORGANISM = (_HERE.parent / "organism.py").read_text("utf-8")
_CENTER = (_HERE.parent / "telegram_center" / "center.py").read_text("utf-8")


def _flag_off():
    os.environ.pop("OCTOPUS_WIRE_MINING_OS", None)


# ── ۱. فلگ‌خاموش = رفتارِ امروز ────────────────────────────────────────────────
def t_flag_absent_returns_none():
    _flag_off()
    assert wiring.mining_os_beat(beat=1, write=False) is None


def t_flag_zero_returns_none():
    os.environ["OCTOPUS_WIRE_MINING_OS"] = "0"
    try:
        assert wiring.mining_os_beat(beat=1, write=False) is None
    finally:
        _flag_off()


def t_flag_is_owner_gated_not_in_paper_profile():
    """فعال‌سازی باید رأیِ صریحِ مالک باشد — نه اثرِ جانبیِ apply_profile."""
    assert "OCTOPUS_WIRE_MINING_OS" not in wiring.PAPER_FULL_FLAGS


# ── ۲. فلگ‌روشن = ضربانِ صادق (نه live جعلی) ───────────────────────────────────
def t_flag_on_returns_honest_skeleton():
    os.environ["OCTOPUS_WIRE_MINING_OS"] = "1"
    try:
        res = wiring.mining_os_beat(beat=7, write=False)
        assert isinstance(res, dict), f"خروجی dict نیست: {type(res)}"
        snap = res.get("mining_os") or {}
        assert snap.get("leg") == "mining", snap.get("leg")
        assert res.get("beat") == 7 and snap.get("beat") == 7
        # تا دادهٔ واقعیِ ناوگان/برق نیامده، live جعل نمی‌شود
        assert snap.get("live") is False, "live بدونِ دادهٔ واقعی True شد"
        assert snap.get("wallet_access") is False, "D-11: صفر دسترسیِ wallet"
    finally:
        _flag_off()


def t_stop_organism_wins_over_flag():
    """kill-switch مقدم بر فلگ است (بدونِ ساختِ فایلِ STOPِ واقعی در درختِ زنده)."""
    os.environ["OCTOPUS_WIRE_MINING_OS"] = "1"
    import opslib
    _real = opslib.STOP_ORGANISM
    _fake = Path(ENV["state"] if isinstance(ENV, dict) and "state" in ENV
                 else _HERE) / "_fake-STOP-ORGANISM"
    try:
        _fake.write_text("test", encoding="utf-8")
        opslib.STOP_ORGANISM = _fake
        assert wiring.mining_os_beat(beat=1, write=False) is None
    finally:
        opslib.STOP_ORGANISM = _real
        _fake.unlink(missing_ok=True)
        _flag_off()


# ── ۳. گاردِ اصلی: صداکننده واقعاً وجود دارد ───────────────────────────────────
def t_organism_actually_calls_the_beat():
    """همان گاردی که نبودش بسته را یتیم کرد. تعریفِ تابع کافی نیست — call site لازم است."""
    assert "mining_os_beat" in _ORGANISM, (
        "organism.py هیچ‌جا mining_os_beat را صدا نمی‌زند — بسته دوباره یتیم شد")
    assert re.search(r'"mining_os":\s*_mining_os', _ORGANISM), (
        "نتیجهٔ ضربان در ORGANISM-STATE merge نمی‌شود — یعنی هیچ‌کس نمی‌بیندش")


def t_center_routes_the_mining_verb():
    """دکمهٔ `mo:` باید در جدولِ dispatch باشد وگرنه کلیک به هیچ‌جا نمی‌رسد."""
    i = _CENTER.index("def _handle_callback")
    # کلِ بدنهٔ تابع — پنجرهٔ ثابتِ ۴۰۰۰ با رشدِ dispatch (۰۷-۳۱) قلابی قرمز می‌شد.
    _j = _CENTER.find("\n    def ", i + 1)
    body = _CENTER[i:_j if _j != -1 else len(_CENTER)]
    assert re.search(r'verb\s*==\s*"mo"', body), "فعلِ mo در _handle_callback مسیر ندارد"
    assert "_handle_mining_callback" in _CENTER, "handlerِ mo تعریف نشده"


def t_mining_command_is_flag_gated_and_bridge_safe():
    """`/mining` پشتِ فلگ ثبت می‌شود، پس باید در _CENTRE_GATED هم باشد —
    وگرنه پلِ دو-باتی تصمیمِ فلگ را دور می‌زند (قراردادِ test_two_bot_bridge)."""
    assert '"/mining"' in _CENTER
    m = re.search(r'_CENTRE_GATED\s*=\s*\{([^}]*)\}', _CENTER)
    assert m and "/mining" in m.group(1), "/mining در _CENTRE_GATED نیست"


def t_ui_is_dark_until_the_owner_flips_the_flag():
    """`_mining_ui` باید **اول** فلگ را بسنجد؛ import بی‌گارد = روشن‌شدنِ ناخواسته."""
    i = _CENTER.index("def _mining_ui")
    body = _CENTER[i:i + 900]
    fl = body.find("OCTOPUS_WIRE_MINING_UI")
    imp = body.find("import")
    assert fl != -1, "فلگِ UI در _mining_ui چک نمی‌شود"
    assert imp == -1 or fl < imp, "فلگ بعد از import سنجیده می‌شود — گاردِ بی‌اثر"


def t_write_false_touches_no_file_in_the_live_tree():
    """قولِ `write=False` باید واقعی باشد — روی **اثر** سنجیده، نه روی فلگ.

    شاهدِ تاریخی (۲۰۲۶-۰۸-۰۱): `mining_os/state/last-beat.json` مقدارِ `beat: 7`
    داشت — عددی که در تولید هیچ‌جا نیست و فقط از همین فایل می‌آمد. `write=False`
    فقط سایدکارِ `_ops` را ساکت می‌کرد و `loop.tick` داخلِ بسته بی‌قید می‌نوشت.
    """
    _syspath = str((_HERE.parents[1] / "03 - Projects" / "Mining").resolve())
    if _syspath not in sys.path:
        sys.path.insert(0, _syspath)
    from mining_os import loop as _loop           # noqa: WPS433 — lazy

    snap_path = Path(_loop._SNAPSHOT)
    before = (snap_path.exists(),
              snap_path.stat().st_mtime_ns if snap_path.exists() else None,
              snap_path.read_bytes() if snap_path.exists() else None)

    os.environ["OCTOPUS_WIRE_MINING_OS"] = "1"
    try:
        wiring.mining_os_beat(beat=4242, write=False)
    finally:
        _flag_off()

    after = (snap_path.exists(),
             snap_path.stat().st_mtime_ns if snap_path.exists() else None,
             snap_path.read_bytes() if snap_path.exists() else None)
    assert before == after, (
        f"write=False فایلِ زنده را عوض کرد: {snap_path}")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mining_os_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
