"""test_output_critic — ارگانیسم باید بداند کِی بد کار کرده.

رأیِ مالک ۲۰۲۶-۰۷-۲۷: «عین معلم بالاسرش باش» + «یادش بده بتونه خودشو بسازه».

دادهٔ همان روز که این ماژول را لازم کرد:
  · ۸۳ پیامِ خودکار، **صفر تای‌شان نمره گرفت**.
  · ۳۵٪ از «چیزهایی که یاد گرفتم» تکراری بود — هفت بار همان جست‌وجو روی یک
    شناسهٔ داخلیِ بی‌معنا.
  · کارتِ «نیازت دارم» چهار بار با همان سه آیتم آمد؛ فقط شمارندهٔ آلارم عوض شد.
  · دکتر دو بار گفت «نامعلوم، نیاز به کاوش» و کاوشی نکرد.

هیچ‌کدام باگ نبودند. همه «کار می‌کردند». مسئله این بود که **هیچ‌چیز نمی‌گفت
بدند**.

دو قیدِ متضاد که هم‌زمان باید برقرار باشند:
  ۱) نمره باید **عینی** باشد — نمرهٔ سلیقه‌ای، نمرهٔ بی‌پایه است و بعداً از
     نمرهٔ واقعی جدا نمی‌شود (همان درسِ حلقهٔ معلم).
  ۲) نمره **فیلتر نیست**. سانسورِ خودکارِ خروجی یعنی سیستمی که می‌تواند بدی‌اش
     را از چشمِ مالک پنهان کند — و آن بدتر از خروجیِ بد است.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("output-critic")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import output_critic as oc   # noqa: E402


def _m(text, stream="discovery", ts=1.0):
    return {"ts": ts, "text": text, "stream": stream}


# ─── ۱: تکرار — الگوی واقعیِ همان روز ─────────────────────────────────────
def t_a_counter_change_is_not_a_new_message():
    """«۱۳ هشدار» → «۱۴ هشدار» همان پیام است. اگر تکرار را نگیرد، بی‌فایده است."""
    msgs = [_m(f"🔔 نیازت دارم (3) · {n} هشدارِ امروز") for n in (13, 14, 16, 18)]
    r = oc.grade(msgs)
    assert r["scores"]["repetition"] < 0.4, r["scores"]
    assert any("شمارنده" in f for f in r["findings"]), r["findings"]


def t_genuinely_different_messages_score_well():
    """گاردی که همه‌چیز را بد بخواند، خاموش می‌شود."""
    msgs = [_m("قلب: ضربان ۹۰۰ ثانیه"), _m("دکتر: دو RFC باز"),
            _m("مغز: انسجام ۰.۹۵"), _m("لید: سه کاندید تازه")]
    r = oc.grade(msgs)
    assert r["scores"]["repetition"] == 1.0, r["scores"]
    assert not any("تکرار" in f for f in r["findings"])


def t_the_real_repeated_research_would_be_caught():
    """هفت بار «دربارهٔ A08 تحقیق کردم» — الگوی واقعیِ ۲۰۲۶-۰۷-۲۷."""
    msgs = [_m("دربارهٔ «A08» تحقیق کردم — «A8» (12 نتیجه)")] * 7
    r = oc.grade(msgs)
    assert r["scores"]["repetition"] <= 0.2, r["scores"]


# ─── ۲: عمل‌پذیری — پیشنهادِ بن‌بست ────────────────────────────────────────
def t_a_dead_command_suggestion_is_flagged():
    """کارتی که بگوید «/چیزی بزن» و آن دستور نرسد، بدترین نوعِ خروجی است."""
    msgs = [_m("۲۵۲ تراکنش منتظرِ توست — /هیچ_دستوری_با_این_نام")]
    r = oc.grade(msgs)
    a = r["scores"]["actionability"]
    assert a is not None and a < 1.0, r["scores"]
    assert any("بن‌بست" in f for f in r["findings"]), r["findings"]


def t_a_message_without_commands_is_not_punished():
    """نبودِ دستور یعنی «سنجیدنی نبود»، نه نمرهٔ صفر."""
    r = oc.grade([_m("قلب سالم است")])
    assert r["scores"]["actionability"] is None, r["scores"]


# ─── ۳: خودپاسخی ─────────────────────────────────────────────────────────
def t_saying_unknown_without_investigating_is_flagged():
    """دکتر دو بار گفت «نامعلوم، نیاز به کاوش» و کاوشی نکرد."""
    msgs = [_m("خطای پرتکرار failed ×13 — نامعلوم (نیاز به کاوش)"),
            _m("خطای پرتکرار failed ×14 — نامعلوم (نیاز به کاوش)")]
    r = oc.grade(msgs)
    assert r["scores"]["self_answer"] < 0.5, r["scores"]
    assert any("نامعلوم" in f for f in r["findings"])


# ─── ۴: مرزها ────────────────────────────────────────────────────────────
def t_the_critic_never_blocks_or_sends_anything():
    """قیدِ سختِ دوم: نمره فیلتر نیست."""
    tree = ast.parse(Path(oc.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("send", "send_text", "write_text", "unlink", "block", "suppress"):
        assert d not in called, f"منتقد خروجی را دستکاری می‌کند: {d}"


def t_the_card_says_the_score_is_advice_not_a_filter():
    body = oc.card()
    assert "فیلتر" in body and "پنهان" in body, body
    assert "نکنی:" in body


def t_an_unmeasurable_dimension_stays_none_not_zero():
    """نمرهٔ بی‌پایه بدتر از نبودِ نمره است."""
    r = oc.grade([_m("سلام")])
    assert r["scores"]["actionability"] is None
    assert r["scores"]["novelty"] is None


def t_hostile_input_never_raises():
    for bad in (None, [], [{}], [{"text": None}], [{"text": "ب" * 9000}],
                ["نه‌دیکشنری"], [{"text": "x", "stream": None}]):
        r = oc.grade(bad)
        assert isinstance(r, dict) and "scores" in r, bad


def t_every_score_is_bounded_and_higher_is_better():
    r = oc.grade([_m("الف"), _m("ب"), _m("الف")])
    for k, v in r["scores"].items():
        assert v is None or 0.0 <= v <= 1.0, (k, v)


def t_the_critic_reads_the_real_reachable_command_set():
    """اگر فهرستِ دستورها را هاردکد کند، با اولین تغییرِ روتر دروغ می‌گوید."""
    src = Path(oc.__file__).read_text("utf-8")
    assert "center.py" in src and "approval_channel.py" in src
    cmds = oc._reachable_commands()
    assert len(cmds) >= 15, f"فهرستِ دستورهای واقعی خوانده نشد: {len(cmds)}"


# ─── ۲۰۲۶-۰۷-۲۸: عمل‌پذیری باید سنجیدنی باشد ──────────────────────────────
# امتحانِ زندهٔ همان روز: `actionability` تقریباً همیشه `None` برمی‌گشت. علتش نه
# باگ بود نه بدشانسی — این سنجه می‌پرسد «فرمانی که پیشنهاد دادم می‌رسد؟» ولی دو
# منبعِ نمونه (discoveries/initiative) تقریباً هرگز فرمان پیشنهاد نمی‌کنند.
# کارت‌هایی که می‌کنند (`/review`، `/doctor focus`، `/heart set`) در نمونه نبودند.
# یعنی مهم‌ترین سنجه به داده‌ای نگاه نمی‌کرد که وجودش را توجیه می‌کند — همان
# شکافی که ۳۲ فرمانِ نرسیده را ماه‌ها پنهان نگه داشت.

def t_the_held_stream_is_a_source():
    """بدونِ این منبع، سنجهٔ عمل‌پذیری داده‌ای برای سنجیدن ندارد."""
    src = Path(oc.__file__).read_text("utf-8")
    i = src.index("for rel, kind in (")
    j = src.index("):", i)
    assert "held-stream.jsonl" in src[i:j], "لاگِ نگه‌داشته‌ها منبع نیست"


def t_actionability_becomes_measurable_when_a_command_is_suggested():
    """با یک فرمانِ واقعی در نمونه، نمره باید عدد شود نه None."""
    live = oc.grade([{"ts": 0, "text": "برو /review را بزن", "stream": "held"}])
    assert live["scores"]["actionability"] is not None, live["scores"]
    assert 0.0 <= live["scores"]["actionability"] <= 1.0


def t_a_dead_command_is_actually_caught():
    """قلبِ سنجه: فرمانی که به هیچ‌جا نمی‌رسد باید نمره را پایین بیاورد."""
    r = oc.grade([{"ts": 0, "text": "بزن /یک_فرمان_که_وجود_ندارد", "stream": "held"}])
    a = r["scores"]["actionability"]
    assert a is not None and a < 1.0, r["scores"]
    assert any("بن‌بست" in f for f in r["findings"]), r["findings"]


def t_no_commands_still_returns_none_not_zero():
    """`None` یعنی «سنجیدنی نبود» — صفر یعنی «بد بود». این دو را قاطی نکن."""
    r = oc.grade([{"ts": 0, "text": "هیچ فرمانی اینجا نیست", "stream": "held"}])
    assert r["scores"]["actionability"] is None, r["scores"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_output_critic: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
