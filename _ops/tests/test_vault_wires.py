"""test_vault_wires.py — اولین سیم‌هایی که دانشِ ابسیدین را به رفتار وصل کردند.

اسکنِ ۲۰۲۶-۰۷-۲۷ (۲۵ ایجنت، هر یافته با ایجنتِ متخاصمِ جدا راستی‌آزمایی) نشان
داد هیچ خطِ کدی در `_ops` هرگز فایل‌های مارک‌داونِ vault را باز نمی‌کند. سه چیز
از آن اسکن این‌جا قفل می‌شود:

  ۱) **تشدیدِ وارونهٔ سؤال‌ها.** شرط `heads[-1] >= today()` یعنی سؤال فقط همان
     روزِ پرسیده‌شدن دیده می‌شد و فردایش برای همیشه نامرئی — هرچه معطل‌تر،
     نامرئی‌تر. اندازه‌گیری: ۳۰ سربرگ، قدیمی‌ترین ۲۰۲۶-۰۷-۰۴، صفر نمایش.
  ۲) **مطالبهٔ چیزی که مالک پارک کرده.** `VQ-ACCT-PARK` با کلماتِ خودِ مالک
     حساب‌کتاب را متوقف کرده بود، ولی «💵 CSV واریزی‌ها نیست» هر روز صدرِ لیست بود.
  ۳) **دکمه‌های بی‌مسیر** — در `test_callback_routing.py` جدا قفل شده.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("vault-wires")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import needs_digest as nd   # noqa: E402


def _seed_questions(dates):
    p = Path(ENV["root"]) / "00 - Inbox" / "AGENT_QUESTIONS.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# سوالات\n\n" + "\n\n".join(f"## {d}\n- یک سوال" for d in dates),
                 "utf-8")


def _seed_queue(text):
    (Path(ENV["root"]) / "VERDICT_QUEUE.md").write_text(text, "utf-8")


def _items():
    return nd.compute().get("items") or []


# ─── ۱: تشدیدِ سؤال باید با کهنگی **بیشتر** شود، نه کمتر ────────────────────
def t_an_old_unanswered_question_becomes_more_visible_not_less():
    _seed_questions(["2026-07-04", "2026-07-16"])
    txt = " ".join(_items())
    assert "AGENT_QUESTIONS" in txt, "سؤالِ کهنه اصلاً دیده نشد"
    assert "2026-07-04" in txt, f"قدیمی‌ترین تاریخ گزارش نشد: {txt}"
    assert "روز" in txt, "سنِ سؤال گزارش نشد"


def t_a_question_asked_today_is_still_reported():
    _seed_questions([opslib.today()])
    txt = " ".join(_items())
    assert "AGENT_QUESTIONS" in txt, txt


def t_no_questions_file_is_silent_not_an_error():
    p = Path(ENV["root"]) / "00 - Inbox" / "AGENT_QUESTIONS.md"
    if p.exists():
        p.unlink()
    txt = " ".join(_items())
    assert "AGENT_QUESTIONS" not in txt
    assert isinstance(nd.compute().get("n"), int)


# ─── ۲: پارکِ مالک باید ساکت کند ────────────────────────────────────────────
def t_a_parked_domain_stops_being_demanded():
    _seed_queue("| VQ-ACCT-PARK | حساب‌کتاب متوقف | **PARKED — دست نزن** | x |\n")
    assert nd._owner_parked("ACCT") is True
    assert not any("CSV واریزی" in i for i in _items()), \
        "چیزی که مالک پارک کرده هنوز مطالبه می‌شود"


def t_an_unparked_domain_is_still_demanded():
    """گاردِ معکوس: پارک نباید به بهانه‌ای برای سکوتِ کلی تبدیل شود."""
    _seed_queue("| VQ-OTHER-001 | چیزِ دیگر | open | x |\n")
    assert nd._owner_parked("ACCT") is False
    assert any("CSV واریزی" in i for i in _items()), \
        "بدونِ پارک، نیازِ واقعی باید دیده شود"


def t_a_missing_or_broken_queue_fails_open():
    """fail-OPEN عمدی: سکوتِ اشتباه بدتر از نویزِ اشتباه است — ارگانیسم نباید
    به‌خاطرِ یک خطای خواندن نیازی را از چشمِ مالک پنهان کند."""
    p = Path(ENV["root"]) / "VERDICT_QUEUE.md"
    if p.exists():
        p.unlink()
    assert nd._owner_parked("ACCT") is False
    _seed_queue("متنِ آزاد بدونِ جدول\n| ناقص\n")
    assert nd._owner_parked("ACCT") is False


def t_park_detection_is_domain_scoped():
    """پارکِ یک حوزه نباید حوزهٔ دیگری را ساکت کند."""
    _seed_queue("| VQ-ACCT-PARK | x | **PARKED** | y |\n")
    assert nd._owner_parked("ACCT") is True
    assert nd._owner_parked("LEAD") is False
    assert nd._owner_parked("") is False


# ─── ۳: قرارداد کلی ────────────────────────────────────────────────────────
def t_the_digest_never_grows_unbounded():
    """۳۰ سربرگ نباید به ۳۰ آیتم تبدیل شود."""
    _seed_questions([f"2026-07-{d:02d}" for d in range(1, 26)])
    items = _items()
    q = [i for i in items if "AGENT_QUESTIONS" in i]
    assert len(q) == 1, f"{len(q)} خطِ سؤال — باید یک خطِ خلاصه باشد"
    for i in items:
        assert len(i) <= 120, f"آیتمِ بلند ({len(i)}): {i[:60]}"


def t_no_secret_or_pii_shaped_string_reaches_the_digest():
    import re
    _seed_questions(["2026-07-04"])
    pat = re.compile(r"(sk-|bot\d{6,}:|ghp_|AKIA|-----BEGIN)", re.I)
    for i in _items():
        assert not pat.search(i), i


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_vault_wires: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
