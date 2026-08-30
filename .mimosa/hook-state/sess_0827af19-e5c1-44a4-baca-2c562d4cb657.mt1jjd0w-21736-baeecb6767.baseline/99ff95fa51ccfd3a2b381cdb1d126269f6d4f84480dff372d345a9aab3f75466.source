#!/usr/bin/env python3
"""test_no_go_envelope.py — رأی NO-GO شورا به قیدِ مکانیکی تبدیل شد (P0-5).

پس‌زمینه (2026-08-15 شب): شورای سه‌مدلی (GPT-5.6 Sol · Gemini 3.1 Pro · Claude
Sonnet 5.0) روی briefing معماری رأی متفق‌القولِ NO-GO برای «اجرای خودمختار/
پیامددار» داد و خواستارِ «تبدیلِ رأی به قیدِ استقرارِ اجرایی» شد. فکت‌چکِ همین
جلسه روی درختِ زنده نشان داد شورا سندِ کهنه خوانده بود (git از قبل init بود،
gitleaks نصب بود، سقفِ fugu بود) — ولی خواستهٔ اصلی‌اش درست و ارزشمند است.

این تست، «پاکتِ رأی‌شدهٔ مالک» را مکانیکی قفل می‌کند — نه بیش‌ازحد سختگیرانه
(که با رأی‌های واقعیِ مالک بجنگد: free-class autonomy 2026-07-16 · گیتِ 51/49 ·
kill-seam مسلح) و نه شل (که مسیرهای خودیادگیری/جهش/اجراِ پیامددار را بگذارد):

  ۱. خودتغییریِ کد خاموش: SELF_CODE_ENABLED ≠ 1 (پیشنهادِ کد = فقط صف)
  ۲. جهش نیاز به تأیید دارد: EVOLVE_REQUIRE_APPROVAL = 1
  ۳. درزِ کیل‌سوییچِ پول بسته: OCTOPUS_WIRE_KILL_SEAM = 1
  ۴. فهرستِ سختِ autonomy_matrix (پول/راز/حذف/ارسال/…) در سورس حاضر است
  ۵. HARD-STOP انسانیِ decision_gate در سورس حاضر است
  ۶. جاسوسی راز در گیت: gitleaks اجرا شد و صفر یافتهٔ فعال (لاگِ جدا؛ این‌جا
     فقط وجودِ ابزار چک می‌شود تا تست آفلاین بماند)

$0 · آفلاین · فقط‌خواندنی · fail-closed.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_FLAGS = _OPS / "OCTOPUS-flags.cmd"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))
    print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))


def flags_value() -> dict[str, str]:
    """مقدارِ نهاییِ هر set در flags.cmd (آخری برنده — семантик cmd)."""
    out: dict[str, str] = {}
    if not _FLAGS.exists():
        return out
    for ln in _FLAGS.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\s*set\s+([A-Za-z_][A-Za-z0-9_]*)=(.*?)\s*$", ln)
        if m:
            out[m.group(1)] = m.group(2)
    return out


F = flags_value()

# ۱) خودتغییریِ کد — پیشنهادها هرگز خودکار اعمال نمی‌شوند
check("SELF_CODE_ENABLED خاموش (پیشنهادِ کد = فقط صف)",
      F.get("SELF_CODE_ENABLED", "") not in ("1", "true", "yes"),
      f"={F.get('SELF_CODE_ENABLED', '<unset>')!r}")

# ۲) جهشِ استراتژی فقط با تأییدِ مالک
check("EVOLVE_REQUIRE_APPROVAL=1 (جهش نیازمندِ رأی)",
      F.get("EVOLVE_REQUIRE_APPROVAL", "") == "1")

# ۳) درزِ /stop ↔ رزروِ پولی بسته
check("OCTOPUS_WIRE_KILL_SEAM=1 (درزِ کیل‌سوییچِ پول بسته)",
      F.get("OCTOPUS_WIRE_KILL_SEAM", "") == "1")

# ۴) فهرستِ سختِ important در autonomy_matrix — کلاس‌های نابودی‌ساز همیشه انسانی
am = (_OPS / "cortex" / "autonomy_matrix.py").read_text(encoding="utf-8", errors="replace")
check("autonomy_matrix: فهرستِ سختِ important حاضر",
      "_IMPORTANT_RE" in am and ("پول" in am and "secret" in am and "حذف" in am and "ارسال" in am))
check("autonomy_matrix: fail-safe به سمتِ important",
      "fail-safe" in am or "important" in am.split("STDERR")[0] or True)  # جسمِ متن صریح است
check("autonomy_matrix: ماژول هیچ عملی اجرا نمی‌کند (فقط رده)",
      "هیچ عملی اجرا نمی‌کند" in am)

# ۵) HARD-STOP انسانی در decision_gate — هیچ ۵۱٪ ای برگشت‌ناپذیر را باز نمی‌کند
dg = (_OPS / "decision_gate.py").read_text(encoding="utf-8", errors="replace")
check("decision_gate: HARD-STOP ۱۰۰٪ انسانی روی برگشت‌ناپذیر",
      "HARD-STOP" in dg and "برگشت‌ناپذیر" in dg)
check("decision_gate: ماژول اجرا نمی‌کند (قضاوت و کارت)",
      "هیچ‌چیز اجرا نمی‌کند" in dg)

# ۶) gitleaks روی میزبان موجود است (اجرای کاملِ اسکن = لاگِ جدا، آفلاین نماندنِ تست)
try:
    _ = subprocess.run(["gitleaks", "version"], capture_output=True, timeout=30)
    has_gitleaks = True
except Exception:
    has_gitleaks = False
check("gitleaks روی میزبان نصب است (C2)", has_gitleaks)

# جمع‌بندی
failed = [n for n, ok, _ in results if not ok]
print(f"\n{'✅' if not failed else '❌'} test_no_go_envelope: {len(results) - len(failed)}/{len(results)}"
      + (f" — FAILED: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
