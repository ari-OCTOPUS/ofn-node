"""Scar-aware verify test (v0.4.7). Pure stdlib; run: python tests/scar_verify_test.py

Exercises: verify_scar_aware() — پذیرشِ خطِ پاره فقط وقتی hash دُم توسط prev رکوردِ
بعدی لنگر شده؛ ردِ لنگرِ جعلی؛ ردِ tamper؛ ردِ پارگیِ بی‌لنگر (خط آخر)؛
پیکانِ سن monotonic از رویِ scar. verify() قدیمی باید روی پارگی FAIL بماند.
Exit code 0 = pass, 1 = fail.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ledger"))

from ledger import Ledger  # noqa: E402


def _fresh(tmpname: str) -> tuple[Ledger, Path]:
    p = Path(tempfile.mkdtemp()) / tmpname
    return Ledger(p), p


def _tear_line(path: Path, lineno: int) -> str:
    """خطِ lineno را مثل torn-write واقعی سر می‌بُرد (دُم با hash می‌ماند).
    برمی‌گرداند: خطِ پاره‌شده."""
    lines = path.read_text(encoding="utf-8").splitlines()
    original = lines[lineno - 1]
    cut_at = original.index('"payload"')          # سر بریده از وسطِ یک کلید
    torn = original[cut_at:]
    lines[lineno - 1] = torn
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return torn


def main() -> int:
    # 1) ledger سالم: هر دو verify سبز
    lg, p = _fresh("clean.jsonl")
    for i in range(4):
        lg.append("HEARTBEAT", {"n": i}, actor="guardian", beat=True)
    ok, msg = lg.verify()
    assert ok, f"clean verify failed: {msg}"
    ok, msg = lg.verify_scar_aware()
    assert ok and msg == "ok", f"clean scar-aware failed: {msg}"

    # 2) پارگیِ لنگرشده در وسط: verify قدیمی FAIL می‌ماند، scar-aware صادقانه OK
    lg, p = _fresh("torn.jsonl")
    for i in range(5):
        lg.append("HEARTBEAT", {"n": i}, actor="guardian", beat=True)
    _tear_line(p, 2)
    lg2 = Ledger(p)
    ok_old, msg_old = lg2.verify()
    assert not ok_old, "verify قدیمی باید روی پارگی FAIL بماند (LAW unchanged)"
    ok_new, msg_new = lg2.verify_scar_aware()
    assert ok_new, f"scar-aware باید پارگیِ لنگرشده را بپذیرد: {msg_new}"
    assert "ok-with-scars: 1" in msg_new and "[2]" in msg_new, msg_new

    # 3) پیکان سن از روی scar فقط monotonic — بعدش دوباره سخت
    #    (رکورد ۳ سنِ ۳ دارد؛ scar سنِ ۲ را بلعیده — نباید FAIL شود)
    #    همین ledger مورد ۲ کافی است: رکوردهای beat سن 1..5 داشتند، scar سن ۲.
    #    ok_new بالا یعنی عبور کرد؛ حالا برگشتِ سن باید هنوز مرگ باشد:
    lines = p.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[-1])
    rec["age_tick"] = 0                            # برگشتِ پیکان (بدون fix هش — tamper هم هست)
    lines.append(json.dumps(rec, ensure_ascii=False))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok_bad, msg_bad = Ledger(p).verify_scar_aware()
    assert not ok_bad, "برگشت/دستکاری بعد از scar باید FAIL باشد"

    # 4) لنگرِ جعلی: hash دُمِ خطِ پاره عوض شود → FAIL
    lg, p = _fresh("fake-anchor.jsonl")
    for i in range(4):
        lg.append("HEARTBEAT", {"n": i}, actor="guardian", beat=True)
    torn = _tear_line(p, 2)
    lines = p.read_text(encoding="utf-8").splitlines()
    lines[1] = torn[:-10] + "deadbeef00" + torn[-2:] if torn.endswith('"}') else torn
    # سادگی و قطعیت: کل hash دُم را با hex جعلی هم‌طول جایگزین کن
    import re
    lines[1] = re.sub(r'[0-9a-f]{64}', "0" * 64, lines[1])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok_fake, msg_fake = Ledger(p).verify_scar_aware()
    assert not ok_fake, f"لنگرِ جعلی نباید پذیرفته شود: {msg_fake}"

    # 5) tamper در رکوردِ سالم هنوز مرگ است (scar-aware سهل‌گیر نیست)
    lg, p = _fresh("tamper.jsonl")
    for i in range(3):
        lg.append("HEARTBEAT", {"n": i}, actor="guardian", beat=True)
    lines = p.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[1])
    rec["payload"] = {"n": 999}
    lines[1] = json.dumps(rec, ensure_ascii=False)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok_t, msg_t = Ledger(p).verify_scar_aware()
    assert not ok_t and "tamper" in msg_t, f"tamper باید گرفته شود: {msg_t}"

    # 6) پارگیِ خطِ آخر (بی‌لنگر — هیچ رکوردِ بعدی تأییدش نمی‌کند) → FAIL
    lg, p = _fresh("torn-tail.jsonl")
    for i in range(3):
        lg.append("HEARTBEAT", {"n": i}, actor="guardian", beat=True)
    _tear_line(p, 3)
    ok_tail, msg_tail = Ledger(p).verify_scar_aware()
    assert not ok_tail, f"پارگیِ بی‌لنگر نباید پذیرفته شود: {msg_tail}"

    print("OK: scar_verify_test — 6/6 (verify قدیمی دست‌نخورده، scar فقط با لنگرِ تأییدشده)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
