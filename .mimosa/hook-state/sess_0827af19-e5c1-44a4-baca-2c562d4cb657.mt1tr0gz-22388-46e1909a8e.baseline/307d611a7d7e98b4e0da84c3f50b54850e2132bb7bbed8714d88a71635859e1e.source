"""test_research_query_sanity — «چیزی که یاد گرفتم» باید دربارهٔ همان موضوع باشد.

از رونوشتِ واقعیِ گروه، ۲۰۲۶-۰۷-۲۷ و ۲۸:

    🔍 دربارهٔ «A08» تحقیق کردم — «A8» (۱۱ نتیجه)              ← ۷ بار
    🔍 دربارهٔ «perception-bias» تحقیق کردم — «Perceptual hashing»

هیچ‌کدام خطا نداد. هیچ تستی قرمز نشد. هر دو **نتیجه برگرداندند** — فقط نتیجه‌ای که
هیچ ربطی به موضوع نداشت. این بدترین شکلِ شکست است: خروجیِ بی‌ارزش که شبیهِ دانش
لباس پوشیده، و چون شمارندهٔ نتایج غیرصفر بود، هیچ گاردی صدایش را درنیاورد.

ریشه در `school-awareness.json` است که دو نگاشت دارد — `A08 → 0.1584` و
`titles: A08 → "perception-bias"` — و هر دو رشته دست‌نخورده به موتورِ جستجو می‌رفتند.
اسلاگِ خط‌تیره‌دار عبارتِ زبانِ طبیعی نیست؛ موتور نزدیک‌ترین چیزِ هم‌پیشوند را می‌دهد.

این تست دو مرز را قفل می‌کند:
  ۱) شناسهٔ خام (`A08`) هرگز به جستجو نمی‌رسد.
  ۲) اسلاگ قبل از جستجو به عبارت تبدیل می‌شود — ولی برچسبِ گزارش دست‌نخورده می‌ماند.

⚠️ صفر ترافیکِ شبکه: opener تزریق می‌شود و هر کوئری را ثبت می‌کند.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("research-query-sanity")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import web_research as wr   # noqa: E402


def _spy():
    """opener که هرگز به شبکه نمی‌رود و هر URL را نگه می‌دارد."""
    seen = []

    def opener(url: str) -> str:
        seen.append(url)
        return ""
    return opener, seen


# ─── ۱: اسلاگ → عبارت ────────────────────────────────────────────────────
def t_a_hyphenated_slug_becomes_a_real_phrase():
    assert wr._query_of("perception-bias") == "perception bias"
    assert wr._query_of("working-memory") == "working memory"
    assert wr._query_of("self_narrative") == "self narrative"


def t_a_normal_phrase_is_left_alone():
    """نرمال‌سازی نباید موضوع‌های سالم را خراب کند."""
    for ok in ("emotion regulation", "sleep", "spaced repetition"):
        assert wr._query_of(ok) == ok


def t_the_report_label_keeps_the_original_topic():
    """برچسب باید همان چیزی بماند که مدرسه می‌شناسد، وگرنه ردیابی می‌شکند."""
    opener, _ = _spy()
    d = wr.research_topics(["perception-bias"], per_topic=1, opener=opener)
    f = d["findings"][0]
    assert f["topic"] == "perception-bias", f
    assert f["query"] == "perception bias", f


def t_the_query_that_actually_leaves_is_the_normalized_one():
    """مرزِ واقعی: چه چیزی به موتور می‌رسد — نه چه چیزی در رکورد نوشته شده."""
    opener, seen = _spy()
    wr.research_topics(["perception-bias"], per_topic=1, opener=opener)
    joined = " ".join(seen)
    assert "perception-bias" not in joined and "perception%2Dbias" not in joined, seen
    assert seen, "هیچ کوئری‌ای ساخته نشد"


# ─── ۲: شناسهٔ خام ────────────────────────────────────────────────────────
def t_a_bare_internal_id_never_reaches_the_engine():
    """`A08` هفت بار رفت و هفت بار «A8» برگشت. دیگر نمی‌رود."""
    opener, seen = _spy()
    d = wr.research_topics(["A08", "A1", "B12", "ZZ999"], per_topic=1, opener=opener)
    assert d["findings"] == [], d["findings"]
    assert seen == [], seen


def t_an_id_shaped_word_that_is_a_real_topic_still_passes():
    """گارد نباید موضوعِ واقعی را بخورد — مرزش شناسهٔ خالص است، نه هر رشتهٔ عددی."""
    opener, seen = _spy()
    d = wr.research_topics(["GPT4 architecture", "web3"], per_topic=1, opener=opener)
    topics = [f["topic"] for f in d["findings"]]
    assert "GPT4 architecture" in topics, topics
    assert seen, "کوئریِ سالم هم بلاک شد"


def t_mixed_input_drops_only_the_ids():
    opener, _ = _spy()
    d = wr.research_topics(["A08", "habit-loop", "A02"], per_topic=1, opener=opener)
    assert [f["topic"] for f in d["findings"]] == ["habit-loop"], d["findings"]


# ─── ۳: هیچ شبکه‌ای ───────────────────────────────────────────────────────
def t_this_test_makes_no_network_call():
    """اگر opener تزریق‌شده دور زده شود، این تست بی‌معنا می‌شود."""
    opener, seen = _spy()
    wr.research_topics(["sleep"], per_topic=1, opener=opener)
    assert seen, "opener تزریقی استفاده نشد — مسیرِ واقعی ممکن است به شبکه برود"
    assert all(isinstance(u, str) for u in seen)


# ─── ۴: نتیجه باید به کوئری ربط داشته باشد ───────────────────────────────
# نیمهٔ دومِ همان فیکس، از دادهٔ زندهٔ `research-latest.json` ساعتِ ۱۱:۱۲:
#     topic='perception-bias'  query='perception bias'  → «Perceptual hashing»
#     topic='motivation'       query='motivation'       → «Motivation»        ✅
#     topic='self-narrative'   query='self narrative'   → n=0                 ✅
# نرمال‌سازی نقصِ **مکانیکی** را برد، ولی نتیجه‌ای که فقط هم‌پیشوند است هنوز
# «چیزی که یاد گرفتم» نامیده می‌شد — چون شمارِ نتایج غیرصفر بود.

def t_a_prefix_only_match_is_rejected():
    """موردِ واقعی که این گارد از آن آمد."""
    assert wr._relevant("perception bias", [{"title": "Perceptual hashing"}]) == []


def t_a_real_match_survives():
    for q, title in (("motivation", "Motivation"),
                     ("working memory", "Working memory"),
                     ("attention", "Attention economy"),
                     ("emotion regulation", "Emotional self-regulation"),
                     ("sleep", "Sleep deprivation")):
        assert wr._relevant(q, [{"title": title}]), (q, title)


def t_a_substring_is_not_enough():
    """«habit» زیررشتهٔ «habituation» است — مرزِ واژه لازم است نه زیررشته."""
    assert wr._relevant("habit loop", [{"title": "Habituation"}]) == []


def t_an_empty_result_stays_empty():
    assert wr._relevant("هرچیزی", []) == []
    assert wr._relevant("", [{"title": "x"}]) == [{"title": "x"}]   # کوئریِ تهی → نسنجیده


def t_the_pipeline_drops_the_irrelevant_hit():
    """مرزِ واقعی: در مسیرِ کامل، `n` باید صفر شود نه یک."""
    opener, _ = _spy()
    d = wr.research_topics(["perception-bias"], per_topic=1, opener=opener)
    assert d["findings"][0]["n"] == 0, d["findings"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_research_query_sanity: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
