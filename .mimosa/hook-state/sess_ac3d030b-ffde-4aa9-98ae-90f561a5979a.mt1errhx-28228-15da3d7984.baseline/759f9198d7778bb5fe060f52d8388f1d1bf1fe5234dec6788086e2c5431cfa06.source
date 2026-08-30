"""
synthesizer.py — از نتایجِ خامِ سرچ یک بریفِ سورس‌دار و تگ‌خورده می‌سازد.

اگر brain در دسترس باشد: خلاصه‌ی هوشمند با تگِ [E]/[S]/[P].
اگر نه: فهرستِ ساده‌ی نتایج با تگِ [S] (چون آزموده‌نشده).
"""

from __future__ import annotations

SYS = (
    "تو یک پژوهشگرِ محتاطی. از نتایجِ جست‌وجوی زیر یک بریفِ کوتاهِ فارسی بساز:\n"
    "• هر ادعا را با تگِ [E] (شواهدِ محکم)، [S] (حدس) یا [P] (چارچوب) مشخص کن.\n"
    "• به منابع با شماره ([1]،[2]) ارجاع بده.\n"
    "• اگر شواهد ضعیف یا متناقض بود، صریح بگو.\n"
    "• علیت را تحمیل نکن؛ «همبستگی ≠ علیت».\n"
    "• پزشک نیستی؛ تشخیص/تجویز نده.\n"
    "در پایان یک «ادعای آزمون‌پذیر» بده که بتوان با یک آزمایشِ N-of-1 سنجید."
)


def synthesize(brain, question: str, results: list[dict], target: str = "armin") -> dict:
    sources = [r.get("url", "") for r in results if r.get("url")]
    if not results:
        return {"brief": "نتیجه‌ای از وب پیدا نشد (یا موتورِ سرچ آفلاین است). "
                         "ادعای آزمون‌پذیر را خودت تعریف کن.",
                "sources": [], "tag": "S"}

    if brain is None or getattr(brain, "name", "offline") == "offline":
        lines = [f"[{i+1}] {r.get('title','')} — {r.get('snippet','')[:120]}"
                 for i, r in enumerate(results[:5])]
        return {"brief": "خلاصه‌ی خام (بدونِ LLM):\n" + "\n".join(lines)
                         + "\n[S] این‌ها آزموده‌نشده‌اند؛ با /experiment محک بزن.",
                "sources": sources, "tag": "S"}

    ctx_data = "\n".join(
        f"[{i+1}] {r.get('title','')}: {r.get('snippet','')}" for i, r in enumerate(results[:5]))
    user = f"سؤال/فرضیه: {question}\nهدف: {target}\n\nنتایجِ جست‌وجو:\n{ctx_data}"
    try:
        brief = brain.ask(SYS, {"domain": "research", "label": "پژوهش", "data": user})
    except Exception as e:
        return {"brief": f"سنتز نشد ({e}). نتایج خام موجودند.", "sources": sources, "tag": "S"}
    return {"brief": brief, "sources": sources, "tag": "S"}
