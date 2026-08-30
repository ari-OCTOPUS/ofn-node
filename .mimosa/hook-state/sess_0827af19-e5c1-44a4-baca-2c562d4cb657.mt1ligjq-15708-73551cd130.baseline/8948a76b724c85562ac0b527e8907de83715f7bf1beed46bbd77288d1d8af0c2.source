"""
engine.py — هماهنگ‌کننده‌ی پژوهش (خالص): search → score → synthesize → gate.

خروجی یک decision-object است که main.py در Postgres ذخیره می‌کند.
قانونِ طلایی: بدونِ منبع fact نده؛ بدونِ uncertainty verdict نده.
"""

from __future__ import annotations

from . import constitution, source_quality

SYS = (
    "تو پژوهشگرِ محتاطِ LANGAR هستی: مهندسِ مولتی‌ایجنت، متخصصِ روانِ انسان، و مهندسِ "
    "این پروژه. از نتایجِ جست‌وجو یک بریفِ کوتاهِ فارسی بده: هر ادعا تگِ [E]/[S]/[P]، "
    "ارجاع به منبع با شماره، اگر شواهد ضعیف بود صریح بگو، علیت را تحمیل نکن، پزشک نیستی. "
    "در پایان یک «ادعای آزمون‌پذیر» بده."
)


def run_research(question: str, target: str, search, brain) -> dict:
    results = search.search(question)
    ranked = source_quality.rank(results, question)
    unc = source_quality.uncertainty(ranked)
    try:
        brief = brain.ask(SYS, question, ranked, target)
    except Exception as e:
        brief = f"سنتز نشد ({e}). نتایج خام موجودند. [S]"
    crit = constitution.critique(brief)
    if not crit.compliant:
        brief = "⚠️ خروجی با قوانین سازگار نبود — طبقِ «در شک: سکوت» حذف شد."
    return {
        "question": question,
        "target": target,
        "brief": brief,
        "sources": [{"url": r.get("url"), "title": r.get("title"), "score": r.get("_score")}
                    for r in ranked[:5]],
        "uncertainty": unc,
        "compliant": crit.compliant,
        "violations": crit.violations,
        "next_step": ("یک آزمایشِ N-of-1 بساز تا روی داده‌ی واقعی سنجیده شود."
                      if target == "armin"
                      else "یک diffِ سطح ۲ برای بازبینیِ انسان پیشنهاد بده."),
    }
