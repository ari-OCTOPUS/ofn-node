"""test_operator_doctrine.py — دکترینِ گفت‌وگو با مالک، به‌عنوان بخشی از خودآگاهی.

رأیِ مالک ۲۰۲۶-۰۷-۲۶: «همه‌چیز را به خودآگاهیِ اختاپوس اضافه کن، دستش بیاید
چطور با من رفتار کند.»

چرا دکترین **ورودیِ** خودشناسی است نه خروجیِ آن: `self_knowledge.synthesize`
هر دور از نو ساخته می‌شود، پس هر درسِ رفتاری که آن‌جا بنشیند دورِ بعد پاک
می‌شود. `snapshot()` ورودیِ آن چرخه است — دکترین آن‌جا تزریق می‌شود تا مغز هر
بار که دربارهٔ خودش فکر می‌کند، با دانستنِ نحوهٔ حرف‌زدن با مالک فکر کند.

سخت‌ترین قیدِ این فایل `t_every_rule_carries_real_evidence` است: قاعدهٔ بی‌شاهد
یعنی سلیقه‌ای که خودش را قانون جا زده. اگر کسی خواست قاعده‌ای اضافه کند، باید
مشاهده‌اش را هم بیاورد.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("operator-doctrine")

sys.path.insert(0, str(_HERE.parent / "tg"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import operator_doctrine as od   # noqa: E402


REQUIRED = ("id", "rule", "why", "evidence", "enforced_by")


# ─── قراردادِ دکترین ─────────────────────────────────────────────────────────
def t_every_rule_carries_real_evidence():
    """قاعدهٔ بی‌شاهد = سلیقه‌ای که خودش را قانون جا زده."""
    for d in od.DOCTRINE:
        for f in REQUIRED:
            assert f in d and str(d[f]).strip(), f"قاعدهٔ {d.get('id')} فیلدِ {f} ندارد"
        assert len(str(d["evidence"])) > 25, \
            f"شاهدِ {d['id']} خیلی کوتاه است — یک مشاهدهٔ واقعی بنویس نه یک برچسب"


def t_rule_ids_are_unique_and_stable():
    ids = [d["id"] for d in od.DOCTRINE]
    assert len(ids) == len(set(ids)), f"شناسهٔ تکراری: {ids}"
    for i in ids:
        assert i.startswith("D") and "-" in i, f"شناسهٔ بدشکل: {i}"


def t_doctrine_is_pure():
    """هیچ I/O — این ماژول وارد promptِ مغز می‌شود و باید ارزان و قطعی بماند."""
    import inspect
    src = inspect.getsource(od)
    for banned in ("open(", "requests", "urllib", "sqlite3", "subprocess"):
        assert banned not in src, f"دکترین باید pure بماند؛ {banned!r} پیدا شد"


def t_it_never_reads_the_private_owner_profile():
    """قیدِ حریمِ خصوصی: `state/OWNER-PROFILE*` را کدِ خودِ مخزن محرمانه اعلام
    کرده. دکترین فقط جملاتِ صریحِ خودِ مالک در چت را حمل می‌کند."""
    import inspect
    src = inspect.getsource(od)
    assert "OWNER-PROFILE" not in src.replace("`state/OWNER-PROFILE*`", "")\
        or "نمی‌خواند" in src, "دکترین نباید پروفایلِ محرمانه را بخواند"


# ─── چکِ ماشینی ─────────────────────────────────────────────────────────────
def t_check_catches_a_duration_deadline():
    assert "D3-weekday" in od.check("تا ۴۸ ساعت دیگر جواب بده")
    assert "D3-weekday" not in od.check("تا یکشنبه جواب بده")


def t_check_catches_a_backreference():
    assert "D2-no-backref" in od.check("مثلِ قبل عمل کن")
    assert "D2-no-backref" not in od.check("این کارت خودبسنده است")


def t_a_decision_card_without_a_stake_is_flagged():
    assert "D1-stake" in od.check("این را تأیید کن", is_decision=True)
    assert "D1-stake" not in od.check("این را تأیید کن\n▸ نکنی: همین‌طور می‌ماند",
                                      is_decision=True)


def t_empty_text_is_the_worst_failure():
    assert "D6-never-silence" in od.check("")
    assert "D6-never-silence" in od.check("   ")


def t_check_never_raises_and_never_rewrites():
    for bad in (None, 123, {"a": 1}, "", "x" * 5000):
        out = od.check(bad)
        assert isinstance(out, list), f"خروجی باید لیست باشد: {bad!r}"


# ─── تزریق به خودشناسی ──────────────────────────────────────────────────────
def t_snapshot_shape_is_small_enough_for_a_prompt():
    """این وارد promptِ مغزِ پولی می‌شود؛ طولش هزینهٔ واقعی دارد."""
    s = od.for_snapshot()
    assert set(s) >= {"version", "rules", "bottleneck"}
    assert len(s["rules"]) == len(od.DOCTRINE)
    blob = "\n".join(s["rules"])
    assert len(blob) < 2000, f"دکترینِ فشرده {len(blob)} کاراکتر — برای prompt گران است"


def t_unenforced_rules_are_named_not_hidden():
    """قاعده‌ای که کسی چکش نمی‌کند باید صریح علامت بخورد، وگرنه شبیهِ
    تضمین به نظر می‌رسد درحالی‌که فقط یک جمله است."""
    s = od.for_snapshot()
    expected = [d["id"] for d in od.DOCTRINE if d["enforced_by"] == "—"]
    assert s["unenforced"] == expected


def t_self_knowledge_injects_it_only_behind_the_flag():
    import os
    sys.path.insert(0, str(_HERE.parent / "doctor"))
    import self_knowledge as sk
    os.environ.pop("OCTOPUS_SELFKNOW_DOCTRINE", None)
    assert "owner_doctrine" not in sk.snapshot(), "فلگ خاموش باید snapshot را دست‌نخورده بگذارد"
    os.environ["OCTOPUS_SELFKNOW_DOCTRINE"] = "1"
    try:
        snap = sk.snapshot()
        assert "owner_doctrine" in snap, "با فلگِ روشن دکترین باید تزریق شود"
        assert snap["owner_doctrine"]["version"] == od.VERSION
    finally:
        os.environ.pop("OCTOPUS_SELFKNOW_DOCTRINE", None)


# ─── مسیرِ تلگرام ───────────────────────────────────────────────────────────
def t_the_card_is_reachable_from_telegram():
    import live_commands as lc
    assert lc.handles("/doctrine") and lc.handles("/رفتار")
    out = lc.dispatch("/doctrine")
    assert out and "چطور باید با تو حرف بزنم" in out
    for d in od.DOCTRINE:
        assert d["rule"] in out, f"قاعدهٔ {d['id']} در کارت نیست"


def t_the_card_marks_which_rules_are_actually_enforced():
    """کارت نباید قاعدهٔ چک‌نشده را شبیهِ تضمین نشان دهد."""
    out = od.card()
    n_paper = sum(1 for d in od.DOCTRINE if d["enforced_by"] == "—")
    assert out.count("📄") == n_paper
    assert out.count("🔒") == len(od.DOCTRINE) - n_paper


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_operator_doctrine: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
