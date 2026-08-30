#!/usr/bin/env python3
"""capability_gate — گیتِ توانایی برای هر مسیرِ پولِ واقعیِ زنده (A3، open-decision #2 قفل‌شدهٔ آری 2026-07-07).

live_gate.is_open(action) = True فقط اگر هر سه با AND برقرار باشند:
  (۱) capability : markerِ سبزِ سوئیت موجود (budget_gate v2 + همهٔ تست‌های A سبز) — فقط اجرای سبزِ کاملِ
      سوئیت (run_all) آن را می‌نویسد؛ هر شکست revokeش می‌کند (fail-closed). ناوگان هرگز نمی‌نویسد.
  (۲) LIVE_ENABLED: پرچمی که فقط انسان از طریقِ ApprovalChannel روشن می‌کند — نه ناوگان، نه تاریخ.
  (۳) per-action approval: یک تأییدِ انسانیِ match‌خورده از ApprovalChannel.
calendar ≠ capability: رسیدنِ 2026-07-21 یا هر تاریخِ دیگری به‌تنهایی هیچ گیتی باز نمی‌کند.

هر اقدامِ پولِ واقعی باید هم از این گیت و هم از money_gate رد شود → require().
الان: Telegram وصل نیست (NotWiredStub) + LIVE_ENABLED غایب → همیشه بسته (حالتِ مطلوبِ فازِ paper).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib                                              # noqa: E402
import money_gate                                          # noqa: E402
from approval_channel import ApprovalChannel, NotWiredStub  # noqa: E402

CAPABILITY_MARKER = opslib.STATE_DIR / "CAPABILITY-OK.flag"   # فقط اجرای سبزِ کاملِ سوئیت می‌نویسد
LIVE_ENABLED_FLAG = opslib.STATE_DIR / "LIVE-ENABLED.flag"    # فقط انسان می‌سازد (مثل ACTIVATION-*.flag)


def _gate_source_files() -> list[Path]:
    """کدِ پول که سبزیِ سوئیت اثباتش می‌کند. تغییرِ هرکدام → fingerprintِ نو → markerِ کهنه بی‌اعتبار
    (markerِ سبزِ کدِ قدیم هرگز مجوزِ کدِ نو نمی‌شود — سفت‌کاریِ verdict آری Track B)."""
    here = Path(__file__).resolve().parent
    return [Path(__file__).resolve(),
            Path(money_gate.__file__).resolve(),
            here / "approval_channel.py",
            here / "organ_gate.py",
            opslib.SCRIPTS / "budget_gate.py"]


def _source_fingerprint() -> str:
    h = hashlib.sha256()
    for f in sorted(_gate_source_files(), key=lambda p: p.name):
        try:
            h.update(f.name.encode("utf-8") + b"\0" + f.read_bytes())
        except OSError:
            h.update(b"<MISSING:" + f.name.encode("utf-8") + b">")
    return h.hexdigest()


def capability_ok() -> bool:
    """marker موجود باشد و fingerprintِ کدِ پول همان باشد که هنگام آخرین سبزیِ سوئیت ثبت شد.
    کد پس از آن تغییر کرده → mismatch → بی‌اعتبار (fail-closed). هر خطای خواندن/parse = بسته."""
    try:
        data = json.loads(CAPABILITY_MARKER.read_text("utf-8"))
    except (OSError, ValueError):
        return False
    return bool(data.get("fingerprint")) and data.get("fingerprint") == _source_fingerprint()


def live_enabled() -> bool:
    return LIVE_ENABLED_FLAG.exists()


_MIN_SUITE_FILES = 100          # سوئیتِ واقعی امروز ۳۶۸ فایل دارد؛ ۱۰۰ کفِ محافظه‌کارانه


def _is_live_marker() -> bool:
    """آیا مارکری که می‌نویسیم همان مارکرِ **زنده** است، یا کپیِ ایزولهٔ یک تست؟"""
    try:
        live = (Path(__file__).resolve().parent.parent / "state").resolve()
        return CAPABILITY_MARKER.parent.resolve() == live
    except OSError:
        return True             # شک = سخت‌گیرانه رفتار کن


def _is_suite_evidence(evidence) -> bool:
    """شواهدِ معتبر = فهرستِ **ماشینیِ** تست‌ها، نه نثرِ دست‌نویس."""
    s = str(evidence or "")
    if not s.startswith("green: "):
        return False
    names = [x.strip() for x in s[len("green: "):].split(",")]
    return sum(1 for n in names if n.endswith(".py")) >= _MIN_SUITE_FILES


def mark_capability(evidence: str) -> bool:
    """فقط از مسیرِ اجرای سبزِ کاملِ سوئیت (run_all). fingerprintِ کدِ پول را به marker می‌بندد.

    ۲۰۲۶-۰۷-۲۸ — تا امروز این جمله فقط یک **قرارداد** بود: تابع هیچ گاردی نداشت
    و هر کدی می‌توانست مارکرِ گیتِ پول را بنویسد. همان روز کسی با این شواهد نوشتش:

        "green-canary: 5/5 held-out canaries pass; 2 pre-existing red (…)"

    یعنی نثرِ دست‌نویسی که **خودش به دو قرمز اعتراف می‌کرد** تبدیل شد به مجوزِ
    عبور از گیتِ پول. آن روز بی‌ضرر بود (یکی از دو قرمز تستی کهنه بود و دیگری
    سبز)، ولی این «امنیتِ تصادفی» است نه ساختاری.

    گارد عمداً فقط روی **مارکرِ زنده** می‌نشیند: تستِ ایزوله (ORG_ROOT موقت)
    آزاد است، چون نمی‌تواند به گیتِ واقعی دست بزند. روی درختِ زنده، شواهد باید
    فهرستِ ماشینیِ ≥۱۰۰ فایلِ تست باشد — چیزی که فقط `run_all` می‌سازد.

    fail-closed: شواهدِ نامعتبر → **هیچ مارکری نوشته نمی‌شود** و هشدار می‌رود.
    نبودِ مارکر یعنی capability بسته، که سمتِ امنِ خطاست.
    خروجی: True اگر واقعاً نوشته شد.
    """
    if _is_live_marker() and not _is_suite_evidence(evidence):
        try:
            opslib.alert([
                "capability_gate: mark_capability با شواهدِ غیرِسوئیت رد شد — "
                f"مارکر نوشته نشد. شواهد: {str(evidence)[:80]!r}"])
        except Exception:  # noqa: BLE001
            pass
        return False
    CAPABILITY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    CAPABILITY_MARKER.write_text(json.dumps(
        {"ts": opslib.now_iso(), "evidence": evidence, "fingerprint": _source_fingerprint()},
        ensure_ascii=False), "utf-8")
    return True


def revoke_capability() -> None:
    """هر شکستِ سوئیت = لغوِ توانایی (fail-closed)."""
    try:
        CAPABILITY_MARKER.unlink()
    except OSError:
        pass


def is_open(action_id: str, amount_aud: float,
            channel: ApprovalChannel | None = None) -> tuple[bool, str]:
    if not capability_ok():
        return False, "no-capability (سوئیت سبزِ اثبات‌شده نیست)"
    if not live_enabled():
        return False, "LIVE_ENABLED off (فقط انسان از ApprovalChannel — نه تاریخ/ناوگان)"
    ch = channel or NotWiredStub()
    appr = ch.approval_for(action_id=action_id, amount_aud=amount_aud)
    if appr is None or not appr.valid:
        return False, f"no per-action approval via {ch.name}"
    return True, "open"


def require(action_id: str, amount_aud: float,
            channel: ApprovalChannel | None = None) -> dict:
    """دروازهٔ واحدِ هر اقدامِ پولِ واقعی: باید هم capability_gate هم money_gate رد شود (fail-closed).
    هر مسیرِ کدِ effectorِ پولِ واقعی باید این را صدا بزند، نه گیت‌ها را جدا."""
    ok, why = is_open(action_id, amount_aud, channel)
    if not ok:
        return {"allow": False, "gate": "live_gate", "reason": why}
    m = money_gate.check(amount_aud, action_id, channel)
    if not m["allow"]:
        return {"allow": False, "gate": "money_gate", "reason": m["reason"]}
    return {"allow": True, "reason": "capability ∧ live_enabled ∧ approval ∧ money_gate"}
