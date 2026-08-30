# -*- coding: utf-8 -*-
"""C-047 (دستور #۱۱ §۲): preflight ریاستارت + کامنت اصلاح‌شدهٔ bat.

۱) منطق تصمیم: RESTART فقط وقتی restart-requested بدون STOP/halt؛
   restart+STOP ⇒ صدای ABORT_RESTART_STOP_PRESENT و خروج STOP.
۲) کامنت سرِ RUN-ORGANISM.bat پروتکل تک‌مارکری را توصیف کند، نه جفت‌مارکری."""
import re
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]


def decide(restart_req: bool, stop: bool, halted: bool):
    """بازتولید منطق organism.py (preflight C-047)."""
    if restart_req and stop:
        return "STOP", "ABORT_RESTART_STOP_PRESENT"
    if restart_req and not halted:
        return "RESTART", None
    if stop or halted:
        return "STOP", None
    return "RUN", None


def test_restart_only_marker_yields_restart():
    assert decide(True, False, False) == ("RESTART", None)


def test_stop_alone_yields_stop():
    assert decide(False, True, False)[0] == "STOP"
    assert decide(False, False, True)[0] == "STOP"


def test_restart_plus_stop_aborts_loudly():
    why, alarm = decide(True, True, False)
    assert (why, alarm) == ("STOP", "ABORT_RESTART_STOP_PRESENT")


def test_organism_has_preflight_string():
    src = (_OPS / "organism.py").read_text(encoding="utf-8")
    assert "ABORT_RESTART_STOP_PRESENT" in src


def test_bat_comment_documents_single_marker_protocol():
    bat = (_OPS / "RUN-ORGANISM.bat").read_text(encoding="utf-8")
    assert "create ONLY" in bat and "RESTART-REQUESTED" in bat
    # پروتکل کهنهٔ جفت‌مارکری دیگر توصیه نشود:
    bad = re.search(r"[Cc]lear both", bat)
    assert not bad, "stale dual-marker protocol text still present"


def test_no_repo_script_writes_dual_markers():
    """§۱۰ دستور #۱۲: هیچ اسکریپتی نباید STOP-ORGANISM را همراه RESTART-REQUESTED
    بنویسد (ریشهٔ C-047). اسکن استاتیک repo — بدون اجرا."""
    import re as _re
    offenders = []
    for pat in ("*.ps1", "*.bat", "*.cmd", "*.py"):
        for p in _OPS.rglob(pat):
            s = str(p)
            if "__pycache__" in s or "/tests/" in s.replace("\\", "/"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # نوشتنِ هر دو مارکر در یک فایل = جفت‌مارکر
            has_stop = _re.search(r"Set-Content\s+-Path\s+\$?stop|touch[^\n]*STOP-ORGANISM|"
                                  r"open\([^\n]*STOP-ORGANISM[^\n]*['\"]w", text)
            has_rest = "RESTART-REQUESTED" in text and _re.search(
                r"Set-Content\s+-Path\s+\$?rest|touch[^\n]*RESTART-REQUESTED|"
                r"open\([^\n]*RESTART-REQUESTED[^\n]*['\"]w", text)
            if has_stop and has_rest:
                offenders.append(str(p.relative_to(_OPS)))
    assert not offenders, f"dual-marker writers still present: {offenders}"
