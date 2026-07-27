"""test_bcm_feed_and_verdicts.py — دو سیمی که یادگیری و آگاهیِ مالک را وصل کردند.

۱) **BCM هرگز activation نمی‌گرفت.** `bcm-weights.json` بعد از ۶۵ قدم `keys: {}`
   داشت، در حالی که `wire_bcm: true` بود. ریشه در امضای خودِ `BCM.step` است:
   «BCM هرگز خودش key اختراع نمی‌کند» — فقط `known_keys` را دنبال می‌کند، و
   هیچ‌کس هرگز کلیدی نداده بود. پس کلِ ریاضیِ ضدِ اشباع روی مجموعهٔ تهی می‌دوید.

۲) **ارگانیسم نمی‌دانست منتظرِ چیست.** `VERDICT_QUEUE.md` صفِ تصمیم‌های مالک است
   (۴۸ ردیفِ باز)، و خودآگاهی هرگز بازش نمی‌کرد — پس کاری را که پشتِ رأیِ باز
   قفل بود دوباره پیشنهاد می‌داد و هرگز نمی‌توانست بگوید «منتظرِ توام».
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("bcm-feed-verdicts")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "neural"), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import wiring          # noqa: E402


# ─── ۱: واژگانِ BCM باید با منبعِ سیگنال هم‌گام بماند ────────────────────────
def t_the_bcm_vocabulary_covers_every_signal_the_source_can_emit():
    """اگر واژگان و تولیدکننده از هم جدا بیفتند، سیگنالِ تازه هرگز کلید نمی‌گیرد و
    بی‌صدا از یادگیری بیرون می‌ماند — همان کوریِ اصلی با شکلِ تازه."""
    import inspect
    import re
    src = inspect.getsource(wiring._hebbian_signals)
    literal = set(re.findall(r'sig\.append\("([a-z_]+)"\)', src))
    missing = literal - set(wiring.BCM_VOCAB)
    assert not missing, f"سیگنالِ بی‌کلید: {sorted(missing)}"
    # شاخهٔ f-string ِ ریتم سه حالتِ ممکن دارد
    if 'sig.append(f"rhythm_' in src:
        for c in ("rhythm_amber", "rhythm_yellow", "rhythm_red"):
            assert c in wiring.BCM_VOCAB, f"{c} در واژگان نیست"
    assert len(set(wiring.BCM_VOCAB)) == len(wiring.BCM_VOCAB), "کلیدِ تکراری"


def t_a_fired_signal_reinforces_and_a_silent_one_decays():
    """قراردادِ BCM: آتش‌کرده y=1 (تقویت)، غایب y=0 (زوال). اگر فقط آتش‌کرده‌ها را
    بدهیم، نیمهٔ فراموشی مرده می‌ماند."""
    from bcm import BCMStabilizer
    p = Path(ENV["ops"]) / "state" / "bcm-test.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    b = BCMStabilizer(persist_path=p)
    vocab = list(wiring.BCM_VOCAB)
    for _ in range(6):
        b.step({"errors_high": 1.0}, known_keys=vocab)
    assert set(b.keys()) == set(vocab), "BCM همهٔ واژگان را نمی‌شناسد"
    hot = b.weight("errors_high")
    cold = b.weight("budget_tight")
    assert hot is not None and cold is not None
    assert hot > cold, f"سیگنالِ آتش‌کرده تقویت نشد: {hot} vs {cold}"


def t_bcm_never_invents_keys_so_the_vocabulary_is_the_only_source():
    from bcm import BCMStabilizer
    p = Path(ENV["ops"]) / "state" / "bcm-test2.json"
    b = BCMStabilizer(persist_path=p)
    b.step({"ghost_signal": 1.0})          # بدونِ known_keys
    assert "ghost_signal" not in b.keys(), "BCM کلید اختراع کرد"
    assert b.keys() == [], b.keys()


def t_the_feed_is_flag_gated_and_off_by_default():
    """رفتارِ نو = افزودنی + flag-gated + پیش‌فرض خاموش."""
    src = Path(wiring.__file__).read_text("utf-8")
    i = src.index("OCTOPUS_WIRE_BCM_FEED")
    block = src[max(0, i - 700):i + 500]
    assert 'flag("OCTOPUS_WIRE_BCM_FEED")' in block, "تغذیه پشتِ فلگ نیست"
    assert "known_keys=list(BCM_VOCAB)" in block, "واژگان به BCM داده نمی‌شود"
    assert "except Exception" in block, "تغذیه می‌تواند تیک را بکشد"


# ─── ۲: صفِ رأیِ مالک ───────────────────────────────────────────────────────
def _seed_queue(rows):
    p = Path(ENV["root"]) / "VERDICT_QUEUE.md"
    body = ["# صف", "", "| ID | تصمیم | گزینه‌ها | وضعیت | اثر |",
            "|---|---|---|---|---|"]
    body += [f"| {r[0]} | {r[1]} | a/b | {r[2]} | x |" for r in rows]
    p.write_text("\n".join(body), "utf-8")
    return p


def t_open_verdicts_reach_the_self_model():
    import self_knowledge as sk
    _seed_queue([("VQ-A-001", "تصمیمِ باز", "open"),
                 ("VQ-A-002", "تصمیمِ بسته", "A selected"),
                 ("VQ-A-003", "تصمیمِ بازِ دوم", "open")])
    s = sk.snapshot()
    v = s.get("owner_verdicts_open")
    assert v, "صفِ رأی به خودآگاهی نمی‌رسد"
    assert v["n"] == 2, f"شمارِ باز غلط: {v}"
    ids = {x["id"] for x in v["نمونه"]}
    assert ids == {"VQ-A-001", "VQ-A-003"}, ids
    assert "VQ-A-002" not in json.dumps(v, ensure_ascii=False), "ردیفِ بسته هم آمد"


def t_a_missing_or_broken_queue_is_not_an_error():
    import self_knowledge as sk
    p = Path(ENV["root"]) / "VERDICT_QUEUE.md"
    if p.exists():
        p.unlink()
    s = sk.snapshot()
    assert "owner_verdicts_open" not in s
    p.write_text("متنِ آزاد بدونِ جدول\n| ناقص |\n", "utf-8")
    assert isinstance(sk.snapshot(), dict)


def t_the_queue_carries_no_content_only_ids_and_titles():
    """گاردِ نشت: این فایل secret ندارد، ولی قرارداد باید صریح بماند."""
    import self_knowledge as sk
    _seed_queue([("VQ-B-001", "تصمیم", "open")])
    v = sk.snapshot().get("owner_verdicts_open") or {}
    for row in v.get("نمونه", []):
        assert set(row.keys()) == {"id", "تصمیم"}, row
        assert len(row["تصمیم"]) <= 110


def t_the_sample_is_bounded_so_the_prompt_does_not_explode():
    """۴۸ ردیفِ باز نباید کلِ prompt را ببلعد."""
    import self_knowledge as sk
    _seed_queue([(f"VQ-C-{i:03d}", f"تصمیمِ {i}", "open") for i in range(40)])
    v = sk.snapshot().get("owner_verdicts_open") or {}
    assert v["n"] == 40, v["n"]
    assert len(v["نمونه"]) <= 6, f"{len(v['نمونه'])} نمونه — prompt منفجر می‌شود"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_bcm_feed_and_verdicts: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
